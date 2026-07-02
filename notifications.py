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
