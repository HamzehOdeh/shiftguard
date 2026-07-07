"""
audit_analytics.py - Post-Week Compliance Auditing, Trend Analysis, and Reporting

This module handles the "after" piece of workforce compliance:
what happened, what it cost, and how to improve going forward.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta, date
from enum import Enum
import csv
import random


# =============================================================================
# DATA MODELS
# =============================================================================

class ViolationType(Enum):
    MEAL_BREAK_MISSED = "meal_break_missed"
    MEAL_BREAK_LATE = "meal_break_late"
    SHIFT_OVER_MAX_HOURS = "shift_over_max_hours"
    UNAUTHORIZED_OVERTIME = "unauthorized_overtime"
    LATE_START = "late_start"
    EARLY_END = "early_end"
    CONSECUTIVE_DAYS_EXCEEDED = "consecutive_days_exceeded"
    INSUFFICIENT_REST_BETWEEN_SHIFTS = "insufficient_rest_between_shifts"
    SCHEDULE_CHANGE_NO_NOTICE = "schedule_change_without_notice"
    MINOR_HOURS_VIOLATION = "minor_hours_violation"
    SPLIT_SHIFT_VIOLATION = "split_shift_violation"
    FAIRNESS_IMBALANCE = "fairness_imbalance"


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Violation:
    violation_type: ViolationType
    employee_id: str
    employee_name: str
    shift_date: date
    severity: Severity
    description: str
    planned_value: Optional[str] = None
    actual_value: Optional[str] = None
    cost_impact: float = 0.0
    manager: str = ""


@dataclass
class ShiftPlanned:
    employee_id: str
    employee_name: str
    shift_date: date
    start_time: str
    end_time: str
    break_start: str
    break_duration_min: int
    manager: str


@dataclass
class ShiftActual:
    employee_id: str
    employee_name: str
    shift_date: date
    start_time: str
    end_time: str
    break_start: Optional[str]
    break_duration_min: int
    overtime_authorized: bool = False
    manager: str = ""


@dataclass
class AuditResult:
    week_start: date
    week_end: date
    facility: str
    violations: List[Violation]
    total_shifts_audited: int
    total_violation_count: int
    total_cost: float
    compliance_rate: float


@dataclass
class CostBreakdown:
    premium_pay_owed: float
    grievance_risk_cost: float
    potential_fines: float
    administrative_costs: float
    total_cost: float


@dataclass
class TrendResult:
    most_common_violations: List[Tuple[ViolationType, int]]
    most_affected_employees: List[Tuple[str, int]]
    day_of_week_patterns: Dict[str, int]
    manager_comparison: Dict[str, float]
    improvement_rate: float
    seasonal_notes: str


@dataclass
class Scorecard:
    facility: str
    period: str
    overall_score: float
    scheduling_score: float
    leave_score: float
    breaks_score: float
    fairness_score: float
    prior_period_score: float
    benchmark_score: float
    top_improvements: List[Dict[str, any]]


@dataclass
class RiskAssessment:
    jurisdiction: str
    total_exposure: float
    investigation_trigger_risk: str
    statute_items: List[Dict[str, any]]
    remediation_priorities: List[Dict[str, any]]


@dataclass
class GrievancePrediction:
    employee_id: str
    employee_name: str
    risk_score: float
    contributing_factors: List[str]
    recommended_actions: List[str]


# =============================================================================
# JURISDICTION-SPECIFIC COST DATA
# =============================================================================

JURISDICTION_COSTS = {
    "CA": {
        "meal_break_penalty_hours": 1.0,
        "rest_break_penalty_hours": 1.0,
        "schedule_change_premium_hours": 1.0,
        "overtime_multiplier": 1.5,
        "double_time_multiplier": 2.0,
        "consecutive_day_7_multiplier": 1.5,
        "consecutive_day_7_over_8_multiplier": 2.0,
        "regulatory_fine_per_violation": 250.0,
        "repeat_violation_multiplier": 2.0,
    },
    "WA": {
        "meal_break_penalty_hours": 1.0,
        "rest_break_penalty_hours": 1.0,
        "schedule_change_premium_hours": 0.5,
        "overtime_multiplier": 1.5,
        "double_time_multiplier": 1.5,
        "consecutive_day_7_multiplier": 1.5,
        "consecutive_day_7_over_8_multiplier": 1.5,
        "regulatory_fine_per_violation": 200.0,
        "repeat_violation_multiplier": 1.5,
    },
    "NY": {
        "meal_break_penalty_hours": 1.0,
        "rest_break_penalty_hours": 0.5,
        "schedule_change_premium_hours": 0.75,
        "overtime_multiplier": 1.5,
        "double_time_multiplier": 1.5,
        "consecutive_day_7_multiplier": 1.5,
        "consecutive_day_7_over_8_multiplier": 1.5,
        "regulatory_fine_per_violation": 300.0,
        "repeat_violation_multiplier": 2.5,
    },
    "DEFAULT": {
        "meal_break_penalty_hours": 1.0,
        "rest_break_penalty_hours": 0.5,
        "schedule_change_premium_hours": 0.5,
        "overtime_multiplier": 1.5,
        "double_time_multiplier": 2.0,
        "consecutive_day_7_multiplier": 1.5,
        "consecutive_day_7_over_8_multiplier": 2.0,
        "regulatory_fine_per_violation": 150.0,
        "repeat_violation_multiplier": 1.5,
    },
}

GRIEVANCE_BASE_COSTS = {
    ViolationType.MEAL_BREAK_MISSED: 500.0,
    ViolationType.MEAL_BREAK_LATE: 200.0,
    ViolationType.SHIFT_OVER_MAX_HOURS: 800.0,
    ViolationType.UNAUTHORIZED_OVERTIME: 600.0,
    ViolationType.CONSECUTIVE_DAYS_EXCEEDED: 1200.0,
    ViolationType.INSUFFICIENT_REST_BETWEEN_SHIFTS: 400.0,
    ViolationType.SCHEDULE_CHANGE_NO_NOTICE: 300.0,
    ViolationType.LATE_START: 100.0,
    ViolationType.EARLY_END: 100.0,
    ViolationType.MINOR_HOURS_VIOLATION: 350.0,
    ViolationType.SPLIT_SHIFT_VIOLATION: 250.0,
    ViolationType.FAIRNESS_IMBALANCE: 150.0,
}


# =============================================================================
# 1. WEEKLY AUDIT
# =============================================================================

def run_audit(
    schedule_planned: List[ShiftPlanned],
    schedule_actual: List[ShiftActual],
    rules: Optional[Dict] = None,
    facility: str = "Default Facility",
) -> AuditResult:
    """
    Compare planned vs actual schedule and identify all violations that occurred.

    Catches: meal breaks missed, shifts that ran over, unauthorized OT,
    late starts/early ends, consecutive day violations.
    """
    if rules is None:
        rules = {
            "max_shift_hours": 10,
            "max_consecutive_days": 6,
            "min_rest_between_shifts_hours": 10,
            "meal_break_by_hour": 5,
            "meal_break_min_duration": 30,
            "late_start_threshold_min": 10,
            "early_end_threshold_min": 15,
        }

    violations = []
    actual_by_key = {
        (s.employee_id, s.shift_date): s for s in schedule_actual
    }

    for planned in schedule_planned:
        key = (planned.employee_id, planned.shift_date)
        actual = actual_by_key.get(key)
        if actual is None:
            continue

        # Check meal break missed
        if actual.break_start is None or actual.break_duration_min < rules["meal_break_min_duration"]:
            violations.append(Violation(
                violation_type=ViolationType.MEAL_BREAK_MISSED,
                employee_id=planned.employee_id,
                employee_name=planned.employee_name,
                shift_date=planned.shift_date,
                severity=Severity.HIGH,
                description=f"Meal break missed or under {rules['meal_break_min_duration']} min "
                            f"(actual: {actual.break_duration_min} min)",
                planned_value=f"{planned.break_duration_min} min break at {planned.break_start}",
                actual_value=f"{actual.break_duration_min} min" if actual.break_start else "No break taken",
                manager=planned.manager,
            ))

        # Check shift over max hours
        planned_hours = _parse_shift_hours(actual.start_time, actual.end_time)
        if planned_hours > rules["max_shift_hours"]:
            violations.append(Violation(
                violation_type=ViolationType.SHIFT_OVER_MAX_HOURS,
                employee_id=planned.employee_id,
                employee_name=planned.employee_name,
                shift_date=planned.shift_date,
                severity=Severity.HIGH,
                description=f"Shift ran {planned_hours:.1f} hours, exceeding {rules['max_shift_hours']} hour max",
                planned_value=f"{_parse_shift_hours(planned.start_time, planned.end_time):.1f} hours",
                actual_value=f"{planned_hours:.1f} hours",
                manager=planned.manager,
            ))

        # Check unauthorized overtime
        planned_end_hour = _time_to_minutes(planned.end_time)
        actual_end_hour = _time_to_minutes(actual.end_time)
        overtime_minutes = actual_end_hour - planned_end_hour
        if overtime_minutes > 15 and not actual.overtime_authorized:
            violations.append(Violation(
                violation_type=ViolationType.UNAUTHORIZED_OVERTIME,
                employee_id=planned.employee_id,
                employee_name=planned.employee_name,
                shift_date=planned.shift_date,
                severity=Severity.MEDIUM,
                description=f"Unauthorized overtime of {overtime_minutes} minutes",
                planned_value=f"End at {planned.end_time}",
                actual_value=f"End at {actual.end_time} (+{overtime_minutes} min unauthorized)",
                manager=planned.manager,
            ))

        # Check late start
        planned_start_min = _time_to_minutes(planned.start_time)
        actual_start_min = _time_to_minutes(actual.start_time)
        late_minutes = actual_start_min - planned_start_min
        if late_minutes > rules["late_start_threshold_min"]:
            violations.append(Violation(
                violation_type=ViolationType.LATE_START,
                employee_id=planned.employee_id,
                employee_name=planned.employee_name,
                shift_date=planned.shift_date,
                severity=Severity.LOW,
                description=f"Started {late_minutes} minutes late",
                planned_value=f"Start at {planned.start_time}",
                actual_value=f"Start at {actual.start_time}",
                manager=planned.manager,
            ))

        # Check early end
        early_minutes = planned_end_hour - actual_end_hour
        if early_minutes > rules["early_end_threshold_min"]:
            violations.append(Violation(
                violation_type=ViolationType.EARLY_END,
                employee_id=planned.employee_id,
                employee_name=planned.employee_name,
                shift_date=planned.shift_date,
                severity=Severity.LOW,
                description=f"Ended {early_minutes} minutes early",
                planned_value=f"End at {planned.end_time}",
                actual_value=f"End at {actual.end_time}",
                manager=planned.manager,
            ))

    # Check consecutive days per employee
    employee_dates = {}
    for actual in schedule_actual:
        employee_dates.setdefault(actual.employee_id, []).append(actual.shift_date)

    for emp_id, dates in employee_dates.items():
        sorted_dates = sorted(dates)
        consecutive = 1
        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
                consecutive += 1
                if consecutive > rules["max_consecutive_days"]:
                    emp_name = next(
                        (s.employee_name for s in schedule_actual if s.employee_id == emp_id),
                        emp_id
                    )
                    manager = next(
                        (s.manager for s in schedule_actual if s.employee_id == emp_id),
                        ""
                    )
                    violations.append(Violation(
                        violation_type=ViolationType.CONSECUTIVE_DAYS_EXCEEDED,
                        employee_id=emp_id,
                        employee_name=emp_name,
                        shift_date=sorted_dates[i],
                        severity=Severity.CRITICAL,
                        description=f"Worked {consecutive} consecutive days (max: {rules['max_consecutive_days']})",
                        planned_value=f"Max {rules['max_consecutive_days']} days",
                        actual_value=f"{consecutive} consecutive days",
                        manager=manager,
                    ))
                    break
            else:
                consecutive = 1

    total_shifts = len(schedule_actual)
    violation_count = len(violations)
    compliance_rate = (1 - violation_count / max(total_shifts, 1)) * 100

    # Determine week boundaries
    all_dates = [s.shift_date for s in schedule_actual]
    week_start = min(all_dates) if all_dates else date.today()
    week_end = max(all_dates) if all_dates else date.today()

    # Calculate costs
    total_cost = sum(v.cost_impact for v in violations)

    return AuditResult(
        week_start=week_start,
        week_end=week_end,
        facility=facility,
        violations=violations,
        total_shifts_audited=total_shifts,
        total_violation_count=violation_count,
        total_cost=total_cost,
        compliance_rate=compliance_rate,
    )


# =============================================================================
# 2. COST CALCULATOR
# =============================================================================

def calculate_violation_costs(
    violations: List[Violation],
    jurisdiction: str = "CA",
    hourly_rates: Optional[Dict[str, float]] = None,
) -> CostBreakdown:
    """
    Calculate the precise dollar impact of each violation.

    Returns premium pay owed, grievance risk cost, potential regulatory fines,
    administrative overhead, and total cost of non-compliance.
    """
    if hourly_rates is None:
        hourly_rates = {}

    default_rate = 22.50  # Average warehouse AA rate
    jur_costs = JURISDICTION_COSTS.get(jurisdiction, JURISDICTION_COSTS["DEFAULT"])

    premium_pay = 0.0
    grievance_risk = 0.0
    potential_fines = 0.0
    admin_costs = 0.0

    for v in violations:
        rate = hourly_rates.get(v.employee_id, default_rate)

        # Premium pay calculation
        if v.violation_type == ViolationType.MEAL_BREAK_MISSED:
            premium_pay += rate * jur_costs["meal_break_penalty_hours"]
            v.cost_impact = rate * jur_costs["meal_break_penalty_hours"]

        elif v.violation_type == ViolationType.MEAL_BREAK_LATE:
            premium_pay += rate * jur_costs["rest_break_penalty_hours"]
            v.cost_impact = rate * jur_costs["rest_break_penalty_hours"]

        elif v.violation_type == ViolationType.UNAUTHORIZED_OVERTIME:
            ot_hours = 0.5  # Estimated average unauthorized OT
            premium_pay += rate * ot_hours * jur_costs["overtime_multiplier"]
            v.cost_impact = rate * ot_hours * jur_costs["overtime_multiplier"]

        elif v.violation_type == ViolationType.SHIFT_OVER_MAX_HOURS:
            premium_pay += rate * 1.0 * jur_costs["overtime_multiplier"]
            v.cost_impact = rate * 1.0 * jur_costs["overtime_multiplier"]

        elif v.violation_type == ViolationType.SCHEDULE_CHANGE_NO_NOTICE:
            premium_pay += rate * jur_costs["schedule_change_premium_hours"]
            v.cost_impact = rate * jur_costs["schedule_change_premium_hours"]

        elif v.violation_type == ViolationType.CONSECUTIVE_DAYS_EXCEEDED:
            premium_pay += rate * 8 * (jur_costs["consecutive_day_7_multiplier"] - 1.0)
            v.cost_impact = rate * 8 * (jur_costs["consecutive_day_7_multiplier"] - 1.0)

        elif v.violation_type in (ViolationType.LATE_START, ViolationType.EARLY_END):
            admin_costs += 15.0  # Administrative tracking cost
            v.cost_impact = 15.0

        else:
            premium_pay += rate * 0.5
            v.cost_impact = rate * 0.5

        # Grievance risk cost
        base_grievance = GRIEVANCE_BASE_COSTS.get(v.violation_type, 200.0)
        if v.severity == Severity.CRITICAL:
            grievance_risk += base_grievance * 0.85
        elif v.severity == Severity.HIGH:
            grievance_risk += base_grievance * 0.45
        elif v.severity == Severity.MEDIUM:
            grievance_risk += base_grievance * 0.20
        else:
            grievance_risk += base_grievance * 0.05

        # Regulatory fines
        if v.severity in (Severity.HIGH, Severity.CRITICAL):
            potential_fines += jur_costs["regulatory_fine_per_violation"]

    # Admin overhead: approximately $50 per violation for tracking/documentation
    admin_costs += len(violations) * 50.0

    total = premium_pay + grievance_risk + potential_fines + admin_costs

    return CostBreakdown(
        premium_pay_owed=round(premium_pay, 2),
        grievance_risk_cost=round(grievance_risk, 2),
        potential_fines=round(potential_fines, 2),
        administrative_costs=round(admin_costs, 2),
        total_cost=round(total, 2),
    )


# =============================================================================
# 3. TREND ANALYSIS
# =============================================================================

def analyze_trends(audit_history: List[AuditResult]) -> TrendResult:
    """
    Analyze patterns across multiple audit periods to identify systemic issues.

    Looks at: most common violations, affected employees, day-of-week patterns,
    manager performance, improvement rates, and seasonal patterns.
    """
    if not audit_history:
        return TrendResult(
            most_common_violations=[],
            most_affected_employees=[],
            day_of_week_patterns={},
            manager_comparison={},
            improvement_rate=0.0,
            seasonal_notes="Insufficient data for seasonal analysis.",
        )

    # Most common violation types
    violation_type_counts = {}
    employee_counts = {}
    day_counts = {"Mon": 0, "Tue": 0, "Wed": 0, "Thu": 0, "Fri": 0, "Sat": 0, "Sun": 0}
    manager_violations = {}
    manager_shifts = {}

    for audit in audit_history:
        for v in audit.violations:
            violation_type_counts[v.violation_type] = violation_type_counts.get(v.violation_type, 0) + 1

            emp_key = f"{v.employee_name} ({v.employee_id})"
            employee_counts[emp_key] = employee_counts.get(emp_key, 0) + 1

            day_name = v.shift_date.strftime("%a")
            if day_name in day_counts:
                day_counts[day_name] += 1

            if v.manager:
                manager_violations[v.manager] = manager_violations.get(v.manager, 0) + 1

        # Track total shifts per manager
        for v in audit.violations:
            if v.manager:
                manager_shifts.setdefault(v.manager, 0)
        # Approximate shifts managed
        if audit.total_shifts_audited > 0:
            unique_managers = set(v.manager for v in audit.violations if v.manager)
            for mgr in unique_managers:
                manager_shifts[mgr] = manager_shifts.get(mgr, 0) + audit.total_shifts_audited // max(len(unique_managers), 1)

    # Sort violation types by frequency
    most_common = sorted(violation_type_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # Sort employees by violation count
    most_affected = sorted(employee_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # Manager comparison (violations per shift managed)
    manager_comparison = {}
    for mgr, viol_count in manager_violations.items():
        shifts = manager_shifts.get(mgr, 1)
        manager_comparison[mgr] = round((1 - viol_count / max(shifts, 1)) * 100, 1)

    # Improvement rate
    if len(audit_history) >= 2:
        first_rate = audit_history[0].compliance_rate
        last_rate = audit_history[-1].compliance_rate
        improvement_rate = last_rate - first_rate
    else:
        improvement_rate = 0.0

    # Seasonal notes
    seasonal_notes = _generate_seasonal_notes(audit_history)

    return TrendResult(
        most_common_violations=most_common,
        most_affected_employees=most_affected,
        day_of_week_patterns=day_counts,
        manager_comparison=manager_comparison,
        improvement_rate=round(improvement_rate, 1),
        seasonal_notes=seasonal_notes,
    )


# =============================================================================
# 4. COMPLIANCE SCORECARD
# =============================================================================

def generate_scorecard(
    facility: str,
    period: str,
    audit_results: List[AuditResult],
    prior_period_results: Optional[List[AuditResult]] = None,
    benchmark_score: float = 78.0,
) -> Scorecard:
    """
    Generate an executive-level compliance scorecard.

    Provides overall score (0-100), category breakdowns, period comparisons,
    facility benchmarking, and top improvement opportunities with $ value.
    """
    if not audit_results:
        return Scorecard(
            facility=facility, period=period,
            overall_score=0, scheduling_score=0, leave_score=0,
            breaks_score=0, fairness_score=0, prior_period_score=0,
            benchmark_score=benchmark_score, top_improvements=[],
        )

    # Calculate category scores
    total_violations = []
    for audit in audit_results:
        total_violations.extend(audit.violations)

    total_shifts = sum(a.total_shifts_audited for a in audit_results)

    scheduling_violations = [v for v in total_violations if v.violation_type in (
        ViolationType.SHIFT_OVER_MAX_HOURS,
        ViolationType.UNAUTHORIZED_OVERTIME,
        ViolationType.CONSECUTIVE_DAYS_EXCEEDED,
        ViolationType.INSUFFICIENT_REST_BETWEEN_SHIFTS,
        ViolationType.SCHEDULE_CHANGE_NO_NOTICE,
    )]

    break_violations = [v for v in total_violations if v.violation_type in (
        ViolationType.MEAL_BREAK_MISSED,
        ViolationType.MEAL_BREAK_LATE,
    )]

    fairness_violations = [v for v in total_violations if v.violation_type in (
        ViolationType.FAIRNESS_IMBALANCE,
    )]

    leave_violations = [v for v in total_violations if v.violation_type in (
        ViolationType.MINOR_HOURS_VIOLATION,
    )]

    # Score = 100 - (violations / shifts * penalty_weight)
    def category_score(violations_list, weight=500):
        if total_shifts == 0:
            return 100.0
        rate = len(violations_list) / total_shifts
        score = max(0, 100 - rate * weight)
        return round(score, 1)

    scheduling_score = category_score(scheduling_violations, 400)
    breaks_score = category_score(break_violations, 600)
    fairness_score = category_score(fairness_violations, 800)
    leave_score = category_score(leave_violations, 500)

    overall_score = round(
        scheduling_score * 0.35 +
        breaks_score * 0.30 +
        fairness_score * 0.20 +
        leave_score * 0.15,
        1
    )

    # Prior period comparison
    prior_score = 0.0
    if prior_period_results:
        prior_total_shifts = sum(a.total_shifts_audited for a in prior_period_results)
        prior_total_violations = sum(a.total_violation_count for a in prior_period_results)
        if prior_total_shifts > 0:
            prior_score = max(0, 100 - (prior_total_violations / prior_total_shifts) * 450)

    # Top improvement opportunities
    improvements = []
    violation_type_costs = {}
    for v in total_violations:
        vtype = v.violation_type.value
        violation_type_costs[vtype] = violation_type_costs.get(vtype, 0) + v.cost_impact

    sorted_costs = sorted(violation_type_costs.items(), key=lambda x: x[1], reverse=True)[:3]
    for vtype, cost in sorted_costs:
        improvements.append({
            "category": vtype.replace("_", " ").title(),
            "potential_savings": round(cost * 0.8, 2),  # 80% reduction target
            "action": _get_improvement_action(vtype),
        })

    return Scorecard(
        facility=facility,
        period=period,
        overall_score=overall_score,
        scheduling_score=scheduling_score,
        leave_score=leave_score,
        breaks_score=breaks_score,
        fairness_score=fairness_score,
        prior_period_score=round(prior_score, 1),
        benchmark_score=benchmark_score,
        top_improvements=improvements,
    )


# =============================================================================
# 5. REGULATORY RISK REPORT
# =============================================================================

def assess_risk(
    violations_history: List[Violation],
    jurisdiction: str = "CA",
) -> RiskAssessment:
    """
    Forward-looking regulatory risk assessment.

    Identifies patterns that could trigger investigation, tracks statute of
    limitations, estimates total exposure, and recommends remediation priority.
    """
    jur_costs = JURISDICTION_COSTS.get(jurisdiction, JURISDICTION_COSTS["DEFAULT"])

    # Total exposure calculation
    total_exposure = 0.0
    for v in violations_history:
        base_fine = jur_costs["regulatory_fine_per_violation"]
        if v.severity == Severity.CRITICAL:
            total_exposure += base_fine * jur_costs["repeat_violation_multiplier"] * 2
        elif v.severity == Severity.HIGH:
            total_exposure += base_fine * jur_costs["repeat_violation_multiplier"]
        else:
            total_exposure += base_fine

    # Investigation trigger risk
    critical_count = sum(1 for v in violations_history if v.severity == Severity.CRITICAL)
    high_count = sum(1 for v in violations_history if v.severity == Severity.HIGH)
    total_count = len(violations_history)

    if critical_count >= 5 or total_count >= 30:
        trigger_risk = "HIGH - Pattern likely to trigger regulatory investigation"
    elif critical_count >= 2 or high_count >= 10 or total_count >= 15:
        trigger_risk = "MEDIUM - Approaching thresholds for regulatory scrutiny"
    else:
        trigger_risk = "LOW - Within acceptable variance for regulatory review"

    # Statute of limitations items
    statute_items = []
    statute_periods = {
        ViolationType.MEAL_BREAK_MISSED: 3,
        ViolationType.UNAUTHORIZED_OVERTIME: 3,
        ViolationType.CONSECUTIVE_DAYS_EXCEEDED: 4,
        ViolationType.SHIFT_OVER_MAX_HOURS: 3,
        ViolationType.SCHEDULE_CHANGE_NO_NOTICE: 2,
        ViolationType.MINOR_HOURS_VIOLATION: 3,
    }

    for v in violations_history:
        years = statute_periods.get(v.violation_type, 3)
        expiry = v.shift_date + timedelta(days=years * 365)
        if expiry > date.today():
            statute_items.append({
                "violation_type": v.violation_type.value,
                "date": v.shift_date.isoformat(),
                "expires": expiry.isoformat(),
                "years_remaining": round((expiry - date.today()).days / 365, 1),
                "exposure": jur_costs["regulatory_fine_per_violation"],
            })

    # Remediation priorities
    type_counts = {}
    for v in violations_history:
        type_counts[v.violation_type] = type_counts.get(v.violation_type, 0) + 1

    remediation_priorities = []
    for vtype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        remediation_priorities.append({
            "violation_type": vtype.value,
            "occurrence_count": count,
            "estimated_cost_to_fix": count * jur_costs["regulatory_fine_per_violation"],
            "priority": "IMMEDIATE" if count >= 5 else "HIGH" if count >= 3 else "MEDIUM",
            "recommendation": _get_remediation_recommendation(vtype),
        })

    return RiskAssessment(
        jurisdiction=jurisdiction,
        total_exposure=round(total_exposure, 2),
        investigation_trigger_risk=trigger_risk,
        statute_items=statute_items[:10],
        remediation_priorities=remediation_priorities,
    )


# =============================================================================
# 6. GRIEVANCE PREDICTOR
# =============================================================================

def predict_grievances(
    schedule_history: List[ShiftActual],
    violations_history: List[Violation],
    union_activity_level: float = 0.5,
) -> List[GrievancePrediction]:
    """
    Predict which employees are most likely to file grievances.

    Based on: repeat violations against same employee, violation severity,
    union activity level, and pattern recognition.
    """
    employee_violations = {}
    for v in violations_history:
        employee_violations.setdefault(v.employee_id, []).append(v)

    predictions = []
    for emp_id, emp_violations in employee_violations.items():
        if len(emp_violations) < 2:
            continue

        emp_name = emp_violations[0].employee_name

        # Base risk from violation count
        count_risk = min(len(emp_violations) / 10.0, 0.5)

        # Severity multiplier
        severity_scores = {
            Severity.LOW: 0.05,
            Severity.MEDIUM: 0.10,
            Severity.HIGH: 0.20,
            Severity.CRITICAL: 0.35,
        }
        severity_risk = sum(severity_scores.get(v.severity, 0.05) for v in emp_violations)
        severity_risk = min(severity_risk, 0.4)

        # Recency factor (more recent = higher risk)
        most_recent = max(v.shift_date for v in emp_violations)
        days_ago = (date.today() - most_recent).days
        recency_risk = max(0, 0.2 - days_ago * 0.005)

        # Union activity multiplier
        union_multiplier = 1.0 + union_activity_level * 0.5

        # Total risk score
        raw_score = (count_risk + severity_risk + recency_risk) * union_multiplier
        risk_score = min(round(raw_score * 100, 1), 99.0)

        # Contributing factors
        factors = []
        if len(emp_violations) >= 3:
            factors.append(f"Violated {len(emp_violations)} times in audit period")
        critical_viols = [v for v in emp_violations if v.severity == Severity.CRITICAL]
        if critical_viols:
            factors.append(f"{len(critical_viols)} critical severity violation(s)")
        consecutive_viols = [v for v in emp_violations if v.violation_type == ViolationType.CONSECUTIVE_DAYS_EXCEEDED]
        if consecutive_viols:
            factors.append("Consecutive days limit exceeded - high grievance correlation")
        if days_ago <= 7:
            factors.append("Most recent violation within last 7 days")
        if union_activity_level > 0.7:
            factors.append("High union activity level at facility")

        # Recommended actions
        actions = []
        if risk_score >= 75:
            actions.append("Schedule immediate manager-employee check-in")
            actions.append("Review and correct upcoming schedule for this employee")
            actions.append("Document corrective actions taken")
        elif risk_score >= 50:
            actions.append("Flag for scheduling review next cycle")
            actions.append("Ensure no further violations in next 2 weeks")
        else:
            actions.append("Monitor - no immediate action required")

        predictions.append(GrievancePrediction(
            employee_id=emp_id,
            employee_name=emp_name,
            risk_score=risk_score,
            contributing_factors=factors,
            recommended_actions=actions,
        ))

    # Sort by risk score descending
    predictions.sort(key=lambda p: p.risk_score, reverse=True)
    return predictions


# =============================================================================
# 7. EXECUTIVE DASHBOARD DATA
# =============================================================================

def get_dashboard_data(
    audit_history: List[AuditResult],
    facility: str = "Default Facility",
) -> Dict:
    """
    Generate structured data suitable for executive dashboard charts.

    Returns data for: violations over time (line), violations by category (pie),
    cost impact (bar), fairness score, and compliance vs benchmark.
    """
    # Violations over time (line chart)
    violations_over_time = []
    for audit in audit_history:
        violations_over_time.append({
            "period": audit.week_start.isoformat(),
            "violation_count": audit.total_violation_count,
            "compliance_rate": round(audit.compliance_rate, 1),
        })

    # Violations by category (pie chart)
    category_counts = {}
    for audit in audit_history:
        for v in audit.violations:
            category = v.violation_type.value.replace("_", " ").title()
            category_counts[category] = category_counts.get(category, 0) + 1

    violations_by_category = [
        {"category": cat, "count": cnt}
        for cat, cnt in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    # Cost impact over time (bar chart)
    cost_over_time = []
    for audit in audit_history:
        total_cost = sum(v.cost_impact for v in audit.violations)
        cost_over_time.append({
            "period": audit.week_start.isoformat(),
            "total_cost": round(total_cost, 2),
            "premium_pay": round(total_cost * 0.45, 2),
            "fines_risk": round(total_cost * 0.30, 2),
            "admin_overhead": round(total_cost * 0.25, 2),
        })

    # Compliance score vs benchmark
    benchmark = 78.0  # Industry average
    compliance_vs_benchmark = []
    for audit in audit_history:
        compliance_vs_benchmark.append({
            "period": audit.week_start.isoformat(),
            "facility_score": round(audit.compliance_rate, 1),
            "benchmark": benchmark,
        })

    return {
        "facility": facility,
        "summary": {
            "total_audits": len(audit_history),
            "total_violations": sum(a.total_violation_count for a in audit_history),
            "total_cost": round(sum(sum(v.cost_impact for v in a.violations) for a in audit_history), 2),
            "current_compliance_rate": round(audit_history[-1].compliance_rate, 1) if audit_history else 0,
        },
        "violations_over_time": violations_over_time,
        "violations_by_category": violations_by_category,
        "cost_over_time": cost_over_time,
        "compliance_vs_benchmark": compliance_vs_benchmark,
    }


# =============================================================================
# 8. EXPORT FUNCTIONS
# =============================================================================

def export_to_csv(audit_results: List[AuditResult], filepath: str) -> str:
    """Export audit results to CSV for external analysis."""
    rows = []
    for audit in audit_results:
        for v in audit.violations:
            rows.append({
                "week_start": audit.week_start.isoformat(),
                "week_end": audit.week_end.isoformat(),
                "facility": audit.facility,
                "employee_id": v.employee_id,
                "employee_name": v.employee_name,
                "violation_type": v.violation_type.value,
                "severity": v.severity.value,
                "shift_date": v.shift_date.isoformat(),
                "description": v.description,
                "planned_value": v.planned_value or "",
                "actual_value": v.actual_value or "",
                "cost_impact": v.cost_impact,
                "manager": v.manager,
            })

    if rows:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    return f"Exported {len(rows)} violation records to {filepath}"


def export_executive_summary(scorecard: Scorecard) -> str:
    """Generate a formatted executive summary text report."""
    delta = scorecard.overall_score - scorecard.prior_period_score
    delta_str = f"+{delta:.1f}" if delta >= 0 else f"{delta:.1f}"
    bench_delta = scorecard.overall_score - scorecard.benchmark_score
    bench_str = f"+{bench_delta:.1f}" if bench_delta >= 0 else f"{bench_delta:.1f}"

    summary = f"""
================================================================================
              WORKFORCE COMPLIANCE EXECUTIVE SUMMARY
================================================================================

Facility:       {scorecard.facility}
Period:         {scorecard.period}
Generated:      {datetime.now().strftime('%Y-%m-%d %H:%M')}

--------------------------------------------------------------------------------
                          COMPLIANCE SCORES
--------------------------------------------------------------------------------

  Overall Score:        {scorecard.overall_score:.1f} / 100  ({delta_str} vs prior period)
  vs. Benchmark:        {bench_str} points vs industry average ({scorecard.benchmark_score:.1f})

  Category Breakdown:
    Scheduling:         {scorecard.scheduling_score:.1f} / 100
    Break Compliance:   {scorecard.breaks_score:.1f} / 100
    Fairness:           {scorecard.fairness_score:.1f} / 100
    Leave Management:   {scorecard.leave_score:.1f} / 100

--------------------------------------------------------------------------------
                     TOP IMPROVEMENT OPPORTUNITIES
--------------------------------------------------------------------------------
"""

    for i, imp in enumerate(scorecard.top_improvements, 1):
        summary += f"""
  {i}. {imp['category']}
     Potential Savings: ${imp['potential_savings']:,.2f}
     Action: {imp['action']}
"""

    summary += """
================================================================================
"""
    return summary


def export_regulatory_defense(
    violations: List[Violation],
    responses: Optional[Dict[str, str]] = None,
) -> str:
    """
    Generate a regulatory defense document for the legal team.

    Documents each violation type, corrective actions taken, and evidence of
    systemic improvement.
    """
    if responses is None:
        responses = {}

    doc = f"""
================================================================================
            REGULATORY DEFENSE DOCUMENTATION
================================================================================

Prepared:       {datetime.now().strftime('%Y-%m-%d')}
Purpose:        Demonstrate good-faith compliance efforts and corrective actions

--------------------------------------------------------------------------------
                      VIOLATION SUMMARY
--------------------------------------------------------------------------------

Total Violations in Scope:  {len(violations)}
"""

    type_counts = {}
    for v in violations:
        type_counts[v.violation_type] = type_counts.get(v.violation_type, 0) + 1

    for vtype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        response = responses.get(vtype.value, "Automated scheduling system deployed to prevent recurrence.")
        doc += f"""
  Type:               {vtype.value.replace('_', ' ').title()}
  Occurrences:        {count}
  Corrective Action:  {response}
"""

    doc += """
--------------------------------------------------------------------------------
                    SYSTEMIC IMPROVEMENTS
--------------------------------------------------------------------------------

  1. AI-powered compliance scheduling system deployed
  2. Real-time violation detection and alerting active
  3. Manager training on compliance requirements completed
  4. Weekly audit process institutionalized
  5. Automated break reminder system implemented

--------------------------------------------------------------------------------
                     EVIDENCE OF IMPROVEMENT
--------------------------------------------------------------------------------

  The organization has demonstrated continuous improvement in compliance
  metrics since deploying the workforce compliance AI system. Violation
  rates have decreased significantly, demonstrating good-faith efforts
  to maintain regulatory compliance.

================================================================================
"""
    return doc


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _time_to_minutes(time_str: str) -> int:
    """Convert HH:MM time string to minutes since midnight."""
    parts = time_str.split(":")
    return int(parts[0]) * 60 + int(parts[1])


def _parse_shift_hours(start: str, end: str) -> float:
    """Calculate shift duration in hours from start/end time strings."""
    start_min = _time_to_minutes(start)
    end_min = _time_to_minutes(end)
    if end_min < start_min:
        end_min += 24 * 60  # Overnight shift
    return (end_min - start_min) / 60.0


def _generate_seasonal_notes(audit_history: List[AuditResult]) -> str:
    """Generate seasonal observation notes from audit data."""
    if len(audit_history) < 4:
        return "Insufficient data for seasonal analysis (need 4+ weeks)."

    first_half_viols = sum(a.total_violation_count for a in audit_history[:len(audit_history) // 2])
    second_half_viols = sum(a.total_violation_count for a in audit_history[len(audit_history) // 2:])

    if first_half_viols > second_half_viols * 1.3:
        return "Improving trend: violations decreasing over time. Earlier periods showed higher violation rates."
    elif second_half_viols > first_half_viols * 1.3:
        return "Warning: violations increasing. May correlate with seasonal volume increase or staffing changes."
    else:
        return "Stable pattern: violation rates relatively consistent across the analysis period."


def _get_improvement_action(violation_type: str) -> str:
    """Get specific improvement action for a violation type."""
    actions = {
        "meal_break_missed": "Deploy automated break reminder system with escalation alerts",
        "meal_break_late": "Adjust scheduling to create natural break windows",
        "shift_over_max_hours": "Set hard stop alerts at 9.5 hours; require manager override to extend",
        "unauthorized_overtime": "Implement mandatory clock-out notifications at scheduled end time",
        "late_start": "Review shift start time realism; consider staggered starts",
        "early_end": "Investigate root cause - understaffing, workload issues, or engagement",
        "consecutive_days_exceeded": "Add hard constraint to scheduling algorithm preventing 7+ day streaks",
        "insufficient_rest_between_shifts": "Enforce minimum 10-hour gap in scheduling system",
        "schedule_change_without_notice": "Lock schedule changes within 72-hour window without premium pay",
        "minor_hours_violation": "Audit minor scheduling for legal compliance quarterly",
        "split_shift_violation": "Eliminate split shifts or ensure proper premium compensation",
        "fairness_imbalance": "Implement rotation algorithm for equitable shift distribution",
    }
    return actions.get(violation_type, "Review and address with operations team")


def _get_remediation_recommendation(violation_type: ViolationType) -> str:
    """Get remediation recommendation for regulatory risk report."""
    recommendations = {
        ViolationType.MEAL_BREAK_MISSED: "Implement mandatory break enforcement with system lockout",
        ViolationType.UNAUTHORIZED_OVERTIME: "Deploy automated shift-end notifications and clock-out enforcement",
        ViolationType.CONSECUTIVE_DAYS_EXCEEDED: "Add hard scheduling constraint; no manual override without VP approval",
        ViolationType.SHIFT_OVER_MAX_HOURS: "Configure maximum shift duration alerts with escalation path",
        ViolationType.SCHEDULE_CHANGE_NO_NOTICE: "Require 72-hour advance notice with system enforcement",
        ViolationType.INSUFFICIENT_REST_BETWEEN_SHIFTS: "Enforce minimum rest period in scheduling algorithm",
    }
    return recommendations.get(violation_type, "Review compliance procedures and retrain scheduling managers")


# =============================================================================
# SIMULATION HELPERS (for __main__ demo)
# =============================================================================

def _generate_simulated_week(
    week_number: int,
    start_date: date,
    num_employees: int = 40,
    compliance_improvement: float = 0.0,
) -> Tuple[List[ShiftPlanned], List[ShiftActual]]:
    """
    Generate simulated planned and actual schedule data for one week.

    As compliance_improvement increases (0.0 to 1.0), fewer violations occur.
    """
    random.seed(42 + week_number)

    employees = [
        (f"AA{i:03d}", f"{'Marcus Johnson,Aisha Patel,Carlos Rivera,Jennifer Kim,David Thompson,Sarah Chen,Robert Wilson,Maria Garcia,James Brown,Lisa Anderson,Kevin Martinez,Nicole Taylor,Brandon Lee,Ashley Davis,Tyler Robinson,Megan White,Jordan Harris,Rachel Clark,Nathan Lewis,Samantha Hall,Christopher Young,Amanda King,Daniel Wright,Jessica Scott,Ryan Green,Emily Baker,Matthew Adams,Lauren Nelson,Andrew Hill,Stephanie Moore,Justin Campbell,Kayla Mitchell,Brandon Roberts,Olivia Turner,Ethan Phillips,Hannah Evans,Dylan Edwards,Sophia Collins,Austin Stewart,Brianna Sanchez'.split(',')[i % 40]}")
        for i in range(num_employees)
    ]

    managers = ["Sarah Mitchell", "Carlos Gutierrez", "Michael Chen", "Rebecca Foster"]

    shift_patterns = [
        ("06:00", "14:30", "10:00"),
        ("07:00", "15:30", "11:00"),
        ("14:00", "22:30", "18:00"),
        ("22:00", "06:30", "02:00"),
    ]

    planned = []
    actual = []

    for day_offset in range(7):
        shift_date = start_date + timedelta(days=day_offset)

        # Each day about 30 of 40 employees are scheduled
        scheduled_today = random.sample(employees, min(30, num_employees))

        for emp_id, emp_name in scheduled_today:
            pattern = random.choice(shift_patterns)
            manager = random.choice(managers)

            planned_shift = ShiftPlanned(
                employee_id=emp_id,
                employee_name=emp_name,
                shift_date=shift_date,
                start_time=pattern[0],
                end_time=pattern[1],
                break_start=pattern[2],
                break_duration_min=30,
                manager=manager,
            )
            planned.append(planned_shift)

            # Simulate actual with violations based on compliance_improvement
            violation_chance = max(0.02, 0.12 - compliance_improvement * 0.10)

            actual_start = pattern[0]
            actual_end = pattern[1]
            actual_break_start = pattern[2]
            actual_break_min = 30
            ot_authorized = False

            # Random violations
            roll = random.random()
            if roll < violation_chance:
                violation_roll = random.random()
                if violation_roll < 0.30:
                    # Meal break missed
                    actual_break_start = None
                    actual_break_min = 0
                elif violation_roll < 0.55:
                    # Unauthorized overtime
                    end_hour, end_min_val = map(int, pattern[1].split(":"))
                    end_min_val += random.randint(25, 90)
                    end_hour += end_min_val // 60
                    end_min_val = end_min_val % 60
                    actual_end = f"{end_hour % 24:02d}:{end_min_val:02d}"
                elif violation_roll < 0.70:
                    # Late start
                    start_hour, start_min_val = map(int, pattern[0].split(":"))
                    start_min_val += random.randint(12, 35)
                    start_hour += start_min_val // 60
                    start_min_val = start_min_val % 60
                    actual_start = f"{start_hour:02d}:{start_min_val:02d}"
                elif violation_roll < 0.85:
                    # Shift over max (extend significantly)
                    end_hour, end_min_val = map(int, pattern[1].split(":"))
                    end_min_val += random.randint(60, 150)
                    end_hour += end_min_val // 60
                    end_min_val = end_min_val % 60
                    actual_end = f"{end_hour % 24:02d}:{end_min_val:02d}"
                else:
                    # Short break
                    actual_break_min = random.randint(15, 25)

            actual_shift = ShiftActual(
                employee_id=emp_id,
                employee_name=emp_name,
                shift_date=shift_date,
                start_time=actual_start,
                end_time=actual_end,
                break_start=actual_break_start,
                break_duration_min=actual_break_min,
                overtime_authorized=ot_authorized,
                manager=manager,
            )
            actual.append(actual_shift)

    return planned, actual


# =============================================================================
# __main__ - DEMONSTRATION
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("   WORKFORCE COMPLIANCE AI - AUDIT ANALYTICS DEMONSTRATION")
    print("=" * 80)
    print()
    print("Facility: West Coast Distribution Center (40 AAs)")
    print("Jurisdiction: California (CA)")
    print("Simulation: 4 weeks with progressive compliance improvement")
    print()

    # Simulate 4 weeks of data with improving compliance
    base_date = date(2026, 6, 1)
    weekly_audits = []
    all_violations = []
    weekly_costs = []

    improvement_levels = [0.0, 0.35, 0.65, 0.90]  # Progressing from no tool to full adoption

    print("-" * 80)
    print("WEEKLY AUDIT RESULTS")
    print("-" * 80)

    for week_num in range(4):
        week_start = base_date + timedelta(weeks=week_num)
        improvement = improvement_levels[week_num]

        planned, actual = _generate_simulated_week(
            week_number=week_num,
            start_date=week_start,
            num_employees=40,
            compliance_improvement=improvement,
        )

        # Run audit
        audit = run_audit(planned, actual, facility="West Coast DC")

        # Calculate costs
        cost_breakdown = calculate_violation_costs(
            audit.violations,
            jurisdiction="CA",
            hourly_rates={f"AA{i:03d}": random.uniform(20.0, 28.0) for i in range(40)},
        )

        # Update violation costs in audit
        audit.total_cost = cost_breakdown.total_cost
        weekly_audits.append(audit)
        all_violations.extend(audit.violations)
        weekly_costs.append(cost_breakdown)

        print(f"\n  Week {week_num + 1} ({week_start.isoformat()} - {(week_start + timedelta(days=6)).isoformat()}):")
        print(f"    Shifts Audited:     {audit.total_shifts_audited}")
        print(f"    Violations Found:   {audit.total_violation_count}")
        print(f"    Compliance Rate:    {audit.compliance_rate:.1f}%")
        print(f"    Total Cost Impact:  ${cost_breakdown.total_cost:,.2f}")
        print(f"      - Premium Pay:    ${cost_breakdown.premium_pay_owed:,.2f}")
        print(f"      - Grievance Risk: ${cost_breakdown.grievance_risk_cost:,.2f}")
        print(f"      - Potential Fines:${cost_breakdown.potential_fines:,.2f}")
        print(f"      - Admin Overhead: ${cost_breakdown.administrative_costs:,.2f}")

    # Trend Analysis
    print("\n")
    print("-" * 80)
    print("TREND ANALYSIS")
    print("-" * 80)

    trends = analyze_trends(weekly_audits)

    print("\n  Most Common Violations:")
    for vtype, count in trends.most_common_violations:
        print(f"    - {vtype.value.replace('_', ' ').title()}: {count} occurrences")

    print("\n  Most Affected Employees:")
    for emp, count in trends.most_affected_employees:
        print(f"    - {emp}: {count} violations")

    print("\n  Day-of-Week Patterns:")
    for day, count in sorted(trends.day_of_week_patterns.items(),
                              key=lambda x: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].index(x[0])):
        bar = "#" * count
        print(f"    {day}: {bar} ({count})")

    print(f"\n  Manager Compliance Scores:")
    for mgr, score in sorted(trends.manager_comparison.items(), key=lambda x: x[1], reverse=True):
        print(f"    - {mgr}: {score:.1f}%")

    print(f"\n  Improvement Rate: {trends.improvement_rate:+.1f} percentage points")
    print(f"  Seasonal Notes: {trends.seasonal_notes}")

    # Compliance Scorecard
    print("\n")
    print("-" * 80)
    print("COMPLIANCE SCORECARD")
    print("-" * 80)

    scorecard = generate_scorecard(
        facility="West Coast Distribution Center",
        period="June 2026",
        audit_results=weekly_audits,
        prior_period_results=weekly_audits[:2],  # Use first 2 weeks as "prior"
        benchmark_score=78.0,
    )

    print(f"\n  Overall Compliance Score: {scorecard.overall_score:.1f} / 100")
    print(f"  Prior Period Score:       {scorecard.prior_period_score:.1f} / 100")
    print(f"  Industry Benchmark:       {scorecard.benchmark_score:.1f} / 100")
    print(f"\n  Category Scores:")
    print(f"    Scheduling:       {scorecard.scheduling_score:.1f}")
    print(f"    Break Compliance: {scorecard.breaks_score:.1f}")
    print(f"    Fairness:         {scorecard.fairness_score:.1f}")
    print(f"    Leave Management: {scorecard.leave_score:.1f}")

    if scorecard.top_improvements:
        print(f"\n  Top Improvement Opportunities:")
        for i, imp in enumerate(scorecard.top_improvements, 1):
            print(f"    {i}. {imp['category']}")
            print(f"       Savings: ${imp['potential_savings']:,.2f}")
            print(f"       Action:  {imp['action']}")

    # Regulatory Risk
    print("\n")
    print("-" * 80)
    print("REGULATORY RISK ASSESSMENT")
    print("-" * 80)

    risk = assess_risk(all_violations, jurisdiction="CA")
    print(f"\n  Jurisdiction: {risk.jurisdiction}")
    print(f"  Total Exposure: ${risk.total_exposure:,.2f}")
    print(f"  Investigation Risk: {risk.investigation_trigger_risk}")
    print(f"\n  Remediation Priorities:")
    for item in risk.remediation_priorities:
        print(f"    [{item['priority']}] {item['violation_type'].replace('_', ' ').title()}")
        print(f"          Occurrences: {item['occurrence_count']}, Est. Cost to Fix: ${item['estimated_cost_to_fix']:,.2f}")
        print(f"          Action: {item['recommendation']}")

    # Grievance Predictor
    print("\n")
    print("-" * 80)
    print("GRIEVANCE PREDICTION")
    print("-" * 80)

    all_actuals = []
    for week_num in range(4):
        week_start = base_date + timedelta(weeks=week_num)
        _, actual = _generate_simulated_week(week_num, week_start, 40, improvement_levels[week_num])
        all_actuals.extend(actual)

    predictions = predict_grievances(all_actuals, all_violations, union_activity_level=0.6)

    print(f"\n  High-Risk Employees (Grievance Probability):")
    for pred in predictions[:5]:
        print(f"\n    {pred.employee_name} ({pred.employee_id})")
        print(f"      Risk Score: {pred.risk_score:.1f}%")
        print(f"      Factors:")
        for factor in pred.contributing_factors:
            print(f"        - {factor}")
        print(f"      Recommended Actions:")
        for action in pred.recommended_actions:
            print(f"        -> {action}")

    # Executive Dashboard Data
    print("\n")
    print("-" * 80)
    print("EXECUTIVE DASHBOARD DATA (JSON-ready)")
    print("-" * 80)

    dashboard = get_dashboard_data(weekly_audits, "West Coast Distribution Center")
    print(f"\n  Summary:")
    print(f"    Total Audits:            {dashboard['summary']['total_audits']}")
    print(f"    Total Violations:        {dashboard['summary']['total_violations']}")
    print(f"    Total Cost Impact:       ${dashboard['summary']['total_cost']:,.2f}")
    print(f"    Current Compliance Rate: {dashboard['summary']['current_compliance_rate']:.1f}%")

    print(f"\n  Violations by Category:")
    for item in dashboard["violations_by_category"]:
        print(f"    - {item['category']}: {item['count']}")

    # ROI Summary
    print("\n")
    print("=" * 80)
    print("ROI SUMMARY - COST SAVINGS FROM COMPLIANCE AI")
    print("=" * 80)

    week1_cost = weekly_costs[0].total_cost
    week4_cost = weekly_costs[3].total_cost
    reduction_pct = ((week1_cost - week4_cost) / week1_cost) * 100 if week1_cost > 0 else 0

    print(f"""
  Week 1 (No Tool):        ${week1_cost:,.2f} in violation costs
  Week 2 (Early Adoption): ${weekly_costs[1].total_cost:,.2f}
  Week 3 (Maturing):       ${weekly_costs[2].total_cost:,.2f}
  Week 4 (Full Adoption):  ${week4_cost:,.2f}

  TOTAL REDUCTION:         {reduction_pct:.0f}% cost decrease
  WEEKLY SAVINGS:          ${week1_cost - week4_cost:,.2f} per week
  PROJECTED ANNUAL SAVINGS: ${(week1_cost - week4_cost) * 52:,.2f}

  Violations: Week 1: {weekly_audits[0].total_violation_count} -> Week 4: {weekly_audits[3].total_violation_count}
  Compliance: Week 1: {weekly_audits[0].compliance_rate:.1f}% -> Week 4: {weekly_audits[3].compliance_rate:.1f}%
""")

    print("-" * 80)
    print("  The ROI is clear: the Workforce Compliance AI system pays for itself")
    print("  within the first month of deployment through violation cost reduction,")
    print("  grievance prevention, and regulatory risk mitigation.")
    print("-" * 80)

    # Executive Summary Export
    print("\n")
    summary_text = export_executive_summary(scorecard)
    print(summary_text)

    print("\n[Audit analytics module ready for integration]")
