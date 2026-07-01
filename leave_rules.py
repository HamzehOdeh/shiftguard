"""
Workforce Compliance AI - Leave & Time-Off Rules Engine
State-by-state PTO, sick leave, holiday, and FMLA compliance rules.
"""

# ============================================================
# FEDERAL RULES
# ============================================================

FEDERAL_FMLA = {
    "jurisdiction": "Federal",
    "law_name": "Family and Medical Leave Act (FMLA)",
    "applies_to": "Employers with 50+ employees; employees with 12+ months tenure and 1,250+ hours worked",
    "rules": [
        {
            "id": "FED-FMLA-001",
            "name": "FMLA Leave Entitlement",
            "description": "Eligible employees entitled to 12 weeks unpaid leave per 12-month period",
            "requirement": "fmla_leave_available_weeks <= 12",
            "penalty": "Back pay + benefits + liquidated damages + attorney fees",
            "severity": "critical"
        },
        {
            "id": "FED-FMLA-002",
            "name": "No Scheduling During Approved Leave",
            "description": "Cannot schedule an employee who is on approved FMLA leave",
            "requirement": "employee_not_on_fmla_leave",
            "penalty": "Interference claim - back pay + damages",
            "severity": "critical"
        },
        {
            "id": "FED-FMLA-003",
            "name": "Reinstatement Rights",
            "description": "Employee must be restored to same or equivalent position upon return",
            "requirement": "same_role_on_return",
            "penalty": "Retaliation claim - compensatory + punitive damages",
            "severity": "critical"
        }
    ]
}

# ============================================================
# STATE PAID SICK LEAVE LAWS
# ============================================================

STATE_SICK_LEAVE = {
    "Illinois": {
        "law_name": "Illinois Paid Leave for All Workers Act",
        "effective": "2024-01-01",
        "rules": [
            {
                "id": "IL-PSL-001",
                "name": "Sick Leave Accrual",
                "description": "1 hour of paid leave per 40 hours worked",
                "accrual_rate": 1/40,
                "cap_hours": 40,
                "carryover": True,
                "carryover_cap_hours": 40,
                "waiting_period_days": 90,
                "severity": "high"
            },
            {
                "id": "IL-PSL-002",
                "name": "No Retaliation for Sick Leave Use",
                "description": "Cannot count sick leave use as attendance violation or schedule punishment",
                "requirement": "no_adverse_action_for_leave_use",
                "penalty": "Back pay + $500/day violation + attorney fees",
                "severity": "high"
            }
        ]
    },
    "California": {
        "law_name": "California Paid Sick Leave (SB 616)",
        "effective": "2024-01-01",
        "rules": [
            {
                "id": "CA-PSL-001",
                "name": "Sick Leave Accrual",
                "description": "1 hour per 30 hours worked; minimum 5 days (40 hrs) available per year",
                "accrual_rate": 1/30,
                "cap_hours": 80,
                "carryover": True,
                "carryover_cap_hours": 80,
                "min_annual_available": 40,
                "waiting_period_days": 90,
                "severity": "high"
            },
            {
                "id": "CA-PSL-002",
                "name": "No Retaliation",
                "description": "Cannot retaliate against employee for using paid sick leave",
                "requirement": "no_adverse_action_for_leave_use",
                "penalty": "Reinstatement + back pay + $10,000 admin penalty",
                "severity": "high"
            }
        ]
    },
    "New York": {
        "law_name": "New York Paid Sick Leave Law",
        "effective": "2021-01-01",
        "rules": [
            {
                "id": "NY-PSL-001",
                "name": "Sick Leave Entitlement",
                "description": "100+ employees: 56 hours paid; 5-99: 40 hours paid; 1-4: 40 hours unpaid",
                "accrual_rate": 1/30,
                "cap_hours_large": 56,
                "cap_hours_medium": 40,
                "carryover": True,
                "severity": "high"
            }
        ]
    },
    "Oregon": {
        "law_name": "Oregon Sick Time Law",
        "effective": "2016-01-01",
        "rules": [
            {
                "id": "OR-PSL-001",
                "name": "Sick Leave Accrual",
                "description": "1 hour per 30 hours worked; 10+ employees: paid; <10: unpaid",
                "accrual_rate": 1/30,
                "cap_hours": 40,
                "carryover": True,
                "carryover_cap_hours": 40,
                "severity": "high"
            }
        ]
    },
    "Michigan": {
        "law_name": "Michigan Paid Medical Leave Act",
        "effective": "2019-03-29",
        "rules": [
            {
                "id": "MI-PSL-001",
                "name": "Sick Leave Accrual",
                "description": "1 hour per 35 hours worked; cap at 40 hours per year",
                "accrual_rate": 1/35,
                "cap_hours": 40,
                "carryover": True,
                "carryover_cap_hours": 40,
                "waiting_period_days": 90,
                "severity": "high"
            }
        ]
    },
    "Washington": {
        "law_name": "Washington Paid Sick Leave",
        "effective": "2018-01-01",
        "rules": [
            {
                "id": "WA-PSL-001",
                "name": "Sick Leave Accrual",
                "description": "1 hour per 40 hours worked; no cap on accrual; unused carries over",
                "accrual_rate": 1/40,
                "cap_hours": None,
                "carryover": True,
                "carryover_cap_hours": None,
                "severity": "high"
            }
        ]
    },
    "Colorado": {
        "law_name": "Colorado Healthy Families & Workplaces Act",
        "effective": "2021-01-01",
        "rules": [
            {
                "id": "CO-PSL-001",
                "name": "Sick Leave Accrual",
                "description": "1 hour per 30 hours worked; cap at 48 hours per year",
                "accrual_rate": 1/30,
                "cap_hours": 48,
                "carryover": True,
                "carryover_cap_hours": 48,
                "severity": "high"
            }
        ]
    }
}

# ============================================================
# STATE HOLIDAY PREMIUM PAY RULES
# ============================================================

STATE_HOLIDAY_RULES = {
    "Massachusetts": {
        "law_name": "Massachusetts Blue Laws (phasing out)",
        "rules": [
            {
                "id": "MA-HOL-001",
                "name": "Premium Pay for Holidays",
                "description": "Retail workers get 1.5x pay on New Year's Day, Memorial Day, Juneteenth, Independence Day, Labor Day, Columbus Day, Veterans Day, Thanksgiving, Christmas (being phased out through 2027)",
                "holidays": ["New Year's Day", "Memorial Day", "Juneteenth", "Independence Day",
                            "Labor Day", "Columbus Day", "Veterans Day", "Thanksgiving", "Christmas"],
                "premium_rate": 1.5,
                "severity": "high"
            }
        ]
    },
    "Rhode Island": {
        "law_name": "Rhode Island Holiday Pay",
        "rules": [
            {
                "id": "RI-HOL-001",
                "name": "Sunday/Holiday Premium",
                "description": "Retail/hospitality workers get 1.5x on Sundays and holidays",
                "premium_rate": 1.5,
                "severity": "medium"
            }
        ]
    },
    "California": {
        "law_name": "California (no mandatory holiday premium)",
        "rules": [
            {
                "id": "CA-HOL-001",
                "name": "No State Holiday Premium Requirement",
                "description": "California does not require holiday premium pay by law, but many CBAs and company policies do. Check CBA/policy.",
                "premium_rate": None,
                "severity": "low"
            }
        ]
    }
}

# ============================================================
# PTO ACCRUAL CAPS & CARRYOVER BY STATE
# ============================================================

PTO_RULES_BY_STATE = {
    "California": {
        "use_it_or_lose_it": False,
        "description": "California prohibits use-it-or-lose-it PTO policies. Accrued PTO is considered wages and must be paid out on termination.",
        "payout_on_termination": True,
        "cap_allowed": True,
        "cap_note": "Employers CAN set a reasonable accrual cap (e.g., 1.5x annual accrual) but cannot forfeit already-accrued time",
        "rules": [
            {
                "id": "CA-PTO-001",
                "name": "PTO Payout on Termination",
                "description": "All accrued, unused PTO must be paid out at final rate of pay upon separation",
                "requirement": "pay_out_pto_on_termination",
                "penalty": "Waiting time penalties: up to 30 days wages",
                "severity": "high"
            },
            {
                "id": "CA-PTO-002",
                "name": "No Forfeiture",
                "description": "Cannot forfeit accrued PTO; can only cap future accrual",
                "requirement": "no_pto_forfeiture",
                "penalty": "Wage claim + DLSE penalties",
                "severity": "high"
            }
        ]
    },
    "Illinois": {
        "use_it_or_lose_it": False,
        "description": "Illinois prohibits forfeiture of earned vacation. Must pay out on termination.",
        "payout_on_termination": True,
        "cap_allowed": True,
        "rules": [
            {
                "id": "IL-PTO-001",
                "name": "PTO Payout on Termination",
                "description": "Earned vacation must be paid out upon separation",
                "requirement": "pay_out_pto_on_termination",
                "penalty": "Back pay + damages",
                "severity": "high"
            }
        ]
    },
    "Michigan": {
        "use_it_or_lose_it": True,
        "description": "Michigan allows use-it-or-lose-it policies if clearly communicated in writing",
        "payout_on_termination": False,
        "cap_allowed": True,
        "rules": [
            {
                "id": "MI-PTO-001",
                "name": "Written Policy Required",
                "description": "Use-it-or-lose-it only valid if in written policy provided to employees",
                "requirement": "written_pto_policy",
                "penalty": "Default to payout if no written policy",
                "severity": "medium"
            }
        ]
    },
    "Oregon": {
        "use_it_or_lose_it": True,
        "description": "Oregon allows use-it-or-lose-it with proper notice. No payout required unless policy states otherwise.",
        "payout_on_termination": False,
        "cap_allowed": True,
        "rules": []
    },
    "New York": {
        "use_it_or_lose_it": True,
        "description": "New York allows use-it-or-lose-it if in written policy. Must pay out if no policy exists.",
        "payout_on_termination": False,
        "cap_allowed": True,
        "rules": [
            {
                "id": "NY-PTO-001",
                "name": "Policy Requirement",
                "description": "Must have clear written policy on forfeiture; otherwise payout is required",
                "requirement": "written_pto_policy",
                "penalty": "Default to payout",
                "severity": "medium"
            }
        ]
    },
    "Colorado": {
        "use_it_or_lose_it": False,
        "description": "Colorado requires payout of all accrued vacation upon separation regardless of policy.",
        "payout_on_termination": True,
        "cap_allowed": True,
        "rules": [
            {
                "id": "CO-PTO-001",
                "name": "Mandatory Payout",
                "description": "All accrued vacation must be paid at separation",
                "requirement": "pay_out_pto_on_termination",
                "penalty": "Unpaid wages claim + penalties",
                "severity": "high"
            }
        ]
    }
}

# ============================================================
# SCHEDULING-RELEVANT LEAVE CHECKS
# ============================================================

def check_leave_compliance(schedule, employee_leave_records, state="Illinois"):
    """
    Check schedule against leave rules.

    employee_leave_records: list of dicts with:
        - employee_id
        - leave_type: "fmla", "sick", "pto", "holiday"
        - start_date, end_date
        - status: "approved", "pending", "denied"
        - hours_accrued, hours_used, hours_available
    """
    violations = []

    for shift in schedule.get("shifts", []):
        emp_id = shift["employee_id"]
        shift_date = shift["date"]

        for leave in employee_leave_records:
            if leave["employee_id"] != emp_id:
                continue
            if leave["status"] != "approved":
                continue

            # Check if shift falls during approved leave
            if leave["start_date"] <= shift_date <= leave["end_date"]:
                if leave["leave_type"] == "fmla":
                    violations.append({
                        "rule_id": "FED-FMLA-002",
                        "rule_name": "Scheduling During FMLA Leave",
                        "severity": "CRITICAL",
                        "description": f"{shift['name']}: Scheduled on {shift_date} but is on approved FMLA leave ({leave['start_date']} to {leave['end_date']})",
                        "affected_employees": shift["name"],
                        "cost_impact": "FMLA interference claim - back pay + liquidated damages + attorney fees ($50K-$500K+)",
                        "recommendation": f"Remove {shift['name']} from schedule on {shift_date}. Assign to qualified replacement."
                    })
                elif leave["leave_type"] == "sick":
                    violations.append({
                        "rule_id": f"{state[:2].upper()}-PSL-002",
                        "rule_name": "Scheduling During Approved Sick Leave",
                        "severity": "HIGH",
                        "description": f"{shift['name']}: Scheduled on {shift_date} but has approved sick leave",
                        "affected_employees": shift["name"],
                        "cost_impact": "Retaliation claim risk + state penalties",
                        "recommendation": f"Remove shift and do not count as attendance issue."
                    })
                elif leave["leave_type"] == "pto":
                    violations.append({
                        "rule_id": "CP-PTO-001",
                        "rule_name": "Scheduling During Approved PTO",
                        "severity": "MEDIUM",
                        "description": f"{shift['name']}: Scheduled on {shift_date} but has approved PTO",
                        "affected_employees": shift["name"],
                        "cost_impact": "Employee grievance + morale impact",
                        "recommendation": f"Remove shift or get employee to voluntarily cancel PTO."
                    })

    return violations


def check_sick_leave_balance(employee_id, hours_requested, hours_available, state="Illinois"):
    """Check if employee has sufficient sick leave balance."""
    if hours_requested > hours_available:
        return {
            "rule_id": f"{state[:2].upper()}-PSL-001",
            "rule_name": "Insufficient Sick Leave Balance",
            "severity": "LOW",
            "description": f"Employee requested {hours_requested} hrs but only has {hours_available} hrs available",
            "recommendation": "Allow unpaid leave or check if other leave banks available"
        }
    return None


def get_state_leave_summary(state):
    """Get a summary of all leave rules for a state."""
    summary = {
        "state": state,
        "sick_leave": STATE_SICK_LEAVE.get(state, {}),
        "holiday_rules": STATE_HOLIDAY_RULES.get(state, {}),
        "pto_rules": PTO_RULES_BY_STATE.get(state, {}),
        "fmla": FEDERAL_FMLA
    }
    return summary


def get_all_leave_rules(state="Illinois"):
    """Get all leave-related rules for a state."""
    rules = []

    # Federal FMLA always applies
    rules.extend(FEDERAL_FMLA["rules"])

    # State sick leave
    state_sick = STATE_SICK_LEAVE.get(state, {})
    if state_sick:
        rules.extend(state_sick.get("rules", []))

    # Holiday rules
    state_hol = STATE_HOLIDAY_RULES.get(state, {})
    if state_hol:
        rules.extend(state_hol.get("rules", []))

    # PTO rules
    state_pto = PTO_RULES_BY_STATE.get(state, {})
    if state_pto:
        rules.extend(state_pto.get("rules", []))

    return rules


if __name__ == "__main__":
    print("=" * 60)
    print("  LEAVE & TIME-OFF COMPLIANCE RULES")
    print("=" * 60)

    states = ["California", "Illinois", "Michigan", "Oregon", "New York", "Colorado", "Washington"]

    print("\n  PAID SICK LEAVE BY STATE:")
    print(f"  {'State':<15} {'Accrual':<15} {'Cap':<10} {'Carryover':<10}")
    print(f"  {'-'*50}")
    for state in states:
        info = STATE_SICK_LEAVE.get(state, {})
        if info:
            rules = info.get("rules", [])
            if rules:
                r = rules[0]
                rate = f"1hr/{int(1/r.get('accrual_rate',0))}hrs"
                cap = f"{r.get('cap_hours', 'None')} hrs"
                carry = "Yes" if r.get('carryover') else "No"
                print(f"  {state:<15} {rate:<15} {cap:<10} {carry:<10}")

    print("\n\n  PTO PAYOUT RULES BY STATE:")
    print(f"  {'State':<15} {'Use-or-Lose OK?':<18} {'Payout Required?':<18}")
    print(f"  {'-'*50}")
    for state in states:
        info = PTO_RULES_BY_STATE.get(state, {})
        if info:
            uol = "Yes" if info.get("use_it_or_lose_it") else "NO"
            payout = "YES" if info.get("payout_on_termination") else "No"
            print(f"  {state:<15} {uol:<18} {payout:<18}")

    print("\n\n  HOLIDAY PREMIUM PAY:")
    for state, info in STATE_HOLIDAY_RULES.items():
        rules = info.get("rules", [])
        if rules:
            print(f"  {state}: {rules[0]['description'][:70]}")

    print("\n\n  FEDERAL FMLA:")
    for r in FEDERAL_FMLA["rules"]:
        print(f"  [{r['id']}] {r['name']}: {r['description']}")

    # Demo: check leave compliance
    print("\n\n  DEMO: Schedule vs Leave Check")
    print("  " + "-" * 40)

    sample_leaves = [
        {"employee_id": "E003", "leave_type": "fmla", "start_date": "2026-07-07", "end_date": "2026-07-18", "status": "approved"},
        {"employee_id": "E009", "leave_type": "pto", "start_date": "2026-07-09", "end_date": "2026-07-11", "status": "approved"},
    ]

    from sample_schedule import generate_schedule
    schedule = generate_schedule()

    leave_violations = check_leave_compliance(schedule, sample_leaves, state="Illinois")
    print(f"\n  Found {len(leave_violations)} leave-related violations:")
    for v in leave_violations:
        print(f"  [{v['severity']}] {v['rule_name']}: {v['description'][:70]}")

    print(f"\n  Total leave rules loaded: {len(get_all_leave_rules('Illinois'))}")
    print("=" * 60)
