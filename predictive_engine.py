"""
Workforce Compliance AI - Predictive Absenteeism & Worker Wellness Engine
Predicts callouts before they happen. Detects burnout patterns.
Calculates schedule stability and attrition risk.
Feeds into self-healing for pre-positioning coverage.
"""

from datetime import datetime, timedelta
from collections import defaultdict
import math


# Risk thresholds
CALLOUT_RISK_THRESHOLDS = {
    "low": 0.25,
    "medium": 0.50,
    "high": 0.75,
}

BURNOUT_THRESHOLDS = {
    "low": 30,
    "medium": 55,
    "high": 75,
}

ATTRITION_THRESHOLDS = {
    "low": 25,
    "medium": 50,
    "high": 70,
}


class PredictiveEngine:
    """
    Predict absenteeism, detect burnout, and calculate attrition risk.
    Uses pattern analysis on historical data (no external ML library needed).
    """

    def __init__(self, employees=None, absence_history=None, schedule_history=None,
                 request_history=None):
        """
        absence_history: list of {"employee_id", "date", "day_of_week", "type", "reason"}
        schedule_history: list of shifts with employee assignments
        request_history: list of requests and their outcomes
        """
        self.employees = employees or []
        self.absence_history = absence_history or []
        self.schedule_history = schedule_history or []
        self.request_history = request_history or []

    # ============================================================
    # PREDICTIVE ABSENTEEISM
    # ============================================================

    def predict_callouts(self, target_date, conditions=None):
        """
        Predict who's likely to call out on a target date.

        Factors considered:
        - Day-of-week pattern (always calls out Mondays?)
        - Post-payday pattern (day after payday = higher callout)
        - Consecutive days fatigue (5th+ day in a row)
        - Recent denial of PTO (asked for this day off and was denied)
        - Team understaffed (when team is short, more callouts cascade)
        - Weather (if conditions provided)
        - Holiday-adjacent (day before/after a holiday)

        Returns: list of employees with callout probability + reasoning
        """
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, "%Y-%m-%d")

        conditions = conditions or {}
        day_name = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][target_date.weekday()]

        predictions = []

        for emp in self.employees:
            emp_id = emp["id"]
            factors = []
            risk_score = 0.0

            # Factor 1: Day-of-week pattern
            dow_risk = self._day_of_week_risk(emp_id, day_name)
            if dow_risk > 0:
                risk_score += dow_risk * 0.30
                factors.append({
                    "factor": "Day-of-week pattern",
                    "weight": 0.30,
                    "value": dow_risk,
                    "detail": f"Called out on {day_name}s {self._count_dow_absences(emp_id, day_name)} times in 90 days",
                })

            # Factor 2: Post-payday (assume biweekly Friday payday)
            payday_risk = self._payday_proximity_risk(target_date)
            if payday_risk > 0:
                risk_score += payday_risk * 0.10
                factors.append({
                    "factor": "Post-payday",
                    "weight": 0.10,
                    "value": payday_risk,
                    "detail": "Day after payday (historically higher callout rate)",
                })

            # Factor 3: Consecutive days fatigue
            consec_risk = self._consecutive_days_risk(emp_id, target_date)
            if consec_risk > 0:
                risk_score += consec_risk * 0.20
                factors.append({
                    "factor": "Consecutive days fatigue",
                    "weight": 0.20,
                    "value": consec_risk,
                    "detail": f"Will be on day {self._get_consecutive_count(emp_id, target_date)+1} in a row",
                })

            # Factor 4: Recently denied PTO for this date
            denial_risk = self._denied_pto_risk(emp_id, target_date)
            if denial_risk > 0:
                risk_score += denial_risk * 0.20
                factors.append({
                    "factor": "Denied PTO for this date",
                    "weight": 0.20,
                    "value": denial_risk,
                    "detail": "Requested this day off and was denied — higher risk of unplanned absence",
                })

            # Factor 5: Holiday-adjacent
            holiday_adj_risk = self._holiday_adjacent_risk(target_date)
            if holiday_adj_risk > 0:
                risk_score += holiday_adj_risk * 0.10
                factors.append({
                    "factor": "Holiday-adjacent",
                    "weight": 0.10,
                    "value": holiday_adj_risk,
                    "detail": "Day before/after a holiday (industry-wide higher callout)",
                })

            # Factor 6: Overall absence frequency
            freq_risk = self._frequency_risk(emp_id)
            if freq_risk > 0:
                risk_score += freq_risk * 0.10
                factors.append({
                    "factor": "Absence frequency",
                    "weight": 0.10,
                    "value": freq_risk,
                    "detail": f"Above-average absence rate ({self._count_recent_absences(emp_id)} in 90 days)",
                })

            # Weather factor (if provided)
            if conditions.get("severe_weather"):
                weather_risk = 0.6
                risk_score += weather_risk * 0.15
                factors.append({
                    "factor": "Severe weather forecast",
                    "weight": 0.15,
                    "value": weather_risk,
                    "detail": f"Weather: {conditions.get('weather_detail', 'severe conditions')}",
                })

            # Normalize to 0-1
            risk_score = min(1.0, max(0.0, risk_score))

            # Determine risk level
            if risk_score >= CALLOUT_RISK_THRESHOLDS["high"]:
                risk_level = "HIGH"
            elif risk_score >= CALLOUT_RISK_THRESHOLDS["medium"]:
                risk_level = "MEDIUM"
            elif risk_score >= CALLOUT_RISK_THRESHOLDS["low"]:
                risk_level = "LOW"
            else:
                risk_level = "MINIMAL"

            predictions.append({
                "employee_id": emp_id,
                "name": emp["name"],
                "risk_score": round(risk_score, 2),
                "risk_level": risk_level,
                "risk_percentage": f"{risk_score*100:.0f}%",
                "factors": factors,
                "recommendation": self._callout_recommendation(risk_level, factors),
            })

        # Sort by risk score descending
        predictions.sort(key=lambda x: x["risk_score"], reverse=True)
        return predictions

    def get_daily_risk_summary(self, target_date, conditions=None):
        """Get a summary of callout risk for a specific day."""
        predictions = self.predict_callouts(target_date, conditions)

        high_risk = [p for p in predictions if p["risk_level"] == "HIGH"]
        medium_risk = [p for p in predictions if p["risk_level"] == "MEDIUM"]

        total_expected_callouts = sum(p["risk_score"] for p in predictions)

        return {
            "date": target_date if isinstance(target_date, str) else target_date.strftime("%Y-%m-%d"),
            "total_employees": len(predictions),
            "high_risk_count": len(high_risk),
            "medium_risk_count": len(medium_risk),
            "expected_callouts": round(total_expected_callouts, 1),
            "high_risk_employees": high_risk,
            "medium_risk_employees": medium_risk,
            "recommendation": (
                f"Pre-position {max(1, round(total_expected_callouts))} standby worker(s). "
                f"{len(high_risk)} employee(s) at high risk."
                if total_expected_callouts >= 0.5 else
                "Low callout risk. Normal staffing should suffice."
            ),
        }

    # ============================================================
    # BURNOUT DETECTION
    # ============================================================

    def calculate_burnout_scores(self):
        """
        Calculate burnout score (0-100) for each employee.

        Burnout signals:
        - Always getting undesirable shifts (nights, weekends, holidays)
        - OT forced (not voluntary)
        - PTO denied repeatedly
        - No consecutive days off in recent period
        - Schedule instability (frequent changes)
        - High coverage request burden
        """
        scores = []

        for emp in self.employees:
            emp_id = emp["id"]
            signals = {}

            # Signal 1: Undesirable shift burden
            undesirable = self._undesirable_shift_load(emp_id)
            signals["undesirable_shifts"] = undesirable

            # Signal 2: Forced OT (not voluntary)
            forced_ot = self._forced_ot_burden(emp_id)
            signals["forced_overtime"] = forced_ot

            # Signal 3: PTO denial rate
            pto_denial = self._pto_denial_rate(emp_id)
            signals["pto_denied"] = pto_denial

            # Signal 4: Days since rest (consecutive work without full day off)
            rest_deficit = self._rest_deficit(emp_id)
            signals["rest_deficit"] = rest_deficit

            # Signal 5: Schedule instability
            instability = self._schedule_instability(emp_id)
            signals["schedule_instability"] = instability

            # Signal 6: Coverage request overload
            coverage_load = self._coverage_overload(emp_id)
            signals["coverage_overload"] = coverage_load

            # Weighted burnout score
            burnout_score = (
                undesirable * 0.25 +
                forced_ot * 0.20 +
                pto_denial * 0.20 +
                rest_deficit * 0.15 +
                instability * 0.10 +
                coverage_load * 0.10
            )
            burnout_score = min(100, max(0, round(burnout_score)))

            if burnout_score >= BURNOUT_THRESHOLDS["high"]:
                level = "HIGH"
            elif burnout_score >= BURNOUT_THRESHOLDS["medium"]:
                level = "MEDIUM"
            else:
                level = "LOW"

            scores.append({
                "employee_id": emp_id,
                "name": emp["name"],
                "burnout_score": burnout_score,
                "burnout_level": level,
                "signals": signals,
                "top_driver": max(signals, key=signals.get),
                "intervention": self._burnout_intervention(level, signals),
            })

        scores.sort(key=lambda x: x["burnout_score"], reverse=True)
        return scores

    # ============================================================
    # SCHEDULE STABILITY SCORE
    # ============================================================

    def calculate_stability_scores(self):
        """
        Calculate schedule stability (0-100%) per employee.
        Higher = more stable/predictable schedule.

        Factors:
        - How often their schedule changes after being posted
        - Consistency of shift times week-to-week
        - Predictability of days off
        - Short-notice changes
        """
        scores = []

        for emp in self.employees:
            emp_id = emp["id"]

            # In production these come from change tracking
            # For now, derive from available data
            changes = self._count_schedule_changes(emp_id)
            consistency = self._shift_time_consistency(emp_id)
            day_off_predictability = self._day_off_predictability(emp_id)

            stability = (
                (100 - changes * 5) * 0.40 +  # fewer changes = more stable
                consistency * 0.35 +
                day_off_predictability * 0.25
            )
            stability = min(100, max(0, round(stability)))

            scores.append({
                "employee_id": emp_id,
                "name": emp["name"],
                "stability_score": stability,
                "stability_pct": f"{stability}%",
                "changes_this_month": changes,
                "shift_consistency": round(consistency),
                "day_off_predictability": round(day_off_predictability),
                "risk": "HIGH" if stability < 60 else ("MEDIUM" if stability < 80 else "LOW"),
            })

        scores.sort(key=lambda x: x["stability_score"])
        return scores

    # ============================================================
    # ATTRITION RISK
    # ============================================================

    def calculate_attrition_risk(self):
        """
        Predict attrition risk based on scheduling patterns.

        Research shows these scheduling patterns correlate with quitting:
        - Low schedule stability (<60%)
        - High burnout score (>70)
        - Repeatedly getting worst shifts
        - Never getting preferred hours/days
        - Denied time-off requests
        - Forced overtime without volunteering
        """
        burnout_scores = {s["employee_id"]: s for s in self.calculate_burnout_scores()}
        stability_scores = {s["employee_id"]: s for s in self.calculate_stability_scores()}

        risks = []

        for emp in self.employees:
            emp_id = emp["id"]
            burnout = burnout_scores.get(emp_id, {})
            stability = stability_scores.get(emp_id, {})

            burnout_score = burnout.get("burnout_score", 0)
            stability_score = stability.get("stability_score", 80)

            # Tenure factor: new employees (<6 months) are higher risk
            hire_date = emp.get("hire_date", "2024-01-01")
            if isinstance(hire_date, str):
                hire_date = datetime.strptime(hire_date, "%Y-%m-%d")
            tenure_months = (datetime.now() - hire_date).days / 30
            tenure_risk = max(0, (12 - tenure_months) / 12 * 30) if tenure_months < 12 else 0

            # Calculate composite attrition risk
            attrition_score = (
                burnout_score * 0.35 +
                (100 - stability_score) * 0.25 +
                tenure_risk * 0.20 +
                self._preference_mismatch(emp_id) * 0.20
            )
            attrition_score = min(100, max(0, round(attrition_score)))

            if attrition_score >= ATTRITION_THRESHOLDS["high"]:
                level = "HIGH"
            elif attrition_score >= ATTRITION_THRESHOLDS["medium"]:
                level = "MEDIUM"
            else:
                level = "LOW"

            risks.append({
                "employee_id": emp_id,
                "name": emp["name"],
                "attrition_risk": attrition_score,
                "risk_level": level,
                "tenure_months": round(tenure_months),
                "burnout_score": burnout_score,
                "stability_score": stability_score,
                "drivers": self._attrition_drivers(burnout, stability, tenure_risk),
                "retention_action": self._retention_recommendation(level, burnout, stability, emp),
            })

        risks.sort(key=lambda x: x["attrition_risk"], reverse=True)
        return risks

    # ============================================================
    # PRE-POSITIONING (feeds into self-healing)
    # ============================================================

    def recommend_standby(self, target_date, shift_type="Day"):
        """
        Based on predictions, recommend pre-positioned standby workers.
        Feeds into self-healing: have someone ready BEFORE the callout.
        """
        risk_summary = self.get_daily_risk_summary(target_date)
        expected = risk_summary["expected_callouts"]

        standby_needed = max(0, round(expected))

        if standby_needed == 0:
            return {
                "date": target_date if isinstance(target_date, str) else target_date.strftime("%Y-%m-%d"),
                "standby_needed": 0,
                "recommendation": "No standby needed. Low callout risk.",
                "high_risk_employees": [],
            }

        return {
            "date": target_date if isinstance(target_date, str) else target_date.strftime("%Y-%m-%d"),
            "standby_needed": standby_needed,
            "expected_callouts": round(expected, 1),
            "high_risk_employees": [
                {"name": p["name"], "risk": p["risk_percentage"]}
                for p in risk_summary["high_risk_employees"]
            ],
            "recommendation": (
                f"Pre-position {standby_needed} standby worker(s) for {shift_type} shift. "
                f"{risk_summary['high_risk_count']} employees at elevated callout risk."
            ),
            "suggested_action": (
                "Send VET pre-offer to available workers: 'Standby shift available — "
                "may be needed, will confirm by shift start. Premium pay applies.'"
            ),
        }

    # ============================================================
    # PRIVATE: Risk Factor Calculations
    # ============================================================

    def _day_of_week_risk(self, emp_id, day_name):
        """How often does this person call out on this day of week?"""
        emp_absences = [a for a in self.absence_history if a["employee_id"] == emp_id]
        if not emp_absences:
            return 0
        dow_absences = [a for a in emp_absences if a.get("day_of_week") == day_name]
        if len(dow_absences) >= 3:
            return 0.9
        elif len(dow_absences) >= 2:
            return 0.5
        elif len(dow_absences) >= 1:
            return 0.2
        return 0

    def _count_dow_absences(self, emp_id, day_name):
        emp_absences = [a for a in self.absence_history if a["employee_id"] == emp_id]
        return len([a for a in emp_absences if a.get("day_of_week") == day_name])

    def _payday_proximity_risk(self, target_date):
        """Is this date the day after payday? (biweekly Friday)"""
        if target_date.weekday() == 5:  # Saturday after payday Friday
            return 0.4
        if target_date.weekday() == 0:  # Monday after payday weekend
            return 0.3
        return 0

    def _consecutive_days_risk(self, emp_id, target_date):
        """Risk based on how many consecutive days they'll have worked."""
        count = self._get_consecutive_count(emp_id, target_date)
        if count >= 5:
            return 0.7
        elif count >= 4:
            return 0.4
        elif count >= 3:
            return 0.2
        return 0

    def _get_consecutive_count(self, emp_id, target_date):
        """Count consecutive scheduled days leading up to target."""
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, "%Y-%m-%d")
        count = 0
        check_date = target_date - timedelta(days=1)
        for _ in range(7):
            date_str = check_date.strftime("%Y-%m-%d")
            scheduled = any(
                s.get("employee_id") == emp_id and s.get("date") == date_str
                for s in self.schedule_history
            )
            if scheduled:
                count += 1
                check_date -= timedelta(days=1)
            else:
                break
        return count

    def _denied_pto_risk(self, emp_id, target_date):
        """Did this employee request this date off and get denied?"""
        target_str = target_date.strftime("%Y-%m-%d") if isinstance(target_date, datetime) else target_date
        denied = [
            r for r in self.request_history
            if r.get("employee_id") == emp_id
            and r.get("status") == "DENIED"
            and r.get("start_date", "") <= target_str <= r.get("end_date", "")
        ]
        return 0.8 if denied else 0

    def _holiday_adjacent_risk(self, target_date):
        """Is this date adjacent to a holiday?"""
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, "%Y-%m-%d")
        holidays = {"2026-07-04", "2026-09-07", "2026-11-26", "2026-12-25", "2026-01-01"}
        prev = (target_date - timedelta(days=1)).strftime("%Y-%m-%d")
        next_d = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")
        if prev in holidays or next_d in holidays:
            return 0.5
        return 0

    def _frequency_risk(self, emp_id):
        """Overall absence frequency risk."""
        count = self._count_recent_absences(emp_id)
        if count >= 5:
            return 0.8
        elif count >= 3:
            return 0.4
        elif count >= 2:
            return 0.2
        return 0

    def _count_recent_absences(self, emp_id):
        return len([a for a in self.absence_history if a["employee_id"] == emp_id])

    def _callout_recommendation(self, risk_level, factors):
        if risk_level == "HIGH":
            return "Pre-position standby coverage. Consider reaching out proactively."
        elif risk_level == "MEDIUM":
            return "Monitor. Have backup plan identified."
        return "Normal risk. No action needed."

    # ============================================================
    # PRIVATE: Burnout Factor Calculations
    # ============================================================

    def _undesirable_shift_load(self, emp_id):
        """Score 0-100 based on undesirable shift burden vs team average."""
        emp_shifts = [s for s in self.schedule_history if s.get("employee_id") == emp_id]
        if not emp_shifts:
            return 30  # baseline

        nights = sum(1 for s in emp_shifts if s.get("shift_type") == "Night" or s.get("shift_name") == "Night")
        weekends = sum(1 for s in emp_shifts if s.get("is_weekend"))
        total = len(emp_shifts)

        undesirable_pct = (nights + weekends) / max(1, total)
        return min(100, undesirable_pct * 150)  # scale up

    def _forced_ot_burden(self, emp_id):
        """Score based on forced (non-voluntary) overtime."""
        forced = len([s for s in self.schedule_history
                     if s.get("employee_id") == emp_id and s.get("is_met")])
        if forced >= 4:
            return 90
        elif forced >= 2:
            return 60
        elif forced >= 1:
            return 30
        return 0

    def _pto_denial_rate(self, emp_id):
        """Score based on how often PTO requests are denied."""
        requests = [r for r in self.request_history if r.get("employee_id") == emp_id]
        if not requests:
            return 0
        denied = len([r for r in requests if r.get("status") == "DENIED"])
        rate = denied / len(requests)
        return min(100, rate * 150)

    def _rest_deficit(self, emp_id):
        """Score based on lack of rest days."""
        count = self._get_consecutive_count(emp_id, datetime.now())
        if count >= 6:
            return 90
        elif count >= 5:
            return 60
        elif count >= 4:
            return 30
        return 0

    def _schedule_instability(self, emp_id):
        """Score based on schedule changes."""
        changes = self._count_schedule_changes(emp_id)
        return min(100, changes * 15)

    def _coverage_overload(self, emp_id):
        """Score based on being asked for coverage too often."""
        coverage_asks = len([s for s in self.schedule_history
                           if s.get("employee_id") == emp_id and s.get("is_vet")])
        if coverage_asks >= 5:
            return 80
        elif coverage_asks >= 3:
            return 50
        elif coverage_asks >= 1:
            return 20
        return 0

    def _burnout_intervention(self, level, signals):
        if level == "HIGH":
            top = max(signals, key=signals.get)
            interventions = {
                "undesirable_shifts": "Rotate to preferred shifts for next 2 weeks",
                "forced_overtime": "Exempt from MET for next period. Offer voluntary only.",
                "pto_denied": "Approve their next PTO request if at all possible",
                "rest_deficit": "Ensure 2 consecutive days off this week",
                "schedule_instability": "Lock their schedule — no changes for 2 weeks",
                "coverage_overload": "Remove from coverage rotation for 2 weeks",
            }
            return interventions.get(top, "Manager 1:1 conversation recommended")
        elif level == "MEDIUM":
            return "Monitor closely. Ensure preferences are being honored."
        return "No intervention needed."

    # ============================================================
    # PRIVATE: Stability & Attrition
    # ============================================================

    def _count_schedule_changes(self, emp_id):
        """Count schedule changes for this employee."""
        return len([s for s in self.schedule_history
                   if s.get("employee_id") == emp_id and s.get("redistributed")])

    def _shift_time_consistency(self, emp_id):
        """How consistent are their shift start times?"""
        shifts = [s for s in self.schedule_history if s.get("employee_id") == emp_id]
        if not shifts:
            return 80
        start_times = set(s.get("start", s.get("start_time", "")) for s in shifts)
        if len(start_times) <= 1:
            return 100  # always same start time
        elif len(start_times) <= 2:
            return 80
        else:
            return 50  # lots of different start times

    def _day_off_predictability(self, emp_id):
        """How predictable are their days off?"""
        # Fixed shift codes = 100% predictable
        emp = next((e for e in self.employees if e["id"] == emp_id), {})
        if emp.get("shift_code"):
            return 95
        return 60  # variable schedule

    def _preference_mismatch(self, emp_id):
        """Score based on how far actual schedule is from preferences."""
        emp = next((e for e in self.employees if e["id"] == emp_id), {})
        prefs = emp.get("preferences", {})
        if not prefs:
            return 20  # no preferences set = low mismatch (they haven't complained)

        mismatch = 0
        preferred_type = prefs.get("preferred_shift_type")
        if preferred_type:
            actual_shifts = [s for s in self.schedule_history if s.get("employee_id") == emp_id]
            if actual_shifts:
                wrong_type = sum(1 for s in actual_shifts
                               if s.get("shift_name", "").lower() != preferred_type)
                mismatch += (wrong_type / max(1, len(actual_shifts))) * 50

        no_work_days = prefs.get("no_work_days", [])
        if no_work_days:
            violations = sum(1 for s in self.schedule_history
                           if s.get("employee_id") == emp_id
                           and s.get("day_of_week", "")[:3] in no_work_days)
            mismatch += min(50, violations * 10)

        return min(100, mismatch)

    def _attrition_drivers(self, burnout, stability, tenure_risk):
        drivers = []
        if burnout.get("burnout_score", 0) >= 60:
            drivers.append(f"High burnout ({burnout['burnout_score']}/100) — top driver: {burnout.get('top_driver', '?')}")
        if stability.get("stability_score", 100) < 70:
            drivers.append(f"Low schedule stability ({stability.get('stability_score')}%)")
        if tenure_risk > 15:
            drivers.append("New employee (<12 months) — critical retention window")
        if not drivers:
            drivers.append("No significant risk drivers")
        return drivers

    def _retention_recommendation(self, level, burnout, stability, emp):
        if level == "HIGH":
            return (
                f"URGENT: {emp['name']} at high attrition risk. "
                f"Recommend: manager 1:1 within 48h, review schedule preferences, "
                f"consider shift change or role rotation."
            )
        elif level == "MEDIUM":
            return f"Monitor {emp['name']}. Ensure schedule preferences are honored."
        return "No action needed."


# ============================================================
# DEMO
# ============================================================

def create_demo_predictive():
    """Create a demo predictive engine with sample history."""
    from sample_schedule import EMPLOYEES, generate_schedule

    schedule = generate_schedule()

    # Simulated absence history (90 days)
    absence_history = [
        # Marcus calls out on Mondays
        {"employee_id": "E004", "date": "2026-04-06", "day_of_week": "Mon", "type": "SICK_UNPLANNED"},
        {"employee_id": "E004", "date": "2026-04-20", "day_of_week": "Mon", "type": "SICK_UNPLANNED"},
        {"employee_id": "E004", "date": "2026-05-04", "day_of_week": "Mon", "type": "SICK_UNPLANNED"},
        {"employee_id": "E004", "date": "2026-06-01", "day_of_week": "Mon", "type": "SICK_UNPLANNED"},
        # Jake calls out Fridays (payday pattern)
        {"employee_id": "E010", "date": "2026-05-01", "day_of_week": "Fri", "type": "SICK_UNPLANNED"},
        {"employee_id": "E010", "date": "2026-05-15", "day_of_week": "Fri", "type": "SICK_UNPLANNED"},
        {"employee_id": "E010", "date": "2026-06-12", "day_of_week": "Fri", "type": "SICK_UNPLANNED"},
        # Sarah occasional
        {"employee_id": "E001", "date": "2026-05-20", "day_of_week": "Wed", "type": "SICK_UNPLANNED"},
    ]

    # Request history (some denied)
    request_history = [
        {"employee_id": "E005", "status": "DENIED", "start_date": "2026-07-07", "end_date": "2026-07-11"},
        {"employee_id": "E002", "status": "APPROVED", "start_date": "2026-06-15", "end_date": "2026-06-19"},
    ]

    engine = PredictiveEngine(
        employees=EMPLOYEES,
        absence_history=absence_history,
        schedule_history=schedule["shifts"],
        request_history=request_history,
    )
    return engine


if __name__ == "__main__":
    engine = create_demo_predictive()

    print("=" * 70)
    print("  PREDICTIVE ABSENTEEISM & WORKER WELLNESS")
    print("=" * 70)

    # Predict callouts for Monday July 6
    print("\n  CALLOUT PREDICTIONS - Monday July 6, 2026:")
    print("  " + "-" * 50)
    predictions = engine.predict_callouts("2026-07-06")
    for p in predictions[:5]:
        if p["risk_level"] != "MINIMAL":
            print(f"  {p['name']:<20} Risk: {p['risk_percentage']:<5} ({p['risk_level']})")
            for f in p["factors"][:2]:
                print(f"    - {f['detail']}")

    # Daily summary
    print("\n\n  DAILY RISK SUMMARY:")
    summary = engine.get_daily_risk_summary("2026-07-06")
    print(f"  Expected callouts: {summary['expected_callouts']}")
    print(f"  High risk: {summary['high_risk_count']}")
    print(f"  Recommendation: {summary['recommendation']}")

    # Burnout scores
    print("\n\n  BURNOUT SCORES:")
    print(f"  {'Name':<20} {'Score':<7} {'Level':<8} {'Top Driver':<25} {'Intervention'}")
    print(f"  {'-'*85}")
    burnout = engine.calculate_burnout_scores()
    for b in burnout[:5]:
        print(f"  {b['name']:<20} {b['burnout_score']:<7} {b['burnout_level']:<8} "
              f"{b['top_driver']:<25} {b['intervention'][:30]}")

    # Attrition risk
    print("\n\n  ATTRITION RISK:")
    print(f"  {'Name':<20} {'Risk':<6} {'Level':<8} {'Tenure (mo)':<12} {'Top Driver'}")
    print(f"  {'-'*75}")
    risks = engine.calculate_attrition_risk()
    for r in risks[:5]:
        driver = r["drivers"][0][:35] if r["drivers"] else ""
        print(f"  {r['name']:<20} {r['attrition_risk']:<6} {r['risk_level']:<8} "
              f"{r['tenure_months']:<12} {driver}")

    # Standby recommendation
    print("\n\n  STANDBY RECOMMENDATION:")
    standby = engine.recommend_standby("2026-07-06")
    print(f"  {standby['recommendation']}")
    if standby.get("suggested_action"):
        print(f"  Action: {standby['suggested_action']}")
