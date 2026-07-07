"""
Workforce Compliance AI - AI Reasoning Module
Uses Claude (Anthropic SDK) for natural language compliance reasoning,
schedule analysis, and intelligent violation detection.
"""

import os
import json

try:
    import anthropic
except ImportError:
    print("=" * 60)
    print("  ERROR: The 'anthropic' package is not installed.")
    print("  Please install it with:")
    print("")
    print("    pip install anthropic")
    print("")
    print("  You also need an API key. Set it as an environment variable:")
    print("")
    print("    set ANTHROPIC_API_KEY=your-api-key-here   (Windows)")
    print("    export ANTHROPIC_API_KEY=your-api-key-here (Linux/Mac)")
    print("=" * 60)
    raise SystemExit(1)


# --- Configuration ---
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096


def _get_client():
    """Create and return an Anthropic client. Validates API key is set."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("=" * 60)
        print("  WARNING: ANTHROPIC_API_KEY environment variable is not set.")
        print("")
        print("  To use AI-powered compliance reasoning, set your API key:")
        print("")
        print("    set ANTHROPIC_API_KEY=your-api-key-here   (Windows)")
        print("    export ANTHROPIC_API_KEY=your-api-key-here (Linux/Mac)")
        print("")
        print("  Get an API key at: https://console.anthropic.com/")
        print("=" * 60)
        return None
    return anthropic.Anthropic(api_key=api_key)


def _format_schedule_for_prompt(schedule):
    """Format the schedule data into a readable string for the AI prompt."""
    lines = []
    lines.append(f"Facility: {schedule['facility']}")
    lines.append(f"Week: {schedule['week_start']} to {schedule['week_end']}")
    lines.append(f"Schedule Posted Date: {schedule['schedule_posted_date']}")
    lines.append(f"Total Shifts: {len(schedule['shifts'])}")
    lines.append("")
    lines.append("SHIFT DETAILS:")
    lines.append("-" * 80)
    lines.append(f"{'Employee':<20} {'Date':<12} {'Start':<7} {'End':<7} {'Role':<8} {'Type':<10}")
    lines.append("-" * 80)
    for s in sorted(schedule["shifts"], key=lambda x: (x["employee_id"], x["date"], x["start"])):
        lines.append(
            f"{s['name']:<20} {s['date']:<12} {s['start']:<7} {s['end']:<7} "
            f"{s['role']:<8} {s['shift_type']:<10}"
        )
    return "\n".join(lines)


def _format_violations_for_prompt(violations):
    """Format detected violations into a readable string for the AI prompt."""
    if not violations:
        return "No violations detected by the rule-based checker."
    lines = []
    for i, v in enumerate(violations, 1):
        lines.append(f"Violation #{i}:")
        lines.append(f"  Rule ID: {v['rule_id']}")
        lines.append(f"  Rule Name: {v['rule_name']}")
        lines.append(f"  Severity: {v['severity']}")
        lines.append(f"  Description: {v['description']}")
        lines.append(f"  Affected: {v['affected_employees']}")
        lines.append(f"  Cost Impact: {v['cost_impact']}")
        lines.append(f"  Recommendation: {v['recommendation']}")
        lines.append("")
    return "\n".join(lines)


def _format_rules_for_prompt(rules):
    """Format compliance rules into a readable string for the AI prompt."""
    lines = []
    for r in rules:
        lines.append(f"[{r['id']}] {r['name']} (Severity: {r['severity']})")
        lines.append(f"   Description: {r['description']}")
        lines.append(f"   Requirement: {r['requirement']}")
        lines.append(f"   Penalty: {r['penalty']}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def analyze_with_ai(schedule, violations, rules):
    """
    Use Claude to perform deep compliance analysis.

    Asks Claude to:
    (a) Confirm or refute each violation found by the rule-based checker
    (b) Identify any ADDITIONAL violations the rule-based checker might have missed
    (c) Suggest the optimal set of schedule changes that fixes all violations
        with minimum disruption
    (d) Estimate total cost impact

    Args:
        schedule: The schedule dict (from generate_schedule())
        violations: List of violation dicts (from check_compliance())
        rules: List of rule dicts (from get_all_rules())

    Returns:
        str: The AI's structured analysis text, or an error message.
    """
    client = _get_client()
    if not client:
        return "[AI Analysis unavailable - API key not configured]"

    schedule_text = _format_schedule_for_prompt(schedule)
    violations_text = _format_violations_for_prompt(violations)
    rules_text = _format_rules_for_prompt(rules)

    prompt = f"""You are an expert workforce compliance analyst specializing in U.S. labor law,
union collective bargaining agreements (CBAs), and corporate scheduling policies.

I need you to perform a thorough compliance audit of the following shift schedule.

=== APPLICABLE RULES AND REGULATIONS ===
{rules_text}

=== SCHEDULE DATA ===
{schedule_text}

=== VIOLATIONS DETECTED BY RULE-BASED CHECKER ===
{violations_text}

=== YOUR ANALYSIS TASKS ===

Please provide a structured analysis covering ALL of the following:

## (A) VIOLATION CONFIRMATION / REFUTATION

For EACH violation listed above, confirm or refute it by citing the specific rule ID
and the exact schedule data that constitutes the violation. If a violation is incorrectly
flagged (false positive), explain why with reference to the rule's actual requirements.

Format each as:
- [CONFIRMED/REFUTED] Rule {{rule_id}}: {{brief explanation citing specific times/dates/hours}}

## (B) ADDITIONAL VIOLATIONS MISSED BY THE RULE-BASED CHECKER

Examine the schedule for violations the automated checker may have missed. Consider:
- CHI-FW-003 (Predictability Pay) implications
- CBA-003 (Seniority-Based Shift Assignment) - are preferred shifts going to junior employees?
- CBA-004 (Overtime Distribution) - is overtime equitably distributed?
- CBA-006 (Mandatory OT Limit) - does any employee exceed 12 hours of mandatory OT?
- CBA-007 (Split Shift Prohibition) - any unreported split shifts?
- CP-003 (Training/Certification) - any role mismatches?
- Potential meal break issues for long shifts (if CA rules applied)

For each new violation found, cite the specific rule ID and the schedule data.

## (C) OPTIMAL SCHEDULE MODIFICATIONS

Propose the minimum set of changes that resolves ALL violations (both confirmed existing
and newly identified) while:
1. Maintaining required staffing levels for each shift period
2. Minimizing disruption (fewest employee schedule changes)
3. Respecting seniority preferences (CBA-003)
4. Staying within all hour limits

For each change, specify:
- Which employee's shift is being modified
- The exact before and after (date, start time, end time)
- Which violation(s) this resolves
- Any ripple effects on other employees

## (D) TOTAL COST IMPACT ESTIMATE

Provide a breakdown of:
1. Current penalty exposure (fines, premium pay owed, grievance costs)
2. Cost of implementing the recommended changes (overtime shifts, additional staffing)
3. Net savings from becoming compliant
4. Risk-adjusted total (probability-weighted penalties if no action taken)

Be specific with dollar amounts where the rules provide penalty rates."""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except anthropic.APIConnectionError:
        return "[AI Analysis failed - Could not connect to the Anthropic API. Check your internet connection.]"
    except anthropic.AuthenticationError:
        return "[AI Analysis failed - Invalid API key. Please check your ANTHROPIC_API_KEY.]"
    except anthropic.RateLimitError:
        return "[AI Analysis failed - Rate limit exceeded. Please wait and try again.]"
    except anthropic.APIStatusError as e:
        return f"[AI Analysis failed - API error: {e.status_code} {e.message}]"


def ask_compliance_question(question, schedule, rules):
    """
    Answer a natural language compliance question in context.

    Takes a question like "If I move Sarah's shift to 8am, does that fix the
    clopening issue?" and provides a contextual answer based on the schedule
    and applicable rules.

    Args:
        question: Natural language question from the user.
        schedule: The schedule dict.
        rules: List of rule dicts.

    Returns:
        str: Natural language answer from Claude, or an error message.
    """
    client = _get_client()
    if not client:
        return "[AI Q&A unavailable - API key not configured]"

    schedule_text = _format_schedule_for_prompt(schedule)
    rules_text = _format_rules_for_prompt(rules)

    prompt = f"""You are an expert workforce compliance advisor. A scheduling manager has a
question about their shift schedule. Answer it clearly, citing specific rule IDs and
schedule data where relevant.

=== APPLICABLE RULES ===
{rules_text}

=== CURRENT SCHEDULE ===
{schedule_text}

=== MANAGER'S QUESTION ===
{question}

=== INSTRUCTIONS ===
Provide a clear, actionable answer. If the question involves a proposed change:
1. Determine if the proposed change fixes the issue cited
2. Check whether the proposed change creates any NEW violations
3. Suggest the best alternative if the proposal doesn't fully resolve the issue
4. Cite specific rule IDs (e.g., CHI-FW-002, CBA-008) in your reasoning

Keep your answer concise but thorough. Use bullet points for multiple findings."""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except anthropic.APIConnectionError:
        return "[AI Q&A failed - Could not connect to the Anthropic API.]"
    except anthropic.AuthenticationError:
        return "[AI Q&A failed - Invalid API key. Please check your ANTHROPIC_API_KEY.]"
    except anthropic.RateLimitError:
        return "[AI Q&A failed - Rate limit exceeded. Please wait and try again.]"
    except anthropic.APIStatusError as e:
        return f"[AI Q&A failed - API error: {e.status_code} {e.message}]"


def generate_compliant_schedule(schedule, violations):
    """
    Ask Claude to propose a fully compliant alternative schedule.

    Returns a modified schedule as a list of shift dicts that resolves all
    identified violations while maintaining operational coverage.

    Args:
        schedule: The current schedule dict.
        violations: List of violation dicts from the compliance checker.

    Returns:
        list: A list of shift dicts representing the compliant schedule,
              or the original shifts list if AI is unavailable.
    """
    client = _get_client()
    if not client:
        print("[AI Schedule Generation unavailable - API key not configured]")
        return schedule["shifts"]

    schedule_text = _format_schedule_for_prompt(schedule)
    violations_text = _format_violations_for_prompt(violations)

    prompt = f"""You are an expert workforce scheduler. Given the following schedule and its
compliance violations, generate a FULLY COMPLIANT alternative schedule.

=== CURRENT SCHEDULE ===
{schedule_text}

=== VIOLATIONS TO FIX ===
{violations_text}

=== CONSTRAINTS ===
1. The schedule must cover the same week: {schedule['week_start']} to {schedule['week_end']}
2. Maintain similar total staffing hours per day (do not drastically reduce coverage)
3. Each shift must be at least 4 hours (CBA-001)
4. No employee works more than 6 consecutive days (CBA-002)
5. Minimum 10 hours between shifts for each employee (CHI-FW-002 / CBA-008)
6. No minor (Tyler Brooks, E006) scheduled past 22:00 or before 06:00 (CP-002)
7. No employee exceeds 60 hours in the week without notation (CP-001)
8. The schedule_posted_date should be at least 14 days before week_start (CHI-FW-001)
9. Respect seniority for preferred shifts where possible (CBA-003)

=== OUTPUT FORMAT ===
Return ONLY a JSON array of shift objects. Each shift must have exactly these fields:
- "employee_id": string (e.g., "E001")
- "name": string (employee full name)
- "date": string in "YYYY-MM-DD" format
- "start": string in "HH:MM" 24-hour format
- "end": string in "HH:MM" 24-hour format
- "role": string (Pick, Pack, Stow, or Ship)
- "shift_type": string (Open, Day, Evening, Close, Short)

Return ONLY the JSON array, no additional text or explanation before or after it."""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text.strip()

        # Extract JSON from the response (handle potential markdown code blocks)
        if response_text.startswith("```"):
            # Remove markdown code fences
            lines = response_text.split("\n")
            json_lines = []
            in_block = False
            for line in lines:
                if line.strip().startswith("```"):
                    in_block = not in_block
                    continue
                if in_block:
                    json_lines.append(line)
            response_text = "\n".join(json_lines)

        shifts = json.loads(response_text)

        # Validate the structure
        required_keys = {"employee_id", "name", "date", "start", "end", "role", "shift_type"}
        for shift in shifts:
            if not required_keys.issubset(shift.keys()):
                missing = required_keys - set(shift.keys())
                print(f"[Warning] AI-generated shift missing keys: {missing}")
                return schedule["shifts"]

        return shifts

    except json.JSONDecodeError as e:
        print(f"[AI Schedule Generation failed - Could not parse AI response as JSON: {e}]")
        return schedule["shifts"]
    except anthropic.APIConnectionError:
        print("[AI Schedule Generation failed - Could not connect to the Anthropic API.]")
        return schedule["shifts"]
    except anthropic.AuthenticationError:
        print("[AI Schedule Generation failed - Invalid API key.]")
        return schedule["shifts"]
    except anthropic.RateLimitError:
        print("[AI Schedule Generation failed - Rate limit exceeded.]")
        return schedule["shifts"]
    except anthropic.APIStatusError as e:
        print(f"[AI Schedule Generation failed - API error: {e.status_code} {e.message}]")
        return schedule["shifts"]


# ---------------------------------------------------------------------------
# Demonstration
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    from sample_schedule import generate_schedule
    from compliance_checker import check_compliance
    from rules_engine import get_all_rules

    print("=" * 70)
    print("  WORKFORCE COMPLIANCE AI - AI REASONING MODULE DEMO")
    print("=" * 70)
    print()

    # Generate sample data
    schedule = generate_schedule()
    violations = check_compliance(schedule)
    rules = get_all_rules("Chicago")

    print(f"  Schedule: {schedule['facility']}")
    print(f"  Week: {schedule['week_start']} to {schedule['week_end']}")
    print(f"  Violations found by rule-based checker: {len(violations)}")
    print()

    # --- Demo 1: Full AI Analysis ---
    print("-" * 70)
    print("  [1] FULL AI COMPLIANCE ANALYSIS")
    print("-" * 70)
    print()
    print("  Sending schedule to Claude for deep analysis...")
    print()

    analysis = analyze_with_ai(schedule, violations, rules)
    print(analysis)
    print()

    # --- Demo 2: Natural Language Q&A ---
    print("-" * 70)
    print("  [2] NATURAL LANGUAGE COMPLIANCE Q&A")
    print("-" * 70)
    print()

    questions = [
        "If I move Sarah's Monday shift start to 08:30, does that fix the clopening issue?",
        "Can Tyler Brooks work until 9:30pm instead of 10:30pm and still be compliant?",
        "What is the cheapest way to fix Marcus Johnson's consecutive days violation?",
    ]

    for q in questions:
        print(f"  Q: {q}")
        print()
        answer = ask_compliance_question(q, schedule, rules)
        print(f"  A: {answer}")
        print()
        print("  " + "-" * 60)
        print()

    # --- Demo 3: Generate Compliant Schedule ---
    print("-" * 70)
    print("  [3] AI-GENERATED COMPLIANT SCHEDULE")
    print("-" * 70)
    print()
    print("  Asking Claude to generate a fully compliant alternative schedule...")
    print()

    new_shifts = generate_compliant_schedule(schedule, violations)

    if new_shifts != schedule["shifts"]:
        print(f"  Generated {len(new_shifts)} shifts in compliant schedule.")
        print()
        print(f"  {'Employee':<20} {'Date':<12} {'Start':<7} {'End':<7} {'Role':<8} {'Type':<10}")
        print(f"  {'-'*74}")
        for s in sorted(new_shifts, key=lambda x: (x["employee_id"], x["date"], x["start"])):
            print(
                f"  {s['name']:<20} {s['date']:<12} {s['start']:<7} {s['end']:<7} "
                f"{s['role']:<8} {s['shift_type']:<10}"
            )
        print()
        print("  Re-running compliance check on AI-generated schedule...")
        new_schedule = {
            "schedule_posted_date": "2026-06-23",  # Fixed: 14 days before week start
            "week_start": schedule["week_start"],
            "week_end": schedule["week_end"],
            "facility": schedule["facility"],
            "shifts": new_shifts
        }
        new_violations = check_compliance(new_schedule)
        print(f"  Violations in AI-generated schedule: {len(new_violations)}")
        if new_violations:
            for v in new_violations:
                print(f"    - [{v['severity']}] {v['rule_id']}: {v['description'][:80]}")
    else:
        print("  [Could not generate alternative schedule - see error above]")

    print()
    print("=" * 70)
    print("  Demo complete.")
    print("=" * 70)
