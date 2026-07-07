"""
ShiftGuard - Database Layer
SQLite for local/dev, PostgreSQL for production.
All schedules, employees, requests, and leave balances persist across sessions.

Setup:
- Local: Works out of the box (SQLite file in ./data/)
- Production: Set DATABASE_URL env var to PostgreSQL connection string

Required pip: sqlalchemy
"""

import os
from datetime import datetime
from contextlib import contextmanager

try:
    from sqlalchemy import (
        create_engine, Column, String, Integer, Float, Boolean, DateTime,
        Text, ForeignKey, JSON, Index
    )
    from sqlalchemy.orm import declarative_base, sessionmaker, relationship
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/shiftguard.db")

Base = declarative_base() if SQLALCHEMY_AVAILABLE else None

if SQLALCHEMY_AVAILABLE:

    class Tenant(Base):
        __tablename__ = "tenants"
        id = Column(String(50), primary_key=True)
        name = Column(String(200), nullable=False)
        industry = Column(String(50))
        state = Column(String(50))
        timezone = Column(String(50), default="America/Chicago")
        settings = Column(JSON, default={})
        created_at = Column(DateTime, default=datetime.utcnow)

    class Employee(Base):
        __tablename__ = "employees"
        id = Column(String(50), primary_key=True)
        tenant_id = Column(String(50), ForeignKey("tenants.id"), nullable=False)
        name = Column(String(200), nullable=False)
        email = Column(String(200))
        role = Column(String(100))
        department = Column(String(100))
        shift_code = Column(String(20))
        hire_date = Column(DateTime)
        hourly_rate = Column(Float)
        seniority = Column(Integer, default=1)
        certifications = Column(JSON, default=[])
        is_active = Column(Boolean, default=True)
        created_at = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (Index("idx_employee_tenant", "tenant_id"),)

    class Shift(Base):
        __tablename__ = "shifts"
        id = Column(Integer, primary_key=True, autoincrement=True)
        tenant_id = Column(String(50), ForeignKey("tenants.id"), nullable=False)
        employee_id = Column(String(50), ForeignKey("employees.id"), nullable=False)
        date = Column(String(10), nullable=False)
        start = Column(String(5), nullable=False)
        end = Column(String(5), nullable=False)
        role = Column(String(100))
        shift_type = Column(String(50))
        status = Column(String(20), default="scheduled")  # scheduled, worked, missed, swapped
        created_at = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (
            Index("idx_shift_employee_date", "employee_id", "date"),
            Index("idx_shift_tenant_date", "tenant_id", "date"),
        )

    class LeaveBalance(Base):
        __tablename__ = "leave_balances"
        id = Column(Integer, primary_key=True, autoincrement=True)
        tenant_id = Column(String(50), ForeignKey("tenants.id"), nullable=False)
        employee_id = Column(String(50), ForeignKey("employees.id"), nullable=False)
        balance_type = Column(String(20), nullable=False)  # PTO, SICK, UPT, FMLA
        available_hours = Column(Float, default=0)
        used_hours = Column(Float, default=0)
        accrual_rate = Column(Float, default=0)
        cap_hours = Column(Float)
        updated_at = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (Index("idx_balance_employee", "employee_id", "balance_type"),)

    class Request(Base):
        __tablename__ = "requests"
        id = Column(Integer, primary_key=True, autoincrement=True)
        tenant_id = Column(String(50), ForeignKey("tenants.id"), nullable=False)
        employee_id = Column(String(50), ForeignKey("employees.id"), nullable=False)
        request_type = Column(String(30), nullable=False)  # HOLIDAY, SHIFT_SWAP, VET, SICK
        start_date = Column(String(10))
        end_date = Column(String(10))
        priority = Column(Integer, default=1)
        reason = Column(Text)
        status = Column(String(20), default="PENDING")
        decided_by = Column(String(50))
        decided_at = Column(DateTime)
        auto_approval_result = Column(JSON)
        created_at = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (Index("idx_request_employee", "employee_id", "status"),)

    class AuditLog(Base):
        __tablename__ = "audit_log"
        id = Column(Integer, primary_key=True, autoincrement=True)
        tenant_id = Column(String(50), ForeignKey("tenants.id"), nullable=False)
        action = Column(String(100), nullable=False)
        actor_id = Column(String(50))
        target_id = Column(String(50))
        details = Column(JSON)
        timestamp = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (Index("idx_audit_tenant_time", "tenant_id", "timestamp"),)

    class ComplianceViolation(Base):
        __tablename__ = "compliance_violations"
        id = Column(Integer, primary_key=True, autoincrement=True)
        tenant_id = Column(String(50), ForeignKey("tenants.id"), nullable=False)
        schedule_date = Column(String(10))
        rule_id = Column(String(30))
        rule_name = Column(String(200))
        severity = Column(String(10))
        employee_id = Column(String(50))
        description = Column(Text)
        recommendation = Column(Text)
        penalty_estimate = Column(Float)
        status = Column(String(20), default="OPEN")  # OPEN, RESOLVED, ACCEPTED_RISK
        resolved_by = Column(String(50))
        resolved_at = Column(DateTime)
        detected_at = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (Index("idx_violation_tenant_status", "tenant_id", "status"),)


class Database:
    """Database connection and operations."""

    def __init__(self, url=None):
        self.url = url or DATABASE_URL
        self.engine = None
        self.Session = None

    def initialize(self):
        """Create engine, tables, and session factory."""
        if not SQLALCHEMY_AVAILABLE:
            return {"success": False, "error": "SQLAlchemy not installed. Run: pip install sqlalchemy"}

        # Create data directory for SQLite
        if "sqlite" in self.url:
            os.makedirs("data", exist_ok=True)

        self.engine = create_engine(self.url, echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        return {"success": True, "url": self.url, "tables_created": len(Base.metadata.tables)}

    @contextmanager
    def session(self):
        """Context manager for database sessions."""
        s = self.Session()
        try:
            yield s
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()

    # --- Tenant Operations ---

    def create_tenant(self, tenant_id, name, industry, state="Illinois"):
        """Create a new organization/tenant."""
        with self.session() as s:
            tenant = Tenant(id=tenant_id, name=name, industry=industry, state=state)
            s.add(tenant)
            return {"id": tenant_id, "name": name}

    # --- Employee Operations ---

    def add_employee(self, tenant_id, employee_id, name, role, department=None,
                     shift_code=None, hire_date=None, hourly_rate=None):
        """Add an employee to a tenant."""
        with self.session() as s:
            emp = Employee(
                id=employee_id, tenant_id=tenant_id, name=name, role=role,
                department=department, shift_code=shift_code,
                hire_date=hire_date, hourly_rate=hourly_rate,
            )
            s.add(emp)
            return {"id": employee_id, "name": name}

    def get_employees(self, tenant_id):
        """Get all active employees for a tenant."""
        with self.session() as s:
            employees = s.query(Employee).filter(
                Employee.tenant_id == tenant_id,
                Employee.is_active == True,
            ).all()
            return [{
                "id": e.id, "name": e.name, "role": e.role,
                "department": e.department, "shift_code": e.shift_code,
                "hire_date": e.hire_date.strftime("%Y-%m-%d") if e.hire_date else None,
                "seniority": e.seniority,
            } for e in employees]

    # --- Schedule Operations ---

    def import_shifts(self, tenant_id, shifts):
        """Bulk import shifts from CSV/API/Sheets data."""
        with self.session() as s:
            count = 0
            for shift_data in shifts:
                shift = Shift(
                    tenant_id=tenant_id,
                    employee_id=shift_data.get("employee_id"),
                    date=shift_data.get("date"),
                    start=shift_data.get("start"),
                    end=shift_data.get("end"),
                    role=shift_data.get("role", ""),
                    shift_type=shift_data.get("shift_type", ""),
                )
                s.add(shift)
                count += 1
            return {"imported": count}

    def get_schedule(self, tenant_id, start_date, end_date):
        """Get schedule for a date range in ShiftGuard format."""
        with self.session() as s:
            shifts = s.query(Shift).filter(
                Shift.tenant_id == tenant_id,
                Shift.date >= start_date,
                Shift.date <= end_date,
            ).all()

            shift_list = [{
                "employee_id": sh.employee_id,
                "date": sh.date,
                "start": sh.start,
                "end": sh.end,
                "role": sh.role,
                "shift_type": sh.shift_type,
            } for sh in shifts]

            # Join employee names
            employees = {e.id: e.name for e in s.query(Employee).filter(
                Employee.tenant_id == tenant_id).all()}
            for shift in shift_list:
                shift["name"] = employees.get(shift["employee_id"], shift["employee_id"])

            return {
                "schedule_posted_date": datetime.now().strftime("%Y-%m-%d"),
                "week_start": start_date,
                "week_end": end_date,
                "facility": f"Database ({tenant_id})",
                "shifts": shift_list,
                "source": "database",
            }

    # --- Request Operations ---

    def create_request(self, tenant_id, employee_id, request_type, start_date,
                       end_date=None, priority=1, reason=""):
        """Create a time-off/swap request."""
        with self.session() as s:
            req = Request(
                tenant_id=tenant_id, employee_id=employee_id,
                request_type=request_type, start_date=start_date,
                end_date=end_date or start_date, priority=priority, reason=reason,
            )
            s.add(req)
            s.flush()
            return {"id": req.id, "status": req.status}

    # --- Audit Operations ---

    def log_action(self, tenant_id, action, actor_id=None, target_id=None, details=None):
        """Log an action to the audit trail."""
        with self.session() as s:
            log = AuditLog(
                tenant_id=tenant_id, action=action,
                actor_id=actor_id, target_id=target_id, details=details,
            )
            s.add(log)

    def log_violation(self, tenant_id, violation_data):
        """Store a detected compliance violation."""
        with self.session() as s:
            v = ComplianceViolation(
                tenant_id=tenant_id,
                schedule_date=violation_data.get("date"),
                rule_id=violation_data.get("rule_id"),
                rule_name=violation_data.get("rule_name"),
                severity=violation_data.get("severity"),
                employee_id=violation_data.get("employee_id"),
                description=violation_data.get("description"),
                recommendation=violation_data.get("recommendation"),
                penalty_estimate=violation_data.get("penalty", 0),
            )
            s.add(v)


def get_database(url=None):
    """Get or create database instance."""
    db = Database(url)
    result = db.initialize()
    if result["success"]:
        return db
    return None
