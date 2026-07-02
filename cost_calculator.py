"""
Workforce Compliance AI - Compliance Cost Calculator
The free viral tool. Enter your state + headcount + industry and get instant
dollar figure of violation exposure. No signup required.
"""

import streamlit as st
from datetime import datetime


# Penalty data by jurisdiction (research-based averages)
PENALTY_DATABASE = {
    "California": {
        "meal_break_violation": {"per_occurrence": 75, "description": "1 hour premium pay per day per employee"},
        "rest_break_violation": {"per_occurrence": 75, "description": "1 hour premium pay per day"},
        "overtime_violation": {"per_occurrence": 200, "description": "Back pay + waiting time penalties"},
        "record_keeping": {"per_occurrence": 250, "description": "Per pay period per employee"},
        "misclassification": {"per_occurrence": 25000, "description": "Per worker misclassified"},
    },
    "New York": {
        "spread_of_hours": {"per_occurrence": 50, "description": "1 hour at minimum wage for 10+ hour spread"},
        "frequency_of_pay": {"per_occurrence": 500, "description": "Per missed pay period"},
        "notice_of_pay": {"per_occurrence": 50, "description": "Per day per employee ($5K max)"},
    },
    "Chicago": {
        "fair_workweek_notice": {"per_occurrence": 400, "description": "$300-500 per employee per violation"},
        "schedule_change_premium": {"per_occurrence": 50, "description": "1 hour predictability pay per change"},
        "clopening": {"per_occurrence": 100, "description": "1.25x pay for hours within rest window"},
        "right_to_rest": {"per_occurrence": 75, "description": "Per violation per employee"},
    },
    "Oregon": {
        "predictive_scheduling": {"per_occurrence": 200, "description": "Per shift per violation"},
        "right_to_rest": {"per_occurrence": 100, "description": "Time-and-a-half for affected hours"},
        "schedule_change": {"per_occurrence": 50, "description": "Half-shift pay for late changes"},
    },
    "Illinois": {
        "paid_leave_violation": {"per_occurrence": 500, "description": "$500/day per violation"},
        "meal_break": {"per_occurrence": 50, "description": "Per missed break"},
        "one_day_rest": {"per_occurrence": 200, "description": "Per week per employee"},
    },
    "Washington": {
        "predictive_scheduling": {"per_occurrence": 150, "description": "Per violation (Seattle)"},
        "rest_break": {"per_occurrence": 100, "description": "Per missed break"},
    },
}

# Industry-specific violation rates (% of shifts with potential violations)
# Conservative estimates based on DOL enforcement data
VIOLATION_RATES = {
    "warehouse": {"meal_break": 0.02, "rest_period": 0.015, "overtime": 0.03, "clopening": 0.01, "minor": 0.002},
    "healthcare": {"rest_period": 0.025, "overtime": 0.04, "consecutive_days": 0.015, "clopening": 0.01},
    "retail": {"clopening": 0.02, "schedule_notice": 0.05, "short_shift": 0.01, "minor": 0.005},
    "hospitality": {"clopening": 0.03, "split_shift": 0.02, "schedule_notice": 0.04, "overtime": 0.025},
    "manufacturing": {"overtime": 0.035, "consecutive_days": 0.02, "rest_period": 0.015},
}


def calculate_compliance_cost(state, headcount, industry, union=False, shifts_per_week=None):
    """
    Calculate estimated annual compliance cost/risk.

    Returns:
    - Low estimate (if only flagrant violations caught)
    - Medium estimate (realistic enforcement)
    - High estimate (class action / DOL audit scenario)
    """
    if shifts_per_week is None:
        shifts_per_week = headcount * 5  # default 5 shifts per employee per week

    annual_shifts = shifts_per_week * 52
    penalties = PENALTY_DATABASE.get(state, PENALTY_DATABASE.get("California", {}))
    rates = VIOLATION_RATES.get(industry, VIOLATION_RATES["warehouse"])

    # Calculate violation counts
    violations = {}
    total_violations = 0
    total_penalty_low = 0
    total_penalty_mid = 0
    total_penalty_high = 0

    for violation_type, rate in rates.items():
        count = round(annual_shifts * rate)
        penalty_info = penalties.get(violation_type) or penalties.get(
            list(penalties.keys())[0] if penalties else "overtime_violation",
            {"per_occurrence": 100}
        )
        per_occ = penalty_info.get("per_occurrence", 100)

        low = round(count * per_occ * 0.3)  # 30% detected
        mid = round(count * per_occ * 0.6)  # 60% detected (audit)
        high = round(count * per_occ * 1.5)  # 150% with penalties + damages

        violations[violation_type] = {
            "estimated_occurrences": count,
            "rate": f"{rate*100:.1f}%",
            "penalty_per": f"${per_occ}",
            "annual_low": low,
            "annual_mid": mid,
            "annual_high": high,
        }
        total_violations += count
        total_penalty_low += low
        total_penalty_mid += mid
        total_penalty_high += high

    # Union premium (grievances add cost)
    if union:
        union_multiplier = 1.4
        total_penalty_low = round(total_penalty_low * union_multiplier)
        total_penalty_mid = round(total_penalty_mid * union_multiplier)
        total_penalty_high = round(total_penalty_high * union_multiplier)

    # Litigation risk premium for larger employers
    if headcount > 500:
        litigation_premium = headcount * 200  # class action exposure
    elif headcount > 100:
        litigation_premium = headcount * 50
    else:
        litigation_premium = 0

    total_penalty_high += litigation_premium

    return {
        "state": state,
        "industry": industry,
        "headcount": headcount,
        "union": union,
        "annual_shifts": annual_shifts,
        "total_estimated_violations": total_violations,
        "violation_breakdown": violations,
        "annual_exposure": {
            "low": total_penalty_low,
            "medium": total_penalty_mid,
            "high": total_penalty_high,
        },
        "monthly_exposure": {
            "low": round(total_penalty_low / 12),
            "medium": round(total_penalty_mid / 12),
            "high": round(total_penalty_high / 12),
        },
        "per_employee_annual": {
            "low": round(total_penalty_low / max(1, headcount)),
            "medium": round(total_penalty_mid / max(1, headcount)),
            "high": round(total_penalty_high / max(1, headcount)),
        },
        "roi_message": (
            f"At ${total_penalty_mid:,}/year exposure, our platform pays for itself "
            f"in {max(1, round(headcount * 20 * 12 / max(1, total_penalty_mid)))} months "
            f"(at $20/employee/month)."
        ),
        "risk_grade": (
            "A (Low Risk)" if total_penalty_mid < 10000 else
            "B (Moderate)" if total_penalty_mid < 50000 else
            "C (Elevated)" if total_penalty_mid < 150000 else
            "D (High Risk)" if total_penalty_mid < 500000 else
            "F (Critical)"
        ),
    }


def run_calculator_app():
    """Standalone Streamlit app for the free compliance cost calculator."""
    st.set_page_config(page_title="Free Compliance Cost Calculator", layout="wide")

    st.title("Compliance Cost Calculator")
    st.markdown("### How much are schedule violations costing you?")
    st.markdown("*Free. No signup. Instant results.*")
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        state = st.selectbox("State", [
            "California", "New York", "Chicago", "Oregon",
            "Illinois", "Washington",
        ])
        industry = st.selectbox("Industry", [
            "warehouse", "healthcare", "retail", "hospitality", "manufacturing",
        ])

    with col2:
        headcount = st.number_input("Hourly employees", min_value=10, max_value=50000, value=500)
        union = st.checkbox("Unionized workforce")

    if st.button("Calculate My Risk", type="primary", use_container_width=True):
        result = calculate_compliance_cost(state, headcount, industry, union)

        st.divider()
        st.markdown("## Your Compliance Risk Score")

        # Risk grade
        grade = result["risk_grade"]
        grade_color = {
            "A (Low Risk)": "#28a745", "B (Moderate)": "#7cb342",
            "C (Elevated)": "#ffc107", "D (High Risk)": "#fd7e14", "F (Critical)": "#dc3545",
        }.get(grade, "#6c757d")

        st.markdown(
            f'<h1 style="color:{grade_color};text-align:center;">{grade}</h1>',
            unsafe_allow_html=True,
        )

        # Dollar figures
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Low Estimate (annual)", f"${result['annual_exposure']['low']:,}")
            st.caption("If only obvious violations caught")
        with col2:
            st.metric("Likely Exposure (annual)", f"${result['annual_exposure']['medium']:,}")
            st.caption("Realistic enforcement scenario")
        with col3:
            st.metric("Worst Case (DOL audit)", f"${result['annual_exposure']['high']:,}")
            st.caption("Class action + full penalties")

        st.divider()

        # Breakdown
        st.markdown("### Violation Breakdown")
        for vtype, data in result["violation_breakdown"].items():
            st.markdown(
                f"**{vtype.replace('_', ' ').title()}**: "
                f"~{data['estimated_occurrences']} violations/year "
                f"@ {data['penalty_per']} each = "
                f"${data['annual_mid']:,}/year (likely)"
            )

        st.divider()

        # ROI message
        st.markdown("### What This Means")
        st.markdown(f"**{result['roi_message']}**")
        st.markdown(
            f"- You have ~**{result['total_estimated_violations']:,}** potential violations per year\n"
            f"- That's **${result['per_employee_annual']['medium']}/employee/year** in exposure\n"
            f"- Monthly burn rate: **${result['monthly_exposure']['medium']:,}/month**\n"
        )

        st.divider()
        st.markdown("### Want to fix this?")
        st.markdown(
            "**Workforce Compliance AI** catches these violations *before* they happen. "
            "Schedule a demo to see how."
        )
        st.button("Schedule Demo", type="primary")
        st.button("Upload Your Schedule for Free Analysis")


if __name__ == "__main__":
    # CLI demo
    print("=" * 70)
    print("  COMPLIANCE COST CALCULATOR")
    print("=" * 70)

    scenarios = [
        ("California", 500, "warehouse", True),
        ("Chicago", 200, "retail", False),
        ("New York", 1000, "healthcare", True),
        ("Oregon", 300, "hospitality", False),
    ]

    for state, hc, ind, union in scenarios:
        result = calculate_compliance_cost(state, hc, ind, union)
        print(f"\n  {state} | {ind} | {hc} employees | {'Union' if union else 'Non-union'}")
        print(f"  Risk Grade: {result['risk_grade']}")
        print(f"  Annual exposure: ${result['annual_exposure']['low']:,} - ${result['annual_exposure']['high']:,}")
        print(f"  Per employee: ${result['per_employee_annual']['medium']}/year")
        print(f"  {result['roi_message']}")
