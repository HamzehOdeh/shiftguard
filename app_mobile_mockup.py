"""
ShiftPool Mobile App - ASCII Wireframe Mockups
================================================
Generates text-based mockups of the employee-facing mobile experience
for the Labor Liquidity Pool product.

Run: python app_mobile_mockup.py
Output: Prints all screens and saves to app_mobile_mockup_output.txt
"""

import os
import sys
from datetime import datetime

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def phone_frame(title, content_lines, width=48):
    """Wrap content in a phone-shaped frame."""
    lines = []
    # Top of phone
    lines.append("         " + "╭" + "─" * (width - 2) + "╮")
    lines.append("         " + "│" + " " * ((width - 2 - 8) // 2) + "──────" + " " * ((width - 2 - 6) // 2) + "│")  # notch
    lines.append("         " + "├" + "─" * (width - 2) + "┤")

    # Status bar
    status = "│ 9:41 AM          ⚡ 87%  │"
    status_padded = "│" + " 9:41 AM".ljust(width - 14) + "⚡ 87% " + "│"
    lines.append("         " + status_padded)
    lines.append("         " + "├" + "─" * (width - 2) + "┤")

    # Screen title
    title_padded = "│" + title.center(width - 2) + "│"
    lines.append("         " + title_padded)
    lines.append("         " + "│" + "─" * (width - 2) + "│")

    # Content
    for line in content_lines:
        if len(line) > width - 4:
            line = line[:width - 4]
        padded = "│ " + line.ljust(width - 4) + " │"
        lines.append("         " + padded)

    # Bottom of phone
    lines.append("         " + "├" + "─" * (width - 2) + "┤")
    lines.append("         " + "│" + " " * ((width - 2 - 12) // 2) + "────────────" + " " * ((width - 2 - 12) // 2) + "│")  # home bar
    lines.append("         " + "╰" + "─" * (width - 2) + "╯")

    return "\n".join(lines)


def section_header(number, title):
    """Create a section header for each screen."""
    lines = []
    lines.append("")
    lines.append("=" * 70)
    lines.append(f"  SCREEN {number}: {title}")
    lines.append("=" * 70)
    lines.append("")
    return "\n".join(lines)


def progress_bar(value, max_val=100, length=20):
    """Create a text progress bar."""
    filled = int((value / max_val) * length)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {value}/{max_val}"


def countdown_display(minutes, seconds):
    """Create a countdown timer display."""
    return f"⏱  {minutes:02d}:{seconds:02d}"


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN DEFINITIONS
# ─────────────────────────────────────────────────────────────────────────────

def screen_1_home():
    """HOME / TIER SELECTION screen."""
    content = [
        "",
        "     ╔═══════════════════════════════╗",
        "     ║    ⚡ S H I F T P O O L ⚡    ║",
        "     ╚═══════════════════════════════╝",
        "",
        "  ┌─────────────────────────────────────┐",
        "  │  YOUR TIER                          │",
        "  │  ╔═══════════════════════════╗      │",
        "  │  ║  ★ TIER 2 - FLEX BUFFER ★ ║      │",
        "  │  ╚═══════════════════════════╝      │",
        "  └─────────────────────────────────────┘",
        "",
        "  RELIABILITY SCORE",
        f"  {progress_bar(87, 100, 24)}",
        "  ▲ Trending up (+4 this month)",
        "",
        "  ┌─────────────────────────────────────┐",
        "  │  EARNINGS THIS MONTH (July)         │",
        "  │  ─────────────────────────────────  │",
        "  │  Base wages:      $3,240.00         │",
        "  │  Flex yield:        $480.00         │",
        "  │  Surge bonuses:     $180.00         │",
        "  │                   ──────────         │",
        "  │  TOTAL:           $3,900.00         │",
        "  └─────────────────────────────────────┘",
        "",
        "  ACTIVE AVAILABILITY WINDOWS:",
        "  ┌───────────────────────────────┐",
        "  │ ● Mon-Fri  6:00AM - 2:30PM   │",
        "  │ ● Sat      2:00PM - 10:30PM  │",
        "  │ ○ Sun      OFF                │",
        "  └───────────────────────────────┘",
        "",
        "  ┌──────────┐ ┌────────────┐ ┌────────┐",
        "  │ Change   │ │ View Pool  │ │  My    │",
        "  │  Tier    │ │  Status    │ │History │",
        "  └──────────┘ └────────────┘ └────────┘",
        "",
    ]
    return section_header(1, "HOME / TIER SELECTION") + phone_frame("ShiftPool - Home", content)


def screen_2_tier_selection():
    """TIER SELECTION / MONTHLY COMMITMENT screen."""
    content = [
        "",
        "  SELECT YOUR MONTHLY TIER",
        "  ════════════════════════════════════",
        "",
        "  ┌─────────────────────────────────┐",
        "  │  TIER 1: ANCHOR                 │",
        "  │  ─────────────────────────────  │",
        "  │  Guaranteed hours. Stable pay.  │",
        "  │  $18/hr. Choose your blocks.    │",
        "  │                                 │",
        "  │  • Fixed weekly schedule        │",
        "  │  • Priority shift selection     │",
        "  │  • Predictable income           │",
        "  └─────────────────────────────────┘",
        "",
        "  ┌─────────────────────────────────┐",
        "  │ ★ TIER 2: FLEX BUFFER ★ CURRENT │",
        "  │  ═════════════════════════════  │",
        "  │  Stay ready, earn $5/hr standby │",
        "  │  + 1.5x when activated.         │",
        "  │  Pick your windows.             │",
        "  │                                 │",
        "  │  • Holding yield while on call  │",
        "  │  • 1.5x pay on activation      │",
        "  │  • Flexible availability        │",
        "  └─────────────────────────────────┘",
        "",
        "  ┌─────────────────────────────────┐",
        "  │  TIER 3: SURGE                  │",
        "  │  ─────────────────────────────  │",
        "  │  Maximum earnings. Claim shifts │",
        "  │  at 2-4x pay. No commitment    │",
        "  │  required.                      │",
        "  │                                 │",
        "  │  • Highest per-hour rates       │",
        "  │  • Zero obligation              │",
        "  │  • Real-time shift marketplace  │",
        "  └─────────────────────────────────┘",
        "",
        "  ╔═══════════════════════════════════╗",
        "  ║   CONFIRM MONTHLY COMMITMENT     ║",
        "  ╚═══════════════════════════════════╝",
        "",
        "  You can change tiers on the 1st of",
        "  each month. Next change: Aug 1, 2026",
        "",
    ]
    return section_header(2, "TIER SELECTION / MONTHLY COMMITMENT") + phone_frame("ShiftPool - Choose Tier", content)


def screen_3_surge_shift():
    """SURGE SHIFT AVAILABLE screen."""
    content = [
        "",
        "  ╔═══════════════════════════════════╗",
        "  ║  🔴 SURGE SHIFT AVAILABLE 🔴     ║",
        "  ║      ▓▓▓ RED ALERT ▓▓▓           ║",
        "  ╚═══════════════════════════════════╝",
        "",
        "  ┌─────────────────────────────────┐",
        "  │  Role:     PACK                 │",
        "  │  Location: Warehouse B          │",
        "  │  Time:     6:00 PM - 2:30 AM    │",
        "  │  Duration: 8.5 hours            │",
        "  └─────────────────────────────────┘",
        "",
        "  ┌─────────────────────────────────┐",
        "  │         LIVE PRICE              │",
        "  │                                 │",
        "  │      ◆ $34.20/hr ◆             │",
        "  │        (1.9x base)              │",
        "  │                                 │",
        "  │  ●∙∙● Price pulses in real time │",
        "  └─────────────────────────────────┘",
        "",
        "  Time remaining to claim:",
        f"      {countdown_display(18, 42)}",
        "",
        "  Price updates in: 4:58",
        "",
        "  ╔═══════════════════════════════════╗",
        "  ║                                   ║",
        "  ║   ✓ CLAIM THIS SHIFT - $34.20/hr ║",
        "  ║                                   ║",
        "  ╚═══════════════════════════════════╝",
        "",
        "  ┌─────────────────────────────────┐",
        "  │ ✓ Compliance verified            │",
        "  │ ✓ Rest period: OK (12hr gap)    │",
        "  │ ✓ Weekly hours: 47/60 (within)  │",
        "  └─────────────────────────────────┘",
        "",
        "  👁 3 other workers viewing this shift",
        "",
    ]
    return section_header(3, "SURGE SHIFT AVAILABLE (Push Notification)") + phone_frame("ShiftPool - Surge Alert!", content)


def screen_4_tier2_activation():
    """TIER 2 ACTIVATION screen."""
    content = [
        "",
        "  ╔═══════════════════════════════════╗",
        "  ║  ⚡ FLEX ACTIVATION ⚡            ║",
        "  ║     ▓▓▓ YOU'RE NEEDED ▓▓▓        ║",
        "  ╚═══════════════════════════════════╝",
        "",
        "  ┌─────────────────────────────────┐",
        "  │  A Tier 1 worker called out.    │",
        "  │  You're first in line!          │",
        "  └─────────────────────────────────┘",
        "",
        "  ┌─────────────────────────────────┐",
        "  │  SHIFT DETAILS                  │",
        "  │  ─────────────────────────────  │",
        "  │  Role:     PICK                 │",
        "  │  Location: Warehouse A          │",
        "  │  Time:     2:00 PM - 10:30 PM   │",
        "  │  Duration: 8.5 hours            │",
        "  │                                 │",
        "  │  Rate: $27.00/hr (1.5x base)    │",
        "  └─────────────────────────────────┘",
        "",
        "  ┌─────────────────────────────────┐",
        "  │  Accept within 15 minutes to    │",
        "  │  keep today's holding yield.    │",
        "  │                                 │",
        f"  │  Time remaining: {countdown_display(14, 23)}    │",
        "  └─────────────────────────────────┘",
        "",
        "  ╔════════════════╗  ┌──────────────┐",
        "  ║  ACCEPT        ║  │   DECLINE    │",
        "  ║  ($27.00/hr)   ║  │              │",
        "  ╚════════════════╝  └──────────────┘",
        "    [GREEN]              [GRAY]",
        "",
        "  ┌─────────────────────────────────┐",
        "  │ ℹ Declining does NOT affect     │",
        "  │   your reliability score.       │",
        "  └─────────────────────────────────┘",
        "",
    ]
    return section_header(4, "TIER 2 ACTIVATION") + phone_frame("ShiftPool - Flex Activation", content)


def screen_5_reliability():
    """RELIABILITY DASHBOARD screen."""
    content = [
        "",
        "  ┌─────────────────────────────────┐",
        "  │                                 │",
        "  │         ╭───────────╮           │",
        "  │        ╱  ░░░░░░░░░  ╲          │",
        "  │       │  ░░░░░░░░░░░  │         │",
        "  │       │  ░░  87   ░░  │         │",
        "  │       │  ░░░░░░░░░░░  │         │",
        "  │        ╲  ░░░░░░░░░  ╱          │",
        "  │         ╰───────────╯           │",
        "  │                                 │",
        "  │    RELIABILITY SCORE: 87        │",
        "  │    ▲ +4 this month (trending up)│",
        "  └─────────────────────────────────┘",
        "",
        "  SCORE HISTORY THIS MONTH:",
        "  ═══════════════════════════════════",
        "",
        "  ✓ Completed 18 Tier 1 shifts  +36",
        "  ✓ Accepted 3 Tier 2 activations +15",
        "  ✓ Covered 1 Tier 3 emergency  +10",
        "  ○ Called out once, 6hr notice    0",
        "                          ──────────",
        "    Net score change:          +61",
        "",
        "  ┌─────────────────────────────────┐",
        "  │  TIER ACCESS STATUS             │",
        "  │  ─────────────────────────────  │",
        "  │  Tier 1: Always ✓              │",
        "  │  Tier 2: Always ✓              │",
        "  │  Tier 3: Eligible (need 70+) ✓ │",
        "  └─────────────────────────────────┘",
        "",
        "  ╔═══════════════════════════════════╗",
        "  ║  ★ Top 15% of all workers at    ║",
        "  ║    this facility!                ║",
        "  ╚═══════════════════════════════════╝",
        "",
    ]
    return section_header(5, "RELIABILITY DASHBOARD") + phone_frame("ShiftPool - My Score", content)


def screen_6_earnings():
    """EARNINGS BREAKDOWN screen."""
    content = [
        "",
        "  EARNINGS BREAKDOWN",
        "  Month: July 2026",
        "  ═══════════════════════════════════",
        "",
        "  ┌─────────────────────────────────┐",
        "  │  Base wages:                    │",
        "  │    180 hrs @ $18.00             │",
        "  │    ........................$3,240│",
        "  │                                 │",
        "  │  Holding yield:                 │",
        "  │    96 hrs standby @ $5.00       │",
        "  │    ...........................$480│",
        "  │                                 │",
        "  │  Flex activations:              │",
        "  │    3 shifts, 9 hrs @ $27.00     │",
        "  │    ...........................$243│",
        "  │                                 │",
        "  │  Surge bonuses:                 │",
        "  │    2 claims, avg $34/hr delta   │",
        "  │    ...........................$180│",
        "  │                                 │",
        "  │  ═══════════════════════════════ │",
        "  │  TOTAL:              $4,143.00  │",
        "  │  ═══════════════════════════════ │",
        "  └─────────────────────────────────┘",
        "",
        "  ╔═══════════════════════════════════╗",
        "  ║  You earned $903 MORE than       ║",
        "  ║  fixed scheduling this month!    ║",
        "  ╚═══════════════════════════════════╝",
        "",
        "  MONTHLY TREND (last 6 months):",
        "  ─────────────────────────────────",
        "  $4.5k│         ╭─╮",
        "  $4.0k│     ╭─╮ │ ├─╮",
        "  $3.5k│ ╭─╮ │ ├─╯ │ │  ★ YOU",
        "  $3.0k│─╯ ├─╯ │   │ │  ARE HERE",
        "  $2.5k│   │    │   │ │",
        "       └───┴────┴───┴─┴──────",
        "        Feb Mar Apr May Jun Jul",
        "",
    ]
    return section_header(6, "EARNINGS BREAKDOWN") + phone_frame("ShiftPool - Earnings", content)


def screen_7_pool_status():
    """POOL STATUS (transparency) screen."""
    content = [
        "",
        "  LABOR POOL STATUS",
        "  Warehouse A - Live View",
        "  ═══════════════════════════════════",
        "",
        "  ┌─────────────────────────────────┐",
        "  │  TODAY'S COVERAGE               │",
        "  │                                 │",
        "  │  ██████████████░ 14/15 (93%)    │",
        "  │                                 │",
        "  └─────────────────────────────────┘",
        "",
        "  BREAKDOWN BY TIER:",
        "  ┌─────────────────────────────────┐",
        "  │                                 │",
        "  │  Tier 1 (Anchor):               │",
        "  │    8/8 confirmed ✓✓✓✓✓✓✓✓      │",
        "  │                                 │",
        "  │  Tier 2 (Flex Buffer):          │",
        "  │    4/5 on standby               │",
        "  │    1 activated (covering T1     │",
        "  │    callout)                     │",
        "  │                                 │",
        "  │  Tier 3 (Surge):                │",
        "  │    2 available in marketplace   │",
        "  │    0 claimed                    │",
        "  │                                 │",
        "  └─────────────────────────────────┘",
        "",
        "  ┌─────────────────────────────────┐",
        "  │  OPEN SHIFTS:                   │",
        "  │  ● Night (10:00 PM - 6:00 AM)  │",
        "  │                                 │",
        "  │  Current surge price: $22.50/hr │",
        "  │  (1.25x base)                   │",
        "  │                                 │",
        "  │  ◌ Market clearing in progress..│",
        "  └─────────────────────────────────┘",
        "",
    ]
    return section_header(7, "POOL STATUS (Transparency View)") + phone_frame("ShiftPool - Pool Status", content)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def generate_all_screens():
    """Generate all mockup screens and return as a single string."""
    output_parts = []

    # Title banner
    banner = """
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║           ⚡  S H I F T P O O L  -  M O B I L E  A P P  ⚡              ║
║                                                                          ║
║              Employee-Facing Mobile Experience Mockups                    ║
║              Labor Liquidity Pool Product                                 ║
║                                                                          ║
║              Generated: {date}                                  ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
""".format(date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    output_parts.append(banner)

    # Generate all screens
    output_parts.append(screen_1_home())
    output_parts.append(screen_2_tier_selection())
    output_parts.append(screen_3_surge_shift())
    output_parts.append(screen_4_tier2_activation())
    output_parts.append(screen_5_reliability())
    output_parts.append(screen_6_earnings())
    output_parts.append(screen_7_pool_status())

    # UX Principles footer
    footer = """
══════════════════════════════════════════════════════════════════════════════
  UX DESIGN PRINCIPLES
══════════════════════════════════════════════════════════════════════════════

These mockups demonstrate the employee experience. The key UX principles:

1. Transparency (always see the price, always see your score)
2. Agency (YOU choose your tier, nobody forces anything)
3. Instant feedback (real-time pricing, live countdowns)
4. Gamification (reliability score, earnings comparison, percentile ranking)

══════════════════════════════════════════════════════════════════════════════
  IMPLEMENTATION NOTES
══════════════════════════════════════════════════════════════════════════════

  - Screens designed for iOS/Android native app (React Native recommended)
  - Push notifications required for Surge alerts (Screen 3) and Flex
    activations (Screen 4)
  - WebSocket connection needed for live price updates and countdowns
  - Reliability score updates in real-time via server-sent events
  - Pool status (Screen 7) provides full transparency into labor market

══════════════════════════════════════════════════════════════════════════════
"""
    output_parts.append(footer)

    return "\n".join(output_parts)


if __name__ == "__main__":
    # Generate all screens
    full_output = generate_all_screens()

    # Print to console
    print(full_output)

    # Save to text file
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, "app_mobile_mockup_output.txt")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_output)

    print(f"\n[Saved to: {output_path}]")
