"""
Workforce Compliance AI - Sample Schedule Generator
Creates a realistic warehouse shift schedule with intentional violations for demo.
"""

import csv
from datetime import datetime, timedelta

EMPLOYEES = [
    {"id": "E001", "name": "Sarah Martinez", "seniority": 1, "role": "Pick", "is_minor": False, "hire_date": "2019-03-15", "hourly_rate": 22.50, "certifications": ["forklift", "hazmat"]},
    {"id": "E002", "name": "James Wilson", "seniority": 2, "role": "Pack", "is_minor": False, "hire_date": "2020-01-10", "hourly_rate": 21.00, "certifications": ["forklift"]},
    {"id": "E003", "name": "Aisha Patel", "seniority": 3, "role": "Pick", "is_minor": False, "hire_date": "2020-08-22", "hourly_rate": 20.50, "certifications": []},
    {"id": "E004", "name": "Marcus Johnson", "seniority": 4, "role": "Stow", "is_minor": False, "hire_date": "2021-02-01", "hourly_rate": 20.00, "certifications": ["forklift"]},
    {"id": "E005", "name": "Chen Wei", "seniority": 5, "role": "Pick", "is_minor": False, "hire_date": "2021-06-15", "hourly_rate": 19.50, "certifications": []},
    {"id": "E006", "name": "Tyler Brooks", "seniority": 6, "role": "Pack", "is_minor": True, "hire_date": "2025-06-01", "hourly_rate": 16.00, "certifications": []},
    {"id": "E007", "name": "Rosa Hernandez", "seniority": 7, "role": "Stow", "is_minor": False, "hire_date": "2022-03-10", "hourly_rate": 19.00, "certifications": []},
    {"id": "E008", "name": "David Kim", "seniority": 8, "role": "Pick", "is_minor": False, "hire_date": "2022-09-20", "hourly_rate": 19.00, "certifications": ["forklift"], "preferences": {"vet_available_days": ["Mon", "Tue", "Thu"], "preferred_shift_type": "night", "notes": "Available for extra day shifts Mon/Tue/Thu"}},
    {"id": "E009", "name": "Fatima Ali", "seniority": 9, "role": "Ship", "is_minor": False, "hire_date": "2023-01-05", "hourly_rate": 18.50, "certifications": [], "preferences": {"vet_available_days": ["Mon", "Wed", "Fri"], "notes": "Happy to pick up extra shifts"}},
    {"id": "E010", "name": "Jake Thompson", "seniority": 10, "role": "Pick", "is_minor": False, "hire_date": "2023-11-15", "hourly_rate": 18.00, "certifications": [], "preferences": {"vet_available_days": ["Mon", "Sat"], "notes": "Available Mondays and Saturdays for VET"}},
]

# Historical fairness data (simulated — in production comes from database)
EMPLOYEE_HISTORY = {
    "E001": {
        "coverage_requests_received": 5, "coverage_requests_accepted": 4,
        "holidays_worked_this_year": 3, "holidays_off_this_year": 1,
        "weekend_shifts_this_month": 3, "night_shifts_this_month": 2,
        "voluntary_covers": 3, "forced_covers": 1, "team_avg_requests": 3,
        "worked_Christmas Day_last_year": True, "worked_Thanksgiving Day_last_year": False,
        "priority_holidays": [
            {"dates": "2026-12-21 to 2026-12-27", "priority": 1, "reason": "Family visit"},
            {"dates": "2026-09-07 to 2026-09-13", "priority": 2, "reason": "Vacation"},
        ],
    },
    "E002": {
        "coverage_requests_received": 2, "coverage_requests_accepted": 2,
        "holidays_worked_this_year": 1, "holidays_off_this_year": 3,
        "weekend_shifts_this_month": 1, "night_shifts_this_month": 0,
        "voluntary_covers": 2, "forced_covers": 0, "team_avg_requests": 3,
        "worked_Christmas Day_last_year": False, "worked_Thanksgiving Day_last_year": True,
        "priority_holidays": [
            {"dates": "2026-11-23 to 2026-11-29", "priority": 1, "reason": "Thanksgiving family"},
            {"dates": "2026-05-18 to 2026-05-24", "priority": 2, "reason": "Anniversary trip"},
        ],
    },
    "E003": {
        "coverage_requests_received": 1, "coverage_requests_accepted": 1,
        "holidays_worked_this_year": 0, "holidays_off_this_year": 3,
        "weekend_shifts_this_month": 0, "night_shifts_this_month": 0,
        "voluntary_covers": 1, "forced_covers": 0, "team_avg_requests": 3,
        "worked_Christmas Day_last_year": False, "worked_Thanksgiving Day_last_year": False,
        "priority_holidays": [
            {"dates": "2026-03-16 to 2026-03-22", "priority": 1, "reason": "Spring break with kids"},
            {"dates": "2026-12-24 to 2026-12-31", "priority": 2, "reason": "Holiday"},
        ],
    },
    "E005": {
        "coverage_requests_received": 4, "coverage_requests_accepted": 3,
        "holidays_worked_this_year": 2, "holidays_off_this_year": 2,
        "weekend_shifts_this_month": 2, "night_shifts_this_month": 3,
        "voluntary_covers": 1, "forced_covers": 2, "team_avg_requests": 3,
        "worked_Christmas Day_last_year": True, "worked_Thanksgiving Day_last_year": True,
        "priority_holidays": [
            {"dates": "2026-01-28 to 2026-02-03", "priority": 1, "reason": "Lunar New Year"},
            {"dates": "2026-08-10 to 2026-08-16", "priority": 2, "reason": "Summer vacation"},
        ],
    },
    "E008": {
        "coverage_requests_received": 3, "coverage_requests_accepted": 2,
        "holidays_worked_this_year": 1, "holidays_off_this_year": 2,
        "weekend_shifts_this_month": 1, "night_shifts_this_month": 1,
        "voluntary_covers": 2, "forced_covers": 0, "team_avg_requests": 3,
        "worked_Christmas Day_last_year": False, "worked_Thanksgiving Day_last_year": True,
        "priority_holidays": [
            {"dates": "2026-09-28 to 2026-10-04", "priority": 1, "reason": "Chuseok"},
            {"dates": "2026-12-21 to 2026-12-27", "priority": 2, "reason": "Christmas"},
        ],
    },
    "E010": {
        "coverage_requests_received": 0, "coverage_requests_accepted": 0,
        "holidays_worked_this_year": 0, "holidays_off_this_year": 2,
        "weekend_shifts_this_month": 0, "night_shifts_this_month": 0,
        "voluntary_covers": 0, "forced_covers": 0, "team_avg_requests": 3,
        "worked_Christmas Day_last_year": False, "worked_Thanksgiving Day_last_year": False,
        "priority_holidays": [
            {"dates": "2026-07-20 to 2026-07-26", "priority": 1, "reason": "Summer trip"},
            {"dates": "2026-12-24 to 2026-12-31", "priority": 2, "reason": "Holiday"},
        ],
    },
}

def generate_schedule():
    """
    Generate a 1-week schedule with intentional compliance violations:
    - Clopening violation (Sarah: closes Sun, opens Mon)
    - 7 consecutive days (Marcus)
    - Minor scheduled past 10pm (Tyler)
    - Short shift under 4 hours (Rosa - CBA violation)
    - Over 60 hours in a week (James)
    - Schedule posted only 3 days before (all - notice violation)
    """
    # Week of July 7-13, 2026 (Mon-Sun)
    # Schedule posted on July 4 (only 3 days notice - violates 14-day and CBA 5-day rules)
    week_start = datetime(2026, 7, 7)
    schedule_posted = datetime(2026, 7, 4)

    shifts = []

    # --- Sarah Martinez (E001) - CLOPENING VIOLATION ---
    # Works closing shift Sunday July 6 (prior week), then opening Monday July 7
    shifts.append({"employee_id": "E001", "name": "Sarah Martinez", "date": "2026-07-06", "start": "14:00", "end": "22:30", "role": "Pick", "shift_type": "Close"})
    shifts.append({"employee_id": "E001", "name": "Sarah Martinez", "date": "2026-07-07", "start": "06:00", "end": "14:30", "role": "Pick", "shift_type": "Open"})  # Only 7.5 hrs between shifts!
    shifts.append({"employee_id": "E001", "name": "Sarah Martinez", "date": "2026-07-08", "start": "06:00", "end": "14:30", "role": "Pick", "shift_type": "Day"})
    shifts.append({"employee_id": "E001", "name": "Sarah Martinez", "date": "2026-07-09", "start": "06:00", "end": "14:30", "role": "Pick", "shift_type": "Day"})
    shifts.append({"employee_id": "E001", "name": "Sarah Martinez", "date": "2026-07-10", "start": "06:00", "end": "14:30", "role": "Pick", "shift_type": "Day"})
    shifts.append({"employee_id": "E001", "name": "Sarah Martinez", "date": "2026-07-11", "start": "06:00", "end": "14:30", "role": "Pick", "shift_type": "Day"})

    # --- James Wilson (E002) - EXCESSIVE HOURS (62.5 hrs) ---
    shifts.append({"employee_id": "E002", "name": "James Wilson", "date": "2026-07-07", "start": "06:00", "end": "16:30", "role": "Pack", "shift_type": "Day"})  # 10.5
    shifts.append({"employee_id": "E002", "name": "James Wilson", "date": "2026-07-08", "start": "06:00", "end": "16:30", "role": "Pack", "shift_type": "Day"})  # 10.5
    shifts.append({"employee_id": "E002", "name": "James Wilson", "date": "2026-07-09", "start": "06:00", "end": "16:30", "role": "Pack", "shift_type": "Day"})  # 10.5
    shifts.append({"employee_id": "E002", "name": "James Wilson", "date": "2026-07-10", "start": "06:00", "end": "16:30", "role": "Pack", "shift_type": "Day"})  # 10.5
    shifts.append({"employee_id": "E002", "name": "James Wilson", "date": "2026-07-11", "start": "06:00", "end": "16:30", "role": "Pack", "shift_type": "Day"})  # 10.5
    shifts.append({"employee_id": "E002", "name": "James Wilson", "date": "2026-07-12", "start": "06:00", "end": "16:30", "role": "Pack", "shift_type": "Day"})  # 10.5 = 63 total

    # --- Marcus Johnson (E004) - 7 CONSECUTIVE DAYS ---
    # Already worked July 1-6 (prior week Mon-Sun), now scheduled July 7
    shifts.append({"employee_id": "E004", "name": "Marcus Johnson", "date": "2026-07-01", "start": "07:00", "end": "15:30", "role": "Stow", "shift_type": "Day"})
    shifts.append({"employee_id": "E004", "name": "Marcus Johnson", "date": "2026-07-02", "start": "07:00", "end": "15:30", "role": "Stow", "shift_type": "Day"})
    shifts.append({"employee_id": "E004", "name": "Marcus Johnson", "date": "2026-07-03", "start": "07:00", "end": "15:30", "role": "Stow", "shift_type": "Day"})
    shifts.append({"employee_id": "E004", "name": "Marcus Johnson", "date": "2026-07-04", "start": "07:00", "end": "15:30", "role": "Stow", "shift_type": "Day"})
    shifts.append({"employee_id": "E004", "name": "Marcus Johnson", "date": "2026-07-05", "start": "07:00", "end": "15:30", "role": "Stow", "shift_type": "Day"})
    shifts.append({"employee_id": "E004", "name": "Marcus Johnson", "date": "2026-07-06", "start": "07:00", "end": "15:30", "role": "Stow", "shift_type": "Day"})
    shifts.append({"employee_id": "E004", "name": "Marcus Johnson", "date": "2026-07-07", "start": "07:00", "end": "15:30", "role": "Stow", "shift_type": "Day"})  # 7th consecutive day!
    shifts.append({"employee_id": "E004", "name": "Marcus Johnson", "date": "2026-07-08", "start": "07:00", "end": "15:30", "role": "Stow", "shift_type": "Day"})  # 8th!

    # --- Tyler Brooks (E006) - MINOR WORKING PAST 10PM ---
    shifts.append({"employee_id": "E006", "name": "Tyler Brooks", "date": "2026-07-07", "start": "16:00", "end": "22:30", "role": "Pack", "shift_type": "Evening"})  # Past 10pm!
    shifts.append({"employee_id": "E006", "name": "Tyler Brooks", "date": "2026-07-08", "start": "14:00", "end": "20:00", "role": "Pack", "shift_type": "Evening"})
    shifts.append({"employee_id": "E006", "name": "Tyler Brooks", "date": "2026-07-09", "start": "14:00", "end": "20:00", "role": "Pack", "shift_type": "Evening"})

    # --- Rosa Hernandez (E007) - SHORT SHIFT (3 hrs - CBA violation) ---
    shifts.append({"employee_id": "E007", "name": "Rosa Hernandez", "date": "2026-07-07", "start": "10:00", "end": "13:00", "role": "Stow", "shift_type": "Short"})  # Only 3 hours!
    shifts.append({"employee_id": "E007", "name": "Rosa Hernandez", "date": "2026-07-08", "start": "07:00", "end": "15:30", "role": "Stow", "shift_type": "Day"})
    shifts.append({"employee_id": "E007", "name": "Rosa Hernandez", "date": "2026-07-09", "start": "07:00", "end": "15:30", "role": "Stow", "shift_type": "Day"})
    shifts.append({"employee_id": "E007", "name": "Rosa Hernandez", "date": "2026-07-10", "start": "07:00", "end": "15:30", "role": "Stow", "shift_type": "Day"})

    # --- Chen Wei (E005) - NIGHT SHIFT BLOCK (5 consecutive nights - violation) ---
    shifts.append({"employee_id": "E005", "name": "Chen Wei", "date": "2026-07-07", "start": "22:00", "end": "06:30", "role": "Pick", "shift_type": "Night"})
    shifts.append({"employee_id": "E005", "name": "Chen Wei", "date": "2026-07-08", "start": "22:00", "end": "06:30", "role": "Pick", "shift_type": "Night"})
    shifts.append({"employee_id": "E005", "name": "Chen Wei", "date": "2026-07-09", "start": "22:00", "end": "06:30", "role": "Pick", "shift_type": "Night"})
    shifts.append({"employee_id": "E005", "name": "Chen Wei", "date": "2026-07-10", "start": "22:00", "end": "06:30", "role": "Pick", "shift_type": "Night"})
    shifts.append({"employee_id": "E005", "name": "Chen Wei", "date": "2026-07-11", "start": "22:00", "end": "06:30", "role": "Pick", "shift_type": "Night"})  # 5th consecutive night!

    # --- Normal schedules for others ---
    for emp_id, name, role in [("E003", "Aisha Patel", "Pick"),
                                ("E008", "David Kim", "Pick"), ("E009", "Fatima Ali", "Ship"),
                                ("E010", "Jake Thompson", "Pick")]:
        for day_offset in range(5):  # Mon-Fri normal
            date = (week_start + timedelta(days=day_offset)).strftime("%Y-%m-%d")
            shifts.append({"employee_id": emp_id, "name": name, "date": date,
                          "start": "07:00", "end": "15:30", "role": role, "shift_type": "Day"})

    return {
        "schedule_posted_date": schedule_posted.strftime("%Y-%m-%d"),
        "week_start": week_start.strftime("%Y-%m-%d"),
        "week_end": (week_start + timedelta(days=6)).strftime("%Y-%m-%d"),
        "facility": "CHI-WH-001 (Chicago Warehouse)",
        "shifts": shifts
    }


def save_schedule_csv(schedule, filepath):
    """Save schedule to CSV."""
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["employee_id", "name", "date", "start", "end", "role", "shift_type"])
        writer.writeheader()
        writer.writerows(schedule["shifts"])
    print(f"Schedule saved to {filepath} ({len(schedule['shifts'])} shifts)")


if __name__ == "__main__":
    schedule = generate_schedule()
    print(f"Generated schedule for {schedule['facility']}")
    print(f"Week: {schedule['week_start']} to {schedule['week_end']}")
    print(f"Posted: {schedule['schedule_posted_date']}")
    print(f"Total shifts: {len(schedule['shifts'])}")
    print(f"\nEmployees: {len(EMPLOYEES)}")

    save_schedule_csv(schedule, r"C:\Users\hodeh\Documents\Support Call\workforce-compliance-ai\sample_schedule.csv")
