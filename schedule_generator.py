"""
Workforce Compliance AI - Fair Schedule Generator
Generates fair schedules from parameters (e.g., "5 residents covering ED 24/7 for a year").
Distributes nights, weekends, holidays equally. Shows fairness scorecard.
Supports adjustments ("Dr. Patel is off first 2 weeks of March").
"""

from datetime import datetime, timedelta
from collections import defaultdict


DEFAULT_CONSTRAINTS = {
    "max_consecutive_days": 6,
    "min_rest_hours": 10,
    "max_weekly_hours": 60,
    "max_consecutive_nights": 4,
    "night_rest_after_block": 48,
}

SHIFT_PATTERNS = {
    "healthcare_24_7": {
        "name": "24/7 Coverage (Healthcare)",
        "shifts_per_day": 3,
        "shifts": [
            {"name": "Day", "start": "07:00", "end": "15:00", "hours": 8, "desirability": 10},
            {"name": "Evening", "start": "15:00", "end": "23:00", "hours": 8, "desirability": 6},
            {"name": "Night", "start": "23:00", "end": "07:00", "hours": 8, "desirability": 3},
        ],
    },
    "healthcare_12hr": {
        "name": "12-Hour Shifts (Healthcare)",
        "shifts_per_day": 2,
        "shifts": [
            {"name": "Day", "start": "07:00", "end": "19:00", "hours": 12, "desirability": 8},
            {"name": "Night", "start": "19:00", "end": "07:00", "hours": 12, "desirability": 4},
        ],
    },
    "warehouse_2shift": {
        "name": "2-Shift Warehouse",
        "shifts_per_day": 2,
        "shifts": [
            {"name": "Day", "start": "06:00", "end": "17:30", "hours": 10, "desirability": 8},
            {"name": "Night", "start": "18:00", "end": "05:30", "hours": 10, "desirability": 5},
        ],
    },
    "retail_standard": {
        "name": "Standard Retail",
        "shifts_per_day": 2,
        "shifts": [
            {"name": "Opening", "start": "06:00", "end": "14:30", "hours": 8, "desirability": 7},
            {"name": "Closing", "start": "14:00", "end": "22:30", "hours": 8, "desirability": 5},
        ],
    },
}

WEEKEND_DAYS = {5, 6}
HOLIDAYS_2026 = {
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-05-25",
    "2026-07-04", "2026-09-07", "2026-10-12", "2026-11-11",
    "2026-11-26", "2026-12-25",
}


class ScheduleGenerator:
    """Generate fair schedules with equal distribution of undesirable shifts."""

    def __init__(self, workers, pattern_type="healthcare_24_7", constraints=None):
        self.workers = workers
        self.pattern = SHIFT_PATTERNS[pattern_type]
        self.constraints = constraints or DEFAULT_CONSTRAINTS
        self.schedule = []
        self.blocked_dates = defaultdict(list)
        self.adjustments = []

    def add_blocked_dates(self, worker_id, start_date, end_date, reason=""):
        self.blocked_dates[worker_id].append({
            "start": start_date if isinstance(start_date, str) else start_date.strftime("%Y-%m-%d"),
            "end": end_date if isinstance(end_date, str) else end_date.strftime("%Y-%m-%d"),
            "reason": reason,
        })

    def generate(self, start_date, end_date, min_per_shift=1):
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        self.schedule = []

        counters = {w["id"]: {
            "total_shifts": 0, "night_shifts": 0, "weekend_shifts": 0,
            "holiday_shifts": 0, "consecutive_days": 0, "last_shift_date": None,
            "last_shift_type": None, "consecutive_nights": 0, "desirability_total": 0,
        } for w in self.workers}

        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            prev_date_str = (current_date - timedelta(days=1)).strftime("%Y-%m-%d")
            is_weekend = current_date.weekday() in WEEKEND_DAYS
            is_holiday = date_str in HOLIDAYS_2026

            # Reset consecutive counters for workers who had yesterday off
            for wid, c in counters.items():
                if c["last_shift_date"] != prev_date_str and c["last_shift_date"] != date_str:
                    c["consecutive_days"] = 0
                    c["consecutive_nights"] = 0

            for shift_def in self.pattern["shifts"]:
                candidates = self._rank_candidates(date_str, shift_def, counters, is_weekend, is_holiday)

                # Fallback: if no candidates pass constraints, relax and pick least-worked
                if not candidates:
                    candidates = self._rank_candidates_relaxed(date_str, shift_def, counters)

                assigned = 0
                for candidate in candidates:
                    if assigned >= min_per_shift:
                        break

                    wid = candidate["id"]
                    c = counters[wid]

                    self.schedule.append({
                        "date": date_str,
                        "day_of_week": current_date.strftime("%A"),
                        "shift_name": shift_def["name"],
                        "start": shift_def["start"],
                        "end": shift_def["end"],
                        "hours": shift_def["hours"],
                        "worker_id": wid,
                        "worker_name": candidate["name"],
                        "is_weekend": is_weekend,
                        "is_holiday": is_holiday,
                    })

                    c["total_shifts"] += 1
                    c["desirability_total"] += shift_def["desirability"]
                    if shift_def["name"] == "Night":
                        c["night_shifts"] += 1
                        c["consecutive_nights"] += 1
                    else:
                        c["consecutive_nights"] = 0
                    if is_weekend:
                        c["weekend_shifts"] += 1
                    if is_holiday:
                        c["holiday_shifts"] += 1

                    if c["last_shift_date"] == (current_date - timedelta(days=1)).strftime("%Y-%m-%d"):
                        c["consecutive_days"] += 1
                    else:
                        c["consecutive_days"] = 1
                    c["last_shift_date"] = date_str
                    c["last_shift_type"] = shift_def["name"]
                    assigned += 1

            current_date += timedelta(days=1)

        return self._build_results(counters, start_date, end_date)

    def apply_adjustment(self, description, worker_id, start_date, end_date):
        self.adjustments.append({
            "description": description, "worker_id": worker_id,
            "start_date": start_date, "end_date": end_date,
        })

        removed = []
        remaining = []
        for shift in self.schedule:
            if shift["worker_id"] == worker_id and start_date <= shift["date"] <= end_date:
                removed.append(shift)
            else:
                remaining.append(shift)

        self.schedule = remaining
        other_workers = [w for w in self.workers if w["id"] != worker_id]

        worker_idx = 0
        for shift in removed:
            assigned_worker = other_workers[worker_idx % len(other_workers)]
            new_shift = {**shift}
            new_shift["worker_id"] = assigned_worker["id"]
            new_shift["worker_name"] = assigned_worker["name"]
            new_shift["redistributed"] = True
            self.schedule.append(new_shift)
            worker_idx += 1

        self.schedule.sort(key=lambda x: (x["date"], x["start"]))

        return {
            "adjustment": description,
            "shifts_removed": len(removed),
            "shifts_redistributed": len(removed),
            "affected_workers": [w["name"] for w in other_workers],
        }

    def get_fairness_scorecard(self):
        worker_stats = defaultdict(lambda: {
            "total_shifts": 0, "night_shifts": 0,
            "weekend_shifts": 0, "holiday_shifts": 0,
        })

        for shift in self.schedule:
            wid = shift["worker_id"]
            worker_stats[wid]["total_shifts"] += 1
            if shift["shift_name"] == "Night":
                worker_stats[wid]["night_shifts"] += 1
            if shift["is_weekend"]:
                worker_stats[wid]["weekend_shifts"] += 1
            if shift["is_holiday"]:
                worker_stats[wid]["holiday_shifts"] += 1

        scorecard = []
        for w in self.workers:
            stats = worker_stats[w["id"]]
            scorecard.append({"worker_id": w["id"], "name": w["name"], **stats})

        if scorecard:
            avg_nights = sum(s["night_shifts"] for s in scorecard) / len(scorecard)
            avg_weekends = sum(s["weekend_shifts"] for s in scorecard) / len(scorecard)
            avg_holidays = sum(s["holiday_shifts"] for s in scorecard) / len(scorecard)
            avg_total = sum(s["total_shifts"] for s in scorecard) / len(scorecard)
            max_night_dev = max(abs(s["night_shifts"] - avg_nights) for s in scorecard)
            max_weekend_dev = max(abs(s["weekend_shifts"] - avg_weekends) for s in scorecard)
            fairness_rating = "EXCELLENT" if max_night_dev <= 2 and max_weekend_dev <= 2 else (
                "GOOD" if max_night_dev <= 4 and max_weekend_dev <= 4 else "NEEDS_REVIEW")
        else:
            avg_nights = avg_weekends = avg_holidays = avg_total = 0
            max_night_dev = max_weekend_dev = 0
            fairness_rating = "N/A"

        return {
            "workers": scorecard,
            "averages": {
                "total_shifts": round(avg_total, 1),
                "night_shifts": round(avg_nights, 1),
                "weekend_shifts": round(avg_weekends, 1),
                "holiday_shifts": round(avg_holidays, 1),
            },
            "max_night_deviation": round(max_night_dev, 1),
            "max_weekend_deviation": round(max_weekend_dev, 1),
            "fairness_rating": fairness_rating,
        }

    def get_weekly_view(self, week_start):
        if isinstance(week_start, str):
            week_start = datetime.strptime(week_start, "%Y-%m-%d")
        week_end = week_start + timedelta(days=6)
        ws = week_start.strftime("%Y-%m-%d")
        we = week_end.strftime("%Y-%m-%d")
        return [s for s in self.schedule if ws <= s["date"] <= we]

    def _rank_candidates_relaxed(self, date_str, shift_def, counters):
        """Fallback when no candidates pass strict constraints — pick least-worked."""
        candidates = []
        for w in self.workers:
            wid = w["id"]
            if self._is_blocked(wid, date_str):
                continue
            c = counters[wid]
            score = c["total_shifts"] * 10
            candidates.append({"id": wid, "name": w["name"], "priority": score})
        candidates.sort(key=lambda x: x["priority"])
        return candidates

    def _rank_candidates(self, date_str, shift_def, counters, is_weekend, is_holiday):
        candidates = []
        for w in self.workers:
            wid = w["id"]
            if self._is_blocked(wid, date_str):
                continue
            c = counters[wid]
            if c["consecutive_days"] >= self.constraints["max_consecutive_days"]:
                continue
            if shift_def["name"] == "Night" and c["consecutive_nights"] >= self.constraints["max_consecutive_nights"]:
                continue

            score = c["total_shifts"] * 10
            if shift_def["name"] == "Night":
                score += c["night_shifts"] * 20
            if is_weekend:
                score += c["weekend_shifts"] * 15
            if is_holiday:
                score += c["holiday_shifts"] * 25
            score -= c["consecutive_days"] * 3

            candidates.append({"id": wid, "name": w["name"], "priority": score})

        candidates.sort(key=lambda x: x["priority"])
        return candidates

    def _is_blocked(self, worker_id, date_str):
        for block in self.blocked_dates.get(worker_id, []):
            if block["start"] <= date_str <= block["end"]:
                return True
        return False

    def _build_results(self, counters, start_date, end_date):
        days = (end_date - start_date).days + 1
        return {
            "schedule": self.schedule,
            "total_shifts": len(self.schedule),
            "date_range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "days": days,
            "workers": len(self.workers),
            "pattern": self.pattern["name"],
            "fairness_scorecard": self.get_fairness_scorecard(),
        }


if __name__ == "__main__":
    residents = [
        {"id": "R1", "name": "Dr. Patel"},
        {"id": "R2", "name": "Dr. Chen"},
        {"id": "R3", "name": "Dr. Williams"},
        {"id": "R4", "name": "Dr. Garcia"},
        {"id": "R5", "name": "Dr. Thompson"},
    ]

    gen = ScheduleGenerator(residents, pattern_type="healthcare_24_7")
    gen.add_blocked_dates("R1", "2026-03-01", "2026-03-14", "Vacation")

    print("=" * 70)
    print("  FAIR SCHEDULE GENERATOR")
    print("  Scenario: 5 ED Residents, 24/7 coverage, Q1 2026")
    print("=" * 70)

    results = gen.generate("2026-01-01", "2026-03-31")

    print(f"\n  Generated: {results['total_shifts']} shifts over {results['days']} days")
    print(f"  Pattern: {results['pattern']}")

    scorecard = results["fairness_scorecard"]
    print(f"\n  FAIRNESS SCORECARD:")
    print(f"    Rating: {scorecard['fairness_rating']}")
    print(f"    Max night deviation: {scorecard['max_night_deviation']} shifts")
    print(f"    Max weekend deviation: {scorecard['max_weekend_deviation']} shifts")

    print(f"\n  {'Name':<16} {'Total':<7} {'Nights':<8} {'Weekends':<10} {'Holidays':<9}")
    print(f"  {'-'*55}")
    for w in scorecard["workers"]:
        print(f"  {w['name']:<16} {w['total_shifts']:<7} {w['night_shifts']:<8} "
              f"{w['weekend_shifts']:<10} {w['holiday_shifts']:<9}")

    print(f"\n  Averages: {scorecard['averages']['total_shifts']} total, "
          f"{scorecard['averages']['night_shifts']} nights, "
          f"{scorecard['averages']['weekend_shifts']} weekends")

    print(f"\n\n  SAMPLE WEEK (Jan 5-11):")
    print(f"  {'Date':<12} {'Day':<10} {'Shift':<8} {'Assigned':<16}")
    print(f"  {'-'*50}")
    week = gen.get_weekly_view("2026-01-05")
    for s in week[:15]:
        print(f"  {s['date']:<12} {s['day_of_week'][:3]:<10} {s['shift_name']:<8} {s['worker_name']:<16}")

    print(f"\n\n  ADJUSTMENT: Dr. Chen no nights week of Feb 1")
    adj = gen.apply_adjustment("Dr. Chen no nights Feb 1 week", "R2", "2026-02-01", "2026-02-07")
    print(f"  Removed: {adj['shifts_removed']}, Redistributed to: {', '.join(adj['affected_workers'])}")
    print(f"  Updated fairness: {gen.get_fairness_scorecard()['fairness_rating']}")
