"""
ShiftGuard - Epic FHIR R4 Integration
Reads schedule, practitioner, and location data from Epic EHR via FHIR API.
Uses SMART on FHIR OAuth2 for authentication.

Epic App Orchard: Register ShiftGuard as a backend application.
Scopes needed: Schedule.read, Practitioner.read, Location.read, PractitionerRole.read

Setup:
1. Register app in Epic App Orchard (sandbox first, then production)
2. Get client_id and generate RSA keypair for JWT assertion
3. Set environment variables: EPIC_BASE_URL, EPIC_CLIENT_ID, EPIC_PRIVATE_KEY_PATH
4. Hospital IT grants backend system access

Epic FHIR Docs: https://fhir.epic.com/
SMART Backend Services: https://hl7.org/fhir/smart-app-launch/backend-services.html

Required pip: requests, cryptography (for JWT signing)
"""

import os
import json
import time
from datetime import datetime, timedelta

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


# Epic FHIR resource mappings
FHIR_RESOURCES = {
    "Schedule": "/Schedule",
    "Slot": "/Slot",
    "Practitioner": "/Practitioner",
    "PractitionerRole": "/PractitionerRole",
    "Location": "/Location",
    "Organization": "/Organization",
}


class EpicFHIRConnector:
    """
    Connects to Epic's FHIR R4 API to read scheduling data.
    Uses SMART Backend Services (system-to-system, no user login needed).
    """

    def __init__(self, base_url=None, client_id=None, private_key_path=None):
        self.base_url = (base_url or os.getenv("EPIC_BASE_URL", "")).rstrip("/")
        self.client_id = client_id or os.getenv("EPIC_CLIENT_ID")
        self.private_key_path = private_key_path or os.getenv("EPIC_PRIVATE_KEY_PATH")
        self.access_token = None
        self.token_expires = None
        self.last_sync = None

    def connect(self):
        """
        Authenticate via SMART Backend Services (JWT assertion flow).
        1. Create signed JWT with client_id
        2. Exchange JWT for access token at Epic's token endpoint
        """
        if not REQUESTS_AVAILABLE:
            return {"success": False, "error": "requests library not installed"}

        if not self.base_url or not self.client_id:
            return {
                "success": False,
                "error": "Missing Epic credentials. Set EPIC_BASE_URL and EPIC_CLIENT_ID.",
                "setup_guide": {
                    "step_1": "Register in Epic App Orchard (https://appmarket.epic.com/)",
                    "step_2": "Request backend system access (Schedule.read, Practitioner.read)",
                    "step_3": "Generate RSA keypair, upload public key to App Orchard",
                    "step_4": "Set EPIC_BASE_URL (e.g., https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4)",
                    "step_5": "Set EPIC_CLIENT_ID and EPIC_PRIVATE_KEY_PATH",
                },
            }

        try:
            # Step 1: Create JWT assertion
            jwt_token = self._create_jwt_assertion()
            if not jwt_token:
                return {"success": False, "error": "Failed to create JWT (check private key)"}

            # Step 2: Exchange for access token
            token_url = f"{self.base_url.split('/api/')[0]}/oauth2/token"
            response = requests.post(token_url, data={
                "grant_type": "client_credentials",
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": jwt_token,
            })

            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.token_expires = datetime.now() + timedelta(seconds=data.get("expires_in", 300))
                return {"success": True, "message": "Authenticated with Epic FHIR API"}
            else:
                return {"success": False, "error": f"Token exchange failed: {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def pull_practitioners(self, department=None):
        """
        Pull practitioner (staff) data from Epic.
        Maps to ShiftGuard employee format.
        """
        params = {"_count": 100}
        if department:
            params["_has:PractitionerRole:practitioner:organization"] = department

        data = self._fhir_get("/Practitioner", params)
        if not data:
            return {"success": False, "error": "Failed to fetch practitioners"}

        practitioners = []
        for entry in data.get("entry", []):
            resource = entry.get("resource", {})
            name_parts = resource.get("name", [{}])[0]
            full_name = f"{name_parts.get('prefix', [''])[0]} {name_parts.get('given', [''])[0]} {name_parts.get('family', '')}".strip()

            qualifications = [q.get("code", {}).get("text", "")
                             for q in resource.get("qualification", [])]

            practitioners.append({
                "id": resource.get("id", ""),
                "name": full_name,
                "npi": next((id["value"] for id in resource.get("identifier", [])
                            if id.get("system") == "http://hl7.org/fhir/sid/us-npi"), ""),
                "qualifications": qualifications,
                "active": resource.get("active", True),
            })

        return {"success": True, "practitioners": practitioners, "count": len(practitioners)}

    def pull_schedule(self, start_date, end_date, practitioner_ids=None, location_id=None):
        """
        Pull schedule slots from Epic for a date range.
        Returns data in ShiftGuard format.
        """
        params = {
            "date": f"ge{start_date}",
            "_count": 200,
        }
        if location_id:
            params["actor"] = f"Location/{location_id}"

        # Get Schedule resources
        schedules_data = self._fhir_get("/Schedule", params)
        if not schedules_data:
            return {"success": False, "error": "Failed to fetch schedules"}

        # Get Slots for each schedule
        shifts = []
        for entry in schedules_data.get("entry", []):
            schedule_resource = entry.get("resource", {})
            schedule_id = schedule_resource.get("id", "")

            # Get practitioner from actor reference
            practitioner_ref = ""
            for actor in schedule_resource.get("actor", []):
                ref = actor.get("reference", "")
                if "Practitioner" in ref:
                    practitioner_ref = ref
                    break

            # Get slots for this schedule
            slots = self._fhir_get("/Slot", {
                "schedule": f"Schedule/{schedule_id}",
                "start": f"ge{start_date}",
                "end": f"le{end_date}",
                "status": "busy",
            })

            if slots:
                for slot_entry in slots.get("entry", []):
                    slot = slot_entry.get("resource", {})
                    start_time = slot.get("start", "")
                    end_time = slot.get("end", "")

                    shifts.append({
                        "employee_id": practitioner_ref.split("/")[-1] if practitioner_ref else "",
                        "name": actor.get("display", practitioner_ref),
                        "date": start_time[:10] if start_time else "",
                        "start": start_time[11:16] if len(start_time) > 16 else "",
                        "end": end_time[11:16] if len(end_time) > 16 else "",
                        "role": schedule_resource.get("serviceType", [{}])[0].get("text", ""),
                        "shift_type": self._classify_shift_type(start_time),
                        "fhir_schedule_id": schedule_id,
                    })

        schedule = {
            "schedule_posted_date": datetime.now().strftime("%Y-%m-%d"),
            "week_start": start_date,
            "week_end": end_date,
            "facility": f"Epic FHIR Import",
            "shifts": shifts,
            "source": "epic_fhir",
            "synced_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        self.last_sync = datetime.now()
        return {
            "success": True,
            "schedule": schedule,
            "stats": {
                "total_shifts": len(shifts),
                "total_practitioners": len(set(s["employee_id"] for s in shifts)),
                "date_range": f"{start_date} to {end_date}",
            },
        }

    def pull_locations(self):
        """Pull hospital locations/units from Epic."""
        data = self._fhir_get("/Location", {"_count": 100, "status": "active"})
        if not data:
            return {"success": False, "error": "Failed to fetch locations"}

        locations = []
        for entry in data.get("entry", []):
            resource = entry.get("resource", {})
            locations.append({
                "id": resource.get("id", ""),
                "name": resource.get("name", ""),
                "type": resource.get("type", [{}])[0].get("text", ""),
                "status": resource.get("status", ""),
            })

        return {"success": True, "locations": locations, "count": len(locations)}

    def get_sync_status(self):
        """Get connection status."""
        return {
            "connected": self.access_token is not None,
            "base_url": self.base_url,
            "client_id": self.client_id,
            "last_sync": self.last_sync.strftime("%Y-%m-%d %H:%M") if self.last_sync else None,
            "token_valid": bool(self.token_expires and datetime.now() < self.token_expires),
            "fhir_version": "R4",
        }

    def _fhir_get(self, resource_path, params=None):
        """Make authenticated FHIR GET request."""
        if not self.access_token:
            conn = self.connect()
            if not conn.get("success"):
                return None

        try:
            url = f"{self.base_url}{resource_path}"
            response = requests.get(url, params=params, headers={
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/fhir+json",
            })

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                # Token expired, retry
                self.connect()
                response = requests.get(url, params=params, headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/fhir+json",
                })
                if response.status_code == 200:
                    return response.json()
            return None
        except Exception:
            return None

    def _create_jwt_assertion(self):
        """Create signed JWT for SMART Backend Services auth."""
        try:
            import jwt as pyjwt
            from cryptography.hazmat.primitives import serialization

            if not self.private_key_path or not os.path.exists(self.private_key_path):
                return None

            with open(self.private_key_path, "rb") as f:
                private_key = serialization.load_pem_private_key(f.read(), password=None)

            now = int(time.time())
            token_url = f"{self.base_url.split('/api/')[0]}/oauth2/token"

            payload = {
                "iss": self.client_id,
                "sub": self.client_id,
                "aud": token_url,
                "jti": f"shiftguard-{now}",
                "iat": now,
                "exp": now + 300,
            }

            return pyjwt.encode(payload, private_key, algorithm="RS384")
        except ImportError:
            return None
        except Exception:
            return None

    def _classify_shift_type(self, start_time):
        """Classify shift as Day/Evening/Night based on start time."""
        if not start_time or len(start_time) < 16:
            return "Day"
        hour = int(start_time[11:13])
        if hour < 12:
            return "Day"
        elif hour < 19:
            return "Evening"
        return "Night"


def create_epic_connector(base_url=None, client_id=None):
    """Factory function."""
    return EpicFHIRConnector(base_url=base_url, client_id=client_id)
