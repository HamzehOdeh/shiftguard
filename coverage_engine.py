"""
Workforce Compliance AI - Fairness-Ranked Coverage Engine
When a gap needs filling, rank available workers by qualification, compliance,
fairness burden, OT distribution, and historical pattern.
"""

from datetime import datetime, timedelta
from collections import defaultdict
from hours_tracker import (
    calculate_employee_hours, calculate_fatigue_score,
    get_shift_duration, classify_shift_type, OT_THRESHOLD_WEEKLY, MAX_WEEKLY_HOURS
)


# Fairness weights (configurable per org)
FAIRNESS_WEIGHTS = {
    "qualification_match": 0.20,
    "hours_compliance": 0.20,
    "request_burden": 0.15,
    "ot_balance": 0.15,
    "holiday_rotation": 0.15,
    "volunteer_ratio": 0.10,
    "seniority": 0.05,
}


def find_coverage(shifts, employees, gap_shift, employee_history=None, reference_date=None):
    """
    Find and rank employees who can cover a gap shift.

    Args:
        shifts: current schedule shifts list
        employees: list of employee dicts
        gap_shift: the shift that needs coverage (dict with date, start, end, role)
        employee_history: historical fairness data (coverage requests, holiday allocations)
        reference_date: date for calculations

    Returns:
        List of candidates ranked by fairness score (best first)
    """
    if reference_date is None:
        reference_date = datetime.strptime(gap_shift["date"], "%Y-%m-%d")
    elif isinstance(reference_date, str):
        reference_date = datetime.strptime(reference_date, "%Y-%m-%d")

    if employee_history is None:
        employee_history = {}

    candidates = []

    for emp in employees:
        emp_id = emp["id"]

        # Skip the person who created the gap (if they called out)
        if gap_shift.get("absent_employee_id") == emp_id:
            continue

        # Check basic qualification
        qual_score = _check_qualification(emp, gap_shift)
        if qual_score == 0:
            continue

        # Check compliance (can they legally/contractually work this shift?)
        metrics = calculate_employee_hours(shifts, emp_id, reference_date)
        metrics = calculate_fatigue_score(metrics)

        compliance = _check_compliance_fit(metrics, gap_shift)
        if compliance["blocked"]:
            continue

        # Calculate fairness dimensions
        history = employee_history.get(emp_id, _default_history())

        request_burden_score = _score_request_burden(history)
        ot_balance_score = _score_ot_balance(metrics, shifts, employees, reference_date)
        holiday_rotation_score = _score_holiday_rotation(history, gap_shift)
        volunteer_score = _score_volunteer_ratio(history)
        seniority_score = _score_seniority(emp, employees, gap_shift)

        # Weighted composite score (higher = better candidate)
        composite = (
            FAIRNESS_WEIGHTS["qualification_match"] * qual_score +
            FAIRNESS_WEIGHTS["hours_compliance"] * compliance["score"] +
            FAIRNESS_WEIGHTS["request_burden"] * request_burden_score +
            FAIRNESS_WEIGHTS["ot_balance"] * ot_balance_score +
            FAIRNESS_WEIGHTS["holiday_rotation"] * holiday_rotation_score +
            FAIRNESS_WEIGHTS["volunteer_ratio"] * volunteer_score +
            FAIRNESS_WEIGHTS["seniority"] * seniority_score
        )

        # OT cost if assigned
        shift_hours = get_shift_duration(gap_shift)
        ot_cost = _estimate_ot_cost(metrics, shift_hours, emp.get("hourly_rate", 20))

        candidates.append({
            "employee_id": emp_id,
            "name": emp["name"],
            "role": emp.get("role", ""),
            "seniority": emp.get("seniority", 0),
            "composite_score": round(composite, 2),
            "current_weekly_hours": metrics["weekly_hours"],
            "fatigue_level": metrics["fatigue_level"],
            "fatigue_score": metrics["fatigue_score"],
            "hours_remaining_before_ot": metrics["hours_remaining_before_ot"],
            "estimated_ot_cost": ot_cost,
            "scores": {
                "qualification": round(qual_score, 2),
                "compliance": round(compliance["score"], 2),
                "request_burden": round(request_burden_score, 2),
                "ot_balance": round(ot_balance_score, 2),
                "holiday_rotation": round(holiday_rotation_score, 2),
                "volunteer_ratio": round(volunteer_score, 2),
                "seniority": round(seniority_score, 2),
            },
            "reason": _build_reason(
                qual_score, compliance, request_burden_score,
                ot_balance_score, holiday_rotation_score, metrics
            ),
        })

    # Sort by composite score descending (best candidate first)
    candidates.sort(key=lambda x: x["composite_score"], reverse=True)

    return candidates


def find_coverage_for_holiday(shifts, employees, holiday_date, role_needed,
                              employee_history=None, reference_date=None):
    """
    Special coverage finder for holiday shifts — applies holiday fairness rotation.
    """
    gap_shift = {
        "date": holiday_date,
        "start": "07:00",
        "end": "15:30",
        "role": role_needed,
        "shift_type": "Holiday",
        "is_holiday": True,
    }
    return find_coverage(shifts, employees, gap_shift, employee_history, reference_date)


def calculate_team_fairness_report(shifts, employees, employee_history=None, reference_date=None):
    """
    Generate a team-wide fairness report showing distribution of burden.
    """
    if reference_date is None:
        reference_date = datetime.now()
    elif isinstance(reference_date, str):
        reference_date = datetime.strptime(reference_date, "%Y-%m-%d")

    if employee_history is None:
        employee_history = {}

    report = []
    for emp in employees:
        emp_id = emp["id"]
        metrics = calculate_employee_hours(shifts, emp_id, reference_date)
        metrics = calculate_fatigue_score(metrics)
        history = employee_history.get(emp_id, _default_history())

        report.append({
            "employee_id": emp_id,
            "name": emp["name"],
            "role": emp.get("role", ""),
            "weekly_hours": metrics["weekly_hours"],
            "fatigue_score": metrics["fatigue_score"],
            "fatigue_level": metrics["fatigue_level"],
            "coverage_requests_received": history.get("coverage_requests_received", 0),
            "coverage_requests_accepted": history.get("coverage_requests_accepted", 0),
            "holidays_worked_this_year": history.get("holidays_worked_this_year", 0),
            "holidays_off_this_year": history.get("holidays_off_this_year", 0),
            "weekend_shifts_this_month": history.get("weekend_shifts_this_month", 0),
            "night_shifts_this_month": history.get("night_shifts_this_month", 0),
            "voluntary_covers": history.get("voluntary_covers", 0),
            "forced_covers": history.get("forced_covers", 0),
            "ot_hours_this_period": max(0, metrics["weekly_hours"] - OT_THRESHOLD_WEEKLY),
            "fairness_index": _calculate_fairness_index(history, metrics, employees, employee_history),
        })

    # Sort by fairness index (lower = has carried more burden = deserves a break)
    report.sort(key=lambda x: x["fairness_index"])

    return report


# --- Scoring Functions ---

def _check_qualification(emp, gap_shift):
    """Check if employee is qualified for the shift role. Returns 0-100."""
    emp_role = emp.get("role", "").lower()
    needed_role = gap_shift.get("role", "").lower()

    if emp.get("is_minor") and classify_shift_type(gap_shift) in ("night", "evening"):
        return 0

    if emp_role == needed_role:
        return 100

    # Cross-trained roles (simplified — in production this comes from a skills matrix)
    cross_train_map = {
        "pick": ["stow", "pack"],
        "pack": ["pick", "ship"],
        "stow": ["pick"],
        "ship": ["pack"],
    }
    if needed_role in cross_train_map.get(emp_role, []):
        return 70

    return 0


def _check_compliance_fit(metrics, gap_shift):
    """Check if assigning this shift would create a compliance violation."""
    shift_hours = get_shift_duration(gap_shift)
    projected_weekly = metrics["weekly_hours"] + shift_hours

    if projected_weekly > MAX_WEEKLY_HOURS:
        return {"blocked": True, "score": 0, "reason": "Would exceed 60-hour cap"}

    if metrics["consecutive_days"] >= 6:
        return {"blocked": True, "score": 0, "reason": "Already at 6 consecutive days"}

    if metrics["fatigue_level"] == "red" and metrics["fatigue_score"] >= 85:
        return {"blocked": True, "score": 0, "reason": "Critical fatigue level"}

    # Score: more remaining capacity = better
    capacity_pct = metrics["hours_remaining_before_cap"] / MAX_WEEKLY_HOURS
    fatigue_penalty = metrics["fatigue_score"] / 100 * 0.3

    score = max(0, min(100, capacity_pct * 100 - fatigue_penalty * 100))
    return {"blocked": False, "score": score, "reason": ""}


def _score_request_burden(history):
    """Score based on how many coverage requests this person has received recently.
    Higher score = fewer recent requests = fairer to ask them."""
    requests = history.get("coverage_requests_received", 0)
    team_avg = history.get("team_avg_requests", 3)

    if team_avg == 0:
        return 80

    ratio = requests / max(1, team_avg)
    if ratio <= 0.5:
        return 100  # asked much less than average
    elif ratio <= 1.0:
        return 70
    elif ratio <= 1.5:
        return 40
    else:
        return 10  # asked way more than average


def _score_ot_balance(metrics, shifts, employees, reference_date):
    """Score based on OT distribution fairness. Less OT = higher score."""
    emp_ot = max(0, metrics["weekly_hours"] - OT_THRESHOLD_WEEKLY)

    # Compare to team average OT
    team_ot = []
    for emp in employees:
        m = calculate_employee_hours(shifts, emp["id"], reference_date)
        team_ot.append(max(0, m["weekly_hours"] - OT_THRESHOLD_WEEKLY))

    avg_ot = sum(team_ot) / max(1, len(team_ot))

    if avg_ot == 0 and emp_ot == 0:
        return 80

    if emp_ot <= avg_ot * 0.5:
        return 100
    elif emp_ot <= avg_ot:
        return 70
    elif emp_ot <= avg_ot * 1.5:
        return 40
    else:
        return 10


def _score_holiday_rotation(history, gap_shift):
    """Score for holiday fairness — worked more holidays = higher score (should get a break)."""
    if not gap_shift.get("is_holiday"):
        return 70  # neutral for non-holiday shifts

    holidays_worked = history.get("holidays_worked_this_year", 0)
    holidays_off = history.get("holidays_off_this_year", 0)

    # More holidays off = more likely they should cover this one
    if holidays_off > holidays_worked + 1:
        return 90
    elif holidays_off >= holidays_worked:
        return 70
    else:
        return 30  # they've worked more holidays, give them a break


def _score_volunteer_ratio(history):
    """Score based on voluntary vs forced coverage. More voluntary = reward them."""
    vol = history.get("voluntary_covers", 0)
    forced = history.get("forced_covers", 0)
    total = vol + forced

    if total == 0:
        return 70

    vol_ratio = vol / total
    if vol_ratio >= 0.8:
        return 50  # they volunteer a lot, don't over-burden
    elif vol_ratio >= 0.5:
        return 70
    else:
        return 90  # they rarely volunteer, fair to assign


def _score_seniority(emp, employees, gap_shift):
    """Seniority scoring — configurable direction."""
    seniority = emp.get("seniority", 99)
    max_seniority = max(e.get("seniority", 1) for e in employees)

    # For undesirable shifts (night, holiday), junior should go first
    # For desirable shifts (day), senior gets priority
    shift_type = classify_shift_type(gap_shift)
    is_undesirable = shift_type == "night" or gap_shift.get("is_holiday")

    if is_undesirable:
        # Higher seniority number (more junior) = higher score for assignment
        return (seniority / max_seniority) * 100
    else:
        # Lower seniority number (more senior) = higher score for desirable shifts
        return (1 - seniority / max_seniority) * 100


def _estimate_ot_cost(metrics, shift_hours, hourly_rate):
    """Estimate additional OT cost if this employee takes the shift."""
    current_hours = metrics["weekly_hours"]
    new_total = current_hours + shift_hours

    if new_total <= OT_THRESHOLD_WEEKLY:
        return 0.0

    ot_hours = min(shift_hours, new_total - OT_THRESHOLD_WEEKLY)
    regular_hours = shift_hours - ot_hours

    return round(ot_hours * hourly_rate * 0.5, 2)  # OT premium only


def _calculate_fairness_index(history, metrics, employees, all_history):
    """
    0-100 fairness index. Lower = person has been carrying more burden.
    Used for team-wide fairness reporting.
    """
    burden_signals = [
        history.get("coverage_requests_received", 0) * 5,
        history.get("holidays_worked_this_year", 0) * 10,
        history.get("weekend_shifts_this_month", 0) * 3,
        history.get("night_shifts_this_month", 0) * 4,
        history.get("forced_covers", 0) * 8,
    ]
    relief_signals = [
        history.get("holidays_off_this_year", 0) * 10,
        history.get("voluntary_covers", 0) * 2,
    ]

    burden = sum(burden_signals)
    relief = sum(relief_signals)
    net = burden - relief

    # Normalize to 0-100 (higher net burden = lower fairness index)
    return max(0, min(100, 50 - net))


def _build_reason(qual, compliance, request_burden, ot_balance, holiday_rotation, metrics):
    """Build a human-readable reason for ranking."""
    reasons = []

    if metrics["weekly_hours"] < 30:
        reasons.append(f"Light week ({metrics['weekly_hours']}h)")
    elif metrics["hours_remaining_before_ot"] > 10:
        reasons.append(f"{metrics['hours_remaining_before_ot']}h before OT")

    if request_burden >= 80:
        reasons.append("Rarely asked for coverage")
    elif request_burden <= 30:
        reasons.append("Frequently asked (fairness concern)")

    if ot_balance >= 80:
        reasons.append("Low OT this period")

    if holiday_rotation >= 80:
        reasons.append("Due for holiday coverage")

    if metrics["fatigue_level"] == "green":
        reasons.append("Well-rested")
    elif metrics["fatigue_level"] == "yellow":
        reasons.append("Moderate fatigue")

    return " | ".join(reasons) if reasons else "Standard candidate"


def _default_history():
    return {
        "coverage_requests_received": 0,
        "coverage_requests_accepted": 0,
        "holidays_worked_this_year": 0,
        "holidays_off_this_year": 0,
        "weekend_shifts_this_month": 0,
        "night_shifts_this_month": 0,
        "voluntary_covers": 0,
        "forced_covers": 0,
        "team_avg_requests": 3,
    }


if __name__ == "__main__":
    from sample_schedule import generate_schedule, EMPLOYEES

    schedule = generate_schedule()
    ref_date = datetime(2026, 7, 11)

    # Simulated employee history for demo
    demo_history = {
        "E001": {"coverage_requests_received": 5, "coverage_requests_accepted": 4,
                 "holidays_worked_this_year": 3, "holidays_off_this_year": 1,
                 "weekend_shifts_this_month": 3, "night_shifts_this_month": 1,
                 "voluntary_covers": 3, "forced_covers": 1, "team_avg_requests": 3},
        "E002": {"coverage_requests_received": 2, "coverage_requests_accepted": 2,
                 "holidays_worked_this_year": 1, "holidays_off_this_year": 3,
                 "weekend_shifts_this_month": 1, "night_shifts_this_month": 0,
                 "voluntary_covers": 2, "forced_covers": 0, "team_avg_requests": 3},
        "E003": {"coverage_requests_received": 1, "coverage_requests_accepted": 1,
                 "holidays_worked_this_year": 0, "holidays_off_this_year": 3,
                 "weekend_shifts_this_month": 0, "night_shifts_this_month": 0,
                 "voluntary_covers": 1, "forced_covers": 0, "team_avg_requests": 3},
        "E005": {"coverage_requests_received": 4, "coverage_requests_accepted": 3,
                 "holidays_worked_this_year": 2, "holidays_off_this_year": 2,
                 "weekend_shifts_this_month": 2, "night_shifts_this_month": 2,
                 "voluntary_covers": 1, "forced_covers": 2, "team_avg_requests": 3},
        "E008": {"coverage_requests_received": 1, "coverage_requests_accepted": 1,
                 "holidays_worked_this_year": 1, "holidays_off_this_year": 2,
                 "weekend_shifts_this_month": 1, "night_shifts_this_month": 0,
                 "voluntary_covers": 1, "forced_covers": 0, "team_avg_requests": 3},
        "E010": {"coverage_requests_received": 0, "coverage_requests_accepted": 0,
                 "holidays_worked_this_year": 0, "holidays_off_this_year": 2,
                 "weekend_shifts_this_month": 0, "night_shifts_this_month": 0,
                 "voluntary_covers": 0, "forced_covers": 0, "team_avg_requests": 3},
    }

    # Scenario: Sarah calls out on Friday, need a Pick replacement
    gap = {
        "date": "2026-07-11",
        "start": "06:00",
        "end": "14:30",
        "role": "Pick",
        "shift_type": "Day",
        "absent_employee_id": "E001",
    }

    print("=" * 70)
    print("  COVERAGE FINDER - FAIRNESS RANKED")
    print("=" * 70)
    print(f"\n  Gap: {gap['role']} shift on {gap['date']} ({gap['start']}-{gap['end']})")
    print(f"  Absent: Sarah Martinez (E001)")
    print(f"\n  {'Rank':<5} {'Name':<20} {'Score':<7} {'Weekly Hrs':<11} {'Fatigue':<9} {'OT Cost':<9} {'Reason'}")
    print(f"  {'-'*90}")

    candidates = find_coverage(
        schedule["shifts"], EMPLOYEES, gap, demo_history, ref_date
    )

    for i, c in enumerate(candidates, 1):
        print(f"  {i:<5} {c['name']:<20} {c['composite_score']:<7} "
              f"{c['current_weekly_hours']:<11} {c['fatigue_level']:<9} "
              f"${c['estimated_ot_cost']:<8} {c['reason'][:40]}")

    # Team fairness report
    print(f"\n\n  TEAM FAIRNESS REPORT")
    print(f"  {'Name':<20} {'Holidays Worked':<16} {'Coverage Reqs':<14} {'Night Shifts':<13} {'Fairness Idx'}")
    print(f"  {'-'*75}")

    report = calculate_team_fairness_report(
        schedule["shifts"], EMPLOYEES, demo_history, ref_date
    )
    for r in report:
        print(f"  {r['name']:<20} {r['holidays_worked_this_year']:<16} "
              f"{r['coverage_requests_received']:<14} {r['night_shifts_this_month']:<13} "
              f"{r['fairness_index']}/100")
