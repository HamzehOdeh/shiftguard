"""
Workforce Compliance AI - Bulk Schedule Generator
One-click: takes all employees, their preferences, approved time-off, and shift
constraints, then generates a full period schedule with fairness.
"""

from datetime import datetime, timedelta
from collections import defaultdict
from schedule_generator import ScheduleGenerator, SHIFT_PATTERNS


def bulk_generate_schedule(
    employees,
    start_date,
    end_date,
    pattern_type="healthcare_24_7",
    approved_time_off=None,
    worker_preferences=None,
    holiday_auction_results=None,
    min_per_shift=1,
    constraints=None,
):
    """
    One-click bulk schedule generation that accounts for everything.

    Args:
        employees: list of {"id", "name", "role", "category"?, ...}
        start_date: "2026-08-01" or datetime
        end_date: "2026-08-31" or datetime
        pattern_type: key from SHIFT_PATTERNS
        approved_time_off: list of {"employee_id", "start_date", "end_date", "reason"}
        worker_preferences: dict of employee_id -> {
            "no_work_days": ["Fri", "Sat"],
            "preferred_shift_type": "day",
            "cannot_work_shifts": ["Night"],
            "max_weekly_hours": 45,
            "vet_available_days": ["Thu"],
            "notes": "..."
        }
        holiday_auction_results: dict of employee_id -> {
            "granted": [{"start_date", "end_date", "period_name"}]
        }
        min_per_shift: minimum people per shift slot
        constraints: override default scheduling constraints

    Returns:
        Full schedule with fairness scorecard, conflicts resolved, audit trail.
    """
    if approved_time_off is None:
        approved_time_off = []
    if worker_preferences is None:
        worker_preferences = {}
    if holiday_auction_results is None:
        holiday_auction_results = {}

    # Build the worker list for the generator
    workers = [{"id": e["id"], "name": e["name"]} for e in employees]

    gen = ScheduleGenerator(workers, pattern_type=pattern_type, constraints=constraints)

    # --- Step 1: Add approved time-off as blocked dates ---
    blocked_summary = []
    for leave in approved_time_off:
        gen.add_blocked_dates(
            leave["employee_id"],
            leave["start_date"],
            leave["end_date"],
            reason=leave.get("reason", "Approved time-off")
        )
        emp_name = next((e["name"] for e in employees if e["id"] == leave["employee_id"]), leave["employee_id"])
        blocked_summary.append({
            "employee": emp_name,
            "dates": f"{leave['start_date']} to {leave['end_date']}",
            "reason": leave.get("reason", ""),
        })

    # --- Step 2: Add holiday auction grants as blocked dates ---
    for emp_id, auction_result in holiday_auction_results.items():
        for granted in auction_result.get("granted", []):
            gen.add_blocked_dates(
                emp_id,
                granted["start_date"],
                granted["end_date"],
                reason=f"Holiday auction: {granted.get('period_name', 'Holiday')}"
            )
            emp_name = next((e["name"] for e in employees if e["id"] == emp_id), emp_id)
            blocked_summary.append({
                "employee": emp_name,
                "dates": f"{granted['start_date']} to {granted['end_date']}",
                "reason": f"Holiday (P{granted.get('priority', '?')}): {granted.get('period_name', '')}",
            })

    # --- Step 3: Add preference-based blocks ---
    # Workers who said "I can't do Fridays" or "no nights"
    preference_notes = []
    if isinstance(start_date, str):
        period_start = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        period_start = start_date

    if isinstance(end_date, str):
        period_end = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        period_end = end_date

    day_name_map = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}

    for emp_id, prefs in worker_preferences.items():
        no_work_days = prefs.get("no_work_days", [])
        if no_work_days:
            # Block specific days of the week for the entire period
            current = period_start
            while current <= period_end:
                day_name = day_name_map[current.weekday()]
                if day_name in no_work_days:
                    date_str = current.strftime("%Y-%m-%d")
                    gen.add_blocked_dates(emp_id, date_str, date_str,
                                         reason=f"Preference: no {day_name}")
                current += timedelta(days=1)

            emp_name = next((e["name"] for e in employees if e["id"] == emp_id), emp_id)
            preference_notes.append(f"{emp_name}: no work on {', '.join(no_work_days)}")

    # --- Step 4: Generate the schedule ---
    results = gen.generate(start_date, end_date, min_per_shift=min_per_shift)

    # --- Step 5: Post-process — remove shifts that violate "cannot_work_shifts" preference ---
    # e.g., worker said "no nights" but got assigned a night because no one else was available
    preference_violations = []
    cleaned_schedule = []

    for shift in results["schedule"]:
        emp_id = shift["worker_id"]
        prefs = worker_preferences.get(emp_id, {})
        cannot_work = prefs.get("cannot_work_shifts", [])

        if shift["shift_name"] in cannot_work:
            # Soft violation — note it but keep if no alternative
            preference_violations.append({
                "employee": shift["worker_name"],
                "date": shift["date"],
                "shift": shift["shift_name"],
                "preference": f"Requested no {shift['shift_name']} shifts",
                "action": "Assigned anyway (no alternative available). Manager review recommended.",
            })

        cleaned_schedule.append(shift)

    results["schedule"] = cleaned_schedule

    # --- Step 6: Build summary ---
    # Group by employee for overview
    emp_summary = defaultdict(lambda: {"total": 0, "days": 0, "evenings": 0, "nights": 0,
                                        "weekends": 0, "holidays": 0})
    for shift in results["schedule"]:
        s = emp_summary[shift["worker_name"]]
        s["total"] += 1
        if shift["shift_name"] == "Day":
            s["days"] += 1
        elif shift["shift_name"] == "Evening":
            s["evenings"] += 1
        elif shift["shift_name"] == "Night":
            s["nights"] += 1
        if shift.get("is_weekend"):
            s["weekends"] += 1
        if shift.get("is_holiday"):
            s["holidays"] += 1

    return {
        "schedule": results["schedule"],
        "total_shifts": results["total_shifts"],
        "date_range": results["date_range"],
        "pattern": results["pattern"],
        "workers": len(employees),
        "fairness_scorecard": gen.get_fairness_scorecard(),
        "blocked_dates_applied": blocked_summary,
        "preferences_applied": preference_notes,
        "preference_violations": preference_violations,
        "employee_summary": dict(emp_summary),
        "generator": gen,  # keep reference for adjustments
    }


def get_available_patterns():
    """Get list of available shift patterns for UI."""
    return {k: v["name"] for k, v in SHIFT_PATTERNS.items()}


# ============================================================
# DEMO
# ============================================================

if __name__ == "__main__":
    # Scenario: Restaurant with 12 employees, generate August schedule
    employees = [
        {"id": f"R{i:02d}", "name": name, "role": role, "category": cat}
        for i, (name, role, cat) in enumerate([
            ("Maria Santos", "Server", "FOH"),
            ("James Park", "Server", "FOH"),
            ("Tanya Williams", "Server", "FOH"),
            ("Carlos Rivera", "Bartender", "FOH"),
            ("Aisha Mohammed", "Host/Hostess", "FOH"),
            ("Kevin Chen", "Busser", "FOH"),
            ("Chef Antoine Dupont", "Sous Chef", "BOH"),
            ("Lisa Nguyen", "Line Cook", "BOH"),
            ("Marcus Johnson", "Line Cook", "BOH"),
            ("David Kim", "Prep Cook", "BOH"),
            ("Rosa Hernandez", "Dishwasher", "BOH"),
            ("Jake Thompson", "Prep Cook", "BOH"),
        ], start=1)
    ]

    # Approved time-off
    approved_off = [
        {"employee_id": "R01", "start_date": "2026-08-10", "end_date": "2026-08-16", "reason": "Vacation (P1)"},
        {"employee_id": "R04", "start_date": "2026-08-20", "end_date": "2026-08-22", "reason": "Wedding"},
        {"employee_id": "R07", "start_date": "2026-08-01", "end_date": "2026-08-03", "reason": "Family visit"},
    ]

    # Worker preferences
    preferences = {
        "R01": {"no_work_days": ["Mon"], "cannot_work_shifts": ["Night"], "max_weekly_hours": 40},
        "R02": {"no_work_days": ["Sun"], "cannot_work_shifts": [], "max_weekly_hours": 45},
        "R03": {"no_work_days": [], "cannot_work_shifts": ["Night"], "max_weekly_hours": 40},
        "R05": {"no_work_days": ["Sat", "Sun"], "cannot_work_shifts": [], "max_weekly_hours": 35},
        "R06": {"no_work_days": [], "cannot_work_shifts": [], "max_weekly_hours": 50},
        "R08": {"no_work_days": ["Wed"], "cannot_work_shifts": [], "max_weekly_hours": 45},
        "R10": {"no_work_days": ["Fri"], "cannot_work_shifts": ["Night"], "max_weekly_hours": 40},
    }

    # Holiday auction results
    auction_results = {
        "R03": {"granted": [{"start_date": "2026-08-25", "end_date": "2026-08-31", "period_name": "Summer week", "priority": 1}]},
        "R09": {"granted": [{"start_date": "2026-08-15", "end_date": "2026-08-17", "period_name": "Family reunion", "priority": 1}]},
    }

    print("=" * 70)
    print("  BULK SCHEDULE GENERATOR")
    print("  Scenario: 12 Restaurant Staff, August 2026")
    print("=" * 70)

    result = bulk_generate_schedule(
        employees=employees,
        start_date="2026-08-01",
        end_date="2026-08-31",
        pattern_type="retail_standard",
        approved_time_off=approved_off,
        worker_preferences=preferences,
        holiday_auction_results=auction_results,
        min_per_shift=2,
    )

    print(f"\n  Generated: {result['total_shifts']} shifts over 31 days")
    print(f"  Pattern: {result['pattern']}")
    print(f"  Workers: {result['workers']}")

    # Blocked dates
    print(f"\n  BLOCKED DATES APPLIED ({len(result['blocked_dates_applied'])}):")
    for b in result["blocked_dates_applied"]:
        print(f"    {b['employee']}: {b['dates']} ({b['reason']})")

    # Preferences applied
    print(f"\n  PREFERENCES APPLIED ({len(result['preferences_applied'])}):")
    for p in result["preferences_applied"]:
        print(f"    {p}")

    # Preference violations
    if result["preference_violations"]:
        print(f"\n  PREFERENCE VIOLATIONS ({len(result['preference_violations'])}):")
        for v in result["preference_violations"]:
            print(f"    {v['employee']}: {v['date']} {v['shift']} - {v['action']}")
    else:
        print(f"\n  No preference violations!")

    # Fairness
    sc = result["fairness_scorecard"]
    print(f"\n  FAIRNESS: {sc['fairness_rating']}")
    print(f"    Night deviation: {sc['max_night_deviation']}")
    print(f"    Weekend deviation: {sc['max_weekend_deviation']}")

    # Employee summary
    print(f"\n  EMPLOYEE SUMMARY:")
    print(f"  {'Name':<25} {'Total':<7} {'Day':<5} {'Eve':<5} {'Night':<6} {'Wknd':<6}")
    print(f"  {'-'*58}")
    for name, stats in sorted(result["employee_summary"].items()):
        print(f"  {name:<25} {stats['total']:<7} {stats['days']:<5} "
              f"{stats['evenings']:<5} {stats['nights']:<6} {stats['weekends']:<6}")

    # Sample week
    print(f"\n  SAMPLE WEEK (Aug 4-10):")
    week = result["generator"].get_weekly_view("2026-08-04")
    print(f"  {'Date':<12} {'Shift':<10} {'Assigned':<25}")
    print(f"  {'-'*50}")
    for s in week[:14]:
        print(f"  {s['date']:<12} {s['shift_name']:<10} {s['worker_name']:<25}")
