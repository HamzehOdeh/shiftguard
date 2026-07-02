"""
ShiftGuard - Dynamic Organization Setup
Customers define their own structure, departments, teams, and roles.
Nothing is hardcoded. The system adapts to ANY organization shape.
"""

from datetime import datetime
from team_hierarchy import Organization, Site, Department, Team


class OrgSetupWizard:
    """
    Guide a customer through setting up their organization.
    Everything is dynamic — they define their own labels, structure, and roles.
    """

    def __init__(self):
        self.org = None
        self.custom_roles = []
        self.custom_departments = []
        self.setup_complete = False

    def create_organization(self, name, industry=None):
        """Step 1: Create the organization."""
        org_id = f"ORG-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.org = Organization(org_id, name, industry or "general")
        return {"org_id": org_id, "name": name, "industry": industry}

    def add_site(self, site_id, name, location=""):
        """Step 2: Add a physical site/location."""
        if not self.org:
            return {"error": "Create organization first"}
        site = self.org.add_site(site_id, name, location)
        return {"site_id": site_id, "name": name, "location": location}

    def add_department(self, site_id, name, manager_name=None):
        """Step 3: Add a department (customer defines the name)."""
        site = self.org.get_site(site_id)
        if not site:
            return {"error": f"Site {site_id} not found"}
        dept_id = f"DEPT-{name.upper().replace(' ', '_')[:10]}"
        manager_id = f"MGR-{dept_id}" if manager_name else None
        dept = site.add_department(dept_id, name, manager_id)
        self.custom_departments.append({"id": dept_id, "name": name, "site": site_id})
        return {"dept_id": dept_id, "name": name, "manager_id": manager_id}

    def add_team(self, site_id, dept_id, name, manager_name=None):
        """Step 4: Add a team within a department (customer defines the name)."""
        site = self.org.get_site(site_id)
        if not site:
            return {"error": f"Site {site_id} not found"}
        dept = site.get_department(dept_id)
        if not dept:
            return {"error": f"Department {dept_id} not found"}
        team_id = f"TEAM-{name.upper().replace(' ', '_')[:12]}"
        manager_id = f"MGR-{team_id}" if manager_name else None
        team = dept.add_team(team_id, name, manager_id)
        return {"team_id": team_id, "name": name, "dept": dept_id, "manager_id": manager_id}

    def add_role(self, role_name, department=None, requires_certification=False,
                 can_cross_train_to=None):
        """
        Step 5: Define a custom role (customer uses their own terminology).
        e.g., "Room Service Attendant", "Patient Care Associate", "Picker Level 2"
        """
        role = {
            "name": role_name,
            "department": department,
            "requires_certification": requires_certification,
            "can_cross_train_to": can_cross_train_to or [],
            "created_at": datetime.now().strftime("%Y-%m-%d"),
        }
        self.custom_roles.append(role)
        return role

    def add_employee(self, site_id, dept_id, team_id, employee_data):
        """
        Step 6: Add an employee to a team.
        employee_data: {"id", "name", "role", "seniority", "hire_date", ...}
        Role can be ANY string — whatever the customer calls it.
        """
        site = self.org.get_site(site_id)
        if not site:
            return {"error": f"Site {site_id} not found"}
        dept = site.get_department(dept_id)
        if not dept:
            return {"error": f"Department {dept_id} not found"}
        team = dept.get_team(team_id)
        if not team:
            return {"error": f"Team {team_id} not found"}

        team.add_member(employee_data)
        return {"success": True, "employee": employee_data["name"], "team": team.name}

    def bulk_import_employees(self, site_id, dept_id, team_id, employees):
        """Import a list of employees into a team at once."""
        results = []
        for emp in employees:
            result = self.add_employee(site_id, dept_id, team_id, emp)
            results.append(result)
        return {"imported": len(results), "results": results}

    def finalize_setup(self):
        """Mark setup as complete and validate."""
        if not self.org:
            return {"error": "No organization created"}
        if not self.org.sites:
            return {"error": "No sites added"}

        all_teams = self.org.get_all_teams()
        total_employees = sum(len(t.members) for t in all_teams)

        if total_employees == 0:
            return {"error": "No employees added to any team"}

        self.setup_complete = True
        return {
            "status": "COMPLETE",
            "organization": self.org.name,
            "sites": len(self.org.sites),
            "departments": len(self.custom_departments),
            "teams": len(all_teams),
            "total_employees": total_employees,
            "custom_roles": len(self.custom_roles),
            "message": f"Setup complete! {total_employees} employees across {len(all_teams)} teams.",
        }

    def get_org(self):
        return self.org

    def get_setup_summary(self):
        """Get current setup state for display."""
        if not self.org:
            return {"status": "NOT_STARTED"}

        all_teams = self.org.get_all_teams()
        summary = {
            "organization": self.org.name,
            "industry": self.org.industry,
            "sites": [],
        }

        for site in self.org.sites.values():
            site_info = {"name": site.name, "departments": []}
            for dept in site.departments.values():
                dept_info = {"name": dept.name, "teams": []}
                for team in dept.teams.values():
                    dept_info["teams"].append({
                        "name": team.name,
                        "members": len(team.members),
                        "roles": list(set(m.get("role", "") for m in team.members)),
                    })
                site_info["departments"].append(dept_info)
            summary["sites"].append(site_info)

        return summary


# ============================================================
# DEMO: Customer setting up their own hotel
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("  DYNAMIC ORG SETUP - Customer Defines Everything")
    print("  Example: Boutique Hotel with custom role names")
    print("=" * 70)

    wizard = OrgSetupWizard()

    # Step 1: Organization
    wizard.create_organization("The Langham Chicago", industry="hospitality")
    print("\n  Created: The Langham Chicago")

    # Step 2: Site
    wizard.add_site("SITE-001", "The Langham Chicago - Main Building", "Chicago, IL")
    print("  Added site: Main Building")

    # Step 3: Departments (CUSTOMER'S terminology)
    wizard.add_department("SITE-001", "Guest Services", manager_name="Diana Walsh")
    wizard.add_department("SITE-001", "Housekeeping & Laundry", manager_name="Maria Santos")
    wizard.add_department("SITE-001", "Food & Beverage", manager_name="Chef Laurent")
    wizard.add_department("SITE-001", "Engineering", manager_name="Tom Brooks")
    print("  Added 4 departments")

    # Step 4: Teams (using returned dept IDs)
    t1 = wizard.add_team("SITE-001", "DEPT-GUEST_SERV", "Front Desk Agents", "Sam Chen")
    wizard.add_team("SITE-001", "DEPT-GUEST_SERV", "Concierge & Bell", "Robert Kim")
    t3 = wizard.add_team("SITE-001", "DEPT-HOUSEKEEPI", "Room Attendants", "Ana Rivera")
    wizard.add_team("SITE-001", "DEPT-HOUSEKEEPI", "Public Area & Laundry", "Jake Morrison")
    wizard.add_team("SITE-001", "DEPT-FOOD_&_BEV", "Restaurant Service", "Sophie Laurent")
    t6 = wizard.add_team("SITE-001", "DEPT-FOOD_&_BEV", "Room Service", "Carlos Mendez")
    wizard.add_team("SITE-001", "DEPT-FOOD_&_BEV", "Kitchen Brigade", "Chef Laurent")
    wizard.add_team("SITE-001", "DEPT-ENGINEERIN", "Maintenance Team", "Tom Brooks")
    print("  Added 8 teams")

    # Step 5: Custom roles (THEIR terminology, not ours)
    wizard.add_role("Guest Service Agent")
    wizard.add_role("Night Auditor")
    wizard.add_role("Bell Captain")
    wizard.add_role("Room Attendant")
    wizard.add_role("Houseperson")
    wizard.add_role("Laundry Attendant")
    wizard.add_role("Turndown Specialist")
    wizard.add_role("Room Service Captain")
    wizard.add_role("Room Service Runner")
    wizard.add_role("Commis Chef")
    wizard.add_role("Chef de Partie")
    wizard.add_role("Maintenance Engineer")
    print("  Defined 12 custom roles")

    # Step 6: Add employees (using returned team IDs)
    fd_team = t1["team_id"]
    rm_team = t3["team_id"]
    rs_team = t6["team_id"]

    wizard.add_employee("SITE-001", "DEPT-GUEST_SERV", fd_team, {
        "id": "EMP001", "name": "Ashley Park", "role": "Guest Service Agent", "seniority": 1
    })
    wizard.add_employee("SITE-001", "DEPT-GUEST_SERV", fd_team, {
        "id": "EMP002", "name": "Marcus Green", "role": "Guest Service Agent", "seniority": 2
    })
    wizard.add_employee("SITE-001", "DEPT-GUEST_SERV", fd_team, {
        "id": "EMP003", "name": "Lin Wei", "role": "Night Auditor", "seniority": 3
    })
    wizard.add_employee("SITE-001", "DEPT-HOUSEKEEPI", rm_team, {
        "id": "EMP004", "name": "Fatima Hassan", "role": "Room Attendant", "seniority": 1
    })
    wizard.add_employee("SITE-001", "DEPT-HOUSEKEEPI", rm_team, {
        "id": "EMP005", "name": "Rosa Gutierrez", "role": "Room Attendant", "seniority": 2
    })
    wizard.add_employee("SITE-001", "DEPT-HOUSEKEEPI", rm_team, {
        "id": "EMP006", "name": "Priya Nair", "role": "Turndown Specialist", "seniority": 3
    })
    wizard.add_employee("SITE-001", "DEPT-FOOD_&_BEV", rs_team, {
        "id": "EMP007", "name": "Derek Thompson", "role": "Room Service Captain", "seniority": 1
    })
    wizard.add_employee("SITE-001", "DEPT-FOOD_&_BEV", rs_team, {
        "id": "EMP008", "name": "Yuki Sato", "role": "Room Service Runner", "seniority": 2
    })
    print("  Added 8 employees")

    # Finalize
    print("\n  SETUP SUMMARY:")
    result = wizard.finalize_setup()
    print(f"    Status: {result['status']}")
    print(f"    Organization: {result['organization']}")
    print(f"    Teams: {result['teams']}")
    print(f"    Employees: {result['total_employees']}")
    print(f"    Custom Roles: {result['custom_roles']}")

    # Show the structure
    print("\n  RESULTING HIERARCHY:")
    summary = wizard.get_setup_summary()
    for site in summary["sites"]:
        print(f"\n  {site['name']}:")
        for dept in site["departments"]:
            print(f"    {dept['name']}:")
            for team in dept["teams"]:
                roles = ", ".join(team["roles"]) if team["roles"] else "No members"
                print(f"      {team['name']} ({team['members']} members) - Roles: {roles}")

    print("\n  KEY POINT: All role names are defined by the CUSTOMER.")
    print("  ShiftGuard doesn't care if you call it 'Turndown Specialist'")
    print("  or 'Evening Housekeeping' — the scheduling logic works the same.")
