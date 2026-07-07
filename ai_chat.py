"""
Workforce Compliance AI - Conversational AI Interface
Claude-powered chat for managers and workers. Understands scheduling context,
calls the right modules, returns natural language answers with actions.
"""

import os
import json
from datetime import datetime, timedelta

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from hours_tracker import (
    get_all_employee_dashboards, predict_shift_impact, calculate_employee_hours,
    calculate_fatigue_score, OT_THRESHOLD_WEEKLY
)
from coverage_engine import find_coverage, calculate_team_fairness_report
from bulk_scheduler import bulk_generate_schedule, get_available_patterns
from leave_management import LeaveBalanceTracker, LEAVE_TYPES
from shift_templates import SHIFT_TEMPLATES, SHIFT_ASSIGNMENTS, find_coverage_for_absence
from holiday_auction import HolidayAuction


SYSTEM_PROMPT = """You are an AI scheduling assistant for a workforce management platform. You help managers and workers with scheduling, compliance, time-off, coverage, and fairness questions.

You have access to these capabilities (call them by responding with structured JSON actions):

MANAGER CAPABILITIES:
- generate_schedule: Create a full schedule for a period (needs: workers count, pattern, dates)
- find_coverage: Find who can cover a gap (needs: date, shift time, role)
- check_hours: See an employee's current hours, fatigue, OT status
- team_dashboard: See all employees' hours and fatigue at once
- run_compliance: Check schedule for violations
- predict_impact: What happens if you add a shift to someone
- fairness_report: Show team fairness distribution
- approve_request: Approve a pending request
- deny_request: Deny with reason and alternative

WORKER CAPABILITIES:
- my_hours: Check own hours remaining this week
- my_balance: Check PTO/sick/UPT balances
- request_off: Submit time-off request with priority
- request_swap: Propose a shift swap
- my_schedule: View own upcoming schedule
- available_vet: See available VET/open shifts

GUIDELINES:
- Be concise and actionable
- When a manager asks to generate a schedule, confirm the parameters then execute
- When asked "who can cover", provide the top 3 ranked by fairness with reasons
- When asked about hours/fatigue, give the specific numbers
- For requests, check compliance and fairness before suggesting approval
- Always explain the "why" behind recommendations
- Flag any compliance risks proactively
- If you need more info to act, ask one clear question

Respond naturally but include an "action" field in your response when you're executing something.
Format: {"message": "your response text", "action": {"type": "action_name", "params": {...}}, "data": {...}}
If no action needed (just answering a question), omit the action field.
"""


class AIChat:
    """Conversational AI interface powered by Claude."""

    def __init__(self, employees=None, schedule_data=None, leave_tracker=None,
                 employee_history=None, user_role="MANAGER", user_employee_id=None):
        self.employees = employees or []
        self.schedule_data = schedule_data or {"shifts": []}
        self.leave_tracker = leave_tracker
        self.employee_history = employee_history or {}
        self.user_role = user_role
        self.user_employee_id = user_employee_id
        self.conversation_history = []
        self.client = None

        if ANTHROPIC_AVAILABLE and os.getenv("ANTHROPIC_API_KEY"):
            self.client = Anthropic()

    def chat(self, user_message):
        """
        Process a user message and return a response.
        Uses Claude API if available, otherwise falls back to rule-based responses.
        """
        self.conversation_history.append({"role": "user", "content": user_message})

        if self.client:
            response = self._call_claude(user_message)
        else:
            response = self._rule_based_response(user_message)

        self.conversation_history.append({"role": "assistant", "content": response["message"]})
        return response

    def _call_claude(self, user_message):
        """Call Claude API with full context."""
        context = self._build_context()

        messages = []
        for msg in self.conversation_history[-10:]:  # last 10 messages for context
            messages.append(msg)

        try:
            response = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                system=SYSTEM_PROMPT + "\n\nCURRENT CONTEXT:\n" + context,
                messages=messages,
            )
            text = response.content[0].text

            # Try to parse as JSON action
            try:
                parsed = json.loads(text)
                if "action" in parsed:
                    action_result = self._execute_action(parsed["action"])
                    parsed["action_result"] = action_result
                return parsed
            except json.JSONDecodeError:
                return {"message": text}

        except Exception as e:
            return {"message": f"AI temporarily unavailable. Error: {str(e)[:100]}"}

    def _rule_based_response(self, user_message):
        """Fallback: pattern-matching responses when Claude API is not available."""
        msg = user_message.lower().strip()

        # --- Coverage questions ---
        if any(kw in msg for kw in ["who can cover", "find coverage", "need someone to cover", "who's available"]):
            return self._handle_coverage_query(msg)

        # --- Schedule generation ---
        if any(kw in msg for kw in ["generate schedule", "create schedule", "build schedule",
                                     "spread", "distribute", "plan the month"]):
            return self._handle_schedule_generation(msg)

        # --- Hours/fatigue questions ---
        if any(kw in msg for kw in ["how many hours", "hours left", "overtime", "fatigue",
                                     "hours remaining", "my hours"]):
            return self._handle_hours_query(msg)

        # --- Balance questions ---
        if any(kw in msg for kw in ["pto balance", "sick balance", "leave balance",
                                     "how much pto", "how many days off", "my balance", "upt"]):
            return self._handle_balance_query(msg)

        # --- Time-off requests ---
        if any(kw in msg for kw in ["request off", "time off", "take off", "day off",
                                     "holiday request", "vacation"]):
            return self._handle_time_off_request(msg)

        # --- Swap requests ---
        if any(kw in msg for kw in ["swap", "trade", "switch shift", "exchange"]):
            return self._handle_swap_query(msg)

        # --- What-if / impact questions ---
        if any(kw in msg for kw in ["what if", "what happens if", "impact of", "can i add"]):
            return self._handle_what_if(msg)

        # --- Fairness ---
        if any(kw in msg for kw in ["fairness", "fair", "equal", "distribution", "who's worked more"]):
            return self._handle_fairness_query()

        # --- Compliance ---
        if any(kw in msg for kw in ["violation", "compliance", "legal", "breaking", "acgme", "rule"]):
            return self._handle_compliance_query()

        # --- Duty hours / ACGME specific ---
        if any(kw in msg for kw in ["duty hour", "80 hour", "safe to cover", "can .* cover",
                                     "at risk", "who's over", "weekly hours", "how many hour"]):
            return self._handle_hours_query(msg)

        # --- Night/weekend/call questions ---
        if any(kw in msg for kw in ["night shift", "who's on call", "jeopardy", "backup",
                                     "who's working", "on call", "tonight", "tomorrow"]):
            return self._handle_coverage_query(msg)

        # --- Schedule / roster ---
        if any(kw in msg for kw in ["schedule", "roster", "who's off", "who is off", "staffing"]):
            return self._handle_schedule_generation(msg)

        # --- Greeting / hi / hello ---
        if any(kw in msg for kw in ["hi", "hello", "hey", "good morning", "good evening"]):
            return {
                "message": (
                    "Hey! I'm Otto, your scheduling assistant. "
                    "I can check duty hours, find coverage, verify swaps, or generate schedules. "
                    "What do you need help with right now?"
                )
            }

        # --- Thank you ---
        if any(kw in msg for kw in ["thank", "thanks", "great", "perfect", "awesome"]):
            return {"message": "You're welcome! Let me know if you need anything else."}

        # --- Fallback: try to be helpful based on context ---
        # Instead of repeating the template, give a contextual response
        if self.employees:
            emp_count = len(self.employees)
            return {
                "message": (
                    f"I'm not sure I understood that. I have data for **{emp_count} staff members** "
                    f"in the system right now.\n\n"
                    f"Try asking me something specific like:\n"
                    f"- \"Is Dr. Patel safe to cover tonight?\"\n"
                    f"- \"Who has the fewest night shifts this month?\"\n"
                    f"- \"What's the duty hour status for all residents?\"\n"
                    f"- \"Can I swap Monday with Wednesday?\"\n\n"
                    f"Or just tell me what you need and I'll figure it out!"
                )
            }

        return {
            "message": (
                "I'm not sure I understood that. Try asking something like:\n"
                "- \"Who can cover tomorrow?\"\n"
                "- \"Is it safe to assign Dr. Kim to Friday night?\"\n"
                "- \"Show me the duty hours dashboard\"\n\n"
                "I work best with specific questions about scheduling, hours, or coverage."
            )
        }

    # --- Action Handlers ---

    def _handle_coverage_query(self, msg):
        """Handle 'who can cover' queries."""
        # Try to find a date reference
        ref_date = datetime.now()
        if "tomorrow" in msg:
            ref_date += timedelta(days=1)

        # Default to a day shift gap
        gap_shift = {
            "date": ref_date.strftime("%Y-%m-%d"),
            "start": "07:00",
            "end": "15:30",
            "role": self.employees[0].get("role", "Staff") if self.employees else "Staff",
            "shift_type": "Day",
        }

        if self.employees and self.schedule_data.get("shifts"):
            candidates = find_coverage(
                self.schedule_data["shifts"], self.employees, gap_shift,
                self.employee_history, ref_date
            )

            if candidates:
                top3 = candidates[:3]
                lines = [f"Here are the top 3 fairness-ranked candidates for {ref_date.strftime('%A, %b %d')}:\n"]
                for i, c in enumerate(top3, 1):
                    lines.append(
                        f"**{i}. {c['name']}** (Score: {c['composite_score']}/100)\n"
                        f"   Weekly hours: {c['current_weekly_hours']}h | "
                        f"Fatigue: {c['fatigue_level']} | "
                        f"Est. OT cost: ${c['estimated_ot_cost']:.0f}\n"
                        f"   Why: {c['reason']}\n"
                    )
                lines.append("\nWould you like me to send a VET offer to the top candidate?")
                return {"message": "\n".join(lines), "data": {"candidates": top3}}
            else:
                return {"message": "No eligible candidates found for that shift. Consider extending the search to other departments or posting as an open shift."}

        return {"message": "I need your team data loaded to find coverage. Please run the demo first or upload a schedule."}

    def _handle_schedule_generation(self, msg):
        """Handle schedule generation requests."""
        # Extract numbers from message
        import re
        numbers = re.findall(r'\d+', msg)
        worker_count = int(numbers[0]) if numbers else len(self.employees)

        patterns = get_available_patterns()
        pattern_list = "\n".join([f"- **{k}**: {v}" for k, v in patterns.items()])

        if not self.employees or worker_count == 0:
            return {
                "message": (
                    f"I'll generate a schedule. I need a few details:\n\n"
                    f"1. **How many workers?** (I see: {worker_count})\n"
                    f"2. **What period?** (e.g., \"August\" or \"next month\")\n"
                    f"3. **What pattern?**\n{pattern_list}\n\n"
                    f"Example: \"Generate August schedule for 5 residents using healthcare 24/7\""
                )
            }

        # If we have enough info, generate
        next_month = datetime.now().replace(day=1) + timedelta(days=32)
        start = next_month.replace(day=1).strftime("%Y-%m-%d")
        end_dt = (next_month.replace(day=1) + timedelta(days=31)).replace(day=1) - timedelta(days=1)
        end = end_dt.strftime("%Y-%m-%d")

        result = bulk_generate_schedule(
            employees=self.employees[:worker_count],
            start_date=start,
            end_date=end,
            pattern_type="healthcare_24_7",
            approved_time_off=[],
            worker_preferences={},
        )

        sc = result["fairness_scorecard"]
        msg_lines = [
            f"Schedule generated for **{result['workers']} workers**, {start} to {end}:\n",
            f"- **{result['total_shifts']} shifts** created",
            f"- Pattern: {result['pattern']}",
            f"- Fairness: **{sc['fairness_rating']}**",
            f"- Night deviation: {sc['max_night_deviation']} shifts",
            f"- Weekend deviation: {sc['max_weekend_deviation']} shifts\n",
            "**Distribution:**",
        ]
        for name, stats in list(result["employee_summary"].items())[:5]:
            msg_lines.append(f"  {name}: {stats['total']} shifts ({stats['nights']} nights, {stats['weekends']} weekends)")

        if len(result["employee_summary"]) > 5:
            msg_lines.append(f"  ... and {len(result['employee_summary'])-5} more")

        msg_lines.append("\nWould you like me to adjust anything? (e.g., \"Dr. Patel needs March 1-14 off\")")

        return {
            "message": "\n".join(msg_lines),
            "action": {"type": "generate_schedule", "params": {"start": start, "end": end}},
            "data": {"fairness": sc, "total_shifts": result["total_shifts"]},
        }

    def _handle_hours_query(self, msg):
        """Handle hours/fatigue questions."""
        if not self.employees or not self.schedule_data.get("shifts"):
            return {"message": "I need schedule data loaded. Please run the demo first."}

        ref_date = datetime.now()
        dashboards = get_all_employee_dashboards(
            self.schedule_data["shifts"], self.employees, ref_date
        )

        # Check if asking about specific person
        target = None
        for emp in self.employees:
            if emp["name"].lower().split()[0] in msg or emp["name"].lower().split()[-1] in msg:
                target = emp
                break

        if target:
            d = next((d for d in dashboards if d.get("employee_id") == target["id"]), None)
            if d:
                return {
                    "message": (
                        f"**{target['name']}** — current status:\n\n"
                        f"- Weekly hours: **{d['weekly_hours']}h** / 40h\n"
                        f"- OT remaining before threshold: **{d['hours_remaining_before_ot']}h**\n"
                        f"- Consecutive days: {d['consecutive_days']}\n"
                        f"- Fatigue score: **{d['fatigue_score']}/100** ({d['fatigue_level'].upper()})\n"
                        f"- Shift mix: {d['shift_type_distribution']['day']}D / "
                        f"{d['shift_type_distribution']['evening']}E / "
                        f"{d['shift_type_distribution']['night']}N\n\n"
                        f"{'**Warning: Approaching fatigue threshold.**' if d['fatigue_level'] != 'green' else 'Looking good - well rested.'}"
                    )
                }

        # Show team summary
        sorted_d = sorted(dashboards, key=lambda x: x.get("fatigue_score", 0), reverse=True)
        lines = ["**Team Hours Dashboard:**\n"]
        lines.append(f"{'Name':<20} {'Hours':<8} {'OT Left':<9} {'Fatigue'}")
        lines.append("-" * 50)
        for d in sorted_d[:8]:
            fatigue_icon = {"green": "OK", "yellow": "WARN", "red": "HIGH"}[d.get("fatigue_level", "green")]
            lines.append(f"{d.get('name', '?'):<20} {d['weekly_hours']:<8} "
                        f"{d['hours_remaining_before_ot']:<9} {fatigue_icon} ({d['fatigue_score']})")

        return {"message": "\n".join(lines)}

    def _handle_balance_query(self, msg):
        """Handle PTO/leave balance questions."""
        if not self.leave_tracker:
            return {"message": "Leave tracking not initialized. Run the demo to load sample data."}

        # If worker asking about themselves
        if self.user_employee_id:
            summary = self.leave_tracker.get_balance_summary(self.user_employee_id)
            if summary:
                lines = [
                    f"**Your Leave Balances:**\n",
                    f"- PTO: **{summary['pto_hours']}h** ({summary['pto_days']} days)",
                    f"  - Flex PTO: {summary.get('pto_flex_hours', 0)}h",
                    f"  - Standard PTO: {summary.get('pto_standard_hours', 0)}h",
                    f"- Sick Leave: **{summary['sick_hours']}h** ({summary['sick_days']} days)",
                    f"- UPT: **{summary['upt_hours']}h**",
                    f"- FMLA: {'Eligible' if summary['fmla_eligible'] else 'Not eligible'}"
                    f" ({summary['fmla_weeks_remaining']} weeks remaining)",
                ]
                if summary.get("at_risk", {}).get("pto_at_risk", 0) > 0:
                    lines.append(f"\n**At Risk:** {summary['at_risk']['pto_at_risk']}h PTO won't carry over!")
                    lines.append(f"Recommendation: {summary['at_risk']['recommendation']}")
                if summary["warnings"]:
                    lines.append("\n**Warnings:**")
                    for w in summary["warnings"]:
                        lines.append(f"- {w}")
                return {"message": "\n".join(lines)}

        return {"message": "I can check your balance. Which employee are you asking about?"}

    def _handle_time_off_request(self, msg):
        """Handle time-off request intent."""
        return {
            "message": (
                "I'll help you submit a time-off request. I need:\n\n"
                "1. **Dates**: When do you want off? (e.g., \"Dec 21-27\")\n"
                "2. **Priority**: How important is this? (1 = most important)\n"
                "3. **Reason** (optional): Helps with approval\n\n"
                "Example: \"Request December 21-27 off, priority 1, family visiting\"\n\n"
                "I'll check availability on your shift code, verify compliance, "
                "and either auto-approve or escalate to your manager with a recommendation."
            )
        }

    def _handle_swap_query(self, msg):
        """Handle shift swap intent."""
        return {
            "message": (
                "To propose a shift swap, I need:\n\n"
                "1. **Your shift date** you want to give up\n"
                "2. **Who** you want to swap with\n"
                "3. **Their shift date** you want to take\n\n"
                "Example: \"Swap my Tuesday with James's Thursday\"\n\n"
                "I'll check compliance for both of you, verify no violations are created, "
                "and send the proposal to them for acceptance."
            )
        }

    def _handle_what_if(self, msg):
        """Handle what-if/impact questions."""
        if not self.employees or not self.schedule_data.get("shifts"):
            return {"message": "Load schedule data first to run what-if analysis."}

        # Try to identify who
        target = None
        for emp in self.employees:
            if emp["name"].lower().split()[0] in msg or emp["name"].lower().split()[-1] in msg:
                target = emp
                break

        if target:
            proposed = {
                "employee_id": target["id"],
                "name": target["name"],
                "date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
                "start": "07:00",
                "end": "15:30",
                "role": target.get("role", "Staff"),
                "shift_type": "Day",
            }
            impact = predict_shift_impact(
                self.schedule_data["shifts"], target["id"], proposed, datetime.now()
            )

            lines = [f"**What-if: Add {target['name']} to a day shift in 2 days:**\n"]
            lines.append(f"- Current: {impact['current']['weekly_hours']}h, fatigue={impact['current']['fatigue_level']}")
            lines.append(f"- Projected: {impact['projected']['weekly_hours']}h, fatigue={impact['projected']['fatigue_level']}")
            lines.append(f"- Recommendation: **{impact['recommendation']}**")
            if impact["warnings"]:
                lines.append("\nWarnings:")
                for w in impact["warnings"]:
                    lines.append(f"- [{w['severity']}] {w['message']}")
            return {"message": "\n".join(lines)}

        return {"message": "Tell me who you want to add a shift to and what day, and I'll predict the impact."}

    def _handle_fairness_query(self):
        """Handle fairness distribution questions."""
        if not self.employees or not self.schedule_data.get("shifts"):
            return {"message": "Load schedule data to see fairness report."}

        report = calculate_team_fairness_report(
            self.schedule_data["shifts"], self.employees,
            self.employee_history, datetime.now()
        )

        lines = ["**Team Fairness Report:**\n"]
        lines.append(f"{'Name':<20} {'Fairness Idx':<13} {'Holidays':<9} {'Coverage Reqs'}")
        lines.append("-" * 55)
        for r in report[:8]:
            lines.append(f"{r['name']:<20} {r['fairness_index']}/100{'     ' if r['fairness_index']<10 else '    '}"
                        f"{r['holidays_worked_this_year']:<9} {r['coverage_requests_received']}")

        lines.append("\n*Lower fairness index = has carried more burden (deserves a break).*")
        return {"message": "\n".join(lines)}

    def _handle_compliance_query(self):
        """Handle compliance check questions."""
        if not self.schedule_data.get("shifts"):
            return {"message": "Load a schedule to check compliance."}

        from compliance_checker import check_compliance
        violations = check_compliance(self.schedule_data)

        if not violations:
            return {"message": "No compliance violations detected in the current schedule."}

        critical = [v for v in violations if v["severity"] == "CRITICAL"]
        high = [v for v in violations if v["severity"] == "HIGH"]

        lines = [f"**Compliance Check:** {len(violations)} violation(s) found\n"]
        if critical:
            lines.append(f"**CRITICAL ({len(critical)}):**")
            for v in critical:
                lines.append(f"- {v['description'][:80]}")
        if high:
            lines.append(f"\n**HIGH ({len(high)}):**")
            for v in high[:3]:
                lines.append(f"- {v['description'][:80]}")
            if len(high) > 3:
                lines.append(f"  ... and {len(high)-3} more")

        lines.append(f"\nTotal estimated exposure: review recommended.")
        return {"message": "\n".join(lines)}

    # --- Helpers ---

    def _build_context(self):
        """Build context string for Claude."""
        ctx = []
        ctx.append(f"User role: {self.user_role}")
        ctx.append(f"Employees on file: {len(self.employees)}")
        if self.employees:
            roles = set(e.get("role", "") for e in self.employees)
            ctx.append(f"Roles: {', '.join(roles)}")
        if self.schedule_data.get("shifts"):
            ctx.append(f"Current schedule: {len(self.schedule_data['shifts'])} shifts loaded")
        if self.user_employee_id:
            ctx.append(f"Viewing as employee: {self.user_employee_id}")
        return "\n".join(ctx)

    def _execute_action(self, action):
        """Execute an action returned by Claude."""
        action_type = action.get("type")
        params = action.get("params", {})

        if action_type == "generate_schedule":
            return {"status": "schedule_generated"}
        elif action_type == "find_coverage":
            return {"status": "coverage_found"}
        elif action_type == "approve_request":
            return {"status": "approved"}

        return {"status": "unknown_action"}


if __name__ == "__main__":
    from sample_schedule import generate_schedule, EMPLOYEES, EMPLOYEE_HISTORY
    from leave_management import create_demo_leave_tracker

    schedule = generate_schedule()
    tracker = create_demo_leave_tracker()

    # Create chat interface
    chat = AIChat(
        employees=EMPLOYEES,
        schedule_data=schedule,
        leave_tracker=tracker,
        employee_history=EMPLOYEE_HISTORY,
        user_role="MANAGER",
        user_employee_id="E001",
    )

    print("=" * 70)
    print("  CONVERSATIONAL AI ASSISTANT")
    print("  Type your questions (Ctrl+C to exit)")
    print("=" * 70)

    # Demo queries
    demo_queries = [
        "Who can cover tomorrow's shift?",
        "How many hours does James have left this week?",
        "What's my PTO balance?",
        "Show me the fairness report",
        "Are there any compliance violations?",
    ]

    for q in demo_queries:
        print(f"\n  YOU: {q}")
        response = chat.chat(q)
        print(f"\n  AI: {response['message']}")
        print(f"  {'-'*60}")
