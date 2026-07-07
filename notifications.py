"""
Workforce Compliance AI - Unified Notification System
Multi-channel notifications with delivery tracking, templates, preferences,
urgency levels, and retry logic.
"""

from datetime import datetime, timedelta
from collections import defaultdict


# Notification channels
CHANNELS = {
    "PUSH": {"name": "Push Notification", "speed": "instant", "cost": "free"},
    "SMS": {"name": "SMS / Text", "speed": "instant", "cost": "$0.01/msg"},
    "EMAIL": {"name": "Email", "speed": "minutes", "cost": "free"},
    "SLACK": {"name": "Slack", "speed": "instant", "cost": "free"},
    "TEAMS": {"name": "Microsoft Teams", "speed": "instant", "cost": "free"},
    "WHATSAPP": {"name": "WhatsApp", "speed": "instant", "cost": "$0.005/msg"},
    "IN_APP": {"name": "In-App Notification", "speed": "instant", "cost": "free"},
}

# Urgency levels determine channel selection and timing
URGENCY_LEVELS = {
    "CRITICAL": {
        "name": "Critical (immediate action required)",
        "channels": ["PUSH", "SMS", "IN_APP"],
        "retry_max": 3,
        "retry_interval_minutes": 5,
        "escalate_after_minutes": 15,
    },
    "HIGH": {
        "name": "High (respond within 30 minutes)",
        "channels": ["PUSH", "IN_APP"],
        "retry_max": 2,
        "retry_interval_minutes": 10,
        "escalate_after_minutes": 30,
    },
    "MEDIUM": {
        "name": "Medium (respond within shift)",
        "channels": ["IN_APP", "EMAIL"],
        "retry_max": 1,
        "retry_interval_minutes": 60,
        "escalate_after_minutes": 240,
    },
    "LOW": {
        "name": "Low (FYI / daily digest)",
        "channels": ["IN_APP"],
        "retry_max": 0,
        "batch": True,
        "batch_frequency": "daily",
    },
}

# Notification templates
TEMPLATES = {
    "VET_OFFER": {
        "title": "VET Available",
        "urgency": "CRITICAL",
        "body": "VET shift available: {date} {start}-{end} ({role}). Covering for {absent_name}. Tap to accept.",
        "actions": ["Accept", "Decline"],
        "expires_minutes": 30,
    },
    "VET_BROADCAST": {
        "title": "Open VET - First to Accept Wins",
        "urgency": "CRITICAL",
        "body": "OPEN VET: {date} {start}-{end} ({role}). First to accept gets the shift. Tap now!",
        "actions": ["Accept"],
        "expires_minutes": 15,
    },
    "REQUEST_APPROVED": {
        "title": "Request Approved",
        "urgency": "MEDIUM",
        "body": "Your {request_type} request for {dates} has been approved.",
        "actions": ["View Details"],
    },
    "REQUEST_DENIED": {
        "title": "Request Denied",
        "urgency": "MEDIUM",
        "body": "Your {request_type} request for {dates} was not approved. Reason: {reason}. Alternatives available.",
        "actions": ["View Alternatives", "Contact Manager"],
    },
    "SCHEDULE_PUBLISHED": {
        "title": "New Schedule Published",
        "urgency": "LOW",
        "body": "Schedule for {period} has been published. Tap to view your shifts.",
        "actions": ["View Schedule"],
    },
    "SHIFT_CHANGE": {
        "title": "Schedule Change",
        "urgency": "HIGH",
        "body": "Your shift on {date} has been updated: {old_shift} -> {new_shift}.",
        "actions": ["View Details", "Contact Manager"],
    },
    "SWAP_REQUEST": {
        "title": "Shift Swap Proposed",
        "urgency": "HIGH",
        "body": "{requester_name} wants to swap: their {requester_date} for your {target_date}. Accept?",
        "actions": ["Accept", "Decline"],
        "expires_minutes": 480,
    },
    "CALLOUT_MANAGER": {
        "title": "Callout Reported",
        "urgency": "HIGH",
        "body": "CALLOUT: {employee_name} for {date} {start}-{end}. Self-healing initiated. {candidates} candidates found.",
        "actions": ["View Status", "Override"],
    },
    "INCIDENT_RESOLVED": {
        "title": "Gap Filled",
        "urgency": "LOW",
        "body": "Coverage resolved: {date} {start}-{end} filled by {covered_by}. No action needed.",
        "actions": ["View Details"],
    },
    "BALANCE_WARNING": {
        "title": "Leave Balance Alert",
        "urgency": "MEDIUM",
        "body": "Your {balance_type} balance is low: {hours_remaining}h remaining. {at_risk_message}",
        "actions": ["View Balances"],
    },
    "FMLA_TRIGGER": {
        "title": "FMLA Notification Required",
        "urgency": "CRITICAL",
        "body": "LEGAL: {employee_name} absent 3+ days. FMLA eligibility notice must be sent within 5 business days.",
        "actions": ["Process FMLA", "View Details"],
    },
    "COMPLIANCE_VIOLATION": {
        "title": "Compliance Violation Detected",
        "urgency": "HIGH",
        "body": "{severity} violation: {rule_name} - {description}. Action required.",
        "actions": ["View Violation", "Fix Now"],
    },
    "BURNOUT_ALERT": {
        "title": "Worker Wellness Alert",
        "urgency": "MEDIUM",
        "body": "{employee_name} showing burnout signals (score: {score}/100). Top factor: {top_driver}. Recommended: {intervention}.",
        "actions": ["Schedule 1:1", "Adjust Schedule"],
    },
    "HOLIDAY_AUCTION_OPEN": {
        "title": "Holiday Preferences Open",
        "urgency": "MEDIUM",
        "body": "Holiday preference submission is now open for {year}. Submit your priorities by {deadline}.",
        "actions": ["Submit Preferences"],
    },
    "AUCTION_RESULTS": {
        "title": "Holiday Allocation Results",
        "urgency": "MEDIUM",
        "body": "Your holiday preferences have been processed. {granted_count} granted, {denied_count} denied. Tap to view.",
        "actions": ["View Results"],
    },
    "UPT_CRITICAL": {
        "title": "UPT Balance Critical",
        "urgency": "HIGH",
        "body": "Your UPT balance is {hours}h. At 0, employment review is triggered. Please ensure attendance.",
        "actions": ["View Balance", "Talk to HR"],
    },
}


class NotificationEngine:
    """Unified notification system with multi-channel delivery."""

    def __init__(self):
        self.queue = []
        self.sent = []
        self.preferences = {}  # employee_id -> channel preferences
        self.delivery_log = []

    def set_preferences(self, employee_id, preferences):
        """
        Set notification preferences for a user.
        preferences: {
            "preferred_channels": ["PUSH", "SMS"],
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "07:00",
            "digest_time": "08:00",
            "language": "en",
            "do_not_disturb": False,
        }
        """
        self.preferences[employee_id] = preferences

    def send(self, template_key, recipient_id, data=None, override_urgency=None):
        """
        Send a notification using a template.

        template_key: key from TEMPLATES dict
        recipient_id: employee_id or "MANAGER" or list of IDs
        data: dict of template variables to fill in
        """
        template = TEMPLATES.get(template_key)
        if not template:
            return {"error": f"Unknown template: {template_key}"}

        data = data or {}
        urgency = override_urgency or template["urgency"]
        urgency_config = URGENCY_LEVELS[urgency]

        # Render template
        title = template["title"]
        body = template["body"].format(**{k: data.get(k, f"[{k}]") for k in self._extract_vars(template["body"])})

        # Determine channels based on urgency + user preferences
        user_prefs = self.preferences.get(recipient_id, {})
        channels = user_prefs.get("preferred_channels", urgency_config["channels"])

        # Check quiet hours
        if self._is_quiet_hours(recipient_id) and urgency not in ("CRITICAL",):
            channels = ["IN_APP"]  # defer to in-app only during quiet hours

        # Handle batch/digest for LOW urgency
        if urgency_config.get("batch"):
            return self._queue_for_digest(recipient_id, title, body, template_key, data)

        # Create notification
        notification = {
            "id": f"NOTIF-{len(self.sent)+len(self.queue)+1:06d}",
            "template": template_key,
            "recipient_id": recipient_id,
            "title": title,
            "body": body,
            "urgency": urgency,
            "channels": channels,
            "actions": template.get("actions", []),
            "data": data,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "expires_at": (
                (datetime.now() + timedelta(minutes=template["expires_minutes"])).strftime("%Y-%m-%d %H:%M")
                if template.get("expires_minutes") else None
            ),
            "status": "SENT",
            "delivered_via": [],
            "read_at": None,
            "acted_on": None,
        }

        # Simulate delivery per channel
        for channel in channels:
            delivery = {
                "channel": channel,
                "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "DELIVERED",
                "cost": CHANNELS[channel]["cost"],
            }
            notification["delivered_via"].append(delivery)
            self.delivery_log.append({**delivery, "notification_id": notification["id"], "recipient": recipient_id})

        self.sent.append(notification)
        return notification

    def send_bulk(self, template_key, recipient_ids, data=None):
        """Send same notification to multiple recipients."""
        results = []
        for rid in recipient_ids:
            result = self.send(template_key, rid, data)
            results.append(result)
        return results

    def mark_read(self, notification_id, recipient_id):
        """Mark a notification as read."""
        notif = next((n for n in self.sent if n["id"] == notification_id), None)
        if notif:
            notif["read_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return {"status": "read"}
        return {"error": "Not found"}

    def mark_acted(self, notification_id, action):
        """Mark that user took an action on a notification."""
        notif = next((n for n in self.sent if n["id"] == notification_id), None)
        if notif:
            notif["acted_on"] = {
                "action": action,
                "at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            return {"status": "acted", "action": action}
        return {"error": "Not found"}

    def get_unread(self, recipient_id):
        """Get all unread notifications for a user."""
        return [
            n for n in self.sent
            if n["recipient_id"] == recipient_id and n["read_at"] is None
        ]

    def get_pending_actions(self, recipient_id):
        """Get notifications awaiting user action."""
        return [
            n for n in self.sent
            if n["recipient_id"] == recipient_id
            and n["acted_on"] is None
            and n.get("actions")
            and n["status"] == "SENT"
        ]

    def get_delivery_stats(self):
        """Get delivery statistics."""
        total = len(self.sent)
        by_channel = defaultdict(int)
        by_urgency = defaultdict(int)
        read_count = sum(1 for n in self.sent if n["read_at"])
        acted_count = sum(1 for n in self.sent if n["acted_on"])

        for n in self.sent:
            by_urgency[n["urgency"]] += 1
            for d in n["delivered_via"]:
                by_channel[d["channel"]] += 1

        return {
            "total_sent": total,
            "read": read_count,
            "read_rate": f"{read_count/max(1,total)*100:.0f}%",
            "acted": acted_count,
            "action_rate": f"{acted_count/max(1,total)*100:.0f}%",
            "by_channel": dict(by_channel),
            "by_urgency": dict(by_urgency),
        }

    # --- Private ---

    def _extract_vars(self, template_str):
        """Extract {variable} names from a template string."""
        import re
        return re.findall(r'\{(\w+)\}', template_str)

    def _is_quiet_hours(self, recipient_id):
        """Check if it's currently quiet hours for this user."""
        prefs = self.preferences.get(recipient_id, {})
        if not prefs.get("quiet_hours_start"):
            return False

        now = datetime.now().strftime("%H:%M")
        start = prefs["quiet_hours_start"]
        end = prefs["quiet_hours_end"]

        if start < end:
            return start <= now <= end
        else:  # overnight (e.g., 22:00 - 07:00)
            return now >= start or now <= end

    def _queue_for_digest(self, recipient_id, title, body, template_key, data):
        """Queue a low-urgency notification for daily digest."""
        item = {
            "id": f"DIGEST-{len(self.queue)+1:06d}",
            "recipient_id": recipient_id,
            "title": title,
            "body": body,
            "template": template_key,
            "queued_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "status": "QUEUED_FOR_DIGEST",
        }
        self.queue.append(item)
        return item


# ============================================================
# SMART NOTIFICATION GENERATOR
# Context-aware alerts based on schedule, fatigue, leave data
# ============================================================

NIGHT_SHIFT_TIPS = [
    "Nap for 90 minutes between 2-4 PM before your shift for peak alertness.",
    "Avoid caffeine within 6 hours of your planned post-shift sleep time.",
    "Wear sunglasses on the drive home to signal your brain it's bedtime.",
    "Keep your bedroom cool (65-68°F) and pitch dark for daytime sleep.",
    "Eat a light meal before your shift — heavy meals increase drowsiness at 3-4 AM.",
]

EARLY_SHIFT_TIPS = [
    "Set your alarm 15 minutes earlier than you think — rushing increases cortisol.",
    "Prepare your uniform and lunch tonight to save 20 minutes tomorrow.",
    "Avoid screens 1 hour before bed tonight for better sleep quality.",
    "Early start means lights out by 10 PM for 7+ hours of sleep.",
]

REST_PERIOD_TIPS = [
    "You have less than 10 hours between shifts. Prioritize sleep over everything else.",
    "Short turnaround ahead — skip the gym tonight and focus on recovery.",
    "Quick turnaround: set a hard bedtime alarm, not just a wake-up alarm.",
]

HYDRATION_TIPS = [
    "12-hour shift ahead — aim for 8+ glasses of water. Dehydration kills focus by hour 8.",
    "Long shift today. Pack extra snacks — your brain needs fuel at the 6-hour mark.",
]


class SmartNotificationGenerator:
    """
    Generates personalized, context-aware notifications for workers.
    Uses schedule + fatigue + leave + portal data to produce smart nudges.
    """

    def __init__(self, employees=None, shifts=None, leave_tracker=None, portal=None):
        self.employees = employees or []
        self.shifts = shifts or []
        self.leave_tracker = leave_tracker
        self.portal = portal

    def generate_worker_notifications(self, employee_id, reference_date=None):
        """Generate all smart notifications for a worker at this moment."""
        if reference_date is None:
            reference_date = datetime.now()
        if isinstance(reference_date, str):
            reference_date = datetime.strptime(reference_date, "%Y-%m-%d")

        notifications = []
        notifications.extend(self._shift_reminders(employee_id, reference_date))
        notifications.extend(self._fatigue_alerts(employee_id, reference_date))
        notifications.extend(self._ot_warnings(employee_id, reference_date))
        notifications.extend(self._pto_updates(employee_id, reference_date))
        notifications.extend(self._coverage_opportunities(employee_id, reference_date))
        notifications.extend(self._wellness_nudges(employee_id, reference_date))
        notifications.extend(self._team_updates(employee_id, reference_date))

        notifications.sort(key=lambda n: n["priority"])
        return notifications

    def generate_manager_notifications(self, reference_date=None):
        """Generate notifications for a manager about their team."""
        if reference_date is None:
            reference_date = datetime.now()
        if isinstance(reference_date, str):
            reference_date = datetime.strptime(reference_date, "%Y-%m-%d")

        notifications = []
        tomorrow_str = (reference_date + timedelta(days=1)).strftime("%Y-%m-%d")

        # Team fatigue risks
        red_workers = []
        yellow_workers = []
        for emp in self.employees:
            emp_id = emp.get("id", emp.get("employee_id"))
            emp_shifts = [s for s in self.shifts if s.get("employee_id") == emp_id]
            weekly_hours = sum(self._shift_hours(s) for s in emp_shifts)

            if weekly_hours > 50:
                red_workers.append(emp["name"])
            elif weekly_hours > 44:
                yellow_workers.append(emp["name"])

        if red_workers:
            notifications.append({
                "priority": 1,
                "priority_label": "URGENT",
                "category": "FATIGUE",
                "icon": "🔴",
                "title": f"Fatigue Risk: {len(red_workers)} worker(s) over 50h",
                "message": f"{', '.join(red_workers[:3])}{'...' if len(red_workers) > 3 else ''} "
                           f"are in the danger zone. Consider reassignment or mandatory rest.",
                "action_label": "View Hours",
                "created_at": reference_date.strftime("%Y-%m-%d %H:%M"),
            })

        # OT cost alert
        ot_workers = [e["name"] for e in self.employees
                      if sum(self._shift_hours(s) for s in self.shifts
                             if s.get("employee_id") == e.get("id", e.get("employee_id"))) > 40]
        if ot_workers:
            est_cost = len(ot_workers) * 180
            notifications.append({
                "priority": 2,
                "priority_label": "HIGH",
                "category": "OT_COST",
                "icon": "💰",
                "title": f"OT Alert: {len(ot_workers)} in overtime (est. +${est_cost:,}/week)",
                "message": f"{', '.join(ot_workers[:4])} exceeded 40h. "
                           f"Redistribute remaining shifts to reduce OT spend.",
                "action_label": "Rebalance",
                "created_at": reference_date.strftime("%Y-%m-%d %H:%M"),
            })

        # Tomorrow's coverage
        if self.leave_tracker:
            on_leave = [
                r for r in self.leave_tracker.leave_records
                if r["start_date"] <= tomorrow_str <= r["end_date"]
                and r["status"] == "ACTIVE"
            ]
            if on_leave:
                names = [next((e["name"] for e in self.employees
                              if e.get("id", e.get("employee_id")) == r["employee_id"]),
                             r["employee_id"]) for r in on_leave[:4]]
                notifications.append({
                    "priority": 3,
                    "priority_label": "NORMAL",
                    "category": "COVERAGE",
                    "icon": "👥",
                    "title": f"Tomorrow: {len(on_leave)} off, verify coverage",
                    "message": f"{', '.join(names)} will be out. Check coverage is filled.",
                    "action_label": "Check Coverage",
                    "created_at": reference_date.strftime("%Y-%m-%d %H:%M"),
                })

        notifications.sort(key=lambda n: n["priority"])
        return notifications

    def _shift_reminders(self, employee_id, reference_date):
        """24-hour shift reminders with context-aware sleep/prep tips."""
        notifications = []
        tomorrow = reference_date + timedelta(days=1)
        tomorrow_str = tomorrow.strftime("%Y-%m-%d")
        today_str = reference_date.strftime("%Y-%m-%d")

        tomorrow_shifts = [
            s for s in self.shifts
            if s.get("employee_id") == employee_id and s.get("date") == tomorrow_str
        ]

        for shift in tomorrow_shifts:
            start_hour = int(shift.get("start", "08:00").split(":")[0])
            end_hour = int(shift.get("end", "16:00").split(":")[0])
            duration = self._shift_hours(shift)
            role = shift.get("role", "")

            # Night shift
            if start_hour >= 22 or start_hour <= 5:
                tip = NIGHT_SHIFT_TIPS[hash(employee_id + tomorrow_str) % len(NIGHT_SHIFT_TIPS)]
                notifications.append({
                    "priority": 2,
                    "priority_label": "HIGH",
                    "category": "SHIFT_REMINDER",
                    "icon": "🌙",
                    "title": f"Night shift in 24h — starts at {shift['start']}",
                    "message": f"You're on night shift tomorrow {shift['start']}-{shift['end']} "
                               f"({role}). Make sure to get enough sleep today. "
                               f"Tip: {tip}",
                    "action_label": "View Schedule",
                    "created_at": reference_date.strftime("%Y-%m-%d %H:%M"),
                })

            # Early morning
            elif start_hour <= 7:
                tip = EARLY_SHIFT_TIPS[hash(employee_id + tomorrow_str) % len(EARLY_SHIFT_TIPS)]
                notifications.append({
                    "priority": 3,
                    "priority_label": "NORMAL",
                    "category": "SHIFT_REMINDER",
                    "icon": "🌅",
                    "title": f"Early shift tomorrow at {shift['start']}",
                    "message": f"Tomorrow: {shift['start']}-{shift['end']} ({role}). "
                               f"Tip: {tip}",
                    "action_label": "View Schedule",
                    "created_at": reference_date.strftime("%Y-%m-%d %H:%M"),
                })

            # Long shift (12h+)
            elif duration >= 12:
                tip = HYDRATION_TIPS[hash(employee_id) % len(HYDRATION_TIPS)]
                notifications.append({
                    "priority": 3,
                    "priority_label": "NORMAL",
                    "category": "SHIFT_REMINDER",
                    "icon": "⏱️",
                    "title": f"{duration:.0f}h shift tomorrow ({shift['start']}-{shift['end']})",
                    "message": f"Long day ahead — {shift['start']} to {shift['end']} ({role}). "
                               f"Tip: {tip}",
                    "action_label": "View Schedule",
                    "created_at": reference_date.strftime("%Y-%m-%d %H:%M"),
                })

            # Standard shift
            else:
                notifications.append({
                    "priority": 4,
                    "priority_label": "LOW",
                    "category": "SHIFT_REMINDER",
                    "icon": "📋",
                    "title": f"Shift tomorrow: {shift['start']}-{shift['end']}",
                    "message": f"You're on at {shift['start']} tomorrow ({role}). Have a great shift!",
                    "action_label": None,
                    "created_at": reference_date.strftime("%Y-%m-%d %H:%M"),
                })

            # Short rest / clopening detection
            today_shifts = [
                s for s in self.shifts
                if s.get("employee_id") == employee_id and s.get("date") == today_str
            ]
            for today_shift in today_shifts:
                today_end = int(today_shift.get("end", "16:00").split(":")[0])
                if today_end >= 20 and start_hour <= 8:
                    rest_hours = (24 - today_end) + start_hour
                    if rest_hours < 11:
                        tip = REST_PERIOD_TIPS[hash(employee_id) % len(REST_PERIOD_TIPS)]
                        notifications.append({
                            "priority": 1,
                            "priority_label": "URGENT",
                            "category": "FATIGUE",
                            "icon": "⚠️",
                            "title": f"Short rest: only {rest_hours}h between shifts",
                            "message": f"You end at {today_shift['end']} tonight and start at "
                                       f"{shift['start']} tomorrow — only {rest_hours}h rest. "
                                       f"{tip}",
                            "action_label": "Request Swap",
                            "created_at": reference_date.strftime("%Y-%m-%d %H:%M"),
                        })

        return notifications

    def _fatigue_alerts(self, employee_id, reference_date):
        """Alerts based on cumulative fatigue."""
        notifications = []
        emp_shifts = [s for s in self.shifts if s.get("employee_id") == employee_id]
        weekly_hours = sum(self._shift_hours(s) for s in emp_shifts)

        # Count consecutive days
        dates = sorted(set(s.get("date", "") for s in emp_shifts))
        consec = 0
        for i in range(len(dates) - 1, -1, -1):
            try:
                d = datetime.strptime(dates[i], "%Y-%m-%d")
                expected = reference_date - timedelta(days=len(dates) - 1 - i)
                if d.date() == expected.date():
                    consec += 1
                else:
                    break
            except (ValueError, TypeError):
                break

        if weekly_hours > 50:
            notifications.append({
                "priority": 1,
                "priority_label": "URGENT",
                "category": "FATIGUE",
                "icon": "🔴",
                "title": f"High fatigue: {weekly_hours:.0f}h this week",
                "message": f"You've worked {weekly_hours:.0f}h this week — well above safe limits. "
                           f"Performance drops 25% at this level. Consider requesting time off "
                           f"or declining extra shifts.",
                "action_label": "Request Day Off",
                "created_at": reference_date.strftime("%Y-%m-%d %H:%M"),
            })
        elif weekly_hours > 44:
            notifications.append({
                "priority": 3,
                "priority_label": "NORMAL",
                "category": "FATIGUE",
                "icon": "🟡",
                "title": f"Moderate fatigue: {weekly_hours:.0f}h this week",
                "message": f"At {weekly_hours:.0f}h, you're above standard (40h). "
                           f"Take your breaks, stay hydrated, and protect your off-days.",
                "action_label": None,
                "created_at": reference_date.strftime("%Y-%m-%d %H:%M"),
            })

        if consec >= 6:
            notifications.append({
                "priority": 1,
                "priority_label": "URGENT",
                "category": "WELLNESS",
                "icon": "😴",
                "title": f"{consec} consecutive days — rest is overdue",
                "message": f"You've worked {consec} days straight. Injury risk increases 37% "
                           f"after 6 consecutive days. Your next day off is critical.",
                "action_label": "View Schedule",
                "created_at": reference_date.strftime("%Y-%m-%d %H:%M"),
            })
        elif consec >= 5:
            notifications.append({
                "priority": 2,
                "priority_label": "HIGH",
                "category": "WELLNESS",
                "icon": "📊",
                "title": f"{consec} consecutive days worked",
                "message": f"Day {consec} in a row. Research shows focus drops significantly "
                           f"after 5 consecutive days. Make your upcoming day off count.",
                "action_label": None,
                "created_at": reference_date.strftime("%Y-%m-%d %H:%M"),
            })

        return notifications

    def _ot_warnings(self, employee_id, reference_date):
        """Overtime proximity and cap warnings."""
        notifications = []
        emp_shifts = [s for s in self.shifts if s.get("employee_id") == employee_id]
        weekly_hours = sum(self._shift_hours(s) for s in emp_shifts)
        remaining_before_ot = max(0, 40 - weekly_hours)

        if weekly_hours > 40:
            ot_hours = weekly_hours - 40
            notifications.append({
                "priority": 3,
                "priority_label": "NORMAL",
                "category": "OT",
                "icon": "💰",
                "title": f"In overtime: {ot_hours:.1f}h OT this week",
                "message": f"You're at {weekly_hours:.0f}h ({ot_hours:.1f}h overtime at 1.5x pay). "
                           f"This is tracked for fairness across the team.",
                "action_label": None,
                "created_at": reference_date.strftime("%Y-%m-%d %H:%M"),
            })
        elif remaining_before_ot <= 4:
            notifications.append({
                "priority": 3,
                "priority_label": "NORMAL",
                "category": "OT",
                "icon": "⏱️",
                "title": f"Only {remaining_before_ot:.1f}h before overtime",
                "message": f"At {weekly_hours:.0f}h this week, you're {remaining_before_ot:.1f}h "
                           f"from the OT threshold. Next shift triggers overtime pay.",
                "action_label": None,
                "created_at": reference_date.strftime("%Y-%m-%d %H:%M"),
            })

        return notifications

    def _pto_updates(self, employee_id, reference_date):
        """PTO request results and balance warnings."""
        notifications = []

        if self.portal:
            for req in self.portal.requests:
                if req["employee_id"] == employee_id and req["type"] == "HOLIDAY":
                    if req["status"] == "AUTO_APPROVED":
                        notifications.append({
                            "priority": 4,
                            "priority_label": "LOW",
                            "category": "PTO",
                            "icon": "✅",
                            "title": f"PTO Approved: {req['start_date']} to {req['end_date']}",
                            "message": "Your request was auto-approved. Coverage is maintained. Enjoy!",
                            "action_label": None,
                            "created_at": reference_date.strftime("%Y-%m-%d %H:%M"),
                        })
                    elif req["status"] == "ESCALATED":
                        notifications.append({
                            "priority": 3,
                            "priority_label": "NORMAL",
                            "category": "PTO",
                            "icon": "⏳",
                            "title": f"PTO Pending: {req['start_date']} to {req['end_date']}",
                            "message": f"Your request is with your manager for review. "
                                       f"Reason: {req.get('auto_approval_result', {}).get('reason', 'needs coverage check')}.",
                            "action_label": "View Status",
                            "created_at": reference_date.strftime("%Y-%m-%d %H:%M"),
                        })

        if self.leave_tracker:
            bal = self.leave_tracker.get_balance_summary(employee_id)
            if bal:
                if bal.get("upt_hours", 20) <= 4:
                    notifications.append({
                        "priority": 1,
                        "priority_label": "URGENT",
                        "category": "BALANCE",
                        "icon": "🚨",
                        "title": f"UPT Critical: {bal['upt_hours']}h remaining",
                        "message": f"Your UPT is dangerously low. Zero balance = termination review. "
                                   f"Avoid unplanned absences until next quarterly grant.",
                        "action_label": "View Balances",
                        "created_at": reference_date.strftime("%Y-%m-%d %H:%M"),
                    })

                at_risk = bal.get("at_risk", {})
                if at_risk.get("pto_at_risk", 0) > 0:
                    notifications.append({
                        "priority": 3,
                        "priority_label": "NORMAL",
                        "category": "BALANCE",
                        "icon": "📅",
                        "title": f"Use-it-or-lose-it: {at_risk['pto_at_risk']}h at risk",
                        "message": f"{at_risk['pto_at_risk']}h PTO won't carry over past year-end. "
                                   f"{at_risk.get('days_until_year_end', '?')} days to use it.",
                        "action_label": "Request PTO",
                        "created_at": reference_date.strftime("%Y-%m-%d %H:%M"),
                    })

        return notifications

    def _coverage_opportunities(self, employee_id, reference_date):
        """VET offers and open shift notifications."""
        notifications = []

        if self.portal:
            my_vet = [
                o for o in self.portal.vet_offers
                if (o.get("offered_to") == employee_id or o.get("offered_to_all"))
                and o.get("status") == "PENDING"
            ]
            for offer in my_vet:
                details = offer.get("shift_details", {})
                notifications.append({
                    "priority": 2,
                    "priority_label": "HIGH",
                    "category": "VET",
                    "icon": "💵",
                    "title": f"VET: {details.get('date', '')} {details.get('start', '')}-{details.get('end', '')}",
                    "message": f"Premium pay shift available ({details.get('department', '')}). "
                               f"First to accept gets it!",
                    "action_label": "Accept",
                    "created_at": reference_date.strftime("%Y-%m-%d %H:%M"),
                })

            open_count = len([s for s in self.portal.open_shifts if not s.get("taken_by")])
            if open_count:
                notifications.append({
                    "priority": 4,
                    "priority_label": "LOW",
                    "category": "OPEN_SHIFT",
                    "icon": "📢",
                    "title": f"{open_count} open shift(s) available",
                    "message": "Pick up extra hours if you want them. First come, first served.",
                    "action_label": "Browse",
                    "created_at": reference_date.strftime("%Y-%m-%d %H:%M"),
                })

        return notifications

    def _wellness_nudges(self, employee_id, reference_date):
        """Proactive wellness based on schedule patterns."""
        notifications = []
        emp_shifts = sorted(
            [s for s in self.shifts if s.get("employee_id") == employee_id],
            key=lambda s: s.get("date", "")
        )

        # Detect clopening pattern
        for i in range(len(emp_shifts) - 1):
            curr = emp_shifts[i]
            nxt = emp_shifts[i + 1]
            try:
                d1 = datetime.strptime(curr.get("date", ""), "%Y-%m-%d")
                d2 = datetime.strptime(nxt.get("date", ""), "%Y-%m-%d")
                if (d2 - d1).days != 1:
                    continue
                curr_end = int(curr.get("end", "16:00").split(":")[0])
                nxt_start = int(nxt.get("start", "08:00").split(":")[0])
                if curr_end >= 22 and nxt_start <= 7 and d2.date() >= reference_date.date():
                    rest = (24 - curr_end) + nxt_start
                    notifications.append({
                        "priority": 2,
                        "priority_label": "HIGH",
                        "category": "WELLNESS",
                        "icon": "😴",
                        "title": f"Clopening alert: {rest}h between shifts",
                        "message": f"Close at {curr['end']} ({curr['date']}) then open at "
                                   f"{nxt['start']} ({nxt['date']}). Get to bed immediately "
                                   f"after your shift. Every minute of sleep counts.",
                        "action_label": "Request Swap",
                        "created_at": reference_date.strftime("%Y-%m-%d %H:%M"),
                    })
                    break
            except (ValueError, TypeError):
                continue

        return notifications

    def _team_updates(self, employee_id, reference_date):
        """Relevant team info (who's off tomorrow, etc.)."""
        notifications = []
        tomorrow_str = (reference_date + timedelta(days=1)).strftime("%Y-%m-%d")

        if self.leave_tracker:
            on_leave = [
                r for r in self.leave_tracker.leave_records
                if r["start_date"] <= tomorrow_str <= r["end_date"]
                and r["status"] == "ACTIVE"
                and r["employee_id"] != employee_id
            ]
            if on_leave:
                names = [next((e["name"] for e in self.employees
                              if e.get("id", e.get("employee_id")) == r["employee_id"]),
                             r["employee_id"]) for r in on_leave[:3]]
                notifications.append({
                    "priority": 4,
                    "priority_label": "LOW",
                    "category": "TEAM",
                    "icon": "👥",
                    "title": f"{len(on_leave)} teammate(s) off tomorrow",
                    "message": f"{', '.join(names)} out tomorrow. Team may be lean.",
                    "action_label": None,
                    "created_at": reference_date.strftime("%Y-%m-%d %H:%M"),
                })

        return notifications

    def _shift_hours(self, shift):
        """Calculate hours from a shift dict."""
        try:
            start_parts = shift.get("start", "08:00").split(":")
            end_parts = shift.get("end", "16:00").split(":")
            start_h = int(start_parts[0]) + int(start_parts[1]) / 60
            end_h = int(end_parts[0]) + int(end_parts[1]) / 60
            if end_h <= start_h:
                end_h += 24
            return end_h - start_h
        except (ValueError, IndexError):
            return 8


def create_demo_smart_notifications(employees, shifts, leave_tracker=None, portal=None):
    """Create a SmartNotificationGenerator with the demo data."""
    return SmartNotificationGenerator(
        employees=employees,
        shifts=shifts,
        leave_tracker=leave_tracker,
        portal=portal,
    )


# ============================================================
# DEMO
# ============================================================

if __name__ == "__main__":
    engine = NotificationEngine()

    # Set user preferences
    engine.set_preferences("E001", {
        "preferred_channels": ["PUSH", "SMS"],
        "quiet_hours_start": "22:00",
        "quiet_hours_end": "07:00",
        "language": "en",
    })
    engine.set_preferences("E008", {
        "preferred_channels": ["PUSH", "WHATSAPP"],
        "quiet_hours_start": "23:00",
        "quiet_hours_end": "08:00",
        "language": "en",
    })
    engine.set_preferences("MGR01", {
        "preferred_channels": ["PUSH", "SLACK", "EMAIL"],
        "language": "en",
    })

    print("=" * 70)
    print("  NOTIFICATION SYSTEM")
    print("=" * 70)

    # Send VET offer
    print("\n  Sending VET offer to David Kim...")
    n1 = engine.send("VET_OFFER", "E008", {
        "date": "2026-07-09", "start": "07:00", "end": "17:30",
        "role": "Pick", "absent_name": "Sarah Martinez",
    })
    print(f"  ID: {n1['id']}")
    print(f"  Channels: {[d['channel'] for d in n1['delivered_via']]}")
    print(f"  Expires: {n1['expires_at']}")

    # Send callout alert to manager
    print("\n  Sending callout alert to manager...")
    n2 = engine.send("CALLOUT_MANAGER", "MGR01", {
        "employee_name": "Sarah Martinez", "date": "2026-07-09",
        "start": "07:00", "end": "17:30", "candidates": "7",
    })
    print(f"  ID: {n2['id']}")
    print(f"  Channels: {[d['channel'] for d in n2['delivered_via']]}")

    # Send balance warning
    print("\n  Sending balance warning to Jake...")
    n3 = engine.send("BALANCE_WARNING", "E010", {
        "balance_type": "UPT", "hours_remaining": "4",
        "at_risk_message": "At 0 hours, employment review is triggered.",
    })
    print(f"  ID: {n3['id']}")

    # Send schedule published (LOW - goes to digest)
    print("\n  Sending schedule published (LOW urgency - digest)...")
    n4 = engine.send("SCHEDULE_PUBLISHED", "E001", {
        "period": "July 7-13, 2026",
    })
    print(f"  Status: {n4['status']}")

    # Broadcast VET
    print("\n  Broadcasting VET to all...")
    results = engine.send_bulk("VET_BROADCAST", ["E003", "E005", "E008", "E010"], {
        "date": "2026-07-09", "start": "07:00", "end": "17:30", "role": "Pick",
    })
    print(f"  Sent to {len(results)} recipients")

    # Stats
    print("\n\n  DELIVERY STATS:")
    stats = engine.get_delivery_stats()
    print(f"  Total sent: {stats['total_sent']}")
    print(f"  By channel: {stats['by_channel']}")
    print(f"  By urgency: {stats['by_urgency']}")

    # Show available templates
    print(f"\n\n  AVAILABLE TEMPLATES ({len(TEMPLATES)}):")
    for key, t in TEMPLATES.items():
        print(f"  {key:<25} [{t['urgency']:<8}] {t['title']}")
