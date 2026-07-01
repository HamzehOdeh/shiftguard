"""
integrations.py - Enterprise Integration Architecture & Platform Compatibility Layer

This module defines the technical integration layer for the Workforce Compliance AI platform:
- How the platform connects to companies' existing HR/WFM/Payroll systems
- Responsive design specifications for mobile, desktop, and tablet
- API specification for third-party connectivity
- Security, compliance, and data warehouse integrations

Enterprise-grade architecture designed for Fortune 500 deployment.
Every integration references real vendor APIs, real authentication methods,
and real data exchange formats.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
import json
from datetime import datetime


# =============================================================================
# 1. PLATFORM COMPATIBILITY - Responsive Design & Multi-Platform Support
# =============================================================================

class PlatformType(Enum):
    MOBILE_IOS = "ios"
    MOBILE_ANDROID = "android"
    DESKTOP_WEB = "desktop_web"
    TABLET = "tablet"
    SMS = "sms"
    SLACK = "slack"
    TEAMS = "teams"
    KIOSK = "kiosk"


PLATFORM_COMPATIBILITY = {
    "mobile": {
        "framework": "React Native or Flutter",
        "platforms": ["iOS 15+", "Android 12+"],
        "responsive": {
            "min_width": "320px",
            "breakpoints": ["320px", "375px", "414px", "428px"],
            "orientation": ["portrait", "landscape"]
        },
        "features": {
            "push_notifications": {
                "alerts": ["surge_alerts", "activation_notices", "schedule_changes"],
                "providers": ["Firebase Cloud Messaging (Android)", "APNs (iOS)"],
                "priority_levels": ["critical", "high", "normal", "low"]
            },
            "offline_mode": {
                "capabilities": [
                    "View current and upcoming schedule",
                    "Queue shift claims for sync when online",
                    "Queue callout submissions",
                    "View cached pool status",
                    "Access downloaded compliance rules"
                ],
                "sync_strategy": "Optimistic UI with conflict resolution on reconnect",
                "storage": "SQLite local DB + encrypted cache"
            },
            "biometric_login": {
                "supported": ["Face ID (iOS)", "Touch ID (iOS)", "Fingerprint (Android)", "Face Unlock (Android)"],
                "fallback": "PIN or password",
                "session_duration": "8 hours with biometric re-auth for sensitive actions"
            }
        }
    },

    "desktop_web": {
        "framework": "React / Next.js Progressive Web App (PWA)",
        "target_users": "Managers, schedulers, HR administrators",
        "responsive": {
            "min_width": "1024px",
            "breakpoints": ["1024px", "1280px", "1440px", "1920px"],
            "layout": "Sidebar navigation with collapsible panels"
        },
        "features": {
            "full_dashboard": {
                "views": [
                    "Real-time pool status with live worker counts",
                    "Schedule calendar with drag-and-drop editing",
                    "Compliance heat map across all locations",
                    "Cost analytics with ROI tracking",
                    "Worker reliability leaderboard"
                ]
            },
            "keyboard_shortcuts": {
                "examples": {
                    "Ctrl+Shift+S": "Open surge pool",
                    "Ctrl+Shift+P": "Post demand to pool",
                    "Ctrl+K": "Command palette (search anything)",
                    "Ctrl+Shift+A": "Analytics dashboard",
                    "Ctrl+Shift+C": "Run compliance check"
                }
            },
            "multi_tab_support": {
                "tabs": ["Schedule View", "Pool Status", "Analytics", "Compliance", "Settings"],
                "real_time_sync": "All tabs share WebSocket connection for live updates"
            }
        }
    },

    "tablet": {
        "framework": "Same as mobile (React Native / Flutter)",
        "enhancements": {
            "split_view": "Side-by-side schedule + pool status",
            "responsive_range": "768px - 1024px",
            "orientation_support": "Full landscape mode with extended dashboard",
            "use_cases": ["Supervisor floor walk", "Team lead shift management", "HR field audits"]
        }
    },

    "sms": {
        "purpose": "Critical alerts for workers without smartphones",
        "provider": "Twilio Programmable SMS",
        "capabilities": [
            "Receive surge alerts with shift details",
            "Reply YES/NO to claim or decline shifts",
            "Receive schedule change notifications",
            "Get pay period summaries",
            "Emergency callout confirmation"
        ],
        "format": "Short codes with structured response options",
        "compliance": "TCPA compliant opt-in/opt-out"
    },

    "slack_teams": {
        "slack": {
            "integration_type": "Slack Bot (Bolt framework)",
            "capabilities": [
                "Post surge alerts to designated channels",
                "/claim command to claim available shifts",
                "/schedule command to view upcoming shifts",
                "/pool-status command for managers",
                "Interactive modals for shift details",
                "Thread-based shift negotiation"
            ]
        },
        "teams": {
            "integration_type": "Microsoft Bot Framework + Adaptive Cards",
            "capabilities": [
                "Proactive messages for surge alerts",
                "Adaptive Card for shift claim workflow",
                "Tab app for full schedule view",
                "Meeting integration for shift handoffs",
                "Power Automate connector for custom workflows"
            ]
        }
    },

    "kiosk_mode": {
        "purpose": "Warehouse floor terminals, break rooms, factory entrances",
        "hardware": ["Touchscreen terminals", "Badge reader integration", "Rugged tablets"],
        "features": [
            "Clock in / clock out with badge or PIN",
            "View today's schedule and assigned area",
            "Claim available open shifts on the spot",
            "View pool status and earnings",
            "Emergency callout submission"
        ],
        "security": {
            "auto_logout": "60 seconds of inactivity",
            "no_persistent_sessions": True,
            "restricted_navigation": "Only approved screens accessible"
        },
        "accessibility": "ADA compliant, large touch targets, high contrast mode"
    }
}


# =============================================================================
# 2. HR/WFM SYSTEM INTEGRATIONS
# =============================================================================

@dataclass
class IntegrationConfig:
    """Configuration for an external system integration."""
    name: str
    vendor: str
    api_type: str
    api_version: str
    auth_method: str
    sync_direction: str  # "pull", "push", "bidirectional"
    data_pulled: List[str] = field(default_factory=list)
    data_pushed: List[str] = field(default_factory=list)
    webhooks: List[str] = field(default_factory=list)
    status: str = "planned"  # planned, in_development, available
    notes: str = ""


UKG_KRONOS_INTEGRATION = IntegrationConfig(
    name="UKG Pro Workforce Management (formerly Kronos)",
    vendor="UKG (Ultimate Kronos Group)",
    api_type="REST API",
    api_version="UKG Pro WFM API v1",
    auth_method="OAuth 2.0 + API Key (tenant-specific)",
    sync_direction="bidirectional",
    data_pulled=[
        "Employee roster (demographics, job assignments, home location)",
        "Published schedules (shifts, assignments, patterns)",
        "Time punches (clock-in/out, breaks, transfers)",
        "Accrual balances (PTO, sick, personal)",
        "Scheduling rules (min/max hours, consecutive days)",
        "Labor demand forecasts",
        "Pay rules and pay codes"
    ],
    data_pushed=[
        "Compliant schedule recommendations",
        "Pool assignments (tier, activation status)",
        "Premium pay flags (surge, holding yield, coverage bonus)",
        "Compliance violation alerts",
        "Auto-generated shift offers",
        "Fill rate analytics per location"
    ],
    webhooks=[
        "schedule.published - When manager publishes new schedule",
        "schedule.changed - When shift is modified/swapped",
        "punch.in - Worker clock-in event",
        "punch.out - Worker clock-out event",
        "punch.missed - Expected punch not received",
        "timeoff.requested - PTO/leave request submitted",
        "timeoff.approved - Leave request approved"
    ],
    status="in_development",
    notes="UKG serves 80,000+ customers. Primary integration target for enterprise."
)

WORKDAY_INTEGRATION = IntegrationConfig(
    name="Workday Human Capital Management",
    vendor="Workday, Inc.",
    api_type="REST API (Workday REST / RAAS / SOAP for legacy)",
    api_version="Workday API v40.0+",
    auth_method="OAuth 2.0 via Workday ISU (Integration System User)",
    sync_direction="bidirectional",
    data_pulled=[
        "Worker profiles (employment data, job history, supervisory org)",
        "Time off balances and calendar",
        "Certifications and licenses (expiration tracking)",
        "Compensation data (base pay, allowances)",
        "Position management (open positions, headcount)",
        "Staffing events (hires, terms, transfers)"
    ],
    data_pushed=[
        "Schedule recommendations with compliance annotations",
        "Compliance alerts (overtime risk, rest period violations)",
        "Pool participation status and tier assignments",
        "Surge event records for payroll processing",
        "Worker reliability scores (anonymized for HR dashboards)"
    ],
    webhooks=[
        "worker.hired - New hire event for onboarding to pool",
        "worker.terminated - Remove from active pool",
        "worker.transferred - Update location/department rules",
        "timeoff.submitted - Adjust availability in pool",
        "certification.expiring - Flag for compliance check"
    ],
    status="planned",
    notes="Workday dominates enterprise HCM (Fortune 500). Critical for market positioning."
)

ADP_INTEGRATION = IntegrationConfig(
    name="ADP Workforce Now / ADP Vantage HCM",
    vendor="ADP, Inc.",
    api_type="ADP Marketplace APIs (REST)",
    api_version="ADP API v2",
    auth_method="ADP Connect OAuth 2.0 (client_credentials grant)",
    sync_direction="bidirectional",
    data_pulled=[
        "Pay rates (regular, OT, double time by worker)",
        "Hours worked (current and historical)",
        "Earnings statements and deduction codes",
        "Employee demographics and job data",
        "Time and attendance records",
        "Benefits enrollment status"
    ],
    data_pushed=[
        "Premium pay calculations (surge, holding yield, coverage bonus)",
        "Surge pay records with transaction IDs",
        "Additional earnings imports (custom earning codes)",
        "Schedule-based accrual adjustments",
        "Compliance-driven pay corrections"
    ],
    webhooks=[
        "payroll.processed - Verify premium pay included",
        "worker.rehired - Reactivate pool membership",
        "worker.statuschange - Update availability"
    ],
    status="planned",
    notes="ADP processes payroll for 1 in 6 US workers. Essential for mid-market."
)

SAP_SUCCESSFACTORS = IntegrationConfig(
    name="SAP SuccessFactors Employee Central + Time Management",
    vendor="SAP SE",
    api_type="OData APIs (REST-like)",
    api_version="SAP SuccessFactors API (OData v2/v4)",
    auth_method="OAuth 2.0 SAML Bearer Assertion",
    sync_direction="bidirectional",
    data_pulled=[
        "Employee master data (personal info, employment, compensation)",
        "Time management records (time accounts, absences, attendances)",
        "Organizational structure (company code, cost center, location)",
        "Qualification/certification data",
        "Work schedule rules and patterns"
    ],
    data_pushed=[
        "Schedule compliance reports",
        "Pool assignment records",
        "Premium pay data for SAP Payroll",
        "Attendance records from pool activations",
        "Compliance audit trail entries"
    ],
    webhooks=[
        "Intelligent Services alerts for employee changes",
        "Integration Center scheduled exports"
    ],
    status="planned",
    notes="SAP dominates large enterprise / manufacturing. Complex but high-value."
)

GENERIC_API = IntegrationConfig(
    name="Generic WFM Connector (Open API)",
    vendor="Any / Custom",
    api_type="REST API (OpenAPI 3.0 specification)",
    api_version="Workforce Compliance AI Connector SDK v1",
    auth_method="OAuth 2.0, API Key, or Basic Auth (configurable)",
    sync_direction="bidirectional",
    data_pulled=[
        "Employee data via standardized schema",
        "Schedule data via standardized schema",
        "Time and attendance records"
    ],
    data_pushed=[
        "Compliant schedules",
        "Pool assignments",
        "Premium pay records",
        "Compliance alerts"
    ],
    webhooks=[
        "Configurable webhook receiver for any event type",
        "Supports JSON and XML payloads",
        "Retry logic with exponential backoff"
    ],
    status="in_development",
    notes="For legacy systems: CSV/SFTP batch import. Custom connector SDK for developers."
)

ALL_HR_INTEGRATIONS = [
    UKG_KRONOS_INTEGRATION,
    WORKDAY_INTEGRATION,
    ADP_INTEGRATION,
    SAP_SUCCESSFACTORS,
    GENERIC_API
]


# =============================================================================
# 3. PAYROLL INTEGRATION
# =============================================================================

PAYROLL_INTEGRATION = {
    "purpose": "Export all pool-related compensation to payroll systems accurately and auditably",

    "supported_formats": {
        "ADP": {
            "format": "ADP ImportExpress / ADP API earnings import",
            "fields": ["employee_id", "earning_code", "hours", "rate", "amount", "effective_date"],
            "earning_codes": {
                "SURGE": "Surge premium (pool Tier 2/3 activation)",
                "HOLD": "Holding yield (Tier 1 standby pay)",
                "COVR": "Coverage bonus (fill guarantee)",
                "OT15": "Overtime at 1.5x",
                "OT20": "Double time at 2.0x"
            }
        },
        "Paychex": {
            "format": "Paychex Flex import CSV / API",
            "fields": ["employee_ssn_last4", "check_date", "earning_type", "hours", "rate"],
            "notes": "Mapped to Paychex earning types on setup"
        },
        "generic_csv": {
            "format": "Universal CSV export (configurable columns)",
            "delimiter": "comma or pipe",
            "encoding": "UTF-8 with BOM for Excel compatibility",
            "fields": ["employee_id", "pay_period", "earning_type", "hours", "rate",
                       "gross_amount", "pool_transaction_id", "compliance_rule_applied"]
        }
    },

    "auto_calculations": {
        "regular_time": "Standard hourly rate * hours worked (up to 8/day or 40/week per jurisdiction)",
        "overtime_1_5x": "1.5x rate for hours exceeding daily/weekly threshold",
        "double_time_2x": "2.0x rate for hours exceeding double-time threshold (e.g., CA 12+ hours/day)",
        "surge_premium": "Additional rate for Tier 2/3 activations (market-clearing price from pool)",
        "holding_yield": "Standby compensation for Tier 1 commitment (per pool contract terms)",
        "coverage_bonus": "One-time bonus for filling hard-to-cover shifts (e.g., holiday, overnight)"
    },

    "audit_trail": {
        "every_payment_linked_to": "Specific pool transaction ID",
        "records_include": [
            "Original demand posting (who, when, why)",
            "Pool tier activated",
            "Worker who claimed the shift",
            "Compliance rules applied (jurisdiction, union CBA)",
            "Rate calculation breakdown",
            "Manager approval (if required)",
            "Timestamp of every state change"
        ],
        "retention": "7 years (IRS requirement) or longer per jurisdiction",
        "export_format": "JSON lines or CSV for auditor consumption"
    },

    "tax_classification": {
        "classification": "W-2 wages (all tiers)",
        "rationale": "Workers are employees, not independent contractors. All pool payments are "
                     "supplemental wages subject to standard withholding.",
        "not_1099": True,
        "implications": [
            "Subject to FICA (Social Security + Medicare)",
            "Subject to FUTA/SUTA (unemployment insurance)",
            "Subject to federal and state income tax withholding",
            "Employer pays employer-side payroll taxes on all premium amounts",
            "Workers comp coverage applies during all pool-activated shifts"
        ]
    }
}


# =============================================================================
# 4. TIME AND ATTENDANCE INTEGRATION
# =============================================================================

TIME_AND_ATTENDANCE = {
    "clock_in_verification": {
        "purpose": "Confirm the worker assigned to a shift actually shows up",
        "methods": [
            "Badge swipe at physical terminal",
            "Mobile app with GPS verification",
            "Biometric terminal (fingerprint/face)",
            "Supervisor manual confirmation",
            "Kiosk PIN entry"
        ],
        "validation_rules": [
            "Worker must be assigned to shift in system",
            "Clock-in must be within configurable window (default: 7 min early to 5 min late)",
            "Location must match assigned work site (if GPS enabled)"
        ]
    },

    "gps_geofence": {
        "purpose": "Verify worker is at correct location (mobile clock-in)",
        "technology": "GPS + WiFi triangulation for indoor accuracy",
        "geofence_radius": "Configurable per site (default: 200 meters)",
        "privacy": {
            "tracking": "Only at clock-in/out events, NOT continuous",
            "data_retention": "Location data deleted after 90 days",
            "opt_out": "Workers can opt out and use alternative verification",
            "compliance": "GDPR/CCPA compliant location consent"
        }
    },

    "badge_biometric_integration": {
        "supported_systems": [
            "HID Global (iCLASS, proximity)",
            "Suprema (fingerprint, face)",
            "ZKTeco (multi-modal biometric)",
            "Kronos InTouch terminals",
            "Custom NFC badge readers"
        ],
        "protocol": "Wiegand, OSDP, or REST API depending on hardware"
    },

    "auto_detection": {
        "late_arrival": {
            "threshold": "Configurable (default: 5 minutes past shift start)",
            "actions": ["Flag in system", "Notify supervisor", "Adjust reliability score"]
        },
        "early_departure": {
            "threshold": "Clock-out before shift end without authorization",
            "actions": ["Flag in system", "Compliance check (min hours met?)", "Adjust pay"]
        },
        "missed_punch": {
            "detection": "Expected punch not received within window",
            "actions": ["Alert worker via push/SMS", "Alert supervisor", "Hold pay pending resolution"]
        },
        "no_show": {
            "definition": "No clock-in within 15 minutes of shift start and no communication",
            "actions": ["Mark as no-show", "Significant reliability score impact",
                        "Auto-trigger next tier in pool"]
        }
    },

    "pool_auto_trigger": {
        "description": "If Tier 1 worker doesn't punch in within 15 minutes, auto-trigger Tier 2",
        "sequence": [
            "T+0: Shift start time. Tier 1 worker expected to clock in.",
            "T+5: No punch detected. Push notification sent to Tier 1 worker.",
            "T+10: Still no punch. SMS sent. Supervisor alerted.",
            "T+15: No punch and no response. Worker marked no-show. Tier 2 auto-activated.",
            "T+16: Tier 2 pool receives surge alert. First responder claims shift.",
            "T+20: If no Tier 2 claim, Tier 3 activated with higher premium."
        ],
        "override": "Supervisor can manually extend grace period or cancel trigger"
    }
}


# =============================================================================
# 5. COMMUNICATION CHANNELS
# =============================================================================

COMMUNICATION_CHANNELS = {
    "push_notifications": {
        "providers": {
            "android": "Firebase Cloud Messaging (FCM)",
            "ios": "Apple Push Notification service (APNs)"
        },
        "message_types": [
            "surge_alert: New shift available in your tier",
            "activation: You've been activated for a shift",
            "schedule_change: Your schedule has been updated",
            "earnings: Pay period summary available",
            "compliance: Action required for compliance",
            "reminder: Shift starts in 1 hour"
        ],
        "delivery_guarantee": "At-least-once with deduplication on client",
        "rich_notifications": "Action buttons (Claim/Decline) directly in notification"
    },

    "sms": {
        "provider": "Twilio Programmable Messaging",
        "use_cases": [
            "Workers without smartphones",
            "Backup channel when push fails",
            "Critical alerts requiring immediate attention",
            "Two-factor authentication codes"
        ],
        "features": {
            "two_way": "Reply YES to claim, NO to decline",
            "short_code": "Branded short code for recognition",
            "mms": "Rich media for schedule images (optional)"
        },
        "compliance": "TCPA compliant: explicit opt-in, easy opt-out (reply STOP)",
        "rate_limiting": "Max 3 messages per worker per hour (non-critical)"
    },

    "email": {
        "provider": "SendGrid (Twilio)",
        "use_cases": [
            "Daily schedule digest (morning summary)",
            "Weekly earnings report",
            "Compliance audit reports (managers)",
            "Pool performance analytics (executives)",
            "Onboarding and training materials"
        ],
        "templates": "Branded HTML templates with plain-text fallback",
        "tracking": "Open and click tracking for engagement analytics"
    },

    "slack_bot": {
        "framework": "Slack Bolt (Node.js/Python)",
        "api": "Slack Web API + Events API + Interactivity",
        "features": [
            "Slash commands: /shift-claim, /schedule, /pool-status, /callout",
            "Interactive Block Kit messages with buttons and modals",
            "Channel-based surge alerts for teams",
            "Direct messages for personal schedule updates",
            "App Home tab with personal dashboard"
        ],
        "deployment": "Slack App Directory listing (enterprise distribution)"
    },

    "teams_bot": {
        "framework": "Microsoft Bot Framework SDK v4",
        "api": "Microsoft Graph API + Bot Connector",
        "features": [
            "Adaptive Cards for rich interactive shift claims",
            "Proactive messaging for surge alerts",
            "Tab application for full schedule/pool view",
            "Messaging extensions for quick actions",
            "Meeting integration for shift handoff ceremonies"
        ],
        "deployment": "Microsoft Teams App Store (enterprise catalog)"
    },

    "whatsapp": {
        "provider": "WhatsApp Business API (Meta)",
        "purpose": "International workforce communication",
        "features": [
            "Template messages for alerts (pre-approved by Meta)",
            "Interactive list messages for shift selection",
            "Location sharing for site directions",
            "Document sharing for schedule PDFs"
        ],
        "regions": "Primary for LATAM, Europe, Asia-Pacific workforces"
    },

    "priority_cascade": {
        "description": "Escalating notification strategy to maximize response rate",
        "sequence": [
            {"channel": "push_notification", "wait": "0 min", "note": "Immediate, lowest friction"},
            {"channel": "sms", "wait": "5 min", "note": "If no response to push"},
            {"channel": "email", "wait": "10 min", "note": "Backup with full details"},
            {"channel": "phone_call", "wait": "15 min", "note": "Critical situations only (IVR or live)"},
            {"channel": "supervisor_alert", "wait": "20 min", "note": "Escalate to human manager"}
        ],
        "config": "Cascade timing configurable per urgency level and worker preference",
        "respect_dnd": "Honor Do Not Disturb hours unless emergency override"
    }
}


# =============================================================================
# 6. DATA WAREHOUSE INTEGRATION
# =============================================================================

DATA_WAREHOUSE = {
    "export_destinations": {
        "Snowflake": {
            "method": "Snowpipe (continuous ingestion) or bulk COPY INTO",
            "format": "Parquet or JSON",
            "schema": "Star schema (fact_pool_transactions, dim_workers, dim_locations, dim_rules)",
            "refresh": "Near real-time (< 5 min latency)"
        },
        "BigQuery": {
            "method": "BigQuery Storage Write API (streaming) or batch load",
            "format": "Avro or JSON newline-delimited",
            "schema": "Partitioned by date, clustered by location_id",
            "refresh": "Real-time streaming inserts"
        },
        "Redshift": {
            "method": "COPY from S3 or Redshift Streaming Ingestion",
            "format": "Parquet or CSV (gzipped)",
            "schema": "Distribution key on location_id, sort key on event_timestamp",
            "refresh": "Micro-batch every 5 minutes"
        },
        "Databricks": {
            "method": "Delta Lake (Unity Catalog) via structured streaming",
            "format": "Delta format (Parquet + transaction log)",
            "schema": "Medallion architecture (bronze/silver/gold)",
            "refresh": "Real-time with exactly-once semantics"
        }
    },

    "analytics_feed": {
        "data_points": [
            "All pool transactions (demand, claim, fill, cancel, no-show)",
            "Fill rates by location, shift type, day of week, time of day",
            "Cost per fill (base + premium breakdown)",
            "Worker reliability scores (anonymized for aggregate analytics)",
            "Compliance rule trigger frequency and resolution",
            "Time-to-fill metrics (demand posted to shift claimed)",
            "Tier distribution and activation patterns"
        ],
        "granularity": "Event-level (every state change is a record)",
        "history": "Full history retained (append-only, never deleted)"
    },

    "bi_tool_connections": {
        "Tableau": "Tableau Server/Cloud connector with live query or extract",
        "PowerBI": "Power BI dataset with DirectQuery or import mode",
        "Looker": "LookML model with predefined explores and dashboards",
        "QuickSight": "Amazon QuickSight SPICE dataset with auto-refresh"
    },

    "real_time_streaming": {
        "Kafka": {
            "topics": [
                "pool.demand.created",
                "pool.demand.filled",
                "pool.worker.activated",
                "pool.shift.claimed",
                "pool.shift.completed",
                "compliance.violation.detected",
                "compliance.rule.triggered"
            ],
            "format": "Avro with Schema Registry",
            "partitioning": "By location_id for ordering guarantees"
        },
        "EventBridge": {
            "bus": "Custom event bus for serverless consumers",
            "patterns": "Rule-based routing to Lambda, SQS, Step Functions",
            "use_case": "Live dashboards, real-time alerting, cross-account sharing"
        }
    }
}


# =============================================================================
# 7. COMPLIANCE DATA FEEDS
# =============================================================================

COMPLIANCE_DATA_FEEDS = {
    "legiscan_api": {
        "provider": "LegiScan (legiscan.com)",
        "api": "LegiScan API v1 (REST + Push)",
        "purpose": "Track new labor law bills across all 50 states + federal",
        "capabilities": [
            "Monitor bills by keyword (scheduling, overtime, wages, leave)",
            "Get real-time status updates (introduced, passed committee, signed)",
            "Full bill text retrieval for AI parsing",
            "Amendment tracking"
        ],
        "update_frequency": "Daily scan + webhook on status change",
        "coverage": "All 50 US states + DC + US Congress"
    },

    "state_legislature_monitoring": {
        "method": "Custom scrapers + RSS feeds + official APIs where available",
        "sources": [
            "State legislature websites (session calendars, bill trackers)",
            "Department of Labor regulation portals",
            "City/county municipal code repositories",
            "Federal Register (DOL, NLRB rules)"
        ],
        "ai_processing": "NLP extraction of scheduling/labor provisions from bill text",
        "alert_system": "Flag any bill that could affect client operations within 30 days"
    },

    "union_cba_ingestion": {
        "method": "Document upload (PDF/Word) + AI extraction",
        "process": [
            "1. Client uploads CBA document(s)",
            "2. AI extracts scheduling rules (seniority, minimum hours, OT distribution)",
            "3. Extracted rules presented for human review/confirmation",
            "4. Confirmed rules encoded into rules engine",
            "5. Ongoing: re-extract on CBA renewal/amendment"
        ],
        "extraction_targets": [
            "Overtime distribution rules (equalization)",
            "Seniority-based shift assignment",
            "Minimum hours guarantees",
            "Mandatory overtime limits",
            "Shift differential requirements",
            "Bid/bump procedures",
            "Grievance-triggering violations"
        ],
        "accuracy": "AI extraction + mandatory human review before activation"
    },

    "auto_update_sla": {
        "target": "New rules deployed to production within 48 hours of law enactment",
        "process": [
            "Law signed/enacted (detected by monitoring)",
            "AI generates draft rule configuration",
            "Legal team reviews and approves (internal or client-side)",
            "Rule deployed to staging environment",
            "Validation against test scenarios",
            "Production deployment with client notification"
        ],
        "emergency": "Critical changes (e.g., minimum wage effective immediately) within 24 hours"
    }
}


# =============================================================================
# 8. SECURITY AND COMPLIANCE
# =============================================================================

SECURITY_AND_COMPLIANCE = {
    "soc2_type_ii": {
        "status": "Architecture designed for SOC 2 Type II certification",
        "controls": [
            "Access controls (least privilege, MFA, session management)",
            "Change management (versioned deployments, approval workflows)",
            "Monitoring and alerting (anomaly detection, intrusion detection)",
            "Incident response (documented procedures, tabletop exercises)",
            "Vendor management (third-party risk assessments)"
        ],
        "audit": "Annual third-party audit with continuous monitoring"
    },

    "hipaa": {
        "status": "HIPAA compliant architecture for healthcare customers",
        "controls": [
            "PHI never stored in scheduling system (only identifiers)",
            "BAA (Business Associate Agreement) available",
            "Minimum necessary standard enforced",
            "Breach notification procedures in place",
            "Employee training on PHI handling"
        ],
        "applicability": "Healthcare, home health, senior care, medical staffing"
    },

    "gdpr_ccpa": {
        "data_subject_rights": [
            "Right to access (export all personal data)",
            "Right to erasure (delete on request, with legal retention exceptions)",
            "Right to rectification (correct inaccurate data)",
            "Right to portability (export in machine-readable format)",
            "Right to object (opt out of automated decision-making)"
        ],
        "data_processing": {
            "lawful_basis": "Legitimate interest (employment relationship) + consent where required",
            "data_minimization": "Only collect data necessary for scheduling/compliance",
            "purpose_limitation": "Data used only for stated scheduling and compliance purposes",
            "storage_limitation": "Configurable retention policies per data category"
        },
        "ccpa_specific": [
            "Do Not Sell My Personal Information (honored, we never sell data)",
            "Annual disclosure of data categories collected",
            "Right to opt out of sharing for cross-context behavioral advertising (N/A)"
        ]
    },

    "rbac": {
        "roles": {
            "worker": "View own schedule, claim shifts, view earnings, manage profile",
            "team_lead": "View team schedule, approve swaps, view team pool status",
            "scheduler": "Create/edit schedules, post demand, manage pool for location",
            "manager": "All scheduler + analytics, compliance reports, approve premiums",
            "hr_admin": "Employee management, rule configuration, audit access",
            "executive": "Read-only analytics, ROI dashboards, cost reports",
            "system_admin": "Full platform configuration, integration management, security settings",
            "auditor": "Read-only access to all logs and compliance records"
        },
        "features": [
            "Custom role builder (combine permissions granularly)",
            "Location-scoped access (manager sees only their sites)",
            "Time-limited elevated access (break-glass procedures)",
            "Segregation of duties enforcement"
        ]
    },

    "encryption": {
        "at_rest": {
            "algorithm": "AES-256-GCM",
            "key_management": "AWS KMS / Azure Key Vault / GCP Cloud KMS (customer-managed keys optional)",
            "scope": "All databases, file storage, backups, logs"
        },
        "in_transit": {
            "protocol": "TLS 1.3 (minimum TLS 1.2)",
            "certificate": "Managed certificates with auto-rotation",
            "internal": "mTLS for service-to-service communication"
        }
    },

    "audit_logging": {
        "scope": "Every action, every data access, every configuration change",
        "immutability": "Write-once append-only log (tamper-evident)",
        "retention": "Minimum 7 years (configurable per regulation)",
        "content": [
            "Who (user ID, role, IP address, device)",
            "What (action type, resource affected, before/after values)",
            "When (UTC timestamp, microsecond precision)",
            "Where (service, endpoint, geographic region)",
            "Why (linked to business event or user session)"
        ],
        "search": "Full-text search with sub-second query response"
    },

    "data_residency": {
        "options": [
            "US (us-east-1, us-west-2)",
            "EU (eu-west-1, eu-central-1) - GDPR compliant",
            "Canada (ca-central-1)",
            "Australia (ap-southeast-2)",
            "UK (eu-west-2) - post-Brexit UK GDPR"
        ],
        "guarantee": "Data never leaves configured region (enforced by infrastructure policy)",
        "multi_region": "Available for global enterprises with per-entity region assignment"
    },

    "sso": {
        "protocols": ["SAML 2.0", "OAuth 2.0 / OpenID Connect"],
        "identity_providers": [
            "Azure Active Directory (Entra ID)",
            "Okta",
            "OneLogin",
            "PingFederate",
            "Google Workspace",
            "AWS IAM Identity Center (SSO)",
            "Any SAML 2.0 or OIDC compliant IdP"
        ],
        "features": [
            "Just-in-time provisioning (auto-create user on first login)",
            "SCIM 2.0 for automated user lifecycle management",
            "Group-to-role mapping (AD group = platform role)",
            "MFA enforcement (delegate to IdP or platform-native)"
        ]
    }
}


# =============================================================================
# 9. API SPECIFICATION
# =============================================================================

@dataclass
class APIEndpoint:
    """Definition of a platform API endpoint."""
    method: str
    path: str
    description: str
    auth: str = "Bearer token (OAuth 2.0)"
    rate_limit: str = "1000 req/min per tenant"
    request_body: Optional[str] = None
    response: Optional[str] = None


API_SPECIFICATION = {
    "base_url": "https://api.workforcecompliance.ai/v1",
    "auth": "OAuth 2.0 Bearer Token (JWT)",
    "rate_limiting": "Tiered: 1000/min (standard), 5000/min (enterprise), custom (dedicated)",
    "versioning": "URL path versioning (/v1/, /v2/)",
    "format": "JSON (application/json)",
    "pagination": "Cursor-based (next_cursor in response)",
    "errors": "RFC 7807 Problem Details (application/problem+json)",

    "endpoints": [
        APIEndpoint(
            method="POST",
            path="/api/pool/demand",
            description="Post labor demand to the liquidity pool. Creates a new demand record "
                        "specifying required workers, shift time, location, and maximum premium.",
            request_body='{"location_id", "shift_start", "shift_end", "workers_needed", '
                         '"role_required", "max_premium_pct", "urgency_level"}',
            response='{"demand_id", "status", "pool_tier_activated", "estimated_fill_time"}'
        ),
        APIEndpoint(
            method="GET",
            path="/api/pool/status",
            description="Get current pool state including available workers per tier, "
                        "active demands, fill rates, and current market-clearing premium.",
            response='{"total_available", "by_tier": {"tier1": N, "tier2": N, "tier3": N}, '
                     '"active_demands", "current_premium_pct", "avg_fill_time_minutes"}'
        ),
        APIEndpoint(
            method="POST",
            path="/api/pool/claim",
            description="Claim a surge shift from the pool. Worker accepts an available "
                        "demand and commits to working the shift.",
            request_body='{"demand_id", "worker_id", "commitment_confirmation": true}',
            response='{"claim_id", "status", "shift_details", "premium_rate", "compliance_check_result"}'
        ),
        APIEndpoint(
            method="POST",
            path="/api/employee/callout",
            description="Initiate a callout (worker cannot make their shift). Triggers "
                        "cascade logic to fill the gap from the pool.",
            request_body='{"worker_id", "shift_id", "reason_code", "notice_hours"}',
            response='{"callout_id", "compliance_impact", "pool_triggered": true, '
                     '"estimated_replacement_time"}'
        ),
        APIEndpoint(
            method="GET",
            path="/api/employee/schedule",
            description="Get employee schedule for specified date range with pool "
                        "assignments and compliance annotations.",
            response='{"shifts": [{"date", "start", "end", "location", "pool_tier", '
                     '"compliance_flags"}], "upcoming_pool_commitments": [...]}'
        ),
        APIEndpoint(
            method="GET",
            path="/api/employee/earnings",
            description="Get earnings breakdown including base pay, overtime, surge premiums, "
                        "holding yields, and coverage bonuses.",
            response='{"period", "base_pay", "overtime_pay", "surge_premium", "holding_yield", '
                     '"coverage_bonus", "total_gross", "pool_transactions": [...]}'
        ),
        APIEndpoint(
            method="POST",
            path="/api/employee/tier",
            description="Change worker's pool tier assignment. Validates eligibility "
                        "and compliance requirements for requested tier.",
            request_body='{"worker_id", "new_tier", "effective_date", "reason"}',
            response='{"tier_change_id", "status", "eligibility_check", "new_tier_benefits"}'
        ),
        APIEndpoint(
            method="GET",
            path="/api/analytics/roi",
            description="Get ROI report comparing pool-based staffing costs vs. "
                        "traditional overtime/agency staffing for the period.",
            response='{"period", "pool_cost", "traditional_cost_estimate", "savings", '
                     '"savings_pct", "fill_rate", "compliance_score", "breakdown_by_location"}'
        ),
        APIEndpoint(
            method="GET",
            path="/api/compliance/check",
            description="Run a compliance check against specified schedule or action. "
                        "Returns all applicable rules and pass/fail status.",
            response='{"compliant": bool, "rules_checked": N, "violations": [...], '
                     '"warnings": [...], "jurisdiction", "cba_rules_applied"}'
        ),
        APIEndpoint(
            method="WebSocket",
            path="/ws/pool/live",
            description="Real-time WebSocket connection for live pool updates. "
                        "Streams demand changes, claims, fill events, and premium adjustments.",
            response='Stream: {"event_type", "timestamp", "data": {...}}'
        )
    ]
}


# =============================================================================
# 10. IMPLEMENTATION TIMELINE
# =============================================================================

IMPLEMENTATION_TIMELINE = {
    "phase_1": {
        "name": "MVP - Core Platform",
        "duration": "3 months",
        "deliverables": [
            "Web application (React/Next.js) with responsive design",
            "Core Pool Engine with demand/claim/fill logic",
            "Basic REST API (all /api/* endpoints)",
            "CSV/SFTP import for employee and schedule data",
            "Manual compliance rule configuration (admin UI)",
            "Basic analytics dashboard (fill rate, cost)",
            "PostgreSQL database with audit logging",
            "OAuth 2.0 authentication + RBAC",
            "Email and basic push notifications"
        ],
        "target_customers": "Early adopter design partners (2-3 companies)"
    },
    "phase_2": {
        "name": "Mobile + Primary Integrations",
        "duration": "6 months (cumulative)",
        "deliverables": [
            "Mobile app (React Native) for iOS and Android",
            "UKG/Kronos bi-directional integration",
            "ADP payroll integration",
            "Push notifications (FCM/APNs) with priority cascade",
            "SMS channel (Twilio) for non-smartphone workers",
            "GPS/geofence clock-in verification",
            "Advanced compliance engine (multi-jurisdiction)",
            "Worker reliability scoring algorithm",
            "Manager approval workflows"
        ],
        "target_customers": "10-20 paying customers across 3+ industries"
    },
    "phase_3": {
        "name": "Full Integration Marketplace + Scale",
        "duration": "9 months (cumulative)",
        "deliverables": [
            "Workday HCM integration",
            "SAP SuccessFactors integration",
            "Slack and Microsoft Teams bots",
            "WhatsApp Business (international)",
            "Full API marketplace with developer portal",
            "Custom connector SDK (build-your-own integration)",
            "White-label option for large enterprises",
            "Data warehouse connectors (Snowflake, BigQuery, Redshift)",
            "Kafka streaming for real-time analytics",
            "SOC 2 Type II certification complete",
            "Multi-region deployment (US + EU)"
        ],
        "target_customers": "50-100 customers, enterprise accounts"
    },
    "phase_4": {
        "name": "AI Intelligence + Self-Service",
        "duration": "12 months (cumulative)",
        "deliverables": [
            "AI chatbot for workers (schedule questions, shift claims via natural language)",
            "Predictive analytics (demand forecasting, no-show prediction)",
            "Self-service rule builder (no-code compliance rule creation)",
            "Union CBA auto-extraction (AI reads PDF, suggests rules)",
            "Kiosk mode for warehouse/factory floor",
            "Advanced reporting (custom dashboards, scheduled exports)",
            "HIPAA certification (healthcare vertical)",
            "Global expansion (APAC, LATAM regions)",
            "AI-powered schedule optimization (auto-generate compliant schedules)"
        ],
        "target_customers": "200+ customers, multiple verticals, international"
    }
}


# =============================================================================
# 11. __main__ - Integration Architecture Diagram
# =============================================================================

def print_architecture_diagram():
    """Print a text-based Integration Architecture Diagram."""
    print("=" * 90)
    print("          WORKFORCE COMPLIANCE AI - INTEGRATION ARCHITECTURE DIAGRAM")
    print("=" * 90)
    print()
    print("  DATA FLOW:")
    print()
    print("  +------------------+     +---------------+     +------------------+     +------------+")
    print("  |  EXTERNAL SYSTEM |     |   API LAYER   |     |   POOL ENGINE    |     |  RESPONSE  |")
    print("  |                  | --> |               | --> |                  | --> |            |")
    print("  | UKG / Workday /  |     | REST + WS +   |     | Demand Matching  |     | Compliant  |")
    print("  | ADP / SAP /      |     | Webhooks      |     | Tier Activation  |     | Schedule + |")
    print("  | Custom WFM       |     | OAuth 2.0     |     | Premium Calc     |     | Alerts +   |")
    print("  +------------------+     +---------------+     +------------------+     | Analytics  |")
    print("                                                         |                +------------+")
    print("                                                         v")
    print("                                                 +------------------+")
    print("                                                 | COMPLIANCE CHECK |")
    print("                                                 |                  |")
    print("                                                 | Federal/State/   |")
    print("                                                 | Local + Union    |")
    print("                                                 | CBA Rules        |")
    print("                                                 +------------------+")
    print()
    print("-" * 90)
    print()


def print_integration_status():
    """Print all supported integrations with their development status."""
    print("  SUPPORTED INTEGRATIONS:")
    print()
    print(f"  {'Integration':<45} {'Type':<20} {'Status':<15}")
    print(f"  {'-'*45} {'-'*20} {'-'*15}")

    integrations_list = [
        ("UKG Pro WFM (Kronos)", "HR/WFM", "In Development"),
        ("Workday HCM", "HR/WFM", "Planned"),
        ("ADP Workforce Now", "Payroll/HR", "Planned"),
        ("SAP SuccessFactors", "HR/WFM", "Planned"),
        ("Generic REST API Connector", "Universal", "In Development"),
        ("CSV/SFTP Batch Import", "Legacy", "Available"),
        ("ADP Payroll Export", "Payroll", "Planned"),
        ("Paychex Payroll Export", "Payroll", "Planned"),
        ("Generic CSV Payroll Export", "Payroll", "Available"),
        ("Firebase Cloud Messaging", "Push (Android)", "In Development"),
        ("Apple Push Notification (APNs)", "Push (iOS)", "In Development"),
        ("Twilio SMS", "SMS", "In Development"),
        ("SendGrid Email", "Email", "Available"),
        ("Slack Bot", "Chat", "Planned"),
        ("Microsoft Teams Bot", "Chat", "Planned"),
        ("WhatsApp Business API", "Chat (Intl)", "Planned"),
        ("Snowflake", "Data Warehouse", "Planned"),
        ("BigQuery", "Data Warehouse", "Planned"),
        ("Redshift", "Data Warehouse", "Planned"),
        ("Databricks / Delta Lake", "Data Warehouse", "Planned"),
        ("Apache Kafka", "Streaming", "Planned"),
        ("AWS EventBridge", "Streaming", "Planned"),
        ("Tableau / PowerBI / Looker", "BI Tools", "Planned"),
        ("LegiScan API", "Compliance Feed", "In Development"),
        ("HID / Suprema / ZKTeco", "Badge/Biometric", "Planned"),
        ("SAML 2.0 / OIDC SSO", "Security", "In Development"),
        ("Okta / Azure AD", "Identity", "In Development"),
    ]

    for name, int_type, status in integrations_list:
        status_indicator = {"Available": "[LIVE]", "In Development": "[DEV]", "Planned": "[PLAN]"}
        print(f"  {name:<45} {int_type:<20} {status_indicator.get(status, status):<15}")

    print()
    print(f"  Total Integrations: {len(integrations_list)}")
    print(f"  Live: {sum(1 for _, _, s in integrations_list if s == 'Available')}")
    print(f"  In Development: {sum(1 for _, _, s in integrations_list if s == 'In Development')}")
    print(f"  Planned: {sum(1 for _, _, s in integrations_list if s == 'Planned')}")
    print()
    print("-" * 90)
    print()


def print_api_endpoints():
    """Print API endpoint summary table."""
    print("  API ENDPOINT SUMMARY:")
    print()
    print(f"  {'Method':<12} {'Endpoint':<30} {'Description':<45}")
    print(f"  {'-'*12} {'-'*30} {'-'*45}")

    for ep in API_SPECIFICATION["endpoints"]:
        desc_short = ep.description[:43] + ".." if len(ep.description) > 45 else ep.description
        print(f"  {ep.method:<12} {ep.path:<30} {desc_short:<45}")

    print()
    print(f"  Base URL: {API_SPECIFICATION['base_url']}")
    print(f"  Auth: {API_SPECIFICATION['auth']}")
    print(f"  Rate Limit: {API_SPECIFICATION['rate_limiting']}")
    print(f"  Format: {API_SPECIFICATION['format']}")
    print()
    print("-" * 90)
    print()


def print_platform_summary():
    """Print platform support summary."""
    print("  PLATFORM SUPPORT:")
    print()
    print("  Platform supports: iOS, Android, Web (desktop/tablet), SMS, Slack, Teams, Kiosk")
    print()
    print("  +--------+  +----------+  +---------+  +-----+  +-------+  +-------+  +-------+")
    print("  |  iOS   |  | Android  |  | Desktop |  | SMS |  | Slack |  | Teams |  | Kiosk |")
    print("  | 320px+ |  |  320px+  |  | 1024px+ |  |     |  |  Bot  |  |  Bot  |  | Touch |")
    print("  | Native |  |  Native  |  |   PWA   |  | 2FA |  | Cmds  |  | Cards |  |  PIN  |")
    print("  +--------+  +----------+  +---------+  +-----+  +-------+  +-------+  +-------+")
    print()
    print("-" * 90)
    print()


def print_timeline_summary():
    """Print implementation timeline summary."""
    print("  IMPLEMENTATION TIMELINE:")
    print()
    for phase_key in ["phase_1", "phase_2", "phase_3", "phase_4"]:
        phase = IMPLEMENTATION_TIMELINE[phase_key]
        print(f"  [{phase['duration']:>9}]  {phase['name']}")
        print(f"               Target: {phase['target_customers']}")
        print(f"               Key deliverables: {len(phase['deliverables'])} items")
        print()
    print("-" * 90)
    print()


if __name__ == "__main__":
    print()
    print_architecture_diagram()
    print_integration_status()
    print_api_endpoints()
    print_platform_summary()
    print_timeline_summary()

    print("  ENTERPRISE READINESS SUMMARY:")
    print()
    print("  Security:     SOC 2 Type II | HIPAA | GDPR/CCPA | AES-256 | TLS 1.3")
    print("  Auth:         SAML 2.0 | OAuth 2.0 | Azure AD | Okta | SCIM 2.0")
    print("  Scale:        Multi-region | Multi-tenant | 99.9% SLA target")
    print("  Compliance:   Real-time law tracking | Union CBA AI extraction | 48hr rule deploy")
    print("  Integrations: UKG | Workday | ADP | SAP | Slack | Teams | Snowflake | Kafka")
    print()
    print("=" * 90)
    print("  This architecture allows any company to connect in <1 week using standard APIs")
    print("=" * 90)
    print()
