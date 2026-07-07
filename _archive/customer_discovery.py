"""
Customer Discovery Interview Guide & Market Analysis Tool
=========================================================
Designed for an Amazon Ops Finance leader exploring workforce compliance AI
targeting warehouse, logistics, and retail companies.
"""

from typing import Dict, List, Tuple


# =============================================================================
# 1. INTERVIEW QUESTIONS - Structured for 45-minute ops leader conversations
# =============================================================================

INTERVIEW_QUESTIONS: Dict[str, List[str]] = {
    "pain_discovery": [
        # Goal: Quantify the cost of the problem today
        "Walk me through how your weekly scheduling process works end-to-end "
        "— from demand forecast to published schedule. Where do bottlenecks hit?",

        "In the last 12 months, how many scheduling-related compliance violations "
        "has your organization received? What was the total financial impact "
        "(fines + back-pay + legal)?",

        "When a predictive scheduling law changes or a new city ordinance passes, "
        "how long does it take your team to update your scheduling rules? "
        "Who owns that process?",

        "Tell me about the last time a shift change triggered a grievance or "
        "union complaint. What was the resolution cost in time and dollars?",

        "If I could eliminate 90% of your compliance violations overnight, "
        "what would that be worth to your organization annually? "
        "How would you measure success?",
    ],

    "workflow": [
        # Goal: Understand current tech stack and decision-making process
        "What tools do you use today for scheduling? "
        "(e.g., UKG/Kronos, Excel, homegrown, Legion, Deputy) "
        "How satisfied are you on a 1-10 scale?",

        "Who actually builds the schedules -is it a central team, site-level "
        "managers, or a shared service? How many FTEs touch scheduling weekly?",

        "How do you currently encode union contract rules, local labor laws, "
        "and company policies into your scheduling process? "
        "Is it documented or tribal knowledge?",

        "When an employee calls out 2 hours before a shift, what is your "
        "current process to find a compliant replacement? "
        "How long does it typically take?",

        "What integrations matter most -payroll (ADP/Workday), HRIS, "
        "time & attendance, demand planning? "
        "What breaks when systems don't talk to each other?",
    ],

    "willingness_to_pay": [
        # Goal: Validate pricing model and identify budget holder
        "What is your current annual spend on workforce management software "
        "(licenses + implementation + internal maintenance)?",

        "Who signs off on a new workforce tool purchase -is it VP Ops, CHRO, "
        "CFO, or a committee? What's the typical approval timeline and threshold?",

        "If a tool could guarantee compliance and reduce scheduling labor by 40%, "
        "would you pay $15-25 per employee per month? "
        "What pricing model do you prefer (per-employee, per-site, flat)?",

        "What's your budget cycle? When do you need to have a vendor selected "
        "to get into next year's budget? Are there discretionary funds available now?",

        "Have you evaluated any new scheduling/compliance tools in the last "
        "18 months? What killed the deal or what are you still looking for?",
    ],
}


# =============================================================================
# 2. TARGET_PERSONAS - Ideal Customer Profiles
# =============================================================================

TARGET_PERSONAS: Dict[str, Dict[str, str]] = {
    "vp_operations": {
        "title": "VP of Operations (Warehouse/Logistics/Distribution)",
        "company_profile": "500-10,000 hourly workers, multi-site, "
                           "operating in states with predictive scheduling laws "
                           "(CA, OR, WA, NY, IL, PA)",
        "pain_points": "Compliance fines eating into margin; manager time wasted "
                       "on schedule adjustments; high turnover from unpredictable schedules",
        "buying_trigger": "Recent compliance fine >$100K, expansion into new "
                          "regulated state, or union contract renegotiation",
        "how_to_reach": "LinkedIn (Amazon alumni network), CSCMP conferences, "
                        "Gartner Supply Chain events, WERC membership lists",
        "objections": "Already invested in UKG; IT won't approve another vendor; "
                      "need to see ROI in <6 months",
        "value_prop": "Reduce compliance violations by 90% while cutting "
                      "scheduling admin time by 40% -pays for itself in quarter one",
    },

    "director_hr_labor_relations": {
        "title": "Director of HR / Labor Relations",
        "company_profile": "Unionized workforce, multi-state operations, "
                           "active grievance history related to scheduling",
        "pain_points": "Grievances cost $5-15K each to resolve; CBA rule encoding "
                       "is manual and error-prone; compliance team is understaffed",
        "buying_trigger": "New CBA ratification, pattern of grievance losses, "
                          "or DOL audit/investigation",
        "how_to_reach": "SHRM events, Labor & Employment Law conferences, "
                        "referrals from employment attorneys",
        "objections": "Union may resist technology; need IT/security review; "
                      "concerned about employee data privacy",
        "value_prop": "Encode every CBA rule into automated guardrails -"
                      "zero-grievance scheduling with full audit trail",
    },

    "cfo_controller": {
        "title": "CFO / Controller (Compliance Cost Angle)",
        "company_profile": "Companies spending >$500K/year on compliance-related "
                           "costs (fines, legal, HR overhead, back-pay)",
        "pain_points": "Unpredictable compliance costs; can't forecast penalty "
                       "exposure; auditors flagging workforce compliance gaps",
        "buying_trigger": "Material compliance cost line item in P&L, "
                          "board/investor pressure on ESG/labor practices, "
                          "or failed audit",
        "how_to_reach": "CFO Alliance events, FEI chapters, "
                        "referrals from Big 4 audit partners",
        "objections": "Show me the NPV; how fast is payback; "
                      "what if laws change and tool becomes obsolete",
        "value_prop": "Turn unpredictable $2M+ compliance risk into a "
                      "predictable $200K SaaS line item with guaranteed SLA",
    },

    "shift_scheduler_ops_manager": {
        "title": "Shift Scheduler / Operations Manager (Daily User)",
        "company_profile": "Site-level operators managing 50-500 workers per shift, "
                           "spending 10-15 hours/week on scheduling",
        "pain_points": "Constant fire drills for call-outs; afraid of making "
                       "a compliance mistake; no visibility into rule changes; "
                       "Excel/paper-based workarounds",
        "buying_trigger": "Personal compliance mistake with consequences, "
                          "promotion with larger scope, or peak season chaos",
        "how_to_reach": "Operations management subreddits, "
                        "frontline manager Slack communities, "
                        "referrals from VP Ops champion",
        "objections": "Another tool to learn; will it work with our weird shifts; "
                      "I've been doing this 15 years without software",
        "value_prop": "One-click compliant schedule generation -"
                      "spend 2 hours/week instead of 15, zero compliance anxiety",
    },
}


# =============================================================================
# 3. MARKET_SIZING - TAM/SAM/SOM Calculator
# =============================================================================

def calculate_market_sizing(
    avg_acv: int = 150_000,
    som_customers_year1: int = 15,
) -> Dict[str, Dict[str, any]]:
    """
    Calculate Total Addressable Market, Serviceable Addressable Market,
    and Serviceable Obtainable Market for workforce compliance AI.

    Assumptions and sources documented inline.
    """

    # --- TAM: All US companies with 500+ hourly/shift workers ---
    # Source: US Census Bureau County Business Patterns (2023)
    # ~18,000 establishments with 500+ employees in NAICS codes:
    #   493 (Warehousing & Storage): ~2,100 establishments
    #   484 (Truck Transportation): ~1,800 establishments
    #   722 (Food Services - large chains): ~4,500 establishments
    #   445/449 (Grocery/Retail - large): ~3,200 establishments
    #   622/623 (Healthcare - hospitals/nursing): ~4,800 establishments
    #   238 (Specialty Construction - large): ~1,600 establishments
    # Total: ~18,000 companies with significant hourly workforce
    tam_companies = 18_000
    tam_revenue = tam_companies * avg_acv

    # --- SAM: Companies in states with predictive scheduling laws ---
    # States/cities with predictive scheduling laws (as of 2025):
    #   Oregon (statewide), California (select cities), Washington (Seattle),
    #   New York (NYC), Illinois (Chicago), Pennsylvania (Philadelphia),
    #   New Jersey (proposed), Connecticut (proposed)
    # ~40% of target companies operate in these jurisdictions
    # Source: National Employment Law Project tracker, A Better Balance
    sam_pct = 0.40
    sam_companies = int(tam_companies * sam_pct)
    sam_revenue = sam_companies * avg_acv

    # --- SOM: Realistic Year-1 Target ---
    # Assumptions for Year 1 (solo founder + 1-2 engineers):
    #   - 50 qualified discovery calls
    #   - 30% conversion to pilot (15 pilots)
    #   - 60% pilot-to-paid conversion (9 paying customers by month 12)
    #   - Average ACV may be lower in year 1 (discount for early adopters)
    # Conservative: 10 customers; Stretch: 20 customers
    som_year1_acv = int(avg_acv * 0.7)  # 30% early-adopter discount
    som_revenue = som_customers_year1 * som_year1_acv

    return {
        "tam": {
            "companies": tam_companies,
            "acv": avg_acv,
            "total_revenue": tam_revenue,
            "description": f"All US companies with 500+ hourly workers "
                           f"({tam_companies:,} companies x ${avg_acv:,} ACV)",
            "total_formatted": f"${tam_revenue / 1e9:.1f}B",
        },
        "sam": {
            "companies": sam_companies,
            "acv": avg_acv,
            "total_revenue": sam_revenue,
            "description": f"Companies in predictive scheduling law states "
                           f"({sam_companies:,} companies x ${avg_acv:,} ACV)",
            "total_formatted": f"${sam_revenue / 1e6:.0f}M",
        },
        "som": {
            "companies": som_customers_year1,
            "acv": som_year1_acv,
            "total_revenue": som_revenue,
            "description": f"Year-1 target with early-adopter pricing "
                           f"({som_customers_year1} customers x ${som_year1_acv:,} ACV)",
            "total_formatted": f"${som_revenue / 1e6:.1f}M",
        },
    }


# =============================================================================
# 4. COMPETITOR_ANALYSIS - Structured competitive intelligence
# =============================================================================

COMPETITOR_ANALYSIS: Dict[str, Dict[str, any]] = {
    "ukg_kronos": {
        "name": "UKG (formerly Kronos + Ultimate Software)",
        "market_position": "Market leader, ~$4B revenue, 80K+ customers",
        "strengths": [
            "Massive install base -switching costs are high",
            "Full HCM suite (payroll, benefits, scheduling, time)",
            "Deep integrations with ERP systems (SAP, Oracle)",
            "Established enterprise sales motion and channel partners",
        ],
        "weaknesses": [
            "Compliance rules require expensive Professional Services to configure",
            "Slow to update when new scheduling laws pass (3-6 month lag)",
            "No AI-native scheduling -bolt-on optimization is basic",
            "Legacy architecture; UX is dated for frontline managers",
            "Contracts are 3-5 years; customers feel locked in",
        ],
        "pricing": "$6-12 PEPM for scheduling module; $20-40 PEPM for full suite; "
                   "$50-200K implementation; 18-24 month deployment",
        "our_differentiator": "We update compliance rules in <48 hours vs their 3-6 months. "
                              "AI-native approach means zero Professional Services for rule "
                              "configuration. We're the 'compliance intelligence layer' that "
                              "can sit on top of UKG - not a rip-and-replace.",
    },

    "legion_workforce": {
        "name": "Legion Workforce Management",
        "market_position": "Series C startup (~$200M raised), AI-first WFM, "
                           "targeting hourly workforce",
        "strengths": [
            "AI-native demand forecasting and auto-scheduling",
            "Modern UX with mobile-first design for frontline workers",
            "Strong in retail (Dollar Tree, Five Below, Cinemark)",
            "Faster implementation than UKG (8-12 weeks)",
        ],
        "weaknesses": [
            "Compliance is a feature, not the core product -limited depth",
            "Weak in unionized environments (no CBA rule engine)",
            "Limited to scheduling -no audit trail for regulatory defense",
            "Still building enterprise credibility; few 5,000+ employee deployments",
            "Investor pressure to grow fast may deprioritize compliance depth",
        ],
        "pricing": "$4-8 PEPM; implementation $25-75K; 8-12 week deployment",
        "our_differentiator": "We go 10x deeper on compliance - CBA encoding, "
                              "predictive violation detection, regulatory defense audit trails. "
                              "Legion optimizes for labor cost; we optimize for zero violations. "
                              "Complementary positioning possible (compliance layer on top).",
    },

    "deputy": {
        "name": "Deputy",
        "market_position": "SMB-focused scheduling tool, ~$100M ARR, "
                           "strong in Australia/UK expanding to US",
        "strengths": [
            "Simple, intuitive UX -minimal training needed",
            "Low price point accessible to SMBs",
            "Good shift-swap and employee self-service features",
            "Marketplace integrations (POS, payroll, HR)",
        ],
        "weaknesses": [
            "Minimal compliance intelligence -basic overtime alerts only",
            "Not built for enterprise complexity (multi-site, multi-union)",
            "No predictive scheduling law compliance features",
            "Limited reporting for regulatory audits",
            "Struggles with complex shift patterns (split shifts, rotating)",
        ],
        "pricing": "$3-5 PEPM; self-serve onboarding; no implementation fee",
        "our_differentiator": "Completely different market segment. Deputy serves "
                              "coffee shops and small restaurants. We serve enterprises "
                              "with complex regulatory environments. No competitive overlap "
                              "but useful comparison for investors to show market validation.",
    },
}


# =============================================================================
# 5. OUTREACH_TEMPLATES - Email templates for customer discovery
# =============================================================================

OUTREACH_TEMPLATES: Dict[str, str] = {
    "cold_outreach_vp_ops": """Subject: Quick question about scheduling compliance at {company_name}

Hi {first_name},

I noticed {company_name} operates distribution centers in {state} -which means
you're navigating the {law_name} predictive scheduling requirements.

I spent {years} years in Ops Finance at Amazon building workforce planning models,
and I'm now researching how operations leaders handle the compliance complexity
of multi-state scheduling laws. I'm not selling anything -I'm interviewing
15-20 ops leaders to validate whether a problem I experienced is universal.

Quick question: How much time does your team spend per week ensuring schedules
comply with local labor laws before they're published?

If this resonates, I'd love 20 minutes to hear about your experience. I'll share
a summary of what I'm learning across similar companies as a thank-you.

Best,
{your_name}

P.S. I've spoken with ops leaders at {social_proof_company_1} and
{social_proof_company_2} -happy to share anonymized insights from those
conversations.
""",

    "warm_intro_amazon_alumni": """Subject: Fellow Amazonian exploring workforce compliance -intro request

Hi {mutual_connection},

Hope you're doing well! I wanted to ask for a quick favor.

I'm building in the workforce compliance space (specifically: AI that ensures
shift schedules comply with predictive scheduling laws and union rules before
they're published). Think of it as "compliance guardrails for scheduling" —
the kind of thing we wished existed when managing {amazon_context}.

I noticed you're connected to {target_name} at {target_company}. They're
exactly the type of ops leader I'd love to learn from -{target_company}
operates in {num_states} states and likely deals with this pain daily.

Would you be open to making a quick intro? I'm doing discovery interviews
(not selling), and I'd keep it to 20 minutes of their time. Happy to return
the favor however I can.

Here's a one-liner they can forward:
"Former Amazon Ops Finance leader researching scheduling compliance pain —
looking for 20 min to learn how {target_company} handles it today."

Thanks so much,
{your_name}
""",

    "follow_up_after_interview": """Subject: Thank you + insights from our conversation

Hi {first_name},

Thanks for spending time with me {day_of_week} -your perspective on
{key_insight} was incredibly valuable.

Three things I'm taking away from our conversation:

1. {takeaway_1}
2. {takeaway_2}
3. {takeaway_3}

As promised, here's what I'm hearing across the {num_interviews} ops leaders
I've spoken with so far:
- {market_insight_1}
- {market_insight_2}

Next steps on my end:
- I'm building a prototype that {prototype_description}
- I'd love to show you a rough version in {timeline} and get your feedback
- If you'd be open to being a design partner (early access + input on
  features), I'd be thrilled to have {company_name} at the table

Is there anyone else on your team or in your network who'd be good for me
to speak with? Specifically looking for people who {referral_description}.

Thanks again,
{your_name}
""",
}


# =============================================================================
# 6. __main__ - 90-Day Validation Plan
# =============================================================================

def print_validation_plan():
    """Print a formatted 90-Day Customer Validation Plan."""

    plan = {
        "weeks_1_to_4": {
            "title": "WEEKS 1-4: Discovery Sprint",
            "goal": "Complete 20 discovery interviews; validate problem severity",
            "milestones": [
                "Finalize target list: 50 companies across warehouse, logistics, retail "
                "(use LinkedIn Sales Navigator + Amazon alumni network)",
                "Send 100 cold outreach messages (target 20% response rate)",
                "Complete 20 discovery interviews using INTERVIEW_QUESTIONS framework",
                "Document findings: pain severity score (1-10), willingness to pay (Y/N/Maybe), "
                "current tool stack, budget cycle timing",
                "Identify 3-5 potential design partners willing to co-develop",
                "Validate or invalidate: 'Compliance violations cost >$500K/year for target segment'",
            ],
            "key_metrics": [
                "Response rate to cold outreach (target: >20%)",
                "Interview completion rate (target: 20 of 50 contacted)",
                "Pain score average (must be >7/10 to proceed)",
                "% who say they'd pay for a solution (must be >60%)",
            ],
            "amazon_network_plays": [
                "Post in Amazon Alumni Slack (#startups, #ops-leaders channels)",
                "Reach out to former FC/Sort Center GMs now at 3PLs",
                "Connect with ex-Amazon finance leaders at target companies",
                "Leverage ASIN (Amazon Startup & Innovation Network) contacts",
            ],
        },
        "weeks_5_to_8": {
            "title": "WEEKS 5-8: Solution Validation & Prototype",
            "goal": "Build MVP scope based on interview data; get 3 LOIs",
            "milestones": [
                "Synthesize interview data into 'Jobs to Be Done' framework",
                "Prioritize features: must-have vs nice-to-have (weight by frequency + severity)",
                "Build clickable prototype / Figma mockup of core compliance engine",
                "Demo prototype to top 10 interview participants; collect NPS scores",
                "Draft pricing model: validate $15-25 PEPM with 5 potential buyers",
                "Secure 3 Letters of Intent (non-binding but signal real commitment)",
                "Define MVP scope: what ships in 90 days post-funding/commitment",
            ],
            "key_metrics": [
                "Prototype NPS score (target: >8/10)",
                "Letters of Intent secured (target: 3-5)",
                "Pricing validation: % who accept $15-25 PEPM (target: >50%)",
                "Feature consensus: top 3 features appear in >70% of interviews",
            ],
            "amazon_network_plays": [
                "Recruit ex-Amazon SDE for technical co-founder conversations",
                "Demo to Amazon Logistics alumni now running ops at customers",
                "Get warm intros to VCs from ex-Amazon Directors/VPs",
            ],
        },
        "weeks_9_to_12": {
            "title": "WEEKS 9-12: Go/No-Go Decision & Launch Prep",
            "goal": "Make data-driven build decision; set up for month 4 launch",
            "milestones": [
                "Compile discovery deck: market size, competitive gap, validation data",
                "Go/No-Go decision based on: LOIs >= 3, pain score >= 8, ACV >= $100K",
                "IF GO: Begin MVP development sprint (compliance rule engine + basic scheduler)",
                "IF GO: Sign 1-2 design partner agreements (free pilot, 6-month commitment)",
                "IF GO: Set up legal entity, contracts, data security baseline (SOC2 prep)",
                "Create investor-ready pitch deck using discovery data as evidence",
                "Plan month 4-6 roadmap: pilot delivery to first design partner",
            ],
            "key_metrics": [
                "Go/No-Go criteria met (binary)",
                "Design partners signed (target: 2)",
                "MVP development timeline established (target: 8-12 weeks to pilot-ready)",
                "Total pipeline value from LOIs (target: >$500K ACV)",
            ],
            "go_no_go_criteria": [
                "GO if: >= 3 LOIs, avg pain score >= 8/10, validated ACV >= $100K, "
                "clear differentiator vs incumbents confirmed by buyers",
                "PIVOT if: pain is real but pricing won't support venture-scale business "
                "(consider consulting-led approach or different segment)",
                "STOP if: pain score < 6/10, < 2 LOIs after 50 conversations, "
                "or buyers say incumbents solve this adequately",
            ],
        },
    }

    print("=" * 78)
    print("  90-DAY CUSTOMER VALIDATION PLAN")
    print("  Workforce Compliance AI - From Amazon Ops Finance to Founder")
    print("=" * 78)
    print()

    for phase_key, phase in plan.items():
        print(f"\n{'-' * 78}")
        print(f"  {phase['title']}")
        print(f"  Goal: {phase['goal']}")
        print(f"{'-' * 78}")

        print(f"\n  Milestones:")
        for i, milestone in enumerate(phase["milestones"], 1):
            print(f"    {i}. {milestone}")

        print(f"\n  Key Metrics:")
        for metric in phase["key_metrics"]:
            print(f"    - {metric}")

        if "amazon_network_plays" in phase:
            print(f"\n  Amazon Network Plays:")
            for play in phase["amazon_network_plays"]:
                print(f"    * {play}")

        if "go_no_go_criteria" in phase:
            print(f"\n  Go/No-Go Decision Framework:")
            for criterion in phase["go_no_go_criteria"]:
                print(f"    >> {criterion}")

        print()

    # Print market sizing summary
    print(f"\n{'=' * 78}")
    print("  MARKET SIZING SUMMARY")
    print(f"{'=' * 78}")
    sizing = calculate_market_sizing()
    for segment, data in sizing.items():
        print(f"\n  {segment.upper()}: {data['total_formatted']}")
        print(f"    {data['description']}")

    print(f"\n{'=' * 78}")
    print("  COMPETITIVE POSITIONING")
    print(f"{'=' * 78}")
    for key, competitor in COMPETITOR_ANALYSIS.items():
        print(f"\n  vs {competitor['name']}:")
        print(f"    Differentiator: {competitor['our_differentiator']}")

    print(f"\n{'=' * 78}")
    print("  Next Action: Send first 20 outreach messages THIS WEEK.")
    print("  Use OUTREACH_TEMPLATES['cold_outreach_vp_ops'] as your starting point.")
    print(f"{'=' * 78}\n")


if __name__ == "__main__":
    print_validation_plan()
