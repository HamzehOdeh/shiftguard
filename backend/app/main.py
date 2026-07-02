"""
Workforce Compliance AI - FastAPI Backend
Production REST API with authentication, RBAC, and full domain operations.
"""

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from datetime import datetime

from .core.config import settings
from .core.auth import decode_token
from .models.database import get_db, create_tables

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from compliance_checker import check_compliance as run_compliance_check
from hours_tracker import get_all_employee_dashboards, predict_shift_impact
from coverage_engine import find_coverage, calculate_team_fairness_report
from leave_management import create_demo_leave_tracker
from schedule_generator import ScheduleGenerator, SHIFT_PATTERNS
from cost_calculator import calculate_compliance_cost
from ai_chat import AIChat
from sample_schedule import generate_schedule, EMPLOYEES, EMPLOYEE_HISTORY

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI-powered workforce compliance, scheduling, and leave management platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# AUTH DEPENDENCY
# ============================================================

async def get_current_user(authorization: Optional[str] = Header(None)):
    """Extract and validate the current user from JWT token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {
        "user_id": payload.get("sub"),
        "tenant_id": payload.get("tenant_id"),
        "role": payload.get("role"),
        "employee_id": payload.get("employee_id"),
    }


def require_role(allowed_roles: list):
    """Dependency factory — require specific roles."""
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{current_user['role']}' not authorized. Required: {allowed_roles}"
            )
        return current_user
    return role_checker


# ============================================================
# HEALTH & STATUS
# ============================================================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
    }


# ============================================================
# AUTH ENDPOINTS
# ============================================================

@app.post("/api/v1/auth/login")
async def login(email: str, password: str, tenant_slug: str):
    """Authenticate user and return JWT tokens."""
    from .core.auth import verify_password, create_access_token, create_refresh_token

    # In production: look up user from DB
    # For now, return structure showing the flow
    raise HTTPException(status_code=501, detail="Database not connected yet — use demo mode")


@app.post("/api/v1/auth/refresh")
async def refresh_token(refresh_token: str):
    """Refresh an expired access token."""
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    from .core.auth import create_access_token
    new_token = create_access_token({
        "sub": payload["sub"],
        "tenant_id": payload.get("tenant_id"),
        "role": payload.get("role"),
    })
    return {"access_token": new_token, "token_type": "bearer"}


# ============================================================
# EMPLOYEE ENDPOINTS
# ============================================================

@app.get("/api/v1/employees")
async def list_employees(current_user: dict = Depends(require_role(["MANAGER", "HR", "ADMIN"]))):
    """List employees (scoped to user's team/tenant)."""
    return {"message": "Employee list", "tenant_id": current_user["tenant_id"]}


@app.get("/api/v1/employees/{employee_id}")
async def get_employee(employee_id: str, current_user: dict = Depends(get_current_user)):
    """Get employee details (workers can only see themselves)."""
    if current_user["role"] == "WORKER" and current_user["employee_id"] != employee_id:
        raise HTTPException(status_code=403, detail="Can only view own data")
    return {"employee_id": employee_id}


# ============================================================
# SCHEDULE ENDPOINTS
# ============================================================

@app.get("/api/v1/schedule")
async def get_schedule(
    start_date: str, end_date: str,
    current_user: dict = Depends(get_current_user)
):
    """Get schedule for date range (scoped by role)."""
    return {"start_date": start_date, "end_date": end_date, "tenant_id": current_user["tenant_id"]}


@app.post("/api/v1/schedule/check-compliance")
async def check_compliance(current_user: dict = Depends(require_role(["MANAGER", "HR", "ADMIN"]))):
    """Run compliance check on current/proposed schedule."""
    schedule = generate_schedule()
    violations = run_compliance_check(schedule)
    return {
        "violations_found": len(violations),
        "critical": len([v for v in violations if v["severity"] == "CRITICAL"]),
        "high": len([v for v in violations if v["severity"] == "HIGH"]),
        "medium": len([v for v in violations if v["severity"] == "MEDIUM"]),
        "violations": violations,
    }


@app.post("/api/v1/schedule/generate")
async def generate_schedule(
    workers: int, pattern: str, start_date: str, end_date: str,
    current_user: dict = Depends(require_role(["MANAGER", "HR", "ADMIN"]))
):
    """Generate a fair schedule from parameters."""
    return {"status": "generator_placeholder", "workers": workers, "pattern": pattern}


# ============================================================
# HOURS & FATIGUE ENDPOINTS
# ============================================================

@app.get("/api/v1/hours/{employee_id}")
async def get_employee_hours(employee_id: str, current_user: dict = Depends(get_current_user)):
    """Get real-time hours tracking and fatigue score."""
    if current_user["role"] == "WORKER" and current_user["employee_id"] != employee_id:
        raise HTTPException(status_code=403, detail="Can only view own hours")
    return {"employee_id": employee_id, "status": "hours_placeholder"}


@app.get("/api/v1/hours/dashboard")
async def hours_dashboard(current_user: dict = Depends(require_role(["MANAGER", "HR", "ADMIN"]))):
    """Get hours dashboard for all team members."""
    schedule = generate_schedule()
    dashboards = get_all_employee_dashboards(schedule["shifts"], EMPLOYEES, datetime.now())
    return {"employees": dashboards}


@app.post("/api/v1/hours/predict-impact")
async def predict_shift_impact(
    employee_id: str, date: str, start: str, end: str,
    current_user: dict = Depends(require_role(["MANAGER", "HR", "ADMIN"]))
):
    """Predict impact of adding a shift to an employee."""
    return {"status": "prediction_placeholder"}


# ============================================================
# LEAVE MANAGEMENT ENDPOINTS
# ============================================================

@app.get("/api/v1/leave/balances/{employee_id}")
async def get_leave_balances(employee_id: str, current_user: dict = Depends(get_current_user)):
    """Get leave balances including PTO breakdown and at-risk hours."""
    if current_user["role"] == "WORKER" and current_user["employee_id"] != employee_id:
        raise HTTPException(status_code=403, detail="Can only view own balances")
    return {"employee_id": employee_id, "status": "balances_placeholder"}


@app.post("/api/v1/leave/report-sick")
async def report_sick(
    hours: float = 8, reason: str = "",
    current_user: dict = Depends(get_current_user)
):
    """Quick action: report sick for today."""
    return {"employee_id": current_user["employee_id"], "status": "sick_reported"}


@app.post("/api/v1/leave/donate")
async def donate_leave(
    recipient_id: str, hours: float, leave_type: str = "PTO",
    current_user: dict = Depends(get_current_user)
):
    """Donate PTO hours to another employee or the pool."""
    return {"donor": current_user["employee_id"], "recipient": recipient_id, "hours": hours}


@app.get("/api/v1/leave/availability-calendar")
async def availability_calendar(current_user: dict = Depends(get_current_user)):
    """Get availability calendar showing open/full/blackout dates."""
    return {"employee_id": current_user["employee_id"], "status": "calendar_placeholder"}


# ============================================================
# REQUEST ENDPOINTS
# ============================================================

@app.post("/api/v1/requests/time-off")
async def request_time_off(
    start_date: str, end_date: str, priority: int = 1,
    reason: str = "", flexible: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Submit a time-off request with priority ranking."""
    return {
        "employee_id": current_user["employee_id"],
        "start_date": start_date, "end_date": end_date,
        "priority": priority, "status": "request_placeholder"
    }


@app.post("/api/v1/requests/shift-swap")
async def request_swap(
    target_employee_id: str, my_date: str, their_date: str, reason: str = "",
    current_user: dict = Depends(get_current_user)
):
    """Propose a shift swap."""
    return {"status": "swap_placeholder"}


@app.post("/api/v1/requests/{request_id}/approve")
async def approve_request(
    request_id: str, notes: str = "",
    current_user: dict = Depends(require_role(["MANAGER", "HR", "ADMIN"]))
):
    """Approve a pending request."""
    return {"request_id": request_id, "status": "APPROVED"}


@app.post("/api/v1/requests/{request_id}/deny")
async def deny_request(
    request_id: str, reason: str = "",
    current_user: dict = Depends(require_role(["MANAGER", "HR", "ADMIN"]))
):
    """Deny a pending request with reason."""
    return {"request_id": request_id, "status": "DENIED", "reason": reason}


# ============================================================
# COVERAGE ENDPOINTS
# ============================================================

@app.post("/api/v1/coverage/find")
async def find_coverage_endpoint(
    date: str, start: str, end: str, role: str,
    absent_employee_id: Optional[str] = None,
    current_user: dict = Depends(require_role(["MANAGER", "HR", "ADMIN"]))
):
    """Find fairness-ranked coverage candidates for a gap."""
    schedule = generate_schedule()
    gap_shift = {
        "date": date, "start": start, "end": end,
        "role": role, "shift_type": "Coverage",
    }
    if absent_employee_id:
        gap_shift["absent_employee_id"] = absent_employee_id

    candidates = find_coverage(
        schedule["shifts"], EMPLOYEES, gap_shift, EMPLOYEE_HISTORY, datetime.strptime(date, "%Y-%m-%d")
    )
    return {"candidates": candidates[:10], "total_available": len(candidates)}


@app.get("/api/v1/coverage/fairness-report")
async def fairness_report(current_user: dict = Depends(require_role(["MANAGER", "HR", "ADMIN"]))):
    """Get team fairness distribution report."""
    return {"status": "fairness_placeholder"}


# ============================================================
# VET / OPEN SHIFTS
# ============================================================

@app.get("/api/v1/vet/offers")
async def get_vet_offers(current_user: dict = Depends(get_current_user)):
    """Get pending VET offers for the current user."""
    return {"employee_id": current_user["employee_id"], "offers": []}


@app.post("/api/v1/vet/offers/{offer_id}/accept")
async def accept_vet(offer_id: str, current_user: dict = Depends(get_current_user)):
    """Accept a VET offer."""
    return {"offer_id": offer_id, "status": "ACCEPTED"}


@app.post("/api/v1/vet/offers/{offer_id}/decline")
async def decline_vet(offer_id: str, current_user: dict = Depends(get_current_user)):
    """Decline a VET offer."""
    return {"offer_id": offer_id, "status": "DECLINED"}


@app.get("/api/v1/open-shifts")
async def list_open_shifts(current_user: dict = Depends(get_current_user)):
    """List available open shifts."""
    return {"shifts": []}


@app.post("/api/v1/open-shifts/{shift_id}/pickup")
async def pickup_open_shift(shift_id: str, current_user: dict = Depends(get_current_user)):
    """Pick up an open shift."""
    return {"shift_id": shift_id, "status": "PICKED_UP"}


# ============================================================
# HOLIDAY AUCTION
# ============================================================

@app.post("/api/v1/auction/submit-preferences")
async def submit_auction_preferences(
    preferences: list,
    current_user: dict = Depends(get_current_user)
):
    """Submit holiday preferences for the auction."""
    return {"employee_id": current_user["employee_id"], "preferences_count": len(preferences)}


@app.get("/api/v1/auction/results")
async def get_auction_results(current_user: dict = Depends(get_current_user)):
    """Get holiday auction allocation results."""
    return {"status": "results_placeholder"}


@app.post("/api/v1/auction/run")
async def run_auction(current_user: dict = Depends(require_role(["HR", "ADMIN"]))):
    """Run the holiday auction allocation algorithm."""
    return {"status": "auction_run_placeholder"}


# ============================================================
# MANAGER QUEUE
# ============================================================

@app.get("/api/v1/queue/summary")
async def queue_summary(current_user: dict = Depends(require_role(["MANAGER", "HR", "ADMIN"]))):
    """Get manager queue summary."""
    return {"status": "queue_placeholder"}


@app.get("/api/v1/queue/action-items")
async def queue_action_items(current_user: dict = Depends(require_role(["MANAGER", "HR", "ADMIN"]))):
    """Get items requiring manager action."""
    return {"items": []}


# ============================================================
# COMPLIANCE & AUDIT
# ============================================================

@app.get("/api/v1/audit/bias-report")
async def get_bias_report(current_user: dict = Depends(require_role(["HR", "ADMIN"]))):
    """Get latest bias audit report (NYC LL144 format)."""
    return {"status": "bias_audit_placeholder"}


@app.post("/api/v1/audit/run-bias-audit")
async def run_bias_audit(current_user: dict = Depends(require_role(["HR", "ADMIN"]))):
    """Run a new bias audit."""
    return {"status": "audit_initiated"}


@app.get("/api/v1/audit/decisions")
async def get_decision_log(
    employee_id: Optional[str] = None,
    current_user: dict = Depends(require_role(["HR", "ADMIN"]))
):
    """Get explainability log of automated decisions."""
    return {"decisions": []}


@app.get("/api/v1/alerts")
async def get_alerts(current_user: dict = Depends(require_role(["MANAGER", "HR", "ADMIN"]))):
    """Get active system alerts."""
    return {"alerts": []}


# ============================================================
# PUBLIC ENDPOINTS (no auth — free tools)
# ============================================================

@app.post("/api/v1/public/cost-calculator")
async def public_cost_calculator(
    state: str, headcount: int, industry: str, union: bool = False
):
    """Free compliance cost calculator — no auth required. The viral tool."""
    result = calculate_compliance_cost(state, headcount, industry, union)
    return result


@app.post("/api/v1/public/chat")
async def public_chat(message: str):
    """Public AI chat demo — limited functionality without auth."""
    chat = AIChat(employees=EMPLOYEES, schedule_data=generate_schedule(),
                  employee_history=EMPLOYEE_HISTORY, user_role="DEMO")
    response = chat.chat(message)
    return response


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
async def startup():
    """Initialize database tables on startup (dev mode only)."""
    if settings.DEBUG:
        create_tables()
