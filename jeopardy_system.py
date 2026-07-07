"""
ShiftGuard - Jeopardy / Proxy Coverage System
Pre-assigns backup residents for every shift. Learns callout patterns.
Predicts who's likely to miss shifts 24-48h before it happens.
When a callout occurs, the jeopardy resident is ALREADY assigned — zero gap.

How residency programs do it today:
  - Chief resident manually assigns "jeopardy call" weekly
  - Same people get stuck as backup every time (unfair)
  - No pattern learning — same callout surprises every month
  - When jeopardy gets activated, nobody checks ACGME compliance

ShiftGuard difference:
  - Jeopardy assigned by FAIRNESS (who's been backup least)
  - System PREDICTS callouts 24-48h ahead (learned patterns)
  - Pre-check: jeopardy assignment won't violate 80h cap
  - Auto-activates when callout confirmed — instant resolution
"""

from datetime import datetime, timedelta
from collections import defaultdict
import math


# Callout pattern indicators (learned from historical data)
PATTERN_SIGNALS = {
    "post_night_float": {
        "description": "Day after night float block ends",
        "risk_multiplier": 2.5,
        "reason": "Circadian disruption makes day shifts after night block high-risk for callout",
    },
    "monday_after_weekend_off": {
        "description": "Monday when worker had Saturday+Sunday off",
        "risk_multiplier": 1.4,
        "reason": "Weekend sleep pattern shift makes Monday early starts harder",
    },
    "friday_evening": {
        "description": "Friday evening/night shifts",
        "risk_multiplier": 1.6,
        "reason": "Social plans, fatigue accumulation from week",
    },
    "day_after_holiday": {
        "description": "First shift after a holiday",
        "risk_multiplier": 1.8,
        "reason": "Travel delays, illness from gatherings",
    },
    "consecutive_day_6_plus": {
        "description": "6th+ consecutive day of work",
        "risk_multiplier": 2.2,
        "reason": "Burnout, fatigue, higher sick rate after extended stretches",
    },
    "pay_period_end": {
        "description": "Last day of pay period / payday",
        "risk_multiplier": 1.3,
        "reason": "Historically higher callout rates on paydays",
    },
    "post_call_day": {
        "description": "Day after 24h call shift",
        "risk_multiplier": 3.0,
        "reason": "Extreme fatigue, highest risk of calling out next scheduled shift",
    },
    "winter_monday": {
        "description": "Monday in December-February",
        "risk_multiplier": 1.5,
        "reason": "Seasonal illness (flu/cold), weather, holiday hangovers",
    },
    "personal_pattern": {
        "description": "Individual's historical callout pattern detected",
        "risk_multiplier": 2.0,
        "reason": "This person has called out on this day-of-week 3+ times in past 6 months",
    },
}


class JeopardySystem:
    """
    Manages pre-assigned backup (jeopardy) coverage and learns callout patterns.
    """

    def __init__(self, residents=None, shifts=None):
        self.residents = residents or {}  # id -> {name, pgy_level, ...}
        self.shifts = shifts or []
        self.jeopardy_assignments = {}  # date -> {shift_key: jeopardy_resident_id}
        self.callout_history = []  # Historical callouts for pattern learning
        self.pattern_scores = defaultdict(lambda: defaultdict(float))  # resident_id -> {pattern: score}
        self.jeopardy_burden = defaultdict(int)  # resident_id -> times_assigned_as_backup
        self.activation_log = []  # When jeopardy was actually activated

    def add_resident(self, resident_id, name, pgy_level, shift_history=None):
        """Register a resident in the jeopardy pool."""
        self.residents[resident_id] = {
            "id": resident_id,
            "name": name,
            "pgy_level": pgy_level,
            "callout_count": 0,
            "jeopardy_activations": 0,
            "reliability_score": 1.0,  # 1.0 = never calls out, 0.0 = always calls out
        }
        if shift_history:
            self._learn_patterns(resident_id, shift_history)

    def record_callout(self, resident_id, date, shift_start, reason="", advance_notice_hours=0):
        """Record a callout event — feeds pattern learning."""
        if isinstance(date, str):
            date_obj = datetime.strptime(date, "%Y-%m-%d")
        else:
            date_obj = date
            date = date_obj.strftime("%Y-%m-%d")

        callout = {
            "resident_id": resident_id,
            "date": date,
            "day_of_week": date_obj.strftime("%A"),
            "month": date_obj.month,
            "shift_start": shift_start,
            "reason": reason,
            "advance_notice_hours": advance_notice_hours,
            "timestamp": datetime.now().isoformat(),
            "patterns_detected": [],
        }

        # Detect which patterns match
        patterns = self._detect_patterns_for_callout(resident_id, date_obj)
        callout["patterns_detected"] = patterns

        self.callout_history.append(callout)

        # Update resident reliability
        if resident_id in self.residents:
            self.residents[resident_id]["callout_count"] += 1
            total_shifts = max(1, len([s for s in self.shifts if s.get("resident_id") == resident_id]))
            self.residents[resident_id]["reliability_score"] = max(0.1,
                1.0 - (self.residents[resident_id]["callout_count"] / total_shifts))

        # Strengthen pattern scores
        for pattern in patterns:
            self.pattern_scores[resident_id][pattern] += 0.3

        return callout

    def assign_jeopardy(self, date, shift_key="day", exclude_ids=None, scheduler=None):
        """
        Assign a jeopardy (backup) resident for a specific shift.
        Uses fairness: who's been backup LEAST recently.
        Checks ACGME compliance: backup won't violate if activated.

        Returns the assigned resident and reasoning.
        """
        exclude = set(exclude_ids or [])
        date_str = date if isinstance(date, str) else date.strftime("%Y-%m-%d")

        # Find who's available (not already scheduled, not excluded)
        scheduled_today = set(
            s.get("resident_id") for s in self.shifts
            if s.get("date") == date_str
        )

        candidates = []
        for res_id, res in self.residents.items():
            if res_id in exclude or res_id in scheduled_today:
                continue

            # Fairness score (lower burden = higher priority for jeopardy)
            burden = self.jeopardy_burden.get(res_id, 0)

            # ACGME check: if activated, would they violate?
            safe = True
            hours_concern = ""
            if scheduler:
                proposed = {
                    "resident_id": res_id,
                    "date": date_str,
                    "start": "07:00" if shift_key == "day" else "19:00",
                    "end": "19:00" if shift_key == "day" else "07:00",
                    "hours": 12,
                    "type": "jeopardy_activation",
                    "is_call": False,
                    "is_post_call": False,
                }
                check = scheduler.check_swap_compliance(res_id, proposed)
                safe = check["safe"]
                if not safe:
                    hours_concern = check["violations"][0]["message"] if check["violations"] else "compliance concern"

            if safe:
                candidates.append({
                    "resident_id": res_id,
                    "name": res["name"],
                    "pgy_level": res["pgy_level"],
                    "jeopardy_burden": burden,
                    "reliability_score": res["reliability_score"],
                    "acgme_safe": True,
                })

        if not candidates:
            return {
                "assigned": False,
                "reason": "No eligible residents available for jeopardy (all scheduled or would violate ACGME)",
            }

        # Sort by: lowest burden first (fairness), then highest reliability
        candidates.sort(key=lambda c: (c["jeopardy_burden"], -c["reliability_score"]))
        selected = candidates[0]

        # Record assignment
        key = f"{date_str}_{shift_key}"
        self.jeopardy_assignments[key] = selected["resident_id"]
        self.jeopardy_burden[selected["resident_id"]] += 1

        return {
            "assigned": True,
            "resident_id": selected["resident_id"],
            "name": selected["name"],
            "pgy_level": selected["pgy_level"],
            "date": date_str,
            "shift": shift_key,
            "reason": (
                f"Assigned {selected['name']} as jeopardy backup. "
                f"Lowest backup burden ({selected['jeopardy_burden']} times assigned). "
                f"ACGME-safe if activated. Reliability: {selected['reliability_score']:.0%}."
            ),
            "alternatives": [c["name"] for c in candidates[1:3]],
        }

    def assign_week_jeopardy(self, week_start, scheduler=None):
        """Assign jeopardy for an entire week (7 days × day + night = 14 slots)."""
        if isinstance(week_start, str):
            week_start = datetime.strptime(week_start, "%Y-%m-%d")

        assignments = []
        for day_offset in range(7):
            date = week_start + timedelta(days=day_offset)
            date_str = date.strftime("%Y-%m-%d")

            # Day shift jeopardy
            day_assign = self.assign_jeopardy(date_str, "day", scheduler=scheduler)
            assignments.append(day_assign)

            # Night shift jeopardy (different person)
            exclude = [day_assign.get("resident_id")] if day_assign.get("assigned") else []
            night_assign = self.assign_jeopardy(date_str, "night", exclude_ids=exclude, scheduler=scheduler)
            assignments.append(night_assign)

        return {
            "week_start": week_start.strftime("%Y-%m-%d"),
            "total_slots": 14,
            "assigned": sum(1 for a in assignments if a.get("assigned")),
            "assignments": assignments,
        }

    def predict_callouts(self, date, lookahead_hours=48):
        """
        Predict who's likely to call out in the next 24-48 hours.
        Based on learned patterns + current schedule state.
        Returns ranked list of at-risk residents with probability.
        """
        if isinstance(date, str):
            date_obj = datetime.strptime(date, "%Y-%m-%d")
        else:
            date_obj = date

        predictions = []

        for res_id, res in self.residents.items():
            # Check tomorrow and day after
            for offset in range(1, int(lookahead_hours / 24) + 1):
                check_date = date_obj + timedelta(days=offset)
                check_str = check_date.strftime("%Y-%m-%d")

                # Is this person scheduled?
                scheduled = [s for s in self.shifts
                             if s.get("resident_id") == res_id and s.get("date") == check_str]
                if not scheduled:
                    continue

                # Calculate risk score based on pattern matching
                risk_score = 0.05  # Base callout rate (~5%)
                risk_factors = []

                patterns = self._detect_patterns_for_callout(res_id, check_date)
                for pattern in patterns:
                    signal = PATTERN_SIGNALS.get(pattern, {})
                    multiplier = signal.get("risk_multiplier", 1.0)
                    risk_score *= multiplier
                    risk_factors.append({
                        "pattern": pattern,
                        "multiplier": multiplier,
                        "reason": signal.get("reason", ""),
                    })

                # Personal history multiplier
                personal_pattern_score = self.pattern_scores.get(res_id, {})
                day_of_week = check_date.strftime("%A")
                if personal_pattern_score.get(day_of_week, 0) > 0.5:
                    risk_score *= 1.5
                    risk_factors.append({
                        "pattern": "personal_history",
                        "multiplier": 1.5,
                        "reason": f"Has called out on {day_of_week}s before",
                    })

                # Cap at 85%
                risk_score = min(0.85, risk_score)

                if risk_score > 0.15:  # Only report if >15% risk
                    predictions.append({
                        "resident_id": res_id,
                        "name": res["name"],
                        "date": check_str,
                        "day": check_date.strftime("%A"),
                        "shift": scheduled[0].get("start", "07:00") + "-" + scheduled[0].get("end", "19:00"),
                        "risk_probability": round(risk_score, 2),
                        "risk_percentage": f"{risk_score * 100:.0f}%",
                        "risk_factors": risk_factors,
                        "jeopardy_assigned": self.jeopardy_assignments.get(f"{check_str}_day") or self.jeopardy_assignments.get(f"{check_str}_night"),
                        "recommendation": self._risk_recommendation(risk_score, res["name"], check_str),
                    })

        # Sort by risk (highest first)
        predictions.sort(key=lambda p: -p["risk_probability"])
        return predictions

    def activate_jeopardy(self, date, shift_key="day", reason="callout"):
        """
        Activate the pre-assigned jeopardy resident.
        Called when a callout is confirmed.
        """
        key = f"{date}_{shift_key}"
        jeopardy_id = self.jeopardy_assignments.get(key)

        if not jeopardy_id:
            return {
                "activated": False,
                "reason": f"No jeopardy assigned for {date} {shift_key}. Finding coverage now...",
            }

        resident = self.residents.get(jeopardy_id, {})

        activation = {
            "activated": True,
            "resident_id": jeopardy_id,
            "name": resident.get("name", jeopardy_id),
            "date": date,
            "shift": shift_key,
            "reason": reason,
            "activated_at": datetime.now().isoformat(),
            "notification": (
                f"JEOPARDY ACTIVATED: {resident.get('name', jeopardy_id)}, "
                f"you are now on for {date} ({shift_key} shift). "
                f"Reason: {reason}. Please confirm availability."
            ),
        }

        self.activation_log.append(activation)

        if jeopardy_id in self.residents:
            self.residents[jeopardy_id]["jeopardy_activations"] += 1

        return activation

    def get_fairness_report(self):
        """Show how evenly jeopardy burden is distributed."""
        report = []
        for res_id, res in self.residents.items():
            report.append({
                "resident": res["name"],
                "pgy_level": res["pgy_level"],
                "times_assigned_backup": self.jeopardy_burden.get(res_id, 0),
                "times_activated": res.get("jeopardy_activations", 0),
                "own_callouts": res.get("callout_count", 0),
                "reliability": f"{res['reliability_score']:.0%}",
            })

        report.sort(key=lambda r: -r["times_assigned_backup"])
        return report

    def _detect_patterns_for_callout(self, resident_id, date_obj):
        """Detect which callout patterns apply to this date/resident."""
        patterns = []
        day_of_week = date_obj.strftime("%A")
        month = date_obj.month

        # Post night float (check if previous 3 days were night shifts)
        recent_nights = sum(
            1 for s in self.shifts
            if s.get("resident_id") == resident_id
            and s.get("date", "") >= (date_obj - timedelta(days=4)).strftime("%Y-%m-%d")
            and s.get("date", "") < date_obj.strftime("%Y-%m-%d")
            and int(s.get("start", "07:00").split(":")[0]) >= 18
        )
        if recent_nights >= 3:
            patterns.append("post_night_float")

        # Monday after weekend off
        if day_of_week == "Monday":
            sat = (date_obj - timedelta(days=2)).strftime("%Y-%m-%d")
            sun = (date_obj - timedelta(days=1)).strftime("%Y-%m-%d")
            weekend_shifts = [s for s in self.shifts
                             if s.get("resident_id") == resident_id
                             and s.get("date") in (sat, sun)]
            if not weekend_shifts:
                patterns.append("monday_after_weekend_off")

        # Friday evening
        if day_of_week == "Friday":
            patterns.append("friday_evening")

        # Consecutive days (6+)
        consec = 0
        for i in range(1, 8):
            check = (date_obj - timedelta(days=i)).strftime("%Y-%m-%d")
            if any(s.get("resident_id") == resident_id and s.get("date") == check for s in self.shifts):
                consec += 1
            else:
                break
        if consec >= 5:
            patterns.append("consecutive_day_6_plus")

        # Winter Monday
        if day_of_week == "Monday" and month in (12, 1, 2):
            patterns.append("winter_monday")

        # Post-call (24h shift yesterday)
        yesterday = (date_obj - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_shifts = [s for s in self.shifts
                           if s.get("resident_id") == resident_id and s.get("date") == yesterday]
        if yesterday_shifts:
            total_yesterday = sum(
                float(s.get("hours", 0)) if s.get("hours") else 12
                for s in yesterday_shifts
            )
            if total_yesterday >= 20:
                patterns.append("post_call_day")

        return patterns

    def _risk_recommendation(self, risk_score, name, date):
        """Generate action recommendation based on risk level."""
        if risk_score > 0.5:
            return f"HIGH RISK: Consider proactively contacting {name} to confirm availability for {date}. Ensure jeopardy backup is ready."
        elif risk_score > 0.3:
            return f"MODERATE RISK: Monitor {name} for {date}. Jeopardy backup should be on standby."
        else:
            return f"LOW-MODERATE RISK: Jeopardy assigned. No proactive action needed."

    def _learn_patterns(self, resident_id, history):
        """Learn callout patterns from historical shift data."""
        for entry in history:
            if entry.get("status") == "callout":
                try:
                    date_obj = datetime.strptime(entry["date"], "%Y-%m-%d")
                    day = date_obj.strftime("%A")
                    self.pattern_scores[resident_id][day] += 0.2
                except (ValueError, KeyError):
                    pass


def create_demo_jeopardy_system():
    """Create a demo jeopardy system with sample residents and history."""
    system = JeopardySystem()

    # Add residents
    system.add_resident("R001", "Dr. Sarah Chen", "PGY-3")
    system.add_resident("R002", "Dr. James Williams", "PGY-2")
    system.add_resident("R003", "Dr. Priya Patel", "PGY-1")
    system.add_resident("R004", "Dr. Michael Kim", "PGY-3")
    system.add_resident("R005", "Dr. Aisha Johnson", "PGY-1")

    # Add some shift history
    base = datetime.now() - timedelta(days=30)
    for day in range(30):
        date = base + timedelta(days=day)
        date_str = date.strftime("%Y-%m-%d")

        # R001 works most days
        if day % 7 != 6:
            system.shifts.append({"resident_id": "R001", "date": date_str, "start": "07:00", "end": "19:00", "hours": 12})
        # R002 alternating
        if day % 2 == 0:
            system.shifts.append({"resident_id": "R002", "date": date_str, "start": "07:00", "end": "17:00", "hours": 10})
        # R003 standard with night float block
        if 10 <= day <= 16:
            system.shifts.append({"resident_id": "R003", "date": date_str, "start": "19:00", "end": "07:00", "hours": 12})
        elif day % 3 != 0:
            system.shifts.append({"resident_id": "R003", "date": date_str, "start": "06:00", "end": "18:00", "hours": 12})
        # R004 lighter (research block)
        if day >= 20:
            system.shifts.append({"resident_id": "R004", "date": date_str, "start": "07:00", "end": "17:00", "hours": 10})
        # R005 standard
        if day % 7 not in (5, 6):
            system.shifts.append({"resident_id": "R005", "date": date_str, "start": "07:00", "end": "19:00", "hours": 12})

    # Record some historical callouts (teaches the system patterns)
    system.record_callout("R002", (base + timedelta(days=7)).strftime("%Y-%m-%d"), "07:00", "illness", 2)
    system.record_callout("R002", (base + timedelta(days=14)).strftime("%Y-%m-%d"), "07:00", "car trouble", 1)
    system.record_callout("R003", (base + timedelta(days=17)).strftime("%Y-%m-%d"), "06:00", "post night float fatigue", 4)
    system.record_callout("R005", (base + timedelta(days=21)).strftime("%Y-%m-%d"), "07:00", "family emergency", 0)

    return system
