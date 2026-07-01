# Workforce Compliance AI - Complete Business & Technical Plan

## Executive Summary

**What:** An AI-powered compliance layer that checks shift schedules against labor laws, union contracts, and company policies — catching violations before they cost money.

**For whom:** Any company with 500+ hourly workers (warehouses, logistics, retail, healthcare, hospitality, manufacturing).

**The problem:** 80M+ hourly workers in the US. Predictive scheduling laws are exploding (12+ states). No existing tool does AI-native compliance reasoning. Violations discovered after the fact cost $5K-$50K+ per quarter.

**The solution:** Upload a schedule → get instant violations + compliant alternatives + cost impact. One second vs. hours of manual checking.

**Your unfair advantage:** 5 years managing millions of labor hours at Amazon. You've lived the pain. Most founders in this space have never met an hourly worker.

---

## Part 1: The Market Opportunity

### Problem Statement

When a shift scheduler builds next week's schedule, they must simultaneously comply with:
- Federal labor law (FMLA, FLSA)
- State labor law (varies by state - predictive scheduling, meal breaks, overtime)
- City/county ordinances (Chicago, NYC, Oregon, Seattle, etc.)
- Union collective bargaining agreements (CBAs)
- Company internal policies (hour caps, minor restrictions, training requirements)

**Current state:** Managers use tribal knowledge, get lucky, or find out weeks later when a grievance is filed or a fine arrives.

**Cost of failure:**
- Chicago Fair Workweek: $300-$500 per employee per violation
- California meal break: 1 hour premium pay per violation per day
- FMLA interference: $50K-$500K+ in damages
- Union grievances: $5K-$50K per grievance in resolution costs
- Aggregate: $50K-$500K+ per year for a mid-size operation

### Market Size

| Tier | Size | Calculation |
|------|------|-------------|
| TAM | $2.7B | 18,000 US companies with 500+ hourly workers x $150K ACV |
| SAM | $1.08B | 7,200 companies in states with predictive scheduling laws x $150K ACV |
| SOM (Year 1) | $1.6M | 15 early-adopter customers x $105K ACV |

### Regulatory Tailwind

States with predictive scheduling or similar laws (growing):
- Oregon (2018)
- New York City (2017)
- Chicago (2020)
- Seattle (2017)
- San Francisco (2015)
- Philadelphia (2020)
- Los Angeles (2023)
- Berkeley, Emeryville (CA)
- New Jersey (proposed)
- Massachusetts (proposed)
- Connecticut (proposed)
- Minnesota (proposed)

**Trend:** 2-3 new jurisdictions per year. Complexity compounds for multi-state employers.

---

## Part 2: Product Overview

### What It Does

```
INPUT: Shift schedule (CSV/Excel/API from Kronos/UKG)
       + Employee data (leave status, seniority, age, certifications)
       + Jurisdiction (state, city, union)

PROCESSING: AI checks every shift against all applicable rules

OUTPUT: Violations list with:
        - Severity (Critical/High/Medium)
        - Specific rule violated (ID + legal citation)
        - Affected employee(s)
        - Cost impact ($ penalty exposure)
        - Recommended fix (compliant alternative)
        - Estimated time to resolve
```

### Demo Results (Current Prototype)

The prototype analyzes a 10-employee, 52-shift warehouse schedule and catches:

| # | Severity | Violation | Cost Impact |
|---|----------|-----------|-------------|
| 1 | CRITICAL | Minor scheduled past 10pm | Legal fine + manager termination risk |
| 2 | CRITICAL | 5 shifts scheduled during approved FMLA leave | $50K-$500K interference claim |
| 3 | HIGH | Chicago 14-day notice not met | $3,000-$5,000 penalty (all employees) |
| 4 | HIGH | Clopening: 7.5hrs between shifts (min 10) | 1.25x pay + grievance |
| 5 | HIGH | 8 consecutive days (CBA max 6) | Double time + grievance |
| 6 | HIGH | 3-hour shift (CBA min 4 hours) | Pay for full 4 hours |
| 7 | MEDIUM | CBA posting deadline missed | Grievance risk |
| 8 | MEDIUM | 63 weekly hours (company max 60) | VP approval required |
| 9-15 | MEDIUM | PTO scheduling conflicts | Employee morale + grievance |

**Total exposure: $4,500 - $8,000+ for ONE week at ONE facility.**

### Rule Categories Covered

1. **Predictive Scheduling Laws** (Oregon, NYC, Chicago, Seattle, LA)
   - Advance notice requirements (7-14 days)
   - Clopening/right to rest (10-11 hours between shifts)
   - Schedule change premium pay
   - Right to input preferences

2. **Meal & Rest Break Laws** (California, Oregon, Washington, etc.)
   - First meal break before 5th hour
   - Second meal break before 10th hour
   - Rest breaks per 4 hours
   - Daily overtime thresholds

3. **Union CBA Rules** (configurable per contract)
   - Minimum shift length
   - Maximum consecutive days
   - Seniority-based assignment
   - Overtime distribution equity
   - Mandatory OT limits
   - Split shift prohibitions

4. **Leave & Time-Off** (Federal + State)
   - FMLA (cannot schedule during approved leave)
   - State paid sick leave (accrual, caps, no-retaliation)
   - PTO carryover and payout rules
   - Holiday premium pay requirements

5. **Company Policy** (configurable)
   - Weekly hour caps
   - Minor/youth restrictions
   - Training/certification requirements

---

## Part 3: Competitive Landscape

### Current Players & Their Gaps

| Player | Revenue | What they do | What they DON'T do |
|--------|---------|-------------|-------------------|
| UKG (Kronos) | $6B+ | Scheduling, time tracking | AI compliance reasoning; rules take 3-6 months to update |
| Workday | $7B+ | HCM for salaried | Not built for hourly/shift complexity |
| Legion | $100M+ | AI scheduling optimization | Shallow compliance; optimizes cost not compliance |
| Deputy | $100M+ | Scheduling for SMBs | Small business focus; no enterprise compliance |
| ADP | $18B+ | Payroll, HR | Post-hoc compliance, not preventive |

### Your Differentiator

| Dimension | Incumbents | You |
|-----------|-----------|-----|
| Rule update speed | 3-6 months | 48 hours (AI parses new laws) |
| CBA encoding | Manual professional services ($50K+) | Self-service AI ingestion |
| Compliance approach | Reactive (after violation) | Preventive (before publishing) |
| Deployment | Rip-and-replace (12-18 months) | Layer on top of existing tools |
| Cost | $500K+ implementation | $15-25 PEPM, no implementation |

### Positioning

**You are NOT replacing UKG/Kronos.** You sit ON TOP as the compliance intelligence layer. This means:
- Faster sales cycle (no system migration)
- Lower risk for buyer (keep what works, add what's missing)
- Partnership opportunity (UKG might resell or acquire you)

---

## Part 4: Technical Architecture

### Current Prototype (Built)

```
workforce-compliance-ai/
├── rules_engine.py          # Structured labor law rules (OR, NYC, CHI, CA)
├── leave_rules.py           # FMLA, sick leave, PTO, holiday rules by state
├── sample_schedule.py       # Realistic demo schedule with violations
├── compliance_checker.py    # Rule-based violation detection engine
├── ai_reasoning.py          # Claude API for natural language reasoning
├── app.py                   # Streamlit web UI (upload + results)
├── customer_discovery.py    # Market research & outreach tools
├── demo.py                  # Terminal demo script
├── requirements.txt         # Python dependencies
└── .gitignore
```

### Production Architecture (To Build)

```
┌─────────────────────────────────────────────────────────┐
│  FRONTEND (React or Streamlit)                          │
│  - Schedule upload (CSV/Excel/API)                      │
│  - Jurisdiction selector                                │
│  - Violation dashboard                                  │
│  - "What-if" natural language questions                 │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  BACKEND API (FastAPI / Python)                         │
│  - Schedule parsing                                     │
│  - Rule engine execution                                │
│  - AI reasoning (Claude API)                            │
│  - Report generation                                    │
└────────────────────────┬────────────────────────────────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐
│  Rules DB    │ │  Claude API  │ │  Integrations        │
│  (Postgres)  │ │  (Reasoning) │ │  - UKG/Kronos API    │
│              │ │              │ │  - Workday API       │
│  - Laws      │ │  - Edge case │ │  - ADP API           │
│  - CBAs      │ │    reasoning │ │  - HRIS systems      │
│  - Policies  │ │  - NL Q&A    │ │                      │
└──────────────┘ └──────────────┘ └──────────────────────┘
       ▲
       │
┌──────────────────────────────────────┐
│  COMPLIANCE DATA PIPELINE            │
│  - LegiScan API (new laws)           │
│  - State .gov scrapers               │
│  - AI parser (law → structured rule) │
│  - Human review & approval           │
└──────────────────────────────────────┘
```

### Live Compliance Data Sources

| Source | What | Cost | Update Frequency |
|--------|------|------|-----------------|
| Govinfo.gov API | Federal regs (FMLA, FLSA) | Free | As published |
| LegiScan API | State bill tracking | $49-299/mo | Daily |
| State legislature sites | New laws/ordinances | Free (scrape) | Weekly |
| SHRM | HR compliance alerts | $200/yr | Weekly |
| Claude API | Parse laws into rules | $20-200/mo | On-demand |
| Manual / expert review | Validate AI-parsed rules | Your time | 48hr SLA |

### Key Insight: The AI Parsing Moat

When a new law passes:
1. LegiScan alerts you (or you scrape the state legislature site)
2. You feed the law text to Claude: "Parse this into structured compliance rules in our JSON format"
3. Claude outputs structured rules (rule ID, requirement, penalty, severity)
4. You review for accuracy (30 min)
5. Deploy to all affected customers

**Result: New law → live in product in 48 hours.**
**Incumbents: 3-6 months for the same update.**

This speed advantage IS your moat in year 1-2.

---

## Part 5: Go-to-Market Strategy

### Pricing Model

| Tier | Price | Target | Includes |
|------|-------|--------|----------|
| Starter | $15/employee/month | 500-2,000 employees | State + federal rules, basic CBA |
| Professional | $22/employee/month | 2,000-10,000 employees | Multi-state, full CBA, AI reasoning |
| Enterprise | $25/employee/month + setup | 10,000+ employees | Custom rules, API access, dedicated support |

**Example deal:** 3,000-employee warehouse operation = $22 x 3,000 = $66K/year
**Target ACV:** $100K-$200K for mid-market, $500K+ for enterprise

### Sales Motion

**Phase 1 (Months 1-6): Founder-led sales**
- You sell directly to VP Ops / CHRO
- 5-10 customers, each hand-onboarded
- You learn product requirements from real usage

**Phase 2 (Months 7-12): Repeatable playbook**
- Hire 1 AE, 1 SDR
- Standard demo → pilot → contract flow
- Case studies from Phase 1 customers

**Phase 3 (Year 2+): Channel + partnerships**
- Integration partnerships with UKG, ADP
- Reseller agreements with HR consultants
- Marketplace listings (Workday, UKG marketplace)

### Ideal First Customers

| Type | Why | How to find |
|------|-----|-------------|
| 3PL warehouses (XPO, Ryder, DHL Supply Chain) | Multi-state, union, high violation risk | Amazon alumni who moved there |
| Regional grocery chains | Chicago/CA predictive scheduling, unionized | Direct outreach |
| Hospital systems | Complex scheduling, high penalty stakes | LinkedIn |
| Food distribution (Sysco, US Foods) | Warehouse + delivery, multi-state | Amazon network |
| Manufacturing (automotive, food processing) | Union + state compliance + shift complexity | Cold outreach |

---

## Part 6: 90-Day Validation Plan

### Weeks 1-4: Discovery Sprint

**Goal:** Complete 20 discovery interviews. Validate problem severity.

| Action | Target | Metric |
|--------|--------|--------|
| Build target list | 50 companies | Done by end of week 1 |
| Send outreach | 100 messages | 20%+ response rate |
| Complete interviews | 20 conversations | Pain score avg > 7/10 |
| Identify design partners | 3-5 willing to co-develop | Verbal commitment |

**Interview questions (top 5):**
1. Walk me through your scheduling process end-to-end. Where do bottlenecks hit?
2. How many compliance violations in the last 12 months? Total financial impact?
3. When a new scheduling law passes, how long to update your rules? Who owns it?
4. Tell me about the last grievance from a scheduling error. Resolution cost?
5. If I could eliminate 90% of violations overnight, what's that worth annually?

**Amazon network plays:**
- Post in Amazon Alumni Slack (#startups, #ops-leaders)
- Reach out to ex-FC GMs now at 3PLs
- Connect with ex-finance leaders at target companies

### Weeks 5-8: Solution Validation

**Goal:** Build MVP scope from interview data. Get 3 Letters of Intent.

| Action | Target | Metric |
|--------|--------|--------|
| Synthesize interviews | Jobs to Be Done framework | Top 3 features clear |
| Demo prototype | Show to top 10 interviewees | NPS > 8/10 |
| Validate pricing | $15-25 PEPM acceptance | > 50% accept |
| Secure LOIs | Non-binding commitment | 3-5 LOIs |

### Weeks 9-12: Go/No-Go Decision

**Goal:** Data-driven decision to build or pivot.

**GO criteria (all must be true):**
- ≥ 3 Letters of Intent
- Average pain score ≥ 8/10
- Validated ACV ≥ $100K
- Clear differentiator confirmed by buyers

**PIVOT if:** Pain is real but pricing won't support venture scale → consider consulting-led approach

**STOP if:** Pain score < 6/10, < 2 LOIs after 50 conversations, buyers say incumbents solve this

---

## Part 7: Financial Projections

### Year 1 (Conservative)

| Quarter | Customers | Revenue | Notes |
|---------|-----------|---------|-------|
| Q1 | 2 (pilots) | $30K | Consulting-style, $15K/mo total |
| Q2 | 5 | $90K | Convert pilots + 3 new |
| Q3 | 10 | $180K | Self-serve onboarding |
| Q4 | 15 | $270K | First AE hired Q3 |
| **Year 1 Total** | **15** | **$570K ARR** | |

### Year 2 Target
- 50 customers, $2.5M ARR
- Seed round ($2-4M) if needed for growth

### Cost Structure (Year 1)

| Item | Monthly | Annual |
|------|---------|--------|
| Your salary (deferred/low) | $5K | $60K |
| Cloud hosting | $200 | $2.4K |
| Claude API | $200 | $2.4K |
| LegiScan + data sources | $300 | $3.6K |
| Legal (entity + contracts) | - | $5K |
| Sales tools (LinkedIn, CRM) | $200 | $2.4K |
| **Total** | **$5.9K** | **$75.8K** |

Breakeven: ~5 customers at $15K ACV = $75K

---

## Part 8: Deployment Steps (This Week)

### Step 1: GitHub Setup (15 minutes)
1. Create account at github.com/signup (personal email)
2. Create private repo: `workforce-compliance-ai`
3. Push code from your local project

### Step 2: Streamlit Cloud Deploy (10 minutes)
1. Go to share.streamlit.io
2. Sign in with GitHub
3. Click "New app" → select your repo → select `app.py`
4. Deploy (takes 2-3 minutes)
5. You get a URL like: `your-app.streamlit.app`

### Step 3: Claude API Key (5 minutes)
1. Go to console.anthropic.com
2. Create account, add payment ($5 minimum)
3. Generate API key
4. Add to Streamlit Cloud secrets (Settings → Secrets)

### Step 4: Test & Share
1. Open your deployed URL
2. Run the demo
3. Share link in customer discovery calls: "Let me show you something"

---

## Part 9: IP & Legal Considerations (Amazon)

### While still at Amazon:

- **DO:** Build on your own time, own equipment, own accounts
- **DO:** Use publicly available legal information (laws are public)
- **DO:** Talk to people outside Amazon for customer discovery
- **DON'T:** Use any Amazon proprietary data, tools, or code
- **DON'T:** Use Amazon email or systems for this
- **DON'T:** Solicit Amazon as a customer while employed
- **DON'T:** Use internal Amazon scheduling data as training data

### Key principle:
Your *knowledge* of how scheduling works is yours. Amazon's *data* and *tools* are theirs. The line is: "Could I have built this having worked at any warehouse company?" If yes, you're fine.

### Before leaving:
- Review your employment agreement's non-compete/IP assignment clauses
- Most Amazon roles have IP assignment for work done "in scope" — this product is clearly outside your finance role
- Consult an employment attorney ($500-1000 for a review) before filing any patents or raising money

---

## Part 10: Exit Scenarios

### Who acquires you (and why):

| Acquirer | Valuation Range | Why they'd buy |
|----------|----------------|---------------|
| UKG | $200M-$1B+ | Add AI compliance to their 50K+ customer base |
| Workday | $100M-$500M | Enter hourly workforce market |
| ADP | $200M-$1B+ | Compliance + payroll integration |
| Ceridian/Dayforce | $100M-$500M | Differentiate vs UKG |
| ServiceNow | $200M-$1B+ | Extend HR workflow automation |
| Private Equity | $50M-$200M | Roll up workforce management |

### Timeline to exit:
- Year 1-2: Build product, get to $2-5M ARR
- Year 3-4: Scale to $10-20M ARR, become category leader
- Year 4-6: Acquisition or IPO path

### What makes you acquirable:
1. **Data moat:** You have the most comprehensive, up-to-date labor rule database
2. **Customer base:** Enterprise customers with long contracts
3. **AI capability:** Rule parsing + reasoning that incumbents can't build quickly
4. **Regulatory expertise:** Domain knowledge encoded in the product

---

## Appendix: Outreach Templates

### Cold Outreach to VP Ops

**Subject:** Quick question about scheduling compliance at {company_name}

Hi {first_name},

I noticed {company_name} operates distribution centers in {state} — which means you're navigating the {law_name} predictive scheduling requirements.

I spent 5 years in Ops Finance at Amazon building workforce planning models, and I'm now researching how operations leaders handle the compliance complexity of multi-state scheduling laws. I'm not selling anything — I'm interviewing 15-20 ops leaders to validate whether this problem is worth solving with better tooling.

Would you have 25 minutes this week or next for a quick conversation? I'd love to hear how your team handles it today.

Either way, I appreciate your time.

Best,
Hamzeh

### Warm Intro via Amazon Alumni

**Subject:** Fellow Amazonian exploring workforce compliance — intro request

Hi {mutual_connection},

Hope you're doing well! I wanted to ask for a quick favor.

I'm building in the workforce compliance space (specifically: AI that ensures shift schedules comply with predictive scheduling laws and union rules before they're published). Think of it as "compliance guardrails for scheduling" — the kind of thing we wished existed when managing labor allocation at Amazon.

I noticed you're connected to {target_name} at {company_name}. Would you be open to making a quick intro? I'm in discovery mode — just trying to learn how their team handles multi-state scheduling compliance today.

Happy to return the favor anytime. Thanks!

Hamzeh

### Follow-Up After Interview

**Subject:** Thank you + insights from our conversation

Hi {first_name},

Thanks for spending time with me — your perspective on {key_insight} was incredibly valuable.

Three things I'm taking away from our conversation:
1. {takeaway_1}
2. {takeaway_2}
3. {takeaway_3}

As promised, here's what I'm hearing across the ops leaders I've spoken with so far:
- Most teams spend 2-4 hours per week on compliance checking manually
- Average violation cost is $15-50K per quarter (higher for unionized facilities)
- Nobody is happy with their current tool's compliance capabilities

I'm building a prototype based on these conversations. Would you be interested in seeing it when it's ready (2-3 weeks)? No commitment — just feedback.

Best,
Hamzeh

---

## Next Steps (Your Action Items)

1. **TODAY:** Create GitHub account + Anthropic API account
2. **THIS WEEK:** Deploy app to Streamlit Cloud, send first 10 outreach messages
3. **NEXT 2 WEEKS:** Complete 5 discovery interviews
4. **30 DAYS:** Have prototype demoed to 10 people, 2-3 design partner candidates identified
5. **60 DAYS:** First LOI signed or clear pivot signal
6. **90 DAYS:** Go/No-Go decision with data to back it up
