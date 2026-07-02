"""
Workforce Compliance AI - Fixed Shift Template System
Supports Amazon FC-style fixed shift codes where AAs have permanent recurring schedules.
Intelligence layer handles coverage, VET/MET, holidays, and LOA gaps.
"""

from datetime import datetime, timedelta
from collections import defaultdict
from hours_tracker import OT_THRESHOLD_WEEKLY, MAX_WEEKLY_HOURS


# Shift template definitions (modeled from Amazon FC patterns)
# Format: [Schedule Group][Number]-[Start Time]-[Department]
SHIFT_TEMPLATES = {
    "DA5-0700-IB": {
        "code": "DA5-0700-IB",
        "department": "Inbound",
        "start_time": "07:00",
        "schedule_type": "front_half",
        "pattern": {
            "Sun": {"start": "06:00", "end": "17:30", "hours": 11},
            "Mon": {"start": "06:00", "end": "17:30", "hours": 11},
            "Tue": {"start": "07:00", "end": "17:30", "hours": 10},
            "Wed": {"start": "07:00", "end": "17:30", "hours": 10},
        },
        "weekly_hours": 42,
        "days_on": ["Sun", "Mon", "Tue", "Wed"],
        "days_off": ["Thu", "Fri", "Sat"],
        "is_baseline": True,
    },
    "DA6-0700-IB": {
        "code": "DA6-0700-IB",
        "department": "Inbound",
        "start_time": "07:00",
        "schedule_type": "front_half",
        "pattern": {
            "Sun": {"start": "06:00", "end": "17:30", "hours": 11},
            "Mon": {"start": "06:00", "end": "17:30", "hours": 11},
            "Tue": {"start": "07:00", "end": "17:30", "hours": 10},
            "Wed": {"start": "07:00", "end": "17:30", "hours": 10},
        },
        "weekly_hours": 42,
        "days_on": ["Sun", "Mon", "Tue", "Wed"],
        "days_off": ["Thu", "Fri", "Sat"],
        "is_baseline": True,
    },
    "DA7-0700-IB": {
        "code": "DA7-0700-IB",
        "department": "Inbound",
        "start_time": "07:00",
        "schedule_type": "front_half",
        "pattern": {
            "Sun": {"start": "06:00", "end": "17:30", "hours": 11},
            "Mon": {"start": "06:00", "end": "17:30", "hours": 11},
            "Tue": {"start": "07:00", "end": "17:30", "hours": 10},
            "Wed": {"start": "07:00", "end": "17:30", "hours": 10},
        },
        "weekly_hours": 42,
        "days_on": ["Sun", "Mon", "Tue", "Wed"],
        "days_off": ["Thu", "Fri", "Sat"],
        "is_baseline": True,
    },
    "DB1-0700-IB": {
        "code": "DB1-0700-IB",
        "department": "Inbound",
        "start_time": "07:00",
        "schedule_type": "back_half",
        "pattern": {
            "Sun": {"start": "06:00", "end": "17:30", "hours": 11},
            "Wed": {"start": "07:00", "end": "17:30", "hours": 10},
            "Thu": {"start": "07:00", "end": "17:30", "hours": 10},
            "Fri": {"start": "07:00", "end": "17:30", "hours": 10},
            "Sat": {"start": "07:00", "end": "12:00", "hours": 5},
        },
        "weekly_hours": 46,
        "days_on": ["Sun", "Wed", "Thu", "Fri", "Sat"],
        "days_off": ["Mon", "Tue"],
        "is_baseline": True,
    },
    "DB2-0700-IB": {
        "code": "DB2-0700-IB",
        "department": "Inbound",
        "start_time": "07:00",
        "schedule_type": "back_half",
        "pattern": {
            "Mon": {"start": "06:00", "end": "17:30", "hours": 11},
            "Wed": {"start": "07:00", "end": "17:30", "hours": 10},
            "Thu": {"start": "07:00", "end": "17:30", "hours": 10},
            "Fri": {"start": "07:00", "end": "17:30", "hours": 10},
            "Sat": {"start": "07:00", "end": "12:00", "hours": 5},
        },
        "weekly_hours": 46,
        "days_on": ["Mon", "Wed", "Thu", "Fri", "Sat"],
        "days_off": ["Sun", "Tue"],
        "is_baseline": True,
    },
    "DB3-0700-IB": {
        "code": "DB3-0700-IB",
        "department": "Inbound",
        "start_time": "07:00",
        "schedule_type": "back_half",
        "pattern": {
            "Tue": {"start": "07:00", "end": "17:30", "hours": 10},
            "Wed": {"start": "07:00", "end": "17:30", "hours": 10},
            "Thu": {"start": "07:00", "end": "17:30", "hours": 10},
            "Fri": {"start": "07:00", "end": "17:30", "hours": 10},
            "Sat": {"start": "07:00", "end": "12:00", "hours": 5},
        },
        "weekly_hours": 45,
        "days_on": ["Tue", "Wed", "Thu", "Fri", "Sat"],
        "days_off": ["Sun", "Mon"],
        "is_baseline": True,
    },
    "DC1-0700-IB": {
        "code": "DC1-0700-IB",
        "department": "Inbound",
        "start_time": "07:00",
        "schedule_type": "mid_week",
        "pattern": {
            "Sun": {"start": "06:00", "end": "17:30", "hours": 11},
            "Mon": {"start": "06:00", "end": "17:30", "hours": 11},
            "Tue": {"start": "07:00", "end": "17:30", "hours": 10},
            "Thu": {"start": "07:00", "end": "17:30", "hours": 10},
            "Fri": {"start": "07:00", "end": "17:30", "hours": 10},
        },
        "weekly_hours": 52,
        "days_on": ["Sun", "Mon", "Tue", "Thu", "Fri"],
        "days_off": ["Wed", "Sat"],
        "is_baseline": True,
    },
    "DL4-0700-IB": {
        "code": "DL4-0700-IB",
        "department": "Inbound",
        "start_time": "07:00",
        "schedule_type": "front_heavy",
        "pattern": {
            "Sun": {"start": "06:00", "end": "17:30", "hours": 11},
            "Mon": {"start": "06:00", "end": "17:30", "hours": 11},
            "Tue": {"start": "06:00", "end": "17:30", "hours": 11},
            "Wed": {"start": "07:00", "end": "17:30", "hours": 10},
            "Sat": {"start": "07:00", "end": "12:00", "hours": 5},
        },
        "weekly_hours": 48,
        "days_on": ["Sun", "Mon", "Tue", "Wed", "Sat"],
        "days_off": ["Thu", "Fri"],
        "is_baseline": True,
    },
    # Night shift examples
    "NA1-1800-IB": {
        "code": "NA1-1800-IB",
        "department": "Inbound",
        "start_time": "18:00",
        "schedule_type": "front_half_night",
        "pattern": {
            "Sun": {"start": "18:00", "end": "05:30", "hours": 11},
            "Mon": {"start": "18:00", "end": "05:30", "hours": 11},
            "Tue": {"start": "19:00", "end": "05:30", "hours": 10},
            "Wed": {"start": "19:00", "end": "05:30", "hours": 10},
        },
        "weekly_hours": 42,
        "days_on": ["Sun", "Mon", "Tue", "Wed"],
        "days_off": ["Thu", "Fri", "Sat"],
        "is_baseline": True,
    },
    "NB1-1800-IB": {
        "code": "NB1-1800-IB",
        "department": "Inbound",
        "start_time": "18:00",
        "schedule_type": "back_half_night",
        "pattern": {
            "Wed": {"start": "19:00", "end": "05:30", "hours": 10},
            "Thu": {"start": "19:00", "end": "05:30", "hours": 10},
            "Fri": {"start": "19:00", "end": "05:30", "hours": 10},
            "Sat": {"start": "19:00", "end": "05:30", "hours": 10},
        },
        "weekly_hours": 40,
        "days_on": ["Wed", "Thu", "Fri", "Sat"],
        "days_off": ["Sun", "Mon", "Tue"],
        "is_baseline": True,
    },
}

# AA assignments to shift codes
SHIFT_ASSIGNMENTS = [
    {"employee_id": "E001", "name": "Sarah Martinez", "shift_code": "DA5-0700-IB", "role": "Pick", "start_date": "2025-01-15"},
    {"employee_id": "E002", "name": "James Wilson", "shift_code": "DA6-0700-IB", "role": "Pack", "start_date": "2024-06-01"},
    {"employee_id": "E003", "name": "Aisha Patel", "shift_code": "DA7-0700-IB", "role": "Pick", "start_date": "2024-09-10"},
    {"employee_id": "E004", "name": "Marcus Johnson", "shift_code": "DB1-0700-IB", "role": "Stow", "start_date": "2024-03-01"},
    {"employee_id": "E005", "name": "Chen Wei", "shift_code": "DB2-0700-IB", "role": "Pick", "start_date": "2024-08-15"},
    {"employee_id": "E006", "name": "Tyler Brooks", "shift_code": "DB3-0700-IB", "role": "Pack", "start_date": "2025-06-01"},
    {"employee_id": "E007", "name": "Rosa Hernandez", "shift_code": "DC1-0700-IB", "role": "Stow", "start_date": "2024-11-01"},
    {"employee_id": "E008", "name": "David Kim", "shift_code": "NA1-1800-IB", "role": "Pick", "start_date": "2024-07-01"},
    {"employee_id": "E009", "name": "Fatima Ali", "shift_code": "NB1-1800-IB", "role": "Ship", "start_date": "2025-02-01"},
    {"employee_id": "E010", "name": "Jake Thompson", "shift_code": "DL4-0700-IB", "role": "Pick", "start_date": "2025-04-01"},
]

# Absence types
ABSENCE_TYPES = {
    "LOA": {"name": "Leave of Absence", "coverage_required": True, "advance_notice": True},
    "FMLA": {"name": "FMLA Leave", "coverage_required": True, "advance_notice": True},
    "PTO": {"name": "Paid Time Off", "coverage_required": True, "advance_notice": True},
    "CALLOUT": {"name": "Unplanned Callout", "coverage_required": True, "advance_notice": False},
    "BEREAVEMENT": {"name": "Bereavement", "coverage_required": True, "advance_notice": False},
    "JURY_DUTY": {"name": "Jury Duty", "coverage_required": True, "advance_notice": True},
    "UPT": {"name": "Unpaid Time (partial day)", "coverage_required": False, "advance_notice": False},
}

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def get_day_name(date_obj):
    """Get abbreviated day name from a date."""
    if isinstance(date_obj, str):
        date_obj = datetime.strptime(date_obj, "%Y-%m-%d")
    return DAY_NAMES[date_obj.weekday()]


def generate_week_schedule(shift_code, week_start_date):
    """
    Generate actual shift instances from a template for a given week.
    week_start_date should be the Sunday of the target week.
    """
    if isinstance(week_start_date, str):
        week_start_date = datetime.strptime(week_start_date, "%Y-%m-%d")

    template = SHIFT_TEMPLATES.get(shift_code)
    if not template:
        return []

    shifts = []
    day_offsets = {"Sun": 0, "Mon": 1, "Tue": 2, "Wed": 3, "Thu": 4, "Fri": 5, "Sat": 6}

    for day_name, day_info in template["pattern"].items():
        offset = day_offsets[day_name]
        shift_date = week_start_date + timedelta(days=offset)
        shifts.append({
            "date": shift_date.strftime("%Y-%m-%d"),
            "day": day_name,
            "start": day_info["start"],
            "end": day_info["end"],
            "hours": day_info["hours"],
            "shift_code": shift_code,
        })

    return sorted(shifts, key=lambda x: x["date"])


def get_employee_schedule(employee_id, week_start_date):
    """Get an employee's scheduled shifts for a week based on their shift code."""
    assignment = next((a for a in SHIFT_ASSIGNMENTS if a["employee_id"] == employee_id), None)
    if not assignment:
        return None

    shifts = generate_week_schedule(assignment["shift_code"], week_start_date)
    for s in shifts:
        s["employee_id"] = employee_id
        s["name"] = assignment["name"]
        s["role"] = assignment["role"]
    return shifts


def find_coverage_for_absence(absent_employee_id, absence_date, absence_type="CALLOUT",
                              vet_met_history=None):
    """
    Find coverage candidates when an AA on a fixed shift is absent.
    Looks for employees whose shift code has that day as an OFF day.

    Returns candidates ranked by fairness:
    1. People whose off-day aligns (natural fit for VET)
    2. Fairness: who's been asked least, who has lowest VET hours this period
    3. Qualifications match
    """
    if isinstance(absence_date, str):
        absence_date_dt = datetime.strptime(absence_date, "%Y-%m-%d")
    else:
        absence_date_dt = absence_date
        absence_date = absence_date_dt.strftime("%Y-%m-%d")

    day_name = get_day_name(absence_date_dt)

    absent_assignment = next(
        (a for a in SHIFT_ASSIGNMENTS if a["employee_id"] == absent_employee_id), None
    )
    if not absent_assignment:
        return {"error": f"Employee {absent_employee_id} not found"}

    absent_template = SHIFT_TEMPLATES[absent_assignment["shift_code"]]
    absent_shift_info = absent_template["pattern"].get(day_name)

    if not absent_shift_info:
        return {"error": f"{absent_assignment['name']} is not scheduled on {day_name}"}

    if vet_met_history is None:
        vet_met_history = {}

    candidates = []

    for assignment in SHIFT_ASSIGNMENTS:
        if assignment["employee_id"] == absent_employee_id:
            continue

        template = SHIFT_TEMPLATES[assignment["shift_code"]]

        # Check if this day is their OFF day (available for VET)
        is_off_day = day_name in template.get("days_off", [])

        # Check if they're qualified (same department or cross-trained)
        same_dept = template["department"] == absent_template["department"]
        role_match = assignment["role"] == absent_assignment["role"]

        if not same_dept:
            continue

        # Calculate current week hours if they take this extra shift
        current_weekly = template["weekly_hours"]
        projected_weekly = current_weekly + absent_shift_info["hours"]

        # Would exceed cap?
        exceeds_cap = projected_weekly > MAX_WEEKLY_HOURS

        # VET/MET history for fairness
        history = vet_met_history.get(assignment["employee_id"], _default_vet_history())
        vet_hours_this_period = history.get("vet_hours_this_period", 0)
        met_hours_this_period = history.get("met_hours_this_period", 0)
        times_asked = history.get("times_asked_this_month", 0)
        times_accepted = history.get("times_accepted_this_month", 0)

        # Fairness score (higher = better candidate to ask)
        fairness_score = _calculate_vet_fairness(
            is_off_day, role_match, vet_hours_this_period,
            met_hours_this_period, times_asked, projected_weekly, exceeds_cap
        )

        # Shift compatibility (day shift person covering night shift is harder)
        same_time_block = _same_time_block(template["start_time"], absent_template["start_time"])

        candidates.append({
            "employee_id": assignment["employee_id"],
            "name": assignment["name"],
            "shift_code": assignment["shift_code"],
            "role": assignment["role"],
            "is_off_day": is_off_day,
            "role_match": role_match,
            "same_time_block": same_time_block,
            "current_weekly_hours": current_weekly,
            "projected_weekly_hours": projected_weekly,
            "exceeds_cap": exceeds_cap,
            "fairness_score": round(fairness_score, 1),
            "vet_hours_this_period": vet_hours_this_period,
            "met_hours_this_period": met_hours_this_period,
            "times_asked": times_asked,
            "coverage_type": "VET" if is_off_day else "MET",
            "shift_to_cover": {
                "date": absence_date,
                "day": day_name,
                "start": absent_shift_info["start"],
                "end": absent_shift_info["end"],
                "hours": absent_shift_info["hours"],
            },
        })

    # Sort: off-day people first (VET), then by fairness score descending
    candidates.sort(key=lambda x: (-x["is_off_day"], -x["fairness_score"]))

    # Split into VET and MET pools
    vet_pool = [c for c in candidates if c["is_off_day"] and not c["exceeds_cap"]]
    met_pool = [c for c in candidates if not c["is_off_day"] and not c["exceeds_cap"]]
    blocked = [c for c in candidates if c["exceeds_cap"]]

    return {
        "absent_employee": absent_assignment["name"],
        "absent_shift_code": absent_assignment["shift_code"],
        "absence_date": absence_date,
        "absence_day": day_name,
        "absence_type": absence_type,
        "shift_to_cover": {
            "start": absent_shift_info["start"],
            "end": absent_shift_info["end"],
            "hours": absent_shift_info["hours"],
        },
        "vet_candidates": vet_pool,
        "met_candidates": met_pool,
        "blocked_candidates": blocked,
        "recommendation": _build_coverage_recommendation(vet_pool, met_pool, absence_type),
    }


def plan_holiday_coverage(holiday_date, department="Inbound", min_coverage_pct=0.5,
                          vet_met_history=None):
    """
    Plan coverage for a holiday when some shift codes are running.
    Determines which shift codes normally work that day and who's needed.
    """
    if isinstance(holiday_date, str):
        holiday_date_dt = datetime.strptime(holiday_date, "%Y-%m-%d")
    else:
        holiday_date_dt = holiday_date
        holiday_date = holiday_date_dt.strftime("%Y-%m-%d")

    day_name = get_day_name(holiday_date_dt)

    if vet_met_history is None:
        vet_met_history = {}

    # Find which shift codes normally work this day
    scheduled_codes = []
    off_day_codes = []

    for code, template in SHIFT_TEMPLATES.items():
        if template["department"] != department:
            continue
        if day_name in template.get("days_on", []):
            scheduled_codes.append(code)
        else:
            off_day_codes.append(code)

    # Find AAs normally scheduled
    normally_working = []
    for assignment in SHIFT_ASSIGNMENTS:
        if assignment["shift_code"] in scheduled_codes:
            normally_working.append(assignment)

    # Find AAs who are off (potential VET pool)
    off_day_pool = []
    for assignment in SHIFT_ASSIGNMENTS:
        if assignment["shift_code"] in off_day_codes:
            off_day_pool.append(assignment)

    # Calculate minimum headcount needed
    total_normal = len(normally_working)
    min_needed = max(1, int(total_normal * min_coverage_pct))

    # Rank VET candidates by fairness
    vet_ranked = []
    for assignment in off_day_pool:
        history = vet_met_history.get(assignment["employee_id"], _default_vet_history())
        holidays_worked = history.get("holidays_worked_this_year", 0)
        vet_hours = history.get("vet_hours_this_period", 0)

        # Lower score = should work this holiday (more rested from holidays)
        burden = holidays_worked * 15 + vet_hours * 2
        vet_ranked.append({
            **assignment,
            "burden_score": burden,
            "holidays_worked": holidays_worked,
            "vet_hours": vet_hours,
        })

    vet_ranked.sort(key=lambda x: x["burden_score"])

    return {
        "holiday_date": holiday_date,
        "day": day_name,
        "department": department,
        "normally_scheduled": normally_working,
        "total_normally_working": total_normal,
        "minimum_coverage_needed": min_needed,
        "coverage_percentage": min_coverage_pct,
        "vet_pool_available": vet_ranked,
        "vet_pool_size": len(vet_ranked),
        "scheduled_shift_codes": scheduled_codes,
        "off_day_shift_codes": off_day_codes,
        "recommendation": (
            f"Need {min_needed} AAs minimum ({min_coverage_pct*100:.0f}% of normal {total_normal}). "
            f"{len(vet_ranked)} available from off-day shift codes for VET."
        ),
    }


def get_vet_met_dashboard(vet_met_history=None):
    """
    Generate a VET/MET fairness dashboard showing distribution across all AAs.
    """
    if vet_met_history is None:
        vet_met_history = {}

    dashboard = []
    for assignment in SHIFT_ASSIGNMENTS:
        emp_id = assignment["employee_id"]
        history = vet_met_history.get(emp_id, _default_vet_history())

        dashboard.append({
            "employee_id": emp_id,
            "name": assignment["name"],
            "shift_code": assignment["shift_code"],
            "role": assignment["role"],
            "base_weekly_hours": SHIFT_TEMPLATES[assignment["shift_code"]]["weekly_hours"],
            "vet_hours_this_period": history.get("vet_hours_this_period", 0),
            "met_hours_this_period": history.get("met_hours_this_period", 0),
            "total_extra_hours": history.get("vet_hours_this_period", 0) + history.get("met_hours_this_period", 0),
            "times_asked": history.get("times_asked_this_month", 0),
            "times_accepted": history.get("times_accepted_this_month", 0),
            "acceptance_rate": (
                round(history.get("times_accepted_this_month", 0) /
                      max(1, history.get("times_asked_this_month", 1)) * 100)
            ),
            "holidays_worked": history.get("holidays_worked_this_year", 0),
        })

    dashboard.sort(key=lambda x: x["total_extra_hours"])
    return dashboard


def get_shift_code_summary():
    """Get a summary of all shift codes and their patterns."""
    summary = []
    for code, template in SHIFT_TEMPLATES.items():
        summary.append({
            "code": code,
            "department": template["department"],
            "type": template["schedule_type"],
            "start_time": template["start_time"],
            "days_on": ", ".join(template["days_on"]),
            "days_off": ", ".join(template.get("days_off", [])),
            "weekly_hours": template["weekly_hours"],
            "is_baseline": template["is_baseline"],
        })
    return summary


# --- Private helpers ---

def _calculate_vet_fairness(is_off_day, role_match, vet_hours, met_hours,
                            times_asked, projected_weekly, exceeds_cap):
    """Calculate fairness score for VET/MET assignment."""
    if exceeds_cap:
        return 0

    score = 50  # baseline

    if is_off_day:
        score += 20  # natural fit

    if role_match:
        score += 15
    else:
        score += 5  # cross-trained OK but not ideal

    # Less VET this period = higher score (fairer to ask them)
    if vet_hours == 0:
        score += 20
    elif vet_hours <= 10:
        score += 10
    elif vet_hours >= 20:
        score -= 10

    # Asked fewer times = higher score
    if times_asked == 0:
        score += 15
    elif times_asked <= 2:
        score += 5
    elif times_asked >= 5:
        score -= 15

    # Penalize if projected hours are high
    if projected_weekly > 50:
        score -= 10
    elif projected_weekly > 55:
        score -= 20

    return max(0, min(100, score))


def _same_time_block(time1, time2):
    """Check if two shift start times are in the same block (day/night)."""
    h1 = int(time1.split(":")[0])
    h2 = int(time2.split(":")[0])

    is_day_1 = 5 <= h1 < 17
    is_day_2 = 5 <= h2 < 17

    return is_day_1 == is_day_2


def _build_coverage_recommendation(vet_pool, met_pool, absence_type):
    """Build recommendation based on available coverage."""
    if vet_pool:
        top = vet_pool[0]
        return (
            f"Offer VET to {top['name']} ({top['shift_code']}, off-day, "
            f"fairness score {top['fairness_score']}). "
            f"{len(vet_pool)} total VET candidates available."
        )
    elif met_pool:
        top = met_pool[0]
        return (
            f"No VET candidates available. Consider MET for {top['name']} "
            f"({top['shift_code']}, fairness score {top['fairness_score']}). "
            f"Note: MET requires advance notice per CBA."
        )
    else:
        return "No eligible candidates found. Consider agency/temp staffing."


def _default_vet_history():
    return {
        "vet_hours_this_period": 0,
        "met_hours_this_period": 0,
        "times_asked_this_month": 0,
        "times_accepted_this_month": 0,
        "holidays_worked_this_year": 0,
    }


if __name__ == "__main__":
    print("=" * 70)
    print("  FIXED SHIFT TEMPLATE SYSTEM")
    print("=" * 70)

    # Show all shift codes
    print(f"\n  SHIFT CODE SUMMARY:")
    print(f"  {'Code':<16} {'Type':<20} {'Days On':<25} {'Weekly Hrs':<10}")
    print(f"  {'-'*75}")
    for s in get_shift_code_summary():
        print(f"  {s['code']:<16} {s['type']:<20} {s['days_on']:<25} {s['weekly_hours']:<10}")

    # Show AA assignments
    print(f"\n\n  AA SHIFT ASSIGNMENTS:")
    print(f"  {'Name':<20} {'Shift Code':<16} {'Role':<8} {'Days On':<25}")
    print(f"  {'-'*70}")
    for a in SHIFT_ASSIGNMENTS:
        template = SHIFT_TEMPLATES[a["shift_code"]]
        print(f"  {a['name']:<20} {a['shift_code']:<16} {a['role']:<8} {', '.join(template['days_on']):<25}")

    # Demo: Coverage for absence
    print(f"\n\n  COVERAGE SCENARIO: Sarah Martinez calls out on Tuesday")
    print(f"  {'-'*50}")

    demo_history = {
        "E004": {"vet_hours_this_period": 0, "met_hours_this_period": 0, "times_asked_this_month": 1, "times_accepted_this_month": 1, "holidays_worked_this_year": 1},
        "E005": {"vet_hours_this_period": 10, "met_hours_this_period": 0, "times_asked_this_month": 3, "times_accepted_this_month": 2, "holidays_worked_this_year": 2},
        "E008": {"vet_hours_this_period": 5, "met_hours_this_period": 0, "times_asked_this_month": 2, "times_accepted_this_month": 2, "holidays_worked_this_year": 0},
        "E009": {"vet_hours_this_period": 0, "met_hours_this_period": 0, "times_asked_this_month": 0, "times_accepted_this_month": 0, "holidays_worked_this_year": 0},
    }

    result = find_coverage_for_absence("E001", "2026-07-07", "CALLOUT", demo_history)

    print(f"  Absent: {result['absent_employee']} ({result['absent_shift_code']})")
    print(f"  Date: {result['absence_date']} ({result['absence_day']})")
    print(f"  Shift to cover: {result['shift_to_cover']['start']}-{result['shift_to_cover']['end']} ({result['shift_to_cover']['hours']}h)")
    print(f"\n  Recommendation: {result['recommendation']}")

    if result["vet_candidates"]:
        print(f"\n  VET CANDIDATES (off-day, fairness-ranked):")
        print(f"  {'Name':<20} {'Shift Code':<16} {'Score':<7} {'VET Hrs':<9} {'Asked'}")
        print(f"  {'-'*60}")
        for c in result["vet_candidates"]:
            print(f"  {c['name']:<20} {c['shift_code']:<16} {c['fairness_score']:<7} "
                  f"{c['vet_hours_this_period']:<9} {c['times_asked']}")

    if result["met_candidates"]:
        print(f"\n  MET CANDIDATES (already working, can extend):")
        for c in result["met_candidates"][:3]:
            print(f"  {c['name']:<20} {c['shift_code']:<16} score={c['fairness_score']}")

    # Holiday coverage plan
    print(f"\n\n  HOLIDAY COVERAGE PLAN: July 4, 2026")
    print(f"  {'-'*50}")
    plan = plan_holiday_coverage("2026-07-04", department="Inbound", min_coverage_pct=0.5, vet_met_history=demo_history)
    print(f"  Day: {plan['day']}")
    print(f"  Normally working: {plan['total_normally_working']} AAs")
    print(f"  Minimum needed: {plan['minimum_coverage_needed']} ({plan['coverage_percentage']*100:.0f}%)")
    print(f"  VET pool: {plan['vet_pool_size']} available")
    print(f"\n  Recommendation: {plan['recommendation']}")
