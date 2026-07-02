"""
Workforce Compliance AI - Real-Time Demand Sensing
Integrates live signals to dynamically adjust staffing needs.
Not just historical forecasting — reacting to RIGHT NOW.
"""

from datetime import datetime, timedelta
from collections import defaultdict
import math


# Signal source definitions
SIGNAL_SOURCES = {
    "patient_census": {"name": "Patient Census", "industry": "healthcare", "update_freq": "15min", "impact": "high"},
    "er_volume": {"name": "ER Walk-ins", "industry": "healthcare", "update_freq": "real-time", "impact": "high"},
    "order_volume": {"name": "Order Volume", "industry": "warehouse", "update_freq": "hourly", "impact": "high"},
    "pos_transactions": {"name": "POS Transactions", "industry": "retail", "update_freq": "real-time", "impact": "high"},
    "foot_traffic": {"name": "Foot Traffic (camera/sensor)", "industry": "retail", "update_freq": "15min", "impact": "medium"},
    "delivery_orders": {"name": "Delivery Orders Queue", "industry": "hospitality", "update_freq": "real-time", "impact": "high"},
    "reservations": {"name": "Reservations", "industry": "hospitality", "update_freq": "hourly", "impact": "medium"},
    "weather": {"name": "Weather Forecast", "industry": "all", "update_freq": "hourly", "impact": "medium"},
    "event_calendar": {"name": "Local Events", "industry": "all", "update_freq": "daily", "impact": "medium"},
    "production_schedule": {"name": "Production Schedule", "industry": "manufacturing", "update_freq": "shift", "impact": "high"},
}

# Staffing models per industry (headcount per demand unit)
STAFFING_MODELS = {
    "healthcare": {
        "base_ratio": {"RN": 4, "CNA": 6, "Tech": 8},  # patients per staff
        "surge_threshold_pct": 20,
        "critical_threshold_pct": 40,
    },
    "warehouse": {
        "base_ratio": {"Picker": 35, "Packer": 40, "Stower": 50},  # units per hour per person
        "surge_threshold_pct": 25,
        "critical_threshold_pct": 50,
    },
    "retail": {
        "base_ratio": {"Sales Associate": 15, "Cashier": 25},  # customers per hour per person
        "surge_threshold_pct": 30,
        "critical_threshold_pct": 50,
    },
    "hospitality": {
        "base_ratio": {"Server": 5, "Kitchen": 20, "Front Desk": 30},  # covers/guests per staff
        "surge_threshold_pct": 25,
        "critical_threshold_pct": 40,
    },
}


class DemandSensingEngine:
    """
    Real-time demand sensing and dynamic staffing adjustment.
    Ingests live signals and recommends immediate staffing changes.
    """

    def __init__(self, industry="warehouse", current_headcount=None, baseline_demand=None):
        self.industry = industry
        self.current_headcount = current_headcount or {}
        self.baseline_demand = baseline_demand or 100
        self.signals = []
        self.alerts = []
        self.adjustments_history = []

    def ingest_signal(self, source, value, timestamp=None):
        """
        Ingest a real-time signal.
        source: key from SIGNAL_SOURCES
        value: current reading (e.g., patient census = 45, order volume = 1200)
        """
        signal = {
            "source": source,
            "value": value,
            "timestamp": timestamp or datetime.now().strftime("%Y-%m-%d %H:%M"),
            "source_info": SIGNAL_SOURCES.get(source, {}),
        }
        self.signals.append(signal)
        return signal

    def analyze_demand(self):
        """
        Analyze current signals and determine demand level.
        Returns: demand level, staffing recommendation, urgency.
        """
        if not self.signals:
            return {
                "demand_level": "NORMAL",
                "demand_pct_vs_baseline": 100,
                "recommendation": "No signals ingested. Operating at baseline.",
                "urgency": "LOW",
            }

        # Get most recent signal per source
        latest = {}
        for s in self.signals:
            latest[s["source"]] = s

        # Calculate demand percentage vs baseline
        demand_values = [s["value"] for s in latest.values()]
        avg_demand = sum(demand_values) / len(demand_values) if demand_values else self.baseline_demand
        demand_pct = (avg_demand / max(1, self.baseline_demand)) * 100

        model = STAFFING_MODELS.get(self.industry, STAFFING_MODELS["warehouse"])
        surge_threshold = 100 + model["surge_threshold_pct"]
        critical_threshold = 100 + model["critical_threshold_pct"]

        if demand_pct >= critical_threshold:
            level = "CRITICAL"
            urgency = "CRITICAL"
        elif demand_pct >= surge_threshold:
            level = "SURGE"
            urgency = "HIGH"
        elif demand_pct >= 90:
            level = "NORMAL"
            urgency = "LOW"
        else:
            level = "LOW"
            urgency = "LOW"

        recommendation = self._generate_staffing_recommendation(level, demand_pct)

        result = {
            "demand_level": level,
            "demand_pct_vs_baseline": round(demand_pct, 1),
            "latest_signals": latest,
            "recommendation": recommendation,
            "urgency": urgency,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        # Generate alert if surge or critical
        if level in ("SURGE", "CRITICAL"):
            self.alerts.append({
                "type": f"DEMAND_{level}",
                "message": recommendation,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "demand_pct": demand_pct,
            })

        return result

    def calculate_staffing_needs(self, demand_value, role=None):
        """
        Calculate exact headcount needed for a given demand level.
        """
        model = STAFFING_MODELS.get(self.industry, STAFFING_MODELS["warehouse"])
        ratios = model["base_ratio"]

        needs = {}
        for r, ratio in ratios.items():
            if role and r != role:
                continue
            needed = math.ceil(demand_value / ratio)
            current = self.current_headcount.get(r, needed)
            gap = needed - current

            needs[r] = {
                "needed": needed,
                "current": current,
                "gap": gap,
                "status": "OVERSTAFFED" if gap < 0 else ("UNDERSTAFFED" if gap > 0 else "OPTIMAL"),
                "action": self._gap_action(gap, r),
            }

        return needs

    def simulate_demand_surge(self, surge_pct, duration_hours=4):
        """
        Simulate a demand surge and recommend response.
        e.g., "ER census up 30% for next 4 hours"
        """
        surge_demand = self.baseline_demand * (1 + surge_pct / 100)
        staffing_needs = self.calculate_staffing_needs(surge_demand)

        total_additional = sum(max(0, n["gap"]) for n in staffing_needs.values())

        response = {
            "surge_pct": surge_pct,
            "duration_hours": duration_hours,
            "baseline_demand": self.baseline_demand,
            "surge_demand": round(surge_demand, 1),
            "staffing_needs": staffing_needs,
            "total_additional_staff": total_additional,
            "response_plan": [],
        }

        if total_additional > 0:
            response["response_plan"] = [
                f"IMMEDIATE: Call in {total_additional} additional staff for next {duration_hours}h",
                "Check self-healing VET pool for available workers",
                "If VET insufficient, authorize overtime for current staff",
                f"Re-evaluate in {min(2, duration_hours)}h — adjust up/down based on trend",
            ]

            # Cost estimate
            avg_hourly = 25
            ot_premium = 1.5
            response["estimated_surge_cost"] = round(total_additional * duration_hours * avg_hourly * ot_premium, 0)
        else:
            response["response_plan"] = ["Current staffing is sufficient. Monitor trend."]
            response["estimated_surge_cost"] = 0

        return response

    def get_hourly_forecast(self, hours_ahead=8):
        """
        Generate hourly demand forecast for the next N hours.
        Uses signal trends + historical patterns.
        """
        now = datetime.now()
        forecast = []

        # Simple pattern: demand peaks mid-shift, lower at start/end
        hour_patterns = {
            6: 0.6, 7: 0.8, 8: 1.0, 9: 1.1, 10: 1.2, 11: 1.3,
            12: 1.2, 13: 1.1, 14: 1.0, 15: 0.9, 16: 0.85, 17: 0.8,
            18: 0.7, 19: 0.6, 20: 0.5, 21: 0.4, 22: 0.3, 23: 0.2,
            0: 0.15, 1: 0.1, 2: 0.1, 3: 0.1, 4: 0.15, 5: 0.4,
        }

        current_demand = self.signals[-1]["value"] if self.signals else self.baseline_demand

        for h in range(hours_ahead):
            forecast_time = now + timedelta(hours=h)
            hour = forecast_time.hour
            pattern_multiplier = hour_patterns.get(hour, 0.8)

            forecasted_demand = current_demand * pattern_multiplier
            staffing = self.calculate_staffing_needs(forecasted_demand)

            forecast.append({
                "time": forecast_time.strftime("%H:%M"),
                "hour": hour,
                "forecasted_demand": round(forecasted_demand, 1),
                "demand_vs_baseline": round(forecasted_demand / max(1, self.baseline_demand) * 100, 1),
                "staffing_needs": staffing,
                "status": "SURGE" if forecasted_demand > self.baseline_demand * 1.25 else (
                    "NORMAL" if forecasted_demand > self.baseline_demand * 0.75 else "LOW"
                ),
            })

        return forecast

    def get_dashboard(self):
        """Get real-time demand dashboard data."""
        analysis = self.analyze_demand()
        forecast = self.get_hourly_forecast(8)
        staffing = self.calculate_staffing_needs(
            self.signals[-1]["value"] if self.signals else self.baseline_demand
        )

        return {
            "current_demand": analysis,
            "forecast_8h": forecast,
            "current_staffing": staffing,
            "alerts": self.alerts[-5:],
            "signals_ingested": len(self.signals),
            "last_update": self.signals[-1]["timestamp"] if self.signals else "No data",
        }

    # --- Private ---

    def _generate_staffing_recommendation(self, level, demand_pct):
        if level == "CRITICAL":
            overage = demand_pct - 100
            return (
                f"CRITICAL: Demand at {demand_pct:.0f}% of baseline (+{overage:.0f}%). "
                f"Immediate additional staffing required. Activate all available VET + consider agency."
            )
        elif level == "SURGE":
            overage = demand_pct - 100
            return (
                f"SURGE: Demand at {demand_pct:.0f}% (+{overage:.0f}%). "
                f"Call in additional staff for next 2-4 hours. Check VET availability."
            )
        elif level == "LOW":
            under = 100 - demand_pct
            return (
                f"LOW demand ({demand_pct:.0f}% of baseline, -{under:.0f}%). "
                f"Consider offering VTO (Voluntary Time Off) to reduce labor cost."
            )
        return f"Normal demand ({demand_pct:.0f}% of baseline). Current staffing adequate."

    def _gap_action(self, gap, role):
        if gap > 2:
            return f"URGENT: Need {gap} more {role}(s) immediately"
        elif gap > 0:
            return f"Call in {gap} additional {role}(s)"
        elif gap < -2:
            return f"Overstaffed by {abs(gap)} — offer VTO"
        elif gap < 0:
            return f"Slightly overstaffed — monitor"
        return "Optimal staffing"


# ============================================================
# DEMO
# ============================================================

if __name__ == "__main__":
    # Healthcare scenario: ER demand sensing
    print("=" * 70)
    print("  REAL-TIME DEMAND SENSING")
    print("  Scenario: Hospital Emergency Department")
    print("=" * 70)

    engine = DemandSensingEngine(
        industry="healthcare",
        current_headcount={"RN": 8, "CNA": 5, "Tech": 3},
        baseline_demand=30,  # 30 patients normal census
    )

    # Simulate signals coming in
    print("\n  INGESTING LIVE SIGNALS:")
    engine.ingest_signal("patient_census", 30, "2026-07-09 14:00")
    print("  14:00 - Patient census: 30 (baseline)")

    engine.ingest_signal("patient_census", 35, "2026-07-09 14:15")
    print("  14:15 - Patient census: 35 (rising)")

    engine.ingest_signal("patient_census", 42, "2026-07-09 14:30")
    print("  14:30 - Patient census: 42 (SURGE!)")

    engine.ingest_signal("er_volume", 12, "2026-07-09 14:30")
    print("  14:30 - ER walk-ins this hour: 12 (2x normal)")

    # Analyze
    print("\n  DEMAND ANALYSIS:")
    analysis = engine.analyze_demand()
    print(f"  Level: {analysis['demand_level']}")
    print(f"  Demand vs baseline: {analysis['demand_pct_vs_baseline']}%")
    print(f"  Urgency: {analysis['urgency']}")
    print(f"  Recommendation: {analysis['recommendation']}")

    # Staffing needs
    print("\n  STAFFING NEEDS (at current demand):")
    needs = engine.calculate_staffing_needs(42)
    for role, info in needs.items():
        print(f"  {role:<8} Need: {info['needed']:<4} Have: {info['current']:<4} "
              f"Gap: {info['gap']:<4} Status: {info['status']}")
        if info['gap'] > 0:
            print(f"           -> {info['action']}")

    # Simulate surge
    print("\n  SURGE SIMULATION (30% increase for 4 hours):")
    surge = engine.simulate_demand_surge(30, duration_hours=4)
    print(f"  Surge demand: {surge['surge_demand']} patients (baseline: {surge['baseline_demand']})")
    print(f"  Additional staff needed: {surge['total_additional_staff']}")
    print(f"  Estimated surge cost: ${surge['estimated_surge_cost']}")
    print(f"  Response plan:")
    for step in surge["response_plan"]:
        print(f"    - {step}")

    # Forecast
    print("\n  8-HOUR FORECAST:")
    forecast = engine.get_hourly_forecast(8)
    print(f"  {'Time':<6} {'Demand':<10} {'vs Base':<10} {'Status'}")
    print(f"  {'-'*35}")
    for f in forecast:
        print(f"  {f['time']:<6} {f['forecasted_demand']:<10} {f['demand_vs_baseline']}%{'   ' if f['demand_vs_baseline']<100 else '  '} {f['status']}")
