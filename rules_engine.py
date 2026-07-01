"""
Workforce Compliance AI - Rules Engine
Defines labor laws, union CBA rules, and company policies as structured data.
"""

# Oregon Predictive Scheduling Law (ORS 653.455-653.471)
OREGON_PREDICTIVE_SCHEDULING = {
    "jurisdiction": "Oregon",
    "law_name": "Oregon Predictive Scheduling Law",
    "effective": "2018-07-01",
    "applies_to": "Retail, hospitality, food service employers with 500+ employees worldwide",
    "rules": [
        {
            "id": "OR-PS-001",
            "name": "Advance Notice",
            "description": "Employers must provide work schedules at least 14 days in advance",
            "requirement": "schedule_notice_days >= 14",
            "penalty": "Per-shift penalty for each violation",
            "severity": "high"
        },
        {
            "id": "OR-PS-002",
            "name": "Right to Rest (Clopening)",
            "description": "Employees cannot be scheduled with less than 10 hours between shifts unless they consent in writing",
            "requirement": "hours_between_shifts >= 10",
            "penalty": "Time-and-a-half pay for hours within the 10-hour window",
            "severity": "high"
        },
        {
            "id": "OR-PS-003",
            "name": "Schedule Change Premium",
            "description": "Changes to schedule after posting require premium pay",
            "requirement": "no_changes_after_posting_without_premium",
            "penalty": "1 hour extra pay (>14 days notice), half-shift pay (<14 days)",
            "severity": "medium"
        },
        {
            "id": "OR-PS-004",
            "name": "Right to Input",
            "description": "Employees have right to identify schedule limitations and preferences",
            "requirement": "availability_preferences_collected",
            "penalty": "Administrative violation",
            "severity": "low"
        }
    ]
}

# NYC Fair Workweek Law (NYC Admin Code 20-1201 et seq.)
NYC_FAIR_WORKWEEK = {
    "jurisdiction": "New York City",
    "law_name": "NYC Fair Workweek Law",
    "effective": "2017-11-26",
    "applies_to": "Fast food, retail employers with 20+ employees in NYC",
    "rules": [
        {
            "id": "NYC-FW-001",
            "name": "Advance Scheduling",
            "description": "Must provide schedule 14 days in advance",
            "requirement": "schedule_notice_days >= 14",
            "penalty": "$10-$75 per affected employee per occurrence",
            "severity": "high"
        },
        {
            "id": "NYC-FW-002",
            "name": "Clopening Prohibition",
            "description": "Cannot schedule closing shift followed by opening shift with less than 11 hours between",
            "requirement": "hours_between_shifts >= 11",
            "penalty": "$100 premium per occurrence",
            "severity": "high"
        },
        {
            "id": "NYC-FW-003",
            "name": "Premium Pay for Changes",
            "description": "Schedule changes with less than 14 days notice require premium pay",
            "requirement": "no_changes_without_premium_under_14_days",
            "penalty": "$10-$75 depending on notice period",
            "severity": "medium"
        },
        {
            "id": "NYC-FW-004",
            "name": "Consecutive Hours Cap",
            "description": "Cannot require work exceeding 12 consecutive hours without consent",
            "requirement": "consecutive_hours <= 12",
            "penalty": "Per-violation penalty",
            "severity": "high"
        }
    ]
}

# Chicago Fair Workweek Ordinance
CHICAGO_FAIR_WORKWEEK = {
    "jurisdiction": "Chicago",
    "law_name": "Chicago Fair Workweek Ordinance",
    "effective": "2020-07-01",
    "applies_to": "Building services, healthcare, hotels, manufacturing, restaurants, retail, warehouse with 100+ employees",
    "rules": [
        {
            "id": "CHI-FW-001",
            "name": "Advance Notice",
            "description": "Must provide schedule 14 days in advance (10 days until 2022)",
            "requirement": "schedule_notice_days >= 14",
            "penalty": "$300-$500 per employee per violation",
            "severity": "high"
        },
        {
            "id": "CHI-FW-002",
            "name": "Right to Rest",
            "description": "10 hours minimum between shifts; employee can decline shifts within this window",
            "requirement": "hours_between_shifts >= 10",
            "penalty": "1.25x pay rate for declined hours",
            "severity": "high"
        },
        {
            "id": "CHI-FW-003",
            "name": "Predictability Pay",
            "description": "Changes to schedule after posting require predictability pay of 1 hour at regular rate",
            "requirement": "no_changes_after_posting_without_pay",
            "penalty": "1 hour additional pay per change",
            "severity": "medium"
        }
    ]
}

# California Meal & Rest Break Law
CALIFORNIA_MEAL_BREAK = {
    "jurisdiction": "California",
    "law_name": "California Meal and Rest Break Requirements",
    "effective": "Ongoing",
    "applies_to": "All non-exempt employees in California",
    "rules": [
        {
            "id": "CA-MB-001",
            "name": "First Meal Break",
            "description": "30-minute unpaid meal break required before 5th hour of work",
            "requirement": "meal_break_before_hour_5 if shift_hours > 5",
            "penalty": "1 hour premium pay per violation per day",
            "severity": "high"
        },
        {
            "id": "CA-MB-002",
            "name": "Second Meal Break",
            "description": "Second 30-minute meal break required before 10th hour of work",
            "requirement": "second_meal_break_before_hour_10 if shift_hours > 10",
            "penalty": "1 hour premium pay per violation per day",
            "severity": "high"
        },
        {
            "id": "CA-MB-003",
            "name": "Rest Breaks",
            "description": "10-minute paid rest break per 4 hours worked (or major fraction thereof)",
            "requirement": "rest_break_per_4_hours",
            "penalty": "1 hour premium pay per violation per day",
            "severity": "medium"
        },
        {
            "id": "CA-MB-004",
            "name": "Daily Overtime",
            "description": "Overtime (1.5x) after 8 hours in a day; double time after 12 hours",
            "requirement": "daily_hours <= 8 for straight time",
            "penalty": "OT pay required",
            "severity": "high"
        }
    ]
}

# Sample Union CBA (modeled on warehouse/logistics CBAs)
SAMPLE_UNION_CBA = {
    "union": "Teamsters Local 299",
    "employer": "Midwest Distribution Inc.",
    "effective": "2024-01-01",
    "expiration": "2027-12-31",
    "facility": "DET3-Equivalent Warehouse",
    "rules": [
        {
            "id": "CBA-001",
            "name": "Minimum Shift Length",
            "description": "No shift shall be less than 4 hours for any bargaining unit employee",
            "requirement": "shift_hours >= 4",
            "penalty": "Pay for full 4 hours regardless",
            "severity": "high"
        },
        {
            "id": "CBA-002",
            "name": "Maximum Consecutive Days",
            "description": "No employee shall work more than 6 consecutive days without a day off",
            "requirement": "consecutive_days <= 6",
            "penalty": "Grievance + double time for 7th day",
            "severity": "high"
        },
        {
            "id": "CBA-003",
            "name": "Seniority-Based Shift Assignment",
            "description": "Preferred shifts must be offered to senior employees first",
            "requirement": "seniority_order_for_preferred_shifts",
            "penalty": "Grievance + back pay differential",
            "severity": "medium"
        },
        {
            "id": "CBA-004",
            "name": "Overtime Distribution",
            "description": "Overtime must be distributed equitably among qualified employees by seniority rotation",
            "requirement": "overtime_equitable_distribution",
            "penalty": "Grievance + pay at OT rate",
            "severity": "medium"
        },
        {
            "id": "CBA-005",
            "name": "Schedule Posting",
            "description": "Weekly schedule must be posted by Wednesday of the prior week (5 days notice)",
            "requirement": "schedule_notice_days >= 5",
            "penalty": "Grievance",
            "severity": "medium"
        },
        {
            "id": "CBA-006",
            "name": "Mandatory OT Limit",
            "description": "Mandatory overtime cannot exceed 12 hours per week without employee consent",
            "requirement": "mandatory_ot_hours <= 12",
            "penalty": "Grievance + premium pay",
            "severity": "high"
        },
        {
            "id": "CBA-007",
            "name": "Split Shift Prohibition",
            "description": "Split shifts are prohibited unless employee volunteers",
            "requirement": "no_split_shifts_without_consent",
            "penalty": "Grievance + 2 hours premium pay",
            "severity": "medium"
        },
        {
            "id": "CBA-008",
            "name": "Rest Between Shifts",
            "description": "Minimum 10 hours between end of one shift and start of next",
            "requirement": "hours_between_shifts >= 10",
            "penalty": "Grievance + time-and-a-half for hours within window",
            "severity": "high"
        }
    ]
}

# Company Policy (internal rules beyond legal requirements)
COMPANY_POLICY = {
    "company": "Midwest Distribution Inc.",
    "rules": [
        {
            "id": "CP-001",
            "name": "Weekly Hour Cap",
            "description": "No employee shall be scheduled for more than 60 hours in a work week without VP approval",
            "requirement": "weekly_hours <= 60",
            "penalty": "Manager escalation required",
            "severity": "medium"
        },
        {
            "id": "CP-002",
            "name": "Minor Restrictions",
            "description": "Employees under 18 cannot work between 10pm and 6am",
            "requirement": "minors_no_night_shifts",
            "penalty": "Legal violation + termination risk",
            "severity": "critical"
        },
        {
            "id": "CP-003",
            "name": "Training Completion",
            "description": "Employees cannot be scheduled for roles they haven't been trained/certified for",
            "requirement": "role_certification_required",
            "penalty": "Safety violation",
            "severity": "high"
        }
    ]
}


def get_all_rules(jurisdiction="Chicago", include_cba=True, include_company=True):
    """Get all applicable rules for a given jurisdiction."""
    rules = []

    # Select jurisdiction law
    if jurisdiction == "Oregon":
        rules.extend(OREGON_PREDICTIVE_SCHEDULING["rules"])
    elif jurisdiction == "NYC":
        rules.extend(NYC_FAIR_WORKWEEK["rules"])
    elif jurisdiction == "Chicago":
        rules.extend(CHICAGO_FAIR_WORKWEEK["rules"])

    # Always include CA meal break if in CA
    if jurisdiction == "California":
        rules.extend(CALIFORNIA_MEAL_BREAK["rules"])

    if include_cba:
        rules.extend(SAMPLE_UNION_CBA["rules"])

    if include_company:
        rules.extend(COMPANY_POLICY["rules"])

    return rules


if __name__ == "__main__":
    rules = get_all_rules("Chicago")
    print(f"Total rules loaded: {len(rules)}")
    print("\nHigh/Critical severity rules:")
    for r in rules:
        if r["severity"] in ("high", "critical"):
            print(f"  [{r['id']}] {r['name']}: {r['description']}")
