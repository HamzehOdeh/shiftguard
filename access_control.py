"""
Workforce Compliance AI - Access Control & Protected Request Override
Role-based permissions, protected request bypass, explainability logs,
human-override audit trail, and data visibility rules.
"""

from datetime import datetime
from collections import defaultdict


# Role definitions with permissions
ROLES = {
    "WORKER": {
        "name": "Worker / Associate",
        "can_view": ["own_schedule", "own_balances", "own_requests", "own_fairness_score",
                     "open_shifts", "vet_offers", "team_schedule_dates_only"],
        "can_action": ["submit_request", "update_preferences", "accept_vet",
                       "pickup_shift", "propose_swap", "report_sick", "donate_pto"],
        "cannot_view": ["other_employee_details", "other_balances", "other_leave_reasons",
                        "demographics", "pattern_alerts", "bias_audit", "manager_notes"],
        "cannot_action": ["approve_deny_requests", "override_algorithm", "view_all_data",
                          "modify_rules", "run_audit"],
    },
    "MANAGER": {
        "name": "Manager / Supervisor",
        "can_view": ["team_schedule", "team_balances", "team_requests", "team_fairness",
                     "coverage_gaps", "team_hours", "team_fatigue", "request_queue",
                     "auto_approval_log", "team_analytics"],
        "can_action": ["approve_deny_requests", "create_vet_offer", "post_open_shift",
                       "override_with_reason", "assign_coverage", "adjust_schedule"],
        "cannot_view": ["other_team_data", "demographics", "bias_audit_detail",
                        "medical_reasons", "ada_details", "salary_data"],
        "cannot_action": ["modify_compliance_rules", "access_demographics",
                          "run_bias_audit", "change_system_config"],
    },
    "HR": {
        "name": "HR / People Operations",
        "can_view": ["all_employee_data", "leave_records", "pattern_alerts",
                     "bias_audit_summary", "compliance_reports", "donation_records",
                     "fmla_records", "ada_accommodations", "grievances"],
        "can_action": ["process_fmla", "process_ada", "override_any_decision",
                       "run_bias_audit", "manage_leave_policies", "process_donations",
                       "handle_escalations", "configure_protected_requests"],
        "cannot_view": ["raw_demographic_data_without_audit_reason"],
        "cannot_action": ["modify_system_code", "delete_audit_trail"],
    },
    "ADMIN": {
        "name": "System Administrator",
        "can_view": ["system_config", "all_data", "audit_logs", "integration_status"],
        "can_action": ["modify_rules", "manage_users", "configure_system",
                       "manage_integrations", "export_data"],
        "cannot_view": ["medical_details_without_need"],
        "cannot_action": ["delete_audit_trail", "modify_past_records"],
    },
}

# Protected request types — BYPASS the fairness algorithm
PROTECTED_REQUEST_TYPES = {
    "RELIGIOUS_ACCOMMODATION": {
        "name": "Religious Accommodation",
        "legal_basis": "Title VII of Civil Rights Act",
        "bypass_fairness": True,
        "bypass_auction": True,
        "auto_approve": True,
        "requires_documentation": False,
        "cannot_deny_unless": "Undue hardship (employer must prove)",
        "override_coverage_minimum": False,
        "notification": "HR must be notified within 24h",
    },
    "ADA_ACCOMMODATION": {
        "name": "ADA / Disability Accommodation",
        "legal_basis": "Americans with Disabilities Act",
        "bypass_fairness": True,
        "bypass_auction": True,
        "auto_approve": False,  # requires interactive process
        "requires_documentation": True,
        "doc_type": "Medical certification or accommodation request",
        "cannot_deny_unless": "Undue hardship or direct threat (interactive process required)",
        "override_coverage_minimum": True,
        "notification": "HR must engage in interactive process",
        "process": [
            "Employee requests accommodation",
            "HR initiates interactive process",
            "Determine essential functions",
            "Identify reasonable accommodations",
            "Implement accommodation or document undue hardship",
        ],
    },
    "FMLA_PROTECTED": {
        "name": "FMLA Leave",
        "legal_basis": "Family and Medical Leave Act",
        "bypass_fairness": True,
        "bypass_auction": True,
        "auto_approve": True,
        "requires_documentation": True,
        "doc_type": "Medical certification (15 days to provide)",
        "cannot_deny_unless": "Employee ineligible (tenure/hours/employer size)",
        "override_coverage_minimum": True,
        "notification": "Eligibility notice within 5 business days",
    },
    "PREGNANCY_ACCOMMODATION": {
        "name": "Pregnancy Accommodation",
        "legal_basis": "Pregnant Workers Fairness Act (PWFA) + PDA",
        "bypass_fairness": True,
        "bypass_auction": True,
        "auto_approve": True,
        "requires_documentation": True,
        "doc_type": "Healthcare provider confirmation",
        "cannot_deny_unless": "Undue hardship (very high bar under PWFA)",
        "override_coverage_minimum": True,
        "notification": "HR immediate notification",
    },
    "MILITARY_LEAVE": {
        "name": "Military Leave (USERRA)",
        "legal_basis": "Uniformed Services Employment and Reemployment Rights Act",
        "bypass_fairness": True,
        "bypass_auction": True,
        "auto_approve": True,
        "requires_documentation": True,
        "doc_type": "Military orders",
        "cannot_deny_unless": "Not applicable - cannot deny",
        "override_coverage_minimum": True,
        "notification": "HR notification for reemployment rights tracking",
    },
    "DOMESTIC_VIOLENCE_LEAVE": {
        "name": "Domestic Violence / Safe Leave",
        "legal_basis": "State laws (IL, CA, NY, OR, etc.)",
        "bypass_fairness": True,
        "bypass_auction": True,
        "auto_approve": True,
        "requires_documentation": False,  # cannot require upfront
        "cannot_deny_unless": "Not applicable in covered states",
        "override_coverage_minimum": True,
        "notification": "Confidential - restricted to HR only",
        "confidential": True,
    },
    "JURY_DUTY": {
        "name": "Jury Duty",
        "legal_basis": "Federal + state jury duty protection laws",
        "bypass_fairness": True,
        "bypass_auction": True,
        "auto_approve": True,
        "requires_documentation": True,
        "doc_type": "Court summons",
        "cannot_deny_unless": "Not applicable - cannot deny",
        "override_coverage_minimum": True,
    },
    "VOTING_TIME": {
        "name": "Voting Time",
        "legal_basis": "State voting leave laws",
        "bypass_fairness": True,
        "bypass_auction": True,
        "auto_approve": True,
        "requires_documentation": False,
        "cannot_deny_unless": "Not applicable in most states",
        "override_coverage_minimum": False,
    },
}


class AccessControl:
    """Manage role-based access and enforce data visibility rules."""

    def __init__(self, org_hierarchy=None):
        self.user_roles = {}  # user_id -> role
        self.user_teams = {}  # user_id -> team/manager mapping (legacy)
        self.org = org_hierarchy  # Organization hierarchy object
        self.audit_log = []
        self.overrides = []

    def assign_role(self, user_id, role):
        """Assign a role to a user."""
        if role not in ROLES:
            return {"error": f"Invalid role: {role}"}
        self.user_roles[user_id] = role
        self.audit_log.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "user_id": user_id, "action": "ROLE_ASSIGNED", "detail": f"Role set to {role}",
        })
        return {"success": True, "role": role}

    def assign_team(self, manager_id, employee_ids):
        """Assign employees to a manager's team."""
        self.user_teams[manager_id] = employee_ids

    def check_permission(self, user_id, action, target_employee_id=None):
        """
        Check if a user has permission to perform an action.
        Returns: {allowed: bool, reason: str}
        """
        role = self.user_roles.get(user_id, "WORKER")
        role_def = ROLES.get(role, ROLES["WORKER"])

        # Check can_action
        if action in role_def.get("cannot_action", []):
            return {"allowed": False, "reason": f"Role '{role}' cannot perform '{action}'"}

        # For managers: check team scope
        if role == "MANAGER" and target_employee_id:
            team = self.user_teams.get(user_id, [])
            if target_employee_id not in team and target_employee_id != user_id:
                return {"allowed": False, "reason": "Employee not in your team"}

        # Workers can only act on themselves
        if role == "WORKER" and target_employee_id and target_employee_id != user_id:
            return {"allowed": False, "reason": "Workers can only manage their own data"}

        return {"allowed": True, "reason": "Permitted"}

    def check_view_permission(self, user_id, data_type, target_employee_id=None):
        """Check if a user can view specific data."""
        role = self.user_roles.get(user_id, "WORKER")
        role_def = ROLES.get(role, ROLES["WORKER"])

        if data_type in role_def.get("cannot_view", []):
            return {"allowed": False, "reason": f"Role '{role}' cannot view '{data_type}'"}

        if role == "WORKER" and target_employee_id and target_employee_id != user_id:
            return {"allowed": False, "reason": "Can only view own data"}

        if role == "MANAGER" and target_employee_id:
            team = self.user_teams.get(user_id, [])
            if target_employee_id not in team:
                return {"allowed": False, "reason": "Employee not in your team"}

        return {"allowed": True}

    def filter_data_for_role(self, user_id, data, data_type="schedule"):
        """Filter data based on user's role and permissions."""
        role = self.user_roles.get(user_id, "WORKER")

        if role == "ADMIN" or role == "HR":
            return data  # full access

        if role == "MANAGER":
            # Use hierarchy if available, otherwise legacy team list
            allowed_ids = self._get_visible_employee_ids(user_id)
            if isinstance(data, list):
                return [d for d in data if d.get("employee_id") in allowed_ids or d.get("worker_id") in allowed_ids]
            return data

        if role == "WORKER":
            if isinstance(data, list):
                return [d for d in data if d.get("employee_id") == user_id or d.get("worker_id") == user_id]
            return data

        return []

    # ============================================================
    # HIERARCHY-AWARE ACCESS (integrates with team_hierarchy.py)
    # ============================================================

    def get_visible_employees(self, user_id):
        """
        Get list of employees this user can see based on org hierarchy.

        - Worker: only themselves
        - Team Manager: their team members only
        - Department Head: all teams in their department
        - HR/Admin: everyone
        """
        role = self.user_roles.get(user_id, "WORKER")

        if role in ("ADMIN", "HR"):
            return self._get_all_employees()

        if role == "WORKER":
            return [user_id]

        # Manager: use hierarchy
        return self._get_visible_employee_ids(user_id)

    def get_visible_schedules(self, user_id, all_schedules):
        """Filter schedules to only what this user is allowed to see."""
        allowed_ids = set(self.get_visible_employees(user_id))

        return [
            s for s in all_schedules
            if s.get("employee_id", s.get("worker_id")) in allowed_ids
        ]

    def get_visible_leave_records(self, user_id, all_records):
        """Filter leave records to only what this user can see."""
        role = self.user_roles.get(user_id, "WORKER")
        allowed_ids = set(self.get_visible_employees(user_id))

        filtered = [r for r in all_records if r.get("employee_id") in allowed_ids]

        # Additional: managers can't see medical REASONS, only that leave exists
        if role == "MANAGER":
            for record in filtered:
                if record.get("leave_type") in ("FMLA", "SHORT_TERM_DISABILITY", "WORKERS_COMP"):
                    record = {**record, "reason": "[Medical - confidential]"}

        return filtered

    def get_visible_requests(self, user_id, all_requests):
        """Filter requests to only what this user can approve/see."""
        role = self.user_roles.get(user_id, "WORKER")

        if role in ("ADMIN", "HR"):
            return all_requests

        allowed_ids = set(self.get_visible_employees(user_id))

        if role == "WORKER":
            return [r for r in all_requests if r.get("employee_id") == user_id]

        return [r for r in all_requests if r.get("employee_id") in allowed_ids]

    def can_schedule_employee(self, manager_id, employee_id):
        """Check if a manager can schedule/modify a specific employee."""
        role = self.user_roles.get(manager_id, "WORKER")

        if role in ("ADMIN", "HR"):
            return {"allowed": True, "reason": "Full access"}

        if role == "WORKER":
            return {"allowed": False, "reason": "Workers cannot schedule others"}

        allowed = self._get_visible_employee_ids(manager_id)
        if employee_id in allowed:
            return {"allowed": True, "reason": "Employee is in your team/department"}

        return {
            "allowed": False,
            "reason": f"Employee {employee_id} is not in your team or department. "
                     f"Contact their manager or escalate to department head."
        }

    def get_access_summary(self, user_id):
        """Get a summary of what a user can see/do for display."""
        role = self.user_roles.get(user_id, "WORKER")
        visible = self.get_visible_employees(user_id)

        if self.org:
            scope = self.org.get_manager_scope(user_id)
            team_names = [t.name for t in scope.get("teams", [])]
            dept_names = [d.name for d in scope.get("departments", [])]
        else:
            team_names = []
            dept_names = []

        return {
            "user_id": user_id,
            "role": role,
            "visible_employees": len(visible),
            "teams": team_names,
            "departments": dept_names,
            "can_approve": role in ("MANAGER", "HR", "ADMIN"),
            "can_schedule": role in ("MANAGER", "HR", "ADMIN"),
            "can_view_all": role in ("HR", "ADMIN"),
            "can_run_audit": role in ("HR", "ADMIN"),
        }

    # ============================================================
    # LIVE FLOOR VIEW (read-only, cross-department)
    # ============================================================

    def get_live_floor_view(self, user_id, all_shifts, current_time=None):
        """
        Get who's currently on shift — visible to ANYONE in the same site.
        Shows: name, role, shift time, department. Nothing else.
        This is the digital equivalent of the nursing station whiteboard.

        Rules:
        - ANY employee can see who's on the floor right now (same site)
        - Only shows: name, role, department, current shift times
        - Does NOT show: hours worked, leave, fairness, schedule history
        - Purpose: "I need to find the charge nurse" or "who's the RT tonight?"
        """
        if current_time is None:
            current_time = datetime.now()
        elif isinstance(current_time, str):
            current_time = datetime.strptime(current_time, "%Y-%m-%d %H:%M")

        today = current_time.strftime("%Y-%m-%d")
        current_hour = current_time.hour

        # Find all shifts happening RIGHT NOW
        on_floor = []
        for shift in all_shifts:
            if shift.get("date") != today:
                continue

            start_str = shift.get("start", "00:00")
            end_str = shift.get("end", "23:59")
            start_h = int(start_str.split(":")[0])
            end_h = int(end_str.split(":")[0])

            # Handle overnight shifts
            if end_h < start_h:
                is_active = current_hour >= start_h or current_hour < end_h
            else:
                is_active = start_h <= current_hour < end_h

            if is_active:
                # Only expose minimal info
                on_floor.append({
                    "name": shift.get("name", shift.get("worker_name", "Unknown")),
                    "role": shift.get("role", "Staff"),
                    "shift": f"{start_str}-{end_str}",
                    "department": shift.get("department", self._get_employee_department(
                        shift.get("employee_id", shift.get("worker_id"))
                    )),
                })

        # Group by department/role for easy reading
        by_department = {}
        for person in on_floor:
            dept = person.get("department", "General")
            if dept not in by_department:
                by_department[dept] = []
            by_department[dept].append(person)

        return {
            "timestamp": current_time.strftime("%Y-%m-%d %H:%M"),
            "total_on_floor": len(on_floor),
            "staff_on_floor": on_floor,
            "by_department": by_department,
            "note": "Live view — names and roles only. For scheduling details, contact the team manager.",
        }

    def can_contact_employee(self, user_id, target_employee_id):
        """
        Check if a user can see contact info for another employee.
        Anyone on the same site can see name + role (for coordination).
        Only same-team manager can see personal contact details.
        """
        role = self.user_roles.get(user_id, "WORKER")

        # HR/Admin can always contact
        if role in ("HR", "ADMIN"):
            return {"allowed": True, "level": "full", "detail": "Full contact info (phone, email)"}

        # Manager of that employee: full contact
        allowed_ids = self._get_visible_employee_ids(user_id)
        if target_employee_id in allowed_ids:
            return {"allowed": True, "level": "full", "detail": "Full contact info (your team member)"}

        # Same site but different team: name + role only, contact via their manager
        return {
            "allowed": True,
            "level": "limited",
            "detail": "Name and role visible. For direct contact, reach out via their team manager or use the in-app messaging.",
        }

    def _get_employee_department(self, employee_id):
        """Get department name for an employee from hierarchy."""
        if not self.org or not employee_id:
            return "General"
        team = self.org.get_employee_team(employee_id)
        if team:
            return team.department.name
        return "General"

    # --- Private helpers ---

    def _get_visible_employee_ids(self, manager_id):
        """Get all employee IDs visible to a manager via hierarchy."""
        if self.org:
            scope = self.org.get_manager_scope(manager_id)
            return [e["id"] for e in scope.get("employees", [])]

        # Fallback to legacy team list
        return self.user_teams.get(manager_id, [])

    def _get_all_employees(self):
        """Get all employee IDs in the org."""
        if self.org:
            all_ids = []
            for team in self.org.get_all_teams():
                all_ids.extend([m["id"] for m in team.members])
            return all_ids
        return []

        return []


class ProtectedRequestHandler:
    """Handle protected requests that bypass normal approval flow."""

    def __init__(self):
        self.protected_requests = []
        self.audit_log = []

    def submit_protected_request(self, employee_id, request_type, details=None):
        """
        Submit a legally protected request. Bypasses fairness algorithm.
        """
        if request_type not in PROTECTED_REQUEST_TYPES:
            return {"error": f"Unknown protected type: {request_type}"}

        ptype = PROTECTED_REQUEST_TYPES[request_type]

        request = {
            "id": f"PROT-{len(self.protected_requests)+1:04d}",
            "employee_id": employee_id,
            "type": request_type,
            "type_name": ptype["name"],
            "legal_basis": ptype["legal_basis"],
            "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "details": details or {},
            "status": "APPROVED" if ptype["auto_approve"] else "PENDING_INTERACTIVE_PROCESS",
            "bypasses_fairness": ptype["bypass_fairness"],
            "bypasses_auction": ptype["bypass_auction"],
            "documentation_required": ptype["requires_documentation"],
            "documentation_received": False,
            "notifications_sent": [],
        }

        # Auto-approve if type allows
        if ptype["auto_approve"]:
            request["approved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            request["approved_by"] = "SYSTEM (legally protected - auto-approved)"
            self._log(employee_id, request_type, "AUTO_APPROVED",
                     f"Protected under {ptype['legal_basis']}")

        # Trigger notifications
        if ptype.get("notification"):
            request["notifications_sent"].append({
                "to": "HR",
                "message": ptype["notification"],
                "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })

        self.protected_requests.append(request)
        return request

    def get_protected_requests(self, employee_id=None):
        """Get protected requests, optionally filtered by employee."""
        if employee_id:
            return [r for r in self.protected_requests if r["employee_id"] == employee_id]
        return self.protected_requests

    def is_request_protected(self, request):
        """Check if a request qualifies for protected status."""
        # Check if the leave type or reason maps to a protected category
        leave_type = request.get("leave_type", request.get("type", ""))
        reason = request.get("reason", "").lower()

        # Direct mappings
        type_mappings = {
            "FMLA": "FMLA_PROTECTED",
            "FMLA_INTERMITTENT": "FMLA_PROTECTED",
            "MILITARY": "MILITARY_LEAVE",
            "JURY_DUTY": "JURY_DUTY",
            "VOTING": "VOTING_TIME",
            "MATERNITY": "PREGNANCY_ACCOMMODATION",
            "RELIGIOUS": "RELIGIOUS_ACCOMMODATION",
        }

        if leave_type in type_mappings:
            return {"protected": True, "type": type_mappings[leave_type]}

        # Reason-based detection
        religious_keywords = ["church", "mosque", "temple", "synagogue", "prayer",
                            "sabbath", "eid", "diwali", "christmas mass", "yom kippur",
                            "ramadan", "religious"]
        if any(kw in reason for kw in religious_keywords):
            return {"protected": True, "type": "RELIGIOUS_ACCOMMODATION"}

        return {"protected": False}

    def _log(self, employee_id, request_type, action, reason):
        self.audit_log.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "employee_id": employee_id,
            "request_type": request_type,
            "action": action,
            "reason": reason,
        })


class ExplainabilityLog:
    """Log every automated decision with human-readable explanation."""

    def __init__(self):
        self.entries = []

    def log_decision(self, decision_type, employee_id, outcome, explanation,
                     factors=None, overrideable=True):
        """
        Log an automated decision with full explainability.
        Every decision must be understandable by a non-technical HR person.
        """
        entry = {
            "id": f"DEC-{len(self.entries)+1:06d}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "decision_type": decision_type,
            "employee_id": employee_id,
            "outcome": outcome,
            "explanation": explanation,
            "factors_considered": factors or [],
            "overrideable": overrideable,
            "overridden": False,
            "override_by": None,
            "override_reason": None,
        }
        self.entries.append(entry)
        return entry

    def override_decision(self, decision_id, overrider_id, reason):
        """Human override of an automated decision."""
        entry = next((e for e in self.entries if e["id"] == decision_id), None)
        if not entry:
            return {"error": "Decision not found"}
        if not entry["overrideable"]:
            return {"error": "This decision cannot be overridden (legally protected)"}

        entry["overridden"] = True
        entry["override_by"] = overrider_id
        entry["override_reason"] = reason
        entry["override_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return {"success": True, "decision": entry}

    def get_decisions(self, employee_id=None, decision_type=None, overridden_only=False):
        """Query the decision log."""
        results = self.entries
        if employee_id:
            results = [e for e in results if e["employee_id"] == employee_id]
        if decision_type:
            results = [e for e in results if e["decision_type"] == decision_type]
        if overridden_only:
            results = [e for e in results if e["overridden"]]
        return results

    def get_explanation_for_employee(self, decision_id):
        """Get worker-facing explanation (filtered, no internal notes)."""
        entry = next((e for e in self.entries if e["id"] == decision_id), None)
        if not entry:
            return None

        return {
            "decision": entry["decision_type"],
            "outcome": entry["outcome"],
            "explanation": entry["explanation"],
            "can_appeal": entry["overrideable"],
        }


# ============================================================
# DISCLAIMER SYSTEM
# ============================================================

LEGAL_DISCLAIMERS = {
    "compliance_output": (
        "DISCLAIMER: This compliance analysis is for informational purposes only and does not "
        "constitute legal advice. Labor laws vary by jurisdiction and change frequently. "
        "Always consult qualified employment counsel for specific compliance questions. "
        "The system operator remains solely responsible for all scheduling decisions."
    ),
    "auto_approval": (
        "This request was processed automatically based on configured rules. "
        "All automated decisions are subject to human review and override. "
        "The employer retains full responsibility for compliance."
    ),
    "bias_audit": (
        "This bias audit uses the four-fifths (80%) rule as defined by EEOC Uniform Guidelines. "
        "Statistical results should be reviewed by qualified professionals. "
        "Passing the audit does not guarantee absence of discrimination."
    ),
    "fairness_algorithm": (
        "The fairness algorithm considers multiple factors including workload distribution, "
        "seniority, historical assignments, and employee preferences. No algorithm can guarantee "
        "perfect fairness. All decisions are subject to human override and legal requirements "
        "take precedence over algorithmic outputs."
    ),
}


if __name__ == "__main__":
    print("=" * 70)
    print("  ACCESS CONTROL & PROTECTED REQUEST SYSTEM")
    print("=" * 70)

    # Setup access control
    ac = AccessControl()
    ac.assign_role("E001", "WORKER")
    ac.assign_role("MGR01", "MANAGER")
    ac.assign_role("HR01", "HR")
    ac.assign_team("MGR01", ["E001", "E002", "E003", "E004", "E005"])

    # Test permissions
    print("\n  PERMISSION CHECKS:")
    tests = [
        ("E001", "submit_request", None),
        ("E001", "approve_deny_requests", None),
        ("E001", "submit_request", "E002"),  # worker acting on other
        ("MGR01", "approve_deny_requests", "E001"),  # manager on own team
        ("MGR01", "approve_deny_requests", "E009"),  # manager on other team
        ("HR01", "run_bias_audit", None),
    ]
    for user, action, target in tests:
        result = ac.check_permission(user, action, target)
        status = "ALLOWED" if result["allowed"] else "DENIED"
        print(f"  {user} -> {action}" + (f" (on {target})" if target else "") +
              f": {status} ({result['reason']})")

    # Protected requests
    print(f"\n\n  PROTECTED REQUEST HANDLING:")
    handler = ProtectedRequestHandler()

    # Religious accommodation
    result = handler.submit_protected_request(
        "E009", "RELIGIOUS_ACCOMMODATION",
        {"dates": "2026-03-20 to 2026-03-22", "reason": "Eid al-Fitr"}
    )
    print(f"  Fatima (E009) - Religious: {result['status']} (bypasses fairness: {result['bypasses_fairness']})")

    # ADA accommodation
    result = handler.submit_protected_request(
        "E004", "ADA_ACCOMMODATION",
        {"accommodation": "Modified schedule - no shifts > 8 hours", "reason": "Medical condition"}
    )
    print(f"  Marcus (E004) - ADA: {result['status']} (requires interactive process)")

    # FMLA
    result = handler.submit_protected_request(
        "E003", "FMLA_PROTECTED",
        {"dates": "2026-07-07 to 2026-07-18", "reason": "Family medical"}
    )
    print(f"  Aisha (E003) - FMLA: {result['status']} (legally cannot deny)")

    # Explainability log
    print(f"\n\n  EXPLAINABILITY LOG:")
    elog = ExplainabilityLog()

    elog.log_decision(
        "SHIFT_ASSIGNMENT", "E001", "ASSIGNED_TO_NIGHT",
        "Assigned to night shift because Sarah has the fewest night shifts this month (2 vs team avg 4).",
        factors=["night_shift_count: 2", "team_average: 4", "fairness_score: highest"]
    )

    elog.log_decision(
        "PTO_DENIAL", "E004", "DENIED",
        "PTO request denied because shift code DB1-0700-IB requires minimum 1 person and Marcus is the only one assigned. Coverage must be arranged first.",
        factors=["shift_code_headcount: 1", "coverage_available: none", "blackout: no"],
        overrideable=True
    )

    for e in elog.entries:
        print(f"  [{e['id']}] {e['decision_type']}: {e['outcome']}")
        print(f"    Explanation: {e['explanation'][:80]}...")
        print(f"    Can override: {e['overrideable']}")
        print()

    # Legal disclaimers
    print(f"\n  LEGAL DISCLAIMERS (auto-attached to outputs):")
    for key, text in LEGAL_DISCLAIMERS.items():
        print(f"\n  [{key}]:")
        print(f"    {text[:100]}...")
