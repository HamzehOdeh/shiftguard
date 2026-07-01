"""
Workforce Compliance AI - Schedule Generator
Core product module: takes headcount + demand plan + employee profiles + rules
and outputs a fully compliant, fair schedule from scratch.

Industry-agnostic design - shift/role structures work for:
warehouse, healthcare, retail, manufacturing, hospitality.
Comments note where industry-specific logic would plug in.
"""

from datetime import datetime, timedelta, date
from collections import defaultdict
from copy import deepcopy
import random
import math

# ============================================================
# 1. DEMAND PLAN STRUCTURE
# Defines what the business needs for each day/shift/role.
# Industry plug-in: override role names, shift times, demand curves.
# ============================================================

DEMAND_PLAN = {
    "week_start": "2026-07-06",  # Monday
    "week_end": "2026-07-12",    # Sunday
    "facility": "Distribution Center - West",
    "timezone": "America/Los_Angeles",
    # Industry plug-in: shift definitions vary by sector
    # Healthcare: 7a-7p / 7p-7a (12-hr shifts)
    # Retail: open/mid/close
    # Manufacturing: 1st/2nd/3rd shift
    "shifts": {
        "day": {"start": "06:00", "end": "14:30", "duration_hours": 8.5, "label": "Day Shift"},
        "night": {"start": "16:00", "end": "00:30", "duration_hours": 8.5, "label": "Night Shift"},
        "flex": {"start": "10:00", "end": "18:30", "duration_hours": 8.5, "label": "Flex Shift"},
    },
    # Industry plug-in: roles differ by sector
    # Healthcare: RN, CNA, RT, Phlebotomist
    # Retail: Cashier, Floor, Stock, Manager
    # Manufacturing: Operator, QC, Maintenance, Logistics
    "roles": {
        "pick": {"label": "Pick", "demand_pct": 0.50, "skill_required": "pick_certified"},
        "pack": {"label": "Pack", "demand_pct": 0.25, "skill_required": "pack_certified"},
        "stow": {"label": "Stow", "demand_pct": 0.15, "skill_required": "stow_certified"},
        "ship": {"label": "Ship", "demand_pct": 0.10, "skill_required": "ship_certified"},
    },
    # Daily demand: headcount needed per shift
    # Higher Wed-Sat (peak mid-week + weekend prep), lower Sun-Mon
    # Calibrated for ~37 active employees at ~5 shifts/week each
    "daily_demand": {
        "Monday":    {"day": {"min": 8, "max": 10}, "night": {"min": 5, "max": 7}, "flex": {"min": 3, "max": 4}},
        "Tuesday":   {"day": {"min": 9, "max": 11}, "night": {"min": 6, "max": 8}, "flex": {"min": 3, "max": 5}},
        "Wednesday": {"day": {"min": 10, "max": 12}, "night": {"min": 7, "max": 9}, "flex": {"min": 4, "max": 5}},
        "Thursday":  {"day": {"min": 10, "max": 12}, "night": {"min": 7, "max": 9}, "flex": {"min": 4, "max": 5}},
        "Friday":    {"day": {"min": 11, "max": 13}, "night": {"min": 8, "max": 10}, "flex": {"min": 4, "max": 6}},
        "Saturday":  {"day": {"min": 10, "max": 12}, "night": {"min": 6, "max": 8}, "flex": {"min": 3, "max": 5}},
        "Sunday":    {"day": {"min": 7, "max": 9}, "night": {"min": 4, "max": 6}, "flex": {"min": 2, "max": 4}},
    },
    # ICQA (Inventory Control & Quality Assurance) - cross-shift need
    # Industry plug-in: audit/quality roles exist across sectors
    "icqa_daily_need": 2,  # 2 ICQA associates per day regardless of shift
}


# ============================================================
# 2. EMPLOYEE PROFILE STRUCTURE
# Everything about each Associate/Employee.
# Industry plug-in: certifications, license types differ by sector.
# ============================================================

def create_employee_profile(
    emp_id, name, seniority_rank, hire_date, certified_roles,
    availability=None, leave_status=None, hours_this_period=0.0,
    ot_hours_ytd=0.0, is_minor=False, max_hours_preference=40,
    consecutive_days_worked=0, preferred_shift=None, weekend_shifts_ytd=0
):
    """
    Create a standardized employee profile.

    Industry plug-in points:
    - certified_roles: healthcare would include license numbers and expiry dates
    - availability: retail might track "open availability" vs restricted
    - leave_status: manufacturing might track workers comp separately
    """
    return {
        "id": emp_id,
        "name": name,
        "seniority_rank": seniority_rank,  # 1 = most senior
        "hire_date": hire_date,
        "certified_roles": certified_roles,  # List of role keys they can perform
        "availability": availability or {
            "Monday": ["day", "night", "flex"],
            "Tuesday": ["day", "night", "flex"],
            "Wednesday": ["day", "night", "flex"],
            "Thursday": ["day", "night", "flex"],
            "Friday": ["day", "night", "flex"],
            "Saturday": ["day", "night", "flex"],
            "Sunday": ["day", "night", "flex"],
        },
        "leave_status": leave_status or {"type": None, "start": None, "end": None},
        "hours_this_period": hours_this_period,
        "ot_hours_ytd": ot_hours_ytd,
        "is_minor": is_minor,
        "max_hours_preference": max_hours_preference,
        "consecutive_days_worked": consecutive_days_worked,
        "preferred_shift": preferred_shift,  # "day", "night", or "flex"
        "weekend_shifts_ytd": weekend_shifts_ytd,
    }


# ============================================================
# 4. GENERATE 40 REALISTIC EMPLOYEES
# Mix of seniority, certifications, leave, minors, OT history.
# ============================================================

def generate_employees():
    """Generate 40 realistic employee profiles with varied characteristics."""

    first_names = [
        "Sarah", "James", "Aisha", "Marcus", "Chen", "Tyler", "Rosa", "David",
        "Fatima", "Jake", "Maria", "Andre", "Priya", "Carlos", "Emma", "Darnell",
        "Yuki", "Omar", "Nicole", "Kwame", "Sofia", "Liam", "Amara", "Jose",
        "Hannah", "DeShawn", "Mei", "Antonio", "Zara", "Patrick", "Nia", "Viktor",
        "Jasmine", "Raj", "Olivia", "Terrence", "Ana", "Mohammed", "Grace", "Diego"
    ]

    last_names = [
        "Martinez", "Wilson", "Patel", "Johnson", "Wei", "Brooks", "Hernandez", "Kim",
        "Ali", "Thompson", "Santos", "Williams", "Sharma", "Rodriguez", "Davis", "Jackson",
        "Tanaka", "Hassan", "Miller", "Asante", "Reyes", "O'Brien", "Okafor", "Gutierrez",
        "Lee", "Washington", "Zhang", "Morales", "Ibrahim", "Murphy", "Brown", "Petrov",
        "Taylor", "Krishnan", "Anderson", "Howard", "Lopez", "Ahmed", "Chen", "Flores"
    ]

    # Role certification patterns (some multi-role, some single)
    cert_patterns = [
        ["pick", "pack", "stow", "ship"],      # Fully cross-trained (senior)
        ["pick", "pack", "stow"],               # Mostly cross-trained
        ["pick", "pack"],                        # Dual-certified
        ["pick"],                                # Single role - pick
        ["pack"],                                # Single role - pack
        ["stow", "ship"],                       # Dual-certified
        ["pick", "stow"],                       # Dual-certified
        ["pack", "ship"],                       # Dual-certified
        ["pick", "pack", "ship"],               # Three roles
        ["stow"],                               # Single role - stow
    ]

    # Hire dates spanning several years (seniority-correlated)
    base_dates = [
        "2018-03-15", "2018-09-01", "2019-01-20", "2019-06-10", "2019-11-05",
        "2020-02-14", "2020-05-30", "2020-08-22", "2020-11-15", "2021-01-10",
        "2021-03-25", "2021-06-01", "2021-08-15", "2021-10-30", "2021-12-20",
        "2022-02-05", "2022-04-18", "2022-06-28", "2022-09-10", "2022-11-22",
        "2023-01-15", "2023-03-01", "2023-05-12", "2023-07-20", "2023-09-30",
        "2023-11-15", "2024-01-08", "2024-03-20", "2024-05-01", "2024-07-15",
        "2024-09-01", "2024-11-10", "2025-01-05", "2025-02-20", "2025-04-01",
        "2025-05-15", "2025-07-01", "2025-09-10", "2025-11-01", "2026-01-15",
    ]

    employees = []
    random.seed(42)  # Reproducible profiles

    for i in range(40):
        emp_id = f"E{i+1:03d}"
        name = f"{first_names[i]} {last_names[i]}"
        seniority = i + 1  # 1 = most senior
        hire_date = base_dates[i]

        # More senior employees have more certifications
        if seniority <= 5:
            certs = cert_patterns[0]  # Fully cross-trained
        elif seniority <= 10:
            certs = cert_patterns[random.randint(1, 2)]
        elif seniority <= 20:
            certs = cert_patterns[random.randint(2, 6)]
        elif seniority <= 30:
            certs = cert_patterns[random.randint(3, 7)]
        else:
            certs = cert_patterns[random.randint(3, 9)]

        # Shift preferences (senior employees more likely to get day shift)
        if seniority <= 10:
            preferred = "day"
        elif seniority <= 25:
            preferred = random.choice(["day", "day", "flex", "night"])
        else:
            preferred = random.choice(["day", "flex", "night", "night"])

        # OT history - varies to test equity
        ot_ytd = round(random.uniform(0, 120), 1)

        # Hours this period (start of week)
        hours_period = 0.0

        # Consecutive days worked (trailing from prior week)
        consec = random.choice([0, 0, 0, 1, 2, 3, 4, 5])

        # Weekend shifts YTD (for equity tracking)
        weekend_ytd = random.randint(5, 30)

        # Minors (2 employees) - determined early for max_hours logic
        is_minor = i in [5, 38]  # Tyler Brooks and Grace Chen

        # Max hours preference
        # Industry plug-in: healthcare often uses 36-hr weeks (3x12)
        if is_minor:
            max_hours = 20  # Minors restricted to part-time (federal/state child labor laws)
        elif seniority > 30:
            max_hours = 40
        else:
            max_hours = random.choice([40, 40, 40, 45, 50])

        # Default full availability
        availability = None

        # Some employees have restricted availability
        if i == 15:  # Darnell Jackson - no weekends
            availability = {
                "Monday": ["day", "night", "flex"],
                "Tuesday": ["day", "night", "flex"],
                "Wednesday": ["day", "night", "flex"],
                "Thursday": ["day", "night", "flex"],
                "Friday": ["day", "night", "flex"],
                "Saturday": [],
                "Sunday": [],
            }
        elif i == 22:  # Amara Okafor - mornings only
            availability = {
                "Monday": ["day"], "Tuesday": ["day"], "Wednesday": ["day"],
                "Thursday": ["day"], "Friday": ["day"], "Saturday": ["day"],
                "Sunday": ["day"],
            }
        elif i == 30:  # Nia Brown - no nights (childcare)
            availability = {
                "Monday": ["day", "flex"], "Tuesday": ["day", "flex"],
                "Wednesday": ["day", "flex"], "Thursday": ["day", "flex"],
                "Friday": ["day", "flex"], "Saturday": ["day", "flex"],
                "Sunday": ["day", "flex"],
            }
        elif i == 35:  # Terrence Howard - only 3 days/week
            availability = {
                "Monday": ["day", "night", "flex"],
                "Tuesday": [],
                "Wednesday": ["day", "night", "flex"],
                "Thursday": [],
                "Friday": ["day", "night", "flex"],
                "Saturday": [],
                "Sunday": [],
            }

        # Leave status - 2-3 employees on leave
        leave = {"type": None, "start": None, "end": None}
        if i == 8:  # Fatima Ali - FMLA
            leave = {"type": "FMLA", "start": "2026-06-20", "end": "2026-09-20"}
        elif i == 19:  # Kwame Asante - PTO
            leave = {"type": "PTO", "start": "2026-07-05", "end": "2026-07-12"}
        elif i == 33:  # Raj Krishnan - sick leave
            leave = {"type": "SICK", "start": "2026-07-04", "end": "2026-07-08"}

        emp = create_employee_profile(
            emp_id=emp_id,
            name=name,
            seniority_rank=seniority,
            hire_date=hire_date,
            certified_roles=certs,
            availability=availability,
            leave_status=leave,
            hours_this_period=hours_period,
            ot_hours_ytd=ot_ytd,
            is_minor=is_minor,
            max_hours_preference=max_hours,
            consecutive_days_worked=consec,
            preferred_shift=preferred,
            weekend_shifts_ytd=weekend_ytd,
        )
        employees.append(emp)

    return employees


# ============================================================
# 5. GENERATE REALISTIC DEMAND PLAN
# Already defined above in DEMAND_PLAN constant.
# This function builds a day-by-day slot list from the plan.
# ============================================================

def build_shift_slots(demand_plan):
    """
    Convert the demand plan into a list of individual slots to fill.
    Each slot = one person needed in a specific day/shift/role.

    Returns: list of dicts with day, shift_type, role, date_str
    """
    week_start = datetime.strptime(demand_plan["week_start"], "%Y-%m-%d")
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    roles = demand_plan["roles"]
    slots = []

    for day_idx, day_name in enumerate(days_of_week):
        current_date = week_start + timedelta(days=day_idx)
        date_str = current_date.strftime("%Y-%m-%d")
        day_demand = demand_plan["daily_demand"][day_name]

        for shift_type, shift_demand in day_demand.items():
            # Use the midpoint of min/max as target headcount
            target = (shift_demand["min"] + shift_demand["max"]) // 2

            # Distribute target across roles based on demand percentages
            for role_key, role_info in roles.items():
                role_count = max(1, round(target * role_info["demand_pct"]))
                for _ in range(role_count):
                    slots.append({
                        "date": date_str,
                        "day_name": day_name,
                        "shift_type": shift_type,
                        "role": role_key,
                        "assigned_to": None,
                    })

        # Add ICQA slots (industry plug-in: quality/audit roles)
        for _ in range(demand_plan["icqa_daily_need"]):
            slots.append({
                "date": date_str,
                "day_name": day_name,
                "shift_type": "day",  # ICQA typically on day shift
                "role": "pick",  # ICQA draws from pick-certified pool
                "assigned_to": None,
                "is_icqa": True,
            })

    return slots


# ============================================================
# 3. SCHEDULE GENERATOR - CORE ALGORITHM
# Assigns shifts respecting all rules and constraints.
# ============================================================

def _is_on_leave(employee, date_str):
    """Check if employee is on leave for a given date."""
    leave = employee["leave_status"]
    if leave["type"] is None:
        return False
    leave_start = datetime.strptime(leave["start"], "%Y-%m-%d").date()
    leave_end = datetime.strptime(leave["end"], "%Y-%m-%d").date()
    check_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    return leave_start <= check_date <= leave_end


def _is_available(employee, day_name, shift_type):
    """Check if employee is available for a given day/shift."""
    avail = employee["availability"]
    return shift_type in avail.get(day_name, [])


def _can_work_shift(employee, shift_type):
    """Check minor restrictions - no night shifts for minors."""
    # Industry plug-in: healthcare has different minor restrictions
    # Manufacturing may prohibit minors from certain equipment roles
    if employee["is_minor"] and shift_type == "night":
        return False
    return True


def _has_required_cert(employee, role):
    """Check if employee is certified for the role."""
    # Industry plug-in: healthcare checks license validity dates
    # Manufacturing checks equipment-specific certifications
    return role in employee["certified_roles"]


def _check_rest_period(employee_schedule, date_str, shift_type, demand_plan):
    """
    Ensure 10+ hours between end of last shift and start of new one.
    Industry plug-in: healthcare may require 11 or 12 hours (varies by state).
    """
    if not employee_schedule:
        return True

    shifts_def = demand_plan["shifts"]
    new_start = datetime.strptime(f"{date_str} {shifts_def[shift_type]['start']}", "%Y-%m-%d %H:%M")

    # Find the most recent shift
    last_shift = employee_schedule[-1]
    last_end_str = f"{last_shift['date']} {shifts_def[last_shift['shift_type']]['end']}"
    last_end = datetime.strptime(last_end_str, "%Y-%m-%d %H:%M")
    # Handle overnight shifts (end time is next day)
    if shifts_def[last_shift["shift_type"]]["end"] < shifts_def[last_shift["shift_type"]]["start"]:
        last_end += timedelta(days=1)

    hours_between = (new_start - last_end).total_seconds() / 3600
    return hours_between >= 10


def _check_consecutive_days(employee, employee_schedule, date_str):
    """
    Max 6 consecutive days. Combines trailing days with new assignments.
    Industry plug-in: some CBAs limit to 5; healthcare often 5-6.
    """
    max_consecutive = 6
    trailing = employee["consecutive_days_worked"]

    # Count consecutive days in the current schedule
    if not employee_schedule:
        return trailing < max_consecutive

    # Get all dates this employee is scheduled
    scheduled_dates = sorted(set(s["date"] for s in employee_schedule))
    new_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    # Count consecutive days ending on or including new_date
    consecutive = trailing
    if scheduled_dates:
        # Check if dates form an unbroken chain up to new_date
        prev_date = new_date - timedelta(days=1)
        chain = 0
        while prev_date.strftime("%Y-%m-%d") in scheduled_dates:
            chain += 1
            prev_date -= timedelta(days=1)
        # If chain reaches back to pre-schedule period, add trailing
        first_sched_date = datetime.strptime(scheduled_dates[0], "%Y-%m-%d").date()
        if prev_date < first_sched_date:
            consecutive = trailing + chain
        else:
            consecutive = chain

    return consecutive < max_consecutive


def _check_weekly_hours(employee, employee_schedule, shift_duration, demand_plan):
    """
    Check that adding this shift won't exceed weekly hour caps.
    Standard: 40 regular, 60 max (with OT).
    Industry plug-in: healthcare may have 36-hr weeks (3x12); retail varies.
    """
    max_weekly = min(employee["max_hours_preference"], 60)  # Hard cap at 60
    current_hours = sum(
        demand_plan["shifts"][s["shift_type"]]["duration_hours"]
        for s in employee_schedule
    )
    return (current_hours + shift_duration) <= max_weekly


def _ot_score(employee, employee_schedule, shift_duration, demand_plan):
    """
    Calculate OT equity score - lower score means this employee should
    get OT before someone with a higher score (spread OT evenly).
    """
    current_hours = sum(
        demand_plan["shifts"][s["shift_type"]]["duration_hours"]
        for s in employee_schedule
    )
    would_be_ot = max(0, (current_hours + shift_duration) - 40)
    total_ot = employee["ot_hours_ytd"] + would_be_ot
    return total_ot


def _weekend_score(employee, day_name):
    """
    Score for weekend equity - employees with fewer weekend shifts YTD
    should be assigned weekends first.
    """
    if day_name in ("Saturday", "Sunday"):
        return employee["weekend_shifts_ytd"]
    return 0


def generate_compliant_schedule(employees, demand_plan, rules=None, jurisdiction="Oregon"):
    """
    Core scheduling algorithm. Generates a fully compliant schedule.

    Algorithm:
    1. Build all shift slots from demand plan
    2. Sort slots by priority (harder-to-fill first: nights, weekends)
    3. For each slot, find eligible employees
    4. Rank eligible employees by: seniority (for preferred shift), OT equity,
       weekend equity, availability match
    5. Assign the top-ranked employee
    6. Track all assignments for constraint checking

    Parameters:
    -----------
    employees : list of employee profiles
    demand_plan : the demand plan structure
    rules : optional dict of rule overrides (uses defaults if None)
    jurisdiction : which jurisdiction's rules to apply

    Returns:
    --------
    dict with "schedule" (list of assignments), "unassigned_slots" (unfilled),
    "fairness_report" (scoring), "metadata"
    """

    # Default rules if not provided
    # Industry plug-in: rules differ significantly by sector
    if rules is None:
        rules = {
            "min_rest_hours": 10,
            "max_consecutive_days": 6,
            "max_weekly_hours": 60,
            "regular_hours": 40,
            "minor_night_restriction": True,
            "seniority_for_preferred_shift": True,
            "ot_equity_enabled": True,
            "weekend_equity_enabled": True,
        }

    # Build shift slots
    slots = build_shift_slots(demand_plan)

    # Sort slots: chronologically by date, then harder shifts first within each day.
    # This ensures balanced daily coverage while still prioritizing hard-to-fill slots.
    shift_priority = {"night": 0, "flex": 1, "day": 2}
    slots.sort(key=lambda s: (s["date"], shift_priority.get(s["shift_type"], 9)))

    # Track assignments per employee
    employee_schedules = defaultdict(list)  # emp_id -> list of assigned shifts
    assignments = []
    unassigned = []

    for slot in slots:
        best_employee = None
        best_score = float('inf')

        # Find eligible employees for this slot
        candidates = []
        for emp in employees:
            emp_id = emp["id"]
            emp_sched = employee_schedules[emp_id]

            # Hard constraints - must all pass
            if _is_on_leave(emp, slot["date"]):
                continue
            if not _is_available(emp, slot["day_name"], slot["shift_type"]):
                continue
            if not _can_work_shift(emp, slot["shift_type"]):
                continue
            if not _has_required_cert(emp, slot["role"]):
                continue
            if not _check_rest_period(emp_sched, slot["date"], slot["shift_type"], demand_plan):
                continue
            if not _check_consecutive_days(emp, emp_sched, slot["date"]):
                continue

            shift_duration = demand_plan["shifts"][slot["shift_type"]]["duration_hours"]
            if not _check_weekly_hours(emp, emp_sched, shift_duration, demand_plan):
                continue

            # Check if already assigned to another shift on same day/shift_type
            already_on_shift = any(
                s["date"] == slot["date"] and s["shift_type"] == slot["shift_type"]
                for s in emp_sched
            )
            if already_on_shift:
                continue

            # Also: cannot work two different shifts on same day
            already_on_day = any(s["date"] == slot["date"] for s in emp_sched)
            if already_on_day:
                continue

            candidates.append(emp)

        if not candidates:
            unassigned.append(slot)
            continue

        # Score and rank candidates
        shift_duration = demand_plan["shifts"][slot["shift_type"]]["duration_hours"]
        scored_candidates = []

        for emp in candidates:
            emp_id = emp["id"]
            emp_sched = employee_schedules[emp_id]
            score = 0

            # Seniority bonus for preferred shift (CBA compliance)
            # Lower seniority_rank = more senior = gets preference
            if rules["seniority_for_preferred_shift"]:
                if emp["preferred_shift"] == slot["shift_type"]:
                    # Senior employees requesting this shift get heavy priority
                    score -= (40 - emp["seniority_rank"]) * 10
                else:
                    score += emp["seniority_rank"] * 2

            # OT equity: prefer employees with lower cumulative OT
            if rules["ot_equity_enabled"]:
                ot = _ot_score(emp, emp_sched, shift_duration, demand_plan)
                score += ot * 3

            # Weekend equity: prefer employees with fewer weekend shifts
            if rules["weekend_equity_enabled"]:
                we_score = _weekend_score(emp, slot["day_name"])
                score += we_score * 5

            # Slight preference for employees with fewer hours this period
            # (spread work more evenly)
            current_hours = sum(
                demand_plan["shifts"][s["shift_type"]]["duration_hours"]
                for s in emp_sched
            )
            score += current_hours * 2

            scored_candidates.append((score, emp["seniority_rank"], emp))

        # Sort: lower score = better candidate; break ties by seniority
        scored_candidates.sort(key=lambda x: (x[0], x[1]))
        best_employee = scored_candidates[0][2]

        # Make the assignment
        assignment = {
            "employee_id": best_employee["id"],
            "employee_name": best_employee["name"],
            "date": slot["date"],
            "day_name": slot["day_name"],
            "shift_type": slot["shift_type"],
            "shift_start": demand_plan["shifts"][slot["shift_type"]]["start"],
            "shift_end": demand_plan["shifts"][slot["shift_type"]]["end"],
            "role": slot["role"],
            "is_icqa": slot.get("is_icqa", False),
        }
        assignments.append(assignment)
        employee_schedules[best_employee["id"]].append(assignment)

    # Build the schedule result
    schedule = {
        "schedule_id": f"SCH-{demand_plan['week_start'].replace('-', '')}",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "jurisdiction": jurisdiction,
        "week_start": demand_plan["week_start"],
        "week_end": demand_plan["week_end"],
        "facility": demand_plan["facility"],
        "total_slots": len(slots),
        "filled_slots": len(assignments),
        "unfilled_slots": len(unassigned),
        "assignments": assignments,
        "unassigned_slots": unassigned,
        "employee_schedules": dict(employee_schedules),
    }

    return schedule


# ============================================================
# 6. FAIRNESS REPORT
# Scores the schedule on multiple equity dimensions.
# ============================================================

def fairness_report(schedule, employees, demand_plan):
    """
    Generate a fairness analysis of the produced schedule.

    Scores:
    - OT equity: standard deviation of OT hours (lower = fairer)
    - Weekend equity: std dev of weekend shifts assigned
    - Preferred shift match rate: % of shifts matching employee preference
    - Seniority respect rate: % of preferred-shift assignments going to senior employees
    - Overall fairness score: 0-100 composite

    Industry plug-in: different sectors weight these differently.
    Healthcare: patient safety > seniority. Retail: availability > equity.
    """
    emp_hours = defaultdict(float)
    emp_ot = defaultdict(float)
    emp_weekend = defaultdict(int)
    emp_preferred_match = defaultdict(lambda: {"matched": 0, "total": 0})

    emp_lookup = {e["id"]: e for e in employees}
    assignments = schedule["assignments"]

    for a in assignments:
        emp_id = a["employee_id"]
        shift_hours = demand_plan["shifts"][a["shift_type"]]["duration_hours"]
        emp_hours[emp_id] += shift_hours

        if a["day_name"] in ("Saturday", "Sunday"):
            emp_weekend[emp_id] += 1

        emp_preferred_match[emp_id]["total"] += 1
        if emp_lookup[emp_id]["preferred_shift"] == a["shift_type"]:
            emp_preferred_match[emp_id]["matched"] += 1

    # Calculate OT for each employee
    for emp_id, hours in emp_hours.items():
        emp_ot[emp_id] = max(0, hours - 40) + emp_lookup[emp_id]["ot_hours_ytd"]

    # Employees with assignments
    assigned_emp_ids = [e["id"] for e in employees if emp_hours.get(e["id"], 0) > 0]

    # OT Equity Score (based on std dev of OT hours among those who worked)
    if assigned_emp_ids:
        ot_values = [emp_ot.get(eid, 0) for eid in assigned_emp_ids]
        ot_mean = sum(ot_values) / len(ot_values)
        ot_variance = sum((v - ot_mean) ** 2 for v in ot_values) / len(ot_values)
        ot_std = math.sqrt(ot_variance)
        # Score: lower std dev = better. Normalize to 0-100
        ot_equity_score = max(0, 100 - (ot_std * 2))
    else:
        ot_equity_score = 100

    # Weekend Equity Score
    if assigned_emp_ids:
        we_values = [emp_weekend.get(eid, 0) for eid in assigned_emp_ids]
        we_mean = sum(we_values) / len(we_values) if we_values else 0
        we_variance = sum((v - we_mean) ** 2 for v in we_values) / len(we_values) if we_values else 0
        we_std = math.sqrt(we_variance)
        weekend_equity_score = max(0, 100 - (we_std * 20))
    else:
        weekend_equity_score = 100

    # Preferred Shift Match Rate
    total_shifts = sum(d["total"] for d in emp_preferred_match.values())
    matched_shifts = sum(d["matched"] for d in emp_preferred_match.values())
    preferred_match_rate = (matched_shifts / total_shifts * 100) if total_shifts > 0 else 0

    # Seniority Respect Rate
    # Check: among preferred-shift assignments, did more senior employees get priority?
    seniority_respect = 0
    seniority_total = 0
    for emp_id, match_data in emp_preferred_match.items():
        emp = emp_lookup[emp_id]
        if match_data["matched"] > 0:
            seniority_total += 1
            # Senior employees (rank <= 20) getting their preferred shift = respected
            if emp["seniority_rank"] <= 20:
                seniority_respect += 1
            else:
                # Junior employees getting preferred shift is also ok if senior ones did too
                seniority_respect += 0.5

    seniority_rate = (seniority_respect / seniority_total * 100) if seniority_total > 0 else 0

    # Overall Fairness Score (weighted composite)
    # Industry plug-in: weights differ by sector/CBA
    overall = (
        ot_equity_score * 0.30 +
        weekend_equity_score * 0.25 +
        preferred_match_rate * 0.25 +
        min(100, seniority_rate) * 0.20
    )

    report = {
        "ot_equity": {
            "score": round(ot_equity_score, 1),
            "ot_std_dev": round(ot_std if assigned_emp_ids else 0, 2),
            "description": "Standard deviation of cumulative OT hours across employees (lower = fairer)",
        },
        "weekend_equity": {
            "score": round(weekend_equity_score, 1),
            "weekend_std_dev": round(we_std if assigned_emp_ids else 0, 2),
            "description": "Distribution evenness of weekend shift assignments",
        },
        "preferred_shift_match": {
            "score": round(preferred_match_rate, 1),
            "matched": matched_shifts,
            "total": total_shifts,
            "description": "Percentage of assignments matching employee's preferred shift",
        },
        "seniority_respect": {
            "score": round(min(100, seniority_rate), 1),
            "description": "Rate at which seniority preference is honored (CBA compliance)",
        },
        "overall_fairness": {
            "score": round(overall, 1),
            "grade": _score_to_grade(overall),
            "description": "Composite fairness score (0-100) - weighted across all dimensions",
        },
        "summary_stats": {
            "total_employees_scheduled": len(assigned_emp_ids),
            "total_shifts_assigned": len(assignments),
            "slots_unfilled": schedule["unfilled_slots"],
            "avg_hours_per_employee": round(
                sum(emp_hours.values()) / len(assigned_emp_ids), 1
            ) if assigned_emp_ids else 0,
            "employees_over_40hrs": sum(1 for h in emp_hours.values() if h > 40),
            "employees_on_leave_excluded": sum(
                1 for e in employees if e["leave_status"]["type"] is not None
            ),
        },
    }

    return report


def _score_to_grade(score):
    """Convert numeric score to letter grade."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


# ============================================================
# 7. WHAT-IF ANALYSIS
# Evaluate proposed changes for rule violations and suggest alternatives.
# ============================================================

def what_if(schedule, employees, demand_plan, change_description, rules=None):
    """
    Evaluate a proposed schedule change for compliance.

    Takes a natural-language-style change description, simulates it,
    checks what rules it would violate, and suggests compliant alternatives.

    Parameters:
    -----------
    schedule : the current schedule dict
    employees : list of employee profiles
    demand_plan : the demand plan
    change_description : dict describing the change, e.g.:
        {"action": "move", "employee_id": "E007", "from_shift": "day",
         "to_shift": "night", "date": "2026-07-08"}
    rules : optional rule overrides

    Returns:
    --------
    dict with "feasible" (bool), "violations" (list), "alternatives" (list)
    """

    if rules is None:
        rules = {
            "min_rest_hours": 10,
            "max_consecutive_days": 6,
            "max_weekly_hours": 60,
            "regular_hours": 40,
            "minor_night_restriction": True,
            "seniority_for_preferred_shift": True,
        }

    emp_lookup = {e["id"]: e for e in employees}
    action = change_description.get("action", "move")
    emp_id = change_description["employee_id"]
    employee = emp_lookup.get(emp_id)

    if not employee:
        return {
            "feasible": False,
            "violations": [{"rule": "INVALID_EMPLOYEE", "message": f"Employee {emp_id} not found"}],
            "alternatives": [],
        }

    violations = []
    alternatives = []

    target_date = change_description.get("date")
    target_shift = change_description.get("to_shift")
    target_role = change_description.get("role", employee["certified_roles"][0] if employee["certified_roles"] else None)

    # Get this employee's current schedule
    emp_sched = schedule["employee_schedules"].get(emp_id, [])

    # Simulate the change
    if action == "move":
        # Remove old assignment, add new one
        simulated_sched = [
            s for s in emp_sched
            if not (s["date"] == target_date and s["shift_type"] == change_description.get("from_shift"))
        ]
    elif action == "add":
        simulated_sched = list(emp_sched)
    elif action == "remove":
        return {
            "feasible": True,
            "violations": [],
            "alternatives": [],
            "note": "Removing a shift is always compliant (may create understaffing)."
        }
    else:
        simulated_sched = list(emp_sched)

    # Check constraints for the proposed new assignment
    day_name = datetime.strptime(target_date, "%Y-%m-%d").strftime("%A")

    # Check 1: Leave status
    if _is_on_leave(employee, target_date):
        violations.append({
            "rule": "LEAVE_VIOLATION",
            "severity": "critical",
            "message": f"{employee['name']} is on {employee['leave_status']['type']} leave on {target_date}",
        })

    # Check 2: Availability
    if not _is_available(employee, day_name, target_shift):
        violations.append({
            "rule": "AVAILABILITY_VIOLATION",
            "severity": "high",
            "message": f"{employee['name']} is not available for {target_shift} shift on {day_name}",
        })

    # Check 3: Minor night restriction
    if not _can_work_shift(employee, target_shift):
        violations.append({
            "rule": "MINOR_RESTRICTION",
            "severity": "critical",
            "message": f"{employee['name']} is a minor and cannot work night shifts",
        })

    # Check 4: Role certification
    if target_role and not _has_required_cert(employee, target_role):
        violations.append({
            "rule": "CERTIFICATION_VIOLATION",
            "severity": "high",
            "message": f"{employee['name']} is not certified for role: {target_role}",
        })

    # Check 5: Rest period
    if not _check_rest_period(simulated_sched, target_date, target_shift, demand_plan):
        violations.append({
            "rule": "REST_PERIOD_VIOLATION",
            "severity": "high",
            "message": f"Less than {rules['min_rest_hours']} hours rest between shifts for {employee['name']}",
        })

    # Check 6: Consecutive days
    if not _check_consecutive_days(employee, simulated_sched, target_date):
        violations.append({
            "rule": "CONSECUTIVE_DAYS_VIOLATION",
            "severity": "medium",
            "message": f"{employee['name']} would exceed {rules['max_consecutive_days']} consecutive days",
        })

    # Check 7: Weekly hours
    shift_duration = demand_plan["shifts"][target_shift]["duration_hours"]
    if not _check_weekly_hours(employee, simulated_sched, shift_duration, demand_plan):
        violations.append({
            "rule": "WEEKLY_HOURS_VIOLATION",
            "severity": "high",
            "message": f"{employee['name']} would exceed weekly hour cap ({rules['max_weekly_hours']} hrs)",
        })

    # Generate alternatives if violations exist
    if violations:
        # Find other employees who could take this slot compliantly
        for alt_emp in employees:
            if alt_emp["id"] == emp_id:
                continue
            alt_id = alt_emp["id"]
            alt_sched = schedule["employee_schedules"].get(alt_id, [])

            # Quick eligibility check
            if _is_on_leave(alt_emp, target_date):
                continue
            if not _is_available(alt_emp, day_name, target_shift):
                continue
            if not _can_work_shift(alt_emp, target_shift):
                continue
            if target_role and not _has_required_cert(alt_emp, target_role):
                continue
            if not _check_rest_period(alt_sched, target_date, target_shift, demand_plan):
                continue
            if not _check_consecutive_days(alt_emp, alt_sched, target_date):
                continue
            if not _check_weekly_hours(alt_emp, alt_sched, shift_duration, demand_plan):
                continue
            # Check not already on a shift that day
            if any(s["date"] == target_date for s in alt_sched):
                continue

            alternatives.append({
                "employee_id": alt_emp["id"],
                "employee_name": alt_emp["name"],
                "seniority_rank": alt_emp["seniority_rank"],
                "reason": "Fully compliant - meets all constraints",
            })

            if len(alternatives) >= 5:
                break

        # Also suggest different shifts for the same employee
        for alt_shift in demand_plan["shifts"]:
            if alt_shift == target_shift:
                continue
            if not _is_available(employee, day_name, alt_shift):
                continue
            if not _can_work_shift(employee, alt_shift):
                continue
            if _check_rest_period(simulated_sched, target_date, alt_shift, demand_plan):
                alternatives.append({
                    "employee_id": emp_id,
                    "employee_name": employee["name"],
                    "alternative_shift": alt_shift,
                    "reason": f"Move to {alt_shift} shift instead - compliant",
                })

    feasible = len(violations) == 0

    return {
        "feasible": feasible,
        "change_evaluated": change_description,
        "violations": violations,
        "violation_count": len(violations),
        "alternatives": alternatives,
        "recommendation": (
            "Change is compliant - proceed." if feasible
            else f"Change violates {len(violations)} rule(s). See alternatives."
        ),
    }


# ============================================================
# 8. MAIN EXECUTION
# Demonstrates the full pipeline: generate, schedule, report, what-if.
# ============================================================

def print_schedule_summary(schedule, employees, demand_plan):
    """Print a human-readable schedule summary."""
    print("=" * 70)
    print(f"  COMPLIANT SCHEDULE: {schedule['schedule_id']}")
    print(f"  Facility: {schedule['facility']}")
    print(f"  Week: {schedule['week_start']} to {schedule['week_end']}")
    print(f"  Jurisdiction: {schedule['jurisdiction']}")
    print(f"  Generated: {schedule['generated_at']}")
    print("=" * 70)
    print(f"\n  Total Slots: {schedule['total_slots']}  |  "
          f"Filled: {schedule['filled_slots']}  |  "
          f"Unfilled: {schedule['unfilled_slots']}")
    print(f"  Fill Rate: {schedule['filled_slots']/schedule['total_slots']*100:.1f}%")
    print()

    # Summary by day
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    week_start = datetime.strptime(demand_plan["week_start"], "%Y-%m-%d")

    print("  DAY-BY-DAY SUMMARY:")
    print("  " + "-" * 66)
    print(f"  {'Day':<12} {'Date':<12} {'Day Shift':<12} {'Night Shift':<14} {'Flex Shift':<12} {'Total':<8}")
    print("  " + "-" * 66)

    for i, day in enumerate(days):
        date_str = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
        day_count = sum(1 for a in schedule["assignments"]
                       if a["date"] == date_str and a["shift_type"] == "day")
        night_count = sum(1 for a in schedule["assignments"]
                        if a["date"] == date_str and a["shift_type"] == "night")
        flex_count = sum(1 for a in schedule["assignments"]
                       if a["date"] == date_str and a["shift_type"] == "flex")
        total = day_count + night_count + flex_count
        print(f"  {day:<12} {date_str:<12} {day_count:<12} {night_count:<14} {flex_count:<12} {total:<8}")

    print("  " + "-" * 66)
    print()

    # Top 10 employees by hours
    emp_hours = defaultdict(float)
    for a in schedule["assignments"]:
        emp_hours[a["employee_id"]] += demand_plan["shifts"][a["shift_type"]]["duration_hours"]

    sorted_emps = sorted(emp_hours.items(), key=lambda x: x[1], reverse=True)[:10]
    emp_lookup = {e["id"]: e for e in employees}

    print("  TOP 10 EMPLOYEES BY HOURS:")
    print("  " + "-" * 50)
    print(f"  {'Name':<22} {'Hours':<10} {'Shifts':<10} {'OT':<8}")
    print("  " + "-" * 50)
    for emp_id, hours in sorted_emps:
        emp = emp_lookup[emp_id]
        shifts_count = sum(1 for a in schedule["assignments"] if a["employee_id"] == emp_id)
        ot = max(0, hours - 40)
        print(f"  {emp['name']:<22} {hours:<10.1f} {shifts_count:<10} {ot:<8.1f}")
    print("  " + "-" * 50)
    print()


def print_fairness_report(report):
    """Print the fairness report in a readable format."""
    print("=" * 70)
    print("  FAIRNESS REPORT")
    print("=" * 70)
    print()
    print(f"  OVERALL FAIRNESS SCORE: {report['overall_fairness']['score']}/100  "
          f"(Grade: {report['overall_fairness']['grade']})")
    print()
    print("  DIMENSION SCORES:")
    print("  " + "-" * 60)
    print(f"  {'Dimension':<28} {'Score':<10} {'Detail':<30}")
    print("  " + "-" * 60)
    print(f"  {'OT Equity':<28} {report['ot_equity']['score']:<10.1f} "
          f"Std Dev: {report['ot_equity']['ot_std_dev']:.2f} hrs")
    print(f"  {'Weekend Equity':<28} {report['weekend_equity']['score']:<10.1f} "
          f"Std Dev: {report['weekend_equity']['weekend_std_dev']:.2f} shifts")
    print(f"  {'Preferred Shift Match':<28} {report['preferred_shift_match']['score']:<10.1f} "
          f"{report['preferred_shift_match']['matched']}/{report['preferred_shift_match']['total']} matched")
    print(f"  {'Seniority Respect':<28} {report['seniority_respect']['score']:<10.1f} "
          f"CBA preference honored")
    print("  " + "-" * 60)
    print()
    print("  SUMMARY STATISTICS:")
    stats = report["summary_stats"]
    print(f"    Employees scheduled:     {stats['total_employees_scheduled']}")
    print(f"    Total shifts assigned:   {stats['total_shifts_assigned']}")
    print(f"    Slots unfilled:          {stats['slots_unfilled']}")
    print(f"    Avg hours/employee:      {stats['avg_hours_per_employee']:.1f}")
    print(f"    Employees over 40 hrs:   {stats['employees_over_40hrs']}")
    print(f"    Employees on leave:      {stats['employees_on_leave_excluded']}")
    print()


def print_what_if(result, description=""):
    """Print a what-if analysis result."""
    print("  " + "-" * 60)
    print(f"  SCENARIO: {description}")
    print(f"  Change: {result['change_evaluated']}")
    print(f"  Feasible: {'YES - Compliant' if result['feasible'] else 'NO - Violations Found'}")
    print()

    if result.get("violations"):
        print(f"  VIOLATIONS ({result['violation_count']}):")
        for v in result["violations"]:
            print(f"    [{v['severity'].upper()}] {v['rule']}: {v['message']}")
        print()

    if result.get("alternatives"):
        print(f"  COMPLIANT ALTERNATIVES ({len(result['alternatives'])}):")
        for alt in result["alternatives"][:3]:
            if "alternative_shift" in alt:
                print(f"    -> {alt['employee_name']}: {alt['reason']}")
            else:
                print(f"    -> {alt['employee_name']} (seniority #{alt['seniority_rank']}): {alt['reason']}")
        print()

    print(f"  RECOMMENDATION: {result['recommendation']}")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  WORKFORCE COMPLIANCE AI - SCHEDULE GENERATOR")
    print("  Generating fully compliant, fair schedule from scratch")
    print("=" * 70 + "\n")

    # Step 1: Generate 40 realistic employees
    print("  [1/4] Generating 40 employee profiles...")
    employees = generate_employees()
    active_count = sum(1 for e in employees if e["leave_status"]["type"] is None)
    minor_count = sum(1 for e in employees if e["is_minor"])
    leave_count = sum(1 for e in employees if e["leave_status"]["type"] is not None)
    print(f"        Active: {active_count} | On Leave: {leave_count} | Minors: {minor_count}")
    print()

    # Step 2: Use the demand plan
    print("  [2/4] Loading demand plan...")
    demand_plan = DEMAND_PLAN
    total_min = sum(
        sum(s["min"] for s in day.values())
        for day in demand_plan["daily_demand"].values()
    )
    total_max = sum(
        sum(s["max"] for s in day.values())
        for day in demand_plan["daily_demand"].values()
    )
    print(f"        Weekly demand: {total_min}-{total_max} shift-slots across 3 shifts")
    print(f"        Roles: Pick (50%), Pack (25%), Stow (15%), Ship (10%)")
    print()

    # Step 3: Generate the schedule
    print("  [3/4] Running compliant schedule generator...")
    print("        Applying rules: rest periods, consecutive days, OT equity,")
    print("        seniority preference, minor restrictions, leave exclusions,")
    print("        role certification, weekly hour caps, weekend equity...")
    print()

    schedule = generate_compliant_schedule(
        employees=employees,
        demand_plan=demand_plan,
        jurisdiction="Oregon"
    )

    # Print schedule summary
    print_schedule_summary(schedule, employees, demand_plan)

    # Step 4: Fairness report
    print("  [4/4] Computing fairness report...")
    print()
    report = fairness_report(schedule, employees, demand_plan)
    print_fairness_report(report)

    # What-If Scenarios
    print("=" * 70)
    print("  WHAT-IF ANALYSIS - 3 SCENARIOS")
    print("=" * 70)
    print()

    # Scenario 1: Move Rosa Hernandez from day to night on Wednesday
    scenario1 = {
        "action": "move",
        "employee_id": "E007",
        "from_shift": "day",
        "to_shift": "night",
        "date": "2026-07-08",
        "role": "stow",
    }
    result1 = what_if(schedule, employees, demand_plan, scenario1)
    print_what_if(result1, "Move Rosa Hernandez from day to night on Wednesday")

    # Scenario 2: Add Tyler Brooks (minor) to night shift on Thursday
    scenario2 = {
        "action": "add",
        "employee_id": "E006",
        "to_shift": "night",
        "date": "2026-07-09",
        "role": "pack",
    }
    result2 = what_if(schedule, employees, demand_plan, scenario2)
    print_what_if(result2, "Add Tyler Brooks (minor) to night shift Thursday")

    # Scenario 3: Add Fatima Ali (on FMLA) to day shift Monday
    scenario3 = {
        "action": "add",
        "employee_id": "E009",
        "to_shift": "day",
        "date": "2026-07-06",
        "role": "ship",
    }
    result3 = what_if(schedule, employees, demand_plan, scenario3)
    print_what_if(result3, "Schedule Fatima Ali (on FMLA leave) for Monday day shift")

    print("=" * 70)
    print("  Schedule generation complete. All constraints enforced.")
    print("=" * 70)
    print()
