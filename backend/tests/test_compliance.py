"""
Test suite for compliance rules engine.
Every rule must have at least one passing and one failing test case.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from datetime import datetime, timedelta
from compliance_checker import check_compliance, get_shift_hours, parse_time
from sample_schedule import EMPLOYEES


def make_schedule(shifts, posted_days_before=3, week_start="2026-07-07"):
    """Helper to create a schedule dict for testing."""
    posted = (datetime.strptime(week_start, "%Y-%m-%d") - timedelta(days=posted_days_before)).strftime("%Y-%m-%d")
    week_end = (datetime.strptime(week_start, "%Y-%m-%d") + timedelta(days=6)).strftime("%Y-%m-%d")
    return {
        "schedule_posted_date": posted,
        "week_start": week_start,
        "week_end": week_end,
        "facility": "Test Facility",
        "shifts": shifts,
    }


def make_shift(emp_id="E001", name="Test Worker", date="2026-07-07",
               start="07:00", end="15:30", role="Pick", shift_type="Day"):
    return {
        "employee_id": emp_id, "name": name, "date": date,
        "start": start, "end": end, "role": role, "shift_type": shift_type,
    }


# ============================================================
# SCHEDULE NOTICE TESTS
# ============================================================

class TestScheduleNotice:
    def test_14_day_notice_passes(self):
        """Schedule posted 14+ days before should not trigger CHI-FW-001."""
        shifts = [make_shift()]
        schedule = make_schedule(shifts, posted_days_before=14)
        violations = check_compliance(schedule)
        chi_violations = [v for v in violations if v["rule_id"] == "CHI-FW-001"]
        assert len(chi_violations) == 0

    def test_short_notice_triggers_violation(self):
        """Schedule posted <14 days before should trigger CHI-FW-001."""
        shifts = [make_shift()]
        schedule = make_schedule(shifts, posted_days_before=3)
        violations = check_compliance(schedule)
        chi_violations = [v for v in violations if v["rule_id"] == "CHI-FW-001"]
        assert len(chi_violations) == 1
        assert chi_violations[0]["severity"] == "HIGH"

    def test_cba_5_day_notice_passes(self):
        """Schedule posted 5+ days before should not trigger CBA-005."""
        shifts = [make_shift()]
        schedule = make_schedule(shifts, posted_days_before=5)
        violations = check_compliance(schedule)
        cba_violations = [v for v in violations if v["rule_id"] == "CBA-005"]
        assert len(cba_violations) == 0

    def test_cba_notice_violation(self):
        """Schedule posted <5 days before should trigger CBA-005."""
        shifts = [make_shift()]
        schedule = make_schedule(shifts, posted_days_before=4)
        violations = check_compliance(schedule)
        cba_violations = [v for v in violations if v["rule_id"] == "CBA-005"]
        assert len(cba_violations) == 1


# ============================================================
# CLOPENING / REST BETWEEN SHIFTS TESTS
# ============================================================

class TestClopening:
    def test_adequate_rest_passes(self):
        """12 hours between shifts should not trigger violation."""
        shifts = [
            make_shift(date="2026-07-07", start="06:00", end="14:00"),
            make_shift(date="2026-07-08", start="06:00", end="14:00"),
        ]
        schedule = make_schedule(shifts, posted_days_before=14)
        violations = check_compliance(schedule)
        rest_violations = [v for v in violations if "Rest" in v["rule_name"] or "Clopening" in v["rule_name"]]
        assert len(rest_violations) == 0

    def test_clopening_detected(self):
        """7.5 hours between shifts should trigger clopening violation."""
        shifts = [
            make_shift(date="2026-07-07", start="14:00", end="22:30"),
            make_shift(date="2026-07-08", start="06:00", end="14:30"),
        ]
        schedule = make_schedule(shifts, posted_days_before=14)
        violations = check_compliance(schedule)
        rest_violations = [v for v in violations if "Clopening" in v["rule_name"]]
        assert len(rest_violations) == 1
        assert rest_violations[0]["severity"] == "HIGH"


# ============================================================
# CONSECUTIVE DAYS TESTS
# ============================================================

class TestConsecutiveDays:
    def test_6_days_passes(self):
        """6 consecutive days should not trigger violation."""
        shifts = []
        for i in range(6):
            date = (datetime(2026, 7, 7) + timedelta(days=i)).strftime("%Y-%m-%d")
            shifts.append(make_shift(date=date))
        schedule = make_schedule(shifts, posted_days_before=14)
        violations = check_compliance(schedule)
        consec_violations = [v for v in violations if "Consecutive" in v["rule_name"]]
        assert len(consec_violations) == 0

    def test_7_days_triggers(self):
        """7+ consecutive days should trigger CBA-002."""
        shifts = []
        for i in range(8):
            date = (datetime(2026, 7, 1) + timedelta(days=i)).strftime("%Y-%m-%d")
            shifts.append(make_shift(date=date))
        schedule = make_schedule(shifts, posted_days_before=14)
        violations = check_compliance(schedule)
        consec_violations = [v for v in violations if "Consecutive" in v["rule_name"]]
        assert len(consec_violations) == 1
        assert "8 consecutive" in consec_violations[0]["description"]


# ============================================================
# MINIMUM SHIFT LENGTH TESTS
# ============================================================

class TestMinShiftLength:
    def test_4_hour_shift_passes(self):
        """4-hour shift should not trigger violation."""
        shifts = [make_shift(start="10:00", end="14:00")]
        schedule = make_schedule(shifts, posted_days_before=14)
        violations = check_compliance(schedule)
        min_violations = [v for v in violations if "Minimum Shift" in v["rule_name"]]
        assert len(min_violations) == 0

    def test_short_shift_triggers(self):
        """3-hour shift should trigger CBA-001."""
        shifts = [make_shift(start="10:00", end="13:00")]
        schedule = make_schedule(shifts, posted_days_before=14)
        violations = check_compliance(schedule)
        min_violations = [v for v in violations if "Minimum Shift" in v["rule_name"]]
        assert len(min_violations) == 1


# ============================================================
# WEEKLY HOURS CAP TESTS
# ============================================================

class TestWeeklyHoursCap:
    def test_under_60_passes(self):
        """50 hours in a week should not trigger violation."""
        shifts = []
        for i in range(5):
            date = (datetime(2026, 7, 7) + timedelta(days=i)).strftime("%Y-%m-%d")
            shifts.append(make_shift(date=date, start="06:00", end="16:00"))  # 10h x 5 = 50h
        schedule = make_schedule(shifts, posted_days_before=14)
        violations = check_compliance(schedule)
        cap_violations = [v for v in violations if "Hour Cap" in v["rule_name"]]
        assert len(cap_violations) == 0

    def test_over_60_triggers(self):
        """62 hours in a week should trigger CP-001."""
        shifts = []
        for i in range(6):
            date = (datetime(2026, 7, 7) + timedelta(days=i)).strftime("%Y-%m-%d")
            shifts.append(make_shift(date=date, start="06:00", end="16:30"))  # 10.5h x 6 = 63h
        schedule = make_schedule(shifts, posted_days_before=14)
        violations = check_compliance(schedule)
        cap_violations = [v for v in violations if "Hour Cap" in v["rule_name"]]
        assert len(cap_violations) == 1


# ============================================================
# MINOR RESTRICTIONS TESTS
# ============================================================

class TestMinorRestrictions:
    def test_minor_day_shift_passes(self):
        """Minor working 9am-5pm should not trigger violation."""
        shifts = [make_shift(emp_id="E006", name="Tyler Brooks",
                            start="09:00", end="17:00")]
        schedule = make_schedule(shifts, posted_days_before=14)
        violations = check_compliance(schedule)
        minor_violations = [v for v in violations if "Minor" in v["rule_name"]]
        assert len(minor_violations) == 0

    def test_minor_past_10pm_triggers(self):
        """Minor working past 10pm should trigger CP-002."""
        shifts = [make_shift(emp_id="E006", name="Tyler Brooks",
                            start="16:00", end="22:30")]
        schedule = make_schedule(shifts, posted_days_before=14)
        violations = check_compliance(schedule)
        minor_violations = [v for v in violations if "Minor" in v["rule_name"]]
        assert len(minor_violations) == 1
        assert minor_violations[0]["severity"] == "CRITICAL"


# ============================================================
# HOURS TRACKER TESTS
# ============================================================

class TestHoursTracker:
    def test_fatigue_score_green(self):
        """Employee with low hours should have green fatigue."""
        from hours_tracker import calculate_employee_hours, calculate_fatigue_score
        shifts = [make_shift(date="2026-07-07"), make_shift(date="2026-07-08")]
        metrics = calculate_employee_hours(shifts, "E001", datetime(2026, 7, 9))
        metrics = calculate_fatigue_score(metrics)
        assert metrics["fatigue_level"] == "green"
        assert metrics["fatigue_score"] < 40

    def test_ot_countdown(self):
        """OT countdown should reflect remaining hours correctly."""
        from hours_tracker import calculate_employee_hours
        shifts = []
        for i in range(4):
            date = (datetime(2026, 7, 7) + timedelta(days=i)).strftime("%Y-%m-%d")
            shifts.append(make_shift(date=date, start="06:00", end="16:00"))  # 10h x 4 = 40h
        metrics = calculate_employee_hours(shifts, "E001", datetime(2026, 7, 11))
        assert metrics["hours_remaining_before_ot"] == 0  # at exactly 40

    def test_predict_shift_impact_warns(self):
        """Adding a shift past 60h should generate warnings."""
        from hours_tracker import predict_shift_impact
        shifts = []
        for i in range(6):
            date = (datetime(2026, 7, 7) + timedelta(days=i)).strftime("%Y-%m-%d")
            shifts.append(make_shift(date=date, start="06:00", end="16:30"))  # 10.5h x 6 = 63h
        proposed = make_shift(date="2026-07-13", start="06:00", end="16:30")
        impact = predict_shift_impact(shifts, "E001", proposed, datetime(2026, 7, 12))
        assert len(impact["warnings"]) > 0


# ============================================================
# SCHEDULE GENERATOR TESTS
# ============================================================

class TestScheduleGenerator:
    def test_full_year_all_shifts_filled(self):
        """Full year 24/7 with 5 workers should generate 1095 shifts."""
        from schedule_generator import ScheduleGenerator
        workers = [{"id": f"W{i}", "name": f"Worker {i}"} for i in range(5)]
        gen = ScheduleGenerator(workers, "healthcare_24_7")
        results = gen.generate("2026-01-01", "2026-12-31")
        assert results["total_shifts"] == 365 * 3  # 3 shifts per day

    def test_fairness_nights_equal(self):
        """Night shifts should be distributed within 2 of each other."""
        from schedule_generator import ScheduleGenerator
        workers = [{"id": f"W{i}", "name": f"Worker {i}"} for i in range(5)]
        gen = ScheduleGenerator(workers, "healthcare_24_7")
        results = gen.generate("2026-01-01", "2026-03-31")
        sc = results["fairness_scorecard"]
        assert sc["max_night_deviation"] <= 2.0

    def test_blocked_dates_respected(self):
        """Blocked dates should not have shifts assigned to that worker."""
        from schedule_generator import ScheduleGenerator
        workers = [{"id": f"W{i}", "name": f"Worker {i}"} for i in range(3)]
        gen = ScheduleGenerator(workers, "healthcare_12hr")
        gen.add_blocked_dates("W0", "2026-01-10", "2026-01-20")
        results = gen.generate("2026-01-01", "2026-01-31")
        blocked_shifts = [s for s in results["schedule"]
                         if s["worker_id"] == "W0" and "2026-01-10" <= s["date"] <= "2026-01-20"]
        assert len(blocked_shifts) == 0


# ============================================================
# HOLIDAY AUCTION TESTS
# ============================================================

class TestHolidayAuction:
    def test_non_conflicting_p1_all_granted(self):
        """If no P1 conflicts, everyone gets their P1."""
        from holiday_auction import HolidayAuction
        auction = HolidayAuction(max_off_per_period=2)
        auction.submit_preferences("A", "Alice", [
            {"period_name": "Christmas Week", "priority": 1, "start_date": "2026-12-21", "end_date": "2026-12-27"}
        ])
        auction.submit_preferences("B", "Bob", [
            {"period_name": "Thanksgiving Week", "priority": 1, "start_date": "2026-11-23", "end_date": "2026-11-29"}
        ])
        results = auction.run_allocation()
        assert len(results["allocations"]["A"]["granted"]) == 1
        assert len(results["allocations"]["B"]["granted"]) == 1

    def test_conflict_resolved_by_fairness(self):
        """When P1 conflicts, person with higher sacrifice score wins."""
        from holiday_auction import HolidayAuction
        auction = HolidayAuction(max_off_per_period=1)
        auction.submit_preferences("A", "Alice", [
            {"period_name": "Christmas Week", "priority": 1, "start_date": "2026-12-21", "end_date": "2026-12-27"}
        ])
        auction.submit_preferences("B", "Bob", [
            {"period_name": "Christmas Week", "priority": 1, "start_date": "2026-12-21", "end_date": "2026-12-27"}
        ])
        auction.set_historical_data("A", {"sacrifice_score": 10, "holidays_denied_last_year": ["Christmas"], "total_holidays_last_year": 1})
        auction.set_historical_data("B", {"sacrifice_score": 0, "holidays_denied_last_year": [], "total_holidays_last_year": 3})

        results = auction.run_allocation()
        assert len(results["allocations"]["A"]["granted"]) == 1
        assert len(results["allocations"]["B"]["denied"]) == 1


# ============================================================
# ACCESS CONTROL TESTS
# ============================================================

class TestAccessControl:
    def test_worker_cannot_approve(self):
        """Workers should not be able to approve requests."""
        from access_control import AccessControl
        ac = AccessControl()
        ac.assign_role("E001", "WORKER")
        result = ac.check_permission("E001", "approve_deny_requests")
        assert result["allowed"] is False

    def test_manager_scoped_to_team(self):
        """Manager should only access their own team."""
        from access_control import AccessControl
        ac = AccessControl()
        ac.assign_role("MGR", "MANAGER")
        ac.assign_team("MGR", ["E001", "E002"])
        assert ac.check_permission("MGR", "approve_deny_requests", "E001")["allowed"] is True
        assert ac.check_permission("MGR", "approve_deny_requests", "E009")["allowed"] is False

    def test_protected_request_bypasses_fairness(self):
        """Religious accommodation should be auto-approved and bypass fairness."""
        from access_control import ProtectedRequestHandler
        handler = ProtectedRequestHandler()
        result = handler.submit_protected_request("E009", "RELIGIOUS_ACCOMMODATION", {})
        assert result["status"] == "APPROVED"
        assert result["bypasses_fairness"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
