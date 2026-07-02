"""
Workforce Compliance AI - Manager Queue & Auto-Resolution
Managers only see what needs their attention. 80%+ resolves automatically.
"""

from datetime import datetime, timedelta
from collections import defaultdict
from worker_portal import (
    WorkerPortal, STATUS_PENDING, STATUS_AUTO_APPROVED,
    STATUS_APPROVED, STATUS_DENIED, STATUS_ESCALATED
)


class ManagerQueue:
    """Manager-facing queue showing only what needs attention."""

    def __init__(self, portal: WorkerPortal):
        self.portal = portal
        self.manager_actions = []

    def get_queue_summary(self):
        """Get a summary of the queue state."""
        all_requests = self.portal.requests

        pending = [r for r in all_requests if r["status"] == STATUS_PENDING]
        escalated = [r for r in all_requests if r["status"] == STATUS_ESCALATED]
        auto_approved = [r for r in all_requests if r["status"] == STATUS_AUTO_APPROVED]
        approved = [r for r in all_requests if r["status"] == STATUS_APPROVED]
        denied = [r for r in all_requests if r["status"] == STATUS_DENIED]

        needs_action = pending + escalated

        return {
            "total_requests": len(all_requests),
            "needs_action": len(needs_action),
            "auto_resolved": len(auto_approved),
            "manually_approved": len(approved),
            "denied": len(denied),
            "escalated": len(escalated),
            "pending": len(pending),
            "auto_resolution_rate": (
                round(len(auto_approved) / max(1, len(all_requests)) * 100, 1)
            ),
            "time_saved_estimate": f"{len(auto_approved) * 5} minutes",
        }

    def get_action_items(self):
        """Get items that need manager attention, sorted by priority."""
        all_requests = self.portal.requests

        needs_action = [
            r for r in all_requests
            if r["status"] in (STATUS_PENDING, STATUS_ESCALATED)
        ]

        # Sort: escalated first, then by submission date
        needs_action.sort(key=lambda x: (
            0 if x["status"] == STATUS_ESCALATED else 1,
            x["submitted_at"]
        ))

        items = []
        for r in needs_action:
            item = {
                "request": r,
                "urgency": self._assess_urgency(r),
                "suggested_action": self._suggest_action(r),
                "alternatives": self._find_alternatives(r),
                "impact_if_approved": self._assess_impact(r),
                "impact_if_denied": self._assess_denial_impact(r),
            }
            items.append(item)

        return items

    def get_auto_approved_log(self):
        """Show what was auto-approved (for transparency/audit)."""
        auto = [
            r for r in self.portal.requests
            if r["status"] == STATUS_AUTO_APPROVED
        ]

        log = []
        for r in auto:
            entry = {
                "request_id": r["id"],
                "type": r["type"],
                "employee": r["employee_name"],
                "submitted": r["submitted_at"],
                "reason": (
                    r.get("auto_approval_result", {}).get("reason", "Auto-approved")
                ),
            }

            if r["type"] == "HOLIDAY":
                entry["details"] = f"{r['start_date']} to {r['end_date']} (Priority {r['priority']})"
            elif r["type"] == "SHIFT_SWAP":
                entry["details"] = f"Swap with {r.get('target_employee_name', 'N/A')}"
            elif r["type"] == "PREFERENCE":
                entry["details"] = "Preferences updated"
            elif r["type"] in ("VET_ACCEPT", "VET_DECLINE"):
                entry["details"] = f"VET response: {r['type'].split('_')[1].lower()}"
            elif r["type"] == "OPEN_SHIFT":
                entry["details"] = f"Picked up shift on {r.get('shift_details', {}).get('date', 'N/A')}"
            else:
                entry["details"] = ""

            log.append(entry)

        return log

    def approve_request(self, request_id, manager_notes=""):
        """Manager manually approves a request."""
        request = self.portal._get_request(request_id)
        if not request:
            return {"error": "Request not found"}

        request["status"] = STATUS_APPROVED
        request["manager_notes"] = manager_notes
        request["resolved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        request["resolved_by"] = "manager"

        self.manager_actions.append({
            "action": "APPROVE",
            "request_id": request_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "notes": manager_notes,
        })

        return {"status": "APPROVED", "request": request}

    def deny_request(self, request_id, reason="", suggest_alternative=True):
        """Manager denies a request with reason and optional alternative."""
        request = self.portal._get_request(request_id)
        if not request:
            return {"error": "Request not found"}

        request["status"] = STATUS_DENIED
        request["manager_notes"] = reason
        request["resolved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        request["resolved_by"] = "manager"

        result = {"status": "DENIED", "reason": reason, "request": request}

        if suggest_alternative and request["type"] == "HOLIDAY":
            alternatives = self._find_alternatives(request)
            request["alternatives_suggested"] = alternatives
            result["alternatives"] = alternatives

        self.manager_actions.append({
            "action": "DENY",
            "request_id": request_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "reason": reason,
        })

        return result

    def get_request_analytics(self):
        """Analytics on request patterns (helps with workforce planning)."""
        all_requests = self.portal.requests

        by_type = defaultdict(int)
        by_employee = defaultdict(int)
        by_status = defaultdict(int)
        holiday_months = defaultdict(int)

        for r in all_requests:
            by_type[r["type"]] += 1
            by_employee[r["employee_name"]] += 1
            by_status[r["status"]] += 1

            if r["type"] == "HOLIDAY":
                month = r["start_date"][:7]
                holiday_months[month] += 1

        # Find peak holiday request periods
        peak_months = sorted(holiday_months.items(), key=lambda x: x[1], reverse=True)

        return {
            "total_requests": len(all_requests),
            "by_type": dict(by_type),
            "by_employee": dict(by_employee),
            "by_status": dict(by_status),
            "peak_holiday_months": peak_months[:5],
            "avg_requests_per_employee": (
                round(len(all_requests) / max(1, len(by_employee)), 1)
            ),
            "most_active_requester": (
                max(by_employee.items(), key=lambda x: x[1]) if by_employee else ("N/A", 0)
            ),
        }

    def get_coverage_gaps(self):
        """Identify upcoming coverage gaps from approved time-off."""
        approved_holidays = [
            r for r in self.portal.requests
            if r["type"] == "HOLIDAY"
            and r["status"] in (STATUS_APPROVED, STATUS_AUTO_APPROVED)
        ]

        gaps = []
        for r in approved_holidays:
            start = datetime.strptime(r["start_date"], "%Y-%m-%d")
            end = datetime.strptime(r["end_date"], "%Y-%m-%d")
            days = (end - start).days + 1

            gaps.append({
                "employee": r["employee_name"],
                "employee_id": r["employee_id"],
                "start_date": r["start_date"],
                "end_date": r["end_date"],
                "days": days,
                "coverage_needed": True,
                "coverage_found": False,
            })

        gaps.sort(key=lambda x: x["start_date"])
        return gaps

    # --- Private helpers ---

    def _assess_urgency(self, request):
        """Assess urgency of a pending request."""
        if request["status"] == STATUS_ESCALATED:
            return "HIGH"

        if request["type"] == "HOLIDAY":
            start = datetime.strptime(request["start_date"], "%Y-%m-%d")
            days_until = (start - datetime.now()).days
            if days_until <= 7:
                return "HIGH"
            elif days_until <= 14:
                return "MEDIUM"
            return "LOW"

        if request["type"] == "SHIFT_SWAP":
            return "MEDIUM"

        return "LOW"

    def _suggest_action(self, request):
        """Suggest what the manager should do."""
        if request["type"] == "HOLIDAY":
            result = request.get("auto_approval_result", {})
            failed = result.get("checks_failed", [])

            if "Coverage risk" in str(failed):
                return "Consider approving with coverage plan - find VET coverage first"
            elif "Fairness concern" in str(failed):
                return "Review against team holiday distribution before deciding"
            elif "Short notice" in str(failed):
                return "Short notice - approve if coverage available, otherwise deny with alternative dates"
            return "Review and approve/deny"

        if request["type"] == "SHIFT_SWAP":
            compliance = request.get("compliance_check", {})
            if compliance.get("both_compliant"):
                return "Swap is compliant - recommend approve once target accepts"
            return "Compliance concern - review details before approving"

        return "Review and decide"

    def _find_alternatives(self, request):
        """Find alternative options to suggest if denying."""
        alternatives = []

        if request["type"] == "HOLIDAY":
            # Suggest nearby dates with better coverage
            start = datetime.strptime(request["start_date"], "%Y-%m-%d")

            # Week before
            alt_start = (start - timedelta(days=7)).strftime("%Y-%m-%d")
            alt_end = (start - timedelta(days=1)).strftime("%Y-%m-%d")
            alternatives.append({
                "type": "earlier_dates",
                "description": f"Week earlier: {alt_start} to {alt_end}",
                "start_date": alt_start,
                "end_date": alt_end,
            })

            # Week after
            end = datetime.strptime(request["end_date"], "%Y-%m-%d")
            alt_start = (end + timedelta(days=1)).strftime("%Y-%m-%d")
            alt_end = (end + timedelta(days=7)).strftime("%Y-%m-%d")
            alternatives.append({
                "type": "later_dates",
                "description": f"Week later: {alt_start} to {alt_end}",
                "start_date": alt_start,
                "end_date": alt_end,
            })

            # Shorter duration
            mid = start + timedelta(days=2)
            alternatives.append({
                "type": "shorter",
                "description": f"Shorter: {request['start_date']} to {mid.strftime('%Y-%m-%d')} (3 days)",
                "start_date": request["start_date"],
                "end_date": mid.strftime("%Y-%m-%d"),
            })

        return alternatives

    def _assess_impact(self, request):
        """Assess the impact of approving this request."""
        if request["type"] == "HOLIDAY":
            return {
                "coverage": "Shift code needs VET coverage for the period",
                "cost": "Potential OT cost for coverage",
                "fairness": "Aligns with priority ranking",
            }
        if request["type"] == "SHIFT_SWAP":
            return {
                "coverage": "No coverage gap - direct swap",
                "cost": "No additional cost",
                "fairness": "Mutual agreement",
            }
        return {}

    def _assess_denial_impact(self, request):
        """Assess the impact of denying this request."""
        priority = request.get("priority", 0)

        impact = {
            "morale": "LOW" if priority > 1 else "HIGH",
            "retention_risk": "LOW",
        }

        if priority == 1:
            impact["morale"] = "HIGH"
            impact["retention_risk"] = "MEDIUM"
            impact["note"] = "This is their #1 priority request - denial may significantly impact morale"

        return impact


if __name__ == "__main__":
    from worker_portal import create_demo_portal

    portal = create_demo_portal()
    queue = ManagerQueue(portal)

    print("=" * 70)
    print("  MANAGER QUEUE & AUTO-RESOLUTION")
    print("=" * 70)

    # Queue summary
    summary = queue.get_queue_summary()
    print(f"\n  QUEUE SUMMARY:")
    print(f"    Total requests:      {summary['total_requests']}")
    print(f"    Auto-resolved:       {summary['auto_resolved']} ({summary['auto_resolution_rate']}%)")
    print(f"    Needs your action:   {summary['needs_action']}")
    print(f"    Escalated:           {summary['escalated']}")
    print(f"    Time saved:          ~{summary['time_saved_estimate']}")

    # Action items
    print(f"\n\n  ACTION ITEMS (requires manager decision):")
    print(f"  {'-'*60}")
    items = queue.get_action_items()

    if items:
        for i, item in enumerate(items, 1):
            r = item["request"]
            print(f"\n  #{i} [{item['urgency']}] {r['type']} - {r['employee_name']}")
            if r["type"] == "HOLIDAY":
                print(f"     Dates: {r['start_date']} to {r['end_date']} (Priority {r['priority']})")
                print(f"     Reason: {r.get('reason', 'N/A')}")
            elif r["type"] == "SHIFT_SWAP":
                print(f"     Swap with: {r.get('target_employee_name', 'N/A')}")
            print(f"     Suggested: {item['suggested_action']}")
            if item["alternatives"]:
                print(f"     Alternatives: {item['alternatives'][0]['description']}")
    else:
        print("  No items need attention - everything was auto-resolved!")

    # Auto-approved log
    print(f"\n\n  AUTO-APPROVED LOG (no manager action needed):")
    print(f"  {'ID':<10} {'Type':<12} {'Employee':<20} {'Details'}")
    print(f"  {'-'*70}")
    for entry in queue.get_auto_approved_log():
        print(f"  {entry['request_id']:<10} {entry['type']:<12} "
              f"{entry['employee']:<20} {entry['details']}")

    # Coverage gaps
    print(f"\n\n  UPCOMING COVERAGE GAPS (from approved time-off):")
    print(f"  {'Employee':<20} {'Dates':<25} {'Days'}")
    print(f"  {'-'*55}")
    for gap in queue.get_coverage_gaps():
        print(f"  {gap['employee']:<20} {gap['start_date']} to {gap['end_date']:<12} {gap['days']}")

    # Analytics
    print(f"\n\n  REQUEST ANALYTICS:")
    analytics = queue.get_request_analytics()
    print(f"    Total requests: {analytics['total_requests']}")
    print(f"    Avg per employee: {analytics['avg_requests_per_employee']}")
    print(f"    Most active: {analytics['most_active_requester'][0]} ({analytics['most_active_requester'][1]} requests)")
    if analytics["peak_holiday_months"]:
        print(f"    Peak holiday months: {', '.join(m[0] for m in analytics['peak_holiday_months'])}")
