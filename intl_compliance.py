"""
Workforce Compliance AI - International Labor Law Engine
Modular country rule packs. Add a country = add a rule set.
Supports: EU, UK, Germany, France, Australia, Canada, UAE, KSA, India.
"""

from datetime import datetime, timedelta


# ============================================================
# INTERNATIONAL RULE PACKS
# ============================================================

COUNTRY_RULES = {
    "EU": {
        "name": "European Union - Working Time Directive",
        "law": "Directive 2003/88/EC",
        "applies_to": "All EU member states (minimum standard, countries can be stricter)",
        "rules": [
            {"id": "EU-WTD-001", "name": "Maximum Weekly Hours", "description": "Maximum 48 hours average per week (calculated over 17-week reference period)", "requirement": "avg_weekly_hours <= 48", "reference_period_weeks": 17, "penalty": "Infringement proceedings + national penalties", "severity": "high"},
            {"id": "EU-WTD-002", "name": "Daily Rest", "description": "Minimum 11 consecutive hours rest in every 24-hour period", "requirement": "daily_rest_hours >= 11", "penalty": "National penalty (varies by member state)", "severity": "high"},
            {"id": "EU-WTD-003", "name": "Weekly Rest", "description": "Minimum 24 consecutive hours uninterrupted rest per 7-day period (plus the 11-hour daily rest = 35 hours total)", "requirement": "weekly_rest_hours >= 24", "penalty": "National penalty", "severity": "high"},
            {"id": "EU-WTD-004", "name": "Paid Annual Leave", "description": "Minimum 4 weeks (20 working days) paid annual leave per year", "requirement": "annual_leave_days >= 20", "penalty": "Cannot be replaced by payment in lieu (except on termination)", "severity": "high"},
            {"id": "EU-WTD-005", "name": "Night Work Limit", "description": "Night workers must not work more than 8 hours in any 24-hour period (average)", "requirement": "night_shift_hours <= 8 avg", "penalty": "National penalty", "severity": "medium"},
            {"id": "EU-WTD-006", "name": "Rest Break", "description": "Break if working day is longer than 6 hours (details per member state)", "requirement": "break_if_shift > 6_hours", "penalty": "National penalty", "severity": "medium"},
        ],
    },
    "UK": {
        "name": "United Kingdom - Working Time Regulations 1998 (post-Brexit)",
        "law": "Working Time Regulations 1998 (as amended)",
        "applies_to": "All workers in the UK (opted out of EU WTD but retained similar rules)",
        "rules": [
            {"id": "UK-WTR-001", "name": "Maximum Weekly Hours", "description": "48-hour maximum average week (17-week reference). Worker CAN opt out in writing.", "requirement": "avg_weekly_hours <= 48 (unless opted out)", "opt_out_available": True, "penalty": "Employment tribunal claim + HSE enforcement", "severity": "high"},
            {"id": "UK-WTR-002", "name": "Daily Rest", "description": "11 consecutive hours rest between working days", "requirement": "daily_rest_hours >= 11", "penalty": "Tribunal claim", "severity": "high"},
            {"id": "UK-WTR-003", "name": "Weekly Rest", "description": "24 hours uninterrupted rest per week (or 48 hours per fortnight)", "requirement": "weekly_rest >= 24h or fortnightly_rest >= 48h", "penalty": "Tribunal claim", "severity": "high"},
            {"id": "UK-WTR-004", "name": "Annual Leave", "description": "5.6 weeks paid leave (28 days for full-time, can include bank holidays)", "requirement": "annual_leave_days >= 28", "penalty": "Tribunal claim + unlawful deduction from wages", "severity": "high"},
            {"id": "UK-WTR-005", "name": "Night Work", "description": "Night workers: max 8 hours per 24-hour period (average). Free health assessment.", "requirement": "night_avg <= 8h, health_assessment_offered", "penalty": "HSE prosecution", "severity": "medium"},
            {"id": "UK-WTR-006", "name": "Rest Break", "description": "20-minute uninterrupted break if shift exceeds 6 hours", "requirement": "break >= 20min if shift > 6h", "penalty": "Tribunal claim", "severity": "medium"},
        ],
    },
    "Germany": {
        "name": "Germany - Arbeitszeitgesetz (Working Hours Act)",
        "law": "ArbZG (Arbeitszeitgesetz)",
        "applies_to": "All employees in Germany",
        "rules": [
            {"id": "DE-AZG-001", "name": "Daily Maximum", "description": "Max 8 hours per working day. Can extend to 10 hours if average over 6 months/24 weeks does not exceed 8h/day.", "requirement": "daily_hours <= 10, avg_daily <= 8 (6-month ref)", "penalty": "Fine up to EUR 15,000; criminal liability for repeated violations", "severity": "high"},
            {"id": "DE-AZG-002", "name": "Daily Rest", "description": "Minimum 11 hours uninterrupted rest between shifts", "requirement": "rest_between_shifts >= 11h", "penalty": "Fine up to EUR 15,000", "severity": "high"},
            {"id": "DE-AZG-003", "name": "Sunday/Holiday Prohibition", "description": "Work on Sundays and public holidays is generally prohibited (exceptions for healthcare, hospitality, emergency services)", "requirement": "no_sunday_work (with exceptions)", "penalty": "Fine + compensatory rest day within 2 weeks", "severity": "medium"},
            {"id": "DE-AZG-004", "name": "Break Requirements", "description": "30min break after 6h work, 45min after 9h. Can be split into 15min blocks.", "requirement": "break_30min_after_6h, break_45min_after_9h", "penalty": "Fine", "severity": "medium"},
            {"id": "DE-AZG-005", "name": "Night Work Compensation", "description": "Night workers entitled to appropriate number of paid days off OR salary supplement", "requirement": "night_compensation_provided", "penalty": "Labor court claim", "severity": "medium"},
            {"id": "DE-AZG-006", "name": "Annual Leave", "description": "Minimum 24 working days (based on 6-day week) = 20 days for 5-day week. Most contracts give 25-30.", "requirement": "annual_leave >= 20 working days", "penalty": "Labor court claim + damages", "severity": "high"},
        ],
    },
    "France": {
        "name": "France - Code du Travail",
        "law": "Code du Travail (Labour Code)",
        "applies_to": "All employees in France",
        "rules": [
            {"id": "FR-CDT-001", "name": "35-Hour Week", "description": "Standard working week is 35 hours. Hours beyond = overtime (limited to 220h/year default).", "requirement": "standard_week = 35h, overtime_cap = 220h/year", "penalty": "Overtime surcharge: +25% (first 8h), +50% (beyond). Fine for exceeding cap.", "severity": "high"},
            {"id": "FR-CDT-002", "name": "Daily Maximum", "description": "Maximum 10 hours per day (extendable to 12 by agreement in exceptional circumstances)", "requirement": "daily_hours <= 10", "penalty": "Fine EUR 750 per worker per violation", "severity": "high"},
            {"id": "FR-CDT-003", "name": "Weekly Maximum", "description": "Absolute maximum 48 hours in any single week. Average max 44 hours over 12 weeks.", "requirement": "weekly_hours <= 48, avg_12_weeks <= 44", "penalty": "Fine + criminal liability", "severity": "high"},
            {"id": "FR-CDT-004", "name": "Daily Rest", "description": "Minimum 11 consecutive hours rest between shifts", "requirement": "daily_rest >= 11h", "penalty": "Fine", "severity": "high"},
            {"id": "FR-CDT-005", "name": "Weekly Rest", "description": "Minimum 35 consecutive hours (24h + 11h daily rest). Must include Sunday.", "requirement": "weekly_rest >= 35h including Sunday", "penalty": "Fine EUR 1,500 per worker", "severity": "high"},
            {"id": "FR-CDT-006", "name": "Right to Disconnect", "description": "Companies with 50+ employees must define hours during which workers are not expected to send/receive emails", "requirement": "disconnect_policy_defined", "penalty": "No direct fine but negotiation obligation; labor court risk", "severity": "medium"},
            {"id": "FR-CDT-007", "name": "Paid Leave", "description": "Minimum 5 weeks (25 working days) paid annual leave", "requirement": "annual_leave >= 25 working days", "penalty": "Damages + labor inspector fine", "severity": "high"},
        ],
    },
    "Australia": {
        "name": "Australia - Fair Work Act 2009",
        "law": "Fair Work Act 2009 + National Employment Standards (NES)",
        "applies_to": "All national system employees in Australia",
        "rules": [
            {"id": "AU-FW-001", "name": "Maximum Weekly Hours", "description": "38 ordinary hours per week. Employer can request reasonable additional hours.", "requirement": "ordinary_hours <= 38, additional must be reasonable", "penalty": "Fair Work Ombudsman prosecution: up to AUD 93,900 per contravention (individual)", "severity": "high"},
            {"id": "AU-FW-002", "name": "Annual Leave", "description": "4 weeks paid annual leave per year (5 weeks for shift workers)", "requirement": "annual_leave >= 4 weeks (5 for shift workers)", "penalty": "FWO enforcement + back pay", "severity": "high"},
            {"id": "AU-FW-003", "name": "Personal/Carer's Leave", "description": "10 days paid personal/carer's leave per year (accumulates)", "requirement": "personal_leave >= 10 days/year", "penalty": "FWO enforcement", "severity": "high"},
            {"id": "AU-FW-004", "name": "Rest Between Shifts", "description": "Minimum 10-hour break between shifts (most modern awards)", "requirement": "rest_between_shifts >= 10h", "penalty": "Award breach — back pay + penalty", "severity": "high"},
            {"id": "AU-FW-005", "name": "Overtime Rates", "description": "First 2 hours overtime: 150%. After that: 200%. Sundays: 200%. Public holidays: 250%.", "requirement": "ot_rate_first_2h = 1.5, ot_after = 2.0, sunday = 2.0, holiday = 2.5", "penalty": "Underpayment claim + penalties", "severity": "high"},
            {"id": "AU-FW-006", "name": "Right to Disconnect", "description": "Employees can refuse contact outside working hours unless refusal is unreasonable (from Aug 2024)", "requirement": "no_contact_outside_hours (reasonable)", "penalty": "Stop orders + civil penalty", "severity": "medium"},
        ],
    },
    "Canada_Ontario": {
        "name": "Canada - Ontario Employment Standards Act",
        "law": "Employment Standards Act, 2000 (ESA)",
        "applies_to": "Most employees in Ontario",
        "rules": [
            {"id": "CA-ON-001", "name": "Daily Maximum", "description": "8 hours per day or established regular work day (whichever is greater). With agreement: up to 13 hours.", "requirement": "daily_hours <= 8 (or agreed max up to 13)", "penalty": "ESA prosecution: fine up to CAD 100,000 + imprisonment", "severity": "high"},
            {"id": "CA-ON-002", "name": "Weekly Maximum", "description": "48 hours per week maximum (can exceed only with written agreement + Ministry approval)", "requirement": "weekly_hours <= 48", "penalty": "ESA violation", "severity": "high"},
            {"id": "CA-ON-003", "name": "Daily Rest", "description": "11 consecutive hours free from work each day", "requirement": "daily_rest >= 11h", "penalty": "ESA violation", "severity": "high"},
            {"id": "CA-ON-004", "name": "Weekly Rest", "description": "At least 24 consecutive hours off every work week, OR 48 consecutive hours off every 2 weeks", "requirement": "weekly_rest >= 24h or biweekly >= 48h", "penalty": "ESA violation", "severity": "high"},
            {"id": "CA-ON-005", "name": "Overtime", "description": "Overtime at 1.5x after 44 hours/week", "requirement": "ot_threshold = 44h/week, rate = 1.5x", "penalty": "Back pay + ESA penalty", "severity": "high"},
            {"id": "CA-ON-006", "name": "Vacation", "description": "2 weeks after 1 year, 3 weeks after 5 years. 4% / 6% vacation pay.", "requirement": "vacation >= 2 weeks (< 5yr) or 3 weeks (5+ yr)", "penalty": "Back pay + fine", "severity": "high"},
        ],
    },
    "UAE": {
        "name": "United Arab Emirates - Federal Labour Law",
        "law": "Federal Decree-Law No. 33 of 2021",
        "applies_to": "All private sector employees in the UAE",
        "rules": [
            {"id": "UAE-LAB-001", "name": "Maximum Daily Hours", "description": "8 hours per day (can extend to 9 for trade/hotel/security). During Ramadan: reduced by 2 hours.", "requirement": "daily_hours <= 8 (9 for specified sectors). Ramadan: daily_hours -= 2", "penalty": "Fine AED 5,000 - 1,000,000", "severity": "high"},
            {"id": "UAE-LAB-002", "name": "Weekly Maximum", "description": "48 hours per week. Friday is normal rest day (or Saturday for some).", "requirement": "weekly_hours <= 48", "penalty": "Fine + labor ban risk", "severity": "high"},
            {"id": "UAE-LAB-003", "name": "Rest Break", "description": "Total working period including breaks must not exceed 12 hours. Break after 5 consecutive hours.", "requirement": "break_after_5h, total_period <= 12h", "penalty": "MOHRE fine", "severity": "medium"},
            {"id": "UAE-LAB-004", "name": "Overtime", "description": "Overtime: 125% normal rate. Night overtime (10pm-4am): 150%. Maximum 2 hours OT per day.", "requirement": "ot_rate = 1.25, night_ot = 1.5, max_ot = 2h/day", "penalty": "Back pay + fine", "severity": "high"},
            {"id": "UAE-LAB-005", "name": "Annual Leave", "description": "30 calendar days paid leave after 1 year. 2 days per month if 6-12 months service.", "requirement": "annual_leave >= 30 calendar days (after 1yr)", "penalty": "Back pay + MOHRE complaint", "severity": "high"},
            {"id": "UAE-LAB-006", "name": "Heat Stress Ban", "description": "Outdoor work prohibited between 12:30pm-3:00pm from June 15 to September 15", "requirement": "no_outdoor_work 12:30-15:00 (Jun 15 - Sep 15)", "penalty": "Fine AED 5,000 per worker + work suspension", "severity": "critical"},
            {"id": "UAE-LAB-007", "name": "Ramadan Hours", "description": "Working hours reduced by 2 hours per day during the month of Ramadan for all workers", "requirement": "ramadan_hours = normal - 2h", "penalty": "Fine", "severity": "high"},
        ],
    },
    "KSA": {
        "name": "Saudi Arabia - Labor Law",
        "law": "Royal Decree No. M/51 (Saudi Labor Law)",
        "applies_to": "All private sector workers in Saudi Arabia",
        "rules": [
            {"id": "KSA-LAB-001", "name": "Maximum Daily Hours", "description": "8 hours per day or 48 hours per week. During Ramadan (for Muslims): 6 hours/day or 36 hours/week.", "requirement": "daily <= 8h (6h Ramadan), weekly <= 48h (36h Ramadan)", "penalty": "Fine SAR 10,000 + suspension", "severity": "high"},
            {"id": "KSA-LAB-002", "name": "Rest Period", "description": "Not more than 5 consecutive hours without at least 30-minute break. Worker should not be at workplace > 12h/day.", "requirement": "break_30min_per_5h, max_presence = 12h", "penalty": "Fine + labor office complaint", "severity": "medium"},
            {"id": "KSA-LAB-003", "name": "Weekly Rest", "description": "Friday is the weekly rest day (can be changed to another day with MHRSD notification). Must be paid.", "requirement": "weekly_rest = Friday (or approved alternative), paid", "penalty": "Fine", "severity": "medium"},
            {"id": "KSA-LAB-004", "name": "Overtime", "description": "Overtime: 150% of hourly rate. Cannot exceed 720 hours per year.", "requirement": "ot_rate = 1.5x, annual_ot <= 720h", "penalty": "Back pay", "severity": "high"},
            {"id": "KSA-LAB-005", "name": "Annual Leave", "description": "21 days per year (first 5 years), 30 days after 5 years. Cannot be replaced by money during employment.", "requirement": "annual_leave >= 21d (< 5yr), >= 30d (5+yr)", "penalty": "Fine + back pay", "severity": "high"},
            {"id": "KSA-LAB-006", "name": "Heat Stress", "description": "Outdoor work banned 12:00-15:00 from June 15 to September 15", "requirement": "no_outdoor_work 12:00-15:00 (Jun 15 - Sep 15)", "penalty": "Fine SAR 10,000 per worker per incident", "severity": "critical"},
        ],
    },
    "India_Maharashtra": {
        "name": "India - Maharashtra Shops and Establishments Act",
        "law": "Maharashtra Shops and Establishments (Regulation of Employment and Conditions of Service) Act, 2017",
        "applies_to": "Commercial establishments in Maharashtra",
        "rules": [
            {"id": "IN-MH-001", "name": "Daily Maximum", "description": "Maximum 9 hours per day", "requirement": "daily_hours <= 9", "penalty": "Fine INR 50,000 first offense, INR 1,00,000 repeat", "severity": "high"},
            {"id": "IN-MH-002", "name": "Weekly Maximum", "description": "Maximum 48 hours per week", "requirement": "weekly_hours <= 48", "penalty": "Fine + imprisonment up to 3 months", "severity": "high"},
            {"id": "IN-MH-003", "name": "Spread Over", "description": "Working hours including breaks must not spread over more than 10.5 hours", "requirement": "spread_over <= 10.5h", "penalty": "Fine", "severity": "medium"},
            {"id": "IN-MH-004", "name": "Weekly Holiday", "description": "One paid holiday per week", "requirement": "weekly_holiday >= 1 day, paid", "penalty": "Fine", "severity": "high"},
            {"id": "IN-MH-005", "name": "Overtime", "description": "Overtime at 2x normal wages", "requirement": "ot_rate = 2.0x", "penalty": "Back pay at double rate", "severity": "high"},
            {"id": "IN-MH-006", "name": "Night Work (Women)", "description": "Women can work at night (after 2017 amendment) with safety measures, transport, and consent", "requirement": "night_work_women: consent + safety + transport", "penalty": "Fine + prosecution", "severity": "medium"},
            {"id": "IN-MH-007", "name": "Leave", "description": "15 days earned leave per year (after 12 months), plus 12 casual + 12 sick leave", "requirement": "earned_leave >= 15d, casual >= 12d, sick >= 12d", "penalty": "Fine + back pay", "severity": "high"},
        ],
    },
}


# ============================================================
# COMPLIANCE CHECKER (International)
# ============================================================

def get_country_rules(country_code):
    """Get all rules for a country."""
    return COUNTRY_RULES.get(country_code, {})


def get_all_countries():
    """List all supported countries with basic info."""
    return {code: {"name": r["name"], "law": r["law"], "rule_count": len(r["rules"])}
            for code, r in COUNTRY_RULES.items()}


def check_international_compliance(schedule_shifts, country_code, employee_info=None):
    """
    Check a schedule against a country's labor laws.
    Returns violations found.
    """
    country = COUNTRY_RULES.get(country_code)
    if not country:
        return {"error": f"Country '{country_code}' not supported"}

    violations = []
    rules = country["rules"]

    # Group shifts by employee
    from collections import defaultdict
    emp_shifts = defaultdict(list)
    for s in schedule_shifts:
        emp_id = s.get("worker_id", s.get("employee_id", "unknown"))
        emp_shifts[emp_id].append(s)

    for emp_id, shifts in emp_shifts.items():
        shifts.sort(key=lambda x: x.get("date", ""))
        emp_name = shifts[0].get("worker_name", shifts[0].get("name", emp_id))

        # Calculate metrics
        weekly_hours = sum(s.get("hours", 8) for s in shifts)
        daily_hours_max = max((s.get("hours", 8) for s in shifts), default=8)

        # Check rest between shifts
        for i in range(len(shifts) - 1):
            current_end = shifts[i].get("end", "15:00")
            next_start = shifts[i+1].get("start", "07:00")
            current_date = shifts[i].get("date", "")
            next_date = shifts[i+1].get("date", "")

            if current_date and next_date and current_date != next_date:
                # Simple rest calculation
                end_h = int(current_end.split(":")[0])
                start_h = int(next_start.split(":")[0])
                rest_hours = (24 - end_h) + start_h
                if rest_hours < 0:
                    rest_hours += 24

                # Check against country's rest requirement
                for rule in rules:
                    if "rest" in rule["name"].lower() and "daily" in rule["name"].lower():
                        required_rest = 11  # default for most countries
                        if rest_hours < required_rest:
                            violations.append({
                                "rule_id": rule["id"],
                                "rule_name": rule["name"],
                                "severity": rule["severity"].upper(),
                                "country": country_code,
                                "description": f"{emp_name}: Only {rest_hours}h rest between {current_date} and {next_date}. {rule['description']}",
                                "affected_employees": emp_name,
                                "legal_reference": country.get("law", ""),
                            })
                        break

        # Check weekly hours
        for rule in rules:
            if "weekly" in rule["name"].lower() and ("max" in rule["name"].lower() or "hour" in rule["name"].lower()):
                threshold = 48  # default
                if "35" in rule.get("description", ""):
                    threshold = 35
                elif "44" in rule.get("description", ""):
                    threshold = 44
                elif "38" in rule.get("description", ""):
                    threshold = 38

                if weekly_hours > threshold:
                    violations.append({
                        "rule_id": rule["id"],
                        "rule_name": rule["name"],
                        "severity": rule["severity"].upper(),
                        "country": country_code,
                        "description": f"{emp_name}: {weekly_hours}h/week exceeds {threshold}h limit. {rule['description']}",
                        "affected_employees": emp_name,
                        "legal_reference": country.get("law", ""),
                    })
                break

    return {
        "country": country_code,
        "country_name": country["name"],
        "law": country["law"],
        "violations_found": len(violations),
        "violations": violations,
    }


# ============================================================
# DEMO
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("  INTERNATIONAL LABOR LAW ENGINE")
    print("=" * 70)

    # Show supported countries
    countries = get_all_countries()
    print(f"\n  SUPPORTED COUNTRIES ({len(countries)}):")
    print(f"  {'Code':<15} {'Name':<50} {'Rules'}")
    print(f"  {'-'*75}")
    for code, info in countries.items():
        print(f"  {code:<15} {info['name']:<50} {info['rule_count']}")

    # Total rules
    total_rules = sum(len(r["rules"]) for r in COUNTRY_RULES.values())
    print(f"\n  Total international rules: {total_rules}")

    # Show France rules as example
    print(f"\n\n  FRANCE - CODE DU TRAVAIL (example):")
    print(f"  {'-'*50}")
    france = COUNTRY_RULES["France"]
    for r in france["rules"]:
        print(f"  [{r['id']}] {r['name']}")
        print(f"    {r['description'][:70]}")
        print()

    # Test compliance check with sample schedule
    sample_shifts = [
        {"worker_id": "W1", "worker_name": "Pierre Dupont", "date": "2026-07-07", "start": "06:00", "end": "18:00", "hours": 12},
        {"worker_id": "W1", "worker_name": "Pierre Dupont", "date": "2026-07-08", "start": "06:00", "end": "18:00", "hours": 12},
        {"worker_id": "W1", "worker_name": "Pierre Dupont", "date": "2026-07-09", "start": "06:00", "end": "18:00", "hours": 12},
        {"worker_id": "W1", "worker_name": "Pierre Dupont", "date": "2026-07-10", "start": "06:00", "end": "18:00", "hours": 12},
        {"worker_id": "W1", "worker_name": "Pierre Dupont", "date": "2026-07-11", "start": "06:00", "end": "14:00", "hours": 8},
    ]

    print(f"\n  COMPLIANCE CHECK - France (Pierre: 56h week):")
    result = check_international_compliance(sample_shifts, "France")
    print(f"  Violations: {result['violations_found']}")
    for v in result["violations"]:
        print(f"    [{v['severity']}] {v['rule_name']}: {v['description'][:60]}")
