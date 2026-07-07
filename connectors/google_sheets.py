"""
ShiftGuard - Google Sheets Connector
Reads schedule data from a shared Google Sheet in real-time.
Customer shares their schedule spreadsheet → ShiftGuard syncs automatically.

Setup:
1. Create a Google Cloud project
2. Enable Google Sheets API
3. Create a service account, download JSON key
4. Customer shares their sheet with the service account email
5. Set GOOGLE_SHEETS_CREDENTIALS_FILE env var to path of JSON key

Required pip: google-auth google-auth-oauthlib google-api-python-client
"""

import os
import json
from datetime import datetime

try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Expected column mapping (flexible — customer can use different headers)
DEFAULT_COLUMN_MAP = {
    "employee_id": ["employee_id", "emp_id", "id", "worker_id", "badge"],
    "name": ["name", "employee_name", "worker_name", "full_name"],
    "date": ["date", "shift_date", "schedule_date", "day"],
    "start": ["start", "start_time", "clock_in", "shift_start", "begin"],
    "end": ["end", "end_time", "clock_out", "shift_end", "finish"],
    "role": ["role", "position", "job_title", "department", "job", "unit"],
    "shift_type": ["shift_type", "type", "shift_name", "shift_code", "pattern"],
}


class GoogleSheetsConnector:
    """Connects to a Google Sheet and reads schedule data."""

    def __init__(self, credentials_file=None, spreadsheet_id=None):
        self.credentials_file = credentials_file or os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE")
        self.spreadsheet_id = spreadsheet_id
        self.service = None
        self.last_sync = None
        self.column_mapping = {}

    def connect(self):
        """Authenticate and create the Sheets service."""
        if not GOOGLE_AVAILABLE:
            return {"success": False, "error": "Google API libraries not installed. Run: pip install google-auth google-api-python-client"}

        if not self.credentials_file:
            return {"success": False, "error": "No credentials file. Set GOOGLE_SHEETS_CREDENTIALS_FILE env var."}

        if not os.path.exists(self.credentials_file):
            return {"success": False, "error": f"Credentials file not found: {self.credentials_file}"}

        try:
            creds = Credentials.from_service_account_file(self.credentials_file, scopes=SCOPES)
            self.service = build("sheets", "v4", credentials=creds)
            return {"success": True, "message": "Connected to Google Sheets API"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def set_spreadsheet(self, spreadsheet_id=None, spreadsheet_url=None):
        """Set which spreadsheet to read. Accepts ID or full URL."""
        if spreadsheet_url:
            # Extract ID from URL: https://docs.google.com/spreadsheets/d/{ID}/edit
            parts = spreadsheet_url.split("/d/")
            if len(parts) > 1:
                self.spreadsheet_id = parts[1].split("/")[0]
            else:
                return {"success": False, "error": "Invalid Google Sheets URL"}
        elif spreadsheet_id:
            self.spreadsheet_id = spreadsheet_id
        else:
            return {"success": False, "error": "Provide spreadsheet_id or spreadsheet_url"}

        return {"success": True, "spreadsheet_id": self.spreadsheet_id}

    def read_schedule(self, sheet_name="Schedule", range_override=None):
        """
        Read schedule data from the connected sheet.
        Returns data in ShiftGuard format (same as CSV upload).
        """
        if not self.service:
            conn = self.connect()
            if not conn["success"]:
                return conn

        if not self.spreadsheet_id:
            return {"success": False, "error": "No spreadsheet configured. Call set_spreadsheet() first."}

        try:
            range_str = range_override or f"{sheet_name}!A:Z"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_str,
            ).execute()

            rows = result.get("values", [])
            if not rows:
                return {"success": False, "error": "Sheet is empty"}

            # First row = headers
            headers = [h.strip().lower() for h in rows[0]]

            # Auto-detect column mapping
            self.column_mapping = self._detect_columns(headers)
            missing = [k for k, v in self.column_mapping.items() if v is None]

            if missing:
                return {
                    "success": False,
                    "error": f"Could not find columns: {', '.join(missing)}",
                    "headers_found": headers,
                    "suggestion": "Expected columns like: employee_id, name, date, start, end, role, shift_type",
                }

            # Parse rows into shifts
            shifts = []
            for row in rows[1:]:
                if not row or len(row) < 4:
                    continue

                shift = {}
                for field, col_idx in self.column_mapping.items():
                    if col_idx is not None and col_idx < len(row):
                        shift[field] = str(row[col_idx]).strip()
                    else:
                        shift[field] = ""

                # Normalize date format
                shift["date"] = self._normalize_date(shift.get("date", ""))
                shift["start"] = self._normalize_time(shift.get("start", ""))
                shift["end"] = self._normalize_time(shift.get("end", ""))

                if shift["date"] and shift["start"]:
                    shifts.append(shift)

            # Build schedule object (same format as CSV upload)
            dates = sorted(set(s["date"] for s in shifts))
            schedule = {
                "schedule_posted_date": datetime.now().strftime("%Y-%m-%d"),
                "week_start": dates[0] if dates else "",
                "week_end": dates[-1] if dates else "",
                "facility": f"Google Sheets Import ({sheet_name})",
                "shifts": shifts,
                "source": "google_sheets",
                "spreadsheet_id": self.spreadsheet_id,
                "synced_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            self.last_sync = datetime.now()

            return {
                "success": True,
                "schedule": schedule,
                "stats": {
                    "total_shifts": len(shifts),
                    "total_employees": len(set(s["employee_id"] for s in shifts)),
                    "date_range": f"{dates[0]} to {dates[-1]}" if dates else "empty",
                    "synced_at": schedule["synced_at"],
                },
            }

        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg:
                return {"success": False, "error": "Spreadsheet not found. Check the ID/URL and sharing permissions."}
            elif "403" in error_msg:
                return {"success": False, "error": "Access denied. Share the sheet with the service account email."}
            return {"success": False, "error": error_msg}

    def get_sync_status(self):
        """Get current connection and sync status."""
        return {
            "connected": self.service is not None,
            "spreadsheet_id": self.spreadsheet_id,
            "last_sync": self.last_sync.strftime("%Y-%m-%d %H:%M:%S") if self.last_sync else None,
            "column_mapping": self.column_mapping,
            "google_api_available": GOOGLE_AVAILABLE,
        }

    def _detect_columns(self, headers):
        """Auto-detect which column is which based on header names."""
        mapping = {}
        for field, aliases in DEFAULT_COLUMN_MAP.items():
            found = None
            for i, h in enumerate(headers):
                if h in aliases or any(a in h for a in aliases):
                    found = i
                    break
            mapping[field] = found
        return mapping

    def _normalize_date(self, date_str):
        """Normalize various date formats to YYYY-MM-DD."""
        if not date_str:
            return ""
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y", "%m-%d-%Y", "%B %d, %Y"]:
            try:
                return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return date_str[:10]

    def _normalize_time(self, time_str):
        """Normalize time to HH:MM format."""
        if not time_str:
            return ""
        time_str = time_str.strip()

        # Handle AM/PM
        for fmt in ["%I:%M %p", "%I:%M%p", "%H:%M", "%H:%M:%S"]:
            try:
                return datetime.strptime(time_str, fmt).strftime("%H:%M")
            except ValueError:
                continue

        # Already in HH:MM?
        if len(time_str) >= 4 and ":" in time_str:
            return time_str[:5]
        return time_str


def create_sheets_connector(spreadsheet_url=None):
    """Factory function to create and configure a connector."""
    connector = GoogleSheetsConnector()
    if spreadsheet_url:
        connector.set_spreadsheet(spreadsheet_url=spreadsheet_url)
    return connector
