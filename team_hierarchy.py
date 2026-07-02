"""
ShiftGuard - Department/Team Hierarchy
Org > Site > Department > Team structure.
Each line manager sees and schedules only their team.
Coverage cascades: team first, then department, then site.
Fairness is measured within the team (peers compared to peers).
"""

from datetime import datetime, timedelta
from collections import defaultdict


class Organization:
    """Top-level organization with sites, departments, and teams."""

    def __init__(self, org_id, name, industry):
        self.org_id = org_id
        self.name = name
        self.industry = industry
        self.sites = {}
        self.all_employees = {}
        self.managers = {}

    def add_site(self, site_id, name, location=""):
        site = Site(site_id, name, location, self)
        self.sites[site_id] = site
        return site

    def get_site(self, site_id):
        return self.sites.get(site_id)

    def get_all_teams(self):
        teams = []
        for site in self.sites.values():
            for dept in site.departments.values():
                for team in dept.teams.values():
                    teams.append(team)
        return teams

    def get_employee_team(self, employee_id):
        """Find which team an employee belongs to."""
        for site in self.sites.values():
            for dept in site.departments.values():
                for team in dept.teams.values():
                    if employee_id in [m["id"] for m in team.members]:
                        return team
        return None

    def get_manager_scope(self, manager_id):
        """Get everything a manager can see/control."""
        scope = {
            "teams": [],
            "departments": [],
            "employees": [],
        }

        for site in self.sites.values():
            for dept in site.departments.values():
                if dept.manager_id == manager_id:
                    scope["departments"].append(dept)
                    for team in dept.teams.values():
                        scope["teams"].append(team)
                        scope["employees"].extend(team.members)
                else:
                    for team in dept.teams.values():
                        if team.manager_id == manager_id:
                            scope["teams"].append(team)
                            scope["employees"].extend(team.members)

        return scope


class Site:
    """Physical location (e.g., Metro General Hospital)."""

    def __init__(self, site_id, name, location, org):
        self.site_id = site_id
        self.name = name
        self.location = location
        self.org = org
        self.departments = {}

    def add_department(self, dept_id, name, manager_id=None):
        dept = Department(dept_id, name, manager_id, self)
        self.departments[dept_id] = dept
        return dept

    def get_department(self, dept_id):
        return self.departments.get(dept_id)


class Department:
    """Department within a site (e.g., Emergency Department)."""

    def __init__(self, dept_id, name, manager_id, site):
        self.dept_id = dept_id
        self.name = name
        self.manager_id = manager_id
        self.site = site
        self.teams = {}

    def add_team(self, team_id, name, manager_id=None):
        team = Team(team_id, name, manager_id, self)
        self.teams[team_id] = team
        return team

    def get_team(self, team_id):
        return self.teams.get(team_id)

    def get_all_members(self):
        members = []
        for team in self.teams.values():
            members.extend(team.members)
        return members


class Team:
    """Scheduling unit managed by one line manager."""

    def __init__(self, team_id, name, manager_id, department):
        self.team_id = team_id
        self.name = name
        self.manager_id = manager_id
        self.department = department
        self.members = []
        self.shift_pattern = None
        self.schedule = []

    def add_member(self, employee):
        """Add an employee to this team."""
        self.members.append(employee)

    def remove_member(self, employee_id):
        self.members = [m for m in self.members if m["id"] != employee_id]

    def get_member(self, employee_id):
        return next((m for m in self.members if m["id"] == employee_id), None)

    def get_member_names(self):
        return [m["name"] for m in self.members]

    def set_shift_pattern(self, pattern_type):
        self.shift_pattern = pattern_type

    def get_schedule_for_period(self, start_date, end_date):
        """Get this team's schedule for a date range."""
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        return [
            s for s in self.schedule
            if start_date <= datetime.strptime(s["date"], "%Y-%m-%d") <= end_date
        ]


def find_coverage_cascading(org, employee_id, date, shift_start, shift_end, role):
    """
    Find coverage by cascading through the hierarchy:
    1. Same team (most likely to be qualified and fair comparison)
    2. Same department, different team (cross-trained, same unit)
    3. Same site, different department (last resort, may need orientation)

    Returns candidates at each level with their source.
    """
    employee_team = org.get_employee_team(employee_id)
    if not employee_team:
        return {"error": "Employee not in any team"}

    dept = employee_team.department
    site = dept.site

    results = {
        "same_team": [],
        "same_department": [],
        "same_site": [],
    }

    # Level 1: Same team
    for member in employee_team.members:
        if member["id"] == employee_id:
            continue
        if _is_available(member, date, employee_team.schedule):
            results["same_team"].append({
                **member,
                "source": "same_team",
                "source_name": employee_team.name,
                "cross_training_needed": False,
            })

    # Level 2: Same department, other teams
    for team in dept.teams.values():
        if team.team_id == employee_team.team_id:
            continue
        for member in team.members:
            if _is_available(member, date, team.schedule):
                results["same_department"].append({
                    **member,
                    "source": "same_department",
                    "source_name": f"{team.name} ({dept.name})",
                    "cross_training_needed": member.get("role") != role,
                })

    # Level 3: Same site, other departments
    for other_dept in site.departments.values():
        if other_dept.dept_id == dept.dept_id:
            continue
        for team in other_dept.teams.values():
            for member in team.members:
                if member.get("role") == role and _is_available(member, date, team.schedule):
                    results["same_site"].append({
                        **member,
                        "source": "same_site",
                        "source_name": f"{team.name} ({other_dept.name})",
                        "cross_training_needed": True,
                        "orientation_needed": True,
                    })

    # Recommendation
    if results["same_team"]:
        rec = f"Found {len(results['same_team'])} candidate(s) within {employee_team.name}. Best option."
    elif results["same_department"]:
        rec = f"No one in same team available. {len(results['same_department'])} from other teams in {dept.name}."
    elif results["same_site"]:
        rec = f"No one in {dept.name} available. {len(results['same_site'])} from other departments (may need orientation)."
    else:
        rec = "No internal coverage available at any level. Consider VET from off-shift or agency."

    return {
        "absent_employee": employee_id,
        "date": date,
        "team": employee_team.name,
        "department": dept.name,
        "results": results,
        "total_candidates": sum(len(v) for v in results.values()),
        "recommendation": rec,
    }


def get_team_view(org, manager_id):
    """
    Get what a specific manager sees when they log in.
    Only their team(s), their employees, their schedule.
    """
    scope = org.get_manager_scope(manager_id)

    if not scope["teams"]:
        return {"error": f"Manager {manager_id} has no assigned teams"}

    view = {
        "manager_id": manager_id,
        "teams": [],
    }

    for team in scope["teams"]:
        team_view = {
            "team_id": team.team_id,
            "team_name": team.name,
            "department": team.department.name,
            "member_count": len(team.members),
            "members": [
                {"id": m["id"], "name": m["name"], "role": m.get("role", ""),
                 "seniority": m.get("seniority", 0)}
                for m in team.members
            ],
            "shift_pattern": team.shift_pattern,
            "schedule_count": len(team.schedule),
        }
        view["teams"].append(team_view)

    view["total_employees"] = len(scope["employees"])
    return view


def _is_available(member, date, team_schedule):
    """Check if a member is not already scheduled on this date."""
    return not any(
        s.get("employee_id") == member["id"] and s.get("date") == date
        for s in team_schedule
    )


# ============================================================
# DEMO: Healthcare Hospital Hierarchy
# ============================================================

def create_healthcare_hierarchy():
    """Create a realistic hospital hierarchy for demo."""
    org = Organization("ORG001", "Metro Health System", "healthcare")

    # Site
    hospital = org.add_site("SITE01", "Metro General Hospital", "Chicago, IL")

    # Emergency Department
    ed = hospital.add_department("ED", "Emergency Department", manager_id="MGR_ED")

    # Team: GME / Residency
    gme = ed.add_team("ED_GME", "ED Residency Program", manager_id="MGR_GME")
    gme.set_shift_pattern("healthcare_24_7")
    gme.add_member({"id": "H001", "name": "Dr. Sarah Chen", "role": "Senior Resident (PGY-3)", "seniority": 1})
    gme.add_member({"id": "H002", "name": "Dr. Marcus Williams", "role": "Senior Resident (PGY-4)", "seniority": 2})
    gme.add_member({"id": "H003", "name": "Dr. Priya Patel", "role": "Junior Resident (PGY-1)", "seniority": 3})

    # Team: Nursing
    nursing = ed.add_team("ED_NURSING", "ED Nursing", manager_id="MGR_NURSING")
    nursing.set_shift_pattern("healthcare_12hr")
    nursing.add_member({"id": "H004", "name": "Jessica Thompson, RN", "role": "Charge Nurse", "seniority": 1})
    nursing.add_member({"id": "H005", "name": "Maria Rodriguez, RN", "role": "Staff RN", "seniority": 2})
    nursing.add_member({"id": "H006", "name": "David Kim, RN", "role": "Staff RN", "seniority": 3})
    nursing.add_member({"id": "H007", "name": "Aisha Ali", "role": "CNA / Patient Care Tech", "seniority": 4})
    nursing.add_member({"id": "H008", "name": "Jake Morrison", "role": "CNA / Patient Care Tech", "seniority": 5})

    # Team: Allied Health
    allied = ed.add_team("ED_ALLIED", "ED Allied Health", manager_id="MGR_ALLIED")
    allied.set_shift_pattern("healthcare_24_7")
    allied.add_member({"id": "H009", "name": "Rosa Hernandez", "role": "Respiratory Therapist (RRT)", "seniority": 1})

    # ICU Department
    icu = hospital.add_department("ICU", "Intensive Care Unit", manager_id="MGR_ICU")

    icu_nursing = icu.add_team("ICU_NURSING", "ICU Nursing", manager_id="MGR_ICU_NURSING")
    icu_nursing.set_shift_pattern("healthcare_12hr")
    icu_nursing.add_member({"id": "IC01", "name": "Amanda Foster, RN", "role": "Charge Nurse", "seniority": 1})
    icu_nursing.add_member({"id": "IC02", "name": "Brian Park, RN", "role": "Staff RN", "seniority": 2})
    icu_nursing.add_member({"id": "IC03", "name": "Catherine Lee, RN", "role": "Staff RN", "seniority": 3})

    return org


def create_warehouse_hierarchy():
    """Create a warehouse/FC hierarchy."""
    org = Organization("ORG002", "Midwest Distribution Inc.", "warehouse")
    fc = org.add_site("SITE01", "CHI-FC-001 (Chicago Fulfillment Center)", "Chicago, IL")

    # Inbound
    inbound = fc.add_department("IB", "Inbound", manager_id="MGR_IB")

    ib_receive = inbound.add_team("IB_RECEIVE", "Receive / Dock", manager_id="MGR_IB_RCV")
    ib_receive.set_shift_pattern("warehouse_2shift")
    ib_receive.add_member({"id": "E004", "name": "Marcus Johnson", "role": "Stow", "seniority": 4})
    ib_receive.add_member({"id": "E007", "name": "Rosa Hernandez", "role": "Stow", "seniority": 7})

    ib_stow = inbound.add_team("IB_STOW", "Stow", manager_id="MGR_IB_STOW")
    ib_stow.set_shift_pattern("warehouse_2shift")
    ib_stow.add_member({"id": "E001", "name": "Sarah Martinez", "role": "Pick", "seniority": 1})
    ib_stow.add_member({"id": "E003", "name": "Aisha Patel", "role": "Pick", "seniority": 3})
    ib_stow.add_member({"id": "E005", "name": "Chen Wei", "role": "Pick", "seniority": 5})

    # Outbound
    outbound = fc.add_department("OB", "Outbound", manager_id="MGR_OB")

    ob_pick = outbound.add_team("OB_PICK", "Pick", manager_id="MGR_OB_PICK")
    ob_pick.set_shift_pattern("warehouse_2shift")
    ob_pick.add_member({"id": "E008", "name": "David Kim", "role": "Pick", "seniority": 8})
    ob_pick.add_member({"id": "E010", "name": "Jake Thompson", "role": "Pick", "seniority": 10})

    ob_pack = outbound.add_team("OB_PACK", "Pack / Ship", manager_id="MGR_OB_PACK")
    ob_pack.set_shift_pattern("warehouse_2shift")
    ob_pack.add_member({"id": "E002", "name": "James Wilson", "role": "Pack", "seniority": 2})
    ob_pack.add_member({"id": "E006", "name": "Tyler Brooks", "role": "Pack", "seniority": 6})
    ob_pack.add_member({"id": "E009", "name": "Fatima Ali", "role": "Ship", "seniority": 9})

    return org


def create_retail_hierarchy():
    """Create a retail store hierarchy."""
    org = Organization("ORG003", "Metro Retail Group", "retail")
    store = org.add_site("SITE01", "Store #4521 - Downtown Chicago", "Chicago, IL")

    # Sales Floor
    sales = store.add_department("SALES", "Sales Floor", manager_id="MGR_SALES")

    sales_team = sales.add_team("SALES_ASSOC", "Sales Associates", manager_id="MGR_SALES_ASSOC")
    sales_team.set_shift_pattern("retail_standard")
    sales_team.add_member({"id": "R002", "name": "Carlos Mendez", "role": "Sales Associate", "seniority": 2})
    sales_team.add_member({"id": "R003", "name": "Tanya Washington", "role": "Sales Associate", "seniority": 3})
    sales_team.add_member({"id": "R006", "name": "DeShawn Harris", "role": "Sales Associate", "seniority": 6})
    sales_team.add_member({"id": "R007", "name": "Emily Nguyen", "role": "Visual Merchandiser", "seniority": 7})

    # Front End
    frontend = store.add_department("FE", "Front End", manager_id="MGR_FE")

    cashiers = frontend.add_team("FE_CASHIERS", "Cashiers", manager_id="MGR_FE_CASH")
    cashiers.set_shift_pattern("retail_standard")
    cashiers.add_member({"id": "R004", "name": "Kevin O'Brien", "role": "Cashier", "seniority": 4})
    cashiers.add_member({"id": "R008", "name": "Jordan Riley", "role": "Cashier", "seniority": 8})

    # Stock / Receiving
    stock = store.add_department("STOCK", "Receiving & Stock", manager_id="MGR_STOCK")

    stock_team = stock.add_team("STOCK_TEAM", "Stock Associates", manager_id="MGR_STOCK_ASSOC")
    stock_team.set_shift_pattern("retail_standard")
    stock_team.add_member({"id": "R005", "name": "Lisa Chang", "role": "Stock Associate", "seniority": 5})

    # Store leadership
    leadership = store.add_department("MGMT", "Store Management", manager_id="MGR_STORE")
    leaders = leadership.add_team("MGMT_TEAM", "Leadership", manager_id="MGR_STORE")
    leaders.add_member({"id": "R001", "name": "Amanda Foster", "role": "Store Manager", "seniority": 1})

    return org


def create_hospitality_hierarchy():
    """Create a hospitality (restaurant/hotel) hierarchy."""
    org = Organization("ORG004", "Grand Plaza Hospitality Group", "hospitality")
    hotel = org.add_site("SITE01", "Grand Plaza Hotel - Chicago", "Chicago, IL")

    # Front of House (Restaurant)
    foh = hotel.add_department("FOH", "Front of House (Restaurant)", manager_id="MGR_FOH")

    servers = foh.add_team("FOH_SERVERS", "Servers & Bar", manager_id="MGR_FOH_SRV")
    servers.set_shift_pattern("retail_standard")
    servers.add_member({"id": "HO05", "name": "Sophie Laurent", "role": "Server", "seniority": 5})
    servers.add_member({"id": "HO06", "name": "Marcus Williams", "role": "Server", "seniority": 6})
    servers.add_member({"id": "HO07", "name": "Priya Sharma", "role": "Host/Hostess", "seniority": 7})
    servers.add_member({"id": "HO08", "name": "Carlos Mendez", "role": "Bartender", "seniority": 8})
    servers.add_member({"id": "HO09", "name": "Jake Morrison", "role": "Busser", "seniority": 9})

    # Back of House (Kitchen)
    boh = hotel.add_department("BOH", "Back of House (Kitchen)", manager_id="MGR_BOH")

    kitchen = boh.add_team("BOH_KITCHEN", "Kitchen Team", manager_id="MGR_BOH_CHEF")
    kitchen.set_shift_pattern("retail_standard")
    kitchen.add_member({"id": "HO01", "name": "Chef Marco Rivera", "role": "Executive Chef", "seniority": 1})
    kitchen.add_member({"id": "HO02", "name": "Ana Torres", "role": "Sous Chef", "seniority": 2})
    kitchen.add_member({"id": "HO03", "name": "DeShawn Mitchell", "role": "Line Cook", "seniority": 3})
    kitchen.add_member({"id": "HO04", "name": "Yuki Tanaka", "role": "Line Cook", "seniority": 4})
    kitchen.add_member({"id": "HO10", "name": "Emma Nguyen", "role": "Dishwasher", "seniority": 10})

    return org


def create_manufacturing_hierarchy():
    """Create a manufacturing plant hierarchy."""
    org = Organization("ORG005", "Midwest Manufacturing Corp.", "manufacturing")
    plant = org.add_site("SITE01", "Assembly Plant - Line 3", "Detroit, MI")

    # Production
    production = plant.add_department("PROD", "Production", manager_id="MGR_PROD")

    operators = production.add_team("PROD_OPS", "Machine Operators & Assembly", manager_id="MGR_PROD_OPS")
    operators.set_shift_pattern("warehouse_2shift")
    operators.add_member({"id": "MF02", "name": "Maria Kowalski", "role": "Machine Operator", "seniority": 2})
    operators.add_member({"id": "MF03", "name": "James Okafor", "role": "Machine Operator", "seniority": 3})
    operators.add_member({"id": "MF04", "name": "Tanya Reeves", "role": "Assembler", "seniority": 4})
    operators.add_member({"id": "MF06", "name": "Sarah Peterson", "role": "Material Handler", "seniority": 6})
    operators.add_member({"id": "MF09", "name": "Diego Ramirez", "role": "Assembler", "seniority": 9})
    operators.add_member({"id": "MF10", "name": "Kyle Brooks", "role": "Material Handler", "seniority": 10})

    leadership = production.add_team("PROD_LEAD", "Production Leadership", manager_id="MGR_PROD")
    leadership.add_member({"id": "MF01", "name": "Robert Chen", "role": "Production Supervisor", "seniority": 1})

    # Quality
    quality = plant.add_department("QA", "Quality", manager_id="MGR_QA")

    qa_team = quality.add_team("QA_INSPECT", "QC Inspectors", manager_id="MGR_QA_INSP")
    qa_team.add_member({"id": "MF05", "name": "Hassan Ali", "role": "QC Inspector", "seniority": 5})

    # Maintenance
    maintenance = plant.add_department("MAINT", "Maintenance", manager_id="MGR_MAINT")

    maint_team = maintenance.add_team("MAINT_TECHS", "Maintenance Technicians", manager_id="MGR_MAINT_TECH")
    maint_team.add_member({"id": "MF07", "name": "Viktor Petrov", "role": "Industrial Electrician", "seniority": 7})
    maint_team.add_member({"id": "MF08", "name": "Linda Zhang", "role": "PLC Technician", "seniority": 8})

    return org


def create_hierarchy_for_industry(industry_key):
    """Get the hierarchy for any industry."""
    if industry_key == "healthcare":
        return create_healthcare_hierarchy()
    elif industry_key == "warehouse":
        return create_warehouse_hierarchy()
    elif industry_key == "retail":
        return create_retail_hierarchy()
    elif industry_key == "hospitality":
        return create_hospitality_hierarchy()
    elif industry_key == "manufacturing":
        return create_manufacturing_hierarchy()
    return None


if __name__ == "__main__":
    org = create_healthcare_hierarchy()

    print("=" * 70)
    print("  TEAM HIERARCHY - MANAGER-SCOPED VIEWS")
    print("=" * 70)

    # Show the org structure
    print(f"\n  Organization: {org.name} ({org.industry})")
    for site in org.sites.values():
        print(f"\n  Site: {site.name}")
        for dept in site.departments.values():
            print(f"    Department: {dept.name} (Manager: {dept.manager_id})")
            for team in dept.teams.values():
                print(f"      Team: {team.name} (Manager: {team.manager_id})")
                for m in team.members:
                    print(f"        - {m['name']} ({m['role']})")

    # What does the Residency Program Director see?
    print(f"\n\n  MANAGER VIEW: Residency Program Director (MGR_GME)")
    print(f"  {'-'*50}")
    view = get_team_view(org, "MGR_GME")
    for team in view["teams"]:
        print(f"  Team: {team['team_name']} ({team['department']})")
        print(f"  Members ({team['member_count']}):")
        for m in team["members"]:
            print(f"    {m['name']} - {m['role']}")

    # What does the Nurse Manager see?
    print(f"\n\n  MANAGER VIEW: ED Nurse Manager (MGR_NURSING)")
    print(f"  {'-'*50}")
    view = get_team_view(org, "MGR_NURSING")
    for team in view["teams"]:
        print(f"  Team: {team['team_name']} ({team['department']})")
        print(f"  Members ({team['member_count']}):")
        for m in team["members"]:
            print(f"    {m['name']} - {m['role']}")

    # What does the ED Director see? (department level - ALL teams)
    print(f"\n\n  MANAGER VIEW: ED Director (MGR_ED)")
    print(f"  {'-'*50}")
    view = get_team_view(org, "MGR_ED")
    print(f"  Total employees: {view['total_employees']}")
    for team in view["teams"]:
        print(f"  Team: {team['team_name']} - {team['member_count']} members")

    # Cascading coverage search
    print(f"\n\n  CASCADING COVERAGE: Dr. Chen calls out")
    print(f"  {'-'*50}")
    result = find_coverage_cascading(org, "H001", "2026-07-09", "07:00", "19:00", "Senior Resident (PGY-3)")
    print(f"  Team: {result['team']}")
    print(f"  Department: {result['department']}")
    print(f"  Same team candidates: {len(result['results']['same_team'])}")
    for c in result["results"]["same_team"]:
        print(f"    - {c['name']} ({c['role']})")
    print(f"  Same department: {len(result['results']['same_department'])}")
    for c in result["results"]["same_department"]:
        print(f"    - {c['name']} ({c['role']}) [from {c['source_name']}] {'(cross-training needed)' if c['cross_training_needed'] else ''}")
    print(f"  Same site: {len(result['results']['same_site'])}")
    print(f"  Recommendation: {result['recommendation']}")
