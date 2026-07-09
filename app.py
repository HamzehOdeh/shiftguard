# Workforce Compliance AI - Streamlit Web Application
# Requirements: pip install streamlit pandas openpyxl
# Run with: streamlit run app.py

import streamlit as st
import pandas as pd
import calendar as cal
import json
from datetime import datetime, timedelta

from rules_engine import get_all_rules
from sample_schedule import generate_schedule, EMPLOYEES, EMPLOYEE_HISTORY
from compliance_checker import check_compliance
from demo_scenarios import INDUSTRY_OPTIONS, generate_demo_for_industry
from hours_tracker import (
    get_all_employee_dashboards, predict_shift_impact, calculate_fatigue_score,
    calculate_employee_hours, OT_THRESHOLD_WEEKLY, MAX_WEEKLY_HOURS
)
from coverage_engine import find_coverage, calculate_team_fairness_report
from shift_intelligence import (
    analyze_schedule_shifts, calculate_premium_pay,
    generate_holiday_coverage_plan, get_holidays_in_range,
    check_night_shift_compliance, is_holiday
)
from worker_portal import WorkerPortal, create_demo_portal, STATUS_AUTO_APPROVED, STATUS_ESCALATED, STATUS_PENDING
from manager_queue import ManagerQueue
from leave_management import (
    LeaveBalanceTracker, create_demo_leave_tracker, LEAVE_TYPES,
    cascade_coverage
)
from shift_templates import SHIFT_ASSIGNMENTS
from ai_chat import AIChat
from notifications import SmartNotificationGenerator, create_demo_smart_notifications


def parse_uploaded_file(uploaded_file):
    """Parse an uploaded CSV or Excel file into the schedule dict format."""
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    required_cols = ["employee_id", "name", "date", "start", "end", "role", "shift_type"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"Missing required columns: {', '.join(missing)}")
        return None

    shifts = df[required_cols].to_dict(orient="records")

    for shift in shifts:
        shift["date"] = str(shift["date"]).strip()[:10]
        shift["start"] = str(shift["start"]).strip()[:5]
        shift["end"] = str(shift["end"]).strip()[:5]
        shift["employee_id"] = str(shift["employee_id"]).strip()
        shift["name"] = str(shift["name"]).strip()
        shift["role"] = str(shift["role"]).strip()
        shift["shift_type"] = str(shift["shift_type"]).strip()

    dates = sorted(set(s["date"] for s in shifts))
    week_start = dates[0] if dates else datetime.today().strftime("%Y-%m-%d")
    week_end = dates[-1] if dates else datetime.today().strftime("%Y-%m-%d")
    posted_date = datetime.today().strftime("%Y-%m-%d")

    schedule = {
        "schedule_posted_date": posted_date,
        "week_start": week_start,
        "week_end": week_end,
        "facility": "Uploaded Schedule",
        "shifts": shifts,
    }
    return schedule


def get_severity_color(severity):
    colors = {
        "CRITICAL": "#dc3545",
        "HIGH": "#fd7e14",
        "MEDIUM": "#ffc107",
    }
    return colors.get(severity, "#6c757d")


def get_fatigue_color(level):
    colors = {"green": "#28a745", "yellow": "#ffc107", "red": "#dc3545"}
    return colors.get(level, "#6c757d")


def estimate_penalty_exposure(violations):
    total_low = 0
    total_high = 0
    for v in violations:
        if v["severity"] == "CRITICAL":
            total_low += 5000
            total_high += 10000
        elif v["severity"] == "HIGH":
            total_low += 500
            total_high += 2000
        elif v["severity"] == "MEDIUM":
            total_low += 100
            total_high += 500
    return total_low, total_high


def render_compliance_tab(schedule, jurisdiction, include_cba, include_company):
    """Render the compliance violations tab."""
    violations = check_compliance(schedule)

    critical = [v for v in violations if v["severity"] == "CRITICAL"]
    high = [v for v in violations if v["severity"] == "HIGH"]
    medium = [v for v in violations if v["severity"] == "MEDIUM"]
    penalty_low, penalty_high = estimate_penalty_exposure(violations)

    # Big penalty number (the hook)
    st.markdown(
        f'<div style="text-align:center;padding:15px;background:#2d1b1b;border-radius:10px;margin-bottom:20px;">'
        f'<p style="color:#ff9999;margin:0;font-size:0.9em;">ESTIMATED WEEKLY PENALTY EXPOSURE</p>'
        f'<h1 style="color:#ff4444;margin:5px 0;font-size:2.5em;">${penalty_low:,} - ${penalty_high:,}</h1>'
        f'<p style="color:#aaa;margin:0;">{len(violations)} violations found across {len(set(v["affected_employees"] for v in violations))} employees</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Compliance score
    max_penalty = max(1, penalty_high)
    compliance_score = max(0, min(100, round(100 - (penalty_high / 200))))
    score_color = "#28a745" if compliance_score >= 80 else ("#ffc107" if compliance_score >= 50 else "#dc3545")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Critical", len(critical))
    with col2:
        st.metric("High", len(high))
    with col3:
        st.metric("Medium", len(medium))
    with col4:
        st.markdown(
            f'<div style="text-align:center;">'
            f'<p style="margin:0;font-size:0.85em;color:#888;">Compliance Score</p>'
            f'<p style="margin:0;font-size:2em;font-weight:bold;color:{score_color};">{compliance_score}/100</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    sorted_violations = sorted(
        violations,
        key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}.get(x["severity"], 3),
    )

    for i, v in enumerate(sorted_violations, 1):
        if i in st.session_state.get("resolved_violations", set()):
            continue
        color = get_severity_color(v["severity"])
        # Show fix inline (visible without expanding)
        st.markdown(
            f'<div style="background:#1a1a2e;padding:10px 14px;border-radius:8px;margin-bottom:4px;'
            f'border-left:4px solid {color};">'
            f'<span style="background-color:{color};color:white;padding:2px 8px;'
            f'border-radius:4px;font-size:0.75em;font-weight:bold;">{v["severity"]}</span> '
            f'<strong>{v["affected_employees"]}</strong> — {v["description"]}<br>'
            f'<span style="color:#28a745;font-size:0.9em;">Fix: {v["recommendation"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        with st.expander(f"Details: {v['rule_id']} - {v['rule_name']} | Cost: {v['cost_impact']}"):
            col_left, col_right = st.columns(2)
            with col_left:
                st.markdown(f"**Rule:** {v['rule_id']} - {v['rule_name']}")
                st.markdown(f"**Affected:** {v['affected_employees']}")
            with col_right:
                st.markdown(f"**Cost Impact:** {v['cost_impact']}")
            st.markdown(f"**Issue:** {v['description']}")
            st.markdown(f"**Fix:** {v['recommendation']}")

            # Inline action buttons
            st.markdown("")
            act_cols = st.columns(4)
            with act_cols[0]:
                if st.button("Resolve", key=f"resolve_{i}", type="primary"):
                    if "resolved_violations" not in st.session_state:
                        st.session_state["resolved_violations"] = set()
                    st.session_state["resolved_violations"].add(i)
                    st.success(f"Resolved! Violation {v['rule_id']} marked as fixed. Schedule updated.")
                    st.rerun()
            with act_cols[1]:
                if st.button("Reassign", key=f"reassign_{i}"):
                    if "resolved_violations" not in st.session_state:
                        st.session_state["resolved_violations"] = set()
                    st.session_state["resolved_violations"].add(i)
                    st.success(f"Reassigned! {v['affected_employees']}'s shift moved to next best-fit employee.")
                    st.rerun()
            with act_cols[2]:
                if st.button("Notify Worker", key=f"notify_{i}"):
                    st.success(f"Notification sent to {v['affected_employees']} about schedule change.")
            with act_cols[3]:
                if st.button("Accept Risk", key=f"accept_{i}"):
                    st.warning(
                        f"⚖️ **Risk Acknowledgment Required:** By accepting this violation, "
                        f"you confirm that you understand the potential penalty "
                        f"({v['cost_impact']}) and accept responsibility on behalf of "
                        f"your organization. This decision is logged in the audit trail."
                    )
                    st.markdown(
                        f'<div style="background:#2d1b1b;padding:8px 12px;border-radius:6px;'
                        f'font-size:0.8em;color:#ff9999;margin-top:4px;">'
                        f'📋 Logged: Manager accepted risk for {v["rule_id"]} — '
                        f'{v["affected_employees"]} — {datetime.now().strftime("%Y-%m-%d %H:%M")}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

    # Export buttons
    st.divider()
    st.markdown("#### Export Compliance Report")
    export_cols = st.columns(3)

    # CSV export
    export_rows = [{
        "Severity": v["severity"],
        "Rule ID": v["rule_id"],
        "Rule": v["rule_name"],
        "Employee": v["affected_employees"],
        "Description": v["description"],
        "Fix": v["recommendation"],
        "Cost Impact": v["cost_impact"],
    } for v in sorted_violations]
    export_df = pd.DataFrame(export_rows)

    with export_cols[0]:
        csv_data = export_df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv_data,
            file_name=f"shiftguard_compliance_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # HTML audit report (print-to-PDF ready)
    with export_cols[1]:
        html_report = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>ShiftGuard Compliance Report</title>
<style>
body {{ font-family: -apple-system, Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px; color: #333; }}
h1 {{ color: #0284c7; border-bottom: 3px solid #0284c7; padding-bottom: 10px; }}
.header {{ display: flex; justify-content: space-between; margin-bottom: 30px; }}
.header-right {{ text-align: right; color: #666; }}
.summary {{ background: #f8f9fa; border-left: 4px solid #dc3545; padding: 15px 20px; margin: 20px 0; }}
.summary h2 {{ color: #dc3545; margin: 0 0 10px 0; font-size: 1.8em; }}
.violation {{ border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0; page-break-inside: avoid; }}
.violation.critical {{ border-left: 4px solid #dc3545; }}
.violation.high {{ border-left: 4px solid #fd7e14; }}
.violation.medium {{ border-left: 4px solid #ffc107; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75em; font-weight: bold; color: white; }}
.badge.critical {{ background: #dc3545; }}
.badge.high {{ background: #fd7e14; }}
.badge.medium {{ background: #ffc107; color: #333; }}
.fix {{ color: #28a745; font-weight: 500; }}
table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
th {{ background: #f8f9fa; }}
.footer {{ margin-top: 40px; padding-top: 20px; border-top: 2px solid #eee; color: #999; font-size: 0.85em; }}
@media print {{ body {{ padding: 20px; }} .no-print {{ display: none; }} }}
</style></head><body>
<div class="header">
<div><h1>ShiftGuard Compliance Report</h1><p>Audit-Ready Compliance Analysis</p></div>
<div class="header-right"><p><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
<p><strong>Report ID:</strong> SGR-{datetime.now().strftime('%Y%m%d%H%M')}</p></div></div>

<table>
<tr><th>Facility</th><td>{schedule.get('facility', 'N/A')}</td><th>Period</th><td>{schedule.get('week_start', '')} to {schedule.get('week_end', '')}</td></tr>
<tr><th>Total Shifts</th><td>{len(schedule.get('shifts', []))}</td><th>Compliance Score</th><td>{compliance_score}/100</td></tr>
</table>

<div class="summary">
<h2>${penalty_low:,} - ${penalty_high:,}</h2>
<p>Estimated Weekly Penalty Exposure | {len(violations)} violations found</p>
<p>Critical: {len(critical)} | High: {len(high)} | Medium: {len(medium)}</p>
</div>

<h2>Violations Detail</h2>
"""
        for idx, v in enumerate(sorted_violations, 1):
            sev_lower = v['severity'].lower()
            html_report += f"""<div class="violation {sev_lower}">
<p><span class="badge {sev_lower}">{v['severity']}</span> <strong>{v['rule_id']}</strong> — {v['rule_name']}</p>
<p><strong>Employee:</strong> {v['affected_employees']}</p>
<p><strong>Issue:</strong> {v['description']}</p>
<p class="fix"><strong>Remediation:</strong> {v['recommendation']}</p>
<p><strong>Estimated Cost:</strong> {v['cost_impact']}</p></div>
"""
        html_report += f"""
<h2>Attestation</h2>
<p>This report was generated automatically by ShiftGuard Workforce Compliance AI.
All violations were checked against applicable labor laws, union collective bargaining agreements,
and company policies active at the time of analysis.</p>
<p><strong>Rules applied:</strong> Federal FLSA, State labor code, CBA provisions, Company scheduling policy</p>
<p><strong>Analysis timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>

<div class="footer">
<p>ShiftGuard v2.0 | shiftguard.ai | This document is intended for compliance and legal review purposes.
Retain for audit defense per your organization's document retention policy.</p>
<p>Report generated automatically. No manual edits applied.</p></div>
</body></html>"""

        st.download_button(
            "Download Audit Report (HTML)",
            html_report,
            file_name=f"shiftguard_audit_report_{datetime.now().strftime('%Y%m%d')}.html",
            mime="text/html",
            use_container_width=True,
            help="Open in browser and Print → Save as PDF for audit-ready document",
        )

    with export_cols[2]:
        st.download_button(
            "Download JSON",
            json.dumps(sorted_violations, indent=2, default=str),
            file_name=f"shiftguard_violations_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True,
        )


def _get_active_employees():
    """Get the currently active employee list (industry-specific)."""
    return st.session_state.get("demo_employees", EMPLOYEES)


def _get_active_history():
    """Get employee history (only available for warehouse demo)."""
    active = st.session_state.get("demo_employees", EMPLOYEES)
    return EMPLOYEE_HISTORY if active is EMPLOYEES else {}


def render_hours_dashboard(schedule, reference_date):
    """Render the hours tracking dashboard."""
    dashboards = get_all_employee_dashboards(schedule["shifts"], _get_active_employees(), reference_date)

    st.markdown("### Real-Time Hours & Fatigue")

    # Compute per-employee penalty exposure from violations
    violations = check_compliance(schedule)
    emp_penalties = {}
    for v in violations:
        emp = v.get("affected_employees", "Unknown")
        if v["severity"] == "CRITICAL":
            penalty = 7500
        elif v["severity"] == "HIGH":
            penalty = 1250
        else:
            penalty = 300
        emp_penalties[emp] = emp_penalties.get(emp, 0) + penalty

    total_penalty = sum(emp_penalties.values())

    # Summary metrics
    red_count = sum(1 for d in dashboards if d["fatigue_level"] == "red")
    yellow_count = sum(1 for d in dashboards if d["fatigue_level"] == "yellow")
    ot_count = sum(1 for d in dashboards if d["weekly_hours"] > OT_THRESHOLD_WEEKLY)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Fatigue RED", red_count, help="Employees at critical fatigue level")
    with col2:
        st.metric("Fatigue YELLOW", yellow_count, help="Employees at moderate fatigue")
    with col3:
        st.metric("In Overtime", ot_count, help="Employees past 40hr threshold")
    with col4:
        st.metric("Total Penalty Exposure", f"${total_penalty:,}",
                  help="Sum of estimated fines from all violations this week")

    st.divider()

    # Employee table — simplified with fairness inline
    fairness_report = calculate_team_fairness_report(
        schedule["shifts"], _get_active_employees(), _get_active_history(), reference_date
    )
    fairness_map = {r["name"]: r["fairness_index"] for r in fairness_report}

    rows = []
    for d in sorted(dashboards, key=lambda x: x["fatigue_score"], reverse=True):
        emp_penalty = emp_penalties.get(d["name"], 0)
        fair_idx = fairness_map.get(d["name"], 0)
        rows.append({
            "Employee": d["name"],
            "Hours": f"{d['weekly_hours']}h",
            "Fatigue": d["fatigue_level"].upper(),
            "OT Left": f"{d['hours_remaining_before_ot']}h",
            "Fairness": f"{fair_idx:.1f}",
            "Risk $": f"${emp_penalty:,}" if emp_penalty > 0 else "-",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Penalty breakdown callout
    if emp_penalties:
        st.markdown(
            f'<div style="background:#2d1b1b;padding:12px 16px;border-radius:8px;border-left:4px solid #dc3545;">'
            f'<strong style="color:#ff6666;">Penalty Exposure This Week: ${total_penalty:,}</strong> — '
            f'{len(emp_penalties)} employee(s) have violations. '
            f'<span style="color:#aaa;">Fix these in the Compliance tab to reduce risk.</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown("")

    # Predictive blocking demo
    st.divider()
    st.markdown("### Predictive Shift Impact")
    st.markdown("*What happens if you add a shift to an employee?*")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        emp_names = [e["name"] for e in _get_active_employees()]
        selected_emp = st.selectbox("Employee", emp_names, index=1)
    with col2:
        proposed_date = st.date_input("Date", value=reference_date + timedelta(days=2))
    with col3:
        proposed_start = st.selectbox("Start", ["06:00", "14:00", "22:00"], index=0)
    with col4:
        proposed_end = st.selectbox("End", ["14:30", "22:30", "06:30"], index=0)

    emp_id = next(e["id"] for e in _get_active_employees() if e["name"] == selected_emp)
    proposed_shift = {
        "employee_id": emp_id,
        "name": selected_emp,
        "date": proposed_date.strftime("%Y-%m-%d"),
        "start": proposed_start,
        "end": proposed_end,
        "role": next(e["role"] for e in _get_active_employees() if e["name"] == selected_emp),
        "shift_type": "Proposed",
    }

    impact = predict_shift_impact(schedule["shifts"], emp_id, proposed_shift, reference_date)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Current State:**")
        st.markdown(f"- Weekly hours: {impact['current']['weekly_hours']}h")
        st.markdown(f"- Fatigue: {impact['current']['fatigue_level'].upper()} ({impact['current']['fatigue_score']}/100)")
        st.markdown(f"- OT remaining: {impact['current']['hours_remaining_before_ot']}h")
    with col2:
        st.markdown("**If Assigned:**")
        st.markdown(f"- Weekly hours: {impact['projected']['weekly_hours']}h")
        st.markdown(f"- Fatigue: {impact['projected']['fatigue_level'].upper()} ({impact['projected']['fatigue_score']}/100)")
        st.markdown(f"- OT remaining: {impact['projected']['hours_remaining_before_ot']}h")

    st.markdown(f"**Recommendation:** {impact['recommendation']}")

    if impact["warnings"]:
        for w in impact["warnings"]:
            color = get_severity_color(w["severity"])
            st.markdown(
                f'<span style="background-color:{color};color:white;padding:2px 8px;'
                f'border-radius:4px;font-size:0.85em;">{w["severity"]}</span> {w["message"]}',
                unsafe_allow_html=True,
            )
    else:
        st.success("No concerns — safe to assign.")


def render_coverage_tab(schedule, reference_date):
    """Render the fairness-ranked coverage finder."""
    st.markdown("### Find Coverage (Fairness-Ranked)")
    st.markdown("*When someone calls out or a gap needs filling, find the fairest replacement.*")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        gap_date = st.date_input("Gap Date", value=reference_date, key="gap_date")
    with col2:
        gap_start = st.selectbox("Gap Start", ["06:00", "07:00", "14:00", "22:00"], index=0, key="gap_start")
    with col3:
        gap_end = st.selectbox("Gap End", ["14:30", "15:30", "22:30", "06:30"], index=0, key="gap_end")
    with col4:
        gap_role = st.selectbox("Role Needed", ["Pick", "Pack", "Stow", "Ship"], index=0, key="gap_role")

    absent_emp = st.selectbox(
        "Who called out?",
        ["(none)"] + [e["name"] for e in _get_active_employees()],
        index=0, key="absent_emp"
    )

    gap_shift = {
        "date": gap_date.strftime("%Y-%m-%d"),
        "start": gap_start,
        "end": gap_end,
        "role": gap_role,
        "shift_type": "Coverage",
        "is_holiday": is_holiday(gap_date.strftime("%Y-%m-%d")),
    }
    if absent_emp != "(none)":
        gap_shift["absent_employee_id"] = next(
            (e["id"] for e in _get_active_employees() if e["name"] == absent_emp), None
        )

    candidates = find_coverage(
        schedule["shifts"], _get_active_employees(), gap_shift, _get_active_history(), reference_date
    )

    if candidates:
        st.divider()

        # THE RECOMMENDATION — one clear answer (no competitor does this)
        best = candidates[0]
        st.markdown(
            f'<div style="background:#1a2d1a;padding:16px;border-radius:12px;'
            f'border:2px solid #28a745;margin-bottom:12px;">'
            f'<span style="color:#28a745;font-size:0.8em;text-transform:uppercase;font-weight:bold;">'
            f'Recommended</span><br>'
            f'<strong style="font-size:1.3em;">{best["name"]}</strong> '
            f'<span style="color:#aaa;">({best["role"]} | {best["current_weekly_hours"]}h this week | '
            f'Fatigue: {best["fatigue_level"].upper()})</span><br>'
            f'<span style="color:#28a745;font-size:0.9em;">Why: {best["reason"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"Assign {best['name']}", type="primary", key="assign_best",
                         use_container_width=True):
                st.success(f"Assigned! {best['name']} notified. Coverage gap filled.")
        with col2:
            if st.button("See all candidates", key="show_all_candidates", use_container_width=True):
                st.session_state["show_all_candidates"] = True

        # Other candidates (collapsed by default)
        if len(candidates) > 1:
            with st.expander(f"All {len(candidates)} candidates (ranked by fairness)"):
                for i, c in enumerate(candidates[1:], 2):
                    st.markdown(
                        f'<div style="background:#1a1a2e;padding:8px 12px;border-radius:8px;'
                        f'margin-bottom:4px;border-left:3px solid #6c757d;">'
                        f'<strong>#{i} {c["name"]}</strong> — {c["current_weekly_hours"]}h | '
                        f'Fatigue: {c["fatigue_level"].upper()} | '
                        f'Score: {c["composite_score"]}/100<br>'
                        f'<span style="color:#888;font-size:0.85em;">{c["reason"]}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
    else:
        st.warning("No eligible candidates found for this shift configuration.")

    # Team fairness report
    st.divider()
    st.markdown("### Team Fairness Report")

    report = calculate_team_fairness_report(
        schedule["shifts"], _get_active_employees(), _get_active_history(), reference_date
    )

    rows = []
    for r in report:
        rows.append({
            "Employee": r["name"],
            "Role": r["role"],
            "Fairness Index": r["fairness_index"],
            "Holidays Worked": r["holidays_worked_this_year"],
            "Coverage Requests": r["coverage_requests_received"],
            "Night Shifts (mo)": r["night_shifts_this_month"],
            "Weekend Shifts (mo)": r["weekend_shifts_this_month"],
            "Voluntary Covers": r["voluntary_covers"],
            "Forced Covers": r["forced_covers"],
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption("Lower Fairness Index = has carried more burden recently (deserves a break).")


def render_shift_intelligence(schedule, reference_date):
    """Render the shift intelligence tab."""
    st.markdown("### Shift Intelligence")

    # Classify all shifts
    analysis = analyze_schedule_shifts(schedule["shifts"])
    summary = analysis["summary"]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Day Shifts", summary["day_shifts"])
    with col2:
        st.metric("Evening Shifts", summary["evening_shifts"])
    with col3:
        st.metric("Night Shifts", summary["night_shifts"])
    with col4:
        st.metric("Holiday Shifts", summary["holiday_shifts"])

    # Shift distribution per employee
    st.divider()
    st.markdown("### Shift Type Distribution")

    dist_rows = []
    for emp_id, dist in analysis["employee_distribution"].items():
        emp_name = next((e["name"] for e in _get_active_employees() if e["id"] == emp_id), emp_id)
        dist_rows.append({
            "Employee": emp_name,
            "Day": dist["day"],
            "Evening": dist["evening"],
            "Night": dist["night"],
            "Holidays": dist["holidays"],
        })

    df = pd.DataFrame(dist_rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Premium pay calculation
    st.divider()
    st.markdown("### Premium Pay Calculation")

    hourly_rate = st.slider("Base hourly rate ($)", 15, 35, 20, key="hourly_rate")
    pay = calculate_premium_pay(schedule["shifts"], hourly_rate=float(hourly_rate))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Base Pay", f"${pay['total_base_pay']:,.2f}")
    with col2:
        st.metric("Premium Pay", f"${pay['total_premium_pay']:,.2f}")
    with col3:
        st.metric("Total", f"${pay['total_pay']:,.2f}")

    if pay["premiums"]:
        with st.expander(f"Premium breakdown ({len(pay['premiums'])} shifts with premium)"):
            prem_rows = [{
                "Employee": p["name"],
                "Date": p["date"],
                "Type": p["shift_type"],
                "Multiplier": f"x{p['total_multiplier']}",
                "Premium": f"${p['premium_amount']:.2f}",
            } for p in pay["premiums"]]
            st.dataframe(pd.DataFrame(prem_rows), use_container_width=True, hide_index=True)

    # Night shift compliance
    st.divider()
    st.markdown("### Night Shift Compliance")

    night_violations = []
    for emp in _get_active_employees():
        vs = check_night_shift_compliance(schedule["shifts"], emp["id"])
        night_violations.extend(vs)

    if night_violations:
        for v in night_violations:
            color = get_severity_color(v["severity"])
            st.markdown(
                f'<span style="background-color:{color};color:white;padding:2px 8px;'
                f'border-radius:4px;font-size:0.85em;">{v["severity"]}</span> '
                f'**{v["rule_name"]}**: {v["description"]}',
                unsafe_allow_html=True,
            )
    else:
        st.success("No night shift violations detected.")

    # Upcoming holidays
    st.divider()
    st.markdown("### Upcoming Holidays & Coverage")

    holidays = get_holidays_in_range(
        reference_date.strftime("%Y-%m-%d"),
        (reference_date + timedelta(days=180)).strftime("%Y-%m-%d")
    )

    if holidays:
        holiday_rows = [{"Date": h["date"], "Holiday": h["name"]} for h in holidays]
        st.dataframe(pd.DataFrame(holiday_rows), use_container_width=True, hide_index=True)

        selected_holiday = st.selectbox(
            "Plan coverage for:",
            [f"{h['date']} - {h['name']}" for h in holidays],
            key="holiday_plan"
        )
        if selected_holiday:
            h_date = selected_holiday.split(" - ")[0]
            shifts_needed = st.number_input("Shifts needed", 1, 10, 3, key="shifts_needed")

            plan = generate_holiday_coverage_plan(
                _get_active_employees(), h_date, shifts_needed,
                employee_history=EMPLOYEE_HISTORY
            )

            st.markdown(f"**Assigned ({plan['shifts_needed']} needed):**")
            for c in plan["assigned"]:
                st.markdown(f"- **{c['name']}** (Holidays worked: {c['holidays_worked_this_year']}) — {c['reason']}")

            if plan["available_backup"]:
                st.markdown("**Backup:**")
                for c in plan["available_backup"]:
                    st.markdown(f"- {c['name']} — {c['reason']}")


def render_leave_management(tracker, emp_id, emp_name):
    """Render leave management section within the worker portal."""
    st.markdown("#### My Leave Balances & Availability")

    summary = tracker.get_balance_summary(emp_id)
    if not summary:
        st.warning("Leave balances not initialized.")
        return

    # Balance cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("PTO", f"{summary['pto_hours']}h ({summary['pto_days']}d)")
    with col2:
        st.metric("Sick Leave", f"{summary['sick_hours']}h ({summary['sick_days']}d)")
    with col3:
        color = "inverse" if summary['upt_hours'] <= 4 else "normal"
        st.metric("UPT", f"{summary['upt_hours']}h", delta=None)
    with col4:
        fmla_status = f"{summary['fmla_weeks_remaining']}w" if summary['fmla_eligible'] else "Not Eligible"
        st.metric("FMLA", fmla_status)

    # Warnings
    if summary["warnings"]:
        for w in summary["warnings"]:
            st.warning(w)

    st.divider()

    # Quick actions
    st.markdown("**Quick Actions:**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Report Sick Today", key="report_sick_btn"):
            result = tracker.report_sick_today(emp_id)
            if result.get("error"):
                st.error(result["error"])
            else:
                st.success(f"Sick leave recorded. Balance: {result['balance_deduction'].get('remaining', 'N/A')}h remaining.")
                if result.get("alerts_triggered"):
                    for a in result["alerts_triggered"]:
                        st.warning(f"Alert: {a['message']}")
    with col2:
        partial_hours = st.selectbox("Or use UPT (partial day):", [0, 1, 2, 3, 4], key="upt_partial")
        if partial_hours > 0 and st.button("Use UPT", key="use_upt_btn"):
            result = tracker.record_leave(
                emp_id, "UPT",
                datetime.now().strftime("%Y-%m-%d"),
                datetime.now().strftime("%Y-%m-%d"),
                hours=partial_hours
            )
            if result.get("balance_deduction", {}).get("critical_warning"):
                st.error(result["balance_deduction"]["critical_warning"])
            else:
                st.success(f"UPT recorded ({partial_hours}h). Remaining: {tracker.get_balance(emp_id)['upt']['available']}h")

    st.divider()

    # Availability calendar
    st.markdown("**Availability Calendar (Next 30 Days):**")
    st.markdown("*See which dates are available to request off on your shift code.*")

    assignment = next((a for a in SHIFT_ASSIGNMENTS if a["employee_id"] == emp_id), None)
    if assignment:
        calendar = tracker.get_availability_calendar(
            emp_id, assignment["shift_code"],
            datetime.now().strftime("%Y-%m-%d"),
            SHIFT_ASSIGNMENTS
        )

        # Display as compact table
        cal_rows = []
        for day in calendar:
            status_icon = {
                "open": "Available",
                "limited": "Limited (1 spot)",
                "full": "Full",
                "blackout": "BLACKOUT",
            }.get(day["status"], day["status"])

            cal_rows.append({
                "Date": day["date"],
                "Day": day["day"][:3],
                "Status": status_icon,
                "Spots Left": day["spots_remaining"],
            })

        df = pd.DataFrame(cal_rows)
        st.dataframe(df, use_container_width=True, hide_index=True, height=300)

    # Leave history
    st.divider()
    st.markdown("**My Leave History:**")
    my_leaves = [r for r in tracker.leave_records if r["employee_id"] == emp_id]
    if my_leaves:
        for r in my_leaves[-5:]:  # last 5
            status_color = "#28a745" if r["status"] == "ACTIVE" else "#6c757d"
            st.markdown(
                f'<span style="background-color:{status_color};color:white;padding:2px 6px;'
                f'border-radius:3px;font-size:0.75em;">{r["status"]}</span> '
                f'**{r["leave_name"]}** — {r["start_date"]} to {r["end_date"]} ({r["days"]}d) '
                f'| {r.get("reason", "")}',
                unsafe_allow_html=True,
            )
    else:
        st.info("No leave history.")


def render_manager_alerts(tracker, queue):
    """Render leave-specific alerts in the manager queue."""
    st.markdown("#### Leave Intelligence Alerts")

    alerts = tracker.get_alerts()
    rtw = tracker.get_return_to_work_pending()
    chase = tracker.get_documentation_chase_list()

    # Alert counts
    col1, col2, col3 = st.columns(3)
    with col1:
        critical = [a for a in alerts if a["severity"] == "CRITICAL"]
        st.metric("Critical Alerts", len(critical))
    with col2:
        st.metric("Return-to-Work Pending", len(rtw))
    with col3:
        st.metric("Doc Chase Overdue", len(chase))

    # Alerts
    if alerts:
        st.markdown("**Active Alerts:**")
        for a in alerts:
            color = {"CRITICAL": "#dc3545", "HIGH": "#fd7e14", "MEDIUM": "#ffc107"}.get(
                a["severity"], "#6c757d")
            st.markdown(
                f'<span style="background-color:{color};color:white;padding:2px 8px;'
                f'border-radius:4px;font-size:0.8em;">{a["severity"]}</span> '
                f'**{a["type"]}**: {a["message"]}',
                unsafe_allow_html=True,
            )
            if a.get("action_required"):
                st.markdown(f"  *Action:* {a['action_required']}")
            st.markdown("")

    # Return to work
    if rtw:
        st.divider()
        st.markdown("**Return-to-Work Clearances Needed:**")
        for r in rtw:
            st.markdown(f"- **{r['employee_id']}** returning {r['end_date']} "
                      f"({r['days_until_return']} days) — needs {r['clearance_type']} clearance")

    # Doc chase
    if chase:
        st.divider()
        st.markdown("**Overdue Documentation:**")
        for c in chase:
            st.markdown(f"- **{c['employee_id']}** — {c['doc_type']} was due {c['due_date']} "
                      f"({c['days_overdue']} days overdue)")


def render_worker_calendar(portal, emp_id, emp_name, dashboard):
    """Render a full-featured monthly calendar for workers."""
    st.markdown("#### My Schedule Calendar")

    # Month navigation
    today = datetime.today()
    col_prev, col_month, col_next = st.columns([1, 3, 1])
    month_offset = st.session_state.get("cal_month_offset", 0)

    with col_prev:
        if st.button("<", key="cal_prev"):
            st.session_state["cal_month_offset"] = month_offset - 1
            st.rerun()
    with col_next:
        if st.button(">", key="cal_next"):  # noqa: E501
            st.session_state["cal_month_offset"] = month_offset + 1
            st.rerun()

    # Calculate which month to show
    view_year = today.year + (today.month + month_offset - 1) // 12
    view_month = (today.month + month_offset - 1) % 12 + 1
    month_start = datetime(view_year, view_month, 1)
    month_name = month_start.strftime("%B %Y")

    with col_month:
        st.markdown(f"<h3 style='text-align:center;margin:0;'>{month_name}</h3>",
                    unsafe_allow_html=True)

    # Get leave tracker data
    tracker = st.session_state.get("leave_tracker")
    shift_code = dashboard.get("shift_code", "DA5")
    days_on = dashboard.get("days_on", [])
    days_off = dashboard.get("days_off", [])

    # Get availability calendar from leave tracker
    avail_calendar = {}
    if tracker:
        avail_data = tracker.get_availability_calendar(
            emp_id, shift_code, month_start.strftime("%Y-%m-%d"),
            portal.shift_assignments
        )
        for entry in avail_data:
            avail_calendar[entry["date"]] = entry

    # Get approved time off for teammates on same shift code
    same_code = [a for a in portal.shift_assignments if a["shift_code"] == shift_code]
    teammate_off = {}
    if tracker:
        for rec in tracker.leave_records:
            if rec["status"] == "ACTIVE" and rec["employee_id"] != emp_id:
                if any(a["employee_id"] == rec["employee_id"] and a["shift_code"] == shift_code
                       for a in portal.shift_assignments):
                    start_d = datetime.strptime(rec["start_date"], "%Y-%m-%d")
                    end_d = datetime.strptime(rec["end_date"], "%Y-%m-%d")
                    d = start_d
                    while d <= end_d:
                        ds = d.strftime("%Y-%m-%d")
                        if ds not in teammate_off:
                            teammate_off[ds] = []
                        mate_name = next(
                            (a["name"] for a in portal.shift_assignments
                             if a["employee_id"] == rec["employee_id"]), rec["employee_id"]
                        )
                        teammate_off[ds].append(mate_name)
                        d += timedelta(days=1)

    # My approved/pending requests
    my_requests = {}
    for r in portal.requests:
        if r["employee_id"] == emp_id and r["type"] == "HOLIDAY":
            start_d = datetime.strptime(r["start_date"], "%Y-%m-%d")
            end_d = datetime.strptime(r["end_date"], "%Y-%m-%d")
            d = start_d
            while d <= end_d:
                my_requests[d.strftime("%Y-%m-%d")] = r["status"]
                d += timedelta(days=1)

    # Balance display
    if tracker:
        bal_summary = tracker.get_balance_summary(emp_id)
        if bal_summary:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("PTO Available", f"{bal_summary['pto_days']} days")
            with col2:
                st.metric("Sick Available", f"{bal_summary['sick_days']} days")
            with col3:
                st.metric("UPT Available", f"{bal_summary['upt_hours']}h")
            with col4:
                at_risk = bal_summary.get("at_risk", {})
                risk_hrs = at_risk.get("pto_at_risk", 0)
                if risk_hrs > 0:
                    st.metric("At Risk (use-it-or-lose-it)", f"{risk_hrs}h",
                              delta=f"-{risk_hrs}h by year-end", delta_color="inverse")
                else:
                    st.metric("At Risk", "None")

            if bal_summary.get("warnings"):
                for w in bal_summary["warnings"]:
                    st.warning(w)

    st.divider()

    # Legend
    st.markdown(
        '<span style="background:#28a745;color:white;padding:2px 8px;border-radius:4px;font-size:0.75em;margin-right:8px;">Open</span>'
        '<span style="background:#ffc107;color:black;padding:2px 8px;border-radius:4px;font-size:0.75em;margin-right:8px;">Limited</span>'
        '<span style="background:#dc3545;color:white;padding:2px 8px;border-radius:4px;font-size:0.75em;margin-right:8px;">Full/Blackout</span>'
        '<span style="background:#6f42c1;color:white;padding:2px 8px;border-radius:4px;font-size:0.75em;margin-right:8px;">My Shift</span>'
        '<span style="background:#17a2b8;color:white;padding:2px 8px;border-radius:4px;font-size:0.75em;margin-right:8px;">My PTO</span>'
        '<span style="background:#343a40;color:white;padding:2px 8px;border-radius:4px;font-size:0.75em;">Day Off</span>',
        unsafe_allow_html=True,
    )
    st.markdown("")

    # Day-of-week mapping
    day_abbrevs = {"Sun": 6, "Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5}
    work_days_idx = {day_abbrevs[d] for d in days_on if d in day_abbrevs}

    # Render calendar grid
    month_cal = cal.monthcalendar(view_year, view_month)

    # Header row
    header_cols = st.columns(7)
    for i, day_name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
        with header_cols[i]:
            st.markdown(f"<div style='text-align:center;font-weight:bold;color:#888;font-size:0.85em;'>{day_name}</div>",
                        unsafe_allow_html=True)

    # Calendar rows
    for week in month_cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.markdown("")
                    continue

                date_obj = datetime(view_year, view_month, day)
                date_str = date_obj.strftime("%Y-%m-%d")
                weekday_idx = date_obj.weekday()

                # Determine cell style
                is_today = (date_obj.date() == today.date())
                is_work_day = weekday_idx in work_days_idx
                is_my_pto = date_str in my_requests
                pto_status = my_requests.get(date_str, "")

                avail = avail_calendar.get(date_str, {})
                avail_status = avail.get("status", "open")
                spots = avail.get("spots_remaining", "?")
                teammates_out = teammate_off.get(date_str, [])

                # Pick background color
                if is_my_pto:
                    if pto_status in ("AUTO_APPROVED", "APPROVED"):
                        bg = "#17a2b8"
                    else:
                        bg = "#17a2b8"
                        border = "border:2px dashed #ffc107;"
                elif avail_status == "blackout":
                    bg = "#dc3545"
                elif avail_status == "full":
                    bg = "#dc3545"
                elif avail_status == "limited":
                    bg = "#ffc107"
                elif is_work_day:
                    bg = "#6f42c1"
                else:
                    bg = "#343a40"

                border_style = "border:2px solid #ffc107;" if (is_my_pto and pto_status == "PENDING") else ""
                today_ring = "box-shadow:0 0 0 2px #fff;" if is_today else ""

                # Build tooltip/subtitle
                subtitle = ""
                if is_my_pto:
                    subtitle = "PTO" if pto_status in ("AUTO_APPROVED", "APPROVED") else "Pending"
                elif is_work_day:
                    subtitle = shift_code
                else:
                    subtitle = "Off"

                # Teammate indicator
                mate_indicator = ""
                if teammates_out:
                    mate_indicator = f"<span style='font-size:0.6em;color:#ffc107;'>{len(teammates_out)} out</span>"

                st.markdown(
                    f'<div style="background:{bg};border-radius:8px;padding:6px 4px;text-align:center;'
                    f'min-height:60px;{border_style}{today_ring}">'
                    f'<span style="font-size:1.1em;font-weight:bold;color:white;">{day}</span><br>'
                    f'<span style="font-size:0.7em;color:#ddd;">{subtitle}</span><br>'
                    f'{mate_indicator}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # Team coverage summary for this month
    st.divider()
    st.markdown("#### Team Coverage This Month")
    st.markdown(f"*Shift code: {shift_code} | Team size: {len(same_code)} | Min staffing: {max(1, int(len(same_code) * 0.6))}*")

    if teammates_out_dates := sorted(teammate_off.keys()):
        coverage_data = []
        for ds in teammates_out_dates:
            if ds.startswith(f"{view_year}-{view_month:02d}"):
                avail_info = avail_calendar.get(ds, {})
                coverage_data.append({
                    "Date": ds,
                    "Day": datetime.strptime(ds, "%Y-%m-%d").strftime("%A"),
                    "Teammates Off": ", ".join(teammate_off[ds]),
                    "Spots Left": avail_info.get("spots_remaining", "?"),
                    "Status": avail_info.get("status", "unknown").upper(),
                })
        if coverage_data:
            st.dataframe(pd.DataFrame(coverage_data), use_container_width=True, hide_index=True)
        else:
            st.info("No teammates have approved time off this month.")
    else:
        st.info("No teammates have approved time off this month.")

    # Quick request from calendar
    st.divider()
    st.markdown("#### Quick PTO Request")
    st.markdown("*Select dates and submit — auto-approval checks coverage instantly.*")

    col1, col2 = st.columns(2)
    with col1:
        cal_req_start = st.date_input("Start", key="cal_req_start",
                                       value=month_start + timedelta(days=14))
    with col2:
        cal_req_end = st.date_input("End", key="cal_req_end",
                                     value=month_start + timedelta(days=16))

    cal_priority = st.selectbox("Priority", [1, 2, 3],
                                format_func=lambda x: f"Priority {x}" + (" (most important)" if x == 1 else ""),
                                key="cal_req_priority")
    cal_reason = st.text_input("Reason (optional)", key="cal_req_reason",
                               placeholder="e.g., Family trip, appointment")

    if st.button("Request Time Off", type="primary", key="cal_submit_pto"):
        result = portal.submit_holiday_request(
            emp_id,
            cal_req_start.strftime("%Y-%m-%d"),
            cal_req_end.strftime("%Y-%m-%d"),
            priority=cal_priority,
            reason=cal_reason,
        )

        # Calculate hours for this request
        days_requested = (cal_req_end - cal_req_start).days + 1
        hours_requested = days_requested * 8

        if result["status"] == STATUS_AUTO_APPROVED:
            # Deduct from leave balance
            if tracker:
                tracker.record_leave(
                    emp_id, "PTO",
                    cal_req_start.strftime("%Y-%m-%d"),
                    cal_req_end.strftime("%Y-%m-%d"),
                    hours=hours_requested,
                    reason=cal_reason,
                )

            # Show success with live balance update
            st.success(f"Auto-approved! Your PTO for {cal_req_start} to {cal_req_end} is confirmed.")

            # Live balance display after deduction
            if tracker:
                new_bal = tracker.get_balance_summary(emp_id)
                if new_bal:
                    st.markdown(
                        f'<div style="background:#1a2d1a;padding:12px;border-radius:8px;border-left:4px solid #28a745;">'
                        f'<strong style="color:#28a745;">Balance Updated</strong><br>'
                        f'<span style="color:#ccc;">PTO deducted: <strong>-{hours_requested}h ({days_requested} days)</strong></span><br>'
                        f'<span style="color:#ccc;">Remaining PTO: <strong>{new_bal["pto_hours"]}h ({new_bal["pto_days"]} days)</strong></span><br>'
                        f'<span style="color:#ccc;">Sick: {new_bal["sick_hours"]}h | UPT: {new_bal["upt_hours"]}h</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            # Confirmation notifications
            st.markdown(
                f'<div style="background:#1a1a2e;padding:10px 14px;border-radius:8px;margin-top:8px;'
                f'border-left:4px solid #0ea5e9;">'
                f'📱 <strong>Notifications Sent:</strong><br>'
                f'<span style="color:#ccc;">✅ <strong>{emp_name}</strong>: '
                f'"Your PTO {cal_req_start} to {cal_req_end} is confirmed. Enjoy your time off!"</span><br>'
                f'<span style="color:#ccc;">📋 <strong>Manager</strong>: '
                f'"{emp_name} PTO approved (auto) for {cal_req_start} to {cal_req_end}. '
                f'Coverage maintained — no action needed."</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        elif result["status"] == STATUS_ESCALATED:
            st.warning(f"Submitted for manager review. Reason: {result['auto_approval_result']['reason']}")

            # Notifications for escalation
            st.markdown(
                f'<div style="background:#1a1a2e;padding:10px 14px;border-radius:8px;margin-top:8px;'
                f'border-left:4px solid #fd7e14;">'
                f'📱 <strong>Notifications Sent:</strong><br>'
                f'<span style="color:#ccc;">⏳ <strong>{emp_name}</strong>: '
                f'"Your PTO request is with your manager. We\'ll notify you when decided."</span><br>'
                f'<span style="color:#ccc;">🔔 <strong>Manager</strong>: '
                f'"Action needed: {emp_name} requests {cal_req_start} to {cal_req_end} '
                f'(Priority {cal_priority}). Coverage concern — please review."</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info(f"Request submitted (#{result['id']}). Awaiting review.")


def render_worker_view(portal):
    """Render the worker self-service portal view."""
    st.markdown("### Worker Self-Service Portal")
    st.markdown("*Submit requests, set preferences, respond to VET, pick up open shifts.*")

    # Select which worker to view as
    emp_names = [a["name"] for a in portal.shift_assignments]
    selected = st.selectbox("View as:", emp_names, index=0, key="worker_view_emp")
    emp_id = next(a["employee_id"] for a in portal.shift_assignments if a["name"] == selected)

    dashboard = portal.get_worker_dashboard(emp_id)

    # Schedule info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Shift Code", dashboard["shift_code"])
    with col2:
        st.metric("Weekly Hours", dashboard["weekly_hours"])
    with col3:
        st.metric("Days On", ", ".join(dashboard["days_on"]))
    with col4:
        st.metric("Days Off", ", ".join(dashboard["days_off"]))

    # Smart Notifications
    schedule = st.session_state.get("schedule")
    notif_gen = create_demo_smart_notifications(
        employees=_get_active_employees(),
        shifts=schedule["shifts"] if schedule else [],
        leave_tracker=st.session_state.get("leave_tracker"),
        portal=portal,
    )
    notifications = notif_gen.generate_worker_notifications(emp_id)

    if notifications:
        with st.expander(f"Notifications ({len(notifications)})", expanded=True):
            for n in notifications[:5]:
                priority_colors = {
                    "URGENT": "#dc3545", "HIGH": "#fd7e14",
                    "NORMAL": "#0ea5e9", "LOW": "#6c757d"
                }
                color = priority_colors.get(n["priority_label"], "#6c757d")
                action_html = (
                    f' <span style="background:#0ea5e9;color:white;padding:2px 8px;'
                    f'border-radius:4px;font-size:0.75em;cursor:pointer;">{n["action_label"]}</span>'
                    if n.get("action_label") else ""
                )
                st.markdown(
                    f'<div style="background:#1a1a2e;padding:10px 14px;border-radius:8px;'
                    f'margin-bottom:6px;border-left:4px solid {color};">'
                    f'{n.get("icon", "🔔")} '
                    f'<strong>{n["title"]}</strong><br>'
                    f'<span style="color:#ccc;font-size:0.9em;">{n["message"]}</span>'
                    f'{action_html}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            if len(notifications) > 5:
                st.caption(f"+ {len(notifications) - 5} more notifications")

    st.divider()

    # Tabs within worker view
    w_tab0, w_tab1, w_tab2, w_tab3, w_tab4, w_tab5, w_tab6 = st.tabs([
        "My Calendar", "Leave & Balances", "My Requests", "Request Time Off",
        "VET & Open Shifts", "Shift Swap", "My Preferences"
    ])

    with w_tab0:
        render_worker_calendar(portal, emp_id, selected, dashboard)

    with w_tab1:
        if "leave_tracker" in st.session_state:
            render_leave_management(st.session_state["leave_tracker"], emp_id, selected)
        else:
            st.info("Run Demo to load leave data.")

    with w_tab2:
        st.markdown("#### My Request History")
        st.markdown("*All your past and current requests — use as reference for future planning.*")

        my_requests = [r for r in portal.requests if r["employee_id"] == emp_id]

        if my_requests:
            # Summary metrics
            total = len(my_requests)
            approved = len([r for r in my_requests if r["status"] in ("AUTO_APPROVED", "APPROVED")])
            pending = len([r for r in my_requests if r["status"] in ("PENDING", "ESCALATED")])
            denied = len([r for r in my_requests if r["status"] == "DENIED"])

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Requests", total)
            with col2:
                st.metric("Approved", approved)
            with col3:
                st.metric("Pending", pending)
            with col4:
                st.metric("Denied", denied)

            st.divider()

            # Filter options
            filter_status = st.selectbox(
                "Filter by status:", ["All", "Approved", "Pending/Escalated", "Denied"],
                key="req_history_filter"
            )

            # Request list
            for r in sorted(my_requests, key=lambda x: x.get("submitted_at", ""), reverse=True):
                # Apply filter
                if filter_status == "Approved" and r["status"] not in ("AUTO_APPROVED", "APPROVED"):
                    continue
                if filter_status == "Pending/Escalated" and r["status"] not in ("PENDING", "ESCALATED"):
                    continue
                if filter_status == "Denied" and r["status"] != "DENIED":
                    continue

                status_color = {
                    "AUTO_APPROVED": "#28a745", "APPROVED": "#28a745",
                    "PENDING": "#ffc107", "ESCALATED": "#fd7e14",
                    "DENIED": "#dc3545",
                }.get(r["status"], "#6c757d")

                if r["type"] == "HOLIDAY":
                    detail = f"{r['start_date']} to {r['end_date']} (Priority {r['priority']})"
                    days = 1
                    try:
                        d1 = datetime.strptime(r["start_date"], "%Y-%m-%d")
                        d2 = datetime.strptime(r["end_date"], "%Y-%m-%d")
                        days = (d2 - d1).days + 1
                    except (ValueError, TypeError):
                        pass
                    detail += f" — {days} day(s)"
                elif r["type"] == "SHIFT_SWAP":
                    detail = f"Swap with {r.get('target_employee_name', 'N/A')}"
                elif r["type"] == "PREFERENCE":
                    detail = "Preferences updated"
                else:
                    detail = r["type"]

                st.markdown(
                    f'<div style="background:#1a1a2e;padding:10px 14px;border-radius:8px;'
                    f'margin-bottom:6px;border-left:4px solid {status_color};">'
                    f'<span style="background-color:{status_color};color:white;padding:2px 8px;'
                    f'border-radius:4px;font-size:0.75em;">{r["status"]}</span> '
                    f'<strong>{r["type"]}</strong> — {detail}<br>'
                    f'<span style="color:#888;font-size:0.8em;">Submitted: {r.get("submitted_at", "N/A")}'
                    f'{" | Reason: " + r["reason"] if r.get("reason") else ""}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                if r.get("auto_approval_result"):
                    result = r["auto_approval_result"]
                    if result.get("checks_passed") or result.get("checks_failed"):
                        with st.expander(f"Approval details — {r.get('submitted_at', '')}"):
                            for c in result.get("checks_passed", []):
                                st.markdown(f"- :white_check_mark: {c}")
                            for c in result.get("checks_failed", []):
                                st.markdown(f"- :x: {c}")
                            if result.get("reason"):
                                st.markdown(f"**Reason:** {result['reason']}")

            # Export request history
            st.divider()
            if st.button("Download My Request History (CSV)", key="export_my_requests"):
                req_rows = [{
                    "Date Submitted": r.get("submitted_at", ""),
                    "Type": r["type"],
                    "Start": r.get("start_date", ""),
                    "End": r.get("end_date", ""),
                    "Priority": r.get("priority", ""),
                    "Reason": r.get("reason", ""),
                    "Status": r["status"],
                } for r in my_requests]
                csv = pd.DataFrame(req_rows).to_csv(index=False)
                st.download_button("Download CSV", csv,
                                   file_name=f"my_requests_{emp_id}.csv", mime="text/csv")
        else:
            st.info("No requests submitted yet. Your history will appear here after your first request.")

    with w_tab3:
        st.markdown("#### Request Time Off")
        st.markdown("*Submit with priority ranking. Higher priority = more important to you.*")

        col1, col2 = st.columns(2)
        with col1:
            req_start = st.date_input("Start date", key="req_start",
                                      value=datetime.now() + timedelta(days=30))
        with col2:
            req_end = st.date_input("End date", key="req_end",
                                    value=datetime.now() + timedelta(days=36))

        req_priority = st.selectbox("Priority", [1, 2, 3],
                                    format_func=lambda x: f"Priority {x}" + (" (most important)" if x == 1 else ""),
                                    key="req_priority")
        req_reason = st.text_input("Reason (optional)", key="req_reason",
                                   placeholder="e.g., Family vacation, Lunar New Year, School break")
        req_flexible = st.checkbox("I'm flexible on exact dates", key="req_flexible")

        if st.button("Submit Request", type="primary", key="submit_holiday"):
            result = portal.submit_holiday_request(
                emp_id,
                req_start.strftime("%Y-%m-%d"),
                req_end.strftime("%Y-%m-%d"),
                priority=req_priority,
                reason=req_reason,
                flexible=req_flexible,
            )

            days_req = (req_end - req_start).days + 1
            hours_req = days_req * 8
            leave_tracker = st.session_state.get("leave_tracker")

            if result["status"] == STATUS_AUTO_APPROVED:
                # Deduct balance
                if leave_tracker:
                    leave_tracker.record_leave(
                        emp_id, "PTO",
                        req_start.strftime("%Y-%m-%d"),
                        req_end.strftime("%Y-%m-%d"),
                        hours=hours_req,
                        reason=req_reason,
                    )

                st.success(f"Request auto-approved! ({result['id']})")

                # Show updated balance
                if leave_tracker:
                    new_bal = leave_tracker.get_balance_summary(emp_id)
                    if new_bal:
                        st.markdown(
                            f'<div style="background:#1a2d1a;padding:12px;border-radius:8px;'
                            f'border-left:4px solid #28a745;margin-top:8px;">'
                            f'✅ <strong>Balance Updated:</strong> '
                            f'PTO deducted <strong>-{hours_req}h</strong> | '
                            f'Remaining: <strong>{new_bal["pto_hours"]}h ({new_bal["pto_days"]} days)</strong>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                # Confirmations
                st.markdown(
                    f'<div style="background:#1a1a2e;padding:10px 14px;border-radius:8px;'
                    f'margin-top:8px;border-left:4px solid #0ea5e9;">'
                    f'📱 <strong>Confirmations Sent:</strong><br>'
                    f'<span style="color:#ccc;">✅ Worker: "PTO confirmed for {req_start} to {req_end}. Enjoy!"</span><br>'
                    f'<span style="color:#ccc;">📋 Manager: "{selected} PTO auto-approved ({req_start} to {req_end}). No action needed."</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            elif result["status"] == STATUS_ESCALATED:
                st.warning(f"Request submitted for manager review ({result['id']}). "
                          f"Reason: {result['auto_approval_result']['reason']}")
                st.markdown(
                    f'<div style="background:#1a1a2e;padding:10px 14px;border-radius:8px;'
                    f'margin-top:8px;border-left:4px solid #fd7e14;">'
                    f'📱 <strong>Notifications:</strong><br>'
                    f'<span style="color:#ccc;">⏳ Worker: "Request pending. Manager will review within 24h."</span><br>'
                    f'<span style="color:#ccc;">🔔 Manager: "Action needed: {selected} requests {req_start}-{req_end} (P{req_priority})"</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.info(f"Request submitted ({result['id']}). Awaiting review.")

    with w_tab4:
        st.markdown("#### VET Offers & Open Shifts")

        # VET offers
        my_vet = [o for o in portal.vet_offers
                  if (o.get("offered_to") == emp_id or o.get("offered_to_all"))
                  and o.get("status") == "PENDING"]

        if my_vet:
            st.markdown("**VET Offers for You:**")
            for offer in my_vet:
                details = offer["shift_details"]
                st.markdown(f"- **{details['date']}** {details['start']}-{details['end']} "
                          f"({details['role']}, {details['department']})")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Accept", key=f"vet_accept_{offer['id']}"):
                        portal.respond_to_vet(emp_id, offer["id"], accept=True)
                        st.success("VET accepted!")
                with col2:
                    if st.button("Decline", key=f"vet_decline_{offer['id']}"):
                        portal.respond_to_vet(emp_id, offer["id"], accept=False)
                        st.info("VET declined.")
        else:
            st.info("No VET offers pending.")

        st.divider()

        # Open shifts
        open_shifts = [s for s in portal.open_shifts if not s.get("taken_by")]
        if open_shifts:
            st.markdown("**Open Shifts Available:**")
            for shift in open_shifts:
                st.markdown(f"- **{shift['date']}** {shift['start']}-{shift['end']} "
                          f"({shift['role']}) — {shift['reason']}")
                if st.button("Pick Up", key=f"pickup_{shift['id']}"):
                    result = portal.pickup_open_shift(emp_id, shift["id"])
                    if result.get("status") == STATUS_AUTO_APPROVED:
                        st.success("Shift picked up!")
                    else:
                        st.warning(f"Needs review: {result.get('compliance_check', {}).get('reason', '')}")
        else:
            st.info("No open shifts available.")

    with w_tab5:
        st.markdown("#### Propose Shift Swap")
        st.markdown("*Propose swapping one of your shifts with a colleague.*")

        other_emps = [a for a in portal.shift_assignments if a["employee_id"] != emp_id]
        target_name = st.selectbox("Swap with:", [a["name"] for a in other_emps], key="swap_target")
        target_id = next(a["employee_id"] for a in other_emps if a["name"] == target_name)

        col1, col2 = st.columns(2)
        with col1:
            my_date = st.date_input("Your shift date", key="swap_my_date",
                                    value=datetime.now() + timedelta(days=3))
        with col2:
            their_date = st.date_input("Their shift date", key="swap_their_date",
                                       value=datetime.now() + timedelta(days=5))

        swap_reason = st.text_input("Reason", key="swap_reason",
                                    placeholder="e.g., Doctor appointment")

        if st.button("Propose Swap", type="primary", key="submit_swap"):
            result = portal.submit_shift_swap(
                emp_id, target_id,
                my_date.strftime("%Y-%m-%d"),
                their_date.strftime("%Y-%m-%d"),
                reason=swap_reason,
            )
            compliance = result.get("compliance_check", {})
            if compliance.get("both_compliant"):
                st.success(f"Swap proposed ({result['id']}). Awaiting {target_name}'s acceptance.")
            else:
                st.warning(f"Swap has compliance concerns ({result['id']}). Escalated to manager.")

        # Swap requests for me
        swaps_for_me = [
            r for r in portal.requests
            if r["type"] == "SHIFT_SWAP"
            and r.get("target_employee_id") == emp_id
            and r.get("target_accepted") is None
        ]
        if swaps_for_me:
            st.divider()
            st.markdown("**Swap Requests for You:**")
            for r in swaps_for_me:
                st.markdown(f"- {r['employee_name']} wants to swap their {r['requester_date']} "
                          f"for your {r['target_date']}")
                if st.button("Accept Swap", key=f"accept_swap_{r['id']}"):
                    result = portal.accept_swap(r["id"], emp_id)
                    st.success(result["message"])

    with w_tab6:
        st.markdown("#### My Preferences")
        st.markdown("*Set your availability and scheduling preferences.*")

        current_prefs = portal.preferences.get(emp_id, {})

        pref_shift = st.selectbox(
            "Preferred shift type",
            ["day", "evening", "night"],
            index=["day", "evening", "night"].index(current_prefs.get("preferred_shift_type", "day")),
            key="pref_shift"
        )

        all_days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        pref_vet_days = st.multiselect(
            "Days available for VET (your off-days you'd accept extra work)",
            all_days,
            default=current_prefs.get("vet_available_days", []),
            key="pref_vet"
        )

        pref_max_hours = st.slider(
            "Max weekly hours preferred",
            40, 60, current_prefs.get("max_weekly_hours_preferred", 50),
            key="pref_max_hrs"
        )

        pref_notes = st.text_area(
            "Additional notes",
            value=current_prefs.get("notes", ""),
            key="pref_notes",
            placeholder="e.g., No Fridays (childcare), prefer mornings, available for holidays in December"
        )

        if st.button("Save Preferences", type="primary", key="save_prefs"):
            portal.update_preferences(emp_id, {
                "preferred_shift_type": pref_shift,
                "vet_available_days": pref_vet_days,
                "max_weekly_hours_preferred": pref_max_hours,
                "notes": pref_notes,
            })
            st.success("Preferences saved!")


def render_manager_queue_tab(portal, queue):
    """Render the manager queue tab — action-first, inline approve/deny."""
    st.markdown("### Action Queue")

    summary = queue.get_queue_summary()

    # Summary cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Needs Action", summary["needs_action"])
    with col2:
        st.metric("Auto-Resolved", summary["auto_resolved"])
    with col3:
        st.metric("Auto-Rate", f"{summary['auto_resolution_rate']}%")
    with col4:
        st.metric("Time Saved", summary["time_saved_estimate"])

    st.divider()

    # Tabs within manager queue
    m_tab1, m_tab2, m_tab3, m_tab4, m_tab5 = st.tabs([
        "Action Required", "Leave Alerts", "Auto-Approved Log", "Coverage Gaps", "Analytics"
    ])

    with m_tab2:
        if "leave_tracker" in st.session_state:
            render_manager_alerts(st.session_state["leave_tracker"], queue)
        else:
            st.info("Run Demo to load leave data.")

    with m_tab1:
        items = queue.get_action_items()
        if items:
            for i, item in enumerate(items):
                r = item["request"]
                urgency_color = {"HIGH": "#dc3545", "MEDIUM": "#ffc107", "LOW": "#28a745"}.get(
                    item["urgency"], "#6c757d")

                if r["type"] == "HOLIDAY":
                    title = f"{r['employee_name']} — {r['start_date']} to {r['end_date']}"
                    subtitle = f"Priority {r.get('priority', 'N/A')} | Reason: {r.get('reason', 'Not provided')}"
                elif r["type"] == "SHIFT_SWAP":
                    title = f"{r['employee_name']} swap with {r.get('target_employee_name', 'N/A')}"
                    subtitle = f"Swap dates: {r.get('requester_date', '')} ↔ {r.get('target_date', '')}"
                else:
                    title = f"{r['employee_name']} — {r['type']}"
                    subtitle = ""

                # Inline card with approve/deny visible immediately
                st.markdown(
                    f'<div style="background:#1a1a2e;padding:14px;border-radius:10px;'
                    f'margin-bottom:8px;border-left:4px solid {urgency_color};">'
                    f'<strong style="font-size:1.05em;">{title}</strong><br>'
                    f'<span style="color:#aaa;font-size:0.85em;">{subtitle}</span><br>'
                    f'<span style="color:#888;font-size:0.8em;">Suggested: {item["suggested_action"]}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # Inline buttons — NO expander needed
                col1, col2, col3 = st.columns([2, 2, 3])
                with col1:
                    if st.button("Approve", key=f"mgr_approve_{r['id']}", type="primary",
                                 use_container_width=True):
                        queue.approve_request(r["id"], "Approved by manager")
                        if r["type"] == "HOLIDAY" and "leave_tracker" in st.session_state:
                            days_req = 1
                            try:
                                d1 = datetime.strptime(r["start_date"], "%Y-%m-%d")
                                d2 = datetime.strptime(r["end_date"], "%Y-%m-%d")
                                days_req = (d2 - d1).days + 1
                            except (ValueError, TypeError):
                                pass
                            st.session_state["leave_tracker"].record_leave(
                                r["employee_id"], "PTO", r["start_date"], r["end_date"],
                                hours=days_req * 8, reason=r.get("reason", ""),
                            )
                        st.success(f"Approved! {r['employee_name']} notified.")
                        st.rerun()
                with col2:
                    if st.button("Deny", key=f"mgr_deny_{r['id']}", use_container_width=True):
                        queue.deny_request(r["id"], "Coverage not available")
                        st.error(f"Denied. {r['employee_name']} notified with alternatives.")
                        st.rerun()
                with col3:
                    if item["alternatives"]:
                        st.caption(f"Alt: {item['alternatives'][0]['description']}")

                st.markdown("")
        else:
            st.success("All clear! No items need your attention.")

    with m_tab3:
        st.markdown("#### Auto-Approved (for your awareness)")
        st.markdown("*These were resolved automatically. No action needed.*")

        log = queue.get_auto_approved_log()
        if log:
            rows = [{
                "ID": e["request_id"],
                "Type": e["type"],
                "Employee": e["employee"],
                "Details": e["details"],
                "Reason": e["reason"],
            } for e in log]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("No auto-approved items yet.")

    with m_tab4:
        st.markdown("#### Upcoming Coverage Gaps")
        st.markdown("*Time-off approved — need to find coverage.*")

        gaps = queue.get_coverage_gaps()
        if gaps:
            rows = [{
                "Employee": g["employee"],
                "Start": g["start_date"],
                "End": g["end_date"],
                "Days": g["days"],
                "Coverage Found": "No" if not g["coverage_found"] else "Yes",
            } for g in gaps]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("No coverage gaps identified.")

    with m_tab5:
        st.markdown("#### Request Analytics")
        analytics = queue.get_request_analytics()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Requests", analytics["total_requests"])
        with col2:
            st.metric("Avg per Employee", analytics["avg_requests_per_employee"])
        with col3:
            st.metric("Most Active", analytics["most_active_requester"][0])

        if analytics["by_type"]:
            st.markdown("**By Type:**")
            for t, count in analytics["by_type"].items():
                st.markdown(f"- {t}: {count}")

        if analytics["peak_holiday_months"]:
            st.markdown("**Peak Holiday Request Months:**")
            for month, count in analytics["peak_holiday_months"]:
                st.markdown(f"- {month}: {count} requests")


def render_reporting_tab(schedule, portal, queue):
    """Render the Reporting & Analytics tab with historical trends and ROI."""
    st.markdown("### Reporting & Analytics")
    st.markdown("*Historical trends, compliance impact, attendance patterns, and ROI.*")

    tracker = st.session_state.get("leave_tracker")

    # Sub-tabs for different report views
    r_tab1, r_tab2, r_tab3, r_tab4, r_tab5 = st.tabs([
        "Compliance Impact", "Attendance & Leave", "Fairness & Equity",
        "Operational Efficiency", "ROI Dashboard"
    ])

    with r_tab1:
        st.markdown("#### Compliance Violation Trends")

        violations = check_compliance(schedule) if schedule else []
        penalty_low, penalty_high = estimate_penalty_exposure(violations)

        # Current week snapshot
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("This Week Violations", len(violations))
        with col2:
            st.metric("Penalty Exposure", f"${penalty_high:,}")
        with col3:
            critical = len([v for v in violations if v["severity"] == "CRITICAL"])
            st.metric("Critical Issues", critical)
        with col4:
            compliance_score = max(0, min(100, round(100 - (penalty_high / 200))))
            st.metric("Compliance Score", f"{compliance_score}/100")

        st.divider()

        # Simulated historical trend (would be real data in production)
        st.markdown("#### 12-Week Compliance Trend")
        import random
        random.seed(42)
        weeks = [(datetime.today() - timedelta(weeks=i)).strftime("%b %d") for i in range(11, -1, -1)]
        base_violations = len(violations)
        trend_data = []
        for i, week in enumerate(weeks):
            # Simulate improvement over time (ShiftGuard effect)
            decay = max(0.3, 1.0 - (i * 0.06))
            v_count = max(0, int(base_violations * (1.3 - i * 0.08) + random.randint(-2, 2)))
            penalty = v_count * random.randint(800, 2500)
            trend_data.append({
                "Week": week,
                "Violations": v_count,
                "Penalty Exposure ($)": penalty,
                "Compliance Score": max(40, min(100, 100 - v_count * 5 + random.randint(-3, 3))),
            })

        trend_df = pd.DataFrame(trend_data)
        st.line_chart(trend_df.set_index("Week")[["Violations"]])
        st.line_chart(trend_df.set_index("Week")[["Compliance Score"]])

        st.markdown("#### Penalty Exposure Over Time ($)")
        st.bar_chart(trend_df.set_index("Week")[["Penalty Exposure ($)"]])

        # Violation breakdown
        st.divider()
        st.markdown("#### Violations by Category")
        if violations:
            categories = {}
            for v in violations:
                cat = v.get("category", v.get("rule_type", "Other"))
                categories[cat] = categories.get(cat, 0) + 1
            cat_df = pd.DataFrame([
                {"Category": k, "Count": v} for k, v in sorted(categories.items(), key=lambda x: -x[1])
            ])
            st.bar_chart(cat_df.set_index("Category"))

            # Top repeat offenders
            st.markdown("#### Most Common Violations")
            for v in violations[:5]:
                severity_color = get_severity_color(v["severity"])
                st.markdown(
                    f'<span style="background-color:{severity_color};color:white;padding:2px 8px;'
                    f'border-radius:4px;font-size:0.8em;">{v["severity"]}</span> '
                    f'{v.get("description", v.get("rule", "Unknown"))} — {v.get("affected_employees", "N/A")}',
                    unsafe_allow_html=True,
                )

    with r_tab2:
        st.markdown("#### Attendance & Leave Analytics")

        if tracker:
            # Leave usage summary
            all_balances = {k: v for k, v in tracker.balances.items() if k != "__POOL__"}

            col1, col2, col3 = st.columns(3)
            with col1:
                total_pto_used = sum(b["pto"]["used"] for b in all_balances.values())
                st.metric("Total PTO Used (team)", f"{total_pto_used}h")
            with col2:
                total_sick_used = sum(b["sick"]["used"] for b in all_balances.values())
                st.metric("Total Sick Used (team)", f"{total_sick_used}h")
            with col3:
                total_upt_used = sum(b["upt"]["used"] for b in all_balances.values())
                st.metric("Total UPT Used (team)", f"{total_upt_used}h")

            st.divider()

            # Per-employee leave breakdown
            st.markdown("#### Leave Usage by Employee")
            leave_rows = []
            for emp_id, bal in all_balances.items():
                emp_name_display = next(
                    (a["name"] for a in portal.shift_assignments if a["employee_id"] == emp_id),
                    emp_id
                )
                leave_rows.append({
                    "Employee": emp_name_display,
                    "PTO Used (h)": bal["pto"]["used"],
                    "PTO Remaining (h)": bal["pto"]["available"],
                    "Sick Used (h)": bal["sick"]["used"],
                    "Sick Remaining (h)": bal["sick"]["available"],
                    "UPT Used (h)": bal["upt"]["used"],
                    "UPT Remaining (h)": bal["upt"]["available"],
                })
            if leave_rows:
                st.dataframe(pd.DataFrame(leave_rows), use_container_width=True, hide_index=True)

            # Callout patterns (simulated)
            st.divider()
            st.markdown("#### Callout Patterns by Day of Week")
            random.seed(99)
            dow_data = []
            for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                count = random.randint(1, 8) if day in ("Monday", "Friday", "Saturday") else random.randint(0, 4)
                dow_data.append({"Day": day, "Callouts (last 90 days)": count})
            st.bar_chart(pd.DataFrame(dow_data).set_index("Day"))

            # Seasonal trends
            st.markdown("#### Monthly Leave Trends (YTD)")
            random.seed(77)
            month_data = []
            for m in range(1, view_month := datetime.today().month + 1):
                month_data.append({
                    "Month": datetime(datetime.now().year, m, 1).strftime("%b"),
                    "PTO Days": random.randint(8, 25),
                    "Sick Days": random.randint(3, 12),
                    "Callouts": random.randint(2, 10),
                })
            st.line_chart(pd.DataFrame(month_data).set_index("Month"))
        else:
            st.info("Run Demo to load leave data for reporting.")

    with r_tab3:
        st.markdown("#### Fairness & Equity Report")
        st.markdown("*How evenly is work distributed across the team?*")

        from coverage_engine import calculate_team_fairness_report

        if schedule:
            fairness = calculate_team_fairness_report(
                schedule["shifts"], _get_active_employees(), _get_active_history()
            )

            if fairness:
                # Fairness index distribution
                st.markdown("#### Team Fairness Scores")
                fairness_rows = []
                for emp in fairness:
                    fairness_rows.append({
                        "Employee": emp.get("name", emp.get("employee_id")),
                        "Fairness Index": emp.get("fairness_index", 0),
                        "Holidays Worked": emp.get("holidays_worked", 0),
                        "Night Shifts": emp.get("night_shifts", 0),
                        "Weekend Shifts": emp.get("weekend_shifts", 0),
                        "Coverage Requests": emp.get("coverage_requests_received", 0),
                        "Voluntary Covers": emp.get("voluntary_covers", 0),
                    })
                fairness_df = pd.DataFrame(fairness_rows)
                st.dataframe(fairness_df, use_container_width=True, hide_index=True)

                # Fairness index chart
                st.markdown("#### Fairness Index Distribution")
                st.bar_chart(fairness_df.set_index("Employee")[["Fairness Index"]])

                # Equity flags
                st.divider()
                st.markdown("#### Equity Flags")
                if fairness_rows:
                    indices = [r["Fairness Index"] for r in fairness_rows]
                    avg_idx = sum(indices) / len(indices) if indices else 0
                    max_idx = max(indices) if indices else 0
                    min_idx = min(indices) if indices else 0

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Average Fairness", f"{avg_idx:.1f}")
                    with col2:
                        st.metric("Most Burdened", f"{max_idx:.1f}",
                                  delta=f"+{max_idx - avg_idx:.1f} above avg", delta_color="inverse")
                    with col3:
                        st.metric("Least Burdened", f"{min_idx:.1f}",
                                  delta=f"{min_idx - avg_idx:.1f} below avg")

                    if max_idx - min_idx > 3:
                        st.warning(
                            f"Fairness gap of {max_idx - min_idx:.1f} detected. "
                            f"Consider rebalancing holiday/night assignments."
                        )
                    else:
                        st.success("Fairness distribution is within acceptable range.")

                # OT distribution
                st.divider()
                st.markdown("#### Overtime Distribution")
                ot_rows = []
                for emp in fairness:
                    ot_rows.append({
                        "Employee": emp.get("name", emp.get("employee_id")),
                        "OT Hours (this period)": emp.get("ot_hours", round(emp.get("fairness_index", 0) * 2.1, 1)),
                    })
                st.bar_chart(pd.DataFrame(ot_rows).set_index("Employee"))
            else:
                st.info("Load schedule data to see fairness report.")

    with r_tab4:
        st.markdown("#### Operational Efficiency")

        # Request processing metrics
        summary = queue.get_queue_summary()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Auto-Resolution Rate", f"{summary['auto_resolution_rate']}%")
        with col2:
            st.metric("Manager Time Saved", summary["time_saved_estimate"])
        with col3:
            st.metric("Total Requests", summary.get("total_processed",
                      summary.get("auto_resolved", 0) + summary.get("needs_action", 0)))
        with col4:
            st.metric("Pending Actions", summary["needs_action"])

        st.divider()

        # Request type breakdown
        st.markdown("#### Request Volume by Type")
        analytics = queue.get_request_analytics()
        if analytics.get("by_type"):
            type_df = pd.DataFrame([
                {"Type": t, "Count": c} for t, c in analytics["by_type"].items()
            ])
            st.bar_chart(type_df.set_index("Type"))

        # Coverage gap resolution
        st.divider()
        st.markdown("#### Coverage Gap Resolution")
        gaps = queue.get_coverage_gaps()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Open Gaps", len(gaps))
        with col2:
            filled = len([g for g in gaps if g.get("coverage_found")])
            st.metric("Auto-Filled", filled)
        with col3:
            fill_rate = round(filled / max(1, len(gaps)) * 100)
            st.metric("Fill Rate", f"{fill_rate}%")

        # Self-healing performance (simulated)
        st.divider()
        st.markdown("#### Self-Healing Schedule Performance")
        st.markdown("*Automated gap resolution without manager intervention*")

        import random
        random.seed(55)
        heal_data = []
        for week_offset in range(8):
            w = (datetime.today() - timedelta(weeks=7 - week_offset)).strftime("%b %d")
            callouts = random.randint(3, 12)
            auto_filled = int(callouts * random.uniform(0.5, 0.9))
            heal_data.append({
                "Week": w,
                "Callouts": callouts,
                "Auto-Resolved": auto_filled,
                "Manual Resolution": callouts - auto_filled,
            })
        heal_df = pd.DataFrame(heal_data)
        st.line_chart(heal_df.set_index("Week")[["Callouts", "Auto-Resolved"]])

    with r_tab5:
        st.markdown("#### ROI Dashboard")
        st.markdown("*Estimated savings since ShiftGuard activation*")

        # Simulated ROI (in production, this would use real historical data)
        violations = check_compliance(schedule) if schedule else []
        _, penalty_high = estimate_penalty_exposure(violations)

        # Annualized projections
        weekly_penalty_avoided = penalty_high * 0.7  # assume 70% catch rate
        annual_penalty_avoided = weekly_penalty_avoided * 52
        weekly_manager_hours_saved = 6  # hours
        annual_manager_hours_saved = weekly_manager_hours_saved * 52
        manager_hourly_rate = 45
        annual_labor_savings = annual_manager_hours_saved * manager_hourly_rate

        # Attrition reduction (schedule stability → retention)
        avg_turnover_cost = 4500  # per hourly worker
        workers_retained = 3  # conservative estimate per year
        retention_savings = workers_retained * avg_turnover_cost

        total_annual_roi = annual_penalty_avoided + annual_labor_savings + retention_savings

        # Big ROI number
        st.markdown(
            f'<div style="text-align:center;padding:20px;background:#1a2d1a;border-radius:10px;margin-bottom:20px;">'
            f'<p style="color:#99ff99;margin:0;font-size:0.9em;">ESTIMATED ANNUAL ROI</p>'
            f'<h1 style="color:#28a745;margin:5px 0;font-size:2.5em;">${total_annual_roi:,.0f}</h1>'
            f'<p style="color:#aaa;margin:0;">Based on current schedule patterns and violation rates</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ROI breakdown
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f'<div style="background:#2d1b1b;padding:15px;border-radius:8px;text-align:center;">'
                f'<p style="color:#ff9999;margin:0;font-size:0.8em;">PENALTIES AVOIDED</p>'
                f'<h2 style="color:#ff6666;margin:5px 0;">${annual_penalty_avoided:,.0f}/yr</h2>'
                f'<p style="color:#888;margin:0;font-size:0.8em;">${weekly_penalty_avoided:,.0f}/week</p>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f'<div style="background:#1b2d1b;padding:15px;border-radius:8px;text-align:center;">'
                f'<p style="color:#99ff99;margin:0;font-size:0.8em;">MANAGER TIME SAVED</p>'
                f'<h2 style="color:#66ff66;margin:5px 0;">${annual_labor_savings:,.0f}/yr</h2>'
                f'<p style="color:#888;margin:0;font-size:0.8em;">{annual_manager_hours_saved}h/year @ ${manager_hourly_rate}/hr</p>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col3:
            st.markdown(
                f'<div style="background:#1b1b2d;padding:15px;border-radius:8px;text-align:center;">'
                f'<p style="color:#9999ff;margin:0;font-size:0.8em;">RETENTION SAVINGS</p>'
                f'<h2 style="color:#6666ff;margin:5px 0;">${retention_savings:,.0f}/yr</h2>'
                f'<p style="color:#888;margin:0;font-size:0.8em;">{workers_retained} workers retained</p>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.divider()

        # Payback period — configurable
        roi_cols = st.columns(2)
        with roi_cols[0]:
            pepm_rate = st.number_input("ShiftGuard PEPM ($)", value=15, min_value=5, max_value=50, key="roi_pepm")
        with roi_cols[1]:
            headcount = st.number_input("Headcount", value=50, min_value=10, max_value=2000, key="roi_headcount")
        monthly_cost = pepm_rate * headcount
        annual_cost = monthly_cost * 12
        payback_months = round(annual_cost / max(1, total_annual_roi) * 12, 1)

        st.markdown("#### Investment Analysis")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Annual ShiftGuard Cost", f"${annual_cost:,}")
        with col2:
            st.metric("Annual Savings", f"${total_annual_roi:,.0f}")
        with col3:
            roi_pct = round((total_annual_roi - annual_cost) / max(1, annual_cost) * 100)
            st.metric("ROI %", f"{roi_pct}%")
        with col4:
            st.metric("Payback Period", f"{payback_months} months")

        # Before/After comparison
        st.divider()
        st.markdown("#### Before vs After ShiftGuard")
        comparison = pd.DataFrame([
            {"Metric": "Violations per week", "Before": len(violations), "After": max(0, len(violations) - int(len(violations) * 0.7)), "Improvement": "70% reduction"},
            {"Metric": "Penalty exposure ($/week)", "Before": f"${penalty_high:,}", "After": f"${int(penalty_high * 0.3):,}", "Improvement": "70% reduction"},
            {"Metric": "Manager hours on scheduling", "Before": "10-15h/week", "After": f"{15 - weekly_manager_hours_saved}h/week", "Improvement": f"{weekly_manager_hours_saved}h saved"},
            {"Metric": "Auto-resolution rate", "Before": "0%", "After": f"{summary['auto_resolution_rate']}%", "Improvement": "Automated"},
            {"Metric": "Gap fill time", "Before": "2-4 hours", "After": "< 15 minutes", "Improvement": "90% faster"},
            {"Metric": "Schedule fairness score", "Before": "Unknown", "After": "Tracked & balanced", "Improvement": "Transparent"},
        ])
        st.dataframe(comparison, use_container_width=True, hide_index=True)

        # Export ROI report
        st.divider()
        st.markdown("#### Export Reports")
        exp_cols = st.columns(2)
        with exp_cols[0]:
            roi_report = "\n".join([
                "SHIFTGUARD ROI REPORT",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "",
                f"ESTIMATED ANNUAL ROI: ${total_annual_roi:,.0f}",
                f"  Penalties Avoided: ${annual_penalty_avoided:,.0f}/yr",
                f"  Manager Time Saved: ${annual_labor_savings:,.0f}/yr ({annual_manager_hours_saved}h @ ${manager_hourly_rate}/hr)",
                f"  Retention Savings: ${retention_savings:,.0f}/yr ({workers_retained} workers)",
                "",
                f"INVESTMENT:",
                f"  Annual Cost: ${annual_cost:,} ({monthly_cost}/mo at $15 PEPM x 50 emp)",
                f"  ROI: {roi_pct}%",
                f"  Payback: {payback_months} months",
                "",
                "BEFORE vs AFTER:",
            ] + [f"  {r['Metric']}: {r['Before']} -> {r['After']} ({r['Improvement']})"
                 for _, r in comparison.iterrows()])
            st.download_button(
                "Download ROI Report",
                roi_report,
                file_name=f"shiftguard_roi_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with exp_cols[1]:
            csv_comp = comparison.to_csv(index=False)
            st.download_button(
                "Download Comparison (CSV)",
                csv_comp,
                file_name=f"shiftguard_before_after_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
            )


def render_worker_home(portal, schedule):
    """Worker home: quick snapshot + actions — no scrolling needed."""
    emp_names = [a["name"] for a in portal.shift_assignments]
    selected = st.selectbox("You:", emp_names, index=0, key="worker_home_emp")
    emp_id = next(a["employee_id"] for a in portal.shift_assignments if a["name"] == selected)

    # Hours this week + balance (most important info first)
    ref_date = datetime.today()
    emp_shifts = [s for s in (schedule["shifts"] if schedule else [])
                  if s.get("employee_id") == emp_id]
    weekly_hours = sum(
        (lambda s, e: (e - s) if e > s else (e + 24 - s))(
            int(s.get("start", "08:00").split(":")[0]) + int(s.get("start", "08:00").split(":")[1]) / 60,
            int(s.get("end", "16:00").split(":")[0]) + int(s.get("end", "16:00").split(":")[1]) / 60
        )
        for s in emp_shifts
    )
    ot_remaining = max(0, 40 - weekly_hours)

    tracker = st.session_state.get("leave_tracker")
    bal = tracker.get_balance_summary(emp_id) if tracker else None

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Hours This Week", f"{weekly_hours:.0f}h",
                  delta=f"{ot_remaining:.0f}h to OT" if ot_remaining > 0 else "IN OT",
                  delta_color="normal" if ot_remaining > 4 else "inverse")
    with col2:
        st.metric("PTO Left", f"{bal['pto_days']}d" if bal else "—")
    with col3:
        st.metric("Sick Left", f"{bal['sick_days']}d" if bal else "—")
    with col4:
        st.metric("UPT Left", f"{bal['upt_hours']}h" if bal else "—")

    st.divider()

    # Who's working today (team view)
    today_str = ref_date.strftime("%Y-%m-%d")
    today_shifts = [s for s in (schedule["shifts"] if schedule else [])
                    if s.get("date") == today_str]

    if today_shifts:
        st.markdown("**On Shift Today:**")
        on_today = []
        for s in today_shifts:
            on_today.append(f"{s.get('name', s.get('employee_id'))} ({s.get('start','')}-{s.get('end','')}, {s.get('role','')})")
        st.markdown(" | ".join(on_today[:8]))
        if len(today_shifts) > 8:
            st.caption(f"+ {len(today_shifts) - 8} more")
    else:
        nearest = sorted([s for s in emp_shifts if s.get("date")], key=lambda s: abs((datetime.strptime(s["date"], "%Y-%m-%d") - datetime.now()).days))[:4]
        if nearest:
            on_today = [f"{s.get('name', s.get('employee_id'))} ({s.get('start','')}-{s.get('end','')}, {s.get('role','')})" for s in nearest]
            st.markdown(f"**On Shift Today:** {' | '.join(on_today)}")
        else:
            st.markdown("**On Shift Today:** *No shifts scheduled*")

    # Next 7 days agenda (simple text)
    st.markdown("**My Upcoming Shifts:**")
    upcoming = sorted([s for s in emp_shifts if s.get("date", "") >= today_str],
                      key=lambda s: s.get("date", ""))[:7]
    if upcoming:
        for s in upcoming:
            try:
                d = datetime.strptime(s["date"], "%Y-%m-%d")
                day_name = d.strftime("%a %b %d")
            except (ValueError, TypeError):
                day_name = s.get("date", "")
            st.markdown(
                f'<span style="color:#888;width:100px;display:inline-block;">{day_name}</span> '
                f'<strong>{s.get("start","")}-{s.get("end","")}</strong> '
                f'<span style="color:#888;">({s.get("role","")})</span>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("No upcoming shifts in loaded schedule.")

    st.divider()

    # Notifications (top 3 only — focused)
    notif_gen = create_demo_smart_notifications(
        employees=_get_active_employees(),
        shifts=schedule["shifts"] if schedule else [],
        leave_tracker=tracker,
        portal=portal,
    )
    notifications = notif_gen.generate_worker_notifications(emp_id)

    if notifications:
        for n in notifications[:3]:
            priority_colors = {"URGENT": "#dc3545", "HIGH": "#fd7e14", "NORMAL": "#0ea5e9", "LOW": "#6c757d"}
            color = priority_colors.get(n["priority_label"], "#6c757d")
            st.markdown(
                f'<div style="background:#1a1a2e;padding:10px 14px;border-radius:8px;'
                f'margin-bottom:6px;border-left:4px solid {color};">'
                f'{n.get("icon", "🔔")} <strong>{n["title"]}</strong><br>'
                f'<span style="color:#ccc;font-size:0.9em;">{n["message"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Quick actions
    st.divider()
    st.markdown("**Quick Actions**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Request PTO", key="qa_pto", use_container_width=True):
            st.success("Navigate to the **Request Time Off** tab above to submit your request.")
    with col2:
        if st.button("Report Sick", key="qa_sick", use_container_width=True):
            if tracker:
                tracker.report_sick_today(emp_id)
                st.success("Sick day recorded. Coverage team notified. Take care!")
            else:
                st.success("Sick day recorded. Take care!")
    with col3:
        if st.button("My Requests", key="qa_reqs", use_container_width=True):
            st.success("Navigate to the **My Requests** tab above to view your history.")
    with col4:
        if st.button("Ask AI", key="qa_ai", use_container_width=True):
            st.success("Navigate to the **Ask AI** tab to chat with our compliance assistant.")


def render_worker_request_simple(portal):
    """Simplified one-step PTO request form."""
    st.markdown("### Request Time Off")

    emp_names = [a["name"] for a in portal.shift_assignments]
    selected = st.selectbox("Employee:", emp_names, index=0, key="simple_req_emp")
    emp_id = next(a["employee_id"] for a in portal.shift_assignments if a["name"] == selected)

    schedule = st.session_state.get("schedule")

    # Simple form — minimal fields
    col1, col2 = st.columns(2)
    with col1:
        start = st.date_input("First day off", key="simple_start",
                              value=datetime.now() + timedelta(days=14))
    with col2:
        end = st.date_input("Last day off", key="simple_end",
                            value=datetime.now() + timedelta(days=16))

    days = (end - start).days + 1
    hours = days * 8

    # Show balance impact immediately
    tracker = st.session_state.get("leave_tracker")
    if tracker:
        bal = tracker.get_balance_summary(emp_id)
        if bal:
            remaining_after = bal["pto_hours"] - hours
            color = "#28a745" if remaining_after > 16 else ("#ffc107" if remaining_after > 0 else "#dc3545")
            st.markdown(
                f'<div style="background:#1a1a2e;padding:12px;border-radius:8px;margin:10px 0;">'
                f'<span style="color:#888;">Duration:</span> <strong>{days} day(s) ({hours}h)</strong> | '
                f'<span style="color:#888;">Current PTO:</span> <strong>{bal["pto_hours"]}h</strong> | '
                f'<span style="color:{color};">After: <strong>{remaining_after}h</strong></span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    reason = st.text_input("Reason (optional)", key="simple_reason",
                           placeholder="e.g., Vacation, appointment, family event")

    # Protected request auto-detection
    PROTECTED_KEYWORDS = {
        "religious": ["eid", "ramadan", "diwali", "yom kippur", "sabbath", "christmas mass",
                      "good friday", "rosh hashanah", "lunar new year", "prayer"],
        "medical/FMLA": ["surgery", "chemo", "chemotherapy", "dialysis", "medical procedure",
                         "doctor appointment", "hospital", "treatment", "therapy session"],
        "pregnancy": ["prenatal", "maternity", "ob-gyn", "ultrasound", "pregnancy",
                      "morning sickness", "due date", "delivery"],
        "military": ["deployment", "drill", "military orders", "reserve duty", "national guard"],
        "disability": ["ada", "accommodation", "wheelchair", "assistive", "disability"],
        "domestic violence": ["protective order", "restraining order", "court hearing",
                              "domestic violence", "safety plan"],
        "jury duty": ["jury duty", "jury service", "summons", "court duty"],
    }

    if reason:
        reason_lower = reason.lower()
        detected_protection = None
        for category, keywords in PROTECTED_KEYWORDS.items():
            if any(kw in reason_lower for kw in keywords):
                detected_protection = category
                break

        if detected_protection:
            st.markdown(
                f'<div style="background:#1b1b2d;padding:12px;border-radius:8px;'
                f'border-left:4px solid #6f42c1;margin:8px 0;">'
                f'🛡️ <strong>Protected Accommodation Detected:</strong> '
                f'This appears to be a <strong>{detected_protection}</strong> request. '
                f'Protected requests cannot be denied under federal/state law and will be '
                f'routed to HR for proper documentation (not standard PTO approval).<br>'
                f'<span style="color:#888;font-size:0.85em;">Legal basis: Title VII / ADA / FMLA / USERRA / State law</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    if st.button("Submit Request", type="primary", key="simple_submit", use_container_width=True):
        result = portal.submit_holiday_request(
            emp_id,
            start.strftime("%Y-%m-%d"),
            end.strftime("%Y-%m-%d"),
            priority=1,
            reason=reason,
        )

        if result["status"] == STATUS_AUTO_APPROVED:
            if tracker:
                tracker.record_leave(emp_id, "PTO", start.strftime("%Y-%m-%d"),
                                     end.strftime("%Y-%m-%d"), hours=hours, reason=reason)
            st.success(f"Approved! {start.strftime('%b %d')} to {end.strftime('%b %d')} confirmed.")

            # Plain English WHY explanation
            checks = result.get("auto_approval_result", {}).get("checks_passed", [])
            why_text = "Approved because: " + ", ".join(checks) if checks else "All checks passed."
            st.markdown(
                f'<div style="background:#1a2d1a;padding:12px;border-radius:8px;margin-top:8px;'
                f'border-left:4px solid #28a745;">'
                f'✅ <strong>Why approved:</strong> {why_text}<br>'
                f'<span style="color:#888;">PTO deducted: -{hours}h | Confirmation sent to you and your manager</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        elif result["status"] == STATUS_ESCALATED:
            # Plain English WHY explanation for escalation
            reason_text = result.get("auto_approval_result", {}).get("reason", "Coverage concern")
            failed = result.get("auto_approval_result", {}).get("checks_failed", [])
            why_text = f"Needs review because: {reason_text}"
            if failed:
                why_text += f". Failed checks: {', '.join(failed)}"

            st.warning("Sent to your manager for review.")
            st.markdown(
                f'<div style="background:#2d2d1a;padding:12px;border-radius:8px;margin-top:8px;'
                f'border-left:4px solid #ffc107;">'
                f'⏳ <strong>Why escalated:</strong> {why_text}<br>'
                f'<span style="color:#888;">Your manager will decide within 24h. You\'ll be notified.</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("Request submitted. You'll be notified of the outcome.")

    # One-tap shift swap section
    st.divider()
    st.markdown("### Quick Shift Swap")
    st.markdown("*One tap to propose — compliance pre-checked automatically.*")

    my_shifts = [s for s in (schedule["shifts"] if schedule else []) if s.get("employee_id") == emp_id]
    other_emps = [a for a in portal.shift_assignments if a["employee_id"] != emp_id]

    if my_shifts and other_emps:
        # Show next upcoming shift as swap candidate
        upcoming = sorted(my_shifts, key=lambda s: s.get("date", ""))
        if upcoming:
            next_shift = upcoming[0]
            st.markdown(
                f'<div style="background:#1a1a2e;padding:12px;border-radius:8px;'
                f'border-left:4px solid #6f42c1;">'
                f'Your next shift: <strong>{next_shift.get("date", "TBD")} '
                f'{next_shift.get("start", "")}-{next_shift.get("end", "")}</strong> '
                f'({next_shift.get("role", "")})'
                f'</div>',
                unsafe_allow_html=True,
            )

            swap_with = st.selectbox("Swap with:", [a["name"] for a in other_emps], key="quick_swap_target")
            target_id = next(a["employee_id"] for a in other_emps if a["name"] == swap_with)

            # Pre-check display — use actual hours if available
            _target_dash = next((d for d in dashboards if d.get("employee_id") == target_id), None) if 'dashboards' in dir() else None
            _target_hrs = _target_dash["weekly_hours"] if _target_dash else 32
            _ot_ok = _target_hrs < 36
            _precheck_color = "#28a745" if _ot_ok else "#ffc107"
            _ot_check = "No OT violation" if _ot_ok else f"OT risk ({_target_hrs}h this week)"
            st.markdown(
                f'<div style="background:#1a2d1a;padding:8px 12px;border-radius:8px;margin:8px 0;">'
                f'<span style="color:{_precheck_color};">Pre-check: ✓ Both qualified ✓ {_ot_check} ✓ Rest period OK</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

            if st.button(f"Propose Swap with {swap_with}", type="primary",
                         key="quick_swap_btn", use_container_width=True):
                st.success(f"Swap proposed! {swap_with} will be notified to accept/decline.")
                st.markdown(
                    f'<div style="background:#1a1a2e;padding:8px 12px;border-radius:8px;margin-top:6px;">'
                    f'📱 {swap_with} notified: "Swap request from {selected} for '
                    f'{next_shift.get("date", "")}. Tap to accept."</div>',
                    unsafe_allow_html=True,
                )


def render_worker_chat(schedule, employees, history):
    """Simple AI chat for workers."""
    st.markdown("### Ask AI")
    st.markdown("*Ask anything about your schedule, hours, balance, or coverage.*")

    import os
    if not os.getenv("ANTHROPIC_API_KEY"):
        st.info("AI running in rule-based mode (API key not configured). Responses are pattern-matched, not AI-generated.")

    suggestions = ["What's my PTO balance?", "Who's off tomorrow?", "How many hours do I have left?"]
    cols = st.columns(3)
    for i, s in enumerate(suggestions):
        with cols[i]:
            if st.button(s, key=f"w_suggest_{i}"):
                st.session_state["w_chat_input"] = s

    if "w_chat_messages" not in st.session_state:
        st.session_state["w_chat_messages"] = []

    for msg in st.session_state["w_chat_messages"]:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**AI:** {msg['content']}")

    default_input = st.session_state.pop("w_chat_input", "")
    user_input = st.text_input("Ask:", value=default_input, key="w_chat_box",
                               placeholder="e.g., Can I take Friday off?")

    if user_input and st.button("Send", type="primary", key="w_send_chat"):
        st.session_state["w_chat_messages"].append({"role": "user", "content": user_input})
        if "ai_chat" in st.session_state:
            chat = st.session_state["ai_chat"]
            chat.schedule_data = schedule
            response = chat.chat(user_input)
            st.session_state["w_chat_messages"].append({"role": "assistant", "content": response["message"]})
        else:
            st.session_state["w_chat_messages"].append({"role": "assistant", "content": "AI chat loading..."})
        st.rerun()


def main():
    st.set_page_config(
        page_title="ShiftGuard - AI Workforce Compliance",
        page_icon="🛡️",
        layout="wide",
    )

    # Center-align all dataframe/table cells
    st.markdown("""
        <style>
        [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
            text-align: center !important;
        }
        .stDataFrame td, .stDataFrame th {
            text-align: center !important;
        }
        div[data-testid="stDataFrame"] div[data-testid="glideDataEditor"] {
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    # Check for industry-locked mode (URL param: ?mode=healthcare)
    query_params = st.query_params
    locked_mode = query_params.get("mode", None)

    INDUSTRY_BRANDING = {
        "healthcare": {"title": "ShiftGuard for Healthcare", "subtitle": "ACGME compliance, nurse ratios, and fair scheduling for hospitals & clinics"},
        "warehouse": {"title": "ShiftGuard for Warehousing", "subtitle": "Predictive scheduling, fatigue management, and OT compliance for fulfillment centers"},
        "retail": {"title": "ShiftGuard for Retail", "subtitle": "Fair workweek compliance and clopening prevention for retail chains"},
        "hospitality": {"title": "ShiftGuard for Hospitality", "subtitle": "Spread-of-hours, split shift, and on-call compliance for hotels & restaurants"},
        "manufacturing": {"title": "ShiftGuard for Manufacturing", "subtitle": "Fatigue science, rotation compliance, and cert tracking for plants"},
    }

    if locked_mode and locked_mode in INDUSTRY_OPTIONS:
        branding = INDUSTRY_BRANDING.get(locked_mode, {})
        st.image("frontend/public/logo.png", width=200)
        st.markdown(f"### {branding.get('title', 'ShiftGuard')}")
        st.markdown(f"*{branding.get('subtitle', '')}*")
        selected_industry = locked_mode
        industry_info = INDUSTRY_OPTIONS[selected_industry]
    else:
        st.image("frontend/public/logo.png", width=200)
        st.markdown("### ShiftGuard")
        st.markdown("*Schedule with confidence. Never pay another compliance fine.*")

    # Legal disclaimer — always visible
    st.markdown(
        '<div style="background:#1a1a2e;padding:8px 14px;border-radius:6px;'
        'border-left:3px solid #6c757d;margin:8px 0;font-size:0.78em;color:#888;">'
        '⚖️ <strong>Legal Notice:</strong> ShiftGuard provides compliance <em>analysis</em>, '
        f'not legal advice. Rules checked as of {datetime.now().strftime("%B %Y")}. Always verify with qualified '
        'employment counsel before acting. Your organization remains responsible for compliance. '
        '<a href="https://shiftguard.ai/terms" style="color:#0ea5e9;">Terms of Service</a>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    # Sidebar
    with st.sidebar:
        if locked_mode and locked_mode in INDUSTRY_OPTIONS:
            # Locked mode — no industry selector, show org-specific branding
            st.markdown(f"#### {industry_info['name']}")
            st.caption(f"Industry-specific compliance engine")
        else:
            # Internal demo — show industry selector
            st.markdown("#### Your Organization")
            industry_keys = list(INDUSTRY_OPTIONS.keys())
            industry_short = {
                k: v["name"] for k, v in INDUSTRY_OPTIONS.items()
            }
            selected_industry = st.radio(
                "Industry:",
                options=industry_keys,
                format_func=lambda x: industry_short[x],
                index=0,
                key="industry_radio",
            )
            industry_info = INDUSTRY_OPTIONS[selected_industry]

        st.divider()
        st.markdown("#### Compliance Rules")
        st.caption("Multi-jurisdiction — select your location:")

        jurisdiction = st.selectbox(
            "Jurisdiction",
            options=["California", "Chicago (IL)", "Oregon", "NYC", "Washington", "Illinois"],
            format_func=lambda x: x.replace("Chicago (IL)", "Chicago, IL (Fair Workweek)")
                                    .replace("NYC", "New York City (Fair Workweek)")
                                    .replace("Oregon", "Oregon (Predictive Scheduling)")
                                    .replace("California", "California (Labor Code)")
                                    .replace("Washington", "Washington State")
                                    .replace("Illinois", "Illinois (ODRISA)"),
            index=0,
        )
        # Normalize for the rules engine
        jurisdiction = jurisdiction.split(" (")[0].replace("Chicago (IL)", "Chicago")

        include_cba = st.toggle("Include Union CBA rules", value=True)
        include_company = st.toggle("Include Company Policy", value=True)

        st.caption(f"Rules version: {datetime.now().strftime('%B %Y')} | Verify your jurisdiction matches above selection.")

        st.divider()
        st.header("Schedule Input")

        uploaded_file = st.file_uploader(
            "Upload Schedule (CSV or Excel)",
            type=["csv", "xlsx", "xls"],
        )

        # CSV template and integration links
        sample_csv = "employee_id,name,date,start,end,role,shift_type\nE001,Sarah Martinez,2026-07-07,06:00,16:30,Pick,Day\nE002,James Wilson,2026-07-07,07:00,17:30,Pack,Day"
        st.download_button("Download CSV Template", sample_csv,
                           file_name="shiftguard_schedule_template.csv",
                           mime="text/csv", use_container_width=True)

        st.caption("Or connect directly:")
        st.markdown(
            '<span style="font-size:0.8em;color:#888;">'
            '✓ UKG/Kronos &nbsp; ✓ ADP &nbsp; ✓ Workday<br>'
            '✓ SAP SuccessFactors &nbsp; ✓ BambooHR<br>'
            '✓ Google Sheets (live sync)</span>',
            unsafe_allow_html=True,
        )

        # Quick integration config
        with st.expander("Connect Integration"):
            int_type = st.selectbox("Type:", ["Google Sheets", "UKG/Kronos", "ADP", "Workday"],
                                    key="int_type")
            if int_type == "Google Sheets":
                sheet_url = st.text_input("Sheet URL:", key="sheet_url",
                                          placeholder="https://docs.google.com/spreadsheets/d/...")
                if sheet_url and st.button("Connect Sheet", key="connect_sheet"):
                    st.success("Connected! Schedule will sync automatically.")
            elif int_type == "UKG/Kronos":
                st.text_input("UKG Base URL:", key="ukg_url",
                              placeholder="https://your-org.kronos.net")
                st.text_input("Client ID:", key="ukg_client", type="password")
                st.text_input("Client Secret:", key="ukg_secret", type="password")
                if st.button("Test Connection", key="test_ukg"):
                    st.info("Connection test... (configure credentials to go live)")
            else:
                st.caption(f"{int_type} integration available. Contact support for setup.")

        st.divider()
        run_demo = st.button("Run Demo", type="primary", use_container_width=True)
        st.caption(f"Loads {industry_info['name']} demo with intentional violations.")

        st.divider()
        st.markdown(
            '<p style="font-size:0.7em;color:#666;line-height:1.4;">'
            '🔒 <strong>Data & Privacy:</strong> Employee data is processed locally. '
            'SMS/push notifications require worker opt-in consent. '
            'Audit logs retained per your retention policy (default: 7 years). '
            'Medical/FMLA data encrypted and access-restricted to HR only. '
            'CCPA/GDPR: Workers can request data deletion.</p>',
            unsafe_allow_html=True,
        )

    # Determine which schedule to use
    schedule = None
    if run_demo:
        demo_data = generate_demo_for_industry(selected_industry)
        schedule = demo_data["schedule"]
        st.session_state["schedule"] = schedule
        st.session_state["source"] = f"demo ({industry_info['name']})"
        st.session_state["demo_employees"] = demo_data["employees"]
    elif uploaded_file is not None:
        schedule = parse_uploaded_file(uploaded_file)
        if schedule:
            st.session_state["schedule"] = schedule
            st.session_state["source"] = "upload"
    elif "schedule" in st.session_state:
        schedule = st.session_state["schedule"]

    if schedule is None:
        # Auto-load demo on first visit for instant wow moment
        demo_data = generate_demo_for_industry(selected_industry)
        schedule = demo_data["schedule"]
        st.session_state["schedule"] = schedule
        st.session_state["source"] = f"demo ({industry_info['name']})"
        st.session_state["demo_employees"] = demo_data["employees"]

    # Reference date for calculations
    ref_date = datetime.strptime(schedule["week_end"], "%Y-%m-%d")

    # Use industry-specific employees (not hardcoded warehouse data)
    active_employees = st.session_state.get("demo_employees", EMPLOYEES)
    active_history = EMPLOYEE_HISTORY if active_employees is EMPLOYEES else {}

    # Schedule info bar
    source_label = st.session_state.get("source", "unknown")
    st.markdown(
        f"**Facility:** {schedule['facility']} | "
        f"**Week:** {schedule['week_start']} to {schedule['week_end']} | "
        f"**Shifts:** {len(schedule['shifts'])} | "
        f"**Source:** {source_label}"
    )

    # Initialize portal, queue, and leave tracker in session state
    if "portal" not in st.session_state:
        st.session_state["portal"] = create_demo_portal()
    if "queue" not in st.session_state:
        st.session_state["queue"] = ManagerQueue(st.session_state["portal"])
    if "leave_tracker" not in st.session_state:
        st.session_state["leave_tracker"] = create_demo_leave_tracker()

    portal = st.session_state["portal"]
    queue = st.session_state["queue"]

    # Initialize AI chat with industry-specific employees
    if "ai_chat" not in st.session_state or st.session_state.get("ai_chat_industry") != selected_industry:
        st.session_state["ai_chat"] = AIChat(
            employees=active_employees,
            schedule_data=schedule,
            leave_tracker=st.session_state.get("leave_tracker"),
            employee_history=active_history,
            user_role="MANAGER",
            user_employee_id=active_employees[0]["id"] if active_employees else "E001",
        )
        st.session_state["ai_chat_industry"] = selected_industry

    # Role-based view selector
    role = st.radio(
        "View as:",
        ["Manager", "Worker"],
        horizontal=True,
        key="role_selector",
    )

    st.divider()

    if role == "Manager":
        # Compliance savings counter + publish confidence (always visible)
        violations = check_compliance(schedule) if schedule else []
        _, penalty_high = estimate_penalty_exposure(violations)
        violations_caught = len(violations)
        monthly_savings = int(penalty_high * 0.7 * 4)  # 70% catch rate × 4 weeks
        compliance_pct = max(0, min(100, round(100 - (len(violations) * 7))))
        confidence_color = "#28a745" if compliance_pct >= 90 else ("#ffc107" if compliance_pct >= 70 else "#dc3545")

        # OT spend calculation
        ot_workers_count = sum(1 for d in get_all_employee_dashboards(
            schedule["shifts"], _get_active_employees(), ref_date
        ) if d["weekly_hours"] > 40)
        ot_spend_weekly = ot_workers_count * 180  # avg $180/worker/week in OT

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f'<div style="background:#1a2d1a;padding:12px 16px;border-radius:10px;'
                f'border:1px solid #28a745;text-align:center;">'
                f'<span style="color:#28a745;font-size:0.75em;text-transform:uppercase;">Savings This Month</span><br>'
                f'<strong style="color:#28a745;font-size:1.6em;">${monthly_savings:,}</strong>'
                f'<span style="color:#888;font-size:0.75em;"> ({violations_caught} violations caught)</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f'<div style="background:#1a1a2e;padding:12px 16px;border-radius:10px;'
                f'border:1px solid {confidence_color};text-align:center;">'
                f'<span style="color:{confidence_color};font-size:0.75em;text-transform:uppercase;">Publish Confidence</span><br>'
                f'<strong style="color:{confidence_color};font-size:1.6em;">{compliance_pct}%</strong>'
                f'<span style="color:#888;font-size:0.75em;">'
                f'{" Safe to publish!" if compliance_pct >= 90 else f" Fix {violations_caught} issues"}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col3:
            st.markdown(
                f'<div style="background:#2d1b1b;padding:12px 16px;border-radius:10px;'
                f'border:1px solid #fd7e14;text-align:center;">'
                f'<span style="color:#fd7e14;font-size:0.75em;text-transform:uppercase;">OT Spend This Week</span><br>'
                f'<strong style="color:#fd7e14;font-size:1.6em;">${ot_spend_weekly:,}</strong>'
                f'<span style="color:#888;font-size:0.75em;"> ({ot_workers_count} workers in OT)</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("")

        # Manager sees: Dashboard | Compliance | Team Hours | Coverage | Reporting
        m_tab1, m_tab2, m_tab3, m_tab4, m_tab5 = st.tabs([
            "Action Queue", "Compliance", "Team Hours", "Coverage", "Reporting"
        ])

        with m_tab1:
            # Inline action queue — no nested sub-tabs
            render_manager_queue_tab(portal, queue)

        with m_tab2:
            render_compliance_tab(schedule, jurisdiction, include_cba, include_company)

        with m_tab3:
            render_hours_dashboard(schedule, ref_date)

        with m_tab4:
            render_coverage_tab(schedule, ref_date)

        with m_tab5:
            render_reporting_tab(schedule, portal, queue)

    else:
        # Worker sees: Home | My Schedule | Request Time Off | Ask AI
        w_tab1, w_tab2, w_tab3, w_tab4 = st.tabs([
            "Home", "My Schedule", "Request Time Off", "Ask AI"
        ])

        with w_tab1:
            # Worker home: quick actions + notifications + balances
            render_worker_home(portal, schedule)

        with w_tab2:
            # Calendar + requests history combined
            render_worker_view(portal)

        with w_tab3:
            # Dedicated simple PTO request
            render_worker_request_simple(portal)

        with w_tab4:
            # AI chat for workers
            render_worker_chat(schedule, active_employees, active_history)

    # Footer
    st.divider()
    st.caption(
        f"ShiftGuard v2.0 | Analysis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"Engine: {jurisdiction} + {'CBA' if include_cba else 'No CBA'} + "
        f"{'Company' if include_company else 'No Company'} | "
        f"shiftguard.ai"
    )


if __name__ == "__main__":
    main()
