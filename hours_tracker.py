"""
Workforce Compliance AI - Continuous Hours Tracking Engine
Real-time tracking of work hours with fatigue scoring, OT countdown, and predictive blocking.
"""

from datetime import datetime, timedelta
from collections import defaultdict


# Fatigue thresholds (based on occupational health research)
FATIGUE_THRESHOLDS = {
    "hours_since_last_rest_day": {"green": 48, "yellow": 72, "red": 96},
    "consecutive_days": {"green": 4, "yellow": 5, "red": 6},
    "hours_between_shifts": {"green": 12, "yellow": 10, "red": 8},
    "weekly_hours": {"green": 40, "yellow": 50, "red": 55},
    "rolling_24h_hours": {"green": 10, "yellow": 12, "red": 14},
    "night_shifts_in_row": {"green": 2, "yellow": 3, "red": 4},
}

OT_THRESHOLD_WEEKLY = 40
MAX_WEEKLY_HOURS = 60
SHIFT_DIFFERENTIAL_NIGHT = 1.15  # 15% night premium


def parse_dt(date_str, time_str):
    return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")


def get_shift_duration(shift):
    start = parse_dt(shift["date"], shift["start"])
    end = parse_dt(shift["date"], shift["end"])
    if end <= start:
        end += timedelta(days=1)
    return (end - start).total_seconds() / 3600


def classify_shift_type(shift):
    """Classify shift as day, evening, or night based on start/end times."""
    start_hour = int(shift["start"].split(":")[0])
    end_hour = int(shift["end"].split(":")[0])

    if start_hour >= 22 or start_hour < 6:
        return "night"
    elif start_hour >= 14 or (end_hour >= 22 or end_hour < 6):
        return "evening"
    else:
        return "day"


def calculate_employee_hours(shifts, employee_id, reference_date=None):
    """
    Calculate comprehensive hours metrics for an employee.
    Returns a dict with all tracking metrics.
    """
    if reference_date is None:
        reference_date = datetime.now()
    elif isinstance(reference_date, str):
        reference_date = datetime.strptime(reference_date, "%Y-%m-%d")

    emp_shifts = sorted(
        [s for s in shifts if s["employee_id"] == employee_id],
        key=lambda x: parse_dt(x["date"], x["start"])
    )

    if not emp_shifts:
        return _empty_metrics(employee_id)

    # Rolling 7-day hours
    week_start = reference_date - timedelta(days=6)
    weekly_shifts = [
        s for s in emp_shifts
        if week_start <= datetime.strptime(s["date"], "%Y-%m-%d") <= reference_date
    ]
    weekly_hours = sum(get_shift_duration(s) for s in weekly_shifts)

    # Rolling 24-hour hours
    last_24h = reference_date - timedelta(hours=24)
    hours_in_24h = sum(
        get_shift_duration(s) for s in emp_shifts
        if parse_dt(s["date"], s["start"]) >= last_24h
        and parse_dt(s["date"], s["start"]) <= reference_date + timedelta(days=1)
    )

    # Consecutive days worked
    dates_worked = sorted(set(s["date"] for s in emp_shifts))
    consecutive_days = _count_consecutive_days(dates_worked, reference_date)

    # Hours between last two shifts
    hours_between = None
    recent_shifts = [
        s for s in emp_shifts
        if datetime.strptime(s["date"], "%Y-%m-%d") <= reference_date
    ]
    if len(recent_shifts) >= 2:
        last = recent_shifts[-1]
        prev = recent_shifts[-2]
        end_prev = parse_dt(prev["date"], prev["end"])
        if end_prev > parse_dt(prev["date"], prev["start"]):
            pass
        else:
            end_prev += timedelta(days=1)
        start_last = parse_dt(last["date"], last["start"])
        hours_between = (start_last - end_prev).total_seconds() / 3600
        if hours_between < 0:
            hours_between += 24

    # Hours since last full rest day (24h with no shift)
    hours_since_rest = _hours_since_rest_day(dates_worked, reference_date)

    # Night shifts in a row
    night_shifts_consecutive = _count_consecutive_night_shifts(emp_shifts, reference_date)

    # OT countdown
    hours_remaining_before_ot = max(0, OT_THRESHOLD_WEEKLY - weekly_hours)
    hours_remaining_before_cap = max(0, MAX_WEEKLY_HOURS - weekly_hours)

    # Shift type distribution this period
    shift_types = {"day": 0, "evening": 0, "night": 0}
    for s in weekly_shifts:
        stype = classify_shift_type(s)
        shift_types[stype] += 1

    return {
        "employee_id": employee_id,
        "reference_date": reference_date.strftime("%Y-%m-%d"),
        "weekly_hours": round(weekly_hours, 1),
        "rolling_24h_hours": round(hours_in_24h, 1),
        "consecutive_days": consecutive_days,
        "hours_between_last_shifts": round(hours_between, 1) if hours_between else None,
        "hours_since_rest_day": hours_since_rest,
        "night_shifts_consecutive": night_shifts_consecutive,
        "hours_remaining_before_ot": round(hours_remaining_before_ot, 1),
        "hours_remaining_before_cap": round(hours_remaining_before_cap, 1),
        "shift_type_distribution": shift_types,
        "fatigue_score": None,  # calculated below
        "fatigue_level": None,
    }


def calculate_fatigue_score(metrics):
    """
    Calculate fatigue score (0-100) and level (green/yellow/red).
    Based on multiple weighted factors from occupational health research.
    """
    scores = []
    weights = {
        "weekly_hours": 0.25,
        "consecutive_days": 0.20,
        "hours_between_shifts": 0.20,
        "hours_since_rest_day": 0.15,
        "night_shifts_consecutive": 0.10,
        "rolling_24h_hours": 0.10,
    }

    # Weekly hours score
    wh = metrics["weekly_hours"]
    t = FATIGUE_THRESHOLDS["weekly_hours"]
    scores.append(("weekly_hours", _score_against_threshold(wh, t["green"], t["yellow"], t["red"])))

    # Consecutive days
    cd = metrics["consecutive_days"]
    t = FATIGUE_THRESHOLDS["consecutive_days"]
    scores.append(("consecutive_days", _score_against_threshold(cd, t["green"], t["yellow"], t["red"])))

    # Hours between shifts (inverse — lower is worse)
    hbs = metrics.get("hours_between_last_shifts")
    if hbs is not None:
        t = FATIGUE_THRESHOLDS["hours_between_shifts"]
        score = _score_against_threshold_inverse(hbs, t["green"], t["yellow"], t["red"])
        scores.append(("hours_between_shifts", score))
    else:
        scores.append(("hours_between_shifts", 0))

    # Hours since rest day
    hsr = metrics.get("hours_since_rest_day", 0)
    t = FATIGUE_THRESHOLDS["hours_since_last_rest_day"]
    scores.append(("hours_since_rest_day", _score_against_threshold(hsr, t["green"], t["yellow"], t["red"])))

    # Night shifts consecutive
    ns = metrics.get("night_shifts_consecutive", 0)
    t = FATIGUE_THRESHOLDS["night_shifts_in_row"]
    scores.append(("night_shifts_consecutive", _score_against_threshold(ns, t["green"], t["yellow"], t["red"])))

    # Rolling 24h
    r24 = metrics.get("rolling_24h_hours", 0)
    t = FATIGUE_THRESHOLDS["rolling_24h_hours"]
    scores.append(("rolling_24h_hours", _score_against_threshold(r24, t["green"], t["yellow"], t["red"])))

    # Weighted total
    total = sum(weights.get(name, 0.1) * score for name, score in scores)
    fatigue_score = min(100, max(0, round(total)))

    if fatigue_score <= 35:
        level = "green"
    elif fatigue_score <= 65:
        level = "yellow"
    else:
        level = "red"

    metrics["fatigue_score"] = fatigue_score
    metrics["fatigue_level"] = level
    metrics["fatigue_breakdown"] = {name: score for name, score in scores}

    return metrics


def predict_shift_impact(shifts, employee_id, proposed_shift, reference_date=None):
    """
    Predict the impact of adding a proposed shift.
    Returns current metrics, projected metrics, and warnings.
    """
    current = calculate_employee_hours(shifts, employee_id, reference_date)
    current = calculate_fatigue_score(current)

    projected_shifts = shifts + [proposed_shift]
    projected = calculate_employee_hours(projected_shifts, employee_id, reference_date)
    projected = calculate_fatigue_score(projected)

    shift_hours = get_shift_duration(proposed_shift)

    warnings = []

    # Check OT trigger
    if current["weekly_hours"] <= OT_THRESHOLD_WEEKLY and projected["weekly_hours"] > OT_THRESHOLD_WEEKLY:
        ot_hours = projected["weekly_hours"] - OT_THRESHOLD_WEEKLY
        warnings.append({
            "type": "overtime_trigger",
            "severity": "MEDIUM",
            "message": f"This shift triggers {ot_hours:.1f} hours of overtime",
            "cost_impact": f"Estimated ${ot_hours * 15 * 0.5:.0f} additional OT cost"
        })

    # Check cap breach
    if projected["weekly_hours"] > MAX_WEEKLY_HOURS:
        warnings.append({
            "type": "cap_breach",
            "severity": "HIGH",
            "message": f"Would exceed {MAX_WEEKLY_HOURS}-hour weekly cap ({projected['weekly_hours']:.1f} hrs total)",
            "cost_impact": "Requires VP approval + compliance violation risk"
        })

    # Check fatigue escalation
    if current["fatigue_level"] != "red" and projected["fatigue_level"] == "red":
        warnings.append({
            "type": "fatigue_red",
            "severity": "HIGH",
            "message": f"Fatigue score would move to RED ({projected['fatigue_score']}/100)",
            "cost_impact": "Safety risk + liability exposure"
        })
    elif current["fatigue_level"] == "green" and projected["fatigue_level"] == "yellow":
        warnings.append({
            "type": "fatigue_yellow",
            "severity": "MEDIUM",
            "message": f"Fatigue score would move to YELLOW ({projected['fatigue_score']}/100)",
            "cost_impact": "Monitor closely"
        })

    # Check rest period
    if projected.get("hours_between_last_shifts") and projected["hours_between_last_shifts"] < 10:
        warnings.append({
            "type": "rest_violation",
            "severity": "HIGH",
            "message": f"Only {projected['hours_between_last_shifts']:.1f}h rest between shifts (minimum 10h)",
            "cost_impact": "Clopening violation + premium pay"
        })

    # Check consecutive days
    if projected["consecutive_days"] > 6:
        warnings.append({
            "type": "consecutive_days",
            "severity": "HIGH",
            "message": f"{projected['consecutive_days']} consecutive days (max 6 per CBA)",
            "cost_impact": "Double time + grievance risk"
        })

    return {
        "current": current,
        "projected": projected,
        "proposed_shift_hours": shift_hours,
        "warnings": warnings,
        "recommendation": _generate_recommendation(warnings, current, projected)
    }


def get_all_employee_dashboards(shifts, employees, reference_date=None):
    """Get hours dashboard for all employees."""
    dashboards = []
    for emp in employees:
        metrics = calculate_employee_hours(shifts, emp["id"], reference_date)
        metrics = calculate_fatigue_score(metrics)
        metrics["name"] = emp["name"]
        metrics["role"] = emp.get("role", "")
        metrics["seniority"] = emp.get("seniority", 0)
        dashboards.append(metrics)
    return dashboards


# --- Private helpers ---

def _empty_metrics(employee_id):
    return {
        "employee_id": employee_id,
        "weekly_hours": 0,
        "rolling_24h_hours": 0,
        "consecutive_days": 0,
        "hours_between_last_shifts": None,
        "hours_since_rest_day": 0,
        "night_shifts_consecutive": 0,
        "hours_remaining_before_ot": OT_THRESHOLD_WEEKLY,
        "hours_remaining_before_cap": MAX_WEEKLY_HOURS,
        "shift_type_distribution": {"day": 0, "evening": 0, "night": 0},
        "fatigue_score": 0,
        "fatigue_level": "green",
    }


def _count_consecutive_days(dates_worked, reference_date):
    if not dates_worked:
        return 0

    ref_str = reference_date.strftime("%Y-%m-%d")
    relevant = [d for d in dates_worked if d <= ref_str]
    if not relevant:
        return 0

    consecutive = 1
    for i in range(len(relevant) - 1, 0, -1):
        d1 = datetime.strptime(relevant[i], "%Y-%m-%d")
        d2 = datetime.strptime(relevant[i-1], "%Y-%m-%d")
        if (d1 - d2).days == 1:
            consecutive += 1
        else:
            break
    return consecutive


def _hours_since_rest_day(dates_worked, reference_date):
    if not dates_worked:
        return 0

    ref_str = reference_date.strftime("%Y-%m-%d")
    relevant = sorted([d for d in dates_worked if d <= ref_str])
    if not relevant:
        return 0

    last_rest = None
    for i in range(len(relevant) - 1, 0, -1):
        d1 = datetime.strptime(relevant[i], "%Y-%m-%d")
        d2 = datetime.strptime(relevant[i-1], "%Y-%m-%d")
        if (d1 - d2).days > 1:
            last_rest = d2 + timedelta(days=1)
            break

    if last_rest is None:
        first_day = datetime.strptime(relevant[0], "%Y-%m-%d")
        return (reference_date - first_day).total_seconds() / 3600

    return (reference_date - last_rest).total_seconds() / 3600


def _count_consecutive_night_shifts(emp_shifts, reference_date):
    ref_str = reference_date.strftime("%Y-%m-%d")
    recent = [s for s in emp_shifts if s["date"] <= ref_str]
    recent.sort(key=lambda x: x["date"], reverse=True)

    count = 0
    for s in recent:
        if classify_shift_type(s) == "night":
            count += 1
        else:
            break
    return count


def _score_against_threshold(value, green_max, yellow_max, red_max):
    """Score 0-100 where 0=good, 100=critical."""
    if value <= green_max:
        return (value / green_max) * 33 if green_max > 0 else 0
    elif value <= yellow_max:
        return 33 + ((value - green_max) / (yellow_max - green_max)) * 33
    elif value <= red_max:
        return 66 + ((value - yellow_max) / (red_max - yellow_max)) * 34
    else:
        return 100


def _score_against_threshold_inverse(value, green_min, yellow_min, red_min):
    """Score 0-100 where higher value = lower fatigue (inverse)."""
    if value >= green_min:
        return 0
    elif value >= yellow_min:
        return 33 * (1 - (value - yellow_min) / (green_min - yellow_min))
    elif value >= red_min:
        return 33 + 33 * (1 - (value - red_min) / (yellow_min - red_min))
    else:
        return 100


def _generate_recommendation(warnings, current, projected):
    if not warnings:
        return "OK to assign — no compliance or fatigue concerns."

    high_warnings = [w for w in warnings if w["severity"] == "HIGH"]
    if high_warnings:
        return f"AVOID assigning — {len(high_warnings)} high-severity concern(s). Consider alternative employee."

    return f"CAUTION — {len(warnings)} concern(s). Assignment is possible but monitor closely."


if __name__ == "__main__":
    from sample_schedule import generate_schedule, EMPLOYEES

    schedule = generate_schedule()
    ref_date = datetime(2026, 7, 11)

    print("=" * 70)
    print("  WORKFORCE COMPLIANCE AI - HOURS TRACKING DASHBOARD")
    print("=" * 70)

    dashboards = get_all_employee_dashboards(schedule["shifts"], EMPLOYEES, ref_date)

    print(f"\n  {'Employee':<20} {'Weekly Hrs':<12} {'Consec Days':<12} {'OT Remaining':<14} {'Fatigue':<10}")
    print(f"  {'-'*68}")

    for d in sorted(dashboards, key=lambda x: x["fatigue_score"], reverse=True):
        fatigue_indicator = {
            "green": "[OK]",
            "yellow": "[WARN]",
            "red": "[DANGER]"
        }[d["fatigue_level"]]

        print(f"  {d['name']:<20} {d['weekly_hours']:<12} {d['consecutive_days']:<12} "
              f"{d['hours_remaining_before_ot']:<14} {fatigue_indicator} {d['fatigue_score']}/100")

    # Demo: predict impact of adding a shift
    print(f"\n\n  PREDICTIVE BLOCKING DEMO:")
    print(f"  What if we add James Wilson (already at 62.5 hrs) to Saturday night?")
    proposed = {
        "employee_id": "E002",
        "name": "James Wilson",
        "date": "2026-07-13",
        "start": "22:00",
        "end": "06:00",
        "role": "Pack",
        "shift_type": "Night"
    }
    impact = predict_shift_impact(schedule["shifts"], "E002", proposed, ref_date)
    print(f"\n  Current: {impact['current']['weekly_hours']}h/week, fatigue={impact['current']['fatigue_level']}")
    print(f"  Projected: {impact['projected']['weekly_hours']}h/week, fatigue={impact['projected']['fatigue_level']}")
    print(f"  Recommendation: {impact['recommendation']}")
    for w in impact["warnings"]:
        print(f"    [{w['severity']}] {w['message']}")
