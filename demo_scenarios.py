"""
Workforce Compliance AI - Multi-Industry Demo Scenarios
Provides realistic sample data for different industries.
"""

from datetime import datetime, timedelta


INDUSTRY_OPTIONS = {
    "healthcare": {
        "name": "Healthcare",
        "subtitle": "Hospital / ED / Nursing",
        "facility": "Metro General Hospital - Emergency Department",
        "roles": ["RN", "CNA", "Resident", "Tech", "Admin"],
        "jurisdiction": "California",
    },
    "warehouse": {
        "name": "Warehouse / Logistics",
        "subtitle": "Distribution Center / FC",
        "facility": "CHI-WH-001 (Chicago Distribution Center)",
        "roles": ["Pick", "Pack", "Stow", "Ship", "Receive"],
        "jurisdiction": "Chicago",
    },
    "retail": {
        "name": "Retail",
        "subtitle": "Store Operations",
        "facility": "Store #4521 - Downtown Chicago",
        "roles": ["Sales Associate", "Cashier", "Stock", "Supervisor", "Visual"],
        "jurisdiction": "Chicago",
    },
    "hospitality": {
        "name": "Hospitality",
        "subtitle": "Hotel / Restaurant",
        "facility": "Grand Plaza Hotel - Chicago",
        "roles": ["Front Desk", "Housekeeping", "Kitchen", "Server", "Maintenance"],
        "jurisdiction": "Chicago",
    },
    "manufacturing": {
        "name": "Manufacturing",
        "subtitle": "Production / Assembly",
        "facility": "Midwest Assembly Plant - Line 3",
        "roles": ["Operator", "Technician", "QC Inspector", "Material Handler", "Lead"],
        "jurisdiction": "Oregon",
    },
}


def generate_healthcare_demo():
    """Generate a healthcare (hospital) demo scenario."""
    week_start = datetime(2026, 7, 7)
    schedule_posted = datetime(2026, 7, 4)

    employees = [
        {"id": "H001", "name": "Dr. Sarah Chen", "seniority": 1, "role": "Resident", "is_minor": False, "hire_date": "2024-07-01", "hourly_rate": 35.00},
        {"id": "H002", "name": "Dr. Marcus Williams", "seniority": 2, "role": "Resident", "is_minor": False, "hire_date": "2024-07-01", "hourly_rate": 35.00},
        {"id": "H003", "name": "Dr. Priya Patel", "seniority": 3, "role": "Resident", "is_minor": False, "hire_date": "2025-07-01", "hourly_rate": 33.00},
        {"id": "H004", "name": "Jessica Thompson, RN", "seniority": 4, "role": "RN", "is_minor": False, "hire_date": "2020-03-15", "hourly_rate": 42.00},
        {"id": "H005", "name": "Maria Rodriguez, RN", "seniority": 5, "role": "RN", "is_minor": False, "hire_date": "2021-06-01", "hourly_rate": 40.00},
        {"id": "H006", "name": "David Kim, RN", "seniority": 6, "role": "RN", "is_minor": False, "hire_date": "2022-01-10", "hourly_rate": 38.00},
        {"id": "H007", "name": "Aisha Ali, CNA", "seniority": 7, "role": "CNA", "is_minor": False, "hire_date": "2023-04-01", "hourly_rate": 22.00},
        {"id": "H008", "name": "Jake Morrison, CNA", "seniority": 8, "role": "CNA", "is_minor": False, "hire_date": "2023-09-15", "hourly_rate": 21.00},
        {"id": "H009", "name": "Rosa Hernandez, Tech", "seniority": 9, "role": "Tech", "is_minor": False, "hire_date": "2022-08-01", "hourly_rate": 28.00},
        {"id": "H010", "name": "Tyler Brooks", "seniority": 10, "role": "CNA", "is_minor": True, "hire_date": "2026-05-15", "hourly_rate": 18.00},
    ]

    shifts = []

    # Dr. Chen - CLOPENING VIOLATION (night shift then morning)
    shifts.append({"employee_id": "H001", "name": "Dr. Sarah Chen", "date": "2026-07-06", "start": "19:00", "end": "07:00", "role": "Resident", "shift_type": "Night"})
    shifts.append({"employee_id": "H001", "name": "Dr. Sarah Chen", "date": "2026-07-07", "start": "07:00", "end": "19:00", "role": "Resident", "shift_type": "Day"})
    shifts.append({"employee_id": "H001", "name": "Dr. Sarah Chen", "date": "2026-07-08", "start": "07:00", "end": "19:00", "role": "Resident", "shift_type": "Day"})
    shifts.append({"employee_id": "H001", "name": "Dr. Sarah Chen", "date": "2026-07-09", "start": "07:00", "end": "19:00", "role": "Resident", "shift_type": "Day"})

    # Dr. Williams - EXCESSIVE HOURS (ACGME 80hr/week concern)
    shifts.append({"employee_id": "H002", "name": "Dr. Marcus Williams", "date": "2026-07-07", "start": "06:00", "end": "18:00", "role": "Resident", "shift_type": "Day"})
    shifts.append({"employee_id": "H002", "name": "Dr. Marcus Williams", "date": "2026-07-08", "start": "06:00", "end": "18:00", "role": "Resident", "shift_type": "Day"})
    shifts.append({"employee_id": "H002", "name": "Dr. Marcus Williams", "date": "2026-07-09", "start": "06:00", "end": "18:00", "role": "Resident", "shift_type": "Day"})
    shifts.append({"employee_id": "H002", "name": "Dr. Marcus Williams", "date": "2026-07-10", "start": "06:00", "end": "18:00", "role": "Resident", "shift_type": "Day"})
    shifts.append({"employee_id": "H002", "name": "Dr. Marcus Williams", "date": "2026-07-11", "start": "06:00", "end": "18:00", "role": "Resident", "shift_type": "Day"})
    shifts.append({"employee_id": "H002", "name": "Dr. Marcus Williams", "date": "2026-07-12", "start": "06:00", "end": "16:00", "role": "Resident", "shift_type": "Day"})

    # Dr. Patel - 8 CONSECUTIVE DAYS
    for i in range(8):
        d = (datetime(2026, 7, 1) + timedelta(days=i)).strftime("%Y-%m-%d")
        shifts.append({"employee_id": "H003", "name": "Dr. Priya Patel", "date": d, "start": "07:00", "end": "19:00", "role": "Resident", "shift_type": "Day"})

    # RN Jessica - 5 consecutive NIGHT shifts
    for i in range(5):
        d = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
        shifts.append({"employee_id": "H004", "name": "Jessica Thompson, RN", "date": d, "start": "19:00", "end": "07:00", "role": "RN", "shift_type": "Night"})

    # RN Maria - normal schedule
    for i in range(4):
        d = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
        shifts.append({"employee_id": "H005", "name": "Maria Rodriguez, RN", "date": d, "start": "07:00", "end": "19:00", "role": "RN", "shift_type": "Day"})

    # RN David - normal
    for i in range(4):
        d = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
        shifts.append({"employee_id": "H006", "name": "David Kim, RN", "date": d, "start": "07:00", "end": "15:30", "role": "RN", "shift_type": "Day"})

    # CNA Aisha - short shift violation
    shifts.append({"employee_id": "H007", "name": "Aisha Ali, CNA", "date": "2026-07-07", "start": "11:00", "end": "14:00", "role": "CNA", "shift_type": "Short"})
    for i in range(1, 5):
        d = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
        shifts.append({"employee_id": "H007", "name": "Aisha Ali, CNA", "date": d, "start": "07:00", "end": "15:30", "role": "CNA", "shift_type": "Day"})

    # Tyler (minor CNA) - night shift violation
    shifts.append({"employee_id": "H010", "name": "Tyler Brooks", "date": "2026-07-07", "start": "15:00", "end": "23:30", "role": "CNA", "shift_type": "Evening"})
    shifts.append({"employee_id": "H010", "name": "Tyler Brooks", "date": "2026-07-08", "start": "07:00", "end": "15:00", "role": "CNA", "shift_type": "Day"})

    # Normal shifts for others
    for i in range(5):
        d = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
        shifts.append({"employee_id": "H008", "name": "Jake Morrison, CNA", "date": d, "start": "07:00", "end": "15:30", "role": "CNA", "shift_type": "Day"})
        shifts.append({"employee_id": "H009", "name": "Rosa Hernandez, Tech", "date": d, "start": "07:00", "end": "15:30", "role": "Tech", "shift_type": "Day"})

    return {
        "employees": employees,
        "schedule": {
            "schedule_posted_date": schedule_posted.strftime("%Y-%m-%d"),
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": (week_start + timedelta(days=6)).strftime("%Y-%m-%d"),
            "facility": "Metro General Hospital - Emergency Department",
            "shifts": shifts,
        },
    }


def generate_retail_demo():
    """Generate a retail store demo scenario."""
    week_start = datetime(2026, 7, 7)
    schedule_posted = datetime(2026, 7, 4)

    employees = [
        {"id": "R001", "name": "Amanda Foster", "seniority": 1, "role": "Supervisor", "is_minor": False, "hire_date": "2019-05-10", "hourly_rate": 26.00},
        {"id": "R002", "name": "Carlos Mendez", "seniority": 2, "role": "Sales Associate", "is_minor": False, "hire_date": "2020-08-01", "hourly_rate": 18.00},
        {"id": "R003", "name": "Tanya Washington", "seniority": 3, "role": "Sales Associate", "is_minor": False, "hire_date": "2021-03-15", "hourly_rate": 17.50},
        {"id": "R004", "name": "Kevin O'Brien", "seniority": 4, "role": "Cashier", "is_minor": False, "hire_date": "2022-01-10", "hourly_rate": 16.50},
        {"id": "R005", "name": "Lisa Chang", "seniority": 5, "role": "Stock", "is_minor": False, "hire_date": "2022-06-01", "hourly_rate": 17.00},
        {"id": "R006", "name": "DeShawn Harris", "seniority": 6, "role": "Sales Associate", "is_minor": False, "hire_date": "2023-02-20", "hourly_rate": 16.50},
        {"id": "R007", "name": "Emily Nguyen", "seniority": 7, "role": "Visual", "is_minor": False, "hire_date": "2023-09-01", "hourly_rate": 19.00},
        {"id": "R008", "name": "Jordan Riley", "seniority": 8, "role": "Cashier", "is_minor": True, "hire_date": "2026-05-01", "hourly_rate": 15.00},
    ]

    shifts = []

    # Amanda (Supervisor) - Clopening: closes then opens
    shifts.append({"employee_id": "R001", "name": "Amanda Foster", "date": "2026-07-06", "start": "14:00", "end": "22:30", "role": "Supervisor", "shift_type": "Close"})
    shifts.append({"employee_id": "R001", "name": "Amanda Foster", "date": "2026-07-07", "start": "05:30", "end": "14:00", "role": "Supervisor", "shift_type": "Open"})
    for i in range(1, 5):
        d = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
        shifts.append({"employee_id": "R001", "name": "Amanda Foster", "date": d, "start": "09:00", "end": "17:30", "role": "Supervisor", "shift_type": "Day"})

    # Carlos - 7 consecutive days
    for i in range(7):
        d = (datetime(2026, 7, 1) + timedelta(days=i)).strftime("%Y-%m-%d")
        shifts.append({"employee_id": "R002", "name": "Carlos Mendez", "date": d, "start": "10:00", "end": "18:30", "role": "Sales Associate", "shift_type": "Day"})
    shifts.append({"employee_id": "R002", "name": "Carlos Mendez", "date": "2026-07-08", "start": "10:00", "end": "18:30", "role": "Sales Associate", "shift_type": "Day"})

    # Jordan (minor) - scheduled past 10pm
    shifts.append({"employee_id": "R008", "name": "Jordan Riley", "date": "2026-07-07", "start": "16:00", "end": "22:30", "role": "Cashier", "shift_type": "Evening"})
    shifts.append({"employee_id": "R008", "name": "Jordan Riley", "date": "2026-07-08", "start": "14:00", "end": "20:00", "role": "Cashier", "shift_type": "Evening"})

    # Kevin - short shift (3hr)
    shifts.append({"employee_id": "R004", "name": "Kevin O'Brien", "date": "2026-07-07", "start": "11:00", "end": "14:00", "role": "Cashier", "shift_type": "Short"})
    for i in range(1, 5):
        d = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
        shifts.append({"employee_id": "R004", "name": "Kevin O'Brien", "date": d, "start": "09:00", "end": "17:30", "role": "Cashier", "shift_type": "Day"})

    # Normal schedules
    for emp_id, name, role in [("R003", "Tanya Washington", "Sales Associate"),
                                ("R005", "Lisa Chang", "Stock"),
                                ("R006", "DeShawn Harris", "Sales Associate"),
                                ("R007", "Emily Nguyen", "Visual")]:
        for i in range(5):
            d = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
            shifts.append({"employee_id": emp_id, "name": name, "date": d, "start": "09:00", "end": "17:30", "role": role, "shift_type": "Day"})

    return {
        "employees": employees,
        "schedule": {
            "schedule_posted_date": schedule_posted.strftime("%Y-%m-%d"),
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": (week_start + timedelta(days=6)).strftime("%Y-%m-%d"),
            "facility": "Store #4521 - Downtown Chicago",
            "shifts": shifts,
        },
    }


def generate_demo_for_industry(industry_key):
    """Get the right demo data for the selected industry."""
    if industry_key == "healthcare":
        return generate_healthcare_demo()
    elif industry_key == "retail":
        return generate_retail_demo()
    else:
        # Default to warehouse (existing demo)
        from sample_schedule import generate_schedule, EMPLOYEES
        return {
            "employees": EMPLOYEES,
            "schedule": generate_schedule(),
        }
