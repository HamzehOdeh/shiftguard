"""
ShiftPool - Employer Dashboard Generator
Generates ASCII/text mockups of the EMPLOYER-FACING dashboard for the Labor Liquidity Pool.
What the VP Ops / scheduler sees.
"""

import os
import sys
from datetime import datetime

OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard_employer_output.txt")


def banner(title):
    width = 80
    line = "=" * width
    return f"\n{line}\n{'|':>1} {title.center(width - 4)} {'|'}\n{line}"


def section(title):
    return f"\n{'─' * 80}\n  {title}\n{'─' * 80}"


def screen_executive_overview():
    output = banner("SCREEN 1: EXECUTIVE OVERVIEW")
    output += """

╔══════════════════════════════════════════════════════════════════════════════╗
║                    ShiftPool - Employer Dashboard                            ║
║                    Live Operations Center                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│                          KEY PERFORMANCE INDICATORS                          │
├────────────┬────────────┬──────────────┬────────────┬──────────┬────────────┤
│ Fill Rate  │ Avg Clear  │ Manager      │ Monthly    │Compliance│ Grievances │
│            │ Time       │ Interventions│ Savings    │ Score    │ Filed      │
├────────────┼────────────┼──────────────┼────────────┼──────────┼────────────┤
│   97.3%    │   8 min    │   0 today    │  $26,281   │  100%    │     0      │
│  ▲ from 68%│ was: 45min │              │vs tradition│          │            │
│  pre-pool  │ + unfilled │              │            │          │            │
├────────────┼────────────┼──────────────┼────────────┼──────────┼────────────┤
│  ████████▉ │  ████░░░░  │  ██████████  │  ████████▊ │██████████│ ██████████ │
│  EXCELLENT │  EXCELLENT │   PERFECT    │    HIGH    │ PERFECT  │  PERFECT   │
└────────────┴────────────┴──────────────┴────────────┴──────────┴────────────┘

  Status: ALL SYSTEMS NOMINAL — Pool operating at full efficiency
  Last updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
"""
    return output


def screen_live_pool_status():
    output = banner("SCREEN 2: LIVE POOL STATUS")
    output += """

╔══════════════════════════════════════════════════════════════════════════════╗
║                        REAL-TIME SHIFT STATUS                                ║
╚══════════════════════════════════════════════════════════════════════════════╝

  TODAY'S SHIFTS
  ─────────────────────────────────────────────────────────────────────────────

  SHIFT             SLOTS      STATUS                 DETAILS
  ─────────────     ─────      ──────                 ───────
  6AM - 2:30PM      15/15      ✓ FILLED               All Tier 1 workers
  (Day Shift)                  [███████████████] 100%  Cleared at 5:42 AM

  2PM - 10:30PM     14/15      ◐ FILLING...           1 Tier 2 activated
  (Swing Shift)                [██████████████░]  93%  Clearing now...

  10PM - 6:30AM     12/15      ◑ FILLING              3 in surge pricing
  (Night Shift)                [████████████░░░]  80%  Surge active

  ─────────────────────────────────────────────────────────────────────────────
  SURGE ACTIVITY
  ─────────────────────────────────────────────────────────────────────────────

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  ACTIVE SURGE: Night Shift                                               │
  │  Rate: $22.50/hr  │  Slots Open: 3  │  Tier 3 Workers Viewing: 6        │
  │  Expected Clear Time: ~12 minutes                                        │
  └──────────────────────────────────────────────────────────────────────────┘

  CLEARING TIMELINE
  ─────────────────────────────────────────────────────────────────────────────
  5:42 AM  │ Day shift cleared    │ Base rate ($18/hr)    │ All Tier 1
  1:48 PM  │ Swing 14/15 filled   │ Base rate ($18/hr)    │ 14 Tier 1
  1:52 PM  │ Swing slot 15        │ Tier 2 activated      │ Holding yield
  9:30 PM  │ Night 12/15 filled   │ Base rate ($18/hr)    │ 12 Tier 1
  9:45 PM  │ Night surge begins   │ $22.50/hr (+25%)      │ 6 viewing now
"""
    return output


def screen_cost_analysis():
    output = banner("SCREEN 3: COST ANALYSIS")
    output += """

╔══════════════════════════════════════════════════════════════════════════════╗
║                     MONTH-TO-DATE COST ANALYSIS                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

  SPENDING COMPARISON
  ═══════════════════════════════════════════════════════════════════════════════

  Traditional Model (projected):    $39,529  ████████████████████████████████████
  Liquidity Pool (actual):          $13,248  ████████████
                                             ─────────────────────────────────────
  SAVINGS:                          $26,281  (66.5% reduction)
                                             ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼

  COST BREAKDOWN
  ─────────────────────────────────────────────────────────────────────────────
  Category                          Amount          vs Traditional
  ─────────────────────────────────────────────────────────────────────────────
  Base payroll                      unchanged       --
  Tier 2 holding yields             $7,200          (predictable buffer cost)
  Surge premiums paid               $4,848          (market-clearing price)
  Mandatory OT forced               $0              was: $12,400
  Grievance costs                   $0              was: $8,200
  Understaffing incidents           0               was: 7 incidents
  Agency/temp labor                 $0              was: $5,600
  ─────────────────────────────────────────────────────────────────────────────
  TOTAL POOL PREMIUM COST:          $13,248
  TOTAL TRADITIONAL COST:           $39,529
  ─────────────────────────────────────────────────────────────────────────────

  DAILY COST TREND (Pool vs Traditional)
  ─────────────────────────────────────────────────────────────────────────────
       $2000 ┤
             │  T T T T T T T T T T T T T T T T T T T T   T = Traditional
       $1500 ┤  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
             │
       $1000 ┤
             │
        $500 ┤  P P P P P P P P P P P P P P P P P P P P   P = Pool
             │  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
          $0 ┼──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──
             1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20

  Result: Pool is cheaper EVERY SINGLE DAY — no exceptions.
"""
    return output


def screen_workforce_health():
    output = banner("SCREEN 4: WORKFORCE HEALTH")
    output += """

╔══════════════════════════════════════════════════════════════════════════════╗
║                         WORKFORCE HEALTH MONITOR                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

  POOL DISTRIBUTION
  ─────────────────────────────────────────────────────────────────────────────
  Tier 1 (Committed):    20 workers  ████████████████████
  Tier 2 (Buffer):       12 workers  ████████████
  Tier 3 (Surge):         8 workers  ████████
                          ──
  Total Pool:            40 workers

  RELIABILITY METRICS
  ─────────────────────────────────────────────────────────────────────────────
  Average Reliability Score:  79.4 / 100  [████████░░] HEALTHY

  Distribution:
    90-100 (Excellent):   8 workers   ████████
    80-89  (Good):       14 workers   ██████████████
    70-79  (Adequate):   12 workers   ████████████
    60-69  (At Risk):     4 workers   ████
    Below 60 (Critical):  2 workers   ██

  ─────────────────────────────────────────────────────────────────────────────
  ⚠ RISK ALERTS
  ─────────────────────────────────────────────────────────────────────────────

  ┌──────────────────────────────────────────────────────────────────────────┐
  │ [!] 3 workers below 70 reliability — may lose Tier 3 access             │
  │     Workers: ID#2847, ID#3091, ID#2956                                  │
  │     Action: Performance review notices sent automatically               │
  └──────────────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────────────────┐
  │ [!] Tier 2 buffer thin on weekends — recommend recruiting 2 more        │
  │     Current weekend Tier 2 coverage: 8 workers (minimum: 10 recommended)│
  │     Action: Notify HR / post Tier 2 openings                            │
  └──────────────────────────────────────────────────────────────────────────┘

  CALLOUT PREDICTION
  ─────────────────────────────────────────────────────────────────────────────
  Tomorrow (Thu): 2.3 expected callouts (NORMAL)
  Confidence: 87% │ Based on: historical patterns, weather, day-of-week

  EMPLOYEE SATISFACTION PROXY
  ─────────────────────────────────────────────────────────────────────────────
  Tier change requests this month: 2
    → Both UPGRADING: Tier 1 → Tier 2 (workers seeking more flexibility)
    → Direction: Positive (workers want MORE participation, not less)
  Voluntary exits from pool: 0
  Grievances related to pool: 0
"""
    return output


def screen_compliance_center():
    output = banner("SCREEN 5: COMPLIANCE CENTER")
    output += """

╔══════════════════════════════════════════════════════════════════════════════╗
║                          COMPLIANCE CENTER                                   ║
║                    ✓ ALL GREEN — FULLY COMPLIANT                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

  COMPLIANCE STATUS
  ─────────────────────────────────────────────────────────────────────────────

  ┌─────────────────────────────────────────────────────┐
  │        ✓  ✓  ✓  ✓  ✓  ALL CHECKS PASSING           │
  │        ─────────────────────────────────             │
  │        Last 30 Days: 0 violations                    │
  │        Shifts Auto-Verified: 142                     │
  │        Manual Reviews Required: 0                    │
  └─────────────────────────────────────────────────────┘

  ACTIVE RULES
  ─────────────────────────────────────────────────────────────────────────────
  Rule                              Status      Last Check      Violations
  ─────────────────────────────────────────────────────────────────────────────
  Chicago Fair Workweek             ✓ ACTIVE    2 min ago       0
    (14-day advance notice)
  CBA Local 299 - Rest Periods      ✓ ACTIVE    2 min ago       0
    (11hr minimum between shifts)
  CBA Local 299 - OT Equity         ✓ ACTIVE    2 min ago       0
    (rotation-based distribution)
  FLSA Overtime Calculation          ✓ ACTIVE    2 min ago       0
  State Meal/Break Requirements      ✓ ACTIVE    2 min ago       0
  Consecutive Day Limits             ✓ ACTIVE    2 min ago       0
  ─────────────────────────────────────────────────────────────────────────────

  AUDIT TRAIL
  ─────────────────────────────────────────────────────────────────────────────
  Total Transactions Logged:  847
  Blockchain-verified:        847 (100%)
  Tamper attempts detected:   0

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  ✓ Ready for regulatory inspection: full documentation available         │
  │    All shift assignments, tier changes, price movements, and worker      │
  │    elections are permanently logged with timestamps and rationale.        │
  └──────────────────────────────────────────────────────────────────────────┘

  RECENT AUTO-BLOCKS
  ─────────────────────────────────────────────────────────────────────────────
  Time          Worker          Action Blocked              Reason
  ─────────────────────────────────────────────────────────────────────────────
  Yesterday     Marcus (T3)     Tier 3 shift claim          Would exceed 6
   3:41 PM                                                  consecutive days
  3 days ago    Rivera (T2)     Swing shift acceptance      < 11hr rest since
                                                            last shift end
  5 days ago    Chen (T1)       OT volunteer                OT equity rotation
                                                            (not their turn)
  ─────────────────────────────────────────────────────────────────────────────
  All blocks logged, explained to worker, and documented for audit.
"""
    return output


def screen_demand_planning():
    output = banner("SCREEN 6: DEMAND PLANNING")
    output += """

╔══════════════════════════════════════════════════════════════════════════════╗
║                         DEMAND PLANNING & FORECAST                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

  NEXT WEEK FORECAST
  ─────────────────────────────────────────────────────────────────────────────

  Day       Need   Committed   Buffer    Surge     Coverage    Status
                   (Tier 1)    (Tier 2)  (Tier 3)
  ─────────────────────────────────────────────────────────────────────────────
  Mon       15     13          2         --        100%        ✓ Covered
  Tue       15     14          1         --        100%        ✓ Covered
  Wed*      18     14          3         1         100%        ✓ Covered
  Thu*      18     14          3         1         100%        ✓ Covered
  Fri       16     13          3         --        100%        ✓ Covered
  Sat       12      8          4         --        100%        ✓ Covered
  Sun       10      6          4         --        100%        ✓ Covered
  ─────────────────────────────────────────────────────────────────────────────
  * = Peak days (demand > 15)

  VISUAL CAPACITY MAP
  ─────────────────────────────────────────────────────────────────────────────
         Mon    Tue    Wed    Thu    Fri    Sat    Sun
  Need:  ███    ███    ████   ████   ███░   ██░    ██
  Have:  ███░   ███░   ████░  ████░  ███░░  ███░   ███░
         ↑ Buffer surplus visible (░ = available buffer beyond need)

  POOL READINESS ASSESSMENT
  ─────────────────────────────────────────────────────────────────────────────

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  Current Tier 2 + Tier 3 capacity covers 120% of projected buffer need. │
  │                                                                          │
  │  ✓ NO ACTION REQUIRED                                                   │
  │                                                                          │
  │  Total buffer workers available: 20 (12 Tier 2 + 8 Tier 3)             │
  │  Maximum buffer needed next week: 4 (Wednesday/Thursday)                │
  │  Surplus capacity: 16 workers                                            │
  └──────────────────────────────────────────────────────────────────────────┘

  ALERT THRESHOLDS
  ─────────────────────────────────────────────────────────────────────────────
  ● Green (current):  Coverage > 110% of projected need
  ○ Yellow:           Coverage 100-110% — monitor closely
  ○ Red:              Coverage < 100% — immediate recruitment needed

  System will auto-notify if projected coverage drops below 100%.
"""
    return output


def screen_roi_report():
    output = banner("SCREEN 7: ROI REPORT (CFO / Board Presentation)")
    output += """

╔══════════════════════════════════════════════════════════════════════════════╗
║                    90-DAY PERFORMANCE REPORT                                 ║
║                    Labor Liquidity Pool ROI Analysis                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

  OPERATIONAL METRICS (90 Days)
  ═══════════════════════════════════════════════════════════════════════════════

  Metric                        Pool Result     Previous (Traditional)
  ─────────────────────────────────────────────────────────────────────────────
  Total shifts scheduled         2,700           2,700
  Auto-cleared (no intervention) 2,619 (97%)     1,836 (68%)
  Manager interventions          81 (3%)         864 (32%)
  Mandatory OT events            4               180
  Grievances filed               0               12
  Regulatory fines               $0              $15,000
  Understaffing incidents        3               47
  ─────────────────────────────────────────────────────────────────────────────

  FINANCIAL SUMMARY
  ═══════════════════════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────────────────────┐
  │                                                                          │
  │   Total Pool Premium Cost (90 days):         $39,744                    │
  │   Total Traditional Cost (90 days):          $118,587                   │
  │                                              ─────────                   │
  │   TOTAL SAVINGS:                             $78,843                    │
  │                                                                          │
  │   ╔══════════════════════════════════════╗                               │
  │   ║         NET ROI: 198%               ║                               │
  │   ╚══════════════════════════════════════╝                               │
  │                                                                          │
  │   Projected Annual Savings: $315,372                                    │
  │                                                                          │
  └──────────────────────────────────────────────────────────────────────────┘

  SAVINGS BREAKDOWN (90 Days)
  ─────────────────────────────────────────────────────────────────────────────
  Eliminated mandatory OT:                       $37,200
  Eliminated grievance processing:               $24,600
  Eliminated regulatory fines:                   $15,000
  Reduced agency/temp labor:                     $16,800
  Reduced manager overtime (scheduling):         $8,400
  Reduced turnover costs:                        $12,000
                                                 ────────
  Gross savings:                                 $114,000
  Less: Pool operating costs:                    -$39,744
  Less: Technology platform:                     -$4,800 (est.)
                                                 ────────
  NET SAVINGS:                                   $78,843
  ─────────────────────────────────────────────────────────────────────────────

  QUARTERLY COMPARISON
  ─────────────────────────────────────────────────────────────────────────────

        Traditional                    Liquidity Pool
        ───────────                    ──────────────
  Cost: ████████████████████████████   Cost: █████████
        $118,587                              $39,744

  Grievances: ████████████ (12)        Grievances: (0)
  Fines: █████ ($15K)                  Fines: (0)
  OT Events: ████████████████ (180)    OT Events: █ (4)

  ─────────────────────────────────────────────────────────────────────────────
  Board Recommendation: EXPAND to all facilities. Current single-site pilot
  demonstrates conclusive ROI. Each additional site projected to yield
  $300K+ annual savings with identical compliance profile.
  ─────────────────────────────────────────────────────────────────────────────
"""
    return output


def closing_statement():
    return """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  The employer dashboard proves:                                              ║
║                                                                              ║
║  1. The pool WORKS (97% fill rate, zero manager intervention)               ║
║  2. It's CHEAPER (66.5% savings vs traditional)                             ║
║  3. It's COMPLIANT (0 violations, full audit trail)                         ║
║  4. Employees PREFER it (tier upgrades, no grievances)                      ║
║                                                                              ║
║  This is what you show in every sales demo.                                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""


def main():
    screens = [
        screen_executive_overview,
        screen_live_pool_status,
        screen_cost_analysis,
        screen_workforce_health,
        screen_compliance_center,
        screen_demand_planning,
        screen_roi_report,
    ]

    full_output = ""
    full_output += "\n" + "█" * 80
    full_output += "\n" + "█" + " " * 78 + "█"
    full_output += "\n" + "█" + "  ShiftPool — EMPLOYER DASHBOARD".center(78) + "█"
    full_output += "\n" + "█" + "  Labor Liquidity Pool Management Console".center(78) + "█"
    full_output += "\n" + "█" + f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(78) + "█"
    full_output += "\n" + "█" + " " * 78 + "█"
    full_output += "\n" + "█" * 80
    full_output += "\n"

    for screen_fn in screens:
        full_output += screen_fn()

    full_output += closing_statement()

    # Print to console (handle Windows encoding)
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(full_output)

    # Save to text file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(full_output)

    print(f"\n[Output saved to: {OUTPUT_FILE}]")


if __name__ == "__main__":
    main()
