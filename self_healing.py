"""
Workforce Compliance AI - Self-Healing Schedule System
When a callout happens, automatically: detect gap -> rank candidates ->
offer VET in sequence -> accept first responder -> update schedule.
If no takers, escalate to MET then agency. Full automation with audit trail.
"""

from datetime import datetime, timedelta
from collections import defaultdict
from coverage_engine import find_coverage
from shift_templates import find_coverage_for_absence, SHIFT_ASSIGNMENTS, SHIFT_TEMPLATES


# Configuration
VET_RESPONSE_TIMEOUT_MINUTES = 30  # how long each VET offer is open
MAX_VET_OFFERS_BEFORE_MET = 5  # try 5 VET offers before escalating to MET
MET_RESPONSE_TIMEOUT_MINUTES = 60
AGENCY_ESCALATION_LEAD_TIME_HOURS = 4  # must escalate to agency this far before shift start


class SelfHealingEngine:
    """
    Automated schedule gap resolution.

    Flow:
    1. Callout detected (worker reports sick, no-show, or LOA starts)
    2. System identifies the gap (date, time, role, department)
    3. Ranks VET candidates by fairness
    4. Sends VET offer to #1 -> waits for response
    5. If declined or timeout -> sends to #2, then #3, etc.
    6. If all VET declined -> escalate to MET (mandatory, with notice)
    7. If MET not possible -> escalate to agency/temp staffing
    8. Manager notified at each stage with status
    """

    def __init__(self, employees=None, schedule_shifts=None, employee_history=None):
        self.employees = employees or []
        self.schedule_shifts = schedule_shifts or []
        self.employee_history = employee_history or {}
        self.incidents = []
        self.notifications = []

    def report_callout(self, employee_id, date, reason="Unplanned absence",
                       shift_start=None, shift_end=None, role=None):
        """
        Entry point: an employee calls out. Triggers the self-healing flow.

        Returns the incident with full resolution plan.
        """
        # Find the employee's scheduled shift for that date
        emp = next((e for e in self.employees if e["id"] == employee_id), None)
        if not emp:
            return {"error": f"Employee {employee_id} not found"}

        if not shift_start:
            # Look up from their shift template or schedule
            assignment = next((a for a in SHIFT_ASSIGNMENTS if a["employee_id"] == employee_id), None)
            if assignment:
                template = SHIFT_TEMPLATES.get(assignment["shift_code"], {})
                day_name = _get_day_name(date)
                day_pattern = template.get("pattern", {}).get(day_name)
                if day_pattern:
                    shift_start = day_pattern["start"]
                    shift_end = day_pattern["end"]
                    role = role or assignment.get("role")

        if not shift_start:
            shift_start = "07:00"
            shift_end = "15:30"
        if not role:
            role = emp.get("role", "Staff")

        # Create incident
        incident = {
            "id": f"INC-{len(self.incidents)+1:04d}",
            "status": "OPEN",
            "employee_id": employee_id,
            "employee_name": emp["name"],
            "date": date,
            "shift_start": shift_start,
            "shift_end": shift_end,
            "role": role,
            "reason": reason,
            "reported_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "resolution": None,
            "resolution_timeline": [],
            "vet_offers_sent": [],
            "met_candidates": [],
            "current_phase": "VET_OFFERING",
            "escalation_level": 1,
        }

        # Find VET candidates
        gap_shift = {
            "date": date,
            "start": shift_start,
            "end": shift_end,
            "role": role,
            "shift_type": "Coverage",
            "absent_employee_id": employee_id,
        }

        ref_date = datetime.strptime(date, "%Y-%m-%d") if isinstance(date, str) else date

        candidates = find_coverage(
            self.schedule_shifts, self.employees, gap_shift,
            self.employee_history, ref_date
        )

        incident["vet_candidates"] = [
            {"employee_id": c["employee_id"], "name": c["name"],
             "score": c["composite_score"], "reason": c["reason"]}
            for c in candidates
        ]

        # Start the VET offering sequence
        if candidates:
            first_offer = self._send_vet_offer(incident, candidates[0])
            incident["resolution_timeline"].append({
                "time": datetime.now().strftime("%H:%M"),
                "event": f"VET offer sent to {candidates[0]['name']} (score: {candidates[0]['composite_score']})",
                "status": "WAITING",
            })
        else:
            # No VET candidates — skip to MET
            incident["current_phase"] = "MET_REQUIRED"
            incident["escalation_level"] = 2
            incident["resolution_timeline"].append({
                "time": datetime.now().strftime("%H:%M"),
                "event": "No VET candidates available. Escalating to MET.",
                "status": "ESCALATED",
            })

        # Notify manager
        self._notify_manager(incident, "CALLOUT_RECEIVED")

        self.incidents.append(incident)
        return incident

    def process_vet_response(self, incident_id, employee_id, accepted=True):
        """
        Process a VET offer response (accept or decline).
        If accepted: resolve incident. If declined: offer to next candidate.
        """
        incident = self._get_incident(incident_id)
        if not incident:
            return {"error": "Incident not found"}

        offer = next(
            (o for o in incident["vet_offers_sent"]
             if o["employee_id"] == employee_id and o["status"] == "PENDING"),
            None
        )
        if not offer:
            return {"error": "No pending offer for this employee"}

        if accepted:
            # RESOLVED via VET
            offer["status"] = "ACCEPTED"
            offer["responded_at"] = datetime.now().strftime("%H:%M")

            incident["status"] = "RESOLVED"
            incident["current_phase"] = "RESOLVED"
            incident["resolution"] = {
                "type": "VET",
                "covered_by": employee_id,
                "covered_by_name": offer["employee_name"],
                "resolved_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "time_to_resolve_minutes": self._minutes_since(incident["reported_at"]),
            }
            incident["resolution_timeline"].append({
                "time": datetime.now().strftime("%H:%M"),
                "event": f"RESOLVED: {offer['employee_name']} accepted VET",
                "status": "RESOLVED",
            })

            self._notify_manager(incident, "RESOLVED_VET")
            return {"status": "RESOLVED", "covered_by": offer["employee_name"]}

        else:
            # DECLINED — offer to next candidate
            offer["status"] = "DECLINED"
            offer["responded_at"] = datetime.now().strftime("%H:%M")
            incident["resolution_timeline"].append({
                "time": datetime.now().strftime("%H:%M"),
                "event": f"{offer['employee_name']} declined VET",
                "status": "DECLINED",
            })

            # Find next candidate
            offered_ids = {o["employee_id"] for o in incident["vet_offers_sent"]}
            remaining = [c for c in incident["vet_candidates"] if c["employee_id"] not in offered_ids]

            if remaining and len(incident["vet_offers_sent"]) < MAX_VET_OFFERS_BEFORE_MET:
                next_candidate = remaining[0]
                self._send_vet_offer(incident, next_candidate)
                incident["resolution_timeline"].append({
                    "time": datetime.now().strftime("%H:%M"),
                    "event": f"VET offer sent to {next_candidate['name']}",
                    "status": "WAITING",
                })
                return {"status": "NEXT_OFFER_SENT", "offered_to": next_candidate["name"]}
            else:
                # Escalate to MET
                return self._escalate_to_met(incident)

    def process_vet_timeout(self, incident_id, employee_id):
        """Handle VET offer timeout (no response within window)."""
        return self.process_vet_response(incident_id, employee_id, accepted=False)

    def escalate_to_agency(self, incident_id):
        """Final escalation: no internal coverage available."""
        incident = self._get_incident(incident_id)
        if not incident:
            return {"error": "Incident not found"}

        incident["current_phase"] = "AGENCY_REQUIRED"
        incident["escalation_level"] = 3
        incident["resolution_timeline"].append({
            "time": datetime.now().strftime("%H:%M"),
            "event": "ESCALATED TO AGENCY: No internal coverage available. Temp staffing required.",
            "status": "AGENCY",
        })

        self._notify_manager(incident, "AGENCY_REQUIRED")

        return {
            "status": "AGENCY_ESCALATED",
            "message": f"No internal coverage found for {incident['date']} {incident['shift_start']}-{incident['shift_end']}. "
                      f"Agency/temp staffing notification sent.",
            "incident": incident,
        }

    def get_incident_status(self, incident_id):
        """Get current status of an incident."""
        incident = self._get_incident(incident_id)
        if not incident:
            return {"error": "Incident not found"}

        return {
            "id": incident["id"],
            "status": incident["status"],
            "phase": incident["current_phase"],
            "escalation_level": incident["escalation_level"],
            "employee": incident["employee_name"],
            "date": incident["date"],
            "shift": f"{incident['shift_start']}-{incident['shift_end']}",
            "offers_sent": len(incident["vet_offers_sent"]),
            "offers_declined": sum(1 for o in incident["vet_offers_sent"] if o["status"] == "DECLINED"),
            "resolution": incident["resolution"],
            "timeline": incident["resolution_timeline"],
        }

    def get_open_incidents(self):
        """Get all unresolved incidents."""
        return [i for i in self.incidents if i["status"] != "RESOLVED"]

    def get_resolution_stats(self):
        """Get stats on how incidents are being resolved."""
        total = len(self.incidents)
        resolved = [i for i in self.incidents if i["status"] == "RESOLVED"]
        vet_resolved = [i for i in resolved if i["resolution"]["type"] == "VET"]
        met_resolved = [i for i in resolved if i["resolution"]["type"] == "MET"]

        avg_time = 0
        if resolved:
            times = [i["resolution"]["time_to_resolve_minutes"] for i in resolved]
            avg_time = sum(times) / len(times)

        return {
            "total_incidents": total,
            "resolved": len(resolved),
            "open": total - len(resolved),
            "resolved_via_vet": len(vet_resolved),
            "resolved_via_met": len(met_resolved),
            "resolved_via_agency": sum(1 for i in self.incidents if i["current_phase"] == "AGENCY_REQUIRED"),
            "avg_resolution_time_minutes": round(avg_time, 1),
            "auto_resolution_rate": round(len(resolved) / max(1, total) * 100, 1),
        }

    # --- Private Methods ---

    def _send_vet_offer(self, incident, candidate):
        """Send a VET offer to a candidate."""
        offer = {
            "employee_id": candidate["employee_id"] if isinstance(candidate, dict) else candidate.get("employee_id"),
            "employee_name": candidate["name"] if isinstance(candidate, dict) else candidate.get("name"),
            "sent_at": datetime.now().strftime("%H:%M"),
            "expires_at": (datetime.now() + timedelta(minutes=VET_RESPONSE_TIMEOUT_MINUTES)).strftime("%H:%M"),
            "status": "PENDING",
            "shift_date": incident["date"],
            "shift_start": incident["shift_start"],
            "shift_end": incident["shift_end"],
            "role": incident["role"],
        }
        incident["vet_offers_sent"].append(offer)

        # Create notification
        self.notifications.append({
            "type": "VET_OFFER",
            "to": offer["employee_id"],
            "message": (
                f"VET Available: {incident['date']} {incident['shift_start']}-{incident['shift_end']} "
                f"({incident['role']}). Covering for {incident['employee_name']}. "
                f"Respond within {VET_RESPONSE_TIMEOUT_MINUTES} minutes."
            ),
            "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "incident_id": incident["id"],
        })

        return offer

    def _escalate_to_met(self, incident):
        """Escalate to MET (Mandatory Extra Time)."""
        incident["current_phase"] = "MET_REQUIRED"
        incident["escalation_level"] = 2
        incident["resolution_timeline"].append({
            "time": datetime.now().strftime("%H:%M"),
            "event": f"All VET offers exhausted ({len(incident['vet_offers_sent'])} sent). Escalating to MET.",
            "status": "ESCALATED",
        })

        self._notify_manager(incident, "MET_REQUIRED")

        return {
            "status": "MET_ESCALATED",
            "message": (
                f"All {len(incident['vet_offers_sent'])} VET offers declined/expired. "
                f"MET (mandatory overtime) may be required. Manager must assign with appropriate notice per CBA."
            ),
            "incident": incident,
        }

    def _notify_manager(self, incident, event_type):
        """Send notification to manager."""
        if event_type == "CALLOUT_RECEIVED":
            message = (
                f"CALLOUT: {incident['employee_name']} on {incident['date']} "
                f"({incident['shift_start']}-{incident['shift_end']}). "
                f"Self-healing initiated. {len(incident.get('vet_candidates', []))} VET candidates available."
            )
        elif event_type == "RESOLVED_VET":
            covered_name = incident.get("resolution", {}).get("covered_by_name", "Unknown")
            message = (
                f"RESOLVED: {incident['date']} gap filled by "
                f"{covered_name} (VET accepted). No action needed."
            )
        elif event_type == "MET_REQUIRED":
            message = (
                f"ESCALATION: {incident['date']} {incident['shift_start']}-{incident['shift_end']} "
                f"still uncovered. All VET declined. MET assignment or agency needed."
            )
        elif event_type == "AGENCY_REQUIRED":
            message = (
                f"AGENCY NEEDED: {incident['date']} {incident['shift_start']}-{incident['shift_end']} "
                f"cannot be covered internally. Initiate temp staffing."
            )
        else:
            message = f"Incident {incident['id']} update: {event_type}"

        messages = {event_type: message}

        self.notifications.append({
            "type": f"MANAGER_{event_type}",
            "to": "MANAGER",
            "message": messages.get(event_type, f"Incident {incident['id']} update: {event_type}"),
            "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "incident_id": incident["id"],
        })

    def _get_incident(self, incident_id):
        return next((i for i in self.incidents if i["id"] == incident_id), None)

    def _minutes_since(self, timestamp_str):
        """Calculate minutes since a timestamp."""
        reported = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M")
        return round((datetime.now() - reported).total_seconds() / 60, 1)


def _get_day_name(date_str):
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    if isinstance(date_str, str):
        date_str = datetime.strptime(date_str, "%Y-%m-%d")
    return days[date_str.weekday()]


# ============================================================
# DEMO
# ============================================================

if __name__ == "__main__":
    from sample_schedule import generate_schedule, EMPLOYEES, EMPLOYEE_HISTORY

    schedule = generate_schedule()

    engine = SelfHealingEngine(
        employees=EMPLOYEES,
        schedule_shifts=schedule["shifts"],
        employee_history=EMPLOYEE_HISTORY,
    )

    print("=" * 70)
    print("  SELF-HEALING SCHEDULE SYSTEM")
    print("=" * 70)

    # Simulate: Sarah calls out tomorrow morning
    print("\n  SCENARIO: Sarah Martinez calls out sick for Monday July 7")
    print("  " + "-" * 50)

    incident = engine.report_callout(
        "E001", "2026-07-07",
        reason="Called in sick - flu symptoms",
        shift_start="06:00", shift_end="14:30", role="Pick"
    )

    print(f"\n  Incident: {incident['id']}")
    print(f"  Status: {incident['status']}")
    print(f"  Phase: {incident['current_phase']}")
    print(f"  VET candidates found: {len(incident['vet_candidates'])}")

    if incident["vet_candidates"]:
        print(f"\n  VET Ranking:")
        for i, c in enumerate(incident["vet_candidates"][:5], 1):
            print(f"    {i}. {c['name']} (score: {c['score']})")

    print(f"\n  VET offer sent to: {incident['vet_offers_sent'][0]['employee_name']}")
    print(f"  Expires at: {incident['vet_offers_sent'][0]['expires_at']}")

    # Simulate: first person declines
    print(f"\n  --- {incident['vet_offers_sent'][0]['employee_name']} DECLINES ---")
    result = engine.process_vet_response(incident["id"], incident["vet_offers_sent"][0]["employee_id"], accepted=False)
    print(f"  Result: {result['status']}")
    if "offered_to" in result:
        print(f"  Next offer to: {result['offered_to']}")

    # Simulate: second person accepts
    current_offer = incident["vet_offers_sent"][-1]
    print(f"\n  --- {current_offer['employee_name']} ACCEPTS ---")
    result = engine.process_vet_response(incident["id"], current_offer["employee_id"], accepted=True)
    print(f"  Result: {result['status']}")
    print(f"  Covered by: {result.get('covered_by', 'N/A')}")

    # Show resolution timeline
    print(f"\n  RESOLUTION TIMELINE:")
    for event in incident["resolution_timeline"]:
        print(f"    [{event['time']}] {event['event']}")

    # Show notifications
    print(f"\n  NOTIFICATIONS SENT:")
    for n in engine.notifications:
        print(f"    To: {n['to']:<10} | {n['message'][:60]}")

    # Stats
    print(f"\n  RESOLUTION STATS:")
    stats = engine.get_resolution_stats()
    print(f"    Total incidents: {stats['total_incidents']}")
    print(f"    Resolved: {stats['resolved']}")
    print(f"    Via VET: {stats['resolved_via_vet']}")
    print(f"    Auto-resolution rate: {stats['auto_resolution_rate']}%")
    print(f"    Avg time: {stats['avg_resolution_time_minutes']} minutes")
