"""
ShiftGuard - Free Compliance Cost Calculator
Standalone viral tool. No signup. Instant results.
Run with: streamlit run calculator_app.py --server.port 8502
"""

import streamlit as st
from datetime import datetime
from cost_calculator import calculate_compliance_cost, PENALTY_DATABASE


def main():
    st.set_page_config(
        page_title="ShiftGuard - Free Compliance Cost Calculator",
        page_icon="",
        layout="centered",
    )

    # Header
    st.markdown(
        '<h1 style="text-align:center;margin-bottom:0;">ShiftGuard</h1>'
        '<p style="text-align:center;color:#888;font-size:1.2em;margin-top:0;">'
        'Schedule with confidence. Never pay another compliance fine.</p>',
        unsafe_allow_html=True,
    )
    st.markdown("")
    st.markdown(
        '<h2 style="text-align:center;">How much are schedule violations costing you?</h2>'
        '<p style="text-align:center;color:#aaa;">Free. No signup. Instant results.</p>',
        unsafe_allow_html=True,
    )
    st.divider()

    # Input form
    col1, col2 = st.columns(2)

    with col1:
        state = st.selectbox(
            "Your state",
            ["California", "New York", "Chicago (Illinois)", "Oregon", "Illinois", "Washington"],
            help="We check jurisdiction-specific labor laws",
        )
        if "Chicago" in state:
            state = "Chicago"

        industry = st.selectbox(
            "Industry",
            [
                ("warehouse", "Warehouse / Distribution / Fulfillment"),
                ("healthcare", "Healthcare / Hospital / Nursing"),
                ("retail", "Retail / Store Operations"),
                ("hospitality", "Hospitality / Restaurant / Hotel"),
                ("manufacturing", "Manufacturing / Production"),
            ],
            format_func=lambda x: x[1],
        )
        industry_key = industry[0]

    with col2:
        headcount = st.number_input(
            "Number of hourly/shift employees",
            min_value=10, max_value=50000, value=200, step=50,
            help="Full-time + part-time hourly workers"
        )
        union = st.checkbox("Unionized workforce", help="Union/CBA adds grievance costs")

    st.markdown("")

    if st.button("Calculate My Compliance Risk", type="primary", use_container_width=True):
        result = calculate_compliance_cost(state, headcount, industry_key, union)

        st.divider()

        # Risk Grade - BIG
        grade = result["risk_grade"]
        grade_colors = {
            "A (Low Risk)": "#28a745", "B (Moderate)": "#7cb342",
            "C (Elevated)": "#ffc107", "D (High Risk)": "#fd7e14", "F (Critical)": "#dc3545",
        }
        color = grade_colors.get(grade, "#dc3545")

        st.markdown(
            f'<div style="text-align:center;padding:30px;background:linear-gradient(135deg,#1a1a2e,#16213e);'
            f'border-radius:15px;border:2px solid {color};">'
            f'<p style="color:#aaa;margin:0;font-size:1em;">YOUR COMPLIANCE RISK GRADE</p>'
            f'<h1 style="color:{color};margin:10px 0;font-size:4em;">{grade}</h1>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown("")

        # Dollar exposure - THE HOOK
        st.markdown(
            f'<div style="text-align:center;padding:25px;background:#2d1b1b;border-radius:12px;">'
            f'<p style="color:#ff9999;margin:0;">ESTIMATED ANNUAL PENALTY EXPOSURE</p>'
            f'<h1 style="color:#ff4444;font-size:3em;margin:10px 0;">'
            f'${result["annual_exposure"]["medium"]:,}</h1>'
            f'<p style="color:#aaa;">Range: ${result["annual_exposure"]["low"]:,} '
            f'to ${result["annual_exposure"]["high"]:,}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown("")

        # Key metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Per Employee/Year", f"${result['per_employee_annual']['medium']:,}")
        with col2:
            st.metric("Monthly Burn", f"${result['monthly_exposure']['medium']:,}/mo")
        with col3:
            st.metric("Est. Violations/Year", f"{result['total_estimated_violations']:,}")

        st.divider()

        # Breakdown
        st.markdown("### Where Your Risk Comes From")
        for vtype, data in result["violation_breakdown"].items():
            pct_of_total = data["annual_mid"] / max(1, result["annual_exposure"]["medium"]) * 100
            st.markdown(
                f'**{vtype.replace("_", " ").title()}** '
                f'({data["rate"]} of shifts) - '
                f'~{data["estimated_occurrences"]:,} violations/year '
                f'= **${data["annual_mid"]:,}** '
                f'({pct_of_total:.0f}% of total)'
            )

        st.divider()

        # ROI pitch
        st.markdown("### The Math")
        monthly_cost = headcount * 20  # $20/employee/month
        months_to_roi = max(1, round(monthly_cost * 12 / max(1, result["annual_exposure"]["medium"])))
        savings_year_1 = result["annual_exposure"]["medium"] - (monthly_cost * 12)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                f'<div style="padding:15px;background:#1a2e1a;border-radius:10px;border:1px solid #28a745;">'
                f'<p style="color:#28a745;font-weight:bold;margin:0;">WITH SHIFTGUARD</p>'
                f'<p style="color:#ccc;margin:5px 0;">Platform cost: ${monthly_cost:,}/month</p>'
                f'<p style="color:#28a745;font-size:1.3em;margin:0;">Year 1 NET savings: <strong>${max(0,savings_year_1):,}</strong></p>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f'<div style="padding:15px;background:#2e1a1a;border-radius:10px;border:1px solid #dc3545;">'
                f'<p style="color:#dc3545;font-weight:bold;margin:0;">WITHOUT (STATUS QUO)</p>'
                f'<p style="color:#ccc;margin:5px 0;">Penalties + legal: ${result["annual_exposure"]["medium"]:,}/year</p>'
                f'<p style="color:#dc3545;font-size:1.3em;margin:0;">Plus: manager time, grievances, lawsuits</p>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.divider()

        # CTA
        st.markdown(
            '<div style="text-align:center;padding:30px;">'
            '<h2>Ready to eliminate these violations?</h2>'
            '<p style="color:#aaa;font-size:1.1em;">'
            'ShiftGuard catches violations before you publish the schedule.<br>'
            'AI-powered. Works in 60 seconds. No 6-month implementation.</p>'
            '</div>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            st.link_button("Try the Full Demo (Free)", "https://shiftguard-giznml7xnt59j5aguqjerc.streamlit.app/", type="primary", use_container_width=True)
        with col2:
            st.link_button("Schedule a Walkthrough", "mailto:hello@shiftguard.ai?subject=ShiftGuard%20Walkthrough%20Request", use_container_width=True)

        st.markdown("")
        st.caption(
            "Estimates based on DOL enforcement data and jurisdiction-specific penalty schedules. "
            "Actual exposure depends on enforcement activity and specific circumstances. "
            "This tool does not constitute legal advice."
        )

    # Footer
    st.divider()
    st.markdown(
        '<p style="text-align:center;color:#666;font-size:0.85em;">'
        'ShiftGuard - AI-Powered Workforce Compliance<br>'
        'Schedule with confidence. Never pay another compliance fine.</p>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
