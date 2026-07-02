"""
Workforce Compliance AI - Database Schema
All domain objects as SQLAlchemy models with full tenant isolation.
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date, Time,
    ForeignKey, Text, JSON, Enum, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from .database import Base


# ============================================================
# ENUMS
# ============================================================

class UserRole(enum.Enum):
    WORKER = "WORKER"
    MANAGER = "MANAGER"
    HR = "HR"
    ADMIN = "ADMIN"


class LeaveType(enum.Enum):
    PTO = "PTO"
    SICK_PLANNED = "SICK_PLANNED"
    SICK_UNPLANNED = "SICK_UNPLANNED"
    FMLA = "FMLA"
    FMLA_INTERMITTENT = "FMLA_INTERMITTENT"
    BEREAVEMENT = "BEREAVEMENT"
    JURY_DUTY = "JURY_DUTY"
    MILITARY = "MILITARY"
    MATERNITY = "MATERNITY"
    SHORT_TERM_DISABILITY = "SHORT_TERM_DISABILITY"
    WORKERS_COMP = "WORKERS_COMP"
    PERSONAL_UNPAID = "PERSONAL_UNPAID"
    RELIGIOUS = "RELIGIOUS"
    VOTING = "VOTING"
    UPT = "UPT"


class RequestStatus(enum.Enum):
    PENDING = "PENDING"
    AUTO_APPROVED = "AUTO_APPROVED"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    ESCALATED = "ESCALATED"
    WITHDRAWN = "WITHDRAWN"


class RequestType(enum.Enum):
    HOLIDAY = "HOLIDAY"
    SHIFT_SWAP = "SHIFT_SWAP"
    VET_ACCEPT = "VET_ACCEPT"
    VET_DECLINE = "VET_DECLINE"
    OPEN_SHIFT = "OPEN_SHIFT"
    PREFERENCE = "PREFERENCE"


class ShiftType(enum.Enum):
    DAY = "DAY"
    EVENING = "EVENING"
    NIGHT = "NIGHT"


class AlertSeverity(enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ============================================================
# CORE TABLES
# ============================================================

class Tenant(Base):
    """Organization / Company — top-level isolation boundary."""
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    industry = Column(String(100))  # healthcare, warehouse, retail, etc.
    state = Column(String(50), nullable=False)  # primary jurisdiction
    timezone = Column(String(50), default="America/Chicago")
    plan = Column(String(50), default="starter")  # starter, professional, enterprise
    max_employees = Column(Integer, default=500)
    settings = Column(JSON, default={})  # tenant-specific configs
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    employees = relationship("Employee", back_populates="tenant")
    users = relationship("User", back_populates="tenant")


class User(Base):
    """Authentication user — can be linked to an employee or standalone (HR/Admin)."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    email = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.WORKER)
    employee_id = Column(String(36), ForeignKey("employees.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    tenant = relationship("Tenant", back_populates="users")
    employee = relationship("Employee", back_populates="user")

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_user_email_per_tenant"),
    )


class Employee(Base):
    """Employee / Associate / Worker."""
    __tablename__ = "employees"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    employee_code = Column(String(50))  # external ID (e.g., Amazon login)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255))
    phone = Column(String(20))
    hire_date = Column(Date, nullable=False)
    department = Column(String(100))
    role = Column(String(100))  # Pick, Pack, Stow, RN, Resident, etc.
    seniority = Column(Integer, default=0)
    hourly_rate = Column(Float)
    is_minor = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    manager_id = Column(String(36), ForeignKey("employees.id"), nullable=True)
    shift_code = Column(String(50))  # assigned fixed shift template
    certifications = Column(JSON, default=[])
    preferences = Column(JSON, default={})
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="employees")
    user = relationship("User", back_populates="employee", uselist=False)
    manager = relationship("Employee", remote_side=[id])
    leave_balances = relationship("LeaveBalance", back_populates="employee")
    leave_records = relationship("LeaveRecord", back_populates="employee")
    shifts = relationship("ShiftAssignment", back_populates="employee")

    __table_args__ = (
        Index("ix_employee_tenant", "tenant_id"),
        Index("ix_employee_dept", "tenant_id", "department"),
        Index("ix_employee_shift_code", "tenant_id", "shift_code"),
    )


# ============================================================
# SCHEDULING TABLES
# ============================================================

class ShiftTemplate(Base):
    """Fixed shift code definition (e.g., DA5-0700-IB)."""
    __tablename__ = "shift_templates"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    code = Column(String(50), nullable=False)  # DA5-0700-IB
    department = Column(String(100))
    start_time = Column(Time)
    schedule_type = Column(String(50))  # front_half, back_half, etc.
    pattern = Column(JSON, nullable=False)  # day->hours mapping
    weekly_hours = Column(Float)
    days_on = Column(JSON)  # ["Sun", "Mon", "Tue", "Wed"]
    days_off = Column(JSON)  # ["Thu", "Fri", "Sat"]
    is_baseline = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_shift_code_per_tenant"),
    )


class ShiftAssignment(Base):
    """Actual shift instance — a specific employee working a specific shift on a specific date."""
    __tablename__ = "shift_assignments"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    employee_id = Column(String(36), ForeignKey("employees.id"), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    hours = Column(Float, nullable=False)
    shift_type = Column(Enum(ShiftType))
    shift_template_code = Column(String(50))
    is_overtime = Column(Boolean, default=False)
    is_holiday = Column(Boolean, default=False)
    is_vet = Column(Boolean, default=False)
    is_met = Column(Boolean, default=False)
    pay_multiplier = Column(Float, default=1.0)
    status = Column(String(20), default="SCHEDULED")  # SCHEDULED, COMPLETED, CANCELLED, NO_SHOW
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    employee = relationship("Employee", back_populates="shifts")

    __table_args__ = (
        Index("ix_shift_date", "tenant_id", "date"),
        Index("ix_shift_employee_date", "tenant_id", "employee_id", "date"),
    )


# ============================================================
# LEAVE MANAGEMENT TABLES
# ============================================================

class LeaveBalance(Base):
    """Current leave balance per employee per type."""
    __tablename__ = "leave_balances"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    employee_id = Column(String(36), ForeignKey("employees.id"), nullable=False)
    leave_type = Column(String(30), nullable=False)  # PTO, SICK, UPT, FMLA, FLEX_PTO
    available_hours = Column(Float, default=0)
    used_hours = Column(Float, default=0)
    pending_hours = Column(Float, default=0)
    accrual_rate = Column(Float, default=0)  # hours per period
    cap_hours = Column(Float, nullable=True)
    carryover_cap = Column(Float, nullable=True)
    year = Column(Integer, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    employee = relationship("Employee", back_populates="leave_balances")

    __table_args__ = (
        UniqueConstraint("tenant_id", "employee_id", "leave_type", "year",
                        name="uq_balance_per_type_year"),
        Index("ix_balance_employee", "tenant_id", "employee_id"),
    )


class LeaveRecord(Base):
    """Individual leave event (PTO taken, sick day, FMLA period, etc.)."""
    __tablename__ = "leave_records"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    employee_id = Column(String(36), ForeignKey("employees.id"), nullable=False)
    leave_type = Column(Enum(LeaveType), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    hours = Column(Float, nullable=False)
    reason = Column(Text)
    status = Column(String(20), default="ACTIVE")  # ACTIVE, COMPLETED, CANCELLED
    is_protected = Column(Boolean, default=False)
    protected_type = Column(String(50))  # RELIGIOUS, ADA, FMLA, etc.
    documentation_status = Column(String(20), default="NOT_REQUIRED")
    documentation_due = Column(Date)
    return_clearance_required = Column(Boolean, default=False)
    return_clearance_received = Column(Boolean, default=False)
    approved_by = Column(String(36))
    approved_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    employee = relationship("Employee", back_populates="leave_records")

    __table_args__ = (
        Index("ix_leave_employee_date", "tenant_id", "employee_id", "start_date"),
        Index("ix_leave_type", "tenant_id", "leave_type"),
    )


# ============================================================
# REQUESTS & APPROVALS
# ============================================================

class Request(Base):
    """Worker request (time-off, swap, VET, etc.)."""
    __tablename__ = "requests"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    employee_id = Column(String(36), ForeignKey("employees.id"), nullable=False)
    request_type = Column(Enum(RequestType), nullable=False)
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING)
    priority = Column(Integer, default=1)
    start_date = Column(Date)
    end_date = Column(Date)
    hours = Column(Float)
    reason = Column(Text)
    is_flexible = Column(Boolean, default=False)
    target_employee_id = Column(String(36), ForeignKey("employees.id"), nullable=True)
    auto_approval_checks = Column(JSON)
    manager_notes = Column(Text)
    alternatives_suggested = Column(JSON)
    resolved_by = Column(String(36))
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_request_employee", "tenant_id", "employee_id"),
        Index("ix_request_status", "tenant_id", "status"),
    )


# ============================================================
# AUDIT & COMPLIANCE
# ============================================================

class AuditLog(Base):
    """Immutable audit trail for all automated decisions."""
    __tablename__ = "audit_log"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    decision_type = Column(String(100), nullable=False)
    employee_id = Column(String(36))
    actor_id = Column(String(36))  # who/what made the decision
    actor_type = Column(String(20))  # SYSTEM, MANAGER, HR, ADMIN
    outcome = Column(String(50), nullable=False)
    explanation = Column(Text, nullable=False)
    factors = Column(JSON)
    is_overridden = Column(Boolean, default=False)
    override_by = Column(String(36))
    override_reason = Column(Text)
    override_at = Column(DateTime)
    is_protected_decision = Column(Boolean, default=False)
    legal_basis = Column(String(200))

    __table_args__ = (
        Index("ix_audit_tenant_time", "tenant_id", "timestamp"),
        Index("ix_audit_employee", "tenant_id", "employee_id"),
        Index("ix_audit_type", "tenant_id", "decision_type"),
    )


class ComplianceViolation(Base):
    """Detected compliance violation."""
    __tablename__ = "compliance_violations"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    rule_id = Column(String(50), nullable=False)
    rule_name = Column(String(200))
    severity = Column(Enum(AlertSeverity), nullable=False)
    description = Column(Text)
    employee_id = Column(String(36), ForeignKey("employees.id"))
    shift_date = Column(Date)
    cost_impact = Column(Text)
    recommendation = Column(Text)
    status = Column(String(20), default="OPEN")  # OPEN, RESOLVED, ACCEPTED_RISK
    resolved_by = Column(String(36))
    resolved_at = Column(DateTime)
    detected_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_violation_tenant_status", "tenant_id", "status"),
    )


class BiasAuditReport(Base):
    """Bias audit results (NYC LL144 compliance)."""
    __tablename__ = "bias_audit_reports"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    audit_period_start = Column(Date, nullable=False)
    audit_period_end = Column(Date, nullable=False)
    overall_status = Column(String(20))  # PASS, WARNING, FAIL
    methodology = Column(Text)
    findings = Column(JSON)
    recommendations = Column(JSON)
    category_results = Column(JSON)
    generated_at = Column(DateTime, server_default=func.now())
    reviewed_by = Column(String(36))
    reviewed_at = Column(DateTime)


# ============================================================
# HOLIDAY AUCTION
# ============================================================

class HolidayAuctionRound(Base):
    """A holiday auction round (typically annual)."""
    __tablename__ = "holiday_auction_rounds"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    year = Column(Integer, nullable=False)
    status = Column(String(20), default="COLLECTING")  # COLLECTING, ALLOCATED, FINALIZED
    max_off_per_period = Column(Integer, default=2)
    submission_deadline = Column(DateTime)
    allocation_run_at = Column(DateTime)
    results = Column(JSON)
    fairness_scorecard = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())


class HolidayPreference(Base):
    """Worker's holiday preference submission for the auction."""
    __tablename__ = "holiday_preferences"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    auction_id = Column(String(36), ForeignKey("holiday_auction_rounds.id"), nullable=False)
    employee_id = Column(String(36), ForeignKey("employees.id"), nullable=False)
    period_name = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    priority = Column(Integer, nullable=False)
    reason = Column(Text)
    is_flexible = Column(Boolean, default=False)
    outcome = Column(String(20))  # GRANTED, DENIED, COMPENSATED
    outcome_reason = Column(Text)
    submitted_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("auction_id", "employee_id", "priority",
                        name="uq_preference_per_priority"),
    )


# ============================================================
# DONATIONS
# ============================================================

class LeaveDonation(Base):
    """PTO/leave donation record."""
    __tablename__ = "leave_donations"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    donor_id = Column(String(36), ForeignKey("employees.id"), nullable=False)
    recipient_id = Column(String(36), ForeignKey("employees.id"), nullable=False)
    leave_type = Column(String(30), nullable=False)
    hours = Column(Float, nullable=False)
    reason = Column(Text)
    status = Column(String(20), default="COMPLETED")
    tax_noted = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("hours > 0", name="ck_donation_positive"),
    )


# ============================================================
# ALERTS & NOTIFICATIONS
# ============================================================

class Alert(Base):
    """System alert (FMLA trigger, pattern detection, UPT zero, etc.)."""
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    alert_type = Column(String(50), nullable=False)
    severity = Column(Enum(AlertSeverity), nullable=False)
    employee_id = Column(String(36), ForeignKey("employees.id"))
    message = Column(Text, nullable=False)
    action_required = Column(Text)
    deadline = Column(Date)
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(String(36))
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_alert_tenant_unresolved", "tenant_id", "is_resolved"),
    )
