# Workforce Compliance AI - Streamlit Web Application
# Requirements: pip install streamlit pandas openpyxl
# Run with: streamlit run app.py

import streamlit as st
import pandas as pd
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

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Critical", len(critical))
    with col2:
        st.metric("High", len(high))
    with col3:
        st.metric("Medium", len(medium))
    with col4:
        st.metric("Penalty Exposure", f"${penalty_low:,}-${penalty_high:,}")

    st.divider()

    sorted_violations = sorted(
        violations,
        key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}.get(x["severity"], 3),
    )

    for i, v in enumerate(sorted_violations, 1):
        color = get_severity_color(v["severity"])
        with st.expander(f"#{i} [{v['severity']}] {v['rule_id']} - {v['rule_name']} | {v['affected_employees']}"):
            st.markdown(
                f'<span style="background-color:{color};color:white;padding:4px 12px;'
                f'border-radius:4px;font-weight:bold;">{v["severity"]}</span>',
                unsafe_allow_html=True,
            )
            st.markdown("")
            col_left, col_right = st.columns(2)
            with col_left:
                st.markdown(f"**Rule:** {v['rule_id']} - {v['rule_name']}")
                st.markdown(f"**Affected:** {v['affected_employees']}")
            with col_right:
                st.markdown(f"**Cost Impact:** {v['cost_impact']}")
            st.markdown(f"**Issue:** {v['description']}")
            st.markdown(f"**Fix:** {v['recommendation']}")


def render_hours_dashboard(schedule, reference_date):
    """Render the hours tracking dashboard."""
    dashboards = get_all_employee_dashboards(schedule["shifts"], EMPLOYEES, reference_date)

    st.markdown("### Real-Time Hours & Fatigue")

    # Summary metrics
    red_count = sum(1 for d in dashboards if d["fatigue_level"] == "red")
    yellow_count = sum(1 for d in dashboards if d["fatigue_level"] == "yellow")
    ot_count = sum(1 for d in dashboards if d["weekly_hours"] > OT_THRESHOLD_WEEKLY)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Fatigue RED", red_count, help="Employees at critical fatigue level")
    with col2:
        st.metric("Fatigue YELLOW", yellow_count, help="Employees at moderate fatigue")
    with col3:
        st.metric("In Overtime", ot_count, help="Employees past 40hr threshold")

    st.divider()

    # Employee table
    rows = []
    for d in sorted(dashboards, key=lambda x: x["fatigue_score"], reverse=True):
        rows.append({
            "Employee": d["name"],
            "Role": d["role"],
            "Weekly Hours": d["weekly_hours"],
            "Consec. Days": d["consecutive_days"],
            "OT Remaining": d["hours_remaining_before_ot"],
            "Cap Remaining": d["hours_remaining_before_cap"],
            "Fatigue Score": d["fatigue_score"],
            "Fatigue Level": d["fatigue_level"].upper(),
            "Day/Eve/Night": f"{d['shift_type_distribution']['day']}/{d['shift_type_distribution']['evening']}/{d['shift_type_distribution']['night']}",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Predictive blocking demo
    st.divider()
    st.markdown("### Predictive Shift Impact")
    st.markdown("*What happens if you add a shift to an employee?*")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        emp_names = [e["name"] for e in EMPLOYEES]
        selected_emp = st.selectbox("Employee", emp_names, index=1)
    with col2:
        proposed_date = st.date_input("Date", value=reference_date + timedelta(days=2))
    with col3:
        proposed_start = st.selectbox("Start", ["06:00", "14:00", "22:00"], index=0)
    with col4:
        proposed_end = st.selectbox("End", ["14:30", "22:30", "06:30"], index=0)

    emp_id = next(e["id"] for e in EMPLOYEES if e["name"] == selected_emp)
    proposed_shift = {
        "employee_id": emp_id,
        "name": selected_emp,
        "date": proposed_date.strftime("%Y-%m-%d"),
        "start": proposed_start,
        "end": proposed_end,
        "role": next(e["role"] for e in EMPLOYEES if e["name"] == selected_emp),
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
        ["(none)"] + [e["name"] for e in EMPLOYEES],
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
            (e["id"] for e in EMPLOYEES if e["name"] == absent_emp), None
        )

    candidates = find_coverage(
        schedule["shifts"], EMPLOYEES, gap_shift, EMPLOYEE_HISTORY, reference_date
    )

    if candidates:
        st.divider()
        st.markdown(f"**{len(candidates)} available candidates** (ranked by fairness):")

        for i, c in enumerate(candidates, 1):
            fatigue_color = get_fatigue_color(c["fatigue_level"])
            with st.expander(
                f"#{i} {c['name']} — Score: {c['composite_score']}/100 | "
                f"Weekly: {c['current_weekly_hours']}h | Fatigue: {c['fatigue_level'].upper()}"
            ):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Role:** {c['role']} | **Seniority:** {c['seniority']}")
                    st.markdown(f"**OT before threshold:** {c['hours_remaining_before_ot']}h")
                    st.markdown(f"**Est. OT cost if assigned:** ${c['estimated_ot_cost']:.2f}")
                with col2:
                    st.markdown("**Fairness Scores:**")
                    for k, v in c["scores"].items():
                        bar_pct = min(100, v)
                        st.markdown(f"  {k}: {v}/100")

                st.markdown(f"**Why:** {c['reason']}")
    else:
        st.warning("No eligible candidates found for this shift configuration.")

    # Team fairness report
    st.divider()
    st.markdown("### Team Fairness Report")

    report = calculate_team_fairness_report(
        schedule["shifts"], EMPLOYEES, EMPLOYEE_HISTORY, reference_date
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
        emp_name = next((e["name"] for e in EMPLOYEES if e["id"] == emp_id), emp_id)
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
    for emp in EMPLOYEES:
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
                EMPLOYEES, h_date, shifts_needed,
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

    st.divider()

    # Tabs within worker view
    w_tab1, w_tab2, w_tab3, w_tab4, w_tab5, w_tab6 = st.tabs([
        "Leave & Balances", "My Requests", "Request Time Off", "VET & Open Shifts", "Shift Swap", "My Preferences"
    ])

    with w_tab1:
        if "leave_tracker" in st.session_state:
            render_leave_management(st.session_state["leave_tracker"], emp_id, selected)
        else:
            st.info("Run Demo to load leave data.")

    with w_tab1:
        st.markdown("#### My Request History")
        my_requests = [r for r in portal.requests if r["employee_id"] == emp_id]

        if my_requests:
            for r in my_requests:
                status_color = {
                    "AUTO_APPROVED": "#28a745", "APPROVED": "#28a745",
                    "PENDING": "#ffc107", "ESCALATED": "#fd7e14",
                    "DENIED": "#dc3545",
                }.get(r["status"], "#6c757d")

                if r["type"] == "HOLIDAY":
                    detail = f"{r['start_date']} to {r['end_date']} (Priority {r['priority']})"
                elif r["type"] == "SHIFT_SWAP":
                    detail = f"Swap with {r.get('target_employee_name', 'N/A')}"
                elif r["type"] == "PREFERENCE":
                    detail = "Preferences updated"
                else:
                    detail = r["type"]

                st.markdown(
                    f'<span style="background-color:{status_color};color:white;padding:2px 8px;'
                    f'border-radius:4px;font-size:0.8em;">{r["status"]}</span> '
                    f'**{r["type"]}** — {detail}',
                    unsafe_allow_html=True,
                )

                if r.get("auto_approval_result"):
                    result = r["auto_approval_result"]
                    if result.get("checks_passed"):
                        with st.expander("Approval details"):
                            for c in result["checks_passed"]:
                                st.markdown(f"- :white_check_mark: {c}")
                            for c in result.get("checks_failed", []):
                                st.markdown(f"- :x: {c}")
        else:
            st.info("No requests submitted yet.")

    with w_tab2:
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
            if result["status"] == STATUS_AUTO_APPROVED:
                st.success(f"Request auto-approved! ({result['id']})")
            elif result["status"] == STATUS_ESCALATED:
                st.warning(f"Request submitted for manager review ({result['id']}). "
                          f"Reason: {result['auto_approval_result']['reason']}")
            else:
                st.info(f"Request submitted ({result['id']}). Awaiting review.")

    with w_tab3:
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

    with w_tab4:
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

    with w_tab5:
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
    """Render the manager queue tab."""
    st.markdown("### Manager Queue")
    st.markdown("*Only items that need your attention. The rest was auto-resolved.*")

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
                    title = f"{r['employee_name']} — {r['start_date']} to {r['end_date']} (P{r['priority']})"
                elif r["type"] == "SHIFT_SWAP":
                    title = f"{r['employee_name']} swap with {r.get('target_employee_name', 'N/A')}"
                else:
                    title = f"{r['employee_name']} — {r['type']}"

                with st.expander(
                    f"[{item['urgency']}] {title}"
                ):
                    st.markdown(
                        f'<span style="background-color:{urgency_color};color:white;padding:2px 8px;'
                        f'border-radius:4px;font-size:0.8em;">{item["urgency"]} URGENCY</span>',
                        unsafe_allow_html=True,
                    )

                    if r["type"] == "HOLIDAY":
                        st.markdown(f"**Reason:** {r.get('reason', 'Not provided')}")
                        st.markdown(f"**Priority:** {r.get('priority', 'N/A')} (1 = most important to them)")

                    st.markdown(f"**Suggested action:** {item['suggested_action']}")

                    # Impact assessment
                    if item.get("impact_if_denied"):
                        denial = item["impact_if_denied"]
                        if denial.get("note"):
                            st.warning(denial["note"])

                    # Alternatives
                    if item["alternatives"]:
                        st.markdown("**If denying, suggest:**")
                        for alt in item["alternatives"]:
                            st.markdown(f"- {alt['description']}")

                    # Action buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Approve", key=f"mgr_approve_{r['id']}", type="primary"):
                            queue.approve_request(r["id"], "Approved by manager")
                            st.success("Approved!")
                            st.rerun()
                    with col2:
                        if st.button("Deny", key=f"mgr_deny_{r['id']}"):
                            queue.deny_request(r["id"], "Coverage not available")
                            st.error("Denied.")
                            st.rerun()
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


def main():
    st.set_page_config(
        page_title="Workforce Compliance AI",
        page_icon="",
        layout="wide",
    )

    st.title("Workforce Compliance AI")
    st.markdown("*AI-powered compliance, fairness, and scheduling intelligence*")
    st.divider()

    # Sidebar
    with st.sidebar:
        st.header("Industry")
        industry_keys = list(INDUSTRY_OPTIONS.keys())
        industry_labels = [f"{v['name']} — {v['subtitle']}" for v in INDUSTRY_OPTIONS.values()]
        selected_industry_idx = st.selectbox(
            "Select your industry",
            range(len(industry_keys)),
            format_func=lambda i: industry_labels[i],
            index=0,
        )
        selected_industry = industry_keys[selected_industry_idx]
        industry_info = INDUSTRY_OPTIONS[selected_industry]

        st.divider()
        st.header("Compliance Rules")

        jurisdiction = st.selectbox(
            "Jurisdiction",
            options=["Chicago", "Oregon", "NYC", "California"],
            index=["Chicago", "Oregon", "NYC", "California"].index(industry_info["jurisdiction"]) if industry_info["jurisdiction"] in ["Chicago", "Oregon", "NYC", "California"] else 0,
        )

        include_cba = st.toggle("Include Union CBA rules", value=True)
        include_company = st.toggle("Include Company Policy", value=True)

        st.divider()
        st.header("Schedule Input")

        uploaded_file = st.file_uploader(
            "Upload Schedule (CSV or Excel)",
            type=["csv", "xlsx", "xls"],
        )

        st.divider()
        run_demo = st.button("Run Demo", type="primary", use_container_width=True)
        st.caption(f"Loads {industry_info['name']} demo with intentional violations.")

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
        st.info("Upload a schedule or click **Run Demo** to get started.")

        st.markdown("### Features")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("**Compliance**\n\nCatch violations before publishing schedules")
        with col2:
            st.markdown("**Hours Tracking**\n\nReal-time fatigue scoring & OT countdown")
        with col3:
            st.markdown("**Coverage Finder**\n\nFairness-ranked replacement suggestions")
        with col4:
            st.markdown("**Shift Intelligence**\n\nDay/night, holidays, premium pay")
        return

    # Reference date for calculations
    ref_date = datetime.strptime(schedule["week_end"], "%Y-%m-%d")

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

    # Initialize AI chat
    if "ai_chat" not in st.session_state:
        st.session_state["ai_chat"] = AIChat(
            employees=EMPLOYEES,
            schedule_data=schedule,
            leave_tracker=st.session_state.get("leave_tracker"),
            employee_history=EMPLOYEE_HISTORY,
            user_role="MANAGER",
            user_employee_id="E001",
        )

    # Main tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "AI Assistant",
        "Compliance",
        "Hours & Fatigue",
        "Coverage Finder",
        "Shift Intelligence",
        "Worker Portal",
        "Manager Queue",
    ])

    with tab1:
        st.markdown("### AI Scheduling Assistant")
        st.markdown("*Ask anything about scheduling, coverage, compliance, hours, or leave.*")

        # Suggested queries
        st.markdown("**Try asking:**")
        suggestions = [
            "Who can cover tomorrow's shift?",
            "How many hours does James have left?",
            "Are there any compliance violations?",
            "Show me the fairness report",
            "Generate next month's schedule",
            "What's my PTO balance?",
        ]
        cols = st.columns(3)
        for i, s in enumerate(suggestions):
            with cols[i % 3]:
                if st.button(s, key=f"suggest_{i}"):
                    st.session_state["chat_input"] = s

        st.divider()

        # Chat history
        if "chat_messages" not in st.session_state:
            st.session_state["chat_messages"] = []

        for msg in st.session_state["chat_messages"]:
            if msg["role"] == "user":
                st.markdown(f"**You:** {msg['content']}")
            else:
                st.markdown(f"**AI:** {msg['content']}")
            st.markdown("")

        # Chat input
        default_input = st.session_state.pop("chat_input", "")
        user_input = st.text_input("Ask a question:", value=default_input, key="chat_box",
                                   placeholder="e.g., Who can cover Sarah's shift tomorrow?")

        if user_input and st.button("Send", type="primary", key="send_chat"):
            st.session_state["chat_messages"].append({"role": "user", "content": user_input})
            chat = st.session_state["ai_chat"]
            chat.schedule_data = schedule
            response = chat.chat(user_input)
            st.session_state["chat_messages"].append({"role": "assistant", "content": response["message"]})
            st.rerun()

    with tab2:
        render_compliance_tab(schedule, jurisdiction, include_cba, include_company)

    with tab3:
        render_hours_dashboard(schedule, ref_date)

    with tab4:
        render_coverage_tab(schedule, ref_date)

    with tab5:
        render_shift_intelligence(schedule, ref_date)

    with tab6:
        render_worker_view(portal)

    with tab7:
        render_manager_queue_tab(portal, queue)

    # Footer
    st.divider()
    st.caption(
        f"Analysis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"Engine: {jurisdiction} + {'CBA' if include_cba else 'No CBA'} + "
        f"{'Company' if include_company else 'No Company'} | "
        f"Workforce Compliance AI v2.0"
    )


if __name__ == "__main__":
    main()
