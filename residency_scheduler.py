"""
ShiftGuard - Residency Scheduling Engine
ACGME-compliant scheduling for GME programs.
Handles: block rotations, 24+4 call, night float, daily adjustments with real-time compliance.

KEY INSIGHT: Programs set a YEAR schedule, but change it DAILY.
Every change must be compliance-checked BEFORE it's approved.
This is what no competitor does.
"""

from datetime import datetime, timedelta
from collections import defaultdict


# ============================================================
# ACGME COMMON PROGRAM REQUIREMENTS (Duty Hours)
# Effective July 2017 (latest revision)
# ============================================================

ACGME_RULES = {
    "WEEKLY_HOURS_CAP": {
        "id": "ACGME-DH-001",
        "name": "80-Hour Weekly Limit",
        "description": "Duty hours must not exceed 80 hours per week, averaged over 4 weeks, inclusive of all in-house call and moonlighting",
        "limit": 80,
        "averaging_window_weeks": 4,
        "includes": ["clinical", "call", "moonlighting"],
        "excludes": ["reading", "research_from_home"],
        "citation": "ACGME Common Program Requirements VI.F.1",
        "penalty": "Citation, probation, loss of accreditation",
    },
    "CONTINUOUS_DUTY_PGY1": {
        "id": "ACGME-DH-002",
        "name": "PGY-1 Continuous Duty Limit",
        "description": "PGY-1 residents must not work more than 24 continuous hours. Up to 4 additional hours for transitions, education, and patient safety.",
        "max_continuous_hours": 24,
        "additional_hours_allowed": 4,
        "additional_purpose": "transitions of care, education, patient safety activities only (no new patients)",
        "applies_to": ["PGY-1"],
        "citation": "ACGME Common Program Requirements VI.F.4.a",
    },
    "CONTINUOUS_DUTY_UPPER": {
        "id": "ACGME-DH-003",
        "name": "Upper-Level Continuous Duty Limit",
        "description": "PGY-2+ residents: 24 hours of continuous duty + up to 4 hours for transitions",
        "max_continuous_hours": 24,
        "additional_hours_allowed": 4,
        "applies_to": ["PGY-2", "PGY-3", "PGY-4", "PGY-5", "Fellow"],
        "citation": "ACGME Common Program Requirements VI.F.4.b",
    },
    "REST_BETWEEN_SHIFTS": {
        "id": "ACGME-DH-004",
        "name": "Minimum Rest Between Shifts",
        "description": "Minimum 8 hours off between scheduled duty periods. Should have 10 hours; MUST have 8 hours.",
        "minimum_hours": 8,
        "recommended_hours": 10,
        "after_24h_duty": 14,
        "citation": "ACGME Common Program Requirements VI.F.5",
    },
    "DAY_OFF_PER_WEEK": {
        "id": "ACGME-DH-005",
        "name": "One Day Off in Seven",
        "description": "Residents must have 1 day (24h) free of duty per week, averaged over 4 weeks. At-home call cannot count as day off.",
        "days_off_per_4_weeks": 4,
        "minimum_continuous_hours": 24,
        "at_home_call_counts": False,
        "citation": "ACGME Common Program Requirements VI.F.2",
    },
    "NIGHT_FLOAT_MAX": {
        "id": "ACGME-DH-006",
        "name": "Night Float Maximum",
        "description": "Night float must not exceed 6 consecutive nights",
        "max_consecutive_nights": 6,
        "citation": "ACGME Common Program Requirements VI.F.6",
    },
    "IN_HOUSE_CALL_FREQUENCY": {
        "id": "ACGME-DH-007",
        "name": "In-House Call Frequency",
        "description": "In-house call must occur no more frequently than every 3rd night, averaged over 4 weeks",
        "max_frequency": "every_third_night",
        "averaging_window_weeks": 4,
        "citation": "ACGME Common Program Requirements VI.F.7",
    },
    "MOONLIGHTING_CAP": {
        "id": "ACGME-DH-008",
        "name": "Moonlighting Restrictions",
        "description": "Internal moonlighting counts toward 80-hour limit. Must not interfere with education. Program director approval required.",
        "counts_toward_80h": True,
        "requires_pd_approval": True,
        "citation": "ACGME Common Program Requirements VI.F.8",
    },
    "EDUCATION_TIME": {
        "id": "ACGME-DH-009",
        "name": "Protected Education Time",
        "description": "Programs should provide protected time for education. Residents should attend >80% of core didactics.",
        "recommended_hours_per_week": 4,
        "didactic_attendance_target": 0.80,
        "citation": "ACGME Common Program Requirements VI.A",
    },
}

# Block rotation types
ROTATION_TYPES = {
    "CLINICAL": {"name": "Clinical Rotation", "duty_hours_apply": True, "example": "ED, ICU, Wards"},
    "CALL": {"name": "Call Block", "duty_hours_apply": True, "is_call": True, "example": "24+4 in-house"},
    "NIGHT_FLOAT": {"name": "Night Float", "duty_hours_apply": True, "max_consecutive": 6, "example": "7 consecutive nights"},
    "ELECTIVE": {"name": "Elective", "duty_hours_apply": True, "lighter_load": True},
    "RESEARCH": {"name": "Research Block", "duty_hours_apply": False, "example": "Protected research time"},
    "VACATION": {"name": "Vacation", "duty_hours_apply": False},
    "CONFERENCE": {"name": "Conference/Education", "duty_hours_apply": False},
}

# Call schedule patterns
CALL_PATTERNS = {
    "24_PLUS_4": {
        "name": "24+4 In-House Call",
        "on_duty_hours": 24,
        "post_call_max_hours": 4,
        "post_call_restrictions": "No new patients, transitions and education only",
        "rest_after": 14,
    },
    "NIGHT_FLOAT": {
        "name": "Night Float",
        "shift_hours": 12,
        "typical_start": "19:00",
        "typical_end": "07:00",
        "max_consecutive": 6,
        "days_off_after": 1,
    },
    "SHORT_CALL": {
        "name": "Short Call (Admitting)",
        "extra_hours": 4,
        "added_to_regular_shift": True,
        "description": "Regular shift + 4h admitting at end",
    },
    "HOME_CALL": {
        "name": "Home Call (Backup)",
        "on_site_required": False,
        "counts_toward_hours": "only_if_called_in",
        "post_call_day_off": "if_called_in_and_worked_past_midnight",
    },
}


class Resident:
    """Represents a resident with PGY level, rotation assignments, and hours tracking."""

    def __init__(self, resident_id, name, pgy_level, program, start_date=None):
        self.id = resident_id
        self.name = name
        self.pgy_level = pgy_level  # PGY-1, PGY-2, etc.
        self.program = program  # e.g., "Emergency Medicine", "Internal Medicine"
        self.start_date = start_date or datetime.now().strftime("%Y-%m-%d")
        self.block_schedule = []  # Year-long rotation blocks
        self.daily_shifts = []  # Actual shifts (includes swaps, adjustments)
        self.moonlighting_hours = 0
        self.violations = []
        self.education_hours = 0


class RotationBlock:
    """A multi-week rotation assignment."""

    def __init__(self, block_id, rotation_type, start_date, end_date,
                 location=None, attending=None, call_pattern=None):
        self.id = block_id
        self.rotation_type = rotation_type
        self.start_date = start_date
        self.end_date = end_date
        self.location = location
        self.attending = attending
        self.call_pattern = call_pattern
        self.adjustments = []  # Swaps, sick calls, changes


class ResidencyScheduler:
    """
    Full residency scheduling engine with ACGME compliance.
    Core capability: every daily adjustment is compliance-checked in real-time.
    """

    def __init__(self, program_name, specialty, num_residents=None):
        self.program_name = program_name
        self.specialty = specialty
        self.residents = {}
        self.rotations = []
        self.daily_log = []
        self.violations = []

    def add_resident(self, resident_id, name, pgy_level):
        """Add a resident to the program."""
        resident = Resident(resident_id, name, pgy_level, self.program_name)
        self.residents[resident_id] = resident
        return resident

    def set_year_schedule(self, resident_id, blocks):
        """
        Set the year-long block rotation schedule for a resident.
        blocks: list of {rotation_type, start_date, end_date, location, call_pattern}
        """
        resident = self.residents.get(resident_id)
        if not resident:
            return {"error": "Resident not found"}

        resident.block_schedule = []
        for i, b in enumerate(blocks):
            block = RotationBlock(
                block_id=f"{resident_id}-BLK-{i+1:02d}",
                rotation_type=b.get("rotation_type", "CLINICAL"),
                start_date=b.get("start_date"),
                end_date=b.get("end_date"),
                location=b.get("location"),
                attending=b.get("attending"),
                call_pattern=b.get("call_pattern"),
            )
            resident.block_schedule.append(block)

        return {"resident": resident_id, "blocks_set": len(blocks)}

    def log_shift(self, resident_id, date, start, end, shift_type="clinical",
                  is_call=False, is_post_call=False):
        """
        Log an actual worked shift (or scheduled shift).
        This is what gets adjusted daily.
        """
        resident = self.residents.get(resident_id)
        if not resident:
            return {"error": "Resident not found"}

        start_hour = int(start.split(":")[0]) + int(start.split(":")[1]) / 60
        end_hour = int(end.split(":")[0]) + int(end.split(":")[1]) / 60
        hours = end_hour - start_hour
        if hours <= 0:
            hours += 24

        shift = {
            "resident_id": resident_id,
            "date": date,
            "start": start,
            "end": end,
            "hours": round(hours, 1),
            "type": shift_type,
            "is_call": is_call,
            "is_post_call": is_post_call,
            "logged_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        resident.daily_shifts.append(shift)
        self.daily_log.append(shift)
        return shift

    def check_swap_compliance(self, resident_id, proposed_shift, giving_up_shift=None):
        """
        THE KEY FEATURE: Before approving a swap/coverage, check if it violates ACGME.
        Returns: {safe: bool, violations: [...], warnings: [...]}
        """
        resident = self.residents.get(resident_id)
        if not resident:
            return {"safe": False, "violations": [{"rule": "UNKNOWN", "message": "Resident not found"}]}

        # Simulate adding the proposed shift
        test_shifts = resident.daily_shifts.copy()
        if giving_up_shift:
            test_shifts = [s for s in test_shifts if not (
                s["date"] == giving_up_shift.get("date") and s["start"] == giving_up_shift.get("start")
            )]
        test_shifts.append(proposed_shift)

        # Run all ACGME checks against the simulated schedule
        violations = []
        warnings = []

        # Check 1: 80-hour weekly cap (averaged over 4 weeks)
        weekly_check = self._check_80h_cap(test_shifts, proposed_shift["date"])
        if weekly_check.get("violated"):
            violations.append(weekly_check)
        elif weekly_check.get("warning"):
            warnings.append(weekly_check)

        # Check 2: Continuous duty limit
        continuous_check = self._check_continuous_duty(
            test_shifts, proposed_shift, resident.pgy_level
        )
        if continuous_check.get("violated"):
            violations.append(continuous_check)

        # Check 3: Rest between shifts
        rest_check = self._check_rest_period(test_shifts, proposed_shift)
        if rest_check.get("violated"):
            violations.append(rest_check)
        elif rest_check.get("warning"):
            warnings.append(rest_check)

        # Check 4: Day off per week
        dayoff_check = self._check_day_off(test_shifts, proposed_shift["date"])
        if dayoff_check.get("violated"):
            violations.append(dayoff_check)

        # Check 5: Night float consecutive
        night_check = self._check_night_float_consecutive(test_shifts, proposed_shift)
        if night_check.get("violated"):
            violations.append(night_check)

        return {
            "safe": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "proposed_shift": proposed_shift,
            "resident": resident.name,
            "pgy_level": resident.pgy_level,
            "explanation": self._generate_explanation(violations, warnings, resident),
        }

    def get_duty_hours_summary(self, resident_id, reference_date=None):
        """
        Real-time duty hours dashboard for a single resident.
        Shows: current week, 4-week average, remaining capacity, risk level.
        """
        resident = self.residents.get(resident_id)
        if not resident:
            return None

        if reference_date is None:
            reference_date = datetime.now()
        if isinstance(reference_date, str):
            reference_date = datetime.strptime(reference_date, "%Y-%m-%d")

        # Calculate rolling 4-week hours
        four_weeks_ago = reference_date - timedelta(weeks=4)
        recent_shifts = [
            s for s in resident.daily_shifts
            if s["date"] >= four_weeks_ago.strftime("%Y-%m-%d")
            and s["date"] <= reference_date.strftime("%Y-%m-%d")
        ]

        total_hours = sum(s["hours"] for s in recent_shifts)
        weekly_average = total_hours / 4 if recent_shifts else 0

        # This week specifically
        week_start = reference_date - timedelta(days=reference_date.weekday())
        this_week_shifts = [
            s for s in recent_shifts
            if s["date"] >= week_start.strftime("%Y-%m-%d")
        ]
        this_week_hours = sum(s["hours"] for s in this_week_shifts)

        # Remaining capacity
        remaining_this_week = max(0, 80 - this_week_hours)
        remaining_before_violation = max(0, (80 * 4) - total_hours)

        # Risk level
        if weekly_average > 78:
            risk = "CRITICAL"
        elif weekly_average > 72:
            risk = "HIGH"
        elif weekly_average > 65:
            risk = "MODERATE"
        else:
            risk = "SAFE"

        # Consecutive days
        dates_worked = sorted(set(s["date"] for s in recent_shifts), reverse=True)
        consecutive = 0
        for i, d in enumerate(dates_worked):
            expected = (reference_date - timedelta(days=i)).strftime("%Y-%m-%d")
            if d == expected:
                consecutive += 1
            else:
                break

        return {
            "resident_id": resident_id,
            "name": resident.name,
            "pgy_level": resident.pgy_level,
            "this_week_hours": round(this_week_hours, 1),
            "four_week_average": round(weekly_average, 1),
            "four_week_total": round(total_hours, 1),
            "remaining_this_week": round(remaining_this_week, 1),
            "remaining_before_violation": round(remaining_before_violation, 1),
            "consecutive_days": consecutive,
            "risk_level": risk,
            "acgme_cap": 80,
            "shifts_this_period": len(recent_shifts),
            "explanation": (
                f"{resident.name} ({resident.pgy_level}): {weekly_average:.0f}h/week avg "
                f"(cap: 80h). {remaining_this_week:.0f}h remaining this week. "
                f"{'SAFE' if risk == 'SAFE' else 'ATTENTION NEEDED — ' + risk + ' risk'}."
            ),
        }

    def get_program_dashboard(self, reference_date=None):
        """Program director view: all residents' duty hours at a glance."""
        dashboard = []
        for res_id, resident in self.residents.items():
            summary = self.get_duty_hours_summary(res_id, reference_date)
            if summary:
                dashboard.append(summary)

        # Sort by risk (highest first)
        risk_order = {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2, "SAFE": 3}
        dashboard.sort(key=lambda x: risk_order.get(x["risk_level"], 4))

        violations_count = sum(1 for d in dashboard if d["risk_level"] in ("CRITICAL", "HIGH"))

        return {
            "program": self.program_name,
            "total_residents": len(self.residents),
            "at_risk": violations_count,
            "all_compliant": violations_count == 0,
            "residents": dashboard,
            "summary": (
                f"Program: {self.program_name} | "
                f"{len(self.residents)} residents | "
                f"{'ALL COMPLIANT' if violations_count == 0 else f'{violations_count} AT RISK'}"
            ),
        }

    def process_daily_adjustment(self, adjustment_type, resident_id, details):
        """
        Handle daily schedule changes with real-time compliance check.
        Types: sick_call, swap, conference, add_shift, remove_shift
        """
        result = {"type": adjustment_type, "resident": resident_id, "timestamp": datetime.now().isoformat()}

        if adjustment_type == "sick_call":
            # Resident calls sick → remove their shifts, check who can cover
            date = details.get("date", datetime.now().strftime("%Y-%m-%d"))
            result["action"] = f"Removed {resident_id} from {date}"
            result["next_step"] = "Find coverage — checking ACGME compliance for all candidates"

            # Find who can cover without violating
            safe_covers = []
            for res_id, res in self.residents.items():
                if res_id == resident_id:
                    continue
                proposed = {
                    "resident_id": res_id,
                    "date": date,
                    "start": details.get("start", "07:00"),
                    "end": details.get("end", "19:00"),
                    "hours": 12,
                    "type": "coverage",
                    "is_call": False,
                    "is_post_call": False,
                }
                check = self.check_swap_compliance(res_id, proposed)
                if check["safe"]:
                    summary = self.get_duty_hours_summary(res_id)
                    safe_covers.append({
                        "resident": res.name,
                        "pgy_level": res.pgy_level,
                        "current_hours": summary["this_week_hours"] if summary else 0,
                        "would_be_at": (summary["this_week_hours"] + 12) if summary else 12,
                        "risk_after": "SAFE" if (summary and summary["this_week_hours"] + 12 < 72) else "MODERATE",
                    })

            safe_covers.sort(key=lambda x: x["current_hours"])
            result["safe_covers"] = safe_covers
            result["recommendation"] = safe_covers[0] if safe_covers else None
            result["explanation"] = (
                f"{len(safe_covers)} residents can cover without ACGME violation. "
                f"Recommend: {safe_covers[0]['resident']} (lowest hours at {safe_covers[0]['current_hours']}h)."
                if safe_covers else "NO SAFE COVERAGE AVAILABLE — all residents would violate 80h cap."
            )

        elif adjustment_type == "swap":
            # Two residents want to swap a shift
            other_id = details.get("other_resident_id")
            date = details.get("date")
            proposed_shift = {
                "resident_id": resident_id,
                "date": date,
                "start": details.get("start", "07:00"),
                "end": details.get("end", "19:00"),
                "hours": details.get("hours", 12),
                "type": "swap_coverage",
                "is_call": details.get("is_call", False),
                "is_post_call": False,
            }

            check_a = self.check_swap_compliance(resident_id, proposed_shift)
            check_b = self.check_swap_compliance(other_id, proposed_shift) if other_id else {"safe": True}

            result["resident_a_safe"] = check_a["safe"]
            result["resident_b_safe"] = check_b["safe"]
            result["approved"] = check_a["safe"] and check_b["safe"]
            result["explanation"] = check_a["explanation"]

            if not result["approved"]:
                result["denial_reason"] = (
                    f"Swap denied: {check_a['violations'][0]['message']}"
                    if check_a["violations"] else "Compliance concern for other resident"
                )

        elif adjustment_type == "conference":
            # Remove from clinical duty for conference day
            date = details.get("date")
            result["action"] = f"Marked {resident_id} as conference day ({date})"
            result["hours_credited"] = details.get("hours", 4)
            result["explanation"] = "Conference time does not count toward duty hours but protects education requirement."

        return result

    # --- Private compliance check methods ---

    def _check_80h_cap(self, shifts, reference_date):
        """Check 80-hour/week cap averaged over 4 weeks."""
        if isinstance(reference_date, str):
            reference_date = datetime.strptime(reference_date, "%Y-%m-%d")

        four_weeks_ago = reference_date - timedelta(weeks=4)
        recent = [s for s in shifts if s["date"] >= four_weeks_ago.strftime("%Y-%m-%d")]
        total = sum(s["hours"] for s in recent)
        avg_weekly = total / 4

        if avg_weekly > 80:
            return {
                "violated": True,
                "rule": "ACGME-DH-001",
                "message": f"80-hour cap VIOLATED: {avg_weekly:.1f}h/week average (max: 80h)",
                "current": round(avg_weekly, 1),
                "limit": 80,
            }
        elif avg_weekly > 75:
            return {
                "warning": True,
                "rule": "ACGME-DH-001",
                "message": f"Approaching 80h cap: {avg_weekly:.1f}h/week average. Only {80 - avg_weekly:.1f}h buffer remaining.",
                "current": round(avg_weekly, 1),
            }
        return {}

    def _check_continuous_duty(self, shifts, proposed, pgy_level):
        """Check continuous duty doesn't exceed 24+4."""
        max_hours = 24
        additional = 4
        proposed_hours = proposed.get("hours", 12)

        # Check if any existing shift + proposed creates >28h continuous block
        same_day = [s for s in shifts if s["date"] == proposed["date"]]
        total_day = sum(s["hours"] for s in same_day) + proposed_hours

        if total_day > (max_hours + additional):
            return {
                "violated": True,
                "rule": "ACGME-DH-002" if "PGY-1" in pgy_level else "ACGME-DH-003",
                "message": f"Continuous duty VIOLATED: {total_day:.0f}h in one period (max: {max_hours}+{additional}h)",
            }
        return {}

    def _check_rest_period(self, shifts, proposed):
        """Check minimum 8h (should be 10h) between duty periods."""
        proposed_date = proposed["date"]
        proposed_start_h = int(proposed["start"].split(":")[0])

        # Find previous day's last shift
        try:
            prev_date = (datetime.strptime(proposed_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return {}

        prev_shifts = [s for s in shifts if s["date"] == prev_date]
        if not prev_shifts:
            return {}

        last_end = max(int(s["end"].split(":")[0]) for s in prev_shifts)
        rest_hours = (24 - last_end) + proposed_start_h

        if rest_hours < 8:
            return {
                "violated": True,
                "rule": "ACGME-DH-004",
                "message": f"Rest period VIOLATED: only {rest_hours}h between shifts (minimum: 8h, recommended: 10h)",
            }
        elif rest_hours < 10:
            return {
                "warning": True,
                "rule": "ACGME-DH-004",
                "message": f"Rest period below recommendation: {rest_hours}h (recommended: 10h, minimum: 8h)",
            }
        return {}

    def _check_day_off(self, shifts, reference_date):
        """Check 1 day off per 7 (averaged over 4 weeks = 4 days off per 28 days)."""
        if isinstance(reference_date, str):
            reference_date = datetime.strptime(reference_date, "%Y-%m-%d")

        four_weeks_ago = reference_date - timedelta(days=28)
        dates_worked = set(
            s["date"] for s in shifts
            if s["date"] >= four_weeks_ago.strftime("%Y-%m-%d")
        )

        days_off = 28 - len(dates_worked)
        if days_off < 4:
            return {
                "violated": True,
                "rule": "ACGME-DH-005",
                "message": f"Day-off requirement VIOLATED: only {days_off} days off in 28 days (minimum: 4)",
            }
        return {}

    def _check_night_float_consecutive(self, shifts, proposed):
        """Check night float doesn't exceed 6 consecutive nights."""
        if int(proposed.get("start", "07:00").split(":")[0]) < 17:
            return {}  # Not a night shift

        proposed_date = proposed["date"]
        consecutive = 1

        for i in range(1, 7):
            try:
                check_date = (datetime.strptime(proposed_date, "%Y-%m-%d") - timedelta(days=i)).strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                break
            night_shifts = [s for s in shifts if s["date"] == check_date and int(s["start"].split(":")[0]) >= 17]
            if night_shifts:
                consecutive += 1
            else:
                break

        if consecutive > 6:
            return {
                "violated": True,
                "rule": "ACGME-DH-006",
                "message": f"Night float VIOLATED: {consecutive} consecutive nights (max: 6)",
            }
        return {}

    def _generate_explanation(self, violations, warnings, resident):
        """Plain English explanation of compliance check result."""
        if not violations and not warnings:
            return f"All clear — {resident.name} can safely take this shift. No ACGME violations."

        parts = []
        if violations:
            parts.append(f"CANNOT APPROVE: {violations[0]['message']}")
        if warnings:
            parts.append(f"Caution: {warnings[0]['message']}")

        return " | ".join(parts)


def create_demo_residency_program():
    """Create a demo EM residency program with sample data."""
    program = ResidencyScheduler("Emergency Medicine Residency", "Emergency Medicine")

    # Add residents
    program.add_resident("R001", "Dr. Sarah Chen", "PGY-3")
    program.add_resident("R002", "Dr. James Williams", "PGY-2")
    program.add_resident("R003", "Dr. Priya Patel", "PGY-1")
    program.add_resident("R004", "Dr. Michael Kim", "PGY-3")
    program.add_resident("R005", "Dr. Aisha Johnson", "PGY-1")

    # Log some shifts to create realistic hours
    base_date = datetime.now() - timedelta(days=14)
    for day_offset in range(14):
        date = (base_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")

        # R001 (PGY-3): Heavy week
        if day_offset % 2 == 0:
            program.log_shift("R001", date, "07:00", "19:00", "clinical")
        if day_offset % 4 == 0:
            program.log_shift("R001", date, "19:00", "07:00", "night_float", is_call=True)

        # R002 (PGY-2): Moderate
        if day_offset % 3 != 0:
            program.log_shift("R002", date, "07:00", "17:00", "clinical")

        # R003 (PGY-1): Standard
        if day_offset < 10 and day_offset % 7 != 6:
            program.log_shift("R003", date, "06:00", "18:00", "clinical")

        # R004: Night float block
        if 3 <= day_offset <= 8:
            program.log_shift("R004", date, "19:00", "07:00", "night_float")

        # R005: Light week (post-vacation)
        if day_offset >= 10 and day_offset % 2 == 0:
            program.log_shift("R005", date, "07:00", "17:00", "clinical")

    return program
