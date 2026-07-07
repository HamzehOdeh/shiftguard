"""
ShiftGuard - Sync Scheduler
Automated nightly (or configurable) sync of schedule data from connected integrations.
Runs compliance check after every sync.

Usage:
  python -m connectors.sync_scheduler          # Run once (cron-friendly)
  python -m connectors.sync_scheduler --daemon  # Run as background service

In production, schedule via:
  - cron: 0 2 * * * cd /app && python -m connectors.sync_scheduler
  - systemd timer
  - AWS EventBridge / Lambda
  - Docker healthcheck + restart policy
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta

# Add parent dir to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from connectors.ukg_kronos import UKGConnector
from connectors.google_sheets import GoogleSheetsConnector
from compliance_checker import check_compliance

os.makedirs("data", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("data/sync.log", mode="a"),
    ]
)
logger = logging.getLogger("shiftguard.sync")

# Sync configuration (in production, stored in database per tenant)
DEFAULT_SYNC_CONFIG = {
    "frequency": "nightly",      # nightly, hourly, manual
    "time": "02:00",             # when to run (for nightly)
    "lookback_days": 7,          # how far back to pull
    "lookahead_days": 14,        # how far forward to pull
    "run_compliance_after": True, # auto-check compliance after sync
    "notify_on_violations": True, # alert manager if critical violations found
}


def sync_ukg(config=None):
    """Pull latest schedule from UKG and run compliance check."""
    config = config or DEFAULT_SYNC_CONFIG
    logger.info("Starting UKG sync...")

    connector = UKGConnector()
    conn_result = connector.connect()

    if not conn_result.get("success"):
        logger.error(f"UKG connection failed: {conn_result.get('error')}")
        return {"success": False, "error": conn_result.get("error")}

    # Calculate date range
    today = datetime.now()
    start = (today - timedelta(days=config["lookback_days"])).strftime("%Y-%m-%d")
    end = (today + timedelta(days=config["lookahead_days"])).strftime("%Y-%m-%d")

    logger.info(f"Pulling schedule: {start} to {end}")
    schedule_result = connector.pull_schedule(start, end)

    if not schedule_result.get("success"):
        logger.error(f"Schedule pull failed: {schedule_result.get('error')}")
        return {"success": False, "error": schedule_result.get("error")}

    schedule = schedule_result["schedule"]
    stats = schedule_result["stats"]
    logger.info(f"Pulled {stats['total_shifts']} shifts for {stats['total_employees']} employees")

    # Run compliance check
    violations = []
    if config["run_compliance_after"]:
        violations = check_compliance(schedule)
        critical = [v for v in violations if v["severity"] == "CRITICAL"]
        logger.info(f"Compliance check: {len(violations)} violations ({len(critical)} critical)")

        if critical and config["notify_on_violations"]:
            logger.warning(f"CRITICAL VIOLATIONS FOUND: {len(critical)} — notification would be sent")

    return {
        "success": True,
        "source": "ukg",
        "synced_at": datetime.now().isoformat(),
        "stats": stats,
        "violations": len(violations),
        "critical_violations": len([v for v in violations if v["severity"] == "CRITICAL"]),
    }


def sync_google_sheets(spreadsheet_url=None, sheet_name="Schedule", config=None):
    """Pull latest schedule from Google Sheets and run compliance check."""
    config = config or DEFAULT_SYNC_CONFIG
    logger.info("Starting Google Sheets sync...")

    connector = GoogleSheetsConnector()

    if spreadsheet_url:
        connector.set_spreadsheet(spreadsheet_url=spreadsheet_url)
    elif os.getenv("GOOGLE_SHEETS_URL"):
        connector.set_spreadsheet(spreadsheet_url=os.getenv("GOOGLE_SHEETS_URL"))
    else:
        logger.error("No spreadsheet URL configured")
        return {"success": False, "error": "No spreadsheet URL. Set GOOGLE_SHEETS_URL env var."}

    result = connector.read_schedule(sheet_name=sheet_name)

    if not result.get("success"):
        logger.error(f"Sheets read failed: {result.get('error')}")
        return {"success": False, "error": result.get("error")}

    schedule = result["schedule"]
    stats = result["stats"]
    logger.info(f"Read {stats['total_shifts']} shifts for {stats['total_employees']} employees")

    # Run compliance check
    violations = []
    if config["run_compliance_after"]:
        violations = check_compliance(schedule)
        critical = [v for v in violations if v["severity"] == "CRITICAL"]
        logger.info(f"Compliance check: {len(violations)} violations ({len(critical)} critical)")

    return {
        "success": True,
        "source": "google_sheets",
        "synced_at": datetime.now().isoformat(),
        "stats": stats,
        "violations": len(violations),
        "critical_violations": len([v for v in violations if v["severity"] == "CRITICAL"]),
    }


def run_all_syncs():
    """Run all configured syncs."""
    results = []

    # UKG
    if os.getenv("UKG_BASE_URL"):
        logger.info("=" * 50)
        logger.info("UKG SYNC")
        results.append(sync_ukg())

    # Google Sheets
    if os.getenv("GOOGLE_SHEETS_URL") or os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE"):
        logger.info("=" * 50)
        logger.info("GOOGLE SHEETS SYNC")
        results.append(sync_google_sheets())

    if not results:
        logger.warning("No integrations configured. Set UKG_BASE_URL or GOOGLE_SHEETS_URL.")
        return {"syncs_run": 0, "message": "No integrations configured"}

    logger.info("=" * 50)
    logger.info(f"SYNC COMPLETE: {len(results)} integration(s) synced")

    return {
        "syncs_run": len(results),
        "results": results,
        "completed_at": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ShiftGuard Sync Scheduler")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon (loop forever)")
    parser.add_argument("--interval", type=int, default=3600, help="Daemon check interval in seconds")
    args = parser.parse_args()

    os.makedirs("data", exist_ok=True)

    if args.daemon:
        import time
        logger.info(f"Starting sync daemon (interval: {args.interval}s)")
        while True:
            try:
                run_all_syncs()
            except Exception as e:
                logger.error(f"Sync failed: {e}")
            time.sleep(args.interval)
    else:
        result = run_all_syncs()
        print(json.dumps(result, indent=2))
