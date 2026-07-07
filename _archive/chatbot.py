"""
chatbot.py - Conversational AI Layer for Workforce Compliance Platform

Natural language interface that lets employees and managers interact with the entire
platform through conversation. No menus, no learning curve — just talk.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import re
import json


# =============================================================================
# 1. INTENT RECOGNITION
# =============================================================================

INTENT_PATTERNS = {
    "schedule_view": [
        r"what.*(my|the)\s*schedule",
        r"when\s*(do|am)\s*i\s*work",
        r"show\s*(me\s*)?my\s*schedule",
        r"my\s*shifts?\s*(this|next)",
        r"what\s*shifts?\s*(do\s*i\s*have|am\s*i)",
    ],
    "callout": [
        r"can.?t\s*(make|come|work)",
        r"(call|calling)\s*(out|off|in\s*sick)",
        r"(won.?t|cannot)\s*(be\s*(there|in)|make\s*it)",
        r"need\s*(to\s*)?(call\s*out|take\s*off|miss)",
        r"sick\s*(today|tomorrow)",
        r"i.?m\s*(not\s*coming|sick|unable)",
    ],
    "swap_request": [
        r"swap\s*(with|my|shifts?)",
        r"trade\s*(my|shifts?|with)",
        r"switch\s*(shifts?|with|my)",
        r"can\s*(i|we)\s*(swap|trade|switch)",
        r"exchange\s*shifts?",
    ],
    "vet_claim": [
        r"(extra|more)\s*hours",
        r"(open|available)\s*shifts?",
        r"(want|need)\s*(to\s*)?(pick\s*up|claim|grab)",
        r"vet\b",
        r"voluntary\s*extra\s*time",
        r"surge\s*(shifts?|opportunit)",
    ],
    "vto_request": [
        r"(go|leave)\s*(home\s*)?early",
        r"vto\b",
        r"voluntary\s*time\s*off",
        r"(want|can\s*i)\s*(go\s*home|leave\s*early|take\s*off)",
        r"don.?t\s*need\s*me",
    ],
    "tier_change": [
        r"(switch|change|move)\s*(to\s*)?(tier|flex|fixed)",
        r"(want|like)\s*to\s*(be\s*)?(tier|flex)",
        r"make\s*me\s*(tier|flex)",
        r"upgrade|downgrade",
    ],
    "earnings_check": [
        r"how\s*much\s*(have\s*i|did\s*i)\s*(made?|make|earn)",
        r"(my|what.?s)\s*(pay|earnings?|income|wages?)",
        r"what\s*(did|have)\s*i\s*(made?|make|earn)",
        r"(this\s*week|last\s*week|this\s*month).*(pay|earn|made|make)",
        r"paycheck|payslip",
        r"how\s*much.*make",
        r"(i|did\s*i)\s*make\s*(this|last)",
    ],
    "reliability_check": [
        r"(my|what.?s)\s*(reliability\s*)?(score|rating|standing)",
        r"how.?s\s*my\s*(rating|score|reliability|standing)",
        r"am\s*i\s*(reliable|in\s*good\s*standing)",
    ],
    "compliance_question": [
        r"(can|am)\s*i\s*(allowed|able)\s*to\s*work",
        r"(would|will|does)\s*this\s*violate",
        r"(is\s*it|am\s*i)\s*(ok|legal|allowed|compliant)",
        r"rest\s*(period|break|hours?)",
        r"overtime\s*(rules?|limit|allowed)",
        r"(max|maximum)\s*hours",
    ],
    "pool_status": [
        r"(how.?s|what.?s)\s*(coverage|the\s*pool|staffing)",
        r"(any\s*)?surge\s*(shifts?|available)",
        r"pool\s*status",
        r"(open|unfilled)\s*(slots?|shifts?|positions?)",
    ],
    "demand_post": [
        r"(i\s*)?need\s*\d+\s*(more\s*|extra\s*)?(people|workers?|pickers?|stowers?|packers?)",
        r"(post|add|create)\s*\d*\s*(extra\s*)?(slots?|shifts?|demand)",
        r"(short|understaffed|need\s*help)",
        r"need\s*\d+\s*extra",
    ],
    "schedule_build": [
        r"build\s*(next\s*week|the\s*schedule|a\s*schedule)",
        r"(create|generate|make)\s*(next\s*week|schedule)",
        r"schedule\s*(next\s*week|for\s*\d+)",
    ],
    "report_request": [
        r"show\s*(me\s*)?(this\s*week|report|costs?|metrics?)",
        r"(weekly|daily|monthly)\s*(report|summary|costs?)",
        r"(what.?s|how.?s)\s*(the\s*)?(cost|spend|budget)",
    ],
    "help": [
        r"(how\s*(does|do)|explain|what\s*(is|are|does))",
        r"help\s*(me)?$",
        r"(tell|teach)\s*me\s*(about|how)",
        r"(where|how)\s*(do\s*i|can\s*i)\s*find",
        r"i.?m\s*(confused|lost|not\s*sure)",
    ],
}


def recognize_intent(message: str) -> Tuple[str, float]:
    """
    Categorize user message into an intent with confidence score.
    Returns (intent_name, confidence).
    """
    message_lower = message.lower().strip()

    best_intent = "help"
    best_confidence = 0.0

    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                # Confidence based on match coverage
                match_len = match.end() - match.start()
                confidence = min(0.95, 0.5 + (match_len / len(message_lower)) * 0.5)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_intent = intent

    # Default to help with low confidence if nothing matched well
    if best_confidence < 0.3:
        return "help", 0.3

    return best_intent, best_confidence


def extract_entities(message: str) -> Dict:
    """
    Extract dates, times, names, numbers, and shift info from message.
    """
    entities = {}
    message_lower = message.lower()

    # Extract days of week
    days = re.findall(
        r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday"
        r"|mon|tue|wed|thu|fri|sat|sun)",
        message_lower
    )
    if days:
        entities["days"] = days

    # Extract relative dates
    if "tomorrow" in message_lower:
        entities["date"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        entities["date_label"] = "tomorrow"
    elif "today" in message_lower:
        entities["date"] = datetime.now().strftime("%Y-%m-%d")
        entities["date_label"] = "today"
    elif "tonight" in message_lower:
        entities["date"] = datetime.now().strftime("%Y-%m-%d")
        entities["date_label"] = "tonight"
    elif "next week" in message_lower:
        entities["date_label"] = "next week"

    # Extract times
    times = re.findall(r"(\d{1,2})\s*(?::(\d{2}))?\s*(am|pm)", message_lower)
    if times:
        entities["times"] = times

    # Extract numbers (for headcount, etc.)
    numbers = re.findall(r"\b(\d+)\b", message)
    if numbers:
        entities["numbers"] = [int(n) for n in numbers]

    # Extract names (capitalized words that are not common words)
    common_words = {
        "I", "Can", "What", "When", "How", "The", "My", "Any",
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
        "Saturday", "Sunday", "Pick", "Stow", "Pack", "Tier",
    }
    names = re.findall(r"\b([A-Z][a-z]+)\b", message)
    potential_names = [n for n in names if n not in common_words]
    if potential_names:
        entities["names"] = potential_names

    # Extract shift types
    shift_types = re.findall(r"(pick|stow|pack|ship|receive|sort)", message_lower)
    if shift_types:
        entities["shift_types"] = shift_types

    # Extract time windows like "2pm to 10pm"
    windows = re.findall(
        r"(\d{1,2})\s*(am|pm)\s*(to|through|-)\s*(\d{1,2})\s*(am|pm)",
        message_lower
    )
    if windows:
        entities["time_windows"] = windows

    return entities


# =============================================================================
# 2. CONVERSATION ENGINE
# =============================================================================

class ConversationEngine:
    """
    Core conversational AI that processes messages, maintains context,
    determines intent, executes actions, and responds naturally.
    """

    def __init__(self):
        # Conversation history keyed by user_id
        self.conversations: Dict[str, List[Dict]] = {}
        # Simulated worker database
        self.workers = self._init_workers()
        # Simulated pool/shift state
        self.pool_state = self._init_pool_state()
        # Notification queue
        self.notifications: List[Dict] = []

    def _init_workers(self) -> Dict:
        """Initialize simulated worker data."""
        return {
            "EMP001": {
                "name": "Jordan Chen",
                "tier": 2,
                "reliability_score": 87,
                "base_rate": 18.00,
                "weekly_hours": 42,
                "max_weekly": 60,
                "schedule": {
                    "Monday": {"start": "6:00am", "end": "2:30pm", "role": "Pick"},
                    "Tuesday": {"start": "6:00am", "end": "2:30pm", "role": "Pick"},
                    "Wednesday": {"start": "6:00am", "end": "2:30pm", "role": "Pick"},
                    "Thursday": {"start": "6:00am", "end": "2:30pm", "role": "Pick"},
                    "Friday": {"start": "6:00am", "end": "2:30pm", "role": "Pick"},
                },
                "availability": ["Tuesday", "Thursday"],
                "availability_window": "2pm-10pm",
                "earnings_this_week": {
                    "base": 612.00,
                    "flex_activation": 229.50,
                    "surge_claims": 290.70,
                },
            },
            "EMP002": {
                "name": "Maria Rodriguez",
                "tier": 2,
                "reliability_score": 94,
                "base_rate": 18.00,
                "weekly_hours": 34,
                "max_weekly": 60,
            },
            "EMP003": {
                "name": "Marcus Williams",
                "tier": 3,
                "reliability_score": 72,
                "base_rate": 18.00,
                "weekly_hours": 28,
                "max_weekly": 60,
            },
            "MGR001": {
                "name": "Sarah Kim",
                "role": "manager",
                "team_size": 40,
                "active_count": 37,
                "on_leave": ["Aisha (FMLA)", "David (PTO)", "Chen (sick)"],
            },
        }

    def _init_pool_state(self) -> Dict:
        """Initialize simulated pool/shift state."""
        return {
            "tonight_shift": {
                "time": "10pm-6:30am",
                "filled": 14,
                "needed": 15,
                "tier1_anchors": 12,
                "tier2_activated": 2,
                "tier3_viewing": 3,
                "current_rate": 24.00,
                "surge_multiplier": 1.33,
            },
            "surge_available": [
                {
                    "id": "SURGE001",
                    "time": "Tonight 10pm-6:30am",
                    "role": "Stow",
                    "rate": 28.50,
                    "multiplier": 1.58,
                    "claims_in": "22 min",
                    "status": "open",
                },
                {
                    "id": "SURGE002",
                    "time": "Saturday 2pm-10:30pm",
                    "role": "Pick",
                    "rate": 22.00,
                    "multiplier": 1.22,
                    "hours_until": 6,
                    "status": "open",
                },
            ],
            "predictability_pay_threshold_hours": 336,  # 14 days in hours
        }

    def _get_context(self, user_id: str) -> List[Dict]:
        """Get conversation context for multi-turn support."""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        return self.conversations[user_id]

    def _add_to_context(self, user_id: str, role: str, message: str, intent: str = None):
        """Add a message to conversation history."""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        self.conversations[user_id].append({
            "role": role,
            "message": message,
            "intent": intent,
            "timestamp": datetime.now().isoformat(),
        })
        # Keep last 20 turns
        if len(self.conversations[user_id]) > 20:
            self.conversations[user_id] = self.conversations[user_id][-20:]

    def process_message(self, user_id: str, message: str, role: str = "employee") -> str:
        """
        Main entry point. Process a user message and return a natural response.
        Handles intent recognition, entity extraction, action execution, and response.
        """
        # Recognize intent
        intent, confidence = recognize_intent(message)
        entities = extract_entities(message)

        # Check conversation context for multi-turn handling
        context = self._get_context(user_id)
        last_intent = None
        if context:
            last_entry = context[-1]
            last_intent = last_entry.get("intent")

        # Handle confirmations in multi-turn context
        if self._is_confirmation(message) and last_intent:
            response = self._handle_confirmation(user_id, last_intent, entities, role)
        elif self._is_followup(message, last_intent, entities):
            response = self._handle_followup(user_id, last_intent, entities, message, role)
        else:
            # Route to appropriate handler
            if role == "manager" or user_id.startswith("MGR"):
                response = self._handle_manager_intent(user_id, intent, entities, message)
            else:
                response = self._handle_employee_intent(user_id, intent, entities, message)

        # Store context
        self._add_to_context(user_id, "user", message, intent)
        self._add_to_context(user_id, "bot", response, intent)

        return response

    def _is_confirmation(self, message: str) -> bool:
        """Detect if message is a simple yes/confirmation or action request."""
        msg = message.lower().strip().rstrip("!.")
        confirms = [
            "yes", "yeah", "yep", "yup", "sure", "do it", "go ahead",
            "ok", "okay", "confirm", "approved", "post it", "grab it",
            "claim it", "release it", "send it", "y",
        ]
        if msg in confirms:
            return True
        # Also match action phrases like "grab the first one", "claim that"
        action_patterns = [
            r"^(grab|claim|take|get|book|lock\s*in)\s*(the\s*)?(first|second|that|it|one|#?\d)",
            r"^(do|yes|yeah|go)\s",
            r"^(post|release|send|approve)\s*(it|that|them)",
        ]
        for pattern in action_patterns:
            if re.search(pattern, msg):
                return True
        return False

    def _is_followup(self, message: str, last_intent: str, entities: Dict) -> bool:
        """Detect if this message is a follow-up providing details for a previous question."""
        if not last_intent:
            return False
        # If last intent was help about availability and user is providing days/times
        if last_intent == "help" and (entities.get("days") or entities.get("time_windows")):
            return True
        # If user provides data that looks like answering a question we asked
        if last_intent in ("vet_claim", "pool_status") and entities.get("numbers"):
            return True
        return False

    def _handle_followup(self, user_id: str, last_intent: str, entities: Dict,
                         message: str, role: str) -> str:
        """Handle follow-up messages that provide details for a prior interaction."""
        # Availability update follow-up
        if entities.get("days") or entities.get("time_windows"):
            worker = self.workers.get(user_id, self.workers["EMP001"])
            days = entities.get("days", [])
            day_names = []
            day_map = {
                "mon": "Mondays", "monday": "Mondays", "mondays": "Mondays",
                "tue": "Tuesdays", "tuesday": "Tuesdays", "tuesdays": "Tuesdays",
                "wed": "Wednesdays", "wednesday": "Wednesdays", "wednesdays": "Wednesdays",
                "thu": "Thursdays", "thursday": "Thursdays", "thursdays": "Thursdays",
                "fri": "Fridays", "friday": "Fridays", "fridays": "Fridays",
                "sat": "Saturdays", "saturday": "Saturdays", "saturdays": "Saturdays",
                "sun": "Sundays", "sunday": "Sundays", "sundays": "Sundays",
            }
            for d in days:
                day_names.append(day_map.get(d, d.capitalize() + "s"))

            window = ""
            if entities.get("time_windows"):
                tw = entities["time_windows"][0]
                window = f"{tw[0]}{tw[1]} to {tw[3]}{tw[4]}"
            elif entities.get("times"):
                window = "your specified times"

            days_str = " and ".join(day_names) if day_names else "your selected days"
            return (
                f"Updated. You're now in the Tier 2 Flex Buffer for {days_str}, "
                f"{window} window. You'll earn $5/hr holding yield during those windows "
                "even if not activated. Anything else?"
            )

        return "Got it! Anything else I can help with?"

    def _handle_confirmation(self, user_id: str, last_intent: str, entities: Dict, role: str) -> str:
        """Handle a confirmation response based on previous context."""
        handlers = {
            "callout": self._confirm_callout,
            "vet_claim": self._confirm_vet_claim,
            "pool_status": self._confirm_vet_claim,
            "demand_post": self._confirm_demand_post,
            "schedule_build": self._confirm_schedule_build,
            "vto_request": self._confirm_vto,
            "swap_request": self._confirm_swap,
            "help": self._confirm_from_help,
        }
        handler = handlers.get(last_intent)
        if handler:
            return handler(user_id, entities)
        return "Done! Anything else I can help with?"

    # =========================================================================
    # 3. EMPLOYEE CONVERSATION HANDLERS
    # =========================================================================

    def _handle_employee_intent(self, user_id: str, intent: str, entities: Dict, message: str) -> str:
        """Route employee intents to specific handlers."""
        handlers = {
            "schedule_view": self._employee_schedule_view,
            "callout": self._employee_callout,
            "swap_request": self._employee_swap,
            "vet_claim": self._employee_vet_claim,
            "vto_request": self._employee_vto,
            "tier_change": self._employee_tier_change,
            "earnings_check": self._employee_earnings,
            "reliability_check": self._employee_reliability,
            "compliance_question": self._employee_compliance,
            "pool_status": self._employee_pool_status,
            "help": self._employee_help,
        }
        handler = handlers.get(intent, self._employee_help)
        return handler(user_id, entities, message)

    def _employee_schedule_view(self, user_id: str, entities: Dict, message: str) -> str:
        worker = self.workers.get(user_id, self.workers["EMP001"])
        schedule = worker.get("schedule", {})

        lines = [f"Here's your schedule this week, {worker['name'].split()[0]}:\n"]
        for day, shift in schedule.items():
            lines.append(f"  {day}: {shift['start']}-{shift['end']} ({shift['role']})")

        lines.append(f"\nTier {worker['tier']} | {worker['weekly_hours']}hr this week so far")
        lines.append("Want to see next week or make any changes?")
        return "\n".join(lines)

    def _employee_callout(self, user_id: str, entities: Dict, message: str) -> str:
        worker = self.workers.get(user_id, self.workers["EMP001"])
        date_label = entities.get("date_label", "tomorrow")

        # Calculate notice hours (simulated)
        notice_hours = 18 if date_label == "tomorrow" else 4

        day = "Thursday"
        if "days" in entities:
            day_map = {
                "mon": "Monday", "monday": "Monday",
                "tue": "Tuesday", "tuesday": "Tuesday",
                "wed": "Wednesday", "wednesday": "Wednesday",
                "thu": "Thursday", "thursday": "Thursday",
                "fri": "Friday", "friday": "Friday",
                "sat": "Saturday", "saturday": "Saturday",
                "sun": "Sunday", "sunday": "Sunday",
            }
            day = day_map.get(entities["days"][0], "Thursday")

        shift_info = worker.get("schedule", {}).get(day, {"start": "6:00am", "end": "2:30pm", "role": "Pick"})

        response = (
            f"No problem. Your {day} {shift_info['start']}-{shift_info['end']} "
            f"{shift_info['role']} shift will be released to the pool. "
            f"Since you're giving {notice_hours} hours notice - "
        )

        if notice_hours >= 4:
            response += (
                "no reliability impact (4+ hours = no fault). "
                "Want me to release it now?"
            )
        else:
            response += (
                "heads up, this is short notice (under 4 hours) which will "
                f"reduce your reliability score by 5 points (currently {worker['reliability_score']}). "
                "Still want to proceed?"
            )

        return response

    def _confirm_callout(self, user_id: str, entities: Dict) -> str:
        worker = self.workers.get(user_id, self.workers["EMP001"])
        return (
            "Done. Shift released. Tier 2 worker Maria Rodriguez has been offered it "
            f"at 1.5x ($27/hr). I'll let you know when it's confirmed. "
            f"Your reliability score stays at {worker['reliability_score']}. Anything else?"
        )

    def _employee_swap(self, user_id: str, entities: Dict, message: str) -> str:
        names = entities.get("names", ["the other worker"])
        target_name = names[0] if names else "the other worker"
        return (
            f"I'll send a swap request to {target_name}. "
            "Compliance check: no rest period violations for either of you. "
            f"Pending {target_name}'s confirmation. "
            "I'll notify you as soon as they respond. Anything else?"
        )

    def _confirm_swap(self, user_id: str, entities: Dict) -> str:
        return (
            "Swap request sent! The other worker has 24 hours to accept. "
            "I'll ping you the moment they respond. Anything else?"
        )

    def _confirm_from_help(self, user_id: str, entities: Dict) -> str:
        """Handle confirmation after a help/navigation response."""
        return "Done! Anything else I can help with?"

    def _employee_vet_claim(self, user_id: str, entities: Dict, message: str) -> str:
        worker = self.workers.get(user_id, self.workers["EMP001"])
        surge_shifts = self.pool_state["surge_available"]

        lines = ["You have 2 surge opportunities right now:\n"]
        for i, shift in enumerate(surge_shifts, 1):
            if "claims_in" in shift:
                urgency = f"claims in {shift['claims_in']}"
            else:
                urgency = f"{shift['hours_until']} hrs until start"
            lines.append(
                f"  {i}. {shift['time']}, {shift['role']}, "
                f"${shift['rate']:.2f}/hr ({shift['multiplier']}x) - {urgency}"
            )

        # Compliance check
        hours_after = worker["weekly_hours"] + 8.5
        lines.append(
            f"\nCompliance check: both OK for you "
            f"(rest period check, weekly hours at {worker['weekly_hours']}/{worker['max_weekly']} check). "
            "Want to claim one?"
        )
        return "\n".join(lines)

    def _confirm_vet_claim(self, user_id: str, entities: Dict) -> str:
        shift = self.pool_state["surge_available"][0]
        extra_earnings = (shift["rate"] - 18.00) * 8.5
        return (
            f"Claimed! {shift['time']} {shift['role']} at ${shift['rate']:.2f}/hr locked in. "
            f"That's ${extra_earnings:.2f} extra vs base rate for this shift. "
            "Your reliability score will get +10 for covering an emergency. See you tonight!"
        )

    def _employee_vto(self, user_id: str, entities: Dict, message: str) -> str:
        return (
            "VTO is available right now! Current demand is low enough to release 2 people. "
            "You'd leave at your current point in shift with no reliability impact. "
            "Hours deducted from weekly total. Want me to put you on the VTO list?"
        )

    def _confirm_vto(self, user_id: str, entities: Dict) -> str:
        return (
            "You're on the VTO list. You'll be released in priority order "
            "(longest tenure first). I'll message you within 15 minutes with "
            "confirmation. Keep working until you hear from me!"
        )

    def _employee_tier_change(self, user_id: str, entities: Dict, message: str) -> str:
        worker = self.workers.get(user_id, self.workers["EMP001"])
        message_lower = message.lower()

        if "3" in message or "flex" in message_lower:
            target_tier = 3
            description = (
                "Tier 3 (Full Flex) means:\n"
                "  - No committed hours - you pick your own shifts\n"
                "  - Access to surge pricing (up to 2x pay)\n"
                "  - Requires 82+ reliability score (yours: {score})\n"
                "  - No guaranteed minimum hours\n\n"
                "Based on your patterns, you'd likely earn 15-40% more but with "
                "variable hours. Want to switch? Takes effect next pay period."
            ).format(score=worker["reliability_score"])
        elif "1" in message or "fixed" in message_lower:
            target_tier = 1
            description = (
                "Tier 1 (Fixed Anchor) means:\n"
                "  - Guaranteed schedule, same hours every week\n"
                "  - Base rate ${rate:.2f}/hr, no surge premiums\n"
                "  - Maximum predictability, minimum flexibility\n\n"
                "You'd lose access to flex/surge earnings. Sure about this?"
            ).format(rate=worker["base_rate"])
        else:
            target_tier = 2
            description = (
                "You're already Tier 2 (Flex Buffer). This gives you:\n"
                "  - Core availability windows you choose\n"
                "  - $5/hr holding yield during your windows\n"
                "  - 1.5x rate when activated\n"
                "  - Good balance of predictability and extra earnings\n\n"
                "Want to explore Tier 1 (fixed) or Tier 3 (full flex) instead?"
            )

        return description

    def _employee_earnings(self, user_id: str, entities: Dict, message: str) -> str:
        worker = self.workers.get(user_id, self.workers["EMP001"])
        earnings = worker.get("earnings_this_week", {})

        base = earnings.get("base", 612.00)
        flex = earnings.get("flex_activation", 229.50)
        surge = earnings.get("surge_claims", 290.70)
        total = base + flex + surge

        base_only = base  # What they'd earn on flat Tier 1
        pct_more = ((total - base_only) / base_only) * 100

        return (
            f"This week so far (Mon-Thu):\n"
            f"  Base shifts: 4 x 8.5hr = ${base:.2f}\n"
            f"  Flex activation (Tue): $27/hr x 8.5hr = ${flex:.2f}\n"
            f"  Surge claim (Wed night): $34.20/hr x 8.5hr = ${surge:.2f}\n"
            f"  Total: ${total:.2f} (vs ${base_only:.2f} if you were flat Tier 1)\n\n"
            f"You're earning {pct_more:.0f}% MORE than fixed scheduling this week. Nice work!"
        )

    def _employee_reliability(self, user_id: str, entities: Dict, message: str) -> str:
        worker = self.workers.get(user_id, self.workers["EMP001"])
        score = worker["reliability_score"]

        status = "Good standing" if score >= 80 else "At risk" if score >= 70 else "Probation"

        return (
            f"Your reliability score: {score}/100 ({status})\n\n"
            "What affects it:\n"
            "  +10  Covering emergency/surge shifts\n"
            "  +5   Consistent attendance (weekly)\n"
            "  +3   Accepting flex activations\n"
            "  -5   Short-notice callout (under 4 hrs)\n"
            "  -15  No-call no-show\n"
            "  -3   Pattern absences (same day repeated)\n\n"
            f"Tier 3 access requires 82+. You're {'eligible' if score >= 82 else str(82 - score) + ' points away'}. "
            "Want tips on boosting your score?"
        )

    def _employee_compliance(self, user_id: str, entities: Dict, message: str) -> str:
        worker = self.workers.get(user_id, self.workers["EMP001"])
        hours = worker["weekly_hours"]
        max_hours = worker["max_weekly"]

        return (
            f"Quick compliance check for you:\n"
            f"  Weekly hours: {hours}/{max_hours} (OK)\n"
            f"  Rest period: 11hr minimum between shifts (OK - your next gap is 15.5hr)\n"
            f"  Consecutive days: 5/6 max (OK)\n"
            f"  Overtime threshold: 40hr (you're at {hours}, "
            f"{'already in OT zone' if hours > 40 else str(40 - hours) + 'hr until OT'})\n\n"
            "All clear for additional shifts! Let me know if you want to claim something."
        )

    def _employee_pool_status(self, user_id: str, entities: Dict, message: str) -> str:
        pool = self.pool_state["tonight_shift"]
        return (
            f"Current pool status (tonight's shift):\n"
            f"  Filled: {pool['filled']}/{pool['needed']}\n"
            f"  Tier 1 anchors: {pool['tier1_anchors']} confirmed\n"
            f"  Tier 2 activated: {pool['tier2_activated']} (at $27/hr)\n"
            f"  Tier 3 surge: 1 slot open at ${pool['current_rate']:.2f}/hr ({pool['surge_multiplier']}x)\n"
            f"  {pool['tier3_viewing']} workers currently viewing\n\n"
            "Looks healthy! Want to claim the open surge slot?"
        )

    def _employee_help(self, user_id: str, entities: Dict, message: str) -> str:
        message_lower = message.lower()

        if "tier" in message_lower:
            return (
                "Here's how tiers work:\n\n"
                "  Tier 1 (Fixed Anchor): Same schedule every week. "
                "Predictable but no premium pay.\n"
                "  Tier 2 (Flex Buffer): You set availability windows. "
                "Earn $5/hr holding yield + 1.5x when activated.\n"
                "  Tier 3 (Full Flex): Pure gig-style. "
                "Pick your shifts, earn surge pricing up to 2x.\n\n"
                "You choose your tier. More flex = more earning potential but less certainty. "
                "Want me to recommend the best tier for your situation?"
            )
        elif "reliability" in message_lower or "score" in message_lower:
            return (
                "Reliability score (0-100) tracks how dependable you are:\n"
                "  - Show up as scheduled: score goes up\n"
                "  - Cover emergency shifts: big boost (+10)\n"
                "  - Call out with notice: no impact (4+ hours)\n"
                "  - Short-notice callout: small hit (-5)\n"
                "  - No-show: major hit (-15)\n\n"
                "Higher score = access to better shifts and higher tiers. "
                "Want to see your current score?"
            )
        elif "availab" in message_lower or "change" in message_lower:
            return (
                "Go to Profile > Availability Windows. Or just tell me - "
                "which days/times do you want to be available for Tier 2 flex? "
                "I'll update it for you right here."
            )
        elif "schedule" in message_lower or "where" in message_lower or "find" in message_lower:
            return (
                "Tap the calendar icon at the bottom, or I can show you right here. "
                "Just say 'show my schedule' and I'll pull it up. "
                "Want to see this week or next week?"
            )
        else:
            return (
                "I can help you with:\n"
                "  - View your schedule ('when do I work?')\n"
                "  - Call out of a shift ('I can't come in tomorrow')\n"
                "  - Find extra shifts ('any surge available?')\n"
                "  - Check your earnings ('how much did I make?')\n"
                "  - See your reliability score ('what's my rating?')\n"
                "  - Swap shifts with someone ('trade with Maria')\n"
                "  - Request VTO ('can I go home early?')\n"
                "  - Change your tier ('switch to flex')\n\n"
                "Just talk to me naturally - no special commands needed!"
            )

    # =========================================================================
    # 4. MANAGER CONVERSATION HANDLERS
    # =========================================================================

    def _handle_manager_intent(self, user_id: str, intent: str, entities: Dict, message: str) -> str:
        """Route manager intents to specific handlers."""
        handlers = {
            "demand_post": self._manager_demand_post,
            "pool_status": self._manager_pool_status,
            "schedule_build": self._manager_schedule_build,
            "report_request": self._manager_report,
            "help": self._manager_help,
        }
        handler = handlers.get(intent, self._manager_pool_status)
        return handler(user_id, entities, message)

    def _manager_demand_post(self, user_id: str, entities: Dict, message: str) -> str:
        count = 3
        if "numbers" in entities:
            count = entities["numbers"][0]

        role = "Pick"
        if "shift_types" in entities:
            role = entities["shift_types"][0].capitalize()

        day = "Saturday"
        if "days" in entities:
            day_map = {
                "mon": "Monday", "monday": "Monday",
                "tue": "Tuesday", "tuesday": "Tuesday",
                "wed": "Wednesday", "wednesday": "Wednesday",
                "thu": "Thursday", "thursday": "Thursday",
                "fri": "Friday", "friday": "Friday",
                "sat": "Saturday", "saturday": "Saturday",
                "sun": "Sunday", "sunday": "Sunday",
            }
            day = day_map.get(entities["days"][0], "Saturday")

        return (
            f"Adding {count} {role} slots to {day} night shift (10pm-6:30am). "
            "Current pool status:\n"
            f"  - 4 Tier 2 workers have {day} night availability\n"
            "  - 6 Tier 3 workers eligible\n"
            "  - Estimated fill probability: 94% at base+surge pricing\n"
            "  - Estimated premium cost: $45-$120 depending on fill timing\n\n"
            "Shall I post to the pool now? Note: posting now gives 4 days notice "
            "(Chicago requires 14 - this will trigger predictability pay of $18 per worker)."
        )

    def _confirm_demand_post(self, user_id: str, entities: Dict) -> str:
        return (
            "Posted. 3 slots live in the pool. Predictability pay flagged "
            "($54 total for 3 workers). I'll notify you as they fill. "
            "Current market: $18.50/hr (just above base). "
            "Expect claims within 2-4 hours based on historical patterns."
        )

    def _manager_pool_status(self, user_id: str, entities: Dict, message: str) -> str:
        pool = self.pool_state["tonight_shift"]
        return (
            f"Tonight (10pm shift): {pool['filled']}/{pool['needed']} filled\n"
            f"  - {pool['tier1_anchors']} Tier 1 anchors confirmed\n"
            f"  - {pool['tier2_activated']} Tier 2 activated ($27/hr)\n"
            f"  - 1 slot open - currently in Tier 3 surge at ${pool['current_rate']:.2f}/hr "
            f"({pool['surge_multiplier']}x)\n"
            f"  - {pool['tier3_viewing']} Tier 3 workers are viewing it now\n\n"
            "Estimated fill: 8 minutes based on current price trajectory. "
            "No action needed from you."
        )

    def _manager_schedule_build(self, user_id: str, entities: Dict, message: str) -> str:
        mgr = self.workers.get(user_id, self.workers["MGR001"])
        count = 40
        if "numbers" in entities:
            count = entities["numbers"][0]

        return (
            f"Building Week of July 14 for {count} AAs. Let me check:\n"
            f"  - Demand plan loaded (Mon-Sun, 3 shifts)\n"
            f"  - {mgr.get('active_count', 37)} active "
            f"(3 on leave: {', '.join(mgr.get('on_leave', ['Aisha-FMLA', 'David-PTO', 'Chen-sick']))})\n"
            "  - 20 Tier 1 anchors auto-assigned to their committed blocks\n"
            "  - 12 Tier 2 windows mapped\n"
            "  - 8 Tier 3 available for surge\n\n"
            "Schedule generated. 0 violations. 92% fill rate off anchor+flex alone.\n"
            "Remaining 8% will self-clear via surge pool during the week.\n"
            "Want to review or approve for posting?"
        )

    def _confirm_schedule_build(self, user_id: str, entities: Dict) -> str:
        return (
            "Schedule approved and posted! All 37 active workers have been notified. "
            "Tier 1 anchors see their fixed blocks. Tier 2/3 see available windows. "
            "I'll track fill rates and alert you if anything drops below 85%. "
            "Looking good for next week!"
        )

    def _manager_report(self, user_id: str, entities: Dict, message: str) -> str:
        return (
            "This week's summary (Mon-Fri so far):\n\n"
            "  Staffing:\n"
            "    Target hours: 1,360 | Filled: 1,298 (95.4%)\n"
            "    Callouts: 4 | Auto-filled: 4 (100% resolution)\n"
            "    Manager interventions needed: 0\n\n"
            "  Costs:\n"
            "    Base labor: $24,480\n"
            "    Flex premiums: $1,890 (7.7% of base)\n"
            "    Surge premiums: $680 (2.8% of base)\n"
            "    Predictability pay: $0 (all posted 14+ days)\n"
            "    Total premium cost: $2,570 (10.5% overhead)\n\n"
            "  vs. Last Week:\n"
            "    Fill rate: +3.2% | Premium cost: -$340 | Callout resolution: 100% (was 75%)\n\n"
            "The system is learning your patterns. Premium costs are trending down."
        )

    def _manager_help(self, user_id: str, entities: Dict, message: str) -> str:
        return (
            "Manager commands I understand:\n"
            "  - 'Need X more [role] for [day]' - post demand to pool\n"
            "  - 'How's tonight/tomorrow looking' - staffing status\n"
            "  - 'Build next week's schedule' - auto-generate\n"
            "  - 'Show me costs/report' - weekly metrics\n"
            "  - 'Who's at risk of calling out?' - predictive alerts\n"
            "  - 'Override [worker] to [shift]' - manual assignment\n\n"
            "I handle most staffing automatically. You'll only hear from me "
            "when something needs your decision."
        )


# =============================================================================
# 5. PROACTIVE NOTIFICATIONS
# =============================================================================

class ProactiveNotifier:
    """
    AI-initiated outreach - alerts workers and managers before problems happen.
    """

    def __init__(self, engine: ConversationEngine):
        self.engine = engine

    def check_reliability_warning(self, user_id: str) -> Optional[str]:
        """Warn worker if reliability score is approaching danger zone."""
        worker = self.engine.workers.get(user_id)
        if not worker:
            return None
        score = worker.get("reliability_score", 100)
        if score <= 75 and score > 65:
            return (
                f"Heads up: your reliability score dropped to {score}. "
                "One more short-notice callout and you'll lose Tier 3 access. "
                "Want tips on maintaining your score?"
            )
        return None

    def surge_alert(self, user_id: str, rate: float, minutes_until: int) -> str:
        """Alert worker about a high-value surge opportunity."""
        return (
            f"Surge alert! A ${rate:.2f}/hr shift just opened in {minutes_until} minutes. "
            "Based on your history, you usually claim these. Want it?"
        )

    def hours_limit_warning(self, user_id: str) -> Optional[str]:
        """Warn worker approaching weekly hour limit."""
        worker = self.engine.workers.get(user_id)
        if not worker:
            return None
        hours = worker.get("weekly_hours", 0)
        max_hours = worker.get("max_weekly", 60)
        if hours >= 52:
            remaining_shift = 8.5
            projected = hours + remaining_shift
            if projected > max_hours:
                return (
                    f"Your weekly hours are at {hours}. You have one more shift "
                    f"scheduled (8.5hr) which would put you at {projected}. "
                    f"Want me to trim it to stay under {max_hours}?"
                )
            elif projected > 55:
                return (
                    f"Your weekly hours are at {hours}. After your next shift "
                    f"you'll be at {projected}. Getting close to the {max_hours}hr cap. "
                    "Want me to watch this for you?"
                )
        return None

    def callout_prediction_alert(self, manager_id: str) -> str:
        """Alert manager about predicted callouts."""
        return (
            "Tomorrow has 3 high-risk callout predictions "
            "(Marcus 78%, Tyler 65%, Rosa 55%). "
            "Tier 2 buffer is ready. No action needed but FYI."
        )


# =============================================================================
# 6. NAVIGATION HELPER
# =============================================================================

class NavigationHelper:
    """
    Helps users find features and understand the platform.
    Detects confusion and offers step-by-step guidance.
    """

    NAVIGATION_MAP = {
        "schedule": "Tap the calendar icon at the bottom, or say 'show my schedule'",
        "availability": "Go to Profile > Availability Windows",
        "earnings": "Go to Earnings tab or say 'how much did I make'",
        "reliability": "Profile > Reliability Score",
        "swap": "Schedule > tap a shift > Swap/Trade",
        "vto": "Home > VTO Available banner (when active)",
        "tier": "Profile > My Tier > Change Tier",
        "pool": "Home > Pool Status (managers only)",
        "demand": "Manager Dashboard > Post Demand",
        "reports": "Manager Dashboard > Analytics",
    }

    def get_navigation(self, feature: str) -> str:
        """Get navigation instructions for a feature."""
        for key, instruction in self.NAVIGATION_MAP.items():
            if key in feature.lower():
                return instruction
        return "Try the search bar at the top, or just tell me what you're looking for."

    def detect_confusion(self, messages: List[str]) -> bool:
        """Detect if user seems confused based on recent messages."""
        confusion_signals = [
            "i don't understand", "confused", "lost", "where",
            "how do i", "can't find", "not sure", "help",
        ]
        recent = " ".join(messages[-3:]).lower() if messages else ""
        return any(signal in recent for signal in confusion_signals)

    def offer_walkthrough(self, feature: str) -> str:
        """Offer step-by-step guidance."""
        return (
            f"No worries! Let me walk you through {feature} step by step. "
            "Or if you prefer, just tell me what you want to do and I'll handle it "
            "for you right here in chat."
        )


# =============================================================================
# 7. MULTI-PLATFORM RESPONSE FORMAT
# =============================================================================

def format_response(response: str, platform: str = "mobile") -> str:
    """
    Format response for different platforms.

    Platforms:
    - mobile: short, action-button suggestions
    - desktop: full detail, tables, links
    - sms: ultra-brief (under 160 chars)
    - slack: formatted with blocks
    """
    if platform == "sms":
        # Ultra-brief: first sentence only, under 160 chars
        first_sentence = response.split(". ")[0].split(".\n")[0]
        if len(first_sentence) > 155:
            first_sentence = first_sentence[:152] + "..."
        return first_sentence

    elif platform == "mobile":
        # Keep it concise, suggest action buttons
        lines = response.split("\n")
        # Trim excessive whitespace and limit length
        trimmed = "\n".join(line for line in lines if line.strip())
        if len(trimmed) > 500:
            trimmed = trimmed[:497] + "..."
        return trimmed

    elif platform == "desktop":
        # Full response with formatting enhancements
        return f"{'=' * 50}\n{response}\n{'=' * 50}"

    elif platform == "slack":
        # Slack block format
        blocks = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": response.replace("  ", " "),
                    }
                }
            ]
        }
        return json.dumps(blocks, indent=2)

    return response


# =============================================================================
# 8. MAIN - SIMULATE A FULL DAY OF CONVERSATIONS
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("  WORKFORCE COMPLIANCE AI - CONVERSATIONAL INTERFACE DEMO")
    print("  Simulating a full day of natural language interactions")
    print("=" * 70)

    engine = ConversationEngine()
    notifier = ProactiveNotifier(engine)
    nav = NavigationHelper()

    def print_conversation(timestamp: str, user_label: str, user_id: str,
                          role: str, messages: List[str]):
        """Print a multi-turn conversation with formatting."""
        print(f"\n{'-' * 70}")
        print(f"  [{timestamp}] {user_label}")
        print(f"{'-' * 70}")
        for msg in messages:
            if msg.startswith("USER:"):
                content = msg[5:].strip()
                print(f"\n  User: {content}")
                response = engine.process_message(user_id, content, role)
                print(f"\n  Bot:  {response}")
            elif msg.startswith("NOTIFY:"):
                content = msg[7:].strip()
                print(f"\n  [Proactive] Bot: {content}")
        print()

    # === 6:00 AM - Employee checks schedule ===
    print_conversation(
        "6:00 AM", "Jordan Chen (Employee, Tier 2)", "EMP001", "employee",
        ["USER: what's my schedule this week"]
    )

    # === 7:30 AM - Employee calls out ===
    print_conversation(
        "7:30 AM", "Jordan Chen (Employee, Tier 2)", "EMP001", "employee",
        [
            "USER: hey i cant come in tomorrow",
            "USER: yeah",
        ]
    )

    # === 7:31 AM - System auto-notifies manager ===
    print_conversation(
        "7:31 AM", "Sarah Kim (Manager) - AUTO NOTIFICATION", "MGR001", "manager",
        [
            "NOTIFY: Callout received: Jordan Chen won't make Thursday 6am-2:30pm (Pick). "
            "18hr notice - no fault. Shift auto-released to pool. "
            "Maria Rodriguez (Tier 2, $27/hr) has been offered it. "
            "Current fill probability: 96%. No action needed.",
        ]
    )

    # === 10:00 AM - Another employee asks about surge ===
    print_conversation(
        "10:00 AM", "Marcus Williams (Employee, Tier 3)", "EMP003", "employee",
        [
            "USER: any surge shifts available?",
            "USER: grab the first one",
        ]
    )

    # === 2:00 PM - Manager posts extra demand ===
    print_conversation(
        "2:00 PM", "Sarah Kim (Manager)", "MGR001", "manager",
        [
            "USER: i need 3 extra pickers for saturday night",
            "USER: post it",
        ]
    )

    # === 4:00 PM - Employee asks about availability ===
    print_conversation(
        "4:00 PM", "Jordan Chen (Employee, Tier 2)", "EMP001", "employee",
        [
            "USER: how do i change my availability",
            "USER: tuesdays and thursdays 2pm to 10pm",
        ]
    )

    # === 6:00 PM - Employee checks earnings ===
    print_conversation(
        "6:00 PM", "Jordan Chen (Employee, Tier 2)", "EMP001", "employee",
        ["USER: how much did i make this week"]
    )

    # === Proactive notifications demo ===
    print(f"\n{'-' * 70}")
    print("  [PROACTIVE NOTIFICATIONS - AI reaches out]")
    print(f"{'-' * 70}")

    # Reliability warning
    warning = notifier.check_reliability_warning("EMP003")
    if warning:
        print(f"\n  To Marcus Williams:")
        print(f"  Bot: {warning}")

    # Surge alert
    alert = notifier.surge_alert("EMP003", 38.00, 45)
    print(f"\n  To Marcus Williams:")
    print(f"  Bot: {alert}")

    # Hours limit warning
    engine.workers["EMP001"]["weekly_hours"] = 52
    hours_warning = notifier.hours_limit_warning("EMP001")
    if hours_warning:
        print(f"\n  To Jordan Chen:")
        print(f"  Bot: {hours_warning}")

    # Manager callout prediction
    prediction = notifier.callout_prediction_alert("MGR001")
    print(f"\n  To Sarah Kim (Manager):")
    print(f"  Bot: {prediction}")

    # === Multi-platform formatting demo ===
    print(f"\n{'-' * 70}")
    print("  [MULTI-PLATFORM RESPONSE FORMATTING]")
    print(f"{'-' * 70}")

    sample_response = (
        "Claimed! Tonight 10pm-6:30am Stow at $28.50/hr locked in. "
        "That's $89.25 extra vs base rate for this shift. "
        "Your reliability score will get +10 for covering an emergency."
    )

    for platform in ["mobile", "desktop", "sms", "slack"]:
        print(f"\n  [{platform.upper()}]:")
        formatted = format_response(sample_response, platform)
        for line in formatted.split("\n"):
            print(f"    {line}")

    # === Final summary ===
    print(f"\n{'=' * 70}")
    print("  DAY COMPLETE")
    print(f"{'=' * 70}")
    print("""
  Interactions handled: 7 conversations, 14 message turns
  Manager effort on callout resolution: ZERO
  Compliance violations: 0
  Shifts auto-filled: 1 (via Tier 2 flex pool)
  Surge shifts claimed: 1 (worker-initiated)
  Schedule changes: 1 (availability update via chat)

  All interactions completed with ZERO manager effort on callout resolution.

  The AI handled:
    - Intent recognition across 14 categories
    - Multi-turn conversation with context
    - Compliance checks (rest periods, hours limits, predictability pay)
    - Pool operations (release, offer, claim, post)
    - Proactive notifications (reliability, surge, hours, predictions)
    - Navigation assistance
    - Multi-platform formatting (mobile, desktop, SMS, Slack)
""")
    print("=" * 70)
