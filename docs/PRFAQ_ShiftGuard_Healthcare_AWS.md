# PR/FAQ: ShiftGuard for Healthcare — AWS Workforce Compliance Product

**Author:** [Your Name]  
**Date:** July 2026  
**Status:** DRAFT — Dual-track strategy (Internal Amazon + External Healthcare)  
**Classification:** Amazon Confidential  

---

## THE DUAL-TRACK STRATEGY

```
Track 1: Internal Amazon Tool (FC operations, 1.5M workers)
Track 2: External Product via AWS (Healthcare market, $800B industry)
                    ↓
Both feed the same AI models → data flywheel accelerates both
```

**Why Healthcare First for External?**

| Factor | Healthcare Advantage |
|--------|---------------------|
| Pain severity | One ACGME violation can close a residency program |
| Budget | Hospitals spend $400K-$2M/year on scheduling software already |
| Regulatory pressure | Joint Commission, CMS, state DOH, OSHA — non-negotiable |
| Switching cost is LOW | Most hospitals hate their current WFM (UKG is dominant, universally disliked) |
| Amazon health ambitions | One Medical, Amazon Pharmacy, Amazon Health — this fits the portfolio |
| AWS healthcare customers | Epic, Cerner, hundreds of health systems already on AWS |

---

## PRESS RELEASE (Healthcare External)

### AWS Launches ShiftGuard for Healthcare: AI Compliance That Prevents Schedule Violations Before They Close Your Residency Program

**SEATTLE — 2027** — Amazon Web Services today announced ShiftGuard for Healthcare, an AI-powered scheduling compliance platform built specifically for hospitals, health systems, and clinical environments. Available through AWS Marketplace, ShiftGuard checks every clinical schedule against ACGME duty hour limits, nurse staffing ratios, state labor laws, and union contracts before publication — preventing the violations that lead to CMS citations, Joint Commission findings, and DOL investigations.

"We lost our ACGME accreditation for 6 months because a scheduling error put residents over 80 hours three weeks in a row," said [CMO Name], Chief Medical Officer at [Health System]. "Nobody noticed until the site visit. ShiftGuard would have flagged it the day the schedule was published."

**Healthcare-specific capabilities include:**
- **ACGME Duty Hour Compliance:** 80-hour weekly cap, 24+4 shift limits, 1-day-off-in-7, 10-hour rest between shifts — checked automatically for every resident
- **Nurse Staffing Ratios:** California Title 22, CMS Conditions of Participation, state-specific RN-to-patient ratios by unit type (ICU, ED, Med-Surg, L&D)
- **Fatigue Science:** SAFTE/FAST circadian models flag schedules that are LEGAL but HIGH fatigue risk — liability protection beyond mere compliance
- **Fair Call Distribution:** Night shifts, weekends, holidays distributed equitably with full transparency. Ends "the chief always gives herself holidays off"
- **FMLA Auto-Triggers:** Detects 3+ day absences and auto-generates required notifications within federal 5-day deadline
- **Union CBA Enforcement:** Digitizes nursing contracts (SEIU, NNU, UFCW) — seniority rules, mandatory rest, OT caps enforced automatically

ShiftGuard integrates with Epic, Cerner, UKG/Kronos, and any EHR/WFM system via FHIR and REST APIs. Setup takes hours, not months.

---

## WHY AMAZON WINS IN HEALTHCARE SCHEDULING

### Amazon's Unfair Advantages

| Advantage | Why No One Else Has It | Healthcare Impact |
|-----------|----------------------|-------------------|
| **1.5M worker scheduling data** | Largest hourly workforce on Earth already using our internal version | AI models trained on Amazon-scale data predict callouts, burnout, optimal staffing better than any competitor |
| **AWS infrastructure** | HIPAA-compliant (already BAA-ready), SOC 2, FedRAMP | Health systems trust AWS — they already run Epic/Cerner on it |
| **AI/ML expertise** | Bedrock, SageMaker, years of ops ML at FC scale | Predictive absenteeism, demand sensing, fatigue modeling — no WFM vendor has this depth |
| **One Medical + Amazon Health** | Direct healthcare operations experience | We KNOW clinical scheduling from the inside, not just as software vendors |
| **Amazon operations DNA** | Invented the science of hourly workforce optimization | FC scheduling patterns (VET/MET, shift codes, self-healing) translate directly to hospital staffing |
| **Distribution via AWS Marketplace** | 300K+ active AWS customers, many are health systems | Zero sales team needed for initial distribution — self-service trial |
| **Capital + patience** | Amazon invests for 7-year payoffs | Can undercut UKG on price while building the moat (data flywheel) |

---

### What UKG Can't Do (But We Can)

| Capability | UKG | ShiftGuard (Amazon) |
|-----------|-----|---------------------|
| Rule update speed | 3-6 months per law change | 48 hours (AI-assisted rule encoding) |
| Pre-publish compliance check | No (flags AFTER violations) | Yes — blocks publish with confidence score |
| Natural language explanations | No | "Denied because Dr. Patel already at 76h this week" |
| Fairness-aware scheduling | No | Equal distribution of nights/holidays with transparency |
| Fatigue science (circadian) | No (just counts hours) | SAFTE/FAST models, crash risk scoring |
| Predictive absenteeism | No | "78% chance someone calls out Friday night" |
| Self-healing gaps | No (manual process) | Auto-finds coverage, contacts, fills — manager wakes up to "resolved" |
| AI schedule generation | No | "Generate fair Q1 resident schedule" → done in seconds |
| Setup time | 6-12 months, $500K+ | Same day, $15-25/employee/month |
| Mobile worker experience | Dated app (2.8 stars) | Modern PWA (push notifications, one-tap actions) |

---

## HEALTHCARE-WORKER-FRIENDLY INTERFACE

### Design Principles for Clinical Staff

Healthcare workers are NOT warehouse workers. The interface must respect:

| Healthcare Reality | Interface Implication |
|---|---|
| Nurses check phones in 10-second gaps between patients | One-tap actions only. No forms, no scrolling. |
| Residents work 80h/week, exhausted | Giant text, high contrast, fatigue-aware colors |
| Charge nurses manage 20+ staff per shift | Dashboard shows WHO'S HERE NOW, not tomorrow |
| Attending physicians have authority but no time | One-glance approval: "Approve [name] [date] → tap" |
| Travel nurses need different onboarding | Role-aware views: permanent vs. traveler vs. resident |
| Night shift = impaired cognition after hour 10 | Dark mode default, minimal cognitive load, no complex decisions at 3 AM |
| Union nurses track hours precisely | Real-time hours counter always visible, contractual OT alert |
| Clinical certs expire (ACLS, BLS, NRP) | Cert countdown prominent, auto-block scheduling if expired |

### Healthcare-Specific UI Screens

**1. Nurse Dashboard (Charge Nurse / Unit Manager)**
```
┌─────────────────────────────────────────────────┐
│  ShiftGuard for Healthcare — ED Unit            │
│  Today: 14 nurses on | 2 off | 1 OPEN GAP      │
├─────────────────────────────────────────────────┤
│  ⚠️ GAP: Night 19:00-07:00 (1 RN short)        │
│  Recommend: Maria Santos (lowest OT, rested)    │
│  [Assign Maria] [See others]                    │
├─────────────────────────────────────────────────┤
│  Publish Confidence: 91% ✓                      │
│  1 issue: Dr. Patel at 78h (ACGME limit: 80)   │
│  [Fix] [Accept Risk]                            │
├─────────────────────────────────────────────────┤
│  Pending Requests:                              │
│  • RN Chen — Jul 15-17 PTO [Approve] [Deny]    │
│  • RN Wilson — Swap Fri↔Mon [Approve] [Deny]   │
└─────────────────────────────────────────────────┘
```

**2. Resident Schedule View (Program Director)**
```
┌─────────────────────────────────────────────────┐
│  Residency Compliance Dashboard                 │
│  Program: Emergency Medicine | PGY-1 through 3  │
├─────────────────────────────────────────────────┤
│  ACGME STATUS:                                  │
│  ✅ All residents under 80h/week                │
│  ✅ No 24+4 violations                          │
│  ⚠️ Dr. Kim: 6 consecutive days (max 6 OK but  │
│     recommend break for wellbeing)              │
├─────────────────────────────────────────────────┤
│  FAIRNESS THIS ROTATION:                        │
│  Nights: Kim 8 | Patel 7 | Jones 8 | Lee 7     │
│  Weekends: Kim 4 | Patel 5 | Jones 4 | Lee 5   │
│  Holidays: Kim 1 | Patel 1 | Jones 2 | Lee 0   │
│  [Generate Next Month] [Adjust]                 │
└─────────────────────────────────────────────────┘
```

**3. Staff Nurse Mobile (On-Shift View)**
```
┌───────────────────────────┐
│ Good evening, Sarah   🌙  │
│ ED | Staff RN | Night     │
├───────────────────────────┤
│ Hours this week: 36h      │
│ ████████████░░░ 4h to OT  │
├───────────────────────────┤
│ 🌙 Night shift in 22h     │
│ Tip: Nap 2-4PM for        │
│ alertness on night shift   │
├───────────────────────────┤
│ 💵 OT Available: Sat 19-07│
│ [Accept] [Pass]           │
├───────────────────────────┤
│ Team tonight:             │
│ Maria (Charge) | James    │
│ Aisha | You | Chen        │
├───────────────────────────┤
│ [Request Off] [Swap Shift]│
│ [Report Sick] [Ask AI]    │
└───────────────────────────┘
```

**4. Fatigue Warning (Night Shift Worker, Hour 10)**
```
┌───────────────────────────┐
│ ⚠️ FATIGUE CHECK-IN       │
│                           │
│ You're 10h into a 12h    │
│ night shift.              │
│                           │
│ Alertness estimate: 62%   │
│ (based on circadian model)│
│                           │
│ 💡 Take your break NOW.   │
│ 15 min rest = 23% boost   │
│ in alertness.             │
│                           │
│ [I'm taking a break]     │
│ [I'm fine, dismiss]      │
└───────────────────────────┘
```

---

## MARKET SIZING (Healthcare Only)

| Segment | Size | Our Target |
|---------|------|-----------|
| US Hospitals | 6,100 hospitals | 300 (5%) in Year 3 |
| Avg nursing staff per hospital | 500-2,000 | Mid-market: 200-800 |
| Current WFM spend | $15-40 PEPM | We charge: $18-25 PEPM |
| Total addressable (US hospitals) | $1.8B/year | |
| Add: clinics, LTC, home health | +$900M | |
| **Total Healthcare TAM** | **$2.7B** | |

**Revenue projection:**
- Year 1: 15 hospitals × 400 avg staff × $20 PEPM × 12 = **$1.4M ARR**
- Year 2: 60 hospitals × 500 avg staff × $22 PEPM × 12 = **$7.9M ARR**
- Year 3: 200 hospitals × 600 avg staff × $22 PEPM × 12 = **$31.7M ARR**

---

## GO-TO-MARKET VIA AWS

| Channel | How It Works |
|---------|-------------|
| **AWS Marketplace** | Self-service trial. Hospital IT finds it alongside Epic/Cerner tools. |
| **AWS Healthcare sales team** | Already selling to health systems. Add ShiftGuard to the conversation. |
| **One Medical integration** | Prove it internally first (Amazon's own clinics). Case study. |
| **Epic App Orchard** | List as Epic-integrated app. Epic hospitals discover it organically. |
| **Conference presence** | HIMSS, ANCC Magnet, AONE — nursing leadership conferences |
| **Viral tool: Risk Calculator** | Free, no signup. "Calculate your penalty exposure in 30 seconds." Captures leads. |

**Distribution advantage:** UKG has a 500-person sales team and 18-month cycles. We have AWS Marketplace + self-service trial + viral calculator. Different game entirely.

---

## COMPETITIVE MOAT (Grows Over Time)

```
Month 1:   Better UI + faster setup (10x faster than UKG)
Month 6:   Compliance-as-code library (50 jurisdictions)
Month 12:  Predictive models trained on real hospital data
Month 24:  Cross-hospital benchmarking ("your OT is 30% above peers")
Month 36:  Data flywheel — predictions improve with every customer
Month 48:  Industry standard — switching cost too high (historical data)
```

No competitor can shortcut this because:
1. Each jurisdiction = months of legal research + encoding
2. Fairness history per worker = years of accumulated data
3. Prediction accuracy = function of data volume (Amazon's advantage)
4. Nurse satisfaction data = retention weapon (can't get elsewhere)

---

## RISKS & MITIGATIONS

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| UKG copies our features | HIGH | They move slowly (3-6mo). Our AI advantage compounds faster than they can copy. Data flywheel is uncopyable. |
| Healthcare buyer resistance ("we're fine") | MEDIUM | Lead with $ exposure calculator. Show them violations in THEIR current schedule. Free trial. |
| Regulatory change breaks our rules | MEDIUM | AI-assisted rule updates in 48h. Version control with rollback. |
| HIPAA concerns | LOW | No PHI needed. Schedule data ≠ health records. AWS BAA covers infrastructure. |
| Union pushback ("AI managing our schedules") | MEDIUM | Frame as fairness tool FOR workers, not surveillance. Union endorsement strategy. |
| Amazon internal politics (competes with internal tools) | MEDIUM | Position as enhancement to internal tools, not replacement. Internal + external are different tracks. |

---

## WHAT'S ALREADY BUILT (Proof of Concept)

Working prototype demonstrates:
- ✅ 31 labor law rules across 4 jurisdictions
- ✅ ACGME duty hour compliance checking
- ✅ Nurse ratio validation
- ✅ AI-powered schedule generation with fairness constraints
- ✅ Worker self-service portal with auto-approval
- ✅ Manager action queue with inline approve/deny
- ✅ Smart notifications with fatigue science tips
- ✅ Holiday auction (priority-based fair allocation)
- ✅ Bias audit (NYC LL144 / EEOC four-fifths rule)
- ✅ UKG/Kronos API connector
- ✅ Google Sheets live sync
- ✅ Database persistence layer
- ✅ ROI reporting dashboard
- ✅ Free compliance risk calculator (viral growth tool)
- ✅ Industry-locked demo mode (?mode=healthcare)

**To see it live:** `streamlit run app.py` then navigate to `?mode=healthcare`

---

## ASK

**Requesting:**
1. **Headcount:** 4 engineers (2 backend, 1 frontend, 1 ML) + 1 healthcare domain expert
2. **Timeline:** 6 months to production pilot (5 hospital partners)
3. **Budget:** $2M first year (team + infrastructure + legal review)
4. **Sponsorship:** VP-level champion in either AWS Healthcare or Operations

**In return:**
- Working product in 6 months (not 18)
- 5 design partner hospitals generating real compliance data
- Path to $30M+ ARR by Year 3
- Internal deployment across Amazon operations sites simultaneously

---

## TENETS

1. **Nurses' time is sacred** — Every feature must work in <10 seconds. If it takes more than one tap, redesign it.
2. **Compliance is patient safety** — A fatigued nurse makes errors. This isn't just about fines — it's about preventing harm.
3. **Fair schedules reduce turnover** — The nursing shortage is a scheduling problem disguised as a hiring problem.
4. **AI advises, humans decide** — Clinical judgment always overrides algorithmic suggestions.
5. **Data stays in the hospital's control** — HIPAA-compliant by architecture, not by policy.

---

*Prepared for internal Amazon discussion. Not for external distribution.*
