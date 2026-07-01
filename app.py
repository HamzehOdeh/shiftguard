# Workforce Compliance AI - Streamlit Web Application
# Requirements: pip install streamlit pandas openpyxl
# Run with: streamlit run app.py

import streamlit as st
import pandas as pd
from datetime import datetime

from rules_engine import get_all_rules
from sample_schedule import generate_schedule, EMPLOYEES
from compliance_checker import check_compliance


def parse_uploaded_file(uploaded_file):
    """Parse an uploaded CSV or Excel file into the schedule dict format."""
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Expected columns: employee_id, name, date, start, end, role, shift_type
    required_cols = ["employee_id", "name", "date", "start", "end", "role", "shift_type"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"Missing required columns: {', '.join(missing)}")
        return None

    shifts = df[required_cols].to_dict(orient="records")

    # Ensure date and time fields are strings
    for shift in shifts:
        shift["date"] = str(shift["date"]).strip()[:10]
        shift["start"] = str(shift["start"]).strip()[:5]
        shift["end"] = str(shift["end"]).strip()[:5]
        shift["employee_id"] = str(shift["employee_id"]).strip()
        shift["name"] = str(shift["name"]).strip()
        shift["role"] = str(shift["role"]).strip()
        shift["shift_type"] = str(shift["shift_type"]).strip()

    # Determine schedule metadata from the data
    dates = sorted(set(s["date"] for s in shifts))
    week_start = dates[0] if dates else datetime.today().strftime("%Y-%m-%d")
    week_end = dates[-1] if dates else datetime.today().strftime("%Y-%m-%d")

    # Default posted date to today (user can adjust if needed)
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
    """Return color for severity level."""
    colors = {
        "CRITICAL": "#dc3545",
        "HIGH": "#fd7e14",
        "MEDIUM": "#ffc107",
    }
    return colors.get(severity, "#6c757d")


def get_severity_emoji(severity):
    """Return a text badge for severity level."""
    badges = {
        "CRITICAL": "CRITICAL",
        "HIGH": "HIGH",
        "MEDIUM": "MEDIUM",
    }
    return badges.get(severity, severity)


def estimate_penalty_exposure(violations):
    """Estimate total penalty exposure from violations."""
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


def main():
    st.set_page_config(
        page_title="Workforce Compliance AI",
        page_icon="",
        layout="wide",
    )

    # Title
    st.title("Workforce Compliance AI")
    st.markdown("*AI-powered schedule compliance for hourly, shift-based workforces*")
    st.divider()

    # Sidebar
    with st.sidebar:
        st.header("Configuration")

        jurisdiction = st.selectbox(
            "Jurisdiction",
            options=["Chicago", "Oregon", "NYC", "California"],
            index=0,
            help="Select the jurisdiction whose labor laws should be applied.",
        )

        include_cba = st.toggle("Include Union CBA rules", value=True)
        include_company = st.toggle("Include Company Policy", value=True)

        st.divider()
        st.header("Schedule Input")

        uploaded_file = st.file_uploader(
            "Upload Schedule (CSV or Excel)",
            type=["csv", "xlsx", "xls"],
            help="Expected columns: employee_id, name, date, start, end, role, shift_type",
        )

        st.divider()
        run_demo = st.button("Run Demo", type="primary", use_container_width=True)
        st.caption("Uses the built-in sample schedule with intentional violations.")

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
        st.info(
            "Upload a schedule file or click **Run Demo** in the sidebar to analyze compliance."
        )
        st.markdown("### How it works")
        st.markdown(
            """
            1. Select your jurisdiction and rule sets in the sidebar
            2. Upload a shift schedule (CSV/Excel) or use the built-in demo
            3. The engine checks the schedule against applicable labor laws, union CBA, and company policies
            4. Review violations, estimated penalties, and recommended fixes
            """
        )

        # Show applicable rules
        rules = get_all_rules(jurisdiction, include_cba, include_company)
        with st.expander(f"View applicable rules for {jurisdiction} ({len(rules)} rules)"):
            for rule in rules:
                severity_color = get_severity_color(rule["severity"].upper())
                st.markdown(
                    f'<span style="background-color:{severity_color};color:white;padding:2px 8px;border-radius:4px;font-size:0.75em;">{rule["severity"].upper()}</span> '
                    f'**{rule["id"]}** - {rule["name"]}: {rule["description"]}',
                    unsafe_allow_html=True,
                )
        return

    # Run compliance check
    violations = check_compliance(schedule)

    # Categorize violations
    critical = [v for v in violations if v["severity"] == "CRITICAL"]
    high = [v for v in violations if v["severity"] == "HIGH"]
    medium = [v for v in violations if v["severity"] == "MEDIUM"]

    # Penalty estimation
    penalty_low, penalty_high = estimate_penalty_exposure(violations)

    # Schedule info
    source_label = st.session_state.get("source", "unknown")
    st.markdown(
        f"**Facility:** {schedule['facility']} | "
        f"**Week:** {schedule['week_start']} to {schedule['week_end']} | "
        f"**Posted:** {schedule['schedule_posted_date']} | "
        f"**Shifts:** {len(schedule['shifts'])} | "
        f"**Source:** {source_label}"
    )

    # Summary cards
    st.subheader("Compliance Summary")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Critical Violations",
            value=len(critical),
            delta=None,
        )
        if critical:
            st.markdown(
                f'<div style="background-color:#dc3545;height:4px;border-radius:2px;"></div>',
                unsafe_allow_html=True,
            )

    with col2:
        st.metric(
            label="High Violations",
            value=len(high),
            delta=None,
        )
        if high:
            st.markdown(
                f'<div style="background-color:#fd7e14;height:4px;border-radius:2px;"></div>',
                unsafe_allow_html=True,
            )

    with col3:
        st.metric(
            label="Medium Violations",
            value=len(medium),
            delta=None,
        )
        if medium:
            st.markdown(
                f'<div style="background-color:#ffc107;height:4px;border-radius:2px;"></div>',
                unsafe_allow_html=True,
            )

    with col4:
        st.metric(
            label="Estimated Penalty Exposure",
            value=f"${penalty_low:,} - ${penalty_high:,}",
            delta=None,
        )

    st.divider()

    # Detailed violations
    st.subheader(f"Violation Details ({len(violations)} total)")

    # Sort: critical first, then high, then medium
    sorted_violations = sorted(
        violations,
        key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}.get(x["severity"], 3),
    )

    for i, v in enumerate(sorted_violations, 1):
        severity = v["severity"]
        color = get_severity_color(severity)
        badge = get_severity_emoji(severity)

        with st.expander(
            f"#{i} [{badge}] {v['rule_id']} - {v['rule_name']} | {v['affected_employees']}"
        ):
            st.markdown(
                f'<span style="background-color:{color};color:white;padding:4px 12px;border-radius:4px;font-weight:bold;">{severity}</span>',
                unsafe_allow_html=True,
            )
            st.markdown("")

            col_left, col_right = st.columns(2)

            with col_left:
                st.markdown(f"**Rule ID:** {v['rule_id']}")
                st.markdown(f"**Rule Name:** {v['rule_name']}")
                st.markdown(f"**Affected Employee(s):** {v['affected_employees']}")

            with col_right:
                st.markdown(f"**Cost Impact:** {v['cost_impact']}")

            st.markdown(f"**Description:** {v['description']}")
            st.markdown(f"**Recommendation:** {v['recommendation']}")

    st.divider()

    # Recommended Actions
    st.subheader("Recommended Actions")
    st.markdown("*Priority-ordered fixes to resolve compliance violations:*")

    # Build recommendations from violations, ordered by severity
    action_num = 1
    if critical:
        for v in critical:
            st.markdown(
                f"**{action_num}. IMMEDIATE** - {v['rule_name']}\n\n"
                f"   {v['recommendation']}"
            )
            action_num += 1

    if high:
        for v in high:
            st.markdown(
                f"**{action_num}. THIS WEEK** - {v['rule_name']} ({v['affected_employees']})\n\n"
                f"   {v['recommendation']}"
            )
            action_num += 1

    if medium:
        for v in medium:
            st.markdown(
                f"**{action_num}. PROCESS IMPROVEMENT** - {v['rule_name']} ({v['affected_employees']})\n\n"
                f"   {v['recommendation']}"
            )
            action_num += 1

    # Footer
    st.divider()
    st.caption(
        f"Analysis performed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"Rules engine: {jurisdiction} + {'CBA' if include_cba else 'No CBA'} + {'Company Policy' if include_company else 'No Company Policy'}"
    )


if __name__ == "__main__":
    main()
