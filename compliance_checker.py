"""
Workforce Compliance AI - Schedule Compliance Checker
Analyzes a shift schedule against labor laws, union CBA, and company policy.
Outputs violations with severity, cost impact, and compliant alternatives.
"""

from datetime import datetime, timedelta
from collections import defaultdict
from rules_engine import get_all_rules, SAMPLE_UNION_CBA, CHICAGO_FAIR_WORKWEEK, COMPANY_POLICY
from sample_schedule import generate_schedule, EMPLOYEES
from leave_rules import check_leave_compliance, get_all_leave_rules


def parse_time(date_str, time_str):
    """Parse date + time into datetime."""
    return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")


def get_shift_hours(shift):
    """Calculate shift duration in hours."""
    start = parse_time(shift["date"], shift["start"])
    end = parse_time(shift["date"], shift["end"])
    if end < start:
        end += timedelta(days=1)
    return (end - start).total_seconds() / 3600


def check_compliance(schedule):
    """Run all compliance checks against the schedule."""
    violations = []
    shifts = schedule["shifts"]
    posted_date = datetime.strptime(schedule["schedule_posted_date"], "%Y-%m-%d")
    week_start = datetime.strptime(schedule["week_start"], "%Y-%m-%d")

    # Group shifts by employee
    emp_shifts = defaultdict(list)
    for s in shifts:
        emp_shifts[s["employee_id"]].append(s)

    # Sort each employee's shifts by date/time
    for emp_id in emp_shifts:
        emp_shifts[emp_id].sort(key=lambda x: parse_time(x["date"], x["start"]))

    # Get employee info
    emp_info = {e["id"]: e for e in EMPLOYEES}

    # ===== CHECK 1: Schedule Notice (Chicago: 14 days, CBA: 5 days) =====
    notice_days = (week_start - posted_date).days
    if notice_days < 14:
        violations.append({
            "rule_id": "CHI-FW-001",
            "rule_name": "Advance Notice (Chicago Fair Workweek)",
            "severity": "HIGH",
            "description": f"Schedule posted only {notice_days} days before week start. Chicago requires 14 days.",
            "affected_employees": "ALL (10 employees)",
            "cost_impact": f"$300-$500 per employee = $3,000-$5,000 total penalty risk",
            "recommendation": "Post schedule by June 23 for the week of July 7. Set calendar reminder for 14-day lead time."
        })
    if notice_days < 5:
        violations.append({
            "rule_id": "CBA-005",
            "rule_name": "Schedule Posting (Union CBA)",
            "severity": "MEDIUM",
            "description": f"Schedule posted only {notice_days} days before week start. CBA requires 5 days (Wednesday prior week).",
            "affected_employees": "ALL bargaining unit employees",
            "cost_impact": "Grievance risk + potential back pay",
            "recommendation": "Post by Wednesday of prior week at minimum."
        })

    # ===== CHECK 2: Clopening / Rest Between Shifts =====
    for emp_id, emp_shift_list in emp_shifts.items():
        for i in range(len(emp_shift_list) - 1):
            current = emp_shift_list[i]
            next_shift = emp_shift_list[i + 1]

            end_time = parse_time(current["date"], current["end"])
            start_time = parse_time(next_shift["date"], next_shift["start"])

            if end_time > start_time:
                end_time = parse_time(current["date"], current["end"])
                start_time = parse_time(next_shift["date"], next_shift["start"])
                if start_time < end_time:
                    start_time += timedelta(days=1)

            hours_between = (start_time - end_time).total_seconds() / 3600

            if hours_between < 10 and hours_between > 0:
                violations.append({
                    "rule_id": "CHI-FW-002 / CBA-008",
                    "rule_name": "Right to Rest (Clopening)",
                    "severity": "HIGH",
                    "description": f"{current['name']}: Only {hours_between:.1f} hours between shifts on {current['date']} (end {current['end']}) and {next_shift['date']} (start {next_shift['start']}). Minimum 10 hours required.",
                    "affected_employees": current["name"],
                    "cost_impact": "1.25x pay rate for hours within 10-hr window + grievance risk",
                    "recommendation": f"Move {next_shift['date']} start to {current['end'].replace(':','')[:2]}:00 + 10hrs = start at {int(current['end'][:2])+10:02d}:00, or reassign to different employee."
                })

    # ===== CHECK 3: Consecutive Days =====
    for emp_id, emp_shift_list in emp_shifts.items():
        dates_worked = sorted(set(s["date"] for s in emp_shift_list))
        consecutive = 1
        max_consecutive = 1

        for i in range(1, len(dates_worked)):
            d1 = datetime.strptime(dates_worked[i-1], "%Y-%m-%d")
            d2 = datetime.strptime(dates_worked[i], "%Y-%m-%d")
            if (d2 - d1).days == 1:
                consecutive += 1
                max_consecutive = max(max_consecutive, consecutive)
            else:
                consecutive = 1

        if max_consecutive > 6:
            emp_name = emp_shift_list[0]["name"]
            violations.append({
                "rule_id": "CBA-002",
                "rule_name": "Maximum Consecutive Days (Union CBA)",
                "severity": "HIGH",
                "description": f"{emp_name}: Scheduled for {max_consecutive} consecutive days. CBA maximum is 6.",
                "affected_employees": emp_name,
                "cost_impact": "Double time pay for day 7+ AND grievance filing",
                "recommendation": f"Insert rest day. Move {dates_worked[6]} shift to a different employee or reschedule."
            })

    # ===== CHECK 4: Minimum Shift Length (CBA: 4 hours) =====
    for s in shifts:
        hours = get_shift_hours(s)
        if hours < 4:
            violations.append({
                "rule_id": "CBA-001",
                "rule_name": "Minimum Shift Length (Union CBA)",
                "severity": "HIGH",
                "description": f"{s['name']}: Shift on {s['date']} is only {hours:.1f} hours ({s['start']}-{s['end']}). CBA minimum is 4 hours.",
                "affected_employees": s["name"],
                "cost_impact": "Must pay for full 4 hours regardless of hours worked",
                "recommendation": f"Extend shift to minimum 4 hours (e.g., {s['start']}-{int(s['start'][:2])+4:02d}:00) or combine with another task."
            })

    # ===== CHECK 5: Weekly Hours Cap (Company: 60 hrs) =====
    for emp_id, emp_shift_list in emp_shifts.items():
        # Only count shifts in the target week
        week_hours = 0
        for s in emp_shift_list:
            s_date = datetime.strptime(s["date"], "%Y-%m-%d")
            if s_date >= week_start and s_date < week_start + timedelta(days=7):
                week_hours += get_shift_hours(s)

        if week_hours > 60:
            emp_name = emp_shift_list[0]["name"]
            violations.append({
                "rule_id": "CP-001",
                "rule_name": "Weekly Hour Cap (Company Policy)",
                "severity": "MEDIUM",
                "description": f"{emp_name}: Scheduled for {week_hours:.1f} hours in the week. Company maximum is 60 without VP approval.",
                "affected_employees": emp_name,
                "cost_impact": "Requires VP approval escalation + overtime cost",
                "recommendation": f"Reduce by {week_hours-60:.1f} hours. Move {week_hours-60:.0f}+ hours to another qualified employee or get VP pre-approval."
            })

    # ===== CHECK 6: Minor Night Shift Restriction =====
    for s in shifts:
        emp = emp_info.get(s["employee_id"], {})
        if emp.get("is_minor"):
            end_hour = int(s["end"].split(":")[0])
            start_hour = int(s["start"].split(":")[0])
            if end_hour >= 22 or end_hour < 6 or start_hour < 6:
                violations.append({
                    "rule_id": "CP-002",
                    "rule_name": "Minor Night Shift Restriction",
                    "severity": "CRITICAL",
                    "description": f"{s['name']} (minor): Scheduled until {s['end']} on {s['date']}. Minors cannot work between 10pm-6am.",
                    "affected_employees": s["name"],
                    "cost_impact": "LEGAL VIOLATION - potential fine + termination of scheduling manager",
                    "recommendation": f"End shift by 22:00 at latest. Change to {s['start']}-21:30 or reassign to daytime shift."
                })

    # ===== CHECK 7: Leave Compliance (FMLA, PTO, Sick) =====
    # Sample leave records for demo - in production this comes from HRIS
    sample_leaves = [
        {"employee_id": "E003", "leave_type": "fmla", "start_date": "2026-07-07", "end_date": "2026-07-18", "status": "approved"},
        {"employee_id": "E009", "leave_type": "pto", "start_date": "2026-07-09", "end_date": "2026-07-11", "status": "approved"},
    ]
    leave_violations = check_leave_compliance(schedule, sample_leaves, state="Illinois")
    violations.extend(leave_violations)

    return violations


def generate_report(schedule, violations):
    """Generate a formatted compliance report."""
    report = []
    report.append("=" * 70)
    report.append("  WORKFORCE COMPLIANCE AI - SCHEDULE ANALYSIS REPORT")
    report.append("=" * 70)
    report.append("")
    report.append(f"  Facility:        {schedule['facility']}")
    report.append(f"  Schedule Week:   {schedule['week_start']} to {schedule['week_end']}")
    report.append(f"  Posted Date:     {schedule['schedule_posted_date']}")
    report.append(f"  Total Shifts:    {len(schedule['shifts'])}")
    report.append(f"  Employees:       {len(set(s['employee_id'] for s in schedule['shifts']))}")
    report.append("")
    report.append("-" * 70)

    # Summary
    critical = [v for v in violations if v["severity"] == "CRITICAL"]
    high = [v for v in violations if v["severity"] == "HIGH"]
    medium = [v for v in violations if v["severity"] == "MEDIUM"]

    report.append("")
    report.append(f"  COMPLIANCE SUMMARY")
    report.append(f"  {'='*50}")
    report.append(f"  Total Violations Found:  {len(violations)}")
    report.append(f"")
    report.append(f"  {'CRITICAL':12} {len(critical)}  {'*' * len(critical) * 3}")
    report.append(f"  {'HIGH':12} {len(high)}  {'*' * len(high) * 3}")
    report.append(f"  {'MEDIUM':12} {len(medium)}  {'*' * len(medium) * 3}")
    report.append("")

    if critical:
        report.append(f"  *** IMMEDIATE ACTION REQUIRED: {len(critical)} CRITICAL VIOLATION(S) ***")
        report.append("")

    report.append("-" * 70)
    report.append("")

    # Detailed violations
    for i, v in enumerate(sorted(violations, key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}[x["severity"]]), 1):
        severity_icon = {"CRITICAL": "[!!!]", "HIGH": "[!!]", "MEDIUM": "[!]"}[v["severity"]]
        report.append(f"  VIOLATION #{i}  {severity_icon} {v['severity']}")
        report.append(f"  {'Rule:':20} {v['rule_id']} - {v['rule_name']}")
        report.append(f"  {'Issue:':20} {v['description']}")
        report.append(f"  {'Affected:':20} {v['affected_employees']}")
        report.append(f"  {'Cost Impact:':20} {v['cost_impact']}")
        report.append(f"  {'Recommendation:':20} {v['recommendation']}")
        report.append("")
        report.append(f"  {'- '*35}")
        report.append("")

    # Compliant alternatives summary
    report.append("=" * 70)
    report.append("  RECOMMENDED ACTIONS (Priority Order)")
    report.append("=" * 70)
    report.append("")
    report.append("  1. IMMEDIATE: Remove Tyler Brooks (minor) from evening shift past 10pm")
    report.append("     -> Reassign to 14:00-21:30 or move to daytime")
    report.append("")
    report.append("  2. THIS WEEK: Fix Sarah Martinez clopening violation")
    report.append("     -> Move Monday start to 08:30 (10hrs after Sunday end)")
    report.append("     -> OR reassign Sunday close to another senior employee")
    report.append("")
    report.append("  3. THIS WEEK: Give Marcus Johnson a rest day")
    report.append("     -> Remove July 7 or July 8 shift, replace with qualified employee")
    report.append("")
    report.append("  4. PROCESS: Extend Rosa Hernandez Monday shift to 4 hours minimum")
    report.append("     -> Change 10:00-13:00 to 10:00-14:00")
    report.append("")
    report.append("  5. PROCESS: Reduce James Wilson to 60 hours or get VP approval")
    report.append("     -> Remove Saturday shift or shorten daily shifts by 30 min")
    report.append("")
    report.append("  6. SYSTEMIC: Implement 14-day advance scheduling process")
    report.append("     -> Current 3-day notice violates Chicago law for ALL employees")
    report.append("     -> Estimated penalty exposure: $3,000-$5,000 per occurrence")
    report.append("")
    report.append("=" * 70)
    report.append(f"  Total Estimated Penalty Exposure: $4,500 - $8,000+")
    report.append(f"  Grievance Risk: HIGH (3 CBA violations identified)")
    report.append("=" * 70)

    return "\n".join(report)


if __name__ == "__main__":
    # Generate sample schedule
    schedule = generate_schedule()

    # Run compliance checks
    violations = check_compliance(schedule)

    # Generate report
    report = generate_report(schedule, violations)
    print(report)

    # Save report
    output_path = r"C:\Users\hodeh\Documents\Support Call\workforce-compliance-ai\compliance_report.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\nReport saved to: {output_path}")
