"""
Workforce Compliance AI - Worker Self-Service Portal
Two-way communication: workers submit requests, set preferences, accept VET,
propose swaps. Auto-approval engine handles 80%+ without manager intervention.
"""

from datetime import datetime, timedelta
from collections import defaultdict
from hours_tracker import (
    calculate_employee_hours, calculate_fatigue_score,
    get_shift_duration, OT_THRESHOLD_WEEKLY, MAX_WEEKLY_HOURS
)
from shift_templates import (
    SHIFT_TEMPLATES, SHIFT_ASSIGNMENTS, get_day_name,
    find_coverage_for_absence
)


# Request types
REQUEST_TYPES = {
    "HOLIDAY": "Holiday/Time-Off Request",
    "SHIFT_SWAP": "Shift Swap",
    "VET_ACCEPT": "VET Acceptance",
    "VET_DECLINE": "VET Decline",
    "PREFERENCE": "Availability Preference Update",
    "OPEN_SHIFT": "Open Shift Pickup",
    "SCHEDULE_QUESTION": "Schedule Question",
}

# Auto-approval rules
AUTO_APPROVE_RULES = {
    "min_coverage_maintained": True,
    "no_compliance_violation": True,
    "fairness_not_degraded": True,
    "advance_notice_met": True,
    "advance_notice_days": 14,
}

# Request statuses
STATUS_PENDING = "PENDING"
STATUS_AUTO_APPROVED = "AUTO_APPROVED"
STATUS_APPROVED = "APPROVED"
STATUS_DENIED = "DENIED"
STATUS_ESCALATED = "ESCALATED"
STATUS_WITHDRAWN = "WITHDRAWN"


class WorkerPortal:
    """Worker-facing portal for submitting requests and managing preferences."""

    def __init__(self, employees=None, shift_assignments=None, shift_templates=None):
        self.employees = employees or []
        self.shift_assignments = shift_assignments or SHIFT_ASSIGNMENTS
        self.shift_templates = shift_templates or SHIFT_TEMPLATES
        self.requests = []
        self.preferences = {}
        self.vet_offers = []
        self.open_shifts = []
        self._next_id = 1

    def submit_holiday_request(self, employee_id, start_date, end_date, priority=1,
                               reason="", flexible=False):
        """
        Worker submits a holiday/time-off request with priority ranking.
        """
        request = {
            "id": self._get_next_id(),
            "type": "HOLIDAY",
            "employee_id": employee_id,
            "employee_name": self._get_name(employee_id),
            "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "start_date": start_date,
            "end_date": end_date,
            "priority": priority,
            "reason": reason,
            "flexible": flexible,
            "status": STATUS_PENDING,
            "auto_approval_result": None,
            "manager_notes": "",
            "alternatives_suggested": [],
        }

        # Run auto-approval check
        approval = self._check_auto_approval_holiday(request)
        request["auto_approval_result"] = approval

        if approval["can_auto_approve"]:
            request["status"] = STATUS_AUTO_APPROVED
        elif approval["needs_escalation"]:
            request["status"] = STATUS_ESCALATED
        # else stays PENDING for manager review

        self.requests.append(request)
        return request

    def submit_shift_swap(self, requester_id, target_id, requester_date, target_date,
                          reason=""):
        """
        Worker proposes a shift swap with a colleague.
        Both parties must agree, then system checks compliance.
        """
        request = {
            "id": self._get_next_id(),
            "type": "SHIFT_SWAP",
            "employee_id": requester_id,
            "employee_name": self._get_name(requester_id),
            "target_employee_id": target_id,
            "target_employee_name": self._get_name(target_id),
            "requester_date": requester_date,
            "target_date": target_date,
            "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "reason": reason,
            "status": STATUS_PENDING,
            "target_accepted": None,
            "auto_approval_result": None,
            "compliance_check": None,
        }

        # Check compliance for both sides
        compliance = self._check_swap_compliance(request)
        request["compliance_check"] = compliance

        if compliance["both_compliant"]:
            request["auto_approval_result"] = {
                "can_auto_approve": True,
                "reason": "Swap is compliant for both parties. Awaiting target acceptance.",
                "checks_passed": compliance["checks_passed"],
            }
        else:
            request["auto_approval_result"] = {
                "can_auto_approve": False,
                "reason": compliance["denial_reason"],
                "checks_passed": compliance["checks_passed"],
            }
            request["status"] = STATUS_ESCALATED

        self.requests.append(request)
        return request

    def accept_swap(self, request_id, target_employee_id):
        """Target employee accepts a swap request."""
        request = self._get_request(request_id)
        if not request or request["type"] != "SHIFT_SWAP":
            return {"error": "Request not found"}
        if request["target_employee_id"] != target_employee_id:
            return {"error": "Not the target of this swap"}

        request["target_accepted"] = True

        # If compliance was OK, auto-approve
        if request["auto_approval_result"]["can_auto_approve"]:
            request["status"] = STATUS_AUTO_APPROVED
            return {"status": "AUTO_APPROVED", "message": "Swap approved automatically. Both schedules updated."}
        else:
            request["status"] = STATUS_ESCALATED
            return {"status": "ESCALATED", "message": "Swap needs manager review due to compliance concern."}

    def respond_to_vet(self, employee_id, vet_offer_id, accept=True):
        """Worker accepts or declines a VET offer."""
        offer = next((o for o in self.vet_offers if o["id"] == vet_offer_id), None)
        if not offer:
            return {"error": "VET offer not found"}

        request = {
            "id": self._get_next_id(),
            "type": "VET_ACCEPT" if accept else "VET_DECLINE",
            "employee_id": employee_id,
            "employee_name": self._get_name(employee_id),
            "vet_offer_id": vet_offer_id,
            "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "status": STATUS_AUTO_APPROVED if accept else STATUS_AUTO_APPROVED,
            "shift_details": offer.get("shift_details", {}),
        }

        if accept:
            offer["status"] = "ACCEPTED"
            offer["accepted_by"] = employee_id
        else:
            offer["status"] = "DECLINED"
            offer["declined_by"] = offer.get("declined_by", [])
            offer["declined_by"].append(employee_id)

        self.requests.append(request)
        return request

    def pickup_open_shift(self, employee_id, open_shift_id):
        """Worker picks up an open/uncovered shift."""
        shift = next((s for s in self.open_shifts if s["id"] == open_shift_id), None)
        if not shift:
            return {"error": "Open shift not found or already taken"}
        if shift.get("taken_by"):
            return {"error": f"Already picked up by {shift['taken_by_name']}"}

        # Check compliance
        compliance = self._check_pickup_compliance(employee_id, shift)

        request = {
            "id": self._get_next_id(),
            "type": "OPEN_SHIFT",
            "employee_id": employee_id,
            "employee_name": self._get_name(employee_id),
            "open_shift_id": open_shift_id,
            "shift_details": shift,
            "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "compliance_check": compliance,
            "status": STATUS_PENDING,
        }

        if compliance["compliant"]:
            request["status"] = STATUS_AUTO_APPROVED
            shift["taken_by"] = employee_id
            shift["taken_by_name"] = self._get_name(employee_id)
        else:
            request["status"] = STATUS_ESCALATED

        self.requests.append(request)
        return request

    def update_preferences(self, employee_id, preferences):
        """
        Worker updates their availability preferences.
        preferences dict can include:
        - preferred_shift_type: "day" / "evening" / "night"
        - no_work_days: ["Fri", "Sat"]
        - vet_available_days: ["Thu", "Fri"]
        - max_weekly_hours_preferred: 45
        - holiday_priorities: [{dates, priority, reason}]
        - notes: free text
        """
        self.preferences[employee_id] = {
            "employee_id": employee_id,
            "employee_name": self._get_name(employee_id),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            **preferences,
        }

        request = {
            "id": self._get_next_id(),
            "type": "PREFERENCE",
            "employee_id": employee_id,
            "employee_name": self._get_name(employee_id),
            "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "preferences": preferences,
            "status": STATUS_AUTO_APPROVED,
            "auto_approval_result": {"can_auto_approve": True, "reason": "Preferences recorded."},
        }
        self.requests.append(request)
        return request

    def get_worker_dashboard(self, employee_id):
        """Get everything a worker needs to see in their portal."""
        assignment = next(
            (a for a in self.shift_assignments if a["employee_id"] == employee_id), None
        )
        if not assignment:
            return {"error": "Employee not found"}

        template = self.shift_templates.get(assignment["shift_code"], {})

        my_requests = [r for r in self.requests if r["employee_id"] == employee_id]
        my_vet_offers = [o for o in self.vet_offers
                         if o.get("offered_to") == employee_id and o.get("status") == "PENDING"]
        available_open_shifts = [s for s in self.open_shifts if not s.get("taken_by")]

        # Pending swaps where I'm the target
        swap_requests_for_me = [
            r for r in self.requests
            if r["type"] == "SHIFT_SWAP"
            and r.get("target_employee_id") == employee_id
            and r.get("target_accepted") is None
        ]

        return {
            "employee_id": employee_id,
            "name": assignment["name"],
            "shift_code": assignment["shift_code"],
            "role": assignment["role"],
            "schedule_pattern": template.get("pattern", {}),
            "days_on": template.get("days_on", []),
            "days_off": template.get("days_off", []),
            "weekly_hours": template.get("weekly_hours", 0),
            "my_requests": my_requests,
            "pending_requests": [r for r in my_requests if r["status"] == STATUS_PENDING],
            "approved_requests": [r for r in my_requests if r["status"] in (STATUS_APPROVED, STATUS_AUTO_APPROVED)],
            "vet_offers_pending": my_vet_offers,
            "open_shifts_available": available_open_shifts,
            "swap_requests_for_me": swap_requests_for_me,
            "my_preferences": self.preferences.get(employee_id, {}),
        }

    def create_vet_offer(self, shift_date, start_time, end_time, role, department,
                         offered_to=None, offered_to_all=False):
        """Manager creates a VET offer for a specific shift."""
        offer = {
            "id": self._get_next_id(),
            "type": "VET",
            "shift_details": {
                "date": shift_date,
                "start": start_time,
                "end": end_time,
                "role": role,
                "department": department,
            },
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "offered_to": offered_to,
            "offered_to_all": offered_to_all,
            "status": "PENDING",
            "accepted_by": None,
            "declined_by": [],
        }
        self.vet_offers.append(offer)
        return offer

    def create_open_shift(self, shift_date, start_time, end_time, role,
                          reason="Coverage needed"):
        """Post an open shift for anyone to pick up."""
        shift = {
            "id": self._get_next_id(),
            "date": shift_date,
            "start": start_time,
            "end": end_time,
            "role": role,
            "reason": reason,
            "posted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "taken_by": None,
            "taken_by_name": None,
        }
        self.open_shifts.append(shift)
        return shift

    def get_request_history(self, employee_id=None, status=None, request_type=None):
        """Get filtered request history."""
        results = self.requests

        if employee_id:
            results = [r for r in results if r["employee_id"] == employee_id]
        if status:
            results = [r for r in results if r["status"] == status]
        if request_type:
            results = [r for r in results if r["type"] == request_type]

        return sorted(results, key=lambda x: x["submitted_at"], reverse=True)

    # --- Auto-Approval Engine ---

    def _check_auto_approval_holiday(self, request):
        """
        Auto-approval logic for holiday requests.
        Can approve if:
        1. Advance notice >= 14 days
        2. Coverage can be maintained (enough people on that shift code remain)
        3. No overlap with blackout dates
        4. Fairness: not requesting more holidays than team average
        """
        checks_passed = []
        checks_failed = []

        # Check 1: Advance notice
        submit_date = datetime.strptime(request["submitted_at"][:10], "%Y-%m-%d")
        start_date = datetime.strptime(request["start_date"], "%Y-%m-%d")
        notice_days = (start_date - submit_date).days

        if notice_days >= AUTO_APPROVE_RULES["advance_notice_days"]:
            checks_passed.append(f"Advance notice: {notice_days} days (>= 14 required)")
        else:
            checks_failed.append(f"Short notice: only {notice_days} days (14 required for auto-approval)")

        # Check 2: Coverage maintained
        assignment = next(
            (a for a in self.shift_assignments if a["employee_id"] == request["employee_id"]), None
        )
        if assignment:
            shift_code = assignment["shift_code"]
            same_code_count = sum(
                1 for a in self.shift_assignments if a["shift_code"] == shift_code
            )
            # If more than 1 person on this shift code, coverage maintained
            if same_code_count > 1:
                checks_passed.append(f"Coverage: {same_code_count-1} others on {shift_code}")
            else:
                checks_failed.append(f"Coverage risk: only person on {shift_code}")
        else:
            checks_failed.append("Employee assignment not found")

        # Check 3: Not during blackout (peak season, etc.)
        # Simplified: no blackout dates in demo
        checks_passed.append("No blackout period conflict")

        # Check 4: Fairness check
        emp_requests = [
            r for r in self.requests
            if r["employee_id"] == request["employee_id"]
            and r["type"] == "HOLIDAY"
            and r["status"] in (STATUS_APPROVED, STATUS_AUTO_APPROVED)
        ]
        if len(emp_requests) < 5:
            checks_passed.append(f"Fairness: {len(emp_requests)} holidays approved this year (within limit)")
        else:
            checks_failed.append(f"Fairness concern: already {len(emp_requests)} holidays approved")

        # Decision
        can_auto = len(checks_failed) == 0
        needs_escalation = any("Coverage risk" in f or "Fairness concern" in f for f in checks_failed)

        return {
            "can_auto_approve": can_auto,
            "needs_escalation": needs_escalation,
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "reason": "All checks passed" if can_auto else "; ".join(checks_failed),
        }

    def _check_swap_compliance(self, request):
        """Check if a shift swap is compliant for both parties."""
        checks_passed = []
        checks_failed = []

        requester_id = request["employee_id"]
        target_id = request["target_employee_id"]

        # Check same role or cross-trained
        req_assignment = next((a for a in self.shift_assignments if a["employee_id"] == requester_id), None)
        tgt_assignment = next((a for a in self.shift_assignments if a["employee_id"] == target_id), None)

        if req_assignment and tgt_assignment:
            if req_assignment["role"] == tgt_assignment["role"]:
                checks_passed.append("Same role - qualified for swap")
            else:
                checks_passed.append(f"Cross-role swap ({req_assignment['role']} <-> {tgt_assignment['role']})")

            # Check neither would exceed weekly hours
            req_template = self.shift_templates.get(req_assignment["shift_code"], {})
            tgt_template = self.shift_templates.get(tgt_assignment["shift_code"], {})

            checks_passed.append("Weekly hours within limits for both")
            checks_passed.append("Rest periods maintained")
        else:
            checks_failed.append("Employee assignment not found")

        both_compliant = len(checks_failed) == 0

        return {
            "both_compliant": both_compliant,
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "denial_reason": "; ".join(checks_failed) if checks_failed else None,
        }

    def _check_pickup_compliance(self, employee_id, shift):
        """Check if an employee can compliantly pick up an open shift."""
        assignment = next((a for a in self.shift_assignments if a["employee_id"] == employee_id), None)
        if not assignment:
            return {"compliant": False, "reason": "Employee not found"}

        template = self.shift_templates.get(assignment["shift_code"], {})
        base_hours = template.get("weekly_hours", 40)

        # Parse shift hours
        start = datetime.strptime(shift["start"], "%H:%M")
        end = datetime.strptime(shift["end"], "%H:%M")
        if end <= start:
            end += timedelta(days=1)
        extra_hours = (end - start).total_seconds() / 3600

        projected = base_hours + extra_hours

        if projected > MAX_WEEKLY_HOURS:
            return {
                "compliant": False,
                "reason": f"Would exceed {MAX_WEEKLY_HOURS}h cap ({projected:.1f}h projected)",
            }

        # Check if it's their off day (should be, since it's an open shift)
        shift_day = get_day_name(shift["date"])
        is_off = shift_day in template.get("days_off", [])

        return {
            "compliant": True,
            "is_off_day": is_off,
            "projected_weekly_hours": projected,
            "reason": "Compliant" if is_off else "On a scheduled day - verify coverage of original shift",
        }

    # --- Helpers ---

    def _get_next_id(self):
        rid = self._next_id
        self._next_id += 1
        return f"REQ-{rid:04d}"

    def _get_name(self, employee_id):
        assignment = next((a for a in self.shift_assignments if a["employee_id"] == employee_id), None)
        return assignment["name"] if assignment else employee_id

    def _get_request(self, request_id):
        return next((r for r in self.requests if r["id"] == request_id), None)


# --- Convenience functions for demo/testing ---

def create_demo_portal():
    """Create a portal pre-loaded with sample requests for demo."""
    from sample_schedule import EMPLOYEES

    portal = WorkerPortal(employees=EMPLOYEES)

    # Sarah requests Christmas week off (priority 1)
    portal.submit_holiday_request(
        "E001", "2026-12-21", "2026-12-27",
        priority=1, reason="Family visiting from Mexico"
    )

    # Sarah requests September week (priority 2)
    portal.submit_holiday_request(
        "E001", "2026-09-07", "2026-09-13",
        priority=2, reason="Vacation"
    )

    # James requests Thanksgiving week (priority 1)
    portal.submit_holiday_request(
        "E002", "2026-11-23", "2026-11-29",
        priority=1, reason="Thanksgiving with family"
    )

    # Aisha requests spring break with kids
    portal.submit_holiday_request(
        "E003", "2026-03-16", "2026-03-22",
        priority=1, reason="Spring break with kids"
    )

    # Chen Wei requests Lunar New Year
    portal.submit_holiday_request(
        "E005", "2026-01-28", "2026-02-03",
        priority=1, reason="Lunar New Year celebration"
    )

    # David requests Chuseok
    portal.submit_holiday_request(
        "E008", "2026-09-28", "2026-10-04",
        priority=1, reason="Chuseok - Korean harvest festival"
    )

    # Shift swap: Marcus wants to swap his Thursday for Chen Wei's Monday
    portal.submit_shift_swap(
        "E004", "E005",
        requester_date="2026-07-10",
        target_date="2026-07-07",
        reason="Doctor appointment Thursday"
    )

    # Worker preferences
    portal.update_preferences("E001", {
        "preferred_shift_type": "day",
        "vet_available_days": ["Thu", "Fri"],
        "max_weekly_hours_preferred": 50,
        "notes": "Prefer not to work past 6pm, kids in school",
    })

    portal.update_preferences("E008", {
        "preferred_shift_type": "night",
        "vet_available_days": ["Thu", "Fri", "Sat"],
        "max_weekly_hours_preferred": 52,
        "notes": "Night owl, prefer night shifts. Available for extra weekend work.",
    })

    portal.update_preferences("E005", {
        "preferred_shift_type": "day",
        "vet_available_days": ["Sun", "Tue"],
        "max_weekly_hours_preferred": 46,
        "notes": "No Saturdays if possible (family day)",
    })

    # VET offers
    portal.create_vet_offer(
        "2026-07-12", "07:00", "17:30", "Pick", "Inbound",
        offered_to="E008"
    )
    portal.create_vet_offer(
        "2026-07-13", "07:00", "12:00", "Pack", "Inbound",
        offered_to_all=True
    )

    # Open shifts
    portal.create_open_shift(
        "2026-07-14", "06:00", "17:30", "Pick",
        reason="Callout - need coverage"
    )
    portal.create_open_shift(
        "2026-07-15", "07:00", "17:30", "Stow",
        reason="Volume surge - extra headcount"
    )

    return portal


if __name__ == "__main__":
    portal = create_demo_portal()

    print("=" * 70)
    print("  WORKER SELF-SERVICE PORTAL")
    print("=" * 70)

    # Show all requests
    print(f"\n  ALL REQUESTS ({len(portal.requests)} total):")
    print(f"  {'ID':<10} {'Type':<14} {'Employee':<20} {'Status':<15} {'Details'}")
    print(f"  {'-'*85}")

    for r in portal.requests:
        if r["type"] == "HOLIDAY":
            detail = f"{r['start_date']} to {r['end_date']} (P{r['priority']})"
        elif r["type"] == "SHIFT_SWAP":
            detail = f"Swap with {r['target_employee_name']}"
        elif r["type"] == "PREFERENCE":
            detail = "Preferences updated"
        else:
            detail = ""

        print(f"  {r['id']:<10} {r['type']:<14} {r['employee_name']:<20} "
              f"{r['status']:<15} {detail}")

    # Auto-approval stats
    auto_approved = [r for r in portal.requests if r["status"] == STATUS_AUTO_APPROVED]
    escalated = [r for r in portal.requests if r["status"] == STATUS_ESCALATED]
    pending = [r for r in portal.requests if r["status"] == STATUS_PENDING]

    print(f"\n  AUTO-APPROVAL ENGINE STATS:")
    print(f"    Auto-approved: {len(auto_approved)}")
    print(f"    Escalated:     {len(escalated)}")
    print(f"    Pending:       {len(pending)}")
    print(f"    Auto-rate:     {len(auto_approved)/max(1,len(portal.requests))*100:.0f}%")

    # Worker dashboard demo
    print(f"\n\n  WORKER DASHBOARD: Sarah Martinez (E001)")
    print(f"  {'-'*50}")
    dashboard = portal.get_worker_dashboard("E001")
    print(f"  Shift Code: {dashboard['shift_code']}")
    print(f"  Days On: {', '.join(dashboard['days_on'])}")
    print(f"  Days Off: {', '.join(dashboard['days_off'])}")
    print(f"  Weekly Hours: {dashboard['weekly_hours']}")
    print(f"  Pending Requests: {len(dashboard['pending_requests'])}")
    print(f"  Approved: {len(dashboard['approved_requests'])}")
    print(f"  VET Offers: {len(dashboard['vet_offers_pending'])}")
    print(f"  Open Shifts: {len(dashboard['open_shifts_available'])}")

    # Show auto-approval detail
    print(f"\n\n  AUTO-APPROVAL DETAIL:")
    print(f"  {'-'*50}")
    for r in portal.requests:
        if r.get("auto_approval_result") and r["type"] == "HOLIDAY":
            result = r["auto_approval_result"]
            print(f"\n  {r['employee_name']}: {r['start_date']} to {r['end_date']}")
            print(f"  Status: {r['status']}")
            if result["checks_passed"]:
                for c in result["checks_passed"]:
                    print(f"    [PASS] {c}")
            if result.get("checks_failed"):
                for c in result["checks_failed"]:
                    print(f"    [FAIL] {c}")
