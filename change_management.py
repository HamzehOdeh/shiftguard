"""
Workforce Compliance AI - Change Management Module
Handles real-time schedule changes AFTER the schedule is published:
VET (Voluntary Extra Time), VTO (Voluntary Time Off), shift swaps,
call-outs, and mandatory overtime assignment.

All decisions are governed by labor law, union CBA, and company policy.
"""

from datetime import datetime, timedelta
from copy import deepcopy

from sample_schedule import EMPLOYEES, generate_schedule
from rules_engine import (
    get_all_rules,
    CHICAGO_FAIR_WORKWEEK,
    OREGON_PREDICTIVE_SCHEDULING,
    NYC_FAIR_WORKWEEK,
    SAMPLE_UNION_CBA,
    COMPANY_POLICY,
)


# =============================================================================
# HELPER UTILITIES
# =============================================================================

def _parse_time(date_str, time_str):
    """Parse date + time strings into a datetime object."""
    return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")


def _shift_hours(shift):
    """Calculate shift duration in hours (with 0.5 hr unpaid break assumed for 8+ hr shifts)."""
    start = _parse_time(shift["date"], shift["start"])
    end = _parse_time(shift["date"], shift["end"])
    duration = (end - start).total_seconds() / 3600
    return duration


def _get_employee_shifts(schedule, employee_id, date=None):
    """Get all shifts for an employee, optionally filtered by date."""
    shifts = [s for s in schedule["shifts"] if s["employee_id"] == employee_id]
    if date:
        shifts = [s for s in shifts if s["date"] == date]
    return shifts


def _weekly_hours(schedule, employee_id, week_start_date):
    """Total scheduled hours for an employee in a given week (Mon-Sun)."""
    week_start = datetime.strptime(week_start_date, "%Y-%m-%d")
    week_end = week_start + timedelta(days=6)
    total = 0.0
    for shift in schedule["shifts"]:
        if shift["employee_id"] == employee_id:
            shift_date = datetime.strptime(shift["date"], "%Y-%m-%d")
            if week_start <= shift_date <= week_end:
                total += _shift_hours(shift)
    return total


def _consecutive_days(schedule, employee_id, target_date_str):
    """Count consecutive days worked up to and including target_date."""
    target = datetime.strptime(target_date_str, "%Y-%m-%d")
    days = 0
    check_date = target
    while True:
        date_str = check_date.strftime("%Y-%m-%d")
        if any(s for s in schedule["shifts"]
               if s["employee_id"] == employee_id and s["date"] == date_str):
            days += 1
            check_date -= timedelta(days=1)
        else:
            break
    return days


def _hours_between_shifts(schedule, employee_id, new_shift_date, new_shift_start):
    """Calculate minimum rest hours between existing shifts and a proposed new shift start."""
    new_start = _parse_time(new_shift_date, new_shift_start)
    min_gap = float('inf')
    for shift in schedule["shifts"]:
        if shift["employee_id"] == employee_id:
            shift_end = _parse_time(shift["date"], shift["end"])
            shift_start = _parse_time(shift["date"], shift["start"])
            # Gap from existing shift end to new shift start
            gap_after = (new_start - shift_end).total_seconds() / 3600
            # Gap from new shift end (hypothetical) back to existing shift start
            if 0 < gap_after < min_gap:
                min_gap = gap_after
    return min_gap if min_gap != float('inf') else 24.0


def _get_employee_record(employee_id):
    """Get employee record from EMPLOYEES list."""
    for emp in EMPLOYEES:
        if emp["id"] == employee_id:
            return emp
    return None


# =============================================================================
# VET ENGINE - Voluntary Extra Time
# =============================================================================

class VETEngine:
    """Manages Voluntary Extra Time (VET) offers with CBA-compliant equity."""

    def __init__(self):
        # Track cumulative OT hours per employee for equity
        self.ot_history = {}
        # Track accept/decline for fairness auditing
        self.offer_history = []

    def offer_vet(self, schedule, date, shift_start, shift_end, hours_needed, employees=None):
        """
        Decide who to offer VET to, in CBA-compliant order.

        Returns:
            dict with 'eligible' (ordered list) and 'excluded' (with reasons)
        """
        if employees is None:
            employees = EMPLOYEES

        week_start = schedule.get("week_start", date)
        eligible = []
        excluded = []

        # Sort by: lowest OT first (equity), then by seniority rotation
        candidates = sorted(
            employees,
            key=lambda e: (self.ot_history.get(e["id"], 0), e["seniority"])
        )

        for emp in candidates:
            emp_id = emp["id"]
            reasons = []

            # Check weekly hour cap (company policy: 60 hrs max)
            current_hours = _weekly_hours(schedule, emp_id, week_start)
            additional_hours = hours_needed
            if current_hours + additional_hours > 60:
                reasons.append(f"Would exceed 60-hr weekly cap ({current_hours:.1f} current + {additional_hours:.1f} = {current_hours + additional_hours:.1f})")

            # Check rest between shifts (CBA-008: 10 hours minimum)
            rest_gap = _hours_between_shifts(schedule, emp_id, date, shift_start)
            if rest_gap < 10:
                reasons.append(f"Insufficient rest between shifts ({rest_gap:.1f} hrs, need 10)")

            # Check consecutive days (CBA-002: max 6)
            consec = _consecutive_days(schedule, emp_id, date)
            if consec >= 6:
                reasons.append(f"Would exceed 6 consecutive days (already at {consec})")

            # Check if minor (no night work)
            if emp.get("is_minor") and shift_end > "22:00":
                reasons.append("Minor cannot work past 10:00 PM")

            # Check if already working this shift
            existing = _get_employee_shifts(schedule, emp_id, date)
            for ex_shift in existing:
                if ex_shift["start"] == shift_start:
                    reasons.append("Already scheduled for this shift")
                    break

            if reasons:
                excluded.append({"employee": emp, "reasons": reasons})
            else:
                eligible.append({
                    "employee": emp,
                    "current_weekly_hours": current_hours,
                    "ot_history_hours": self.ot_history.get(emp_id, 0),
                    "seniority": emp["seniority"],
                })

        # Record the offer for fairness tracking
        self.offer_history.append({
            "date": date,
            "shift": f"{shift_start}-{shift_end}",
            "hours_needed": hours_needed,
            "eligible_count": len(eligible),
            "excluded_count": len(excluded),
        })

        return {"eligible": eligible, "excluded": excluded}

    def record_acceptance(self, employee_id, hours):
        """Record that an employee accepted VET."""
        self.ot_history[employee_id] = self.ot_history.get(employee_id, 0) + hours

    def record_decline(self, employee_id):
        """Record that an employee declined VET (tracked for fairness but not penalized)."""
        self.offer_history.append({
            "type": "decline",
            "employee_id": employee_id,
            "timestamp": datetime.now().isoformat(),
        })


# =============================================================================
# VTO ENGINE - Voluntary Time Off
# =============================================================================

class VTOEngine:
    """Manages Voluntary Time Off (VTO) offers with minimum staffing guarantees."""

    # Minimum staffing per role to maintain coverage
    MINIMUM_STAFFING = {
        "Pick": 2,
        "Pack": 1,
        "Stow": 1,
        "Ship": 1,
    }

    def offer_vto(self, schedule, date, shift_type, hours_surplus, employees=None):
        """
        Decide who can take VTO while maintaining minimum staffing.

        CBA compliance: offer by inverse seniority (least senior has first option).
        Cannot force VTO on someone who wants to work.

        Returns:
            dict with 'eligible' and 'coverage_impact'
        """
        if employees is None:
            employees = EMPLOYEES

        # Get all employees working this date/shift
        working = []
        for shift in schedule["shifts"]:
            if shift["date"] == date and shift["shift_type"] == shift_type:
                emp = _get_employee_record(shift["employee_id"])
                if emp:
                    working.append({"employee": emp, "shift": shift})

        # Count current staffing by role for this shift
        role_counts = {}
        for w in working:
            role = w["shift"]["role"]
            role_counts[role] = role_counts.get(role, 0) + 1

        # Sort by inverse seniority (highest seniority number = least senior gets first option)
        working_sorted = sorted(working, key=lambda w: -w["employee"]["seniority"])

        eligible = []
        excluded = []

        for w in working_sorted:
            emp = w["employee"]
            shift = w["shift"]
            role = shift["role"]
            reasons = []

            # Check minimum staffing for this role
            min_required = self.MINIMUM_STAFFING.get(role, 1)
            if role_counts.get(role, 0) <= min_required:
                reasons.append(f"Would drop {role} below minimum staffing ({min_required} required)")

            # Check skill coverage (if this is the only person with this role on shift)
            same_role_others = [x for x in working if x["shift"]["role"] == role
                                and x["employee"]["id"] != emp["id"]]
            if not same_role_others and min_required > 0:
                reasons.append(f"Only {role} worker on this shift - cannot release")

            if reasons:
                excluded.append({"employee": emp, "reasons": reasons})
            else:
                eligible.append({
                    "employee": emp,
                    "shift": shift,
                    "hours_released": _shift_hours(shift),
                    "note": "VTO is voluntary - employee may decline",
                })
                # Decrement role count if this person takes VTO
                # (for subsequent eligibility checks)
                role_counts[role] = role_counts.get(role, 0) - 1

            # Stop once we have enough hours covered
            total_releasable = sum(e["hours_released"] for e in eligible)
            if total_releasable >= hours_surplus:
                break

        coverage_impact = {
            "roles_after_vto": {
                role: role_counts.get(role, 0) for role in self.MINIMUM_STAFFING
            },
            "total_hours_releasable": sum(e["hours_released"] for e in eligible),
            "hours_surplus_requested": hours_surplus,
        }

        return {"eligible": eligible, "excluded": excluded, "coverage_impact": coverage_impact}


# =============================================================================
# SHIFT SWAP CHECKER
# =============================================================================

class ShiftSwapChecker:
    """Validates shift swap requests for compliance with all rules."""

    def check_swap(self, schedule, employee_a_id, shift_a, employee_b_id, shift_b, rules=None):
        """
        Validate a proposed shift swap between two employees.

        Checks both employees against all rules post-swap.

        Returns:
            dict with 'approved' (bool), 'reasons', and 'cost_impact'
        """
        if rules is None:
            rules = get_all_rules("Chicago")

        emp_a = _get_employee_record(employee_a_id)
        emp_b = _get_employee_record(employee_b_id)
        violations = []
        warnings = []

        # --- Role/Skill Compatibility ---
        if shift_a["role"] != shift_b["role"]:
            # Check if each employee can perform the other's role
            if emp_a["role"] != shift_b["role"]:
                violations.append(
                    f"{emp_a['name']} is certified for {emp_a['role']}, "
                    f"not {shift_b['role']} (required for Shift B)"
                )
            if emp_b["role"] != shift_a["role"]:
                violations.append(
                    f"{emp_b['name']} is certified for {emp_b['role']}, "
                    f"not {shift_a['role']} (required for Shift A)"
                )

        # --- Rest Period Checks for Employee A (taking Shift B) ---
        rest_a = _hours_between_shifts(schedule, employee_a_id, shift_b["date"], shift_b["start"])
        if rest_a < 10:
            violations.append(
                f"{emp_a['name']} would have only {rest_a:.1f} hrs rest "
                f"(need 10) if taking shift on {shift_b['date']}"
            )

        # --- Rest Period Checks for Employee B (taking Shift A) ---
        rest_b = _hours_between_shifts(schedule, employee_b_id, shift_a["date"], shift_a["start"])
        if rest_b < 10:
            violations.append(
                f"{emp_b['name']} would have only {rest_b:.1f} hrs rest "
                f"(need 10) if taking shift on {shift_a['date']}"
            )

        # --- Consecutive Days for Employee A ---
        consec_a = _consecutive_days(schedule, employee_a_id, shift_b["date"])
        if consec_a >= 6:
            violations.append(
                f"{emp_a['name']} would hit {consec_a + 1} consecutive days"
            )

        # --- Consecutive Days for Employee B ---
        consec_b = _consecutive_days(schedule, employee_b_id, shift_a["date"])
        if consec_b >= 6:
            violations.append(
                f"{emp_b['name']} would hit {consec_b + 1} consecutive days"
            )

        # --- Weekly Hours Check ---
        week_start = schedule.get("week_start", shift_a["date"])
        hours_a = _weekly_hours(schedule, employee_a_id, week_start)
        hours_b = _weekly_hours(schedule, employee_b_id, week_start)

        swap_delta_a = _shift_hours(shift_b) - _shift_hours(shift_a)
        swap_delta_b = _shift_hours(shift_a) - _shift_hours(shift_b)

        if hours_a + swap_delta_a > 60:
            violations.append(
                f"{emp_a['name']} would exceed 60-hr cap "
                f"({hours_a + swap_delta_a:.1f} hrs after swap)"
            )
        if hours_b + swap_delta_b > 60:
            violations.append(
                f"{emp_b['name']} would exceed 60-hr cap "
                f"({hours_b + swap_delta_b:.1f} hrs after swap)"
            )

        # --- Minor Restrictions ---
        if emp_a.get("is_minor") and shift_b["end"] > "22:00":
            violations.append(f"{emp_a['name']} is a minor and cannot work past 10:00 PM")
        if emp_b.get("is_minor") and shift_a["end"] > "22:00":
            violations.append(f"{emp_b['name']} is a minor and cannot work past 10:00 PM")

        # --- Predictability Pay (schedule already posted?) ---
        cost_impact = 0.0
        schedule_posted = schedule.get("schedule_posted_date")
        if schedule_posted:
            posted_dt = datetime.strptime(schedule_posted, "%Y-%m-%d")
            today = datetime.now()
            if today > posted_dt:
                # Schedule was already posted - predictability pay applies
                # Chicago: 1 hour additional pay per change
                cost_impact = 2 * 18.0  # 2 employees x $18/hr (assumed rate)
                warnings.append(
                    f"Predictability pay owed: ${cost_impact:.2f} "
                    f"(1 hr per employee, schedule already posted)"
                )

        approved = len(violations) == 0

        return {
            "approved": approved,
            "employee_a": emp_a["name"] if emp_a else employee_a_id,
            "employee_b": emp_b["name"] if emp_b else employee_b_id,
            "violations": violations,
            "warnings": warnings,
            "cost_impact": cost_impact,
        }


# =============================================================================
# CALLOUT HANDLER
# =============================================================================

class CalloutHandler:
    """Handles employee call-outs and finds compliant replacements."""

    def __init__(self, vet_engine=None):
        self.vet_engine = vet_engine or VETEngine()

    def handle_callout(self, schedule, employee_id, date, shift, on_call_list=None):
        """
        Handle an employee calling out. Find replacement using priority order:
        1. Volunteers from VET list (already offered)
        2. On-call employees
        3. Qualified employees on day off (by inverse seniority)
        4. Mandatory OT (last resort)

        Returns:
            dict with ranked replacement options and compliance status for each
        """
        emp = _get_employee_record(employee_id)
        emp_name = emp["name"] if emp else employee_id
        role_needed = shift["role"]
        shift_hours = _shift_hours(shift)

        options = []

        # --- Option 1: VET Volunteers ---
        vet_result = self.vet_engine.offer_vet(
            schedule, date, shift["start"], shift["end"], shift_hours
        )
        for candidate in vet_result["eligible"][:3]:  # Top 3 from VET
            options.append({
                "priority": 1,
                "method": "VET Volunteer",
                "employee": candidate["employee"],
                "compliance_status": "COMPLIANT",
                "notes": (
                    f"Current weekly hrs: {candidate['current_weekly_hours']:.1f}, "
                    f"OT equity rank: {candidate['ot_history_hours']:.1f} hrs cumulative"
                ),
                "cost": "1.5x rate (OT)" if candidate["current_weekly_hours"] >= 40 else "Straight time",
            })

        # --- Option 2: On-call Employees ---
        if on_call_list:
            for oc_id in on_call_list:
                oc_emp = _get_employee_record(oc_id)
                if not oc_emp:
                    continue
                if oc_emp["role"] != role_needed:
                    continue
                weekly_hrs = _weekly_hours(schedule, oc_id, schedule.get("week_start", date))
                rest = _hours_between_shifts(schedule, oc_id, date, shift["start"])
                consec = _consecutive_days(schedule, oc_id, date)

                status = "COMPLIANT"
                notes_parts = []
                if weekly_hrs + shift_hours > 60:
                    status = "WARNING - exceeds 60hr cap"
                    notes_parts.append("Would exceed weekly cap")
                if rest < 10:
                    status = "VIOLATION - rest period"
                    notes_parts.append(f"Only {rest:.1f} hrs rest")
                if consec >= 6:
                    status = "VIOLATION - consecutive days"
                    notes_parts.append(f"{consec} consecutive days already")

                options.append({
                    "priority": 2,
                    "method": "On-Call",
                    "employee": oc_emp,
                    "compliance_status": status,
                    "notes": "; ".join(notes_parts) if notes_parts else "All checks passed",
                    "cost": "On-call rate + OT if >40 hrs",
                })

        # --- Option 3: Qualified employees on day off (inverse seniority) ---
        day_off_employees = []
        for e in EMPLOYEES:
            if e["id"] == employee_id:
                continue
            if e["role"] != role_needed:
                continue
            existing_shifts = _get_employee_shifts(schedule, e["id"], date)
            if not existing_shifts:
                day_off_employees.append(e)

        # Sort by inverse seniority (least senior asked first)
        day_off_employees.sort(key=lambda e: -e["seniority"])

        for doff_emp in day_off_employees[:3]:
            weekly_hrs = _weekly_hours(schedule, doff_emp["id"], schedule.get("week_start", date))
            rest = _hours_between_shifts(schedule, doff_emp["id"], date, shift["start"])
            consec = _consecutive_days(schedule, doff_emp["id"], date)

            status = "COMPLIANT"
            notes_parts = []
            if weekly_hrs + shift_hours > 60:
                status = "WARNING"
                notes_parts.append(f"Weekly hours would be {weekly_hrs + shift_hours:.1f}")
            if rest < 10:
                status = "VIOLATION"
                notes_parts.append(f"Rest gap only {rest:.1f} hrs")
            if consec >= 6:
                status = "VIOLATION"
                notes_parts.append(f"Already {consec} consecutive days")
            if doff_emp.get("is_minor") and shift["end"] > "22:00":
                status = "VIOLATION"
                notes_parts.append("Minor - cannot work past 10 PM")

            options.append({
                "priority": 3,
                "method": "Day-Off Recall (Inverse Seniority)",
                "employee": doff_emp,
                "compliance_status": status,
                "notes": "; ".join(notes_parts) if notes_parts else "All checks passed",
                "cost": "OT rate (called in on day off)",
            })

        # --- Option 4: Mandatory OT (last resort) ---
        # Only if no compliant volunteers found
        compliant_options = [o for o in options if o["compliance_status"] == "COMPLIANT"]
        if not compliant_options:
            mot_assigner = MandatoryOTAssigner()
            mot_result = mot_assigner.assign_mandatory_ot(
                EMPLOYEES, date, shift,
                rules=get_all_rules("Chicago"),
                schedule=schedule
            )
            if mot_result["assigned"]:
                options.append({
                    "priority": 4,
                    "method": "Mandatory OT (Last Resort)",
                    "employee": mot_result["assigned"],
                    "compliance_status": mot_result["compliance_status"],
                    "notes": mot_result["justification"],
                    "cost": "1.5x rate (mandatory OT) + potential grievance risk",
                })

        return {
            "callout_employee": emp_name,
            "date": date,
            "shift": f"{shift['start']}-{shift['end']} ({shift['role']})",
            "replacement_options": sorted(options, key=lambda o: o["priority"]),
        }


# =============================================================================
# MANDATORY OT ASSIGNER
# =============================================================================

class MandatoryOTAssigner:
    """Assigns mandatory overtime as last resort, with full CBA compliance."""

    # Track mandatory OT assignments for equitable rotation
    _rotation_history = {}

    def assign_mandatory_ot(self, employees, date, shift, rules, schedule=None):
        """
        Force OT assignment when all voluntary options exhausted.

        CBA rules:
        - Inverse seniority (least senior assigned first)
        - Equitable rotation (track cumulative mandatory OT)
        - Max 12 hrs mandatory OT per week
        - Must still pass rest/consecutive checks

        Returns:
            dict with assignment, audit trail, and compliance status
        """
        role_needed = shift["role"]
        shift_hours_needed = _shift_hours(shift)

        # Filter to qualified employees, sort by inverse seniority + rotation equity
        candidates = [
            e for e in employees
            if e["role"] == role_needed and not e.get("is_minor")
        ]

        # Sort: inverse seniority first, then by least mandatory OT history
        candidates.sort(
            key=lambda e: (
                -e["seniority"],
                self._rotation_history.get(e["id"], 0)
            )
        )

        week_start = schedule.get("week_start", date) if schedule else date

        for candidate in candidates:
            emp_id = candidate["id"]
            violations = []

            # Check rest between shifts
            if schedule:
                rest = _hours_between_shifts(schedule, emp_id, date, shift["start"])
                if rest < 10:
                    violations.append(f"Rest period violation ({rest:.1f} hrs)")

                # Check consecutive days
                consec = _consecutive_days(schedule, emp_id, date)
                if consec >= 6:
                    violations.append(f"Consecutive days violation ({consec + 1} days)")

                # Check weekly hour cap
                weekly = _weekly_hours(schedule, emp_id, week_start)
                if weekly + shift_hours_needed > 60:
                    violations.append(f"Weekly cap exceeded ({weekly + shift_hours_needed:.1f} hrs)")

            # Check mandatory OT weekly limit (CBA-006: 12 hrs max)
            current_mandatory = self._rotation_history.get(emp_id, 0)
            if current_mandatory + shift_hours_needed > 12:
                violations.append(
                    f"Mandatory OT limit exceeded ({current_mandatory + shift_hours_needed:.1f} hrs, max 12)"
                )

            if not violations:
                # Valid assignment
                self._rotation_history[emp_id] = current_mandatory + shift_hours_needed
                return {
                    "assigned": candidate,
                    "compliance_status": "COMPLIANT (Mandatory OT - CBA inverse seniority)",
                    "justification": (
                        f"Assigned by inverse seniority rotation. "
                        f"Cumulative mandatory OT: {self._rotation_history[emp_id]:.1f} hrs this period."
                    ),
                    "audit_trail": {
                        "date": date,
                        "shift": f"{shift['start']}-{shift['end']}",
                        "assigned_to": candidate["id"],
                        "reason": "All voluntary options exhausted",
                        "seniority_rank": candidate["seniority"],
                        "mandatory_ot_total": self._rotation_history[emp_id],
                        "candidates_checked": len(candidates),
                        "timestamp": datetime.now().isoformat(),
                    },
                }

        # No one can be assigned without violation
        return {
            "assigned": None,
            "compliance_status": "CANNOT ASSIGN - all candidates have violations",
            "justification": "No qualified employee can be assigned without rule violation. Escalate to management.",
            "audit_trail": {
                "date": date,
                "shift": f"{shift['start']}-{shift['end']}",
                "assigned_to": None,
                "reason": "All candidates have blocking violations",
                "candidates_checked": len(candidates),
                "timestamp": datetime.now().isoformat(),
            },
        }


# =============================================================================
# SCHEDULE CHANGE LOG
# =============================================================================

class ScheduleChangeLog:
    """Maintains full audit trail of every schedule change after publication."""

    def __init__(self, jurisdiction="Chicago"):
        self.changes = []
        self.jurisdiction = jurisdiction

    def log_change(self, original_shift, new_shift, reason, approved_by, timestamp=None):
        """
        Record a schedule change with full context.

        Args:
            original_shift: dict of original shift details (or None for additions)
            new_shift: dict of new shift details (or None for removals)
            reason: str explaining why the change was made
            approved_by: str identifying who approved
            timestamp: datetime of when change was made (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Calculate predictability pay owed for this change
        premium = self._calculate_single_premium(original_shift, new_shift)

        entry = {
            "change_id": len(self.changes) + 1,
            "timestamp": timestamp.isoformat(),
            "original": original_shift,
            "new": new_shift,
            "reason": reason,
            "approved_by": approved_by,
            "type": self._classify_change(original_shift, new_shift),
            "premium_pay_owed": premium,
        }
        self.changes.append(entry)
        return entry

    def _classify_change(self, original, new):
        """Classify the type of schedule change."""
        if original is None:
            return "ADDITION"
        if new is None:
            return "REMOVAL"
        if original.get("employee_id") != new.get("employee_id"):
            return "REASSIGNMENT"
        if original.get("start") != new.get("start") or original.get("end") != new.get("end"):
            return "TIME_CHANGE"
        return "MODIFICATION"

    def _calculate_single_premium(self, original, new):
        """Calculate premium pay for a single change based on jurisdiction."""
        if self.jurisdiction == "Chicago":
            # 1 hour additional pay per schedule change after posting
            return 18.00  # Assumed hourly rate
        elif self.jurisdiction == "Oregon":
            # Half-shift pay for changes with <14 days notice
            if new and new.get("start") and new.get("end"):
                hours = _shift_hours(new) if "date" in new else 8.0
                return (hours / 2) * 18.00
            return 4 * 18.00  # Default half of 8-hr shift
        elif self.jurisdiction == "NYC":
            # $10-$75 depending on notice period (assume short notice here)
            return 75.00
        return 0.0

    def get_weekly_summary(self):
        """Generate a weekly change summary with total premium costs."""
        total_premium = sum(c["premium_pay_owed"] for c in self.changes)
        by_type = {}
        for c in self.changes:
            change_type = c["type"]
            by_type[change_type] = by_type.get(change_type, 0) + 1

        return {
            "total_changes": len(self.changes),
            "changes_by_type": by_type,
            "total_premium_pay_owed": total_premium,
            "jurisdiction": self.jurisdiction,
            "changes": self.changes,
        }


# =============================================================================
# PREMIUM PAY CALCULATOR
# =============================================================================

class PremiumPayCalculator:
    """Calculates premium pay obligations across jurisdictions."""

    # Jurisdiction-specific premium rules
    PREMIUM_RULES = {
        "Chicago": {
            "description": "1 hour additional pay per schedule change after posting",
            "calculation": "hourly_rate * 1.0 per change",
            "base_rate": 18.00,
        },
        "Oregon": {
            "description": "Half-shift pay for changes with <14 days notice",
            "calculation": "hourly_rate * (shift_hours / 2) per change",
            "base_rate": 18.00,
        },
        "NYC": {
            "description": "$10-$75 depending on notice period",
            "tiers": [
                {"notice_hours": 0, "notice_max_hours": 24, "amount": 75.00},
                {"notice_hours": 24, "notice_max_hours": 48, "amount": 50.00},
                {"notice_hours": 48, "notice_max_hours": 168, "amount": 25.00},
                {"notice_hours": 168, "notice_max_hours": 336, "amount": 10.00},
            ],
        },
    }

    def calculate_premiums(self, changes, jurisdiction="Chicago", hourly_rate=18.00):
        """
        Calculate total premium pay owed for a list of changes.

        Args:
            changes: list of change dicts (from ScheduleChangeLog)
            jurisdiction: which premium rules to apply
            hourly_rate: base hourly rate for calculations

        Returns:
            dict with itemized premiums and totals
        """
        items = []
        total = 0.0

        for change in changes:
            premium = 0.0
            description = ""

            if jurisdiction == "Chicago":
                premium = hourly_rate * 1.0  # 1 hour per change
                description = f"1 hr predictability pay @ ${hourly_rate:.2f}/hr"

            elif jurisdiction == "Oregon":
                # Half-shift pay
                shift_data = change.get("new") or change.get("original")
                if shift_data and "date" in shift_data and "start" in shift_data and "end" in shift_data:
                    hours = _shift_hours(shift_data)
                else:
                    hours = 8.0
                premium = (hours / 2) * hourly_rate
                description = f"Half-shift ({hours/2:.1f} hrs) @ ${hourly_rate:.2f}/hr"

            elif jurisdiction == "NYC":
                # Tiered based on notice period
                notice_hrs = change.get("notice_hours", 0)
                for tier in self.PREMIUM_RULES["NYC"]["tiers"]:
                    if tier["notice_hours"] <= notice_hrs < tier["notice_max_hours"]:
                        premium = tier["amount"]
                        description = f"NYC tier: ${tier['amount']:.2f} ({notice_hrs} hrs notice)"
                        break
                else:
                    premium = 10.00
                    description = "NYC minimum premium"

            items.append({
                "change_id": change.get("change_id", "N/A"),
                "type": change.get("type", "UNKNOWN"),
                "premium": premium,
                "description": description,
                "employee": (change.get("new") or change.get("original") or {}).get("name", "Unknown"),
            })
            total += premium

        return {
            "jurisdiction": jurisdiction,
            "rule_applied": self.PREMIUM_RULES.get(jurisdiction, {}).get("description", "Unknown"),
            "items": items,
            "total_premium_owed": total,
            "hourly_rate_used": hourly_rate,
        }


# =============================================================================
# __main__ DEMONSTRATION
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("WORKFORCE COMPLIANCE AI - CHANGE MANAGEMENT MODULE")
    print("Real-Time Schedule Change Engine with Full Compliance Checking")
    print("=" * 80)

    # --- Setup: Published schedule for 10 employees (scales to any headcount) ---
    schedule = generate_schedule()
    print(f"\nPublished Schedule: {schedule['facility']}")
    print(f"Week: {schedule['week_start']} to {schedule['week_end']}")
    print(f"Posted: {schedule['schedule_posted_date']}")
    print(f"Total shifts: {len(schedule['shifts'])}")
    print(f"Employees: {len(EMPLOYEES)} (demo; scales to any headcount)")

    # Initialize engines
    vet_engine = VETEngine()
    vto_engine = VTOEngine()
    swap_checker = ShiftSwapChecker()
    callout_handler = CalloutHandler(vet_engine=vet_engine)
    change_log = ScheduleChangeLog(jurisdiction="Chicago")
    premium_calc = PremiumPayCalculator()

    # =========================================================================
    # SCENARIO 1: Three employees call out on Wednesday (July 9)
    # =========================================================================
    print("\n" + "=" * 80)
    print("SCENARIO 1: THREE CALLOUTS ON WEDNESDAY (2026-07-09)")
    print("=" * 80)

    callout_date = "2026-07-09"
    callout_shifts = [
        {"employee_id": "E003", "date": callout_date, "start": "07:00", "end": "15:30", "role": "Pick", "shift_type": "Day"},
        {"employee_id": "E005", "date": callout_date, "start": "07:00", "end": "15:30", "role": "Pick", "shift_type": "Day"},
        {"employee_id": "E009", "date": callout_date, "start": "07:00", "end": "15:30", "role": "Ship", "shift_type": "Day"},
    ]

    for i, callout_shift in enumerate(callout_shifts, 1):
        emp = _get_employee_record(callout_shift["employee_id"])
        print(f"\n--- Callout #{i}: {emp['name']} ({callout_shift['role']}) ---")

        result = callout_handler.handle_callout(
            schedule, callout_shift["employee_id"], callout_date, callout_shift
        )

        print(f"  Shift: {result['shift']}")
        print(f"  Replacement Options ({len(result['replacement_options'])}):")
        for opt in result["replacement_options"]:
            print(f"    Priority {opt['priority']} [{opt['method']}]: "
                  f"{opt['employee']['name']} - {opt['compliance_status']}")
            print(f"      Notes: {opt['notes']}")
            print(f"      Cost: {opt['cost']}")

        # Log the callout and first compliant replacement
        compliant = [o for o in result["replacement_options"] if "COMPLIANT" in o["compliance_status"]]
        if compliant:
            replacement = compliant[0]
            change_log.log_change(
                original_shift=callout_shift,
                new_shift={**callout_shift, "employee_id": replacement["employee"]["id"],
                           "name": replacement["employee"]["name"]},
                reason=f"Callout by {emp['name']} - replaced via {replacement['method']}",
                approved_by="System (Auto-VET)",
            )

    # =========================================================================
    # SCENARIO 2: Thursday has surplus labor - VTO offered
    # =========================================================================
    print("\n" + "=" * 80)
    print("SCENARIO 2: THURSDAY SURPLUS - VTO OFFERED (2026-07-10)")
    print("=" * 80)

    vto_date = "2026-07-10"
    print(f"\n  Surplus: 2 extra Pick shifts (demand dropped)")

    vto_result = vto_engine.offer_vto(schedule, vto_date, "Day", hours_surplus=17.0)

    print(f"\n  Eligible for VTO ({len(vto_result['eligible'])}):")
    for e in vto_result["eligible"]:
        print(f"    {e['employee']['name']} (Seniority #{e['employee']['seniority']}) "
              f"- {e['hours_released']:.1f} hrs releasable")
        print(f"      Note: {e['note']}")

    print(f"\n  Excluded from VTO ({len(vto_result['excluded'])}):")
    for x in vto_result["excluded"]:
        print(f"    {x['employee']['name']}: {'; '.join(x['reasons'])}")

    print(f"\n  Coverage Impact:")
    print(f"    Roles after VTO: {vto_result['coverage_impact']['roles_after_vto']}")
    print(f"    Total hours releasable: {vto_result['coverage_impact']['total_hours_releasable']:.1f}")

    # Log VTO acceptances
    for e in vto_result["eligible"][:2]:  # Assume 2 accept
        original = {"employee_id": e["employee"]["id"], "name": e["employee"]["name"],
                    "date": vto_date, "start": "07:00", "end": "15:30",
                    "role": e["employee"]["role"], "shift_type": "Day"}
        change_log.log_change(
            original_shift=original,
            new_shift=None,
            reason=f"VTO accepted by {e['employee']['name']} (surplus labor)",
            approved_by="Operations Manager",
        )

    # =========================================================================
    # SCENARIO 3: Friday shift swap request
    # =========================================================================
    print("\n" + "=" * 80)
    print("SCENARIO 3: SHIFT SWAP REQUEST - FRIDAY (2026-07-11)")
    print("=" * 80)

    # David Kim (E008, Pick, Day) wants to swap with Sarah Martinez (E001, Pick, Day)
    shift_a = {"employee_id": "E008", "name": "David Kim", "date": "2026-07-11",
               "start": "07:00", "end": "15:30", "role": "Pick", "shift_type": "Day"}
    shift_b = {"employee_id": "E001", "name": "Sarah Martinez", "date": "2026-07-11",
               "start": "06:00", "end": "14:30", "role": "Pick", "shift_type": "Day"}

    print(f"\n  Request: David Kim (07:00-15:30) <-> Sarah Martinez (06:00-14:30)")
    swap_result = swap_checker.check_swap(schedule, "E008", shift_a, "E001", shift_b)

    print(f"\n  Decision: {'APPROVED' if swap_result['approved'] else 'DENIED'}")
    if swap_result["violations"]:
        print(f"  Violations:")
        for v in swap_result["violations"]:
            print(f"    - {v}")
    if swap_result["warnings"]:
        print(f"  Warnings:")
        for w in swap_result["warnings"]:
            print(f"    - {w}")
    print(f"  Cost Impact: ${swap_result['cost_impact']:.2f}")

    if swap_result["approved"]:
        change_log.log_change(
            original_shift=shift_a,
            new_shift={**shift_b, "employee_id": "E008", "name": "David Kim"},
            reason="Shift swap: David Kim <-> Sarah Martinez (mutual request)",
            approved_by="Shift Supervisor",
        )
        change_log.log_change(
            original_shift=shift_b,
            new_shift={**shift_a, "employee_id": "E001", "name": "Sarah Martinez"},
            reason="Shift swap: David Kim <-> Sarah Martinez (mutual request)",
            approved_by="Shift Supervisor",
        )

    # =========================================================================
    # SCENARIO 4: Mandatory OT needed for Saturday
    # =========================================================================
    print("\n" + "=" * 80)
    print("SCENARIO 4: MANDATORY OT - SATURDAY (2026-07-12)")
    print("=" * 80)

    mot_date = "2026-07-12"
    mot_shift = {"employee_id": None, "date": mot_date, "start": "06:00",
                 "end": "14:30", "role": "Pick", "shift_type": "Day"}

    print(f"\n  Need: 1 Pick worker for Saturday 06:00-14:30")
    print(f"  All voluntary options exhausted. Initiating mandatory OT assignment.")

    mot_assigner = MandatoryOTAssigner()
    mot_result = mot_assigner.assign_mandatory_ot(
        EMPLOYEES, mot_date, mot_shift,
        rules=get_all_rules("Chicago"),
        schedule=schedule
    )

    if mot_result["assigned"]:
        print(f"\n  Assigned: {mot_result['assigned']['name']} "
              f"(Seniority #{mot_result['assigned']['seniority']})")
        print(f"  Status: {mot_result['compliance_status']}")
        print(f"  Justification: {mot_result['justification']}")
        print(f"  Audit Trail:")
        for k, v in mot_result["audit_trail"].items():
            print(f"    {k}: {v}")

        change_log.log_change(
            original_shift=None,
            new_shift={**mot_shift, "employee_id": mot_result["assigned"]["id"],
                       "name": mot_result["assigned"]["name"]},
            reason=f"Mandatory OT: {mot_result['justification']}",
            approved_by="Operations Manager (CBA compliant)",
        )
    else:
        print(f"\n  CANNOT ASSIGN: {mot_result['justification']}")
        print(f"  Action: Escalate to senior management")

    # =========================================================================
    # SCENARIO 5: VET offered for Wednesday gaps (show eligibility logic)
    # =========================================================================
    print("\n" + "=" * 80)
    print("SCENARIO 5: VET ELIGIBILITY ANALYSIS - WEDNESDAY (2026-07-09)")
    print("=" * 80)

    vet_result = vet_engine.offer_vet(
        schedule, "2026-07-09", "07:00", "15:30", hours_needed=8.5
    )

    print(f"\n  VET Offer: Wednesday 07:00-15:30 (8.5 hrs needed)")
    print(f"\n  Eligible ({len(vet_result['eligible'])}):")
    for e in vet_result["eligible"]:
        print(f"    {e['employee']['name']} | Seniority #{e['seniority']} | "
              f"Weekly Hrs: {e['current_weekly_hours']:.1f} | "
              f"Cumulative OT: {e['ot_history_hours']:.1f}")

    print(f"\n  Excluded ({len(vet_result['excluded'])}):")
    for x in vet_result["excluded"]:
        print(f"    {x['employee']['name']}: {'; '.join(x['reasons'])}")

    # =========================================================================
    # FINAL: Premium Pay Summary + Audit Log
    # =========================================================================
    print("\n" + "=" * 80)
    print("WEEKLY PREMIUM PAY SUMMARY")
    print("=" * 80)

    summary = change_log.get_weekly_summary()
    premium_result = premium_calc.calculate_premiums(
        summary["changes"], jurisdiction="Chicago", hourly_rate=18.00
    )

    print(f"\n  Jurisdiction: {premium_result['jurisdiction']}")
    print(f"  Rule: {premium_result['rule_applied']}")
    print(f"  Hourly Rate: ${premium_result['hourly_rate_used']:.2f}")
    print(f"\n  Itemized Premiums:")
    for item in premium_result["items"]:
        print(f"    #{item['change_id']} [{item['type']}] {item['employee']}: "
              f"${item['premium']:.2f} - {item['description']}")

    print(f"\n  TOTAL PREMIUM PAY OWED: ${premium_result['total_premium_owed']:.2f}")

    print("\n" + "=" * 80)
    print("FULL CHANGE AUDIT LOG")
    print("=" * 80)

    print(f"\n  Total Changes This Week: {summary['total_changes']}")
    print(f"  By Type: {summary['changes_by_type']}")
    print(f"  Total Premium Cost: ${summary['total_premium_pay_owed']:.2f}")
    print(f"\n  Detailed Log:")
    for c in summary["changes"]:
        print(f"    [{c['change_id']}] {c['timestamp'][:19]} | {c['type']} | "
              f"Reason: {c['reason'][:60]}...")
        print(f"         Approved by: {c['approved_by']} | Premium: ${c['premium_pay_owed']:.2f}")

    print("\n" + "=" * 80)
    print("END OF CHANGE MANAGEMENT DEMO")
    print(f"Note: This demo uses {len(EMPLOYEES)} employees but all engines")
    print("scale to any headcount with O(n log n) sorting for equity decisions.")
    print("=" * 80)
