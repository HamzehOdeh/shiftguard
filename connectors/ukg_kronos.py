"""
ShiftGuard - UKG/Kronos WFM Connector
Pulls schedule, timecard, and employee data from UKG Pro Workforce Management.
Most hospitals and large employers use UKG (formerly Kronos).

Setup:
1. Customer provides: UKG API base URL, client ID, client secret, tenant ID
2. OAuth2 client credentials flow for authentication
3. Pulls schedules nightly or on-demand via webhook

Required pip: requests
UKG API Docs: https://developer.ukg.com/

Environment Variables:
  UKG_BASE_URL: https://{tenant}.ultipro.com or https://{tenant}.kronos.net
  UKG_CLIENT_ID: OAuth2 client ID
  UKG_CLIENT_SECRET: OAuth2 client secret
  UKG_TENANT_ID: Customer's UKG tenant identifier
"""

import os
import json
from datetime import datetime, timedelta

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = [1, 3, 10]
RATE_LIMIT_CALLS_PER_MINUTE = 60


class UKGConnector:
    """
    Connects to UKG Pro WFM (formerly Kronos Workforce Ready / Dimensions).
    Pulls schedules, employees, and timecards.
    Includes retry with exponential backoff and rate limiting.
    """

    def __init__(self, base_url=None, client_id=None, client_secret=None, tenant_id=None):
        self.base_url = (base_url or os.getenv("UKG_BASE_URL", "")).rstrip("/")
        self.client_id = client_id or os.getenv("UKG_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("UKG_CLIENT_SECRET")
        self.tenant_id = tenant_id or os.getenv("UKG_TENANT_ID")
        self.access_token = None
        self.token_expires = None
        self.last_sync = None
        self._call_timestamps = []

    def connect(self):
        """Authenticate via OAuth2 client credentials."""
        if not REQUESTS_AVAILABLE:
            return {"success": False, "error": "requests library not installed. Run: pip install requests"}

        if not self.base_url or not self.client_id or not self.client_secret:
            return {
                "success": False,
                "error": "Missing UKG credentials. Set UKG_BASE_URL, UKG_CLIENT_ID, UKG_CLIENT_SECRET env vars.",
                "setup_guide": {
                    "step_1": "Get API credentials from UKG admin console",
                    "step_2": "Set environment variables or pass to constructor",
                    "step_3": "Ensure schedule read permissions are granted",
                },
            }

        try:
            token_url = f"{self.base_url}/api/authentication/token"
            response = requests.post(token_url, data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }, headers={"Content-Type": "application/x-www-form-urlencoded"})

            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.token_expires = datetime.now() + timedelta(seconds=data.get("expires_in", 3600))
                return {"success": True, "message": "Authenticated with UKG API"}
            else:
                return {"success": False, "error": f"Auth failed: {response.status_code} — {response.text[:200]}"}

        except requests.exceptions.ConnectionError:
            return {"success": False, "error": f"Cannot connect to {self.base_url}. Check URL and network."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_headers(self):
        """Get auth headers, refreshing token if needed."""
        if not self.access_token or (self.token_expires and datetime.now() > self.token_expires):
            self.connect()
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _rate_limit_check(self):
        """Enforce rate limiting (60 calls/minute)."""
        import time
        now = time.time()
        self._call_timestamps = [t for t in self._call_timestamps if now - t < 60]
        if len(self._call_timestamps) >= RATE_LIMIT_CALLS_PER_MINUTE:
            wait = 60 - (now - self._call_timestamps[0])
            if wait > 0:
                time.sleep(wait)
        self._call_timestamps.append(now)

    def _request_with_retry(self, method, url, **kwargs):
        """Make HTTP request with retry and exponential backoff."""
        import time
        self._rate_limit_check()

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                response = getattr(requests, method)(url, **kwargs)

                if response.status_code == 429:
                    # Rate limited by UKG — wait and retry
                    retry_after = int(response.headers.get("Retry-After", RETRY_BACKOFF_SECONDS[attempt]))
                    time.sleep(retry_after)
                    continue

                if response.status_code >= 500:
                    # Server error — retry with backoff
                    time.sleep(RETRY_BACKOFF_SECONDS[attempt])
                    continue

                return response

            except requests.exceptions.ConnectionError as e:
                last_error = e
                time.sleep(RETRY_BACKOFF_SECONDS[attempt])
            except requests.exceptions.Timeout as e:
                last_error = e
                time.sleep(RETRY_BACKOFF_SECONDS[attempt])

        # All retries exhausted
        raise Exception(f"Failed after {MAX_RETRIES} retries. Last error: {last_error}")

    def pull_employees(self):
        """Pull employee roster from UKG."""
        try:
            url = f"{self.base_url}/api/personnel/v1/employees"
            response = requests.get(url, headers=self._get_headers(), params={
                "status": "active",
                "pageSize": 500,
            })

            if response.status_code != 200:
                return {"success": False, "error": f"Failed: {response.status_code}"}

            ukg_employees = response.json().get("employees", response.json())

            employees = []
            for emp in ukg_employees:
                employees.append({
                    "id": emp.get("employeeId", emp.get("personNumber", "")),
                    "name": f"{emp.get('firstName', '')} {emp.get('lastName', '')}".strip(),
                    "role": emp.get("jobTitle", emp.get("primaryJob", {}).get("name", "")),
                    "department": emp.get("department", emp.get("orgUnit", {}).get("name", "")),
                    "hire_date": emp.get("hireDate", ""),
                    "email": emp.get("emailAddress", ""),
                    "shift_code": emp.get("scheduledShift", emp.get("shiftPattern", "")),
                })

            return {"success": True, "employees": employees, "count": len(employees)}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def pull_schedule(self, start_date, end_date, org_unit=None):
        """
        Pull published schedule from UKG for a date range.
        Returns data in ShiftGuard format.
        """
        try:
            # UKG Dimensions uses /scheduling/v1/schedules endpoint
            url = f"{self.base_url}/api/scheduling/v1/schedules"
            params = {
                "startDate": start_date,
                "endDate": end_date,
                "scheduleType": "published",
            }
            if org_unit:
                params["orgUnit"] = org_unit

            response = requests.get(url, headers=self._get_headers(), params=params)

            if response.status_code != 200:
                return {"success": False, "error": f"Failed: {response.status_code}"}

            ukg_schedule = response.json()

            # Map UKG format → ShiftGuard format
            shifts = []
            for entry in ukg_schedule.get("scheduleEntries", ukg_schedule.get("shifts", [])):
                shift = {
                    "employee_id": entry.get("employeeId", entry.get("personNumber", "")),
                    "name": entry.get("employeeName", entry.get("displayName", "")),
                    "date": entry.get("date", entry.get("shiftDate", ""))[:10],
                    "start": self._extract_time(entry.get("startTime", entry.get("inTime", ""))),
                    "end": self._extract_time(entry.get("endTime", entry.get("outTime", ""))),
                    "role": entry.get("jobTitle", entry.get("laborCategory", "")),
                    "shift_type": entry.get("shiftLabel", entry.get("shiftType", "Day")),
                }
                if shift["date"] and shift["start"]:
                    shifts.append(shift)

            schedule = {
                "schedule_posted_date": datetime.now().strftime("%Y-%m-%d"),
                "week_start": start_date,
                "week_end": end_date,
                "facility": f"UKG Import ({org_unit or 'All'})",
                "shifts": shifts,
                "source": "ukg_kronos",
                "synced_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            self.last_sync = datetime.now()

            return {
                "success": True,
                "schedule": schedule,
                "stats": {
                    "total_shifts": len(shifts),
                    "total_employees": len(set(s["employee_id"] for s in shifts)),
                    "date_range": f"{start_date} to {end_date}",
                },
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def pull_timecards(self, start_date, end_date):
        """Pull actual hours worked (timecards) for compliance comparison."""
        try:
            url = f"{self.base_url}/api/timekeeping/v1/timecards"
            response = requests.get(url, headers=self._get_headers(), params={
                "startDate": start_date,
                "endDate": end_date,
            })

            if response.status_code != 200:
                return {"success": False, "error": f"Failed: {response.status_code}"}

            data = response.json()
            timecards = []
            for tc in data.get("timecards", data.get("entries", [])):
                timecards.append({
                    "employee_id": tc.get("employeeId", tc.get("personNumber", "")),
                    "date": tc.get("date", "")[:10],
                    "hours_worked": tc.get("totalHours", tc.get("durationHours", 0)),
                    "clock_in": tc.get("inTime", tc.get("punchIn", "")),
                    "clock_out": tc.get("outTime", tc.get("punchOut", "")),
                    "overtime_hours": tc.get("overtimeHours", 0),
                    "status": tc.get("status", "worked"),
                })

            return {"success": True, "timecards": timecards, "count": len(timecards)}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_sync_status(self):
        """Get connection and sync status."""
        return {
            "connected": self.access_token is not None,
            "base_url": self.base_url,
            "tenant_id": self.tenant_id,
            "last_sync": self.last_sync.strftime("%Y-%m-%d %H:%M:%S") if self.last_sync else None,
            "token_valid": (
                self.token_expires and datetime.now() < self.token_expires
            ) if self.token_expires else False,
        }

    def _extract_time(self, time_str):
        """Extract HH:MM from various UKG time formats."""
        if not time_str:
            return ""
        # Handle ISO format: 2026-07-07T06:00:00
        if "T" in time_str:
            time_str = time_str.split("T")[1]
        return time_str[:5]


class UKGWebhookHandler:
    """
    Handle webhooks from UKG when schedules are published or changed.
    UKG can push events to our endpoint when:
    - A schedule is published
    - A shift is changed
    - An employee calls out
    - A timecard is approved
    """

    def __init__(self, connector, callback=None):
        self.connector = connector
        self.callback = callback

    def handle_event(self, event_data):
        """Process incoming webhook event from UKG."""
        event_type = event_data.get("eventType", event_data.get("type", ""))

        handlers = {
            "SCHEDULE_PUBLISHED": self._on_schedule_published,
            "SHIFT_CHANGED": self._on_shift_changed,
            "EMPLOYEE_CALLOUT": self._on_callout,
            "TIMECARD_APPROVED": self._on_timecard_approved,
        }

        handler = handlers.get(event_type)
        if handler:
            return handler(event_data)
        return {"handled": False, "event_type": event_type}

    def _on_schedule_published(self, event):
        """New schedule published — pull and run compliance check."""
        period = event.get("payload", {})
        start = period.get("startDate", "")
        end = period.get("endDate", "")
        if start and end:
            result = self.connector.pull_schedule(start, end)
            if result["success"] and self.callback:
                self.callback("schedule_updated", result["schedule"])
            return {"handled": True, "action": "pulled_schedule", "shifts": result.get("stats", {}).get("total_shifts", 0)}
        return {"handled": False, "error": "Missing dates in event"}

    def _on_shift_changed(self, event):
        """Individual shift changed — re-check compliance for that employee."""
        payload = event.get("payload", {})
        return {"handled": True, "action": "shift_change_detected", "employee": payload.get("employeeId")}

    def _on_callout(self, event):
        """Employee called out — trigger self-healing coverage flow."""
        payload = event.get("payload", {})
        return {
            "handled": True,
            "action": "callout_detected",
            "employee": payload.get("employeeId"),
            "date": payload.get("date"),
            "trigger": "self_healing_coverage",
        }

    def _on_timecard_approved(self, event):
        """Timecard approved — compare actual vs scheduled for compliance."""
        return {"handled": True, "action": "timecard_logged"}


def create_ukg_connector(base_url=None, client_id=None, client_secret=None):
    """Factory function to create UKG connector."""
    return UKGConnector(base_url=base_url, client_id=client_id, client_secret=client_secret)
