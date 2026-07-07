# PR/FAQ: ShiftGuard — AI-Powered Schedule Compliance for Amazon Hourly Workforce

**Author:** [Your Name]  
**Date:** July 2026  
**Status:** DRAFT — For leadership review  
**Classification:** Amazon Confidential  

---

## PRESS RELEASE

### Amazon Launches ShiftGuard: AI That Catches Schedule Violations Before They Cost Millions

**SEATTLE — July 2026** — Amazon today announced ShiftGuard, an AI-powered compliance intelligence system that automatically checks every shift schedule against federal, state, and local labor laws before it's published. ShiftGuard is now live across Amazon Fulfillment Centers, preventing scheduling violations that previously resulted in Department of Labor investigations, class-action lawsuits, and tens of millions in penalties.

"Scheduling 1.5 million hourly associates across 50 states, each with different labor laws, predictive scheduling ordinances, and union agreements, is the most complex compliance problem in workforce management," said [VP/SVP Name], VP of Worldwide Operations. "ShiftGuard doesn't just flag violations after the fact — it prevents them from happening. It's the difference between a smoke detector and a firewall."

**The Problem:** Amazon's hourly workforce spans jurisdictions with different — and often conflicting — labor regulations. Chicago's Fair Workweek requires 14-day schedule notice with premium pay for changes. Oregon's Predictive Scheduling law mandates rest periods between shifts. California requires meal breaks at specific intervals. New York City's Fast Food scheduling law adds additional layers. Today, Operations managers must manually verify compliance across all applicable regulations for every schedule they publish. Violations are caught reactively — after a DOL complaint, after an associate files a claim, after the penalty is assessed.

**The Solution:** ShiftGuard analyzes every schedule against all applicable labor laws in real-time. Before a manager clicks "Publish," the system shows:
- Exact violations with the specific law being broken
- Dollar penalty exposure if published as-is
- AI-generated fix suggestions that maintain coverage
- Fairness distribution to prevent bias claims

The system also provides associates with self-service PTO requests with auto-approval (when coverage allows), reducing manager workload by 60% while improving associate satisfaction.

"I used to spend 4 hours every Sunday checking our schedule against the Chicago Fair Workweek rules," said [FC Manager Name], Area Manager at Amazon FC MDW2. "Now I get a confidence score in 2 seconds. Last month it caught a clopening violation I would have missed — that's a $500 fine per associate per occurrence we avoided."

ShiftGuard is built on Amazon's AI infrastructure and integrates natively with A-to-Z, MyTime, and existing FC scheduling tools. No new hardware or 6-month implementation required — it layers on top of existing systems.

For associates, ShiftGuard includes a fairness engine that ensures nights, weekends, holidays, and mandatory extra time (MET) are distributed equitably across the team, with full transparency. Associates can see their fairness score, request time off through the system, and receive AI-powered shift reminders with fatigue management tips.

ShiftGuard is now available for all Amazon Operations sites in the US, with international expansion (EU Working Time Directive, UK, Canada, Middle East) planned for 2027.

---

## FREQUENTLY ASKED QUESTIONS

### External (Associate/Manager-Facing)

**Q: What is ShiftGuard?**
A: ShiftGuard is an AI-powered compliance layer that checks your schedule against all applicable labor laws before it's published. It catches violations, suggests fixes, and shows managers the penalty risk in dollars. For associates, it provides fair scheduling, self-service PTO, and smart shift reminders.

**Q: Does this replace A-to-Z or MyTime?**
A: No. ShiftGuard sits ON TOP of existing scheduling systems. Think of it as a spell-checker for schedules — your tools stay the same, but now they're compliance-aware.

**Q: How does it know which laws apply to my site?**
A: ShiftGuard maintains a continuously-updated library of labor laws by jurisdiction. When a schedule is created for MDW2 (Chicago), it automatically applies Chicago Fair Workweek + Illinois ODRISA + federal FLSA + any applicable CBA. No manual configuration needed.

**Q: Will this affect my scheduling flexibility as a manager?**
A: You maintain full control. ShiftGuard shows violations and suggests fixes — it never blocks you from publishing. If you choose to accept a risk, you acknowledge it (logged in the audit trail). Think of it as a GPS that shows you speed traps — you decide whether to slow down.

**Q: How does the fairness engine work for associates?**
A: The system tracks who works nights, weekends, holidays, and MET over time. When assigning undesirable shifts, it prioritizes associates who've done fewer recently. Associates can see their fairness score and the system explains every decision in plain English.

**Q: Can I request PTO through ShiftGuard?**
A: Yes. Submit your request, and if coverage is maintained, it's auto-approved in seconds — no manager needed. If coverage is tight, it escalates to your manager with context. You'll always know WHY a decision was made.

---

### Internal (Stakeholder/Leadership FAQs)

**Q: What's the estimated cost savings?**
A: Conservative estimate based on current enforcement data:

| Category | Annual Savings (US Operations) |
|----------|-------------------------------|
| DOL penalties avoided | $15-40M (based on 2024-2025 settlement trends) |
| Class-action lawsuit risk reduction | $50-100M in avoided exposure |
| Manager time savings (4h/week × 10K managers) | $90M in labor productivity |
| Associate attrition reduction (schedule stability) | $25-50M (based on $4,500/turnover × reduced churn) |
| **Total estimated annual value** | **$180-280M** |

Cost to build and operate: ~$5-15M/year (engineering team + AI compute + legal updates).

**Q: Why build this instead of buying from UKG or a vendor?**
A: Three reasons:
1. **Scale:** No vendor handles 1.5M workers across 50 states with Amazon's schedule complexity (fixed shift codes, VET/MET, cross-trained roles, surge staffing).
2. **Integration:** ShiftGuard integrates natively with A-to-Z, MyTime, and Amazon's internal systems. A vendor would need 12-18 months of integration work.
3. **Data flywheel:** With Amazon's scheduling data, the AI predictions (callout probability, optimal staffing, fatigue risk) become uniquely powerful. No vendor has this data at this scale.
4. **Potential external product:** Once proven internally, this becomes a sellable product via AWS Marketplace (see "Productization" section below).

**Q: What's the competitive landscape?**
A: Current market leaders:
- **UKG/Kronos** ($5B+ revenue): Deep compliance, but slow updates (3-6 months per law change), expensive ($500K+ implementation), dated UI.
- **Legion WFM** ($185M funded): Good AI/forecasting, but shallow compliance, no CBA support.
- **Deputy** (mid-market): Good UX, but no enterprise compliance depth.

None of them offer: pre-publish compliance checking with dollar exposure, AI-generated fix suggestions, fairness-aware scheduling, or natural language decision explanation. These are ShiftGuard's unique differentiators.

**Q: What's the timeline to deploy?**
A: 
- **Phase 1 (Q3 2026):** Pilot at 5 FCs in high-risk jurisdictions (Chicago, Oregon, California, NYC). Layer on existing scheduling — read-only compliance check.
- **Phase 2 (Q4 2026):** Expand to 50 FCs. Add pre-publish blocking for CRITICAL violations. Associate self-service PTO.
- **Phase 3 (Q1 2027):** All US Operations (800+ sites). Full fairness engine, VET/MET distribution, holiday auction.
- **Phase 4 (2027):** International expansion + AWS Marketplace productization.

**Q: What's the associate experience impact?**
A: Based on research and pilot projections:
- Schedule stability score visible to every associate (research: #1 driver of hourly turnover)
- Fair distribution of undesirable shifts (transparent, auditable)
- Self-service PTO with instant approval (80%+ auto-approved, no manager bottleneck)
- 24h shift reminders with fatigue tips (e.g., "Night shift tomorrow — nap at 2PM for alertness")
- Plain English explanations for every decision ("denied because 2 teammates already off")
- Net: improved VOA scores on "scheduling fairness" questions

**Q: What about union implications?**
A: ShiftGuard strengthens CBA compliance, not weakens it:
- CBA rules are encoded as first-class constraints (seniority, rotation, OT caps)
- System proves compliance during grievance proceedings (timestamped audit trail)
- Fairness engine aligns with union goals (equitable distribution)
- Could reduce grievances by 30-50% by preventing violations before they happen
- Legal has reviewed: automated SCHEDULING is not an AEDT under NYC LL144 (scheduling ≠ hiring/firing)

**Q: What data does it need? Privacy implications?**
A: 
- **Input:** Schedule data (shifts, times, roles), employee roster (name, role, seniority, hire date), applicable jurisdiction
- **Does NOT need:** SSN, bank info, health records, performance data
- **Privacy:** FMLA/medical data is encrypted and restricted to HR only. Associates can request data deletion (CCPA compliant). No biometric data.
- **Storage:** All data in Amazon-controlled infrastructure (no third-party data sharing)

**Q: What if ShiftGuard gives wrong advice?**
A: 
- Legal disclaimer on all outputs: "compliance analysis, not legal advice"
- Rules are version-controlled with effective dates
- Human override always available (manager can accept risk, logged in audit)
- Amazon Legal reviews rule updates before deployment
- System is ADVISORY — managers make final decisions. Liability stays with Amazon's existing compliance structure.

**Q: How does this relate to Amazon's existing Compliance teams?**
A: ShiftGuard doesn't replace Employment Law or HR teams. It's a TOOL for Operations managers that encodes the rules those teams define. Think of it as:
- Legal team defines the rules → ShiftGuard encodes them
- ShiftGuard flags violations → Managers fix them
- If manager accepts risk → Legal is alerted for high-severity items
- Audit trail → Legal can use in defense during DOL investigations

**Q: Could this become an external AWS product?**
A: Yes — this is the long-term vision:
- **Phase 1:** Internal Amazon tool (prove value, reduce fines)
- **Phase 2:** Offer to Amazon subsidiaries (Whole Foods, MGM, Zoox)
- **Phase 3:** AWS Marketplace product: "Amazon Workforce Compliance" (similar to how Amazon's internal tools became AWS services)
- **TAM for external market:** $2.7B (workforce compliance software)
- **Moat if productized:** Amazon's scale data (1.5M workers) trains models no competitor can match

---

## APPENDIX: PROOF OF CONCEPT

A working prototype has been built demonstrating:
- 31 labor law rules across 4 jurisdictions (CA, IL/Chicago, OR, NYC)
- Real-time compliance checking with penalty exposure calculation
- AI-powered fix suggestions (Claude integration)
- Worker self-service portal with auto-approval engine
- Fairness-ranked coverage finding
- Holiday auction system (priority-based fair allocation)
- Smart notifications with fatigue science tips
- ROI reporting dashboard
- Integration connectors (UKG/Kronos, Google Sheets, database)

The prototype runs today and can be demonstrated on demand.

---

## TENETS (In Priority Order)

1. **Associate safety first** — No schedule that creates unsafe fatigue conditions should publish without explicit acknowledgment.
2. **Compliance is preventive, not reactive** — Catch violations BEFORE they happen, not after the DOL shows up.
3. **Fairness is a feature, not a report** — Equal distribution of undesirable work is enforced by the system, not hoped for.
4. **Managers decide, AI advises** — ShiftGuard recommends; humans choose. Override is always available with accountability.
5. **Speed of law** — When a new labor law passes, ShiftGuard updates within 48 hours, not 6 months.

---

*Document prepared for internal discussion. Not for external distribution.*
