"""
Healthcare Compliance Rules for Workforce Compliance AI Platform.

Same engine as warehouse/logistics, different rules. This module demonstrates
platform scalability -- the compliance framework adapts to ANY regulated industry
by swapping rule sets while keeping the scheduling and audit engine intact.

Covers: nurse-patient ratios, shift limits, credential tracking, patient safety,
fatigue management, and healthcare union rules.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any

# =============================================================================
# 1. NURSE-PATIENT RATIOS BY STATE AND UNIT
# Same engine: ratio checks work like warehouse worker-to-task ratios
# =============================================================================

NURSE_PATIENT_RATIOS = {
    "California": {  # Title 22, Section 70217
        "ICU": {"ratio": (1, 2), "license_required": "RN"},
        "Med-Surg": {"ratio": (1, 5), "license_required": "RN"},
        "ED": {"ratio": (1, 4), "license_required": "RN"},
        "L&D": {"ratio": (1, 2), "license_required": "RN"},
        "Telemetry": {"ratio": (1, 4), "license_required": "RN"},
        "Psych": {"ratio": (1, 6), "license_required": "RN"},
        "OR": {"ratio": (1, 1), "license_required": "RN"},
    },
    "Massachusetts": {  # Question 4, 2014 ballot
        "ICU": {"ratio": (1, 1), "license_required": "RN"},  # 1:1 to 1:2 depending on acuity
        "Med-Surg": {"ratio": (1, 4), "license_required": "RN"},
        "ED": {"ratio": (1, 4), "license_required": "RN"},
    },
    "New York": {  # Similar to CA guidelines
        "ICU": {"ratio": (1, 2), "license_required": "RN"},
        "Med-Surg": {"ratio": (1, 5), "license_required": "RN"},
        "ED": {"ratio": (1, 4), "license_required": "RN"},
        "L&D": {"ratio": (1, 2), "license_required": "RN"},
        "Telemetry": {"ratio": (1, 4), "license_required": "RN"},
    },
}

# =============================================================================
# 2. SHIFT RULES
# Same engine: hour caps work like warehouse max-hours rules
# =============================================================================

SHIFT_RULES = {
    "max_shift_hours": 16,
    "mandatory_ot_prohibition_states": ["OR", "NY", "PA", "IL", "NJ"],
    "min_rest_between_shifts_hours": 10,  # 8-10hr depending on state
    "max_consecutive_days": 6,  # 5-6 depending on facility policy
    "break_requirements": {
        "8_hour_shift": {"breaks": 2, "meal_period_minutes": 30},
        "12_hour_shift": {"breaks": 3, "meal_period_minutes": 30},
    },
    "break_coverage_required": True,  # Must maintain ratios during breaks
}

# =============================================================================
# 3. CREDENTIAL REQUIREMENTS
# Same engine: credential tracking works like warehouse forklift certs
# =============================================================================

CREDENTIAL_REQUIREMENTS = {
    "RN": {
        "license": "State RN License (active, unencumbered)",
        "scope": ["assessment", "care_planning", "medication_admin", "IV_therapy",
                  "delegation", "patient_education", "charge_duties"],
        "certs_by_unit": {
            "ICU": ["BLS", "ACLS"],
            "ED": ["BLS", "ACLS", "PALS"],
            "Med-Surg": ["BLS"],
            "Telemetry": ["BLS", "ACLS"],
            "L&D": ["BLS", "NRP"],
        },
    },
    "LPN": {
        "license": "State LPN License (active)",
        "scope": ["medication_admin", "wound_care", "vital_signs", "documentation"],
        "scope_limits": ["NO_assessment", "NO_IV_push", "NO_blood_admin",
                         "NO_care_planning", "NO_charge_duties"],
        "certs_by_unit": {"Med-Surg": ["BLS"], "Psych": ["BLS"]},
    },
    "CNA": {
        "license": "State CNA Certification",
        "scope": ["vital_signs", "ADLs", "ambulation", "intake_output"],
        "supervision_required": "RN",  # Must have RN on same unit, same shift
        "max_patients": 10,
        "certs_by_unit": {"all": ["BLS"]},
    },
    "travel_nurse": {
        "compact_license": True,  # Nurse Licensure Compact (NLC) or state-specific
        "orientation_hours": 8,
        "float_restrictions": "home_unit_only_first_2_weeks",
    },
}

# =============================================================================
# 4. PATIENT SAFETY RULES
# Same engine: safety minimums work like warehouse safety officer requirements
# =============================================================================

PATIENT_SAFETY_RULES = {
    "charge_nurse": {"required": True, "per": "unit_per_shift", "license": "RN",
                     "min_experience_years": 2},
    "experience_mix": {
        "max_travelers_per_shift_pct": 0.50,  # No more than 50% travelers
        "min_experienced_staff_pct": 0.40,  # 40% must have 1+ year at facility
    },
    "code_team": {"required_24_7": True, "min_acls_per_unit": 1},
    "float_restrictions": {
        "ICU_float_to": ["Telemetry", "ED"],  # Can float to similar acuity
        "Med-Surg_float_to": ["Telemetry"],
        "no_float": ["L&D", "OR"],  # Specialty units, no floating in/out
    },
}

# =============================================================================
# 5. FATIGUE MANAGEMENT
# Same engine: fatigue tracking works like warehouse consecutive-hours alerts
# =============================================================================

FATIGUE_MANAGEMENT = {
    "max_weekly_hours": 60,
    "max_consecutive_hours": 16,
    "mandatory_rest_after_12hr_shift_hours": 10,
    "sentinel_event_trigger_hours": 16,  # TJC flags errors after 16+ hr shifts
    "double_back_prohibition": True,  # No night-to-day within 10 hours
    "fatigue_risk_levels": {
        "low": {"hours_worked": (0, 8)},
        "moderate": {"hours_worked": (8, 12)},
        "high": {"hours_worked": (12, 16)},
        "critical": {"hours_worked": (16, float("inf"))},
    },
}

# =============================================================================
# 6. HEALTHCARE UNION RULES
# Same engine: seniority/rotation rules work like warehouse union bid systems
# =============================================================================

HEALTHCARE_UNION_RULES = {
    "shift_preference": "seniority",  # Senior staff pick shifts first
    "weekend_rotation": "every_other",  # Max every-other-weekend
    "holiday_rotation": "alternating_years",  # If worked last year, off this year
    "low_census_cancellation": "inverse_seniority",  # Least senior canceled first
    "mandatory_ot_limits": {
        "max_mandatory_ot_per_period": 1,  # Max 1 mandatory OT per pay period
        "rotation_order": "inverse_seniority",
    },
    "float_restrictions": {
        "volunteer_first": True,
        "rotation_if_no_volunteer": True,
        "max_float_per_period": 2,  # Max 2 floats per pay period
    },
}


# =============================================================================
# 7. COMPLIANCE CHECK FUNCTION
# Same engine: check_healthcare_compliance mirrors check_warehouse_compliance
# =============================================================================

def check_healthcare_compliance(
    schedule: List[Dict[str, Any]],
    unit_census: Dict[str, int],
    staff_credentials: Dict[str, Dict[str, Any]],
    state: str = "California",
) -> List[Dict[str, Any]]:
    """
    Check a nursing schedule against all healthcare compliance rules.
    Same pattern as warehouse compliance -- iterate rules, flag violations.
    """
    violations = []

    # --- Ratio checks ---
    ratios = NURSE_PATIENT_RATIOS.get(state, NURSE_PATIENT_RATIOS["California"])
    units_in_schedule = {}
    for entry in schedule:
        unit = entry.get("unit")
        if unit not in units_in_schedule:
            units_in_schedule[unit] = []
        if entry.get("role") == "RN":
            units_in_schedule[unit].append(entry)

    for unit, census in unit_census.items():
        if unit in ratios:
            required_ratio = ratios[unit]["ratio"]
            max_patients_per_nurse = required_ratio[1]
            nurses_on_unit = len(units_in_schedule.get(unit, []))
            nurses_needed = -(-census // max_patients_per_nurse)  # Ceiling division
            if nurses_on_unit < nurses_needed:
                actual_ratio = f"1:{census // max(nurses_on_unit, 1)}"
                violations.append({
                    "rule": "NURSE_PATIENT_RATIO",
                    "severity": "CRITICAL",
                    "unit": unit,
                    "detail": (f"{unit}: {census} patients, {nurses_on_unit} nurses = "
                               f"{actual_ratio}. {state} requires 1:{max_patients_per_nurse}. "
                               f"Need {nurses_needed - nurses_on_unit} more RNs."),
                    "patient_safety_impact": "Direct risk to patient outcomes",
                })

    # --- Shift length and fatigue checks ---
    for entry in schedule:
        hours = entry.get("shift_hours", 0)
        if hours > SHIFT_RULES["max_shift_hours"]:
            violations.append({
                "rule": "MAX_SHIFT_EXCEEDED",
                "severity": "CRITICAL",
                "staff": entry.get("name"),
                "detail": f"{entry.get('name')} scheduled for {hours}hr shift (max {SHIFT_RULES['max_shift_hours']}hr).",
                "patient_safety_impact": "Fatigue-related sentinel event risk",
            })
        if hours > FATIGUE_MANAGEMENT["sentinel_event_trigger_hours"]:
            violations.append({
                "rule": "SENTINEL_EVENT_TRIGGER",
                "severity": "CRITICAL",
                "staff": entry.get("name"),
                "detail": f"{entry.get('name')}: {hours}hr shift triggers TJC sentinel event review.",
                "patient_safety_impact": "Joint Commission reportable event",
            })

    # --- Credential checks ---
    for entry in schedule:
        staff_id = entry.get("staff_id")
        creds = staff_credentials.get(staff_id, {})
        role = entry.get("role")
        unit = entry.get("unit")
        tasks = entry.get("tasks", [])

        # Scope violations (LPN doing RN-only tasks)
        if role == "LPN":
            lpn_limits = CREDENTIAL_REQUIREMENTS["LPN"]["scope_limits"]
            for task in tasks:
                if f"NO_{task}" in lpn_limits:
                    violations.append({
                        "rule": "SCOPE_VIOLATION",
                        "severity": "CRITICAL",
                        "staff": entry.get("name"),
                        "detail": f"{entry.get('name')} (LPN) assigned '{task}' -- outside LPN scope.",
                        "patient_safety_impact": "Unlicensed practice, patient harm risk",
                    })

        # Expired certifications
        if creds.get("bls_expiry"):
            expiry = datetime.strptime(creds["bls_expiry"], "%Y-%m-%d")
            if expiry < datetime.now():
                violations.append({
                    "rule": "EXPIRED_CERTIFICATION",
                    "severity": "HIGH",
                    "staff": entry.get("name"),
                    "detail": f"{entry.get('name')} BLS expired {creds['bls_expiry']}. Cannot work patient care.",
                    "patient_safety_impact": "Unable to respond to cardiac arrest",
                })

    # --- Patient safety checks ---
    for unit in unit_census:
        unit_staff = [e for e in schedule if e.get("unit") == unit]
        # Charge nurse check
        charge_on_unit = [e for e in unit_staff if e.get("is_charge")]
        if not charge_on_unit:
            violations.append({
                "rule": "NO_CHARGE_NURSE",
                "severity": "HIGH",
                "unit": unit,
                "detail": f"{unit}: No charge nurse assigned this shift.",
                "patient_safety_impact": "No clinical leadership for unit decisions",
            })

        # Experience mix -- too many travelers
        travelers = [e for e in unit_staff if e.get("is_traveler")]
        if unit_staff:
            traveler_pct = len(travelers) / len(unit_staff)
            max_pct = PATIENT_SAFETY_RULES["experience_mix"]["max_travelers_per_shift_pct"]
            if traveler_pct > max_pct:
                violations.append({
                    "rule": "EXPERIENCE_MIX_VIOLATION",
                    "severity": "HIGH",
                    "unit": unit,
                    "detail": (f"{unit}: {len(travelers)}/{len(unit_staff)} staff are travelers "
                               f"({traveler_pct:.0%}). Max allowed: {max_pct:.0%}."),
                    "patient_safety_impact": "Insufficient institutional knowledge for safe care",
                })

    return violations


# =============================================================================
# 8. SAMPLE DATA -- 30 staff, 3 units, schedule with intentional violations
# =============================================================================

SAMPLE_STAFF_CREDENTIALS = {
    "RN001": {"name": "Sarah Chen", "role": "RN", "bls_expiry": "2027-03-15", "acls": True, "is_traveler": False, "years_at_facility": 5},
    "RN002": {"name": "James Rivera", "role": "RN", "bls_expiry": "2026-11-01", "acls": True, "is_traveler": False, "years_at_facility": 3},
    "RN003": {"name": "Priya Patel", "role": "RN", "bls_expiry": "2027-06-20", "acls": True, "is_traveler": False, "years_at_facility": 7},
    "RN004": {"name": "Mike Thompson", "role": "RN", "bls_expiry": "2026-08-10", "acls": False, "is_traveler": False, "years_at_facility": 2},
    "RN005": {"name": "Lisa Zhang", "role": "RN", "bls_expiry": "2025-01-15", "acls": True, "is_traveler": False, "years_at_facility": 4},  # VIOLATION: expired BLS
    "RN006": {"name": "David Kim", "role": "RN", "bls_expiry": "2027-02-28", "acls": True, "is_traveler": True, "years_at_facility": 0},
    "RN007": {"name": "Rachel Green", "role": "RN", "bls_expiry": "2027-04-15", "acls": True, "is_traveler": True, "years_at_facility": 0},
    "RN008": {"name": "Tom Walsh", "role": "RN", "bls_expiry": "2026-12-01", "acls": True, "is_traveler": True, "years_at_facility": 0},
    "RN009": {"name": "Amy Foster", "role": "RN", "bls_expiry": "2027-01-20", "acls": True, "is_traveler": True, "years_at_facility": 0},
    "RN010": {"name": "Carlos Mendez", "role": "RN", "bls_expiry": "2027-05-10", "acls": True, "is_traveler": False, "years_at_facility": 6},
    "RN011": {"name": "Nina Kowalski", "role": "RN", "bls_expiry": "2026-09-30", "acls": True, "is_traveler": False, "years_at_facility": 4},
    "RN012": {"name": "Ben Harper", "role": "RN", "bls_expiry": "2027-07-01", "acls": False, "is_traveler": False, "years_at_facility": 1},
    "RN013": {"name": "Diana Ross", "role": "RN", "bls_expiry": "2027-03-15", "acls": True, "is_traveler": True, "years_at_facility": 0},
    "RN014": {"name": "Kevin Park", "role": "RN", "bls_expiry": "2026-10-15", "acls": True, "is_traveler": False, "years_at_facility": 3},
    "RN015": {"name": "Maria Santos", "role": "RN", "bls_expiry": "2027-08-20", "acls": True, "is_traveler": False, "years_at_facility": 8},
    "RN016": {"name": "Jake Morrison", "role": "RN", "bls_expiry": "2027-04-01", "acls": True, "is_traveler": True, "years_at_facility": 0},
    "RN017": {"name": "Aisha Williams", "role": "RN", "bls_expiry": "2026-12-15", "acls": True, "is_traveler": False, "years_at_facility": 5},
    "RN018": {"name": "Greg Nelson", "role": "RN", "bls_expiry": "2027-02-10", "acls": False, "is_traveler": False, "years_at_facility": 2},
    "LPN001": {"name": "Carol Davis", "role": "LPN", "bls_expiry": "2027-01-30", "acls": False, "is_traveler": False, "years_at_facility": 6},
    "LPN002": {"name": "Robert Lee", "role": "LPN", "bls_expiry": "2026-11-20", "acls": False, "is_traveler": False, "years_at_facility": 4},
    "LPN003": {"name": "Tina Brown", "role": "LPN", "bls_expiry": "2027-05-15", "acls": False, "is_traveler": False, "years_at_facility": 3},
    "CNA001": {"name": "Alex Johnson", "role": "CNA", "bls_expiry": "2027-03-01", "acls": False, "is_traveler": False, "years_at_facility": 2},
    "CNA002": {"name": "Pat O'Brien", "role": "CNA", "bls_expiry": "2026-09-15", "acls": False, "is_traveler": False, "years_at_facility": 1},
    "CNA003": {"name": "Sam Turner", "role": "CNA", "bls_expiry": "2027-06-01", "acls": False, "is_traveler": False, "years_at_facility": 3},
    "CNA004": {"name": "Jordan Blake", "role": "CNA", "bls_expiry": "2026-08-30", "acls": False, "is_traveler": False, "years_at_facility": 1},
    "CNA005": {"name": "Taylor Reed", "role": "CNA", "bls_expiry": "2027-04-20", "acls": False, "is_traveler": False, "years_at_facility": 2},
    "CNA006": {"name": "Morgan Hill", "role": "CNA", "bls_expiry": "2027-01-10", "acls": False, "is_traveler": False, "years_at_facility": 4},
    "CHG001": {"name": "Patricia Moore", "role": "RN", "bls_expiry": "2027-09-01", "acls": True, "is_traveler": False, "years_at_facility": 10},
    "CHG002": {"name": "William Grant", "role": "RN", "bls_expiry": "2027-07-15", "acls": True, "is_traveler": False, "years_at_facility": 8},
    "CHG003": {"name": "Susan Clark", "role": "RN", "bls_expiry": "2027-05-30", "acls": True, "is_traveler": False, "years_at_facility": 12},
}

# Unit census: ICU 12 beds, Med-Surg 30 beds, ED 20 beds
SAMPLE_UNIT_CENSUS = {"ICU": 12, "Med-Surg": 30, "ED": 20}

# Schedule with intentional violations for demo
SAMPLE_SCHEDULE = [
    # ICU -- only 4 RNs for 12 patients = 1:3 (VIOLATION: CA requires 1:2, need 6)
    {"staff_id": "RN001", "name": "Sarah Chen", "role": "RN", "unit": "ICU", "shift_hours": 12, "is_charge": True, "is_traveler": False, "tasks": []},
    {"staff_id": "RN006", "name": "David Kim", "role": "RN", "unit": "ICU", "shift_hours": 12, "is_charge": False, "is_traveler": True, "tasks": []},
    {"staff_id": "RN007", "name": "Rachel Green", "role": "RN", "unit": "ICU", "shift_hours": 12, "is_charge": False, "is_traveler": True, "tasks": []},
    {"staff_id": "RN008", "name": "Tom Walsh", "role": "RN", "unit": "ICU", "shift_hours": 12, "is_charge": False, "is_traveler": True, "tasks": []},
    # Med-Surg -- 6 RNs for 30 patients = 1:5 (compliant for CA)
    {"staff_id": "RN002", "name": "James Rivera", "role": "RN", "unit": "Med-Surg", "shift_hours": 12, "is_charge": False, "is_traveler": False, "tasks": []},
    {"staff_id": "RN003", "name": "Priya Patel", "role": "RN", "unit": "Med-Surg", "shift_hours": 12, "is_charge": False, "is_traveler": False, "tasks": []},
    {"staff_id": "RN004", "name": "Mike Thompson", "role": "RN", "unit": "Med-Surg", "shift_hours": 18, "is_charge": False, "is_traveler": False, "tasks": []},  # VIOLATION: 18hr shift
    {"staff_id": "RN010", "name": "Carlos Mendez", "role": "RN", "unit": "Med-Surg", "shift_hours": 12, "is_charge": False, "is_traveler": False, "tasks": []},
    {"staff_id": "RN011", "name": "Nina Kowalski", "role": "RN", "unit": "Med-Surg", "shift_hours": 12, "is_charge": False, "is_traveler": False, "tasks": []},
    {"staff_id": "RN012", "name": "Ben Harper", "role": "RN", "unit": "Med-Surg", "shift_hours": 12, "is_charge": False, "is_traveler": False, "tasks": []},
    {"staff_id": "LPN001", "name": "Carol Davis", "role": "LPN", "unit": "Med-Surg", "shift_hours": 12, "is_charge": False, "is_traveler": False, "tasks": ["assessment"]},  # VIOLATION: LPN doing assessment
    # Med-Surg has no charge nurse assigned -- VIOLATION
    # ED -- all travelers on same shift -- VIOLATION
    {"staff_id": "RN009", "name": "Amy Foster", "role": "RN", "unit": "ED", "shift_hours": 12, "is_charge": False, "is_traveler": True, "tasks": []},
    {"staff_id": "RN013", "name": "Diana Ross", "role": "RN", "unit": "ED", "shift_hours": 12, "is_charge": False, "is_traveler": True, "tasks": []},
    {"staff_id": "RN016", "name": "Jake Morrison", "role": "RN", "unit": "ED", "shift_hours": 12, "is_charge": False, "is_traveler": True, "tasks": []},
    {"staff_id": "RN005", "name": "Lisa Zhang", "role": "RN", "unit": "ED", "shift_hours": 12, "is_charge": False, "is_traveler": False, "tasks": []},  # VIOLATION: expired BLS
    {"staff_id": "RN014", "name": "Kevin Park", "role": "RN", "unit": "ED", "shift_hours": 12, "is_charge": False, "is_traveler": False, "tasks": []},
    # ED has no charge nurse assigned -- VIOLATION
]


# =============================================================================
# 9. MAIN BLOCK -- Run compliance checks and display results
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("WORKFORCE COMPLIANCE AI -- HEALTHCARE MODULE")
    print("Same engine, healthcare rules. Platform scalability proof.")
    print("=" * 70)
    print()

    # Run compliance check
    violations = check_healthcare_compliance(
        schedule=SAMPLE_SCHEDULE,
        unit_census=SAMPLE_UNIT_CENSUS,
        staff_credentials=SAMPLE_STAFF_CREDENTIALS,
        state="California",
    )

    # Display ratio calculations
    print("STAFFING RATIO ANALYSIS")
    print("-" * 50)
    ratios = NURSE_PATIENT_RATIOS["California"]
    for unit, census in SAMPLE_UNIT_CENSUS.items():
        rn_count = len([e for e in SAMPLE_SCHEDULE if e["unit"] == unit and e["role"] == "RN"])
        if unit in ratios:
            required = ratios[unit]["ratio"]
            actual = census / max(rn_count, 1)
            needed = -(-census // required[1])
            status = "COMPLIANT" if rn_count >= needed else "VIOLATION"
            print(f"  {unit}: {census} patients, {rn_count} nurses = 1:{actual:.1f}. "
                  f"CA requires 1:{required[1]}. "
                  f"{'OK' if status == 'COMPLIANT' else f'Need {needed - rn_count} more RNs.'}")
    print()

    # Display violations grouped by severity
    print(f"COMPLIANCE VIOLATIONS FOUND: {len(violations)}")
    print("-" * 50)
    for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        sev_violations = [v for v in violations if v["severity"] == severity]
        if sev_violations:
            print(f"\n  [{severity}] ({len(sev_violations)} violations)")
            for v in sev_violations:
                print(f"    Rule: {v['rule']}")
                print(f"    Detail: {v['detail']}")
                print(f"    Patient Impact: {v['patient_safety_impact']}")
                print()

    print("=" * 70)
    print("Platform insight: Same scheduling engine handles warehouse OR healthcare.")
    print("Swap the rules module, keep the AI optimization and audit trail.")
    print("=" * 70)
