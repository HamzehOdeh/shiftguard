# ShiftGuard: AI-Powered Workforce Compliance Intelligence

**The platform that shows you the dollar cost of every scheduling violation before you publish.**

---

## Executive Summary

Every year, U.S. employers pay **$2.7 billion** in wage and hour penalties — the single largest category of Department of Labor enforcement actions. The root cause isn't malice. It's complexity: a single warehouse in Chicago must comply with FLSA, Illinois ODRISA, Chicago Fair Workweek, any applicable CBA, company policy, and OSHA fatigue guidelines — simultaneously, for every shift, for every worker.

ShiftGuard is an AI compliance intelligence platform that checks shift schedules against all applicable labor laws, union contracts, and company policies **before they're published**. It catches violations instantly, shows the penalty exposure in dollars, and suggests compliant alternatives.

We don't replace your scheduling system. We make it compliant.

---

## The Problem

### Schedule Compliance Is Broken Everywhere

| The Reality | The Cost |
|-------------|----------|
| 70% of DOL investigations find violations | $1,150 avg penalty per violation |
| Predictive scheduling laws now in 12+ jurisdictions | $100-$500/worker/day for late schedule changes |
| Clopening violations in hospitality cost $500-$3,000 each | 83% of managers unaware of local ordinances |
| ACGME violations can shut down a residency program | One violation = 6 months probation |
| Class-action lawsuits for systematic violations | $5M-$50M settlements (FedEx, Walmart, Amazon) |

### Why Existing Solutions Fail

**UKG/Kronos** (market leader): Updates compliance rules every 3-6 months. Costs $500K+ to implement. Takes 6-12 months to deploy. By the time it's live, 3 new city ordinances have passed.

**Manual checking**: Operations managers spend 4-8 hours/week verifying schedules against regulations they don't fully understand. They miss violations routinely — especially edge cases involving rolling averages, consecutive day limits, and overlapping jurisdictions.

**Reactive compliance tools**: Flag violations after they happen. By then, the penalty is already incurred, the worker complaint is already filed, or the DOL investigation is already initiated.

---

## The Solution

### ShiftGuard: Preventive Compliance Intelligence

ShiftGuard sits on top of your existing scheduling system (UKG, ADP, When I Work, Google Sheets — or anything that produces a schedule). It acts as an intelligent compliance layer:

```
Schedule Created → ShiftGuard Checks → Violations Flagged → Fix Suggested → Publish with Confidence
         ↓                                      ↓
    60 seconds                          Shows $ penalty exposure
```

### What Makes Us Different

| Capability | ShiftGuard | UKG | Legion | Deputy |
|-----------|-----------|-----|--------|--------|
| Pre-publish compliance check | Yes | No (post-hoc) | No | No |
| Penalty $ exposure on every violation | Yes | No | No | No |
| AI fix suggestions | Yes | No | Partial | No |
| Multi-jurisdiction auto-detection | Yes | Manual config | No | No |
| Union CBA rule enforcement | Yes | Partial | No | No |
| Setup time | 60 seconds | 6-12 months | 3+ months | 2-4 weeks |
| Fairness engine (equitable distribution) | Yes | No | Cost-optimized | No |
| Plain English explanation of every decision | Yes | No | No | No |
| Price per employee/month | $15-25 | $50-100+ | $25-50+ | $6.50 |

---

## How It Works

### For Managers

1. **Upload or connect your schedule** — CSV, Google Sheets, UKG API, or manual entry
2. **Instant compliance scan** — every shift checked against all applicable laws in under 60 seconds
3. **See violations ranked by severity and cost** — "CRITICAL: $7,500/week exposure" with the exact law cited
4. **One-click fix** — AI suggests the least-disruptive compliant alternative
5. **Publish with a confidence score** — "94% compliant. 2 issues to fix."
6. **Ongoing monitoring** — schedule changes trigger instant re-check

### For Workers (Mobile PWA)

- See your schedule, request PTO, accept VET shifts
- Transparent fairness: see why decisions were made
- Smart notifications: shift reminders with fatigue tips
- Self-service: most requests auto-approved when coverage allows

### For Executives

- **ROI Dashboard**: penalties avoided, labor cost savings, compliance rate trends
- **Audit defense**: timestamped proof that every schedule was checked before publication
- **Benchmarking**: how your compliance rate compares to industry average

---

## The Technology

### AI Compliance Engine

ShiftGuard maintains a continuously-updated library of labor laws encoded as executable rules:

- **31 rules** across 6 jurisdictions (Oregon, NYC, Chicago, California, Federal, plus any CBA)
- **7 violation categories**: schedule notice, rest periods, consecutive days, minimum shift length, weekly hours cap, minor restrictions, leave compliance
- **50 U.S. states** with state-specific penalty amounts
- **Union CBA digitization**: converts contract language into enforceable rules

When a new law passes or an ordinance is updated, we push the rule to all affected customers within 48 hours — not 3-6 months.

### AI Reasoning (Claude-Powered)

Beyond rule-matching, ShiftGuard uses large language models to:

- Explain violations in plain English ("Denied because 2 teammates already off, coverage drops below 60%")
- Generate compliant schedule alternatives that minimize disruption
- Answer natural language questions ("Can Dr. Patel cover tonight without violating ACGME?")
- Predict callout patterns and pre-position coverage

### Fairness Engine (Unique to ShiftGuard)

No competing product offers algorithmic fairness. ShiftGuard ensures:

- Night shifts, weekends, and holidays distributed equitably
- Overtime distributed by fairness score, not just availability
- Historical tracking: year-over-year holiday rotation balance
- Transparent scoring: every worker sees their fairness index
- EEOC four-fifths rule compliance (bias audit built in)

---

## Market Opportunity

### Total Addressable Market: $2.7 Billion

| Segment | Employers | Workers | Our Revenue Opportunity |
|---------|-----------|---------|------------------------|
| Healthcare (hospitals, clinics) | 6,100 | 5.3M | $950M |
| Warehousing & Logistics | 19,000 | 1.8M | $540M |
| Retail (multi-location) | 31,000 | 4.2M | $630M |
| Hospitality (hotels, restaurants) | 54,000 | 3.1M | $465M |
| Manufacturing | 12,500 | 1.2M | $180M |

**SAM (Serviceable):** $1.08B (US employers with 100-5,000 hourly workers in regulated jurisdictions)

**SOM (Year 1 target):** $570K ARR (15 customers at avg. 250 employees, $25 PEPM)

### Why Now

1. **Regulatory wave**: 12+ new predictive scheduling ordinances since 2022 (Chicago, LA, Philadelphia, Seattle, San Francisco, NYC, Oregon...)
2. **Enforcement surge**: DOL hired 600+ new investigators in 2024-2025
3. **AI maturity**: LLMs now good enough to reason about complex multi-jurisdiction rules
4. **Worker expectations**: Gen Z hourly workers demand schedule stability and fairness transparency
5. **Post-COVID labor scarcity**: retention matters more — unfair scheduling drives 40% of hourly turnover

---

## Business Model

### SaaS: $15-25 Per Employee Per Month

| Tier | Price | Includes |
|------|-------|----------|
| **Compliance Core** | $15 PEPM | Pre-publish scan, violation alerts, fix suggestions, audit trail |
| **Compliance + Fairness** | $20 PEPM | + fairness engine, worker portal, PTO auto-approval, coverage intelligence |
| **Enterprise** | $25 PEPM | + AI chat, predictive callouts, demand sensing, multi-site, SSO, SLA |

### Revenue Projections

| | Year 1 | Year 2 | Year 3 |
|-|--------|--------|--------|
| Customers | 15 | 50 | 150 |
| Avg employees/customer | 250 | 350 | 400 |
| PEPM (blended) | $20 | $22 | $23 |
| **ARR** | **$570K** | **$2.5M** | **$8.3M** |
| Gross margin | 85% | 87% | 90% |

### Unit Economics

- **CAC**: ~$3,000 (free calculator → demo → trial → close)
- **LTV**: $60,000+ (3-year avg retention, $20 PEPM, 250 employees)
- **LTV/CAC**: 20x
- **Payback period**: <2 months
- **Net revenue retention**: 130%+ (seat expansion + tier upgrade)

---

## Go-To-Market Strategy

### Phase 1: Product-Led Growth (Months 1-6)

```
Free Compliance Calculator (viral, no signup)
        ↓ captures email
Interactive Demo (see YOUR industry violations)
        ↓ qualifies intent
14-Day Free Trial (upload real schedule)
        ↓ proves ROI
Close ($15-25 PEPM)
```

**The Free Calculator** is our growth engine. Enter your state, industry, and headcount → get instant risk grade and annual penalty exposure. No signup. Shareable. Every HR leader who sees their "$47,000 annual risk" becomes a warm lead.

### Phase 2: Vertical Focus (Months 6-18)

1. **Healthcare first** — highest pain, biggest budgets, regulatory non-negotiable
2. **Warehouse/logistics second** — high violation rates, predictive scheduling laws
3. **Multi-location retail third** — volume play, city-by-city ordinance complexity

### Phase 3: Platform (Months 18-36)

- API-first: embed compliance intelligence into any scheduling tool
- White-label: license to WFM vendors who lack compliance depth
- Marketplace: add-on rule packs by jurisdiction (EU, UK, Middle East)

---

## Competitive Moat

### Five Layers of Defensibility

| Moat | What It Means | Time to Replicate |
|------|---------------|-------------------|
| **Compliance-as-code library** | Every law = versioned, executable rule. 50 states + local. Continuously updated. | 12-18 months + dedicated legal team |
| **Data flywheel** | Every customer's schedules improve predictions for all. Callout patterns, demand curves, violation correlations. | Requires scale we'll have first |
| **Year-over-year fairness memory** | Historical allocation data per worker makes switching painful. "The system knows your team better than you do." | Cannot replicate without history |
| **AI reasoning layer** | LLM-powered explanations and schedule generation. Fine-tuned on scheduling domain. | Commodity AI without domain data |
| **Multi-jurisdiction velocity** | New law passes → rule deployed in 48h. Competitors take 3-6 months. | Requires architecture built for speed |

---

## Traction & Current State

### Product (Live — July 2026)

- **Full compliance engine**: 31 rules, 7 violation categories, 50 states, 5 industries
- **Healthcare app**: ACGME compliance, residency scheduler, jeopardy system, nursing ratios
- **AI assistant (Otto)**: Claude-powered, answers scheduling questions in plain English
- **Worker mobile app (PWA)**: installable, native-feeling, calendar/request/balance
- **Free calculator**: instant risk grade, deployed and shareable
- **Manager dashboard**: violations, fixes, ROI tracking, fairness scores
- **Data connectors**: UKG/Kronos API, Google Sheets, database layer

### Live URLs

| Asset | URL |
|-------|-----|
| Healthcare Demo (Streamlit) | shiftguard-giznml7xnt59j5aguqjerc.streamlit.app |
| Worker Mobile App (PWA) | frontend-lyart-three-52.vercel.app/worker |
| Free Calculator | frontend-lyart-three-52.vercel.app/calculator |
| Interactive Demo | frontend-lyart-three-52.vercel.app/demo |
| Source Code | github.com/HamzehOdeh/shiftguard |

---

## The Team

### Hamzeh Odeh — Founder & CEO

- **5 years Amazon Operations Finance** — managed compliance and labor cost optimization across millions of hours
- Saw firsthand: billions spent on scheduling tools that still produce violations daily
- Deep domain expertise in the exact problem being solved
- Built the entire product (engine, AI, frontend, mobile, connectors)

**Why this founder wins:**
- Lived the problem at the world's largest employer of hourly workers
- Understands both the ops pain (manager side) and the financial impact (finance side)
- Technical enough to build, business enough to sell
- Network includes ops leaders at the companies most likely to buy

---

## The Ask

### Seeking: $1.5M Seed Round

| Use of Funds | Allocation |
|--------------|-----------|
| Engineering (2 senior hires) | 45% |
| Sales & GTM (1 AE + marketing) | 30% |
| Legal (compliance rule library expansion) | 15% |
| Infrastructure & ops | 10% |

### Milestones to Series A (18 months)

1. 15 paying customers ($570K ARR)
2. 3 case studies with measurable ROI
3. Healthcare vertical dominance (5+ hospitals)
4. 95% gross retention rate
5. Self-serve signup live (product-led growth engine)

---

## Why ShiftGuard Wins

```
1. We show the COST before you publish (nobody else does)
2. We fix the violation for you (AI-powered, one click)  
3. We prove FAIRNESS algorithmically (legal protection + retention)
4. We deploy in 60 seconds (not 6 months)
5. We update rules in 48 hours (not 3-6 months)
```

**The bottom line:** Every schedule published without ShiftGuard is a gamble. We turn compliance from a liability into a competitive advantage.

---

*ShiftGuard — Schedule with confidence. Never pay another compliance fine.*

**Contact:** hello@shiftguard.ai  
**Demo:** frontend-lyart-three-52.vercel.app/demo  
**Calculator:** frontend-lyart-three-52.vercel.app/calculator
