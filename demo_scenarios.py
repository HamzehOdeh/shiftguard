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
        "jurisdiction": "California",
        "role_categories": {
            "Graduate Medical Education (GME)": ["Attending Physician", "Fellow", "Senior Resident (PGY-3+)", "Junior Resident (PGY-1/PGY-2)"],
            "Nursing Services": ["Nurse Practitioner (NP)", "Charge Nurse", "Staff RN", "LPN/LVN", "CNA / Patient Care Tech"],
            "Allied Health": ["Respiratory Therapist (RRT)", "Radiology Tech", "Lab Tech (MLS)", "Phlebotomist", "Surgical Tech", "Pharmacy Tech"],
            "Support Staff": ["Health Unit Coordinator", "Patient Transporter", "EVS", "Food & Nutrition"],
        },
    },
    "warehouse": {
        "name": "Warehouse / Logistics",
        "subtitle": "Distribution Center / FC",
        "facility": "CHI-FC-001 (Chicago Fulfillment Center)",
        "jurisdiction": "Chicago",
        "shift_code_format": "[D/N][Schedule Group][#]-[Start Time]-[Dept]",
        "shift_code_legend": {
            "D/N": "Day or Night",
            "A": "Front Half (Sun-Wed)",
            "B": "Back Half (Wed-Sat)",
            "C": "Front Half Nights",
            "L": "Back Half Nights",
            "0700": "7:00 AM start",
            "1800": "6:00 PM start",
            "IB": "Inbound",
            "OB": "Outbound",
            "ICQA": "Inventory Control & Quality",
        },
        "role_categories": {
            "Inbound (IB)": ["Receiver", "Stower", "Decant", "IB Problem Solver"],
            "Outbound (OB)": ["Picker", "Packer (Singles)", "Packer (AFE/Multi)", "Shipper", "Slam Operator", "Rebin"],
            "ICQA": ["Cycle Counter", "Amnesty", "Damage Processing"],
            "Support / Indirect": ["Process Assistant (PA)", "Learning Ambassador", "WHS (Safety)", "Amnesty Responder"],
            "Maintenance (RME)": ["RME Tech", "Controls Systems Tech", "Maintenance Planner"],
        },
    },
    "retail": {
        "name": "Retail",
        "subtitle": "Store Operations",
        "facility": "Store #4521 - Downtown Chicago",
        "jurisdiction": "Chicago",
        "role_categories": {
            "Store Leadership": ["Store Manager", "Assistant Manager", "Shift Lead / Key Holder"],
            "Sales Floor": ["Sales Associate", "Department Lead", "Visual Merchandiser"],
            "Front End": ["Head Cashier", "Cashier", "Customer Service", "Greeter"],
            "Receiving / Stock": ["Receiving Lead", "Stock Associate", "Inventory Specialist"],
            "Loss Prevention": ["LP Manager", "Asset Protection Associate"],
        },
    },
    "hospitality": {
        "name": "Hospitality",
        "subtitle": "Hotel / Restaurant",
        "facility": "Grand Plaza Hotel - Chicago",
        "jurisdiction": "Chicago",
        "role_categories": {
            "Front Office": ["Front Office Manager", "Front Desk Agent", "Night Auditor", "Concierge", "Bell Staff"],
            "Housekeeping": ["Executive Housekeeper", "Housekeeping Supervisor", "Room Attendant", "Laundry"],
            "Food & Beverage": ["F&B Manager", "Server", "Bartender", "Host/Hostess", "Busser"],
            "Kitchen (BOH)": ["Executive Chef", "Sous Chef", "Line Cook", "Prep Cook", "Dishwasher"],
            "Engineering": ["Chief Engineer", "Maintenance Tech", "Groundskeeper"],
        },
    },
    "manufacturing": {
        "name": "Manufacturing",
        "subtitle": "Production / Assembly",
        "facility": "Midwest Assembly Plant - Line 3",
        "jurisdiction": "Oregon",
        "role_categories": {
            "Production": ["Production Supervisor", "Line Lead", "Machine Operator", "Assembler", "Material Handler"],
            "Quality": ["Quality Engineer", "QC Inspector", "Metrology Tech"],
            "Maintenance": ["Industrial Electrician", "Industrial Mechanic", "PLC Tech", "HVAC Tech"],
            "EHS (Safety)": ["EHS Manager", "Safety Specialist"],
            "Supply Chain": ["Production Planner", "Shipping & Receiving", "Inventory Control"],
        },
    },
}


def generate_healthcare_demo():
    """Generate a healthcare (hospital) demo scenario."""
    week_start = datetime(2026, 7, 7)
    schedule_posted = datetime(2026, 7, 4)

    employees = [
        {"id": "H001", "name": "Dr. Sarah Chen", "seniority": 1, "role": "Senior Resident (PGY-3)", "category": "GME", "is_minor": False, "hire_date": "2024-07-01", "hourly_rate": 35.00},
        {"id": "H002", "name": "Dr. Marcus Williams", "seniority": 2, "role": "Senior Resident (PGY-4)", "category": "GME", "is_minor": False, "hire_date": "2024-07-01", "hourly_rate": 35.00},
        {"id": "H003", "name": "Dr. Priya Patel", "seniority": 3, "role": "Junior Resident (PGY-1)", "category": "GME", "is_minor": False, "hire_date": "2025-07-01", "hourly_rate": 33.00},
        {"id": "H004", "name": "Jessica Thompson, RN", "seniority": 4, "role": "Charge Nurse", "category": "Nursing", "is_minor": False, "hire_date": "2020-03-15", "hourly_rate": 42.00},
        {"id": "H005", "name": "Maria Rodriguez, RN", "seniority": 5, "role": "Staff RN", "category": "Nursing", "is_minor": False, "hire_date": "2021-06-01", "hourly_rate": 40.00},
        {"id": "H006", "name": "David Kim, RN", "seniority": 6, "role": "Staff RN", "category": "Nursing", "is_minor": False, "hire_date": "2022-01-10", "hourly_rate": 38.00},
        {"id": "H007", "name": "Aisha Ali", "seniority": 7, "role": "CNA / Patient Care Tech", "category": "Nursing", "is_minor": False, "hire_date": "2023-04-01", "hourly_rate": 22.00},
        {"id": "H008", "name": "Jake Morrison", "seniority": 8, "role": "CNA / Patient Care Tech", "category": "Nursing", "is_minor": False, "hire_date": "2023-09-15", "hourly_rate": 21.00},
        {"id": "H009", "name": "Rosa Hernandez", "seniority": 9, "role": "Respiratory Therapist (RRT)", "category": "Allied Health", "is_minor": False, "hire_date": "2022-08-01", "hourly_rate": 28.00},
        {"id": "H010", "name": "Tyler Brooks", "seniority": 10, "role": "CNA / Patient Care Tech", "category": "Nursing", "is_minor": True, "hire_date": "2026-05-15", "hourly_rate": 18.00},
    ]

    shifts = []

    # Dr. Chen - CLOPENING VIOLATION (night shift then morning)
    shifts.append({"employee_id": "H001", "name": "Dr. Sarah Chen", "date": "2026-07-06", "start": "19:00", "end": "07:00", "role": "Senior Resident (PGY-3)", "shift_type": "Night"})
    shifts.append({"employee_id": "H001", "name": "Dr. Sarah Chen", "date": "2026-07-07", "start": "07:00", "end": "19:00", "role": "Senior Resident (PGY-3)", "shift_type": "Day"})
    shifts.append({"employee_id": "H001", "name": "Dr. Sarah Chen", "date": "2026-07-08", "start": "07:00", "end": "19:00", "role": "Senior Resident (PGY-3)", "shift_type": "Day"})
    shifts.append({"employee_id": "H001", "name": "Dr. Sarah Chen", "date": "2026-07-09", "start": "07:00", "end": "19:00", "role": "Senior Resident (PGY-3)", "shift_type": "Day"})

    # Dr. Williams - EXCESSIVE HOURS (ACGME 80hr/week concern)
    shifts.append({"employee_id": "H002", "name": "Dr. Marcus Williams", "date": "2026-07-07", "start": "06:00", "end": "18:00", "role": "Senior Resident (PGY-4)", "shift_type": "Day"})
    shifts.append({"employee_id": "H002", "name": "Dr. Marcus Williams", "date": "2026-07-08", "start": "06:00", "end": "18:00", "role": "Senior Resident (PGY-4)", "shift_type": "Day"})
    shifts.append({"employee_id": "H002", "name": "Dr. Marcus Williams", "date": "2026-07-09", "start": "06:00", "end": "18:00", "role": "Senior Resident (PGY-4)", "shift_type": "Day"})
    shifts.append({"employee_id": "H002", "name": "Dr. Marcus Williams", "date": "2026-07-10", "start": "06:00", "end": "18:00", "role": "Senior Resident (PGY-4)", "shift_type": "Day"})
    shifts.append({"employee_id": "H002", "name": "Dr. Marcus Williams", "date": "2026-07-11", "start": "06:00", "end": "18:00", "role": "Senior Resident (PGY-4)", "shift_type": "Day"})
    shifts.append({"employee_id": "H002", "name": "Dr. Marcus Williams", "date": "2026-07-12", "start": "06:00", "end": "16:00", "role": "Senior Resident (PGY-4)", "shift_type": "Day"})

    # Dr. Patel - 8 CONSECUTIVE DAYS
    for i in range(8):
        d = (datetime(2026, 7, 1) + timedelta(days=i)).strftime("%Y-%m-%d")
        shifts.append({"employee_id": "H003", "name": "Dr. Priya Patel", "date": d, "start": "07:00", "end": "19:00", "role": "Junior Resident (PGY-1)", "shift_type": "Day"})

    # RN Jessica - 5 consecutive NIGHT shifts
    for i in range(5):
        d = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
        shifts.append({"employee_id": "H004", "name": "Jessica Thompson, RN", "date": d, "start": "19:00", "end": "07:00", "role": "Staff RN", "shift_type": "Night"})

    # RN Maria - normal schedule
    for i in range(4):
        d = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
        shifts.append({"employee_id": "H005", "name": "Maria Rodriguez, RN", "date": d, "start": "07:00", "end": "19:00", "role": "Staff RN", "shift_type": "Day"})

    # RN David - normal
    for i in range(4):
        d = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
        shifts.append({"employee_id": "H006", "name": "David Kim, RN", "date": d, "start": "07:00", "end": "15:30", "role": "Staff RN", "shift_type": "Day"})

    # CNA Aisha - short shift violation
    shifts.append({"employee_id": "H007", "name": "Aisha Ali, CNA", "date": "2026-07-07", "start": "11:00", "end": "14:00", "role": "CNA / Patient Care Tech", "shift_type": "Short"})
    for i in range(1, 5):
        d = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
        shifts.append({"employee_id": "H007", "name": "Aisha Ali, CNA", "date": d, "start": "07:00", "end": "15:30", "role": "CNA / Patient Care Tech", "shift_type": "Day"})

    # Tyler (minor CNA) - night shift violation
    shifts.append({"employee_id": "H010", "name": "Tyler Brooks", "date": "2026-07-07", "start": "15:00", "end": "23:30", "role": "CNA / Patient Care Tech", "shift_type": "Evening"})
    shifts.append({"employee_id": "H010", "name": "Tyler Brooks", "date": "2026-07-08", "start": "07:00", "end": "15:00", "role": "CNA / Patient Care Tech", "shift_type": "Day"})

    # Normal shifts for others
    for i in range(5):
        d = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
        shifts.append({"employee_id": "H008", "name": "Jake Morrison, CNA", "date": d, "start": "07:00", "end": "15:30", "role": "CNA / Patient Care Tech", "shift_type": "Day"})
        shifts.append({"employee_id": "H009", "name": "Rosa Hernandez, Tech", "date": d, "start": "07:00", "end": "15:30", "role": "Respiratory Therapist (RRT)", "shift_type": "Day"})

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
