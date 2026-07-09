# ShiftGuard — Service Level Agreement & Support Model

**Version:** 1.0  
**Effective Date:** Upon contract execution  
**Last Updated:** July 2026

---

## 1. Service Tiers

| | Starter | Professional | Enterprise |
|---|---|---|---|
| **PEPM** | $15 | $20 | $25 |
| **Min headcount** | 25 | 50 | 200+ |
| **Uptime SLA** | 99.5% | 99.9% | 99.95% |
| **Support hours** | Business (9-5 ET) | Extended (7a-9p ET) | 24/7 |
| **Response time (Critical)** | 4 hours | 1 hour | 15 minutes |
| **Response time (High)** | 8 hours | 4 hours | 1 hour |
| **Response time (Normal)** | 2 business days | 1 business day | 4 hours |
| **Dedicated CSM** | No | Shared | Named |
| **Custom integrations** | No | 1 included | Unlimited |
| **Law update SLA** | 7 days | 48 hours | 24 hours |
| **Onboarding** | Self-serve | Guided (2 sessions) | White-glove (unlimited) |
| **Data retention** | 12 months | 24 months | 7 years |
| **Audit reports** | Monthly | Weekly | Real-time |

---

## 2. Uptime Guarantee & Credits

### Definition
"Uptime" is measured as the percentage of minutes in a calendar month where the ShiftGuard platform is accessible and processing requests. Excludes scheduled maintenance windows (communicated 72h in advance, max 4h/month).

### Credit Schedule

| Monthly Uptime | Service Credit |
|---|---|
| 99.9% - 99.95% | None (Enterprise meets SLA) |
| 99.5% - 99.9% | 10% of monthly fee |
| 99.0% - 99.5% | 25% of monthly fee |
| 95.0% - 99.0% | 50% of monthly fee |
| Below 95.0% | 100% of monthly fee |

Credits are applied to the following month's invoice. Maximum credit per month: 100% of that month's fee. Credits do not apply during force majeure events.

### Monitoring
- Status page: status.shiftguard.ai (public)
- Automated synthetic monitoring every 60 seconds
- Customer-facing incident notifications via email within 5 minutes of detection

---

## 3. Support Model

### Channels
| Channel | Starter | Professional | Enterprise |
|---|---|---|---|
| In-app chat (Otto) | Yes | Yes | Yes |
| Email support | Yes | Yes | Yes |
| Phone support | No | Business hours | 24/7 |
| Slack Connect | No | No | Yes |
| On-site support | No | No | Quarterly |

### Severity Definitions

**Critical (P1):** Platform entirely unavailable, compliance engine returning incorrect results, data loss event, or security breach. All schedules cannot be published.

**High (P2):** Major feature degraded (e.g., AI reasoning unavailable, one jurisdiction's rules not processing), significant performance degradation (>5s response times), or incorrect violation detection for a specific rule.

**Normal (P3):** Non-blocking issues — UI bugs, report formatting errors, feature requests, minor performance issues, documentation gaps.

**Low (P4):** Cosmetic issues, enhancement requests, training questions.

### Escalation Path
1. L1 Support (in-app / email) — initial triage, known issues, configuration help
2. L2 Engineering — investigation, workarounds, bug fixes
3. L3 Platform Team — architecture issues, data recovery, security incidents
4. Executive Escalation — available to Enterprise customers via named CSM

---

## 4. Compliance Rule Maintenance

### Law Update SLA
When a labor law, regulation, or significant enforcement guidance changes:

| Tier | Update Deployed |
|---|---|
| Starter | Within 7 calendar days |
| Professional | Within 48 hours |
| Enterprise | Within 24 hours |

### Process
1. **Detection:** AI-assisted legal monitoring scans federal/state registers, DOL bulletins, and municipality notices daily
2. **Analysis:** Compliance team assesses impact, affected jurisdictions, and effective dates
3. **Implementation:** Rule engine updated, version-controlled, unit-tested
4. **Notification:** Affected customers notified via email + in-app banner with plain-English summary
5. **Audit trail:** Previous rule version preserved in compliance history for legal defense

### Covered Jurisdictions (at launch)
- All 50 US states (federal FLSA baseline + state-specific)
- Municipal: NYC, Chicago, San Francisco, Los Angeles, Seattle, Philadelphia, Portland
- Union CBA: Teamsters, SEIU, CNA/NNU (custom per customer)

### Adding New Jurisdictions
- US states/cities: Included in base subscription
- International: Professional/Enterprise add-on ($5 PEPM per country)

---

## 5. Data Handling & Security

### Architecture
- **Hosting:** AWS (us-east-1 primary, us-west-2 DR)
- **Encryption at rest:** AES-256
- **Encryption in transit:** TLS 1.3
- **Database:** PostgreSQL with automated daily backups, 30-day retention
- **Secrets management:** AWS Secrets Manager, rotated every 90 days

### HIPAA Compliance (Healthcare Tier)
- BAA (Business Associate Agreement) available for Enterprise healthcare customers
- PHI isolation: healthcare customer data stored in dedicated database schema
- Access logging: every read/write of employee data logged with actor + timestamp
- Minimum necessary principle: role-based access ensures users see only their scope
- Annual third-party security audit (SOC 2 Type II target: Q2 2027)

### Data Ownership
- Customer retains full ownership of all data
- Data export available at any time (CSV, JSON, API)
- Upon contract termination: 30-day data retrieval window, then permanent deletion with certificate of destruction
- No data used for cross-customer training without explicit written consent

### Incident Response
- Security incidents acknowledged within 30 minutes (Enterprise: 15 minutes)
- Customer notification within 1 hour of confirmed breach
- Post-incident report within 72 hours
- Compliant with state breach notification laws (varies 30-72 hours)

---

## 6. Onboarding Process

### Self-Serve (Starter)
1. Sign up, select state + industry
2. Upload schedule (CSV/Excel) or connect Google Sheets
3. First compliance report generated in < 60 seconds
4. In-app walkthrough + knowledge base articles
5. Otto AI available for configuration questions

### Guided (Professional)
1. **Kickoff call** (30 min): understand workflows, integrations, team structure
2. **Configuration session** (60 min): set up jurisdictions, rules, shift templates, roles
3. Go-live support: first week daily check-ins via email
4. 30-day health check call

### White-Glove (Enterprise)
1. **Discovery** (1 week): on-site or video sessions with ops, legal, HR stakeholders
2. **Configuration** (1-2 weeks): custom rules, CBA digitization, UKG/Kronos integration setup
3. **Parallel run** (2 weeks): ShiftGuard runs alongside existing process, discrepancies resolved
4. **Go-live** (1 day): cutover with live support on standby
5. **Stabilization** (4 weeks): daily monitoring, weekly calls, optimization recommendations
6. **Ongoing:** Quarterly business reviews, proactive rule update briefings

### Typical Timeline
| Tier | First value | Full deployment |
|---|---|---|
| Starter | Same day | 1 day |
| Professional | Day 1 | 1-2 weeks |
| Enterprise | Week 1 | 4-6 weeks |

---

## 7. Maintenance & Release Schedule

### Release Cadence
- **Bug fixes / hotfixes:** Deployed as needed (zero-downtime rolling deploys)
- **Feature releases:** Bi-weekly (every other Tuesday)
- **Major versions:** Quarterly (backward-compatible; breaking changes get 90-day migration window)

### Maintenance Windows
- Scheduled: Sundays 2:00-6:00 AM ET (announced 72h in advance)
- Maximum planned downtime: 4 hours/month
- Emergency maintenance: communicated via status page + email immediately

### Backward Compatibility
- API versioning: v1, v2, etc. — previous version supported for 12 months after successor launches
- Configuration changes: never retroactively applied; customer opts in
- Rule updates: forward-looking (new schedules checked against new rules; historical compliance reports use point-in-time rules)

---

## 8. Disaster Recovery

| Metric | Target |
|---|---|
| RPO (Recovery Point Objective) | 1 hour |
| RTO (Recovery Time Objective) | 4 hours (Starter/Pro), 1 hour (Enterprise) |
| Backup frequency | Every hour (incremental), daily (full) |
| DR region | us-west-2 (automatic failover) |
| DR testing | Quarterly (results shared with Enterprise customers) |

---

## 9. Contract Terms

### Billing
- Annual contracts (10% discount) or monthly
- NET 30 payment terms
- No setup fees for Starter/Professional
- Enterprise: custom SOW, may include implementation fee

### Termination
- Monthly: 30-day written notice
- Annual: auto-renews unless 60-day notice before renewal date
- For-cause termination: immediate if material breach uncured after 30-day notice
- SLA credit cap exceeded 3 consecutive months: customer may terminate without penalty

### Data Portability
- Full data export within 5 business days of request
- Formats: CSV, JSON, PDF (compliance reports)
- API access remains active for 30 days post-termination for data retrieval

---

## 10. Exclusions

This SLA does not apply to:
- Features labeled "Beta" or "Preview"
- Downtime caused by customer's systems, integrations, or network
- Force majeure events
- Scheduled maintenance within published windows
- Usage exceeding documented API rate limits
- Customer-initiated configuration changes that cause errors

---

## Contact

- **Support:** support@shiftguard.ai
- **Sales:** sales@shiftguard.ai
- **Security:** security@shiftguard.ai
- **Status page:** status.shiftguard.ai
- **Documentation:** docs.shiftguard.ai

---

*This document is a template for customer agreements. Specific terms may be negotiated for Enterprise contracts. ShiftGuard reserves the right to update this SLA with 30-day written notice to affected customers.*
