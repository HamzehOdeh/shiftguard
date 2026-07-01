"""
Workforce Compliance AI - Daycare/Childcare Industry Module
Staff-to-child ratio compliance engine for licensed childcare facilities.
Same platform architecture as warehouse/retail modules - different ruleset.
Scalable: add any state by extending the ratio dictionaries below.
"""

from datetime import datetime

# STAFF-TO-CHILD RATIOS BY STATE AND AGE GROUP
# Format: {state: {age_group: (staff, children)}}
# Extensible - add new states/territories as licensing data becomes available.

STAFF_CHILD_RATIOS = {
    "federal": {
        "infants_0-12mo": (1, 3),
        "toddlers_12-24mo": (1, 4),
        "2yr": (1, 6),
        "3yr": (1, 9),
        "4yr": (1, 10),
        "5yr+": (1, 12),
    },
    "california": {
        "infants_0-18mo": (1, 4),
        "toddlers_18-30mo": (1, 6),
        "preschool_30mo-6yr": (1, 12),
    },
    "new_york": {
        "infants_0-18mo": (1, 4),
        "toddlers_18-36mo": (1, 5),
        "3-5yr": (1, 7),
    },
    "texas": {
        "infants_0-17mo": (1, 4),
        "18mo-2yr": (1, 5),
        "2yr": (1, 9),
        "3yr": (1, 13),
        "4yr": (1, 16),
    },
    "illinois": {
        "infants_0-14mo": (1, 4),
        "15-20mo": (1, 5),
        "21-35mo": (1, 8),
        "3yr": (1, 10),
        "4-5yr": (1, 10),
    },
    "florida": {
        "infants_0-12mo": (1, 4),
        "1yr": (1, 6),
        "2yr": (1, 11),
        "3yr": (1, 15),
        "4-5yr": (1, 20),
    },
    "massachusetts": {
        "infants_0-15mo": (1, 3),
        "toddlers_15-33mo": (1, 4),
        "2.9-7yr": (1, 10),
    },
}

# GROUP SIZE LIMITS (max children per classroom regardless of staff count)
# Platform can enforce both ratio AND group size simultaneously.

GROUP_SIZE_LIMITS = {
    "federal": {"infants": 6, "toddlers": 8, "2yr": 12, "3yr": 18, "4yr": 20, "5yr+": 24},
    "illinois": {"infants": 12, "15-20mo": 15, "21-35mo": 16, "3yr": 20, "4-5yr": 20},
    "new_york": {"infants": 8, "toddlers": 10, "3-5yr": 15},
}

# STAFF QUALIFICATIONS - licensing requirements per role

STAFF_QUALIFICATIONS = {
    "lead_teacher": {"education": "CDA credential or Associate/Bachelor in ECE",
                     "experience_years": 2, "cpr_first_aid": True,
                     "background_check": True, "annual_training_hours": 20},
    "assistant_teacher": {"education": "HS diploma + state-approved training (30hrs)",
                          "experience_years": 0, "cpr_first_aid": True,
                          "background_check": True, "annual_training_hours": 15},
    "director": {"education": "Bachelor degree in ECE or related field",
                 "experience_years": 5, "cpr_first_aid": True,
                 "background_check": True, "annual_training_hours": 30},
}

# SCHEDULING RULES - ratio must hold at ALL times including transitions

SCHEDULING_RULES = {
    "ratio_maintained_always": True,  # arrival, nap, outdoor, breaks
    "minimum_staff_on_site": 2, "mixed_age_policy": "use_strictest_ratio",
    "break_coverage": "float_staff_required", "check_interval_minutes": 30,
}

# VIOLATION SEVERITY - drives licensing risk scoring

VIOLATION_SEVERITY = {
    "ratio_exceeded": "CRITICAL",             # immediate license risk
    "unqualified_staff_alone": "CRITICAL",    # assistant alone with children
    "expired_background_check": "CRITICAL",   # cannot be on premises
    "below_minimum_staff": "CRITICAL",        # fewer than 2 on site
    "training_deficiency": "HIGH",            # corrective action window
    "expired_cpr": "HIGH",                    # must remedy within 30 days
    "group_size_exceeded": "HIGH",
}


# CORE COMPLIANCE ENGINE

def calculate_required_staff(enrollment_by_age, state="federal"):
    """Return minimum staff needed per room given enrollment and state ratios.
    Scales to any state in STAFF_CHILD_RATIOS dictionary.
    """
    ratios = STAFF_CHILD_RATIOS.get(state, STAFF_CHILD_RATIOS["federal"])
    results = {}
    total_staff = 0
    for age_group, child_count in enrollment_by_age.items():
        # Find matching ratio key (partial match for flexibility)
        matched_ratio = None
        for key, (staff, children) in ratios.items():
            if age_group.lower() in key.lower() or key.lower() in age_group.lower():
                matched_ratio = (staff, children)
                break
        if not matched_ratio:
            matched_ratio = (1, 4)  # conservative fallback
        staff_per, children_per = matched_ratio
        needed = -(-child_count // children_per) * staff_per  # ceiling division
        results[age_group] = {"children": child_count, "staff_needed": needed,
                              "ratio": f"1:{children_per}"}
        total_staff += needed
    results["_total"] = total_staff
    return results


def check_daycare_compliance(schedule, enrollment, staff_qualifications, state="illinois"):
    """Check compliance at 30-min intervals across the full operating day.
    Returns list of violations with time, room, severity, and remediation.
    Platform-agnostic: works for any state once ratios are loaded.
    """
    violations = []
    ratios = STAFF_CHILD_RATIOS.get(state, STAFF_CHILD_RATIOS["federal"])
    interval = SCHEDULING_RULES["check_interval_minutes"]

    # Check credentials first (applies regardless of time)
    for staff in staff_qualifications:
        if staff.get("cpr_expiry") and staff["cpr_expiry"] < datetime.now().strftime("%Y-%m-%d"):
            violations.append({
                "type": "expired_cpr", "severity": VIOLATION_SEVERITY["expired_cpr"],
                "staff": staff["name"], "detail": f"CPR expired {staff['cpr_expiry']}",
            })
        if staff.get("background_check_expiry") and \
           staff["background_check_expiry"] < datetime.now().strftime("%Y-%m-%d"):
            violations.append({
                "type": "expired_background_check",
                "severity": VIOLATION_SEVERITY["expired_background_check"],
                "staff": staff["name"],
                "detail": "Cannot be on premises with expired background check",
            })
        if staff.get("role") == "assistant_teacher" and staff.get("alone_with_children"):
            violations.append({
                "type": "unqualified_staff_alone",
                "severity": VIOLATION_SEVERITY["unqualified_staff_alone"],
                "staff": staff["name"],
                "detail": "Assistant teacher cannot be sole supervisor",
            })

    # Check ratios at each 30-min interval
    for time_block in schedule:
        time_label = time_block["time"]
        total_staff_on_site = 0

        for room in time_block.get("rooms", []):
            room_name = room["name"]
            children = room["children_present"]
            staff_count = room["staff_present"]
            total_staff_on_site += staff_count

            # Find applicable ratio
            matched_ratio = None
            for key, (s, c) in ratios.items():
                if room.get("age_group", "").lower() in key.lower() or \
                   key.lower() in room.get("age_group", "").lower():
                    matched_ratio = (s, c)
                    break
            if not matched_ratio:
                matched_ratio = (1, 4)

            staff_per, children_per = matched_ratio
            required = -(-children // children_per) * staff_per
            actual_ratio = f"1:{children // staff_count}" if staff_count > 0 else "1:0"

            if staff_count < required:
                violations.append({
                    "type": "ratio_exceeded",
                    "severity": VIOLATION_SEVERITY["ratio_exceeded"],
                    "time": time_label, "room": room_name,
                    "detail": f"{children} children, {staff_count} staff = {actual_ratio}. "
                              f"Requires 1:{children_per}. Need {required - staff_count} more staff.",
                })

        # Check minimum staff on site
        if total_staff_on_site < SCHEDULING_RULES["minimum_staff_on_site"]:
            violations.append({
                "type": "below_minimum_staff",
                "severity": VIOLATION_SEVERITY["below_minimum_staff"],
                "time": time_label,
                "detail": f"Only {total_staff_on_site} staff on site. Minimum is 2.",
            })

    return violations


# SAMPLE DATA - 15 staff, 60 children facility in Illinois (with violations)

def _staff(name, role, cpr, bg, alone=False):
    return {"name": name, "role": role, "cpr_expiry": cpr,
            "background_check_expiry": bg, "alone_with_children": alone}

SAMPLE_STAFF = [
    _staff("Maria Torres", "director", "2027-03-15", "2027-01-10"),
    _staff("James Chen", "lead_teacher", "2027-05-20", "2027-06-01"),
    _staff("Sarah Kim", "lead_teacher", "2027-08-10", "2027-04-15"),
    _staff("David Okafor", "lead_teacher", "2027-02-28", "2027-09-01"),
    _staff("Lisa Patel", "lead_teacher", "2027-11-30", "2027-07-20"),
    _staff("Tom Nguyen", "assistant_teacher", "2025-11-01", "2027-05-15"),  # EXPIRED CPR
    _staff("Amy Walsh", "assistant_teacher", "2027-04-10", "2027-03-22", alone=True),  # VIOLATION
    _staff("Carlos Ruiz", "assistant_teacher", "2027-06-15", "2027-08-30"),
    _staff("Rachel Green", "lead_teacher", "2027-09-01", "2027-02-14"),
    _staff("Mike Johnson", "assistant_teacher", "2027-07-20", "2027-11-01"),
    _staff("Nina Kowalski", "lead_teacher", "2027-10-05", "2027-12-01"),
    _staff("Omar Hassan", "assistant_teacher", "2027-01-15", "2027-04-30"),
    _staff("Priya Sharma", "lead_teacher", "2027-12-20", "2027-10-10"),
    _staff("Kevin Brown", "assistant_teacher", "2027-03-30", "2027-06-15"),
    _staff("Diana Lopez", "assistant_teacher", "2027-08-25", "2027-09-20"),
]

# Enrollment: Infants 8, Toddlers 12, Preschool 20, Pre-K 20 = 60 total
SAMPLE_ENROLLMENT = {
    "infants": 8,
    "toddlers_15-20mo": 12,
    "preschool_3yr": 20,
    "pre-k_4-5yr": 20,
}

# Schedule with intentional violations at specific time blocks
def _room(name, age, children, staff):
    return {"name": name, "age_group": age, "children_present": children, "staff_present": staff}

SAMPLE_SCHEDULE = [
    {"time": "6:30am", "rooms": [
        _room("Infant Room", "infants", 3, 1),
    ]},  # VIOLATION: only 1 staff on site at opening
    {"time": "7:00am", "rooms": [
        _room("Infant Room", "infants", 5, 2),
        _room("Toddler Room", "15-20mo", 4, 1),
    ]},
    {"time": "8:00am", "rooms": [
        _room("Infant Room", "infants", 8, 2), _room("Toddler Room", "15-20mo", 12, 3),
        _room("Preschool Room", "3yr", 20, 2), _room("Pre-K Room", "4-5yr", 20, 2),
    ]},
    {"time": "9:00am", "rooms": [
        _room("Infant Room", "infants", 8, 2), _room("Toddler Room", "15-20mo", 12, 3),
        _room("Preschool Room", "3yr", 20, 2), _room("Pre-K Room", "4-5yr", 20, 2),
    ]},
    {"time": "11:30am", "rooms": [  # Lunch break coverage gap
        _room("Infant Room", "infants", 8, 1),  # VIOLATION: 1:8 need 1:4
        _room("Toddler Room", "15-20mo", 12, 2),
        _room("Preschool Room", "3yr", 20, 2), _room("Pre-K Room", "4-5yr", 20, 2),
    ]},
    {"time": "2:00pm", "rooms": [
        _room("Infant Room", "infants", 8, 2), _room("Toddler Room", "15-20mo", 12, 3),
        _room("Preschool Room", "3yr", 20, 2), _room("Pre-K Room", "4-5yr", 20, 2),
    ]},
    {"time": "5:00pm", "rooms": [
        _room("Infant Room", "infants", 4, 1), _room("Toddler Room", "15-20mo", 6, 2),
        _room("Preschool Room", "3yr", 10, 1), _room("Pre-K Room", "4-5yr", 12, 2),
    ]},
]


# MAIN - Run compliance analysis and print report

if __name__ == "__main__":
    print("=" * 70)
    print("WORKFORCE COMPLIANCE AI - DAYCARE MODULE")
    print("Facility: Bright Futures Learning Center | State: Illinois")
    print("Enrollment: 60 children | Staff: 15 | Operating: 6:30am - 6:00pm")
    print("=" * 70)

    # Calculate required staffing
    print("\n--- MINIMUM STAFFING REQUIREMENTS (Illinois) ---")
    requirements = calculate_required_staff(SAMPLE_ENROLLMENT, "illinois")
    for room, data in requirements.items():
        if room == "_total":
            print(f"\n  TOTAL MINIMUM STAFF NEEDED: {data}")
        else:
            print(f"  {room}: {data['children']} children / ratio {data['ratio']}"
                  f" = {data['staff_needed']} staff required")

    # Run full compliance check
    print("\n--- COMPLIANCE CHECK (30-min intervals) ---")
    violations = check_daycare_compliance(
        SAMPLE_SCHEDULE, SAMPLE_ENROLLMENT, SAMPLE_STAFF, "illinois"
    )

    # Print ratio analysis per time block
    print("\n--- RATIO ANALYSIS BY TIME BLOCK ---")
    ratios = STAFF_CHILD_RATIOS["illinois"]
    for block in SAMPLE_SCHEDULE:
        print(f"\n  [{block['time']}]")
        for room in block.get("rooms", []):
            c = room["children_present"]
            s = room["staff_present"]
            actual = f"1:{c // s}" if s > 0 else "NO STAFF"
            # Determine required ratio
            req_ratio = "1:4"  # default
            for key, (_, children_per) in ratios.items():
                if room.get("age_group", "").lower() in key.lower() or \
                   key.lower() in room.get("age_group", "").lower():
                    req_ratio = f"1:{children_per}"
                    break
            status = "COMPLIANT" if c / s <= int(req_ratio.split(":")[1]) else "VIOLATION"
            marker = "  " if status == "COMPLIANT" else ">>"
            print(f"  {marker} {room['name']}: {c} children, {s} staff = {actual}. "
                  f"IL requires {req_ratio}. {status}")

    # Print violations grouped by severity
    print("\n--- VIOLATIONS FOUND ---")
    critical = [v for v in violations if v.get("severity") == "CRITICAL"]
    high = [v for v in violations if v.get("severity") == "HIGH"]

    print(f"\n  CRITICAL ({len(critical)}):")
    for v in critical:
        time_str = f"[{v['time']}] " if "time" in v else ""
        room_str = f"{v['room']} - " if "room" in v else ""
        staff_str = f"{v['staff']} - " if "staff" in v else ""
        print(f"    {time_str}{room_str}{staff_str}{v['detail']}")

    print(f"\n  HIGH ({len(high)}):")
    for v in high:
        staff_str = f"{v['staff']} - " if "staff" in v else ""
        print(f"    {staff_str}{v['detail']}")

    # Licensing impact summary
    print("\n--- LICENSING IMPACT ---")
    print(f"  Total violations: {len(violations)}")
    print(f"  Critical (immediate license risk): {len(critical)}")
    print(f"  High (corrective action required): {len(high)}")
    if len(critical) > 0:
        print("\n  WARNING: Critical violations trigger mandatory state inspection.")
        print("  Remediation: Add float staff for break coverage, verify all credentials,")
        print("  ensure minimum 2 staff at open/close. Platform recommends schedule rebuild.")
    print("\n" + "=" * 70)
    # Platform scales: add state, add age brackets, re-run. Same engine, new rules.
