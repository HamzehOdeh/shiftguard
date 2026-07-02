# Workforce Compliance AI - Streamlit Web Application
# Requirements: pip install streamlit pandas openpyxl
# Run with: streamlit run app.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from rules_engine import get_all_rules
from sample_schedule import generate_schedule, EMPLOYEES, EMPLOYEE_HISTORY
from compliance_checker import check_compliance
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
        st.header("Configuration")

        jurisdiction = st.selectbox(
            "Jurisdiction",
            options=["Chicago", "Oregon", "NYC", "California"],
            index=0,
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
        st.caption("Uses built-in sample schedule with intentional violations.")

    # Determine which schedule to use
    schedule = None
    if run_demo:
        schedule = generate_schedule()
        st.session_state["schedule"] = schedule
        st.session_state["source"] = "demo"
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

    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Compliance Violations",
        "Hours & Fatigue Dashboard",
        "Coverage Finder",
        "Shift Intelligence"
    ])

    with tab1:
        render_compliance_tab(schedule, jurisdiction, include_cba, include_company)

    with tab2:
        render_hours_dashboard(schedule, ref_date)

    with tab3:
        render_coverage_tab(schedule, ref_date)

    with tab4:
        render_shift_intelligence(schedule, ref_date)

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
