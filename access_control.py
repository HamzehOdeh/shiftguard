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

    def __init__(self):
        self.user_roles = {}  # user_id -> role
        self.user_teams = {}  # user_id -> team/manager mapping
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
            team = self.user_teams.get(user_id, [])
            if isinstance(data, list):
                return [d for d in data if d.get("employee_id") in team or d.get("worker_id") in team]
            return data

        if role == "WORKER":
            if isinstance(data, list):
                return [d for d in data if d.get("employee_id") == user_id or d.get("worker_id") == user_id]
            return data

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
