"""
Workforce Compliance AI - Priority-Based Fair Holiday Auction System
Workers submit holiday preferences ranked by priority. System allocates using
fairness-constrained algorithm with year-over-year memory and transparent explanations.
"""

from datetime import datetime, timedelta
from collections import defaultdict


# Holiday value groups (equivalent-value slots — if you get one, lower priority for others in group)
HOLIDAY_GROUPS = {
    "winter_major": {
        "name": "Winter Major Holidays",
        "slots": ["Christmas Week", "New Year's Week"],
        "description": "Getting one means lower priority for the other",
    },
    "thanksgiving": {
        "name": "Thanksgiving Period",
        "slots": ["Thanksgiving Week", "Black Friday Weekend"],
        "description": "Major family holiday",
    },
    "summer": {
        "name": "Summer Holidays",
        "slots": ["July 4th Week", "Memorial Day Week", "Labor Day Week"],
        "description": "Summer holiday slots",
    },
    "school_breaks": {
        "name": "School Breaks",
        "slots": ["Spring Break", "Fall Break", "Winter Break"],
        "description": "For parents with school-age children",
    },
    "cultural": {
        "name": "Cultural/Religious",
        "slots": ["Lunar New Year", "Eid", "Diwali", "Chuseok", "Ramadan"],
        "description": "Cultural and religious observances",
    },
}

# Predefined holiday periods for 2026
HOLIDAY_PERIODS_2026 = {
    "Christmas Week": {"start": "2026-12-21", "end": "2026-12-27"},
    "New Year's Week": {"start": "2026-12-28", "end": "2027-01-03"},
    "Thanksgiving Week": {"start": "2026-11-23", "end": "2026-11-29"},
    "Black Friday Weekend": {"start": "2026-11-27", "end": "2026-11-29"},
    "July 4th Week": {"start": "2026-06-29", "end": "2026-07-05"},
    "Memorial Day Week": {"start": "2026-05-23", "end": "2026-05-25"},
    "Labor Day Week": {"start": "2026-09-05", "end": "2026-09-07"},
    "Spring Break": {"start": "2026-03-16", "end": "2026-03-22"},
    "Fall Break": {"start": "2026-10-12", "end": "2026-10-16"},
    "Winter Break": {"start": "2026-12-21", "end": "2027-01-02"},
    "Lunar New Year": {"start": "2026-01-28", "end": "2026-02-03"},
    "Eid al-Fitr": {"start": "2026-03-20", "end": "2026-03-22"},
    "Diwali": {"start": "2026-10-19", "end": "2026-10-21"},
    "Chuseok": {"start": "2026-09-28", "end": "2026-10-01"},
}


class HolidayAuction:
    """
    Priority-based fair holiday allocation system.

    Algorithm:
    1. Collect all worker preferences with priority rankings
    2. Round 1: Grant all Priority 1 requests where no conflict
    3. Conflicts on P1: tiebreak by fairness score (year-over-year history)
    4. Losers get their P2 guaranteed as compensation
    5. Round 2: Grant P2+ where they don't conflict with someone's P1
    6. Paired holiday balancing: if you got Christmas, lower priority for NYE
    7. Year-over-year: who sacrificed last year gets priority this year
    """

    def __init__(self, max_off_per_period=None):
        self.submissions = {}  # employee_id -> list of preferences
        self.historical_data = {}  # employee_id -> year-over-year allocation history
        self.allocation_results = {}
        self.max_off_per_period = max_off_per_period or 2  # max people off per period
        self.explanations = []

    def submit_preferences(self, employee_id, employee_name, preferences):
        """
        Worker submits holiday preferences ranked by priority.

        preferences: list of dicts, each with:
        - period_name: "Christmas Week", "Spring Break", or custom dates
        - start_date, end_date: if custom
        - priority: 1, 2, 3, ... (1 = most important)
        - reason: optional
        - flexible: bool (can shift by a few days?)
        """
        self.submissions[employee_id] = {
            "employee_id": employee_id,
            "employee_name": employee_name,
            "preferences": sorted(preferences, key=lambda x: x["priority"]),
            "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

    def set_historical_data(self, employee_id, history):
        """
        Set year-over-year history for fairness tiebreaking.

        history dict:
        - holidays_granted_last_year: list of period names
        - holidays_denied_last_year: list of period names
        - total_holidays_last_year: int
        - sacrifice_score: int (higher = sacrificed more)
        """
        self.historical_data[employee_id] = history

    def run_allocation(self):
        """
        Run the full allocation algorithm.
        Returns allocation results with explanations for every decision.
        """
        self.allocation_results = {}
        self.explanations = []

        if not self.submissions:
            return {"error": "No submissions to allocate"}

        # Initialize results
        for emp_id, sub in self.submissions.items():
            self.allocation_results[emp_id] = {
                "employee_id": emp_id,
                "employee_name": sub["employee_name"],
                "granted": [],
                "denied": [],
                "compensated": [],
            }

        # Round 1: Grant non-conflicting P1 requests
        self._round_1_priority_1()

        # Round 2: Grant P2+ where no conflict with P1
        self._round_2_remaining()

        # Apply paired holiday balancing
        self._apply_paired_balancing()

        # Generate fairness scorecard
        scorecard = self._generate_scorecard()

        return {
            "allocations": self.allocation_results,
            "scorecard": scorecard,
            "explanations": self.explanations,
            "summary": self._generate_summary(),
        }

    def get_allocation_for_employee(self, employee_id):
        """Get allocation results for a specific employee."""
        return self.allocation_results.get(employee_id)

    def get_fairness_scorecard(self):
        """Get the fairness scorecard showing balance across all workers."""
        return self._generate_scorecard()

    # --- Allocation Rounds ---

    def _round_1_priority_1(self):
        """Round 1: Process all Priority 1 requests."""
        self._log("=== ROUND 1: Priority 1 Allocation ===")

        # Group P1 requests by period
        p1_by_period = defaultdict(list)
        for emp_id, sub in self.submissions.items():
            for pref in sub["preferences"]:
                if pref["priority"] == 1:
                    period = pref.get("period_name", f"{pref.get('start_date')}-{pref.get('end_date')}")
                    p1_by_period[period].append({
                        "employee_id": emp_id,
                        "employee_name": sub["employee_name"],
                        "preference": pref,
                    })

        # Process each period
        for period, requesters in p1_by_period.items():
            if len(requesters) <= self.max_off_per_period:
                # No conflict — grant all
                for req in requesters:
                    self._grant(req["employee_id"], req["preference"],
                               f"P1 granted — no conflict ({len(requesters)}/{self.max_off_per_period} slots used)")
            else:
                # Conflict — tiebreak by fairness
                self._log(f"  CONFLICT on '{period}': {len(requesters)} want it, {self.max_off_per_period} slots")
                ranked = self._tiebreak_by_fairness(requesters)

                # Grant winners
                for winner in ranked[:self.max_off_per_period]:
                    self._grant(winner["employee_id"], winner["preference"],
                               f"P1 granted — won tiebreak (fairness score: {winner['fairness_score']})")

                # Deny losers but compensate with guaranteed P2
                for loser in ranked[self.max_off_per_period:]:
                    self._deny(loser["employee_id"], loser["preference"],
                              f"P1 denied — lost tiebreak (fairness score: {loser['fairness_score']}). "
                              f"Your P2 will be guaranteed as compensation.")
                    self.allocation_results[loser["employee_id"]]["compensated"].append({
                        "reason": f"Lost P1 tiebreak for '{period}'",
                        "compensation": "P2 request guaranteed",
                    })

    def _round_2_remaining(self):
        """Round 2: Process P2+ requests."""
        self._log("\n=== ROUND 2: Priority 2+ Allocation ===")

        # Track what's already allocated per period
        allocated_counts = self._count_allocations_by_period()

        # Get compensated employees (losers of Round 1 get P2 guaranteed)
        compensated_emps = set()
        for emp_id, result in self.allocation_results.items():
            if result["compensated"]:
                compensated_emps.add(emp_id)

        # Process P2+ in priority order
        for priority in range(2, 6):  # P2 through P5
            for emp_id, sub in self.submissions.items():
                for pref in sub["preferences"]:
                    if pref["priority"] != priority:
                        continue

                    period = pref.get("period_name", f"{pref.get('start_date')}-{pref.get('end_date')}")

                    # Already granted or denied this specific request?
                    already_processed = (
                        any(g["period"] == period for g in self.allocation_results[emp_id]["granted"]) or
                        any(d["period"] == period for d in self.allocation_results[emp_id]["denied"])
                    )
                    if already_processed:
                        continue

                    current_count = allocated_counts.get(period, 0)

                    # Compensated employees get guaranteed P2
                    if emp_id in compensated_emps and priority == 2:
                        self._grant(emp_id, pref,
                                   f"P2 guaranteed — compensation for P1 loss")
                        allocated_counts[period] = current_count + 1
                        compensated_emps.discard(emp_id)
                        continue

                    # Check if period has room
                    if current_count < self.max_off_per_period:
                        # Check if this conflicts with someone else's P1
                        conflicts_with_p1 = self._conflicts_with_granted_p1(period, emp_id)
                        if not conflicts_with_p1:
                            self._grant(emp_id, pref,
                                       f"P{priority} granted — room available ({current_count+1}/{self.max_off_per_period})")
                            allocated_counts[period] = current_count + 1
                        else:
                            self._deny(emp_id, pref,
                                      f"P{priority} denied — conflicts with {conflicts_with_p1}'s P1 request")
                    else:
                        self._deny(emp_id, pref,
                                  f"P{priority} denied — period full ({current_count}/{self.max_off_per_period})")

    def _apply_paired_balancing(self):
        """Apply paired holiday balancing (if you got Christmas, deprioritize NYE)."""
        self._log("\n=== PAIRED HOLIDAY BALANCING ===")

        for emp_id, result in self.allocation_results.items():
            granted_periods = [g["period"] for g in result["granted"]]

            for group_name, group in HOLIDAY_GROUPS.items():
                slots_in_group = group["slots"]
                granted_in_group = [p for p in granted_periods if p in slots_in_group]

                if len(granted_in_group) > 1:
                    # Got multiple in same group — flag for review
                    self._log(f"  NOTE: {result['employee_name']} got multiple in '{group_name}': {granted_in_group}")
                    # In a real system, might revoke the lower-priority one
                    # For now, just note it in explanations

    # --- Helper Methods ---

    def _tiebreak_by_fairness(self, requesters):
        """Rank conflicting requesters by fairness score (higher = more deserving)."""
        for req in requesters:
            emp_id = req["employee_id"]
            history = self.historical_data.get(emp_id, {})

            # Factors that increase priority (you sacrificed before)
            sacrifice_score = history.get("sacrifice_score", 0)
            denied_last_year = len(history.get("holidays_denied_last_year", []))
            total_last_year = history.get("total_holidays_last_year", 0)

            # Factors that decrease priority (you already got a lot)
            granted_this_round = len(self.allocation_results.get(emp_id, {}).get("granted", []))

            fairness_score = (
                sacrifice_score * 3 +
                denied_last_year * 10 +
                (5 - total_last_year) * 5 -  # fewer holidays last year = more deserving
                granted_this_round * 8
            )

            req["fairness_score"] = fairness_score

        return sorted(requesters, key=lambda x: x["fairness_score"], reverse=True)

    def _grant(self, employee_id, preference, reason):
        """Grant a holiday request."""
        period = preference.get("period_name",
                               f"{preference.get('start_date')}-{preference.get('end_date')}")
        self.allocation_results[employee_id]["granted"].append({
            "period": period,
            "priority": preference["priority"],
            "start_date": preference.get("start_date", HOLIDAY_PERIODS_2026.get(period, {}).get("start")),
            "end_date": preference.get("end_date", HOLIDAY_PERIODS_2026.get(period, {}).get("end")),
            "reason": reason,
        })
        self._log(f"  GRANTED: {self.submissions[employee_id]['employee_name']} -> {period} (P{preference['priority']}): {reason}")

    def _deny(self, employee_id, preference, reason):
        """Deny a holiday request with explanation."""
        period = preference.get("period_name",
                               f"{preference.get('start_date')}-{preference.get('end_date')}")
        self.allocation_results[employee_id]["denied"].append({
            "period": period,
            "priority": preference["priority"],
            "reason": reason,
        })
        self._log(f"  DENIED: {self.submissions[employee_id]['employee_name']} -> {period} (P{preference['priority']}): {reason}")

    def _count_allocations_by_period(self):
        """Count how many people are allocated to each period."""
        counts = defaultdict(int)
        for emp_id, result in self.allocation_results.items():
            for g in result["granted"]:
                counts[g["period"]] += 1
        return counts

    def _conflicts_with_granted_p1(self, period, exclude_emp):
        """Check if a period conflicts with someone's already-granted P1."""
        for emp_id, result in self.allocation_results.items():
            if emp_id == exclude_emp:
                continue
            for g in result["granted"]:
                if g["period"] == period and g["priority"] == 1:
                    return result["employee_name"] if emp_id in self.submissions else emp_id
        return None

    def _generate_scorecard(self):
        """Generate fairness scorecard showing balance."""
        scorecard = []
        for emp_id, result in self.allocation_results.items():
            granted_count = len(result["granted"])
            denied_count = len(result["denied"])
            p1_granted = any(g["priority"] == 1 for g in result["granted"])

            # Value score: P1 holiday = 10 pts, P2 = 7, P3+ = 4
            value_score = sum(
                10 if g["priority"] == 1 else 7 if g["priority"] == 2 else 4
                for g in result["granted"]
            )

            scorecard.append({
                "employee_id": emp_id,
                "employee_name": result["employee_name"],
                "holidays_granted": granted_count,
                "holidays_denied": denied_count,
                "p1_granted": p1_granted,
                "value_score": value_score,
                "compensated": len(result["compensated"]) > 0,
            })

        # Sort by value score for comparison
        scorecard.sort(key=lambda x: x["value_score"], reverse=True)

        # Calculate fairness metrics
        values = [s["value_score"] for s in scorecard]
        avg_value = sum(values) / max(1, len(values))
        max_deviation = max(abs(v - avg_value) for v in values) if values else 0

        return {
            "employees": scorecard,
            "avg_value_score": round(avg_value, 1),
            "max_deviation": round(max_deviation, 1),
            "fairness_rating": "EXCELLENT" if max_deviation <= 3 else (
                "GOOD" if max_deviation <= 6 else "NEEDS_REVIEW"
            ),
        }

    def _generate_summary(self):
        """Generate allocation summary."""
        total_granted = sum(len(r["granted"]) for r in self.allocation_results.values())
        total_denied = sum(len(r["denied"]) for r in self.allocation_results.values())
        total_compensated = sum(1 for r in self.allocation_results.values() if r["compensated"])

        return {
            "total_submissions": len(self.submissions),
            "total_requests": sum(len(s["preferences"]) for s in self.submissions.values()),
            "total_granted": total_granted,
            "total_denied": total_denied,
            "grant_rate": round(total_granted / max(1, total_granted + total_denied) * 100, 1),
            "employees_compensated": total_compensated,
        }

    def _log(self, message):
        """Log allocation decision."""
        self.explanations.append(message)


# ============================================================
# DEMO
# ============================================================

def create_demo_auction():
    """Create a demo auction with sample submissions."""
    auction = HolidayAuction(max_off_per_period=2)

    # Submit preferences
    auction.submit_preferences("E001", "Sarah Martinez", [
        {"period_name": "Christmas Week", "priority": 1, "reason": "Family visiting from Mexico",
         "start_date": "2026-12-21", "end_date": "2026-12-27"},
        {"period_name": "Labor Day Week", "priority": 2, "reason": "Beach trip",
         "start_date": "2026-09-05", "end_date": "2026-09-07"},
        {"period_name": "Spring Break", "priority": 3, "reason": "Kids school break",
         "start_date": "2026-03-16", "end_date": "2026-03-22"},
    ])

    auction.submit_preferences("E002", "James Wilson", [
        {"period_name": "Thanksgiving Week", "priority": 1, "reason": "Family tradition",
         "start_date": "2026-11-23", "end_date": "2026-11-29"},
        {"period_name": "Christmas Week", "priority": 2, "reason": "Would like but flexible",
         "start_date": "2026-12-21", "end_date": "2026-12-27"},
        {"period_name": "July 4th Week", "priority": 3, "reason": "Camping trip",
         "start_date": "2026-06-29", "end_date": "2026-07-05"},
    ])

    auction.submit_preferences("E003", "Aisha Patel", [
        {"period_name": "Spring Break", "priority": 1, "reason": "Kids school break",
         "start_date": "2026-03-16", "end_date": "2026-03-22"},
        {"period_name": "Diwali", "priority": 2, "reason": "Religious observance",
         "start_date": "2026-10-19", "end_date": "2026-10-21"},
        {"period_name": "Christmas Week", "priority": 3, "reason": "Family",
         "start_date": "2026-12-21", "end_date": "2026-12-27"},
    ])

    auction.submit_preferences("E005", "Chen Wei", [
        {"period_name": "Lunar New Year", "priority": 1, "reason": "Family celebration",
         "start_date": "2026-01-28", "end_date": "2026-02-03"},
        {"period_name": "Christmas Week", "priority": 2, "reason": "Travel to family",
         "start_date": "2026-12-21", "end_date": "2026-12-27"},
        {"period_name": "Labor Day Week", "priority": 3, "reason": "Rest",
         "start_date": "2026-09-05", "end_date": "2026-09-07"},
    ])

    auction.submit_preferences("E008", "David Kim", [
        {"period_name": "Chuseok", "priority": 1, "reason": "Korean harvest festival",
         "start_date": "2026-09-28", "end_date": "2026-10-01"},
        {"period_name": "Christmas Week", "priority": 2, "reason": "Family time",
         "start_date": "2026-12-21", "end_date": "2026-12-27"},
        {"period_name": "New Year's Week", "priority": 3, "reason": "Celebration",
         "start_date": "2026-12-28", "end_date": "2027-01-03"},
    ])

    # Historical data (year-over-year memory)
    auction.set_historical_data("E001", {
        "holidays_granted_last_year": ["Thanksgiving Week", "Spring Break"],
        "holidays_denied_last_year": ["Christmas Week"],
        "total_holidays_last_year": 2,
        "sacrifice_score": 8,  # was denied Christmas last year
    })
    auction.set_historical_data("E002", {
        "holidays_granted_last_year": ["Christmas Week", "July 4th Week"],
        "holidays_denied_last_year": [],
        "total_holidays_last_year": 2,
        "sacrifice_score": 0,
    })
    auction.set_historical_data("E003", {
        "holidays_granted_last_year": ["Spring Break"],
        "holidays_denied_last_year": ["Thanksgiving Week"],
        "total_holidays_last_year": 1,
        "sacrifice_score": 5,
    })
    auction.set_historical_data("E005", {
        "holidays_granted_last_year": ["Lunar New Year", "Christmas Week"],
        "holidays_denied_last_year": [],
        "total_holidays_last_year": 2,
        "sacrifice_score": 0,
    })
    auction.set_historical_data("E008", {
        "holidays_granted_last_year": ["Chuseok"],
        "holidays_denied_last_year": ["New Year's Week", "Christmas Week"],
        "total_holidays_last_year": 1,
        "sacrifice_score": 12,  # denied twice last year
    })

    return auction


if __name__ == "__main__":
    auction = create_demo_auction()
    results = auction.run_allocation()

    print("=" * 70)
    print("  HOLIDAY AUCTION - PRIORITY-BASED FAIR ALLOCATION")
    print("=" * 70)

    # Summary
    summary = results["summary"]
    print(f"\n  SUMMARY:")
    print(f"    Submissions: {summary['total_submissions']} employees")
    print(f"    Total requests: {summary['total_requests']}")
    print(f"    Granted: {summary['total_granted']}")
    print(f"    Denied: {summary['total_denied']}")
    print(f"    Grant rate: {summary['grant_rate']}%")
    print(f"    Compensated: {summary['employees_compensated']}")

    # Per-employee results
    print(f"\n\n  ALLOCATION RESULTS:")
    print(f"  {'-'*65}")

    for emp_id, result in results["allocations"].items():
        print(f"\n  {result['employee_name']}:")
        if result["granted"]:
            for g in result["granted"]:
                print(f"    [GRANTED] {g['period']} (P{g['priority']}): {g['reason']}")
        if result["denied"]:
            for d in result["denied"]:
                print(f"    [DENIED]  {d['period']} (P{d['priority']}): {d['reason']}")
        if result["compensated"]:
            for c in result["compensated"]:
                print(f"    [COMPENSATED] {c['reason']} -> {c['compensation']}")

    # Fairness scorecard
    print(f"\n\n  FAIRNESS SCORECARD:")
    scorecard = results["scorecard"]
    print(f"    Overall fairness: {scorecard['fairness_rating']}")
    print(f"    Average value: {scorecard['avg_value_score']}")
    print(f"    Max deviation: {scorecard['max_deviation']}")
    print(f"\n  {'Employee':<20} {'Granted':<9} {'Denied':<8} {'P1 Got?':<9} {'Value':<7}")
    print(f"  {'-'*55}")
    for s in scorecard["employees"]:
        p1 = "Yes" if s["p1_granted"] else "No"
        print(f"  {s['employee_name']:<20} {s['holidays_granted']:<9} "
              f"{s['holidays_denied']:<8} {p1:<9} {s['value_score']:<7}")

    # Explanations (audit trail)
    print(f"\n\n  ALLOCATION LOG (audit trail):")
    print(f"  {'-'*60}")
    for exp in results["explanations"]:
        print(f"  {exp}")
