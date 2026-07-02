"""
Workforce Compliance AI - Shift Intelligence Module
Day/night shift classification, national holiday calendar, premium pay,
and shift-type-specific compliance rules.
"""

from datetime import datetime, timedelta, date
from collections import defaultdict


# US Federal Holidays (fixed and calculated)
FEDERAL_HOLIDAYS_2026 = {
    "2026-01-01": "New Year's Day",
    "2026-01-19": "Martin Luther King Jr. Day",
    "2026-02-16": "Presidents' Day",
    "2026-05-25": "Memorial Day",
    "2026-06-19": "Juneteenth",
    "2026-07-04": "Independence Day (Observed)",
    "2026-09-07": "Labor Day",
    "2026-10-12": "Columbus Day",
    "2026-11-11": "Veterans Day",
    "2026-11-26": "Thanksgiving Day",
    "2026-12-25": "Christmas Day",
}

FEDERAL_HOLIDAYS_2027 = {
    "2027-01-01": "New Year's Day",
    "2027-01-18": "Martin Luther King Jr. Day",
    "2027-02-15": "Presidents' Day",
    "2027-05-31": "Memorial Day",
    "2027-06-19": "Juneteenth",
    "2027-07-05": "Independence Day (Observed)",
    "2027-09-06": "Labor Day",
    "2027-10-11": "Columbus Day",
    "2027-11-11": "Veterans Day",
    "2027-11-25": "Thanksgiving Day",
    "2027-12-25": "Christmas Day",
}

# Common school holiday periods (approximate, varies by district)
SCHOOL_HOLIDAY_PERIODS_2026 = [
    {"name": "Winter Break", "start": "2026-12-21", "end": "2027-01-02"},
    {"name": "Spring Break", "start": "2026-03-16", "end": "2026-03-20"},
    {"name": "Summer Break", "start": "2026-06-15", "end": "2026-08-20"},
    {"name": "Fall Break", "start": "2026-10-12", "end": "2026-10-16"},
    {"name": "Thanksgiving Break", "start": "2026-11-23", "end": "2026-11-27"},
]

# Holiday value groups (equivalent-value slots for fair rotation)
HOLIDAY_VALUE_GROUPS = {
    "winter_major": ["Christmas Day", "New Year's Day"],
    "winter_adjacent": ["2026-12-24", "2026-12-26", "2026-12-31"],
    "thanksgiving_week": ["Thanksgiving Day", "2026-11-27"],  # Thu + Black Friday
    "summer_major": ["Independence Day (Observed)", "Memorial Day", "Labor Day"],
    "school_breaks": ["Spring Break", "Fall Break"],
}

# Shift type definitions
SHIFT_TYPES = {
    "day": {
        "name": "Day Shift",
        "typical_hours": "06:00-14:30",
        "start_range": (5, 13),
        "differential": 1.0,
        "fatigue_weight": 1.0,
    },
    "evening": {
        "name": "Evening Shift",
        "typical_hours": "14:00-22:30",
        "start_range": (13, 21),
        "differential": 1.05,
        "fatigue_weight": 1.1,
    },
    "night": {
        "name": "Night Shift",
        "typical_hours": "22:00-06:30",
        "start_range": (21, 5),
        "differential": 1.15,
        "fatigue_weight": 1.4,
    },
}

# Night shift specific compliance rules
NIGHT_SHIFT_RULES = {
    "max_consecutive_nights": 4,
    "min_rest_after_night_block": 48,  # hours
    "rotation_direction": "forward",  # day→evening→night is healthier
    "minor_prohibition_start": 22,
    "minor_prohibition_end": 6,
}


def classify_shift(shift):
    """
    Classify a shift and return enriched shift data.
    """
    start_hour = int(shift["start"].split(":")[0])
    end_hour = int(shift["end"].split(":")[0])

    # Determine shift type
    if start_hour >= 21 or start_hour < 5:
        shift_type = "night"
    elif start_hour >= 13 or end_hour > 22 or end_hour < 5:
        shift_type = "evening"
    else:
        shift_type = "day"

    shift_info = SHIFT_TYPES[shift_type]

    # Check if it's a holiday
    shift_date = shift["date"]
    holiday_name = get_holiday_name(shift_date)
    is_holiday = holiday_name is not None

    # Calculate differential pay multiplier
    base_differential = shift_info["differential"]
    holiday_premium = 1.5 if is_holiday else 1.0
    total_multiplier = base_differential * holiday_premium

    return {
        **shift,
        "classified_type": shift_type,
        "type_name": shift_info["name"],
        "differential": base_differential,
        "holiday_name": holiday_name,
        "is_holiday": is_holiday,
        "holiday_premium": holiday_premium,
        "total_pay_multiplier": round(total_multiplier, 3),
        "fatigue_weight": shift_info["fatigue_weight"],
    }


def get_holiday_name(date_str):
    """Check if a date is a federal holiday."""
    all_holidays = {**FEDERAL_HOLIDAYS_2026, **FEDERAL_HOLIDAYS_2027}
    return all_holidays.get(date_str)


def is_holiday(date_str):
    """Simple boolean check for holiday."""
    return get_holiday_name(date_str) is not None


def is_school_holiday(date_str):
    """Check if date falls within a school holiday period."""
    d = datetime.strptime(date_str, "%Y-%m-%d")
    for period in SCHOOL_HOLIDAY_PERIODS_2026:
        start = datetime.strptime(period["start"], "%Y-%m-%d")
        end = datetime.strptime(period["end"], "%Y-%m-%d")
        if start <= d <= end:
            return period["name"]
    return None


def get_holidays_in_range(start_date, end_date):
    """Get all holidays within a date range."""
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

    holidays = []
    all_holidays = {**FEDERAL_HOLIDAYS_2026, **FEDERAL_HOLIDAYS_2027}

    for date_str, name in all_holidays.items():
        d = datetime.strptime(date_str, "%Y-%m-%d")
        if start_date <= d <= end_date:
            holidays.append({"date": date_str, "name": name})

    return sorted(holidays, key=lambda x: x["date"])


def analyze_schedule_shifts(shifts):
    """
    Analyze all shifts in a schedule and return enriched data with
    day/night classification, holiday detection, and pay multipliers.
    """
    classified = [classify_shift(s) for s in shifts]

    # Summary stats
    by_type = defaultdict(list)
    for s in classified:
        by_type[s["classified_type"]].append(s)

    # Per-employee shift type distribution
    emp_distribution = defaultdict(lambda: {"day": 0, "evening": 0, "night": 0, "holidays": 0})
    for s in classified:
        emp_distribution[s["employee_id"]][s["classified_type"]] += 1
        if s["is_holiday"]:
            emp_distribution[s["employee_id"]]["holidays"] += 1

    return {
        "classified_shifts": classified,
        "summary": {
            "total_shifts": len(classified),
            "day_shifts": len(by_type["day"]),
            "evening_shifts": len(by_type["evening"]),
            "night_shifts": len(by_type["night"]),
            "holiday_shifts": sum(1 for s in classified if s["is_holiday"]),
        },
        "employee_distribution": dict(emp_distribution),
    }


def check_night_shift_compliance(shifts, employee_id):
    """
    Check night-shift-specific compliance rules for an employee.
    """
    emp_shifts = sorted(
        [s for s in shifts if s["employee_id"] == employee_id],
        key=lambda x: x["date"]
    )

    violations = []
    classified = [classify_shift(s) for s in emp_shifts]
    night_shifts = [s for s in classified if s["classified_type"] == "night"]

    # Check consecutive nights
    if len(night_shifts) >= 2:
        consecutive = 1
        max_consecutive = 1
        for i in range(1, len(night_shifts)):
            d1 = datetime.strptime(night_shifts[i-1]["date"], "%Y-%m-%d")
            d2 = datetime.strptime(night_shifts[i]["date"], "%Y-%m-%d")
            if (d2 - d1).days == 1:
                consecutive += 1
                max_consecutive = max(max_consecutive, consecutive)
            else:
                consecutive = 1

        if max_consecutive > NIGHT_SHIFT_RULES["max_consecutive_nights"]:
            violations.append({
                "rule_id": "NS-001",
                "rule_name": "Maximum Consecutive Night Shifts",
                "severity": "HIGH",
                "description": f"{emp_shifts[0]['name']}: {max_consecutive} consecutive night shifts "
                              f"(maximum {NIGHT_SHIFT_RULES['max_consecutive_nights']})",
                "affected_employees": emp_shifts[0]["name"],
                "cost_impact": "Fatigue risk + potential safety incident liability",
                "recommendation": f"Limit to {NIGHT_SHIFT_RULES['max_consecutive_nights']} "
                                 f"consecutive nights, then 48h rest minimum."
            })

    # Check rotation direction (backward rotation is harmful)
    if len(classified) >= 2:
        for i in range(1, len(classified)):
            prev_type = classified[i-1]["classified_type"]
            curr_type = classified[i]["classified_type"]

            # Backward rotation: night → evening → day (going against circadian)
            backward = (
                (prev_type == "night" and curr_type == "evening") or
                (prev_type == "night" and curr_type == "day" and
                 _days_between(classified[i-1]["date"], classified[i]["date"]) <= 1) or
                (prev_type == "evening" and curr_type == "day" and
                 _days_between(classified[i-1]["date"], classified[i]["date"]) <= 1)
            )

            if backward:
                rest_hours = _hours_between_shifts(classified[i-1], classified[i])
                if rest_hours < 24:
                    violations.append({
                        "rule_id": "NS-002",
                        "rule_name": "Backward Shift Rotation",
                        "severity": "MEDIUM",
                        "description": f"{emp_shifts[0]['name']}: Backward rotation "
                                      f"({prev_type}→{curr_type}) with only {rest_hours:.0f}h rest. "
                                      f"Forward rotation (day→evening→night) is recommended.",
                        "affected_employees": emp_shifts[0]["name"],
                        "cost_impact": "Increased fatigue + health risk from circadian disruption",
                        "recommendation": "Use forward rotation or provide minimum 24h between type changes."
                    })
                    break  # Only flag once

    return violations


def calculate_premium_pay(shifts, hourly_rate=20.0):
    """
    Calculate premium pay obligations for a schedule.
    Returns per-shift premium breakdown and totals.
    """
    premiums = []
    total_base = 0
    total_premium = 0

    for shift in shifts:
        classified = classify_shift(shift)
        start = datetime.strptime(f"{shift['date']} {shift['start']}", "%Y-%m-%d %H:%M")
        end = datetime.strptime(f"{shift['date']} {shift['end']}", "%Y-%m-%d %H:%M")
        if end <= start:
            end += timedelta(days=1)
        hours = (end - start).total_seconds() / 3600

        base_pay = hours * hourly_rate
        actual_pay = hours * hourly_rate * classified["total_pay_multiplier"]
        premium_amount = actual_pay - base_pay

        total_base += base_pay
        total_premium += premium_amount

        if premium_amount > 0:
            premiums.append({
                "employee_id": shift["employee_id"],
                "name": shift.get("name", ""),
                "date": shift["date"],
                "shift_type": classified["classified_type"],
                "hours": round(hours, 1),
                "holiday": classified["holiday_name"],
                "differential": classified["differential"],
                "holiday_premium": classified["holiday_premium"],
                "total_multiplier": classified["total_pay_multiplier"],
                "base_pay": round(base_pay, 2),
                "actual_pay": round(actual_pay, 2),
                "premium_amount": round(premium_amount, 2),
            })

    return {
        "premiums": premiums,
        "total_base_pay": round(total_base, 2),
        "total_premium_pay": round(total_premium, 2),
        "total_pay": round(total_base + total_premium, 2),
        "premium_percentage": round(total_premium / max(1, total_base) * 100, 1),
    }


def generate_holiday_coverage_plan(employees, holiday_date, shifts_needed,
                                   employee_history=None, role=None):
    """
    Generate a fair holiday coverage plan.
    Returns ranked list of who should work based on fairness rotation.
    """
    if employee_history is None:
        employee_history = {}

    holiday_name = get_holiday_name(holiday_date) or "Holiday"
    holiday_group = _get_holiday_value_group(holiday_name)

    candidates = []
    for emp in employees:
        if emp.get("is_minor"):
            continue
        if role and emp.get("role", "").lower() != role.lower():
            continue

        emp_id = emp["id"]
        history = employee_history.get(emp_id, {})

        # Fairness signals
        holidays_worked = history.get("holidays_worked_this_year", 0)
        same_group_worked = history.get(f"{holiday_group}_worked", 0)
        last_year_same = history.get(f"worked_{holiday_name.replace(' ', '_').lower()}_last_year", False)

        # Score: lower = should work this time (more rested from holidays)
        burden_score = (
            holidays_worked * 10 +
            same_group_worked * 20 +
            (30 if last_year_same else 0)
        )

        candidates.append({
            "employee_id": emp_id,
            "name": emp["name"],
            "role": emp.get("role", ""),
            "seniority": emp.get("seniority", 0),
            "burden_score": burden_score,
            "holidays_worked_this_year": holidays_worked,
            "worked_same_holiday_last_year": last_year_same,
            "reason": _holiday_reason(holidays_worked, last_year_same, same_group_worked),
        })

    # Sort: lowest burden first (they should work, they've had it easier)
    candidates.sort(key=lambda x: x["burden_score"])

    # Mark top N as "assigned"
    for i, c in enumerate(candidates):
        c["assigned"] = i < shifts_needed
        c["rank"] = i + 1

    return {
        "holiday": holiday_name,
        "date": holiday_date,
        "shifts_needed": shifts_needed,
        "candidates": candidates,
        "assigned": [c for c in candidates if c["assigned"]],
        "available_backup": [c for c in candidates if not c["assigned"]][:3],
    }


# --- Private helpers ---

def _days_between(date1, date2):
    d1 = datetime.strptime(date1, "%Y-%m-%d")
    d2 = datetime.strptime(date2, "%Y-%m-%d")
    return abs((d2 - d1).days)


def _hours_between_shifts(shift1, shift2):
    end1 = datetime.strptime(f"{shift1['date']} {shift1['end']}", "%Y-%m-%d %H:%M")
    start2 = datetime.strptime(f"{shift2['date']} {shift2['start']}", "%Y-%m-%d %H:%M")
    if end1 > start2:
        end1 -= timedelta(days=1)
    return (start2 - end1).total_seconds() / 3600


def _get_holiday_value_group(holiday_name):
    for group, holidays in HOLIDAY_VALUE_GROUPS.items():
        if holiday_name in holidays:
            return group
    return "other"


def _holiday_reason(holidays_worked, worked_last_year, same_group):
    reasons = []
    if holidays_worked == 0:
        reasons.append("Hasn't worked any holidays this year")
    elif holidays_worked >= 3:
        reasons.append(f"Already worked {holidays_worked} holidays")

    if worked_last_year:
        reasons.append("Worked this same holiday last year")

    if same_group >= 2:
        reasons.append("Worked multiple holidays in same group")

    return " | ".join(reasons) if reasons else "Standard rotation"


if __name__ == "__main__":
    from sample_schedule import generate_schedule, EMPLOYEES

    schedule = generate_schedule()

    print("=" * 70)
    print("  SHIFT INTELLIGENCE MODULE")
    print("=" * 70)

    # Analyze schedule
    analysis = analyze_schedule_shifts(schedule["shifts"])
    summary = analysis["summary"]

    print(f"\n  Schedule Analysis:")
    print(f"    Total shifts: {summary['total_shifts']}")
    print(f"    Day shifts:   {summary['day_shifts']}")
    print(f"    Evening:      {summary['evening_shifts']}")
    print(f"    Night:        {summary['night_shifts']}")
    print(f"    Holiday:      {summary['holiday_shifts']}")

    # Premium pay calculation
    print(f"\n  Premium Pay Calculation (at $20/hr base):")
    pay = calculate_premium_pay(schedule["shifts"], hourly_rate=20.0)
    print(f"    Total base pay:    ${pay['total_base_pay']:,.2f}")
    print(f"    Premium pay:       ${pay['total_premium_pay']:,.2f}")
    print(f"    Total pay:         ${pay['total_pay']:,.2f}")
    print(f"    Premium %:         {pay['premium_percentage']}%")

    if pay["premiums"]:
        print(f"\n    Premium Breakdown:")
        for p in pay["premiums"][:5]:
            print(f"      {p['name']:<20} {p['date']} {p['shift_type']:<8} "
                  f"x{p['total_multiplier']} = +${p['premium_amount']:.2f}")

    # Holiday coverage plan
    print(f"\n\n  HOLIDAY COVERAGE PLAN - Independence Day 2026")
    print(f"  {'-'*50}")

    demo_history = {
        "E001": {"holidays_worked_this_year": 2, "worked_Independence Day (Observed)_last_year": True},
        "E002": {"holidays_worked_this_year": 1, "worked_Independence Day (Observed)_last_year": False},
        "E003": {"holidays_worked_this_year": 0, "worked_Independence Day (Observed)_last_year": False},
        "E005": {"holidays_worked_this_year": 3, "worked_Independence Day (Observed)_last_year": True},
        "E008": {"holidays_worked_this_year": 1, "worked_Independence Day (Observed)_last_year": True},
        "E010": {"holidays_worked_this_year": 0, "worked_Independence Day (Observed)_last_year": False},
    }

    plan = generate_holiday_coverage_plan(
        EMPLOYEES, "2026-07-04", shifts_needed=3,
        employee_history=demo_history, role="Pick"
    )

    print(f"  Holiday: {plan['holiday']} ({plan['date']})")
    print(f"  Shifts needed: {plan['shifts_needed']}")
    print(f"\n  {'Rank':<5} {'Name':<20} {'Assigned':<10} {'Holidays Worked':<16} {'Reason'}")
    print(f"  {'-'*75}")
    for c in plan["candidates"]:
        assigned = "YES" if c["assigned"] else ""
        print(f"  {c['rank']:<5} {c['name']:<20} {assigned:<10} "
              f"{c['holidays_worked_this_year']:<16} {c['reason'][:35]}")

    # Night shift compliance check
    print(f"\n\n  NIGHT SHIFT COMPLIANCE CHECK")
    print(f"  {'-'*50}")
    for emp in EMPLOYEES[:5]:
        violations = check_night_shift_compliance(schedule["shifts"], emp["id"])
        if violations:
            for v in violations:
                desc = v['description'].replace('→', '->')
                print(f"  [{v['severity']}] {desc}")

    # Upcoming holidays
    print(f"\n\n  UPCOMING HOLIDAYS (July-December 2026):")
    holidays = get_holidays_in_range("2026-07-01", "2026-12-31")
    for h in holidays:
        print(f"    {h['date']}  {h['name']}")
