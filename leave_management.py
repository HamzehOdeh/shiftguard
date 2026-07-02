"""
Workforce Compliance AI - Comprehensive Leave Management Engine
All leave types, accrual tracking, balance management, documentation requirements,
pattern detection, FMLA triggers, return-to-work, and cascading coverage automation.
"""

from datetime import datetime, timedelta
from collections import defaultdict


# ============================================================
# LEAVE TYPE DEFINITIONS
# ============================================================

LEAVE_TYPES = {
    "PTO": {
        "name": "Paid Time Off / Vacation",
        "planned": True,
        "documentation_required": False,
        "approval_method": "priority_system",
        "accrual_based": True,
        "protected": False,
        "min_notice_days": 14,
        "max_consecutive_days": 14,
        "can_be_denied": True,
    },
    "SICK_PLANNED": {
        "name": "Sick Leave (Planned Medical)",
        "planned": True,
        "documentation_required": True,
        "doc_type": "doctor_note",
        "doc_required_after_days": 3,
        "approval_method": "auto_approve",
        "accrual_based": True,
        "protected": True,
        "min_notice_days": 0,
        "can_be_denied": False,
    },
    "SICK_UNPLANNED": {
        "name": "Sick Leave (Unplanned / Callout)",
        "planned": False,
        "documentation_required": True,
        "doc_type": "doctor_note",
        "doc_required_after_days": 3,
        "approval_method": "auto_register",
        "accrual_based": True,
        "protected": True,
        "min_notice_days": 0,
        "can_be_denied": False,
    },
    "FMLA": {
        "name": "Family and Medical Leave Act",
        "planned": None,  # can be either
        "documentation_required": True,
        "doc_type": "medical_certification",
        "doc_deadline_days": 15,
        "approval_method": "auto_protected",
        "accrual_based": False,
        "entitlement_hours": 480,  # 12 weeks x 40 hrs
        "protected": True,
        "job_protected": True,
        "min_notice_days": 30,  # when foreseeable
        "can_be_denied": False,
        "eligibility": {
            "months_employed": 12,
            "hours_worked": 1250,
            "employer_size": 50,
        },
    },
    "FMLA_INTERMITTENT": {
        "name": "FMLA (Intermittent / Reduced Schedule)",
        "planned": True,
        "documentation_required": True,
        "doc_type": "medical_certification",
        "approval_method": "auto_protected",
        "accrual_based": False,
        "entitlement_hours": 480,
        "protected": True,
        "job_protected": True,
        "can_be_denied": False,
        "max_days_per_month": None,  # set per certification
    },
    "BEREAVEMENT": {
        "name": "Bereavement Leave",
        "planned": False,
        "documentation_required": False,
        "doc_type": "death_certificate_or_obituary",
        "doc_required_after_days": 5,
        "approval_method": "auto_approve",
        "accrual_based": False,
        "entitlement_days": {"immediate_family": 5, "extended_family": 3},
        "protected": True,
        "min_notice_days": 0,
        "can_be_denied": False,
    },
    "JURY_DUTY": {
        "name": "Jury Duty",
        "planned": False,
        "documentation_required": True,
        "doc_type": "summons",
        "approval_method": "auto_approve",
        "accrual_based": False,
        "protected": True,
        "paid": True,  # varies by state
        "min_notice_days": 0,
        "can_be_denied": False,
    },
    "MILITARY": {
        "name": "Military Leave (USERRA)",
        "planned": None,
        "documentation_required": True,
        "doc_type": "military_orders",
        "approval_method": "auto_protected",
        "accrual_based": False,
        "protected": True,
        "job_protected": True,
        "max_years": 5,
        "can_be_denied": False,
    },
    "MATERNITY": {
        "name": "Maternity / Paternity / Parental Leave",
        "planned": True,
        "documentation_required": True,
        "doc_type": "medical_certification",
        "approval_method": "auto_protected",
        "accrual_based": False,
        "protected": True,
        "job_protected": True,
        "entitlement_weeks": 12,  # FMLA minimum, state may be more
        "can_be_denied": False,
    },
    "SHORT_TERM_DISABILITY": {
        "name": "Short-Term Disability",
        "planned": False,
        "documentation_required": True,
        "doc_type": "medical_certification",
        "approval_method": "auto_protected",
        "accrual_based": False,
        "protected": True,
        "max_weeks": 26,
        "paid": True,  # via insurance
        "pay_percentage": 0.6,
        "can_be_denied": False,
    },
    "WORKERS_COMP": {
        "name": "Workers' Compensation",
        "planned": False,
        "documentation_required": True,
        "doc_type": "incident_report",
        "approval_method": "auto_protected",
        "accrual_based": False,
        "protected": True,
        "requires_clearance_to_return": True,
        "can_be_denied": False,
    },
    "PERSONAL_UNPAID": {
        "name": "Personal Leave (Unpaid)",
        "planned": True,
        "documentation_required": False,
        "approval_method": "manager_approval",
        "accrual_based": False,
        "protected": False,
        "min_notice_days": 14,
        "max_days": 30,
        "can_be_denied": True,
    },
    "RELIGIOUS": {
        "name": "Religious Observance",
        "planned": True,
        "documentation_required": False,
        "approval_method": "auto_approve",
        "accrual_based": False,
        "protected": True,
        "accommodation_required": True,
        "can_be_denied": False,
    },
    "VOTING": {
        "name": "Voting Time",
        "planned": True,
        "documentation_required": False,
        "approval_method": "auto_approve",
        "accrual_based": False,
        "protected": True,
        "max_hours": 4,  # varies by state: 2-4 hrs
        "paid": True,
        "can_be_denied": False,
    },
    "UPT": {
        "name": "Unpaid Time (Partial Day)",
        "planned": False,
        "documentation_required": False,
        "approval_method": "self_service",
        "accrual_based": True,
        "protected": False,
        "min_notice_days": 0,
        "deducted_from": "upt_balance",
        "can_be_denied": False,
        "zero_balance_consequence": "termination_review",
    },
}

# State-specific accrual rates
ACCRUAL_RATES = {
    "California": {"sick": {"rate": 1/30, "cap": 80, "min_annual": 40, "carryover_cap": 80}},
    "Illinois": {"sick": {"rate": 1/40, "cap": 40, "carryover_cap": 40}},
    "New York": {"sick": {"rate": 1/30, "cap_large": 56, "cap_small": 40}},
    "Oregon": {"sick": {"rate": 1/30, "cap": 40, "carryover_cap": 40}},
    "Washington": {"sick": {"rate": 1/40, "cap": None, "carryover_cap": None}},
    "Colorado": {"sick": {"rate": 1/30, "cap": 48, "carryover_cap": 48}},
    "Michigan": {"sick": {"rate": 1/35, "cap": 40, "carryover_cap": 40}},
}

# Default PTO accrual schedule (by tenure)
PTO_ACCRUAL_SCHEDULE = [
    {"min_years": 0, "max_years": 1, "hours_per_year": 80},    # 2 weeks
    {"min_years": 1, "max_years": 3, "hours_per_year": 120},   # 3 weeks
    {"min_years": 3, "max_years": 5, "hours_per_year": 160},   # 4 weeks
    {"min_years": 5, "max_years": 99, "hours_per_year": 200},  # 5 weeks
]

# UPT default allocation
UPT_QUARTERLY_GRANT = 20  # hours per quarter


# ============================================================
# LEAVE BALANCE TRACKER
# ============================================================

class LeaveBalanceTracker:
    """Track leave balances, accruals, and usage for all employees."""

    def __init__(self, state="Illinois"):
        self.state = state
        self.balances = {}
        self.transactions = []
        self.leave_records = []
        self.documentation = {}
        self.patterns = defaultdict(list)
        self.alerts = []

    def initialize_employee(self, employee_id, hire_date, hours_worked_ytd=0):
        """Set up initial balances for an employee."""
        if isinstance(hire_date, str):
            hire_date = datetime.strptime(hire_date, "%Y-%m-%d")

        tenure_years = (datetime.now() - hire_date).days / 365.25

        # PTO based on tenure
        pto_annual = 80
        for tier in PTO_ACCRUAL_SCHEDULE:
            if tier["min_years"] <= tenure_years < tier["max_years"]:
                pto_annual = tier["hours_per_year"]
                break

        # Sick leave accrual based on state
        state_rules = ACCRUAL_RATES.get(self.state, ACCRUAL_RATES["Illinois"])
        sick_rate = state_rules["sick"]["rate"]
        sick_cap = state_rules["sick"].get("cap", 40)
        sick_accrued = min(sick_cap or 999, hours_worked_ytd * sick_rate)

        # FMLA eligibility
        fmla_eligible = tenure_years >= 1 and hours_worked_ytd >= 1250

        # PTO breakdown: flex vs standard
        flex_pct = 0.25  # 25% of PTO is flex (can be used in smaller increments)
        standard_pct = 0.75
        pto_available = round(pto_annual * 0.5, 1)  # mid-year estimate
        flex_available = round(pto_available * flex_pct, 1)
        standard_available = round(pto_available * standard_pct, 1)

        self.balances[employee_id] = {
            "employee_id": employee_id,
            "hire_date": hire_date.strftime("%Y-%m-%d"),
            "tenure_years": round(tenure_years, 1),
            "state": self.state,
            "pto": {
                "available": pto_available,
                "flex_available": flex_available,
                "standard_available": standard_available,
                "used": 0,
                "flex_used": 0,
                "standard_used": 0,
                "accrual_rate_per_year": pto_annual,
                "pending": 0,
                "carryover_cap": round(pto_annual * 1.5, 1),  # typical cap = 1.5x annual
            },
            "sick": {
                "available": round(sick_accrued, 1),
                "used": 0,
                "accrual_rate": sick_rate,
                "cap": sick_cap,
            },
            "upt": {
                "available": UPT_QUARTERLY_GRANT,
                "used": 0,
                "quarterly_grant": UPT_QUARTERLY_GRANT,
            },
            "fmla": {
                "eligible": fmla_eligible,
                "available_hours": 480 if fmla_eligible else 0,
                "used_hours": 0,
                "year_start": datetime.now().strftime("%Y-01-01"),
            },
            "bereavement": {
                "immediate_family_days": 5,
                "extended_family_days": 3,
                "used_this_year": 0,
            },
            "donated": {
                "received_hours": 0,
                "donated_hours": 0,
                "received_from": [],
                "donated_to": [],
            },
        }
        return self.balances[employee_id]

    def get_balance(self, employee_id):
        """Get current leave balances for an employee."""
        return self.balances.get(employee_id, None)

    def get_balance_summary(self, employee_id):
        """Get a worker-friendly balance summary with PTO breakdown and at-risk hours."""
        bal = self.balances.get(employee_id)
        if not bal:
            return None

        warnings = []
        if bal["upt"]["available"] <= 4:
            warnings.append(f"UPT LOW: Only {bal['upt']['available']}h remaining")
        if bal["pto"]["available"] <= 8:
            warnings.append(f"PTO LOW: Only {bal['pto']['available']}h remaining")

        # Calculate at-risk hours (won't carry over at year-end)
        at_risk = self._calculate_at_risk_hours(employee_id)
        if at_risk["pto_at_risk"] > 0:
            warnings.append(
                f"AT RISK: {at_risk['pto_at_risk']}h PTO will NOT carry over after "
                f"{at_risk['year_end']} (state: {bal['state']}). Use by then or lose it."
            )
        if at_risk["sick_at_risk"] > 0:
            warnings.append(
                f"SICK AT RISK: {at_risk['sick_at_risk']}h sick leave exceeds carryover cap. "
                f"Use {at_risk['sick_at_risk']}h before year-end."
            )

        return {
            "pto_hours": bal["pto"]["available"],
            "pto_days": round(bal["pto"]["available"] / 8, 1),
            "pto_flex_hours": bal["pto"].get("flex_available", 0),
            "pto_standard_hours": bal["pto"].get("standard_available", 0),
            "pto_flex_days": round(bal["pto"].get("flex_available", 0) / 8, 1),
            "pto_standard_days": round(bal["pto"].get("standard_available", 0) / 8, 1),
            "sick_hours": bal["sick"]["available"],
            "sick_days": round(bal["sick"]["available"] / 8, 1),
            "upt_hours": bal["upt"]["available"],
            "fmla_eligible": bal["fmla"]["eligible"],
            "fmla_hours_remaining": bal["fmla"]["available_hours"] - bal["fmla"]["used_hours"],
            "fmla_weeks_remaining": round(
                (bal["fmla"]["available_hours"] - bal["fmla"]["used_hours"]) / 40, 1
            ),
            "at_risk": at_risk,
            "warnings": warnings,
            "days_until_year_end": at_risk["days_until_year_end"],
        }

    def _calculate_at_risk_hours(self, employee_id):
        """
        Calculate hours at risk of being lost at year-end based on state law.
        - California/Illinois/Colorado: NO use-it-or-lose-it (PTO never expires)
        - Michigan/Oregon/New York: use-it-or-lose-it allowed with written policy
        - Sick leave: may have carryover caps
        """
        bal = self.balances.get(employee_id)
        if not bal:
            return {"pto_at_risk": 0, "sick_at_risk": 0}

        state = bal["state"]
        year_end = f"{datetime.now().year}-12-31"
        days_left = (datetime.strptime(year_end, "%Y-%m-%d") - datetime.now()).days

        # PTO at-risk depends on state
        # States where PTO CANNOT be forfeited (no at-risk)
        no_forfeit_states = {"California", "Illinois", "Colorado"}

        pto_at_risk = 0
        if state not in no_forfeit_states:
            # Use-it-or-lose-it states: anything above carryover cap is at risk
            carryover_cap = bal["pto"].get("carryover_cap", bal["pto"]["accrual_rate_per_year"])
            if bal["pto"]["available"] > carryover_cap:
                pto_at_risk = round(bal["pto"]["available"] - carryover_cap, 1)

        # Sick leave at-risk (carryover cap)
        sick_at_risk = 0
        state_rules = ACCRUAL_RATES.get(state, {})
        sick_rules = state_rules.get("sick", {})
        sick_carryover_cap = sick_rules.get("carryover_cap")

        if sick_carryover_cap and bal["sick"]["available"] > sick_carryover_cap:
            sick_at_risk = round(bal["sick"]["available"] - sick_carryover_cap, 1)

        return {
            "pto_at_risk": pto_at_risk,
            "sick_at_risk": sick_at_risk,
            "year_end": year_end,
            "days_until_year_end": max(0, days_left),
            "state": state,
            "state_rule": "No forfeiture" if state in no_forfeit_states else "Use-it-or-lose-it (with policy)",
            "pto_carryover_cap": bal["pto"].get("carryover_cap", "Unlimited"),
            "sick_carryover_cap": sick_carryover_cap or "Unlimited",
            "recommendation": self._at_risk_recommendation(pto_at_risk, sick_at_risk, days_left),
        }

    def _at_risk_recommendation(self, pto_at_risk, sick_at_risk, days_left):
        """Generate recommendation for at-risk hours."""
        if pto_at_risk == 0 and sick_at_risk == 0:
            return "No hours at risk. Your state protects accrued time."

        parts = []
        if pto_at_risk > 0:
            days_needed = max(1, int(pto_at_risk / 8))
            parts.append(f"Schedule {days_needed} PTO day(s) before year-end to avoid losing {pto_at_risk}h")
        if sick_at_risk > 0:
            parts.append(f"{sick_at_risk}h sick exceeds carryover cap")

        if days_left < 60 and pto_at_risk > 0:
            parts.append("URGENT: Less than 60 days remaining")

        return ". ".join(parts)

    def record_leave(self, employee_id, leave_type, start_date, end_date,
                     hours=None, reason="", documentation=None):
        """
        Record a leave event. Deducts from balance, checks eligibility,
        triggers alerts (FMLA notification, pattern detection, etc.)
        """
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        days = (end_date - start_date).days + 1
        if hours is None:
            hours = days * 8  # default to 8-hour days

        bal = self.balances.get(employee_id)
        if not bal:
            return {"error": "Employee not initialized"}

        leave_def = LEAVE_TYPES.get(leave_type)
        if not leave_def:
            return {"error": f"Unknown leave type: {leave_type}"}

        record = {
            "id": f"LV-{len(self.leave_records)+1:04d}",
            "employee_id": employee_id,
            "leave_type": leave_type,
            "leave_name": leave_def["name"],
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "days": days,
            "hours": hours,
            "reason": reason,
            "status": "ACTIVE",
            "documentation_status": "NOT_REQUIRED",
            "documentation_due": None,
            "recorded_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "alerts_triggered": [],
            "return_clearance_required": leave_def.get("requires_clearance_to_return", False),
            "return_clearance_received": False,
        }

        # Deduct from balance
        deduction_result = self._deduct_balance(employee_id, leave_type, hours)
        record["balance_deduction"] = deduction_result

        # Check documentation requirements
        doc_result = self._check_documentation(leave_type, days, documentation)
        record["documentation_status"] = doc_result["status"]
        record["documentation_due"] = doc_result.get("due_date")

        # Check for FMLA trigger
        fmla_alert = self._check_fmla_trigger(employee_id, leave_type, days)
        if fmla_alert:
            record["alerts_triggered"].append(fmla_alert)
            self.alerts.append(fmla_alert)

        # Pattern detection
        pattern_alert = self._detect_patterns(employee_id, leave_type, start_date)
        if pattern_alert:
            record["alerts_triggered"].append(pattern_alert)
            self.alerts.append(pattern_alert)

        # Record the transaction
        self.leave_records.append(record)
        self.patterns[employee_id].append({
            "type": leave_type,
            "date": start_date.strftime("%Y-%m-%d"),
            "day_of_week": start_date.strftime("%A"),
        })

        return record

    def report_sick_today(self, employee_id, hours=None, reason="Not feeling well"):
        """Quick action: report sick for today."""
        today = datetime.now()
        if hours is None:
            hours = 8  # full day default

        return self.record_leave(
            employee_id, "SICK_UNPLANNED",
            today.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"),
            hours=hours, reason=reason
        )

    def process_accrual(self, employee_id, hours_worked):
        """Process accrual for hours worked (called periodically)."""
        bal = self.balances.get(employee_id)
        if not bal:
            return

        state_rules = ACCRUAL_RATES.get(self.state, ACCRUAL_RATES["Illinois"])
        sick_rate = state_rules["sick"]["rate"]
        sick_cap = state_rules["sick"].get("cap")

        # Accrue sick leave
        accrued = hours_worked * sick_rate
        new_sick = bal["sick"]["available"] + accrued
        if sick_cap:
            new_sick = min(sick_cap, new_sick)
        bal["sick"]["available"] = round(new_sick, 2)

        return {"sick_accrued": round(accrued, 2), "new_balance": bal["sick"]["available"]}

    def process_quarterly_upt_grant(self, employee_id):
        """Grant quarterly UPT allocation."""
        bal = self.balances.get(employee_id)
        if not bal:
            return
        bal["upt"]["available"] += UPT_QUARTERLY_GRANT
        return {"upt_granted": UPT_QUARTERLY_GRANT, "new_balance": bal["upt"]["available"]}

    # ============================================================
    # PTO / HOLIDAY DONATION SYSTEM
    # ============================================================

    def donate_hours(self, donor_id, recipient_id, hours, leave_type="PTO", reason=""):
        """
        Donate PTO/sick hours from one employee to another.

        Rules:
        - Donor must retain minimum 40h PTO after donation (protect the donor)
        - Recipient must have exhausted own balance of that type OR have qualifying event
        - Max single donation: 40 hours
        - Tracks all donations for audit/tax purposes
        """
        donor_bal = self.balances.get(donor_id)
        recip_bal = self.balances.get(recipient_id)

        if not donor_bal or not recip_bal:
            return {"error": "Employee not found", "success": False}

        # Validation
        errors = []
        min_donor_retain = 40  # must keep at least 40h PTO
        max_single_donation = 40

        if hours > max_single_donation:
            errors.append(f"Max single donation is {max_single_donation}h")

        if hours <= 0:
            errors.append("Donation must be positive")

        if leave_type == "PTO":
            donor_available = donor_bal["pto"]["available"]
            if donor_available - hours < min_donor_retain:
                errors.append(
                    f"Donor must retain {min_donor_retain}h PTO. "
                    f"Current: {donor_available}h. Max donatable: {donor_available - min_donor_retain}h"
                )
        elif leave_type == "SICK":
            donor_available = donor_bal["sick"]["available"]
            if donor_available - hours < 16:  # keep at least 16h sick
                errors.append(f"Donor must retain at least 16h sick leave")
        else:
            errors.append(f"Cannot donate {leave_type} type leave")

        if errors:
            return {"error": "; ".join(errors), "success": False}

        # Process donation
        if leave_type == "PTO":
            donor_bal["pto"]["available"] -= hours
            recip_bal["pto"]["available"] += hours
        elif leave_type == "SICK":
            donor_bal["sick"]["available"] -= hours
            recip_bal["sick"]["available"] += hours

        # Track
        donation_record = {
            "id": f"DON-{len(self.transactions)+1:04d}",
            "donor_id": donor_id,
            "recipient_id": recipient_id,
            "hours": hours,
            "leave_type": leave_type,
            "reason": reason,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "status": "COMPLETED",
            "tax_note": "Donated leave may be taxable to recipient per IRS guidance",
        }

        donor_bal["donated"]["donated_hours"] += hours
        donor_bal["donated"]["donated_to"].append({
            "to": recipient_id, "hours": hours, "date": donation_record["timestamp"][:10]
        })
        recip_bal["donated"]["received_hours"] += hours
        recip_bal["donated"]["received_from"].append({
            "from": donor_id, "hours": hours, "date": donation_record["timestamp"][:10]
        })

        self.transactions.append(donation_record)

        return {
            "success": True,
            "donation": donation_record,
            "donor_new_balance": donor_bal["pto"]["available"] if leave_type == "PTO" else donor_bal["sick"]["available"],
            "recipient_new_balance": recip_bal["pto"]["available"] if leave_type == "PTO" else recip_bal["sick"]["available"],
        }

    def donate_to_pool(self, donor_id, hours, leave_type="PTO"):
        """Donate hours to the company-wide leave sharing pool."""
        # Ensure pool exists
        if "__POOL__" not in self.balances:
            self.balances["__POOL__"] = {
                "employee_id": "__POOL__",
                "hire_date": "2020-01-01",
                "tenure_years": 0,
                "state": self.state,
                "pto": {"available": 0, "flex_available": 0, "standard_available": 0,
                        "used": 0, "flex_used": 0, "standard_used": 0,
                        "accrual_rate_per_year": 0, "pending": 0, "carryover_cap": 99999},
                "sick": {"available": 0, "used": 0, "accrual_rate": 0, "cap": None},
                "upt": {"available": 0, "used": 0, "quarterly_grant": 0},
                "fmla": {"eligible": False, "available_hours": 0, "used_hours": 0},
                "bereavement": {"immediate_family_days": 0, "extended_family_days": 0, "used_this_year": 0},
                "donated": {"received_hours": 0, "donated_hours": 0, "received_from": [], "donated_to": []},
            }
        return self.donate_hours(donor_id, "__POOL__", hours, leave_type, reason="Pool donation")

    def request_from_pool(self, recipient_id, hours, reason=""):
        """
        Request hours from the company leave pool.
        Requires: own balance exhausted + qualifying event.
        """
        recip_bal = self.balances.get(recipient_id)
        if not recip_bal:
            return {"error": "Employee not found", "success": False}

        # Check eligibility: own PTO must be exhausted
        if recip_bal["pto"]["available"] > 8:
            return {
                "error": f"Must exhaust own PTO first. You have {recip_bal['pto']['available']}h remaining.",
                "success": False,
            }

        # Check pool balance
        pool_bal = self.balances.get("__POOL__")
        if not pool_bal:
            # Initialize pool if needed
            self.balances["__POOL__"] = {
                "employee_id": "__POOL__",
                "pto": {"available": 0},
                "sick": {"available": 0},
                "donated": {"received_hours": 0, "donated_hours": 0, "received_from": [], "donated_to": []},
            }
            pool_bal = self.balances["__POOL__"]

        if pool_bal["pto"]["available"] < hours:
            return {
                "error": f"Pool only has {pool_bal['pto']['available']}h available. Requested: {hours}h",
                "success": False,
            }

        # Transfer from pool to recipient
        pool_bal["pto"]["available"] -= hours
        recip_bal["pto"]["available"] += hours
        recip_bal["donated"]["received_hours"] += hours
        recip_bal["donated"]["received_from"].append({
            "from": "Company Pool", "hours": hours, "date": datetime.now().strftime("%Y-%m-%d")
        })

        return {
            "success": True,
            "hours_received": hours,
            "new_balance": recip_bal["pto"]["available"],
            "pool_remaining": pool_bal["pto"]["available"],
            "note": "Subject to HR approval for qualifying event verification",
        }

    def get_donation_history(self, employee_id=None):
        """Get donation history — all or for a specific employee."""
        donations = [t for t in self.transactions if t.get("status") == "COMPLETED"
                     and "DON-" in t.get("id", "")]
        if employee_id:
            donations = [d for d in donations
                        if d["donor_id"] == employee_id or d["recipient_id"] == employee_id]
        return donations

    def get_pool_balance(self):
        """Get current company leave pool balance."""
        pool = self.balances.get("__POOL__")
        if not pool:
            return {"pto_hours": 0, "sick_hours": 0, "total_donations": 0}
        return {
            "pto_hours": pool["pto"]["available"],
            "sick_hours": pool.get("sick", {}).get("available", 0),
            "total_donations": len([t for t in self.transactions if "__POOL__" in str(t.get("recipient_id", ""))]),
        }

    def get_availability_calendar(self, employee_id, shift_code, month_start, shift_assignments):
        """
        Generate availability calendar showing which dates are available to request off.
        Considers: who else on the shift code is already off, blackout dates, minimums.
        """
        if isinstance(month_start, str):
            month_start = datetime.strptime(month_start, "%Y-%m-%d")

        # Get all people on same shift code
        same_code_people = [
            a for a in shift_assignments if a["shift_code"] == shift_code
        ]
        total_on_code = len(same_code_people)
        min_required = max(1, int(total_on_code * 0.6))  # 60% minimum staffing

        calendar = []
        for day_offset in range(30):
            date = month_start + timedelta(days=day_offset)
            date_str = date.strftime("%Y-%m-%d")

            # Count who's already off that day
            already_off = sum(
                1 for rec in self.leave_records
                if rec["start_date"] <= date_str <= rec["end_date"]
                and any(a["employee_id"] == rec["employee_id"] and a["shift_code"] == shift_code
                        for a in shift_assignments)
                and rec["status"] == "ACTIVE"
            )

            available_spots = total_on_code - already_off - min_required
            is_blackout = self._is_blackout_date(date_str)

            if is_blackout:
                status = "blackout"
                availability = "unavailable"
            elif available_spots <= 0:
                status = "full"
                availability = "unavailable"
            elif available_spots == 1:
                status = "limited"
                availability = "limited"
            else:
                status = "open"
                availability = "available"

            calendar.append({
                "date": date_str,
                "day": date.strftime("%A"),
                "status": status,
                "availability": availability,
                "spots_remaining": max(0, available_spots),
                "already_off": already_off,
                "total_on_code": total_on_code,
                "is_blackout": is_blackout,
            })

        return calendar

    def get_return_to_work_pending(self):
        """Get employees who need return-to-work clearance."""
        pending = []
        for rec in self.leave_records:
            if (rec["return_clearance_required"]
                    and not rec["return_clearance_received"]
                    and rec["status"] == "ACTIVE"):
                end_date = datetime.strptime(rec["end_date"], "%Y-%m-%d")
                if end_date <= datetime.now() + timedelta(days=7):
                    pending.append({
                        "employee_id": rec["employee_id"],
                        "leave_type": rec["leave_type"],
                        "end_date": rec["end_date"],
                        "days_until_return": (end_date - datetime.now()).days,
                        "clearance_type": "medical" if rec["leave_type"] in ("WORKERS_COMP", "SHORT_TERM_DISABILITY", "FMLA") else "general",
                    })
        return pending

    def get_documentation_chase_list(self):
        """Get overdue documentation."""
        chase = []
        for rec in self.leave_records:
            if rec["documentation_status"] == "REQUIRED" and rec.get("documentation_due"):
                due = datetime.strptime(rec["documentation_due"], "%Y-%m-%d")
                if due <= datetime.now():
                    days_overdue = (datetime.now() - due).days
                    chase.append({
                        "employee_id": rec["employee_id"],
                        "leave_id": rec["id"],
                        "leave_type": rec["leave_type"],
                        "doc_type": LEAVE_TYPES[rec["leave_type"]].get("doc_type", "documentation"),
                        "due_date": rec["documentation_due"],
                        "days_overdue": days_overdue,
                        "urgency": "HIGH" if days_overdue > 5 else "MEDIUM",
                    })
        return chase

    def get_alerts(self, unresolved_only=True):
        """Get all system alerts."""
        if unresolved_only:
            return [a for a in self.alerts if not a.get("resolved")]
        return self.alerts

    def get_team_leave_overview(self, shift_code=None, shift_assignments=None):
        """Get team-wide leave overview for a period."""
        active = [r for r in self.leave_records if r["status"] == "ACTIVE"]

        if shift_code and shift_assignments:
            code_employees = [
                a["employee_id"] for a in shift_assignments if a["shift_code"] == shift_code
            ]
            active = [r for r in active if r["employee_id"] in code_employees]

        by_type = defaultdict(int)
        by_employee = defaultdict(int)
        total_days = 0

        for r in active:
            by_type[r["leave_type"]] += 1
            by_employee[r["employee_id"]] += r["days"]
            total_days += r["days"]

        return {
            "active_leaves": len(active),
            "total_days_off": total_days,
            "by_type": dict(by_type),
            "by_employee": dict(by_employee),
        }

    # --- Private methods ---

    def _deduct_balance(self, employee_id, leave_type, hours):
        """Deduct hours from the appropriate balance."""
        bal = self.balances.get(employee_id)
        if not bal:
            return {"error": "No balance found"}

        if leave_type in ("PTO", "PERSONAL_UNPAID"):
            if bal["pto"]["available"] >= hours:
                bal["pto"]["available"] -= hours
                bal["pto"]["used"] += hours
                return {"deducted_from": "PTO", "hours": hours, "remaining": bal["pto"]["available"]}
            else:
                available = bal["pto"]["available"]
                bal["pto"]["available"] = 0
                bal["pto"]["used"] += available
                remainder = hours - available
                # Overflow to UPT
                bal["upt"]["available"] = max(0, bal["upt"]["available"] - remainder)
                bal["upt"]["used"] += remainder
                return {"deducted_from": "PTO+UPT", "pto_used": available, "upt_used": remainder}

        elif leave_type in ("SICK_PLANNED", "SICK_UNPLANNED"):
            if bal["sick"]["available"] >= hours:
                bal["sick"]["available"] -= hours
                bal["sick"]["used"] += hours
                return {"deducted_from": "SICK", "hours": hours, "remaining": bal["sick"]["available"]}
            else:
                available = bal["sick"]["available"]
                bal["sick"]["available"] = 0
                bal["sick"]["used"] += available
                return {"deducted_from": "SICK", "hours": available,
                        "warning": f"Insufficient sick balance. Only {available}h available."}

        elif leave_type == "UPT":
            bal["upt"]["available"] = max(0, bal["upt"]["available"] - hours)
            bal["upt"]["used"] += hours
            result = {"deducted_from": "UPT", "hours": hours, "remaining": bal["upt"]["available"]}
            if bal["upt"]["available"] <= 0:
                result["critical_warning"] = "UPT BALANCE AT ZERO - termination review triggered"
                self.alerts.append({
                    "type": "UPT_ZERO",
                    "employee_id": employee_id,
                    "severity": "CRITICAL",
                    "message": f"Employee UPT balance at zero. Policy review required.",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "resolved": False,
                })
            return result

        elif leave_type in ("FMLA", "FMLA_INTERMITTENT"):
            bal["fmla"]["used_hours"] += hours
            remaining = bal["fmla"]["available_hours"] - bal["fmla"]["used_hours"]
            return {"deducted_from": "FMLA", "hours": hours, "remaining": remaining}

        # Protected leaves don't deduct from PTO/sick
        elif leave_type in ("BEREAVEMENT", "JURY_DUTY", "MILITARY", "WORKERS_COMP",
                            "MATERNITY", "SHORT_TERM_DISABILITY", "RELIGIOUS", "VOTING"):
            return {"deducted_from": "NONE", "reason": "Protected leave - no balance deduction"}

        return {"deducted_from": "UNKNOWN", "hours": hours}

    def _check_documentation(self, leave_type, days, documentation):
        """Check if documentation is required and its status."""
        leave_def = LEAVE_TYPES.get(leave_type, {})

        if not leave_def.get("documentation_required"):
            return {"status": "NOT_REQUIRED"}

        threshold = leave_def.get("doc_required_after_days", 0)
        if days <= threshold and threshold > 0:
            return {"status": "NOT_REQUIRED", "note": f"Required after {threshold} days"}

        if documentation:
            return {"status": "RECEIVED", "received_at": datetime.now().strftime("%Y-%m-%d")}

        # Documentation needed but not yet received
        deadline_days = leave_def.get("doc_deadline_days", 5)
        due_date = (datetime.now() + timedelta(days=deadline_days)).strftime("%Y-%m-%d")

        return {
            "status": "REQUIRED",
            "doc_type": leave_def.get("doc_type", "documentation"),
            "due_date": due_date,
            "deadline_days": deadline_days,
        }

    def _check_fmla_trigger(self, employee_id, leave_type, days):
        """
        Check if this absence triggers FMLA notification requirement.
        3+ consecutive days of incapacity may trigger FMLA eligibility notice.
        """
        if leave_type in ("FMLA", "FMLA_INTERMITTENT"):
            return None  # already FMLA

        if days >= 3 and leave_type in ("SICK_PLANNED", "SICK_UNPLANNED", "SHORT_TERM_DISABILITY"):
            bal = self.balances.get(employee_id, {})
            fmla = bal.get("fmla", {})

            if fmla.get("eligible") and fmla.get("used_hours", 0) < fmla.get("available_hours", 480):
                return {
                    "type": "FMLA_TRIGGER",
                    "employee_id": employee_id,
                    "severity": "HIGH",
                    "message": (
                        f"Employee absent {days}+ days. Legally required to notify of FMLA rights "
                        f"within 5 business days. Employee has "
                        f"{fmla['available_hours'] - fmla.get('used_hours', 0)}h FMLA remaining."
                    ),
                    "action_required": "Send FMLA eligibility notice within 5 business days",
                    "deadline": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "resolved": False,
                }
        return None

    def _detect_patterns(self, employee_id, leave_type, leave_date):
        """Detect suspicious or concerning absence patterns."""
        if leave_type not in ("SICK_UNPLANNED", "UPT"):
            return None

        history = self.patterns.get(employee_id, [])
        recent_unplanned = [
            p for p in history
            if p["type"] in ("SICK_UNPLANNED", "UPT")
            and (leave_date - datetime.strptime(p["date"], "%Y-%m-%d")).days <= 90
        ]

        # Pattern: same day of week
        day_of_week = leave_date.strftime("%A")
        same_day = [p for p in recent_unplanned if p["day_of_week"] == day_of_week]

        if len(same_day) >= 3:
            return {
                "type": "PATTERN_DETECTED",
                "employee_id": employee_id,
                "severity": "MEDIUM",
                "message": (
                    f"Pattern detected: {len(same_day)+1} unplanned absences on {day_of_week}s "
                    f"in the last 90 days. May indicate scheduling conflict or personal issue."
                ),
                "action_required": "Manager should have supportive conversation with employee",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "resolved": False,
            }

        # Pattern: frequency
        if len(recent_unplanned) >= 5:
            return {
                "type": "FREQUENCY_ALERT",
                "employee_id": employee_id,
                "severity": "MEDIUM",
                "message": (
                    f"High unplanned absence frequency: {len(recent_unplanned)+1} occurrences "
                    f"in 90 days. Check if employee needs FMLA accommodation or support."
                ),
                "action_required": "Review with HR. Consider FMLA eligibility or EAP referral.",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "resolved": False,
            }

        return None

    def _is_blackout_date(self, date_str):
        """Check if a date is in a blackout period (peak, Prime Week, etc.)."""
        # Demo: Prime Week and Black Friday/Cyber Monday are blackout
        blackout_periods = [
            ("2026-07-13", "2026-07-16"),   # Prime Day
            ("2026-11-26", "2026-12-02"),   # Black Friday / Cyber Monday
            ("2026-12-15", "2026-12-24"),   # Peak holiday shipping
        ]
        for start, end in blackout_periods:
            if start <= date_str <= end:
                return True
        return False


# ============================================================
# CASCADING COVERAGE AUTOMATION
# ============================================================

def cascade_coverage(absence_record, shift_assignments, vet_met_history=None):
    """
    When someone goes on leave, automatically cascade coverage:
    1. Check if VET candidates available
    2. If yes -> offer VET to fairness-ranked list
    3. If no takers -> escalate to MET
    4. If still short -> flag for agency/temp staffing
    """
    from shift_templates import find_coverage_for_absence

    emp_id = absence_record["employee_id"]
    start = datetime.strptime(absence_record["start_date"], "%Y-%m-%d")
    end = datetime.strptime(absence_record["end_date"], "%Y-%m-%d")

    coverage_plan = {
        "leave_id": absence_record["id"],
        "employee_id": emp_id,
        "dates_needing_coverage": [],
        "status": "PLANNING",
    }

    current = start
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")

        result = find_coverage_for_absence(emp_id, date_str, "LOA", vet_met_history)

        if isinstance(result, dict) and "error" not in result:
            day_plan = {
                "date": date_str,
                "vet_candidates": len(result.get("vet_candidates", [])),
                "met_candidates": len(result.get("met_candidates", [])),
                "top_vet": result["vet_candidates"][0]["name"] if result.get("vet_candidates") else None,
                "status": "VET_AVAILABLE" if result.get("vet_candidates") else (
                    "MET_REQUIRED" if result.get("met_candidates") else "AGENCY_NEEDED"
                ),
            }
        else:
            day_plan = {
                "date": date_str,
                "vet_candidates": 0,
                "met_candidates": 0,
                "status": "NOT_SCHEDULED" if "not scheduled" in str(result.get("error", "")).lower() else "UNKNOWN",
            }

        coverage_plan["dates_needing_coverage"].append(day_plan)
        current += timedelta(days=1)

    # Summary
    statuses = [d["status"] for d in coverage_plan["dates_needing_coverage"]]
    if all(s in ("VET_AVAILABLE", "NOT_SCHEDULED") for s in statuses):
        coverage_plan["status"] = "COVERED_VET"
    elif "AGENCY_NEEDED" in statuses:
        coverage_plan["status"] = "NEEDS_AGENCY"
    elif "MET_REQUIRED" in statuses:
        coverage_plan["status"] = "NEEDS_MET"
    else:
        coverage_plan["status"] = "COVERED_VET"

    return coverage_plan


# ============================================================
# DEMO / TESTING
# ============================================================

def create_demo_leave_tracker():
    """Create a pre-populated leave tracker for demo."""
    from sample_schedule import EMPLOYEES

    tracker = LeaveBalanceTracker(state="Illinois")

    for emp in EMPLOYEES:
        tracker.initialize_employee(
            emp["id"],
            emp["hire_date"],
            hours_worked_ytd=1000
        )

    # Record some historical leaves
    tracker.record_leave("E001", "PTO", "2026-03-10", "2026-03-14", reason="Spring vacation")
    tracker.record_leave("E001", "SICK_UNPLANNED", "2026-04-07", "2026-04-07", hours=8, reason="Flu")
    tracker.record_leave("E001", "SICK_UNPLANNED", "2026-05-05", "2026-05-05", hours=8, reason="Migraine")

    tracker.record_leave("E002", "PTO", "2026-02-14", "2026-02-14", reason="Valentine's Day")
    tracker.record_leave("E002", "JURY_DUTY", "2026-04-20", "2026-04-24", reason="Called for jury service")

    tracker.record_leave("E003", "FMLA", "2026-07-07", "2026-07-18", reason="Family medical")

    tracker.record_leave("E005", "RELIGIOUS", "2026-01-29", "2026-01-30", reason="Lunar New Year")

    # Simulate pattern: Marcus calls out on Mondays
    tracker.record_leave("E004", "SICK_UNPLANNED", "2026-04-06", "2026-04-06", hours=8)
    tracker.record_leave("E004", "SICK_UNPLANNED", "2026-04-20", "2026-04-20", hours=8)
    tracker.record_leave("E004", "SICK_UNPLANNED", "2026-05-04", "2026-05-04", hours=8)
    tracker.record_leave("E004", "SICK_UNPLANNED", "2026-06-01", "2026-06-01", hours=8)

    # UPT usage
    tracker.record_leave("E010", "UPT", "2026-05-15", "2026-05-15", hours=4, reason="Left early")
    tracker.record_leave("E010", "UPT", "2026-06-02", "2026-06-02", hours=8, reason="No-show")
    tracker.record_leave("E010", "UPT", "2026-06-15", "2026-06-15", hours=8, reason="No-show")

    return tracker


if __name__ == "__main__":
    tracker = create_demo_leave_tracker()

    print("=" * 70)
    print("  COMPREHENSIVE LEAVE MANAGEMENT ENGINE")
    print("=" * 70)

    # Show all leave types
    print(f"\n  SUPPORTED LEAVE TYPES ({len(LEAVE_TYPES)}):")
    print(f"  {'Type':<22} {'Protected':<10} {'Approval':<16} {'Can Deny'}")
    print(f"  {'-'*60}")
    for code, lt in LEAVE_TYPES.items():
        print(f"  {code:<22} {'Yes' if lt['protected'] else 'No':<10} "
              f"{lt['approval_method']:<16} {'No' if not lt['can_be_denied'] else 'Yes'}")

    # Balance summaries
    print(f"\n\n  EMPLOYEE BALANCE SUMMARIES:")
    print(f"  {'Name':<20} {'PTO (hrs)':<10} {'Sick (hrs)':<11} {'UPT (hrs)':<10} {'FMLA Elig':<10}")
    print(f"  {'-'*65}")

    from sample_schedule import EMPLOYEES
    for emp in EMPLOYEES[:6]:
        summary = tracker.get_balance_summary(emp["id"])
        if summary:
            print(f"  {emp['name']:<20} {summary['pto_hours']:<10} {summary['sick_hours']:<11} "
                  f"{summary['upt_hours']:<10} {'Yes' if summary['fmla_eligible'] else 'No':<10}")
            if summary["warnings"]:
                for w in summary["warnings"]:
                    print(f"    *** {w}")

    # Alerts
    print(f"\n\n  SYSTEM ALERTS:")
    print(f"  {'-'*60}")
    alerts = tracker.get_alerts()
    if alerts:
        for a in alerts:
            print(f"  [{a['severity']}] {a['type']}: {a['message'][:65]}")
            if a.get("action_required"):
                print(f"         Action: {a['action_required'][:60]}")
    else:
        print("  No active alerts.")

    # Documentation chase
    print(f"\n\n  DOCUMENTATION CHASE LIST:")
    chase = tracker.get_documentation_chase_list()
    if chase:
        for c in chase:
            print(f"  {c['employee_id']}: {c['doc_type']} due {c['due_date']} ({c['days_overdue']} days overdue)")
    else:
        print("  No overdue documentation.")

    # Report sick today demo
    print(f"\n\n  DEMO: Jake Thompson reports sick today")
    result = tracker.report_sick_today("E010", reason="Food poisoning")
    print(f"  Status: {result['status']}")
    print(f"  Balance: {result['balance_deduction']}")
    if result.get("alerts_triggered"):
        for a in result["alerts_triggered"]:
            print(f"  ALERT: {a['message'][:60]}")
