"""
Workforce Compliance AI - Simulation Mode ("What If" Engine)
Model scenarios before committing: add/remove staff, change shift patterns,
new laws, CBA terms, demand changes. Compare current vs proposed.
"""

from datetime import datetime, timedelta
from collections import defaultdict
from schedule_generator import ScheduleGenerator, SHIFT_PATTERNS
from hours_tracker import get_all_employee_dashboards, OT_THRESHOLD_WEEKLY, MAX_WEEKLY_HOURS
from compliance_checker import check_compliance


class Simulation:
    """
    Run what-if scenarios and compare outcomes before making real changes.
    """

    def __init__(self, employees, schedule_data, reference_date=None):
        self.employees = employees
        self.schedule_data = schedule_data
        self.reference_date = reference_date or datetime.now()
        self.scenarios = []

    def simulate_add_workers(self, count, role, names=None):
        """
        What if we add N workers?
        Shows impact on: OT, coverage gaps, fatigue, cost.
        """
        if names is None:
            names = [f"New Hire {i+1}" for i in range(count)]

        current = self._analyze_current()

        # Create new employees
        new_emps = []
        for i in range(count):
            new_emps.append({
                "id": f"NEW{i+1:03d}",
                "name": names[i] if i < len(names) else f"New Hire {i+1}",
                "role": role,
                "seniority": len(self.employees) + i + 1,
                "is_minor": False,
                "hire_date": datetime.now().strftime("%Y-%m-%d"),
                "hourly_rate": 18.00,
            })

        expanded_emps = self.employees + new_emps
        projected = self._analyze_with_workers(expanded_emps)

        # Calculate impact
        ot_reduction = current["total_ot_hours"] - projected["total_ot_hours"]
        fatigue_improvement = current["avg_fatigue"] - projected["avg_fatigue"]
        coverage_improvement = projected["coverage_score"] - current["coverage_score"]

        scenario = {
            "type": "ADD_WORKERS",
            "description": f"Add {count} {role}(s)",
            "current": current,
            "projected": projected,
            "impact": {
                "ot_hours_saved_weekly": round(ot_reduction, 1),
                "ot_cost_saved_weekly": round(ot_reduction * 30, 0),  # avg $30/hr OT
                "fatigue_score_reduction": round(fatigue_improvement, 1),
                "coverage_improvement_pct": round(coverage_improvement, 1),
                "new_hire_cost_weekly": count * 40 * 18,  # 40hrs * rate
                "net_savings_weekly": round(ot_reduction * 30 - count * 40 * 18, 0),
            },
            "recommendation": self._add_workers_recommendation(count, ot_reduction, fatigue_improvement),
        }
        self.scenarios.append(scenario)
        return scenario

    def simulate_remove_workers(self, count, role):
        """What if we lose N workers (attrition, layoff)?"""
        current = self._analyze_current()

        # Remove workers of this role
        remaining = [e for e in self.employees if e.get("role") != role]
        role_workers = [e for e in self.employees if e.get("role") == role]
        remaining += role_workers[count:]  # keep all except the last N

        projected = self._analyze_with_workers(remaining)

        ot_increase = projected["total_ot_hours"] - current["total_ot_hours"]
        fatigue_increase = projected["avg_fatigue"] - current["avg_fatigue"]

        scenario = {
            "type": "REMOVE_WORKERS",
            "description": f"Lose {count} {role}(s)",
            "current": current,
            "projected": projected,
            "impact": {
                "ot_hours_increase_weekly": round(ot_increase, 1),
                "ot_cost_increase_weekly": round(ot_increase * 30, 0),
                "fatigue_score_increase": round(fatigue_increase, 1),
                "coverage_gap_risk": "HIGH" if len(remaining) < len(self.employees) * 0.8 else "MEDIUM",
                "shifts_at_risk": round(count * 5),  # ~5 shifts per week per person
            },
            "recommendation": (
                f"RISK: Losing {count} {role}(s) will increase OT by ~{ot_increase:.0f}h/week "
                f"(${ot_increase*30:.0f} cost). Recommend hiring {count} replacements within 30 days."
            ),
        }
        self.scenarios.append(scenario)
        return scenario

    def simulate_shift_pattern_change(self, from_pattern, to_pattern, worker_count=None):
        """What if we change shift patterns (e.g., 8hr to 12hr shifts)?"""
        if worker_count is None:
            worker_count = len(self.employees)

        workers = [{"id": f"W{i}", "name": f"Worker {i}"} for i in range(worker_count)]

        # Generate current pattern
        gen_current = ScheduleGenerator(workers, from_pattern)
        results_current = gen_current.generate(
            self.reference_date.strftime("%Y-%m-%d"),
            (self.reference_date + timedelta(days=30)).strftime("%Y-%m-%d")
        )
        sc_current = results_current["fairness_scorecard"]

        # Generate new pattern
        gen_new = ScheduleGenerator(workers, to_pattern)
        results_new = gen_new.generate(
            self.reference_date.strftime("%Y-%m-%d"),
            (self.reference_date + timedelta(days=30)).strftime("%Y-%m-%d")
        )
        sc_new = results_new["fairness_scorecard"]

        from_info = SHIFT_PATTERNS[from_pattern]
        to_info = SHIFT_PATTERNS[to_pattern]

        scenario = {
            "type": "SHIFT_PATTERN_CHANGE",
            "description": f"Change from {from_info['name']} to {to_info['name']}",
            "current_pattern": {
                "name": from_info["name"],
                "shifts_per_day": from_info["shifts_per_day"],
                "total_shifts_month": results_current["total_shifts"],
                "fairness": sc_current["fairness_rating"],
                "night_deviation": sc_current["max_night_deviation"],
            },
            "proposed_pattern": {
                "name": to_info["name"],
                "shifts_per_day": to_info["shifts_per_day"],
                "total_shifts_month": results_new["total_shifts"],
                "fairness": sc_new["fairness_rating"],
                "night_deviation": sc_new["max_night_deviation"],
            },
            "impact": {
                "shifts_per_day_change": to_info["shifts_per_day"] - from_info["shifts_per_day"],
                "total_shifts_change": results_new["total_shifts"] - results_current["total_shifts"],
                "fairness_change": f"{sc_current['fairness_rating']} -> {sc_new['fairness_rating']}",
            },
            "recommendation": (
                f"Pattern change would go from {results_current['total_shifts']} to "
                f"{results_new['total_shifts']} shifts/month. "
                f"Fairness: {sc_new['fairness_rating']}."
            ),
        }
        self.scenarios.append(scenario)
        return scenario

    def simulate_new_compliance_rule(self, rule_name, rule_impact_description, affected_pct=0.3):
        """What if a new labor law passes? How many violations would current schedule create?"""
        current_violations = check_compliance(self.schedule_data)
        current_count = len(current_violations)

        # Estimate additional violations from new rule
        total_shifts = len(self.schedule_data.get("shifts", []))
        estimated_new_violations = round(total_shifts * affected_pct)

        scenario = {
            "type": "NEW_COMPLIANCE_RULE",
            "description": f"New rule: {rule_name}",
            "current_violations": current_count,
            "estimated_additional_violations": estimated_new_violations,
            "total_projected_violations": current_count + estimated_new_violations,
            "affected_shifts_pct": f"{affected_pct*100:.0f}%",
            "impact": {
                "rule": rule_name,
                "description": rule_impact_description,
                "additional_violations": estimated_new_violations,
                "estimated_penalty_exposure": f"${estimated_new_violations * 500:,.0f} - ${estimated_new_violations * 2000:,.0f}",
                "schedule_changes_needed": estimated_new_violations,
            },
            "recommendation": (
                f"New '{rule_name}' would create ~{estimated_new_violations} additional violations "
                f"in current schedule. Estimated exposure: ${estimated_new_violations * 500:,.0f}+. "
                f"Schedule redesign recommended before effective date."
            ),
        }
        self.scenarios.append(scenario)
        return scenario

    def simulate_demand_change(self, increase_pct):
        """What if demand increases/decreases by X%?"""
        current = self._analyze_current()
        current_headcount = len(self.employees)
        additional_needed = round(current_headcount * (increase_pct / 100))

        if increase_pct > 0:
            scenario = {
                "type": "DEMAND_INCREASE",
                "description": f"Demand increases {increase_pct}%",
                "current_headcount": current_headcount,
                "additional_headcount_needed": additional_needed,
                "impact": {
                    "without_hiring": {
                        "ot_increase_pct": round(increase_pct * 1.5),
                        "fatigue_risk": "HIGH" if increase_pct > 20 else "MEDIUM",
                        "compliance_risk": "HIGH" if increase_pct > 30 else "MEDIUM",
                        "estimated_weekly_ot_cost": round(additional_needed * 20 * 30),
                    },
                    "with_hiring": {
                        "hires_needed": additional_needed,
                        "time_to_fill_weeks": 4,
                        "training_weeks": 2,
                        "fully_staffed_by": (self.reference_date + timedelta(weeks=6)).strftime("%Y-%m-%d"),
                    },
                },
                "recommendation": (
                    f"{increase_pct}% demand increase requires {additional_needed} additional workers. "
                    f"Without hiring: ${additional_needed * 20 * 30:,}/week in OT. "
                    f"Start hiring now — fully staffed by "
                    f"{(self.reference_date + timedelta(weeks=6)).strftime('%b %d')}."
                ),
            }
        else:
            reduction = abs(additional_needed)
            scenario = {
                "type": "DEMAND_DECREASE",
                "description": f"Demand decreases {abs(increase_pct)}%",
                "current_headcount": current_headcount,
                "surplus_workers": reduction,
                "impact": {
                    "options": [
                        f"Reduce hours across team (everyone loses ~{abs(increase_pct)}% hours)",
                        f"VTO (Voluntary Time Off) — offer {reduction} slots per shift",
                        f"Reassign {reduction} workers to other departments",
                        f"Natural attrition — don't backfill next {reduction} departures",
                    ],
                },
                "recommendation": (
                    f"{abs(increase_pct)}% demand decrease creates {reduction} surplus workers. "
                    f"Recommend VTO offers before considering reductions."
                ),
            }

        self.scenarios.append(scenario)
        return scenario

    def compare_scenarios(self):
        """Compare all simulated scenarios side by side."""
        if not self.scenarios:
            return {"message": "No scenarios simulated yet."}

        return {
            "scenarios_run": len(self.scenarios),
            "summaries": [
                {
                    "type": s["type"],
                    "description": s["description"],
                    "recommendation": s["recommendation"],
                }
                for s in self.scenarios
            ],
        }

    # --- Private Analysis ---

    def _analyze_current(self):
        """Analyze current state."""
        if not self.schedule_data.get("shifts"):
            return {"total_ot_hours": 0, "avg_fatigue": 20, "coverage_score": 80}

        dashboards = get_all_employee_dashboards(
            self.schedule_data["shifts"], self.employees, self.reference_date
        )

        total_ot = sum(max(0, d["weekly_hours"] - OT_THRESHOLD_WEEKLY) for d in dashboards)
        avg_fatigue = sum(d.get("fatigue_score", 0) for d in dashboards) / max(1, len(dashboards))
        coverage_score = 80  # baseline

        return {
            "total_ot_hours": total_ot,
            "avg_fatigue": avg_fatigue,
            "coverage_score": coverage_score,
            "headcount": len(self.employees),
        }

    def _analyze_with_workers(self, workers):
        """Analyze projected state with different worker count."""
        # Simplified: more workers = less OT and fatigue
        current = self._analyze_current()
        ratio = len(self.employees) / max(1, len(workers))

        projected_ot = current["total_ot_hours"] * ratio
        projected_fatigue = current["avg_fatigue"] * min(1.5, ratio)
        projected_coverage = min(100, current["coverage_score"] / ratio)

        return {
            "total_ot_hours": projected_ot,
            "avg_fatigue": projected_fatigue,
            "coverage_score": projected_coverage,
            "headcount": len(workers),
        }

    def _add_workers_recommendation(self, count, ot_reduction, fatigue_improvement):
        net_benefit = ot_reduction * 30 - count * 40 * 18
        if net_benefit > 0:
            return (
                f"POSITIVE ROI: Adding {count} worker(s) saves ${net_benefit:.0f}/week net "
                f"(OT savings exceed new hire cost). Fatigue drops {fatigue_improvement:.0f} points."
            )
        return (
            f"Adding {count} worker(s) costs ${abs(net_benefit):.0f}/week more than OT savings, "
            f"but reduces fatigue by {fatigue_improvement:.0f} points and improves coverage."
        )


if __name__ == "__main__":
    from sample_schedule import generate_schedule, EMPLOYEES

    schedule = generate_schedule()
    sim = Simulation(EMPLOYEES, schedule, reference_date=datetime(2026, 7, 11))

    print("=" * 70)
    print("  SIMULATION MODE - WHAT IF SCENARIOS")
    print("=" * 70)

    # Scenario 1: Add 3 pickers
    print("\n  SCENARIO 1: What if we add 3 Pickers?")
    print("  " + "-" * 50)
    result = sim.simulate_add_workers(3, "Pick")
    print(f"  OT saved: {result['impact']['ot_hours_saved_weekly']}h/week")
    print(f"  OT cost saved: ${result['impact']['ot_cost_saved_weekly']}/week")
    print(f"  New hire cost: ${result['impact']['new_hire_cost_weekly']}/week")
    print(f"  Net: ${result['impact']['net_savings_weekly']}/week")
    print(f"  Recommendation: {result['recommendation']}")

    # Scenario 2: Lose 2 workers
    print("\n\n  SCENARIO 2: What if we lose 2 Pickers?")
    print("  " + "-" * 50)
    result = sim.simulate_remove_workers(2, "Pick")
    print(f"  OT increase: {result['impact']['ot_hours_increase_weekly']}h/week")
    print(f"  Coverage gap risk: {result['impact']['coverage_gap_risk']}")
    print(f"  Recommendation: {result['recommendation']}")

    # Scenario 3: Change shift pattern
    print("\n\n  SCENARIO 3: Change from 24/7 (3x8hr) to 12hr shifts?")
    print("  " + "-" * 50)
    result = sim.simulate_shift_pattern_change("healthcare_24_7", "healthcare_12hr", 5)
    print(f"  Current: {result['current_pattern']['total_shifts_month']} shifts/month, fairness={result['current_pattern']['fairness']}")
    print(f"  Proposed: {result['proposed_pattern']['total_shifts_month']} shifts/month, fairness={result['proposed_pattern']['fairness']}")
    print(f"  Recommendation: {result['recommendation']}")

    # Scenario 4: New compliance rule
    print("\n\n  SCENARIO 4: What if California passes new rest period law?")
    print("  " + "-" * 50)
    result = sim.simulate_new_compliance_rule(
        "CA Rest Period Extension",
        "Minimum 12 hours between shifts (up from 10)",
        affected_pct=0.15
    )
    print(f"  Current violations: {result['current_violations']}")
    print(f"  Additional from new rule: {result['estimated_additional_violations']}")
    print(f"  Penalty exposure: {result['impact']['estimated_penalty_exposure']}")
    print(f"  Recommendation: {result['recommendation']}")

    # Scenario 5: Demand surge
    print("\n\n  SCENARIO 5: What if demand increases 30% (peak season)?")
    print("  " + "-" * 50)
    result = sim.simulate_demand_change(30)
    print(f"  Additional headcount needed: {result['additional_headcount_needed']}")
    print(f"  Without hiring OT cost: ${result['impact']['without_hiring']['estimated_weekly_ot_cost']}/week")
    print(f"  Recommendation: {result['recommendation']}")
