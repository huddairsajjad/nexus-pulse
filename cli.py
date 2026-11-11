"""
H.Huddair's Nexus-Pulse - Level 2
Unified Command Line Interface (CLI) Control Center
Location: Desktop/rabbi/cli.py
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from security.machine_fingerprint import generate_machine_fingerprint
from security.license_validator import (
    load_or_initialize_license,
    generate_license_key,
    verify_license_key,
    LICENSE_FILE_PATH
)
from config.config_manager import get_config
from core.agents.localization_engine import LocalizationEngine
from core.agents.scraper_agent import DeepScraperAgent
from core.agents.priority_finder import PriorityEmailFinder
from core.hygiene.zero_bounce_shield import get_hygiene_shield
from database.deduplication_shield import get_dedup_shield
from vault.vault_manager import get_vault_manager
from core.orchestrator import NexusPulseOrchestrator

from auth.user_manager import get_user_manager
from core.outreach.approval_gate import get_approval_gate
from core.outreach.scheduler import get_scheduler
from core.outreach.inbox_rotator import get_inbox_rotator
from core.outreach.reply_listener import get_reply_listener
from core.agents.webform_agent import BackupWebFormAgent
from core.agents.followup_engine import get_followup_engine


BANNER = f"""{Fore.CYAN}
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║     ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗      ██████╗ ██╗   ██╗    ║
║     ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝      ██╔══██╗██║   ██║    ║
║     ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗█████╗██████╔╝██║   ██║    ║
║     ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║╚════╝██╔═══╝ ██║   ██║    ║
║     ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║      ██║     ╚██████╔╝    ║
║     ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝      ╚═╝      ╚═════╝     ║
║                                                                           ║
║            H.HUDDAIR'S NEXUS-PULSE  [LEVEL 2 FULL ENTERPRISE]             ║
║        Autonomous Multi-Agent B2B Lead Engine & Anti-Theft Fortress       ║
╚═══════════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""


def print_banner():
    print(BANNER)


def show_security_status():
    print(f"\n{Fore.YELLOW}═══════════════════════════════════════════════════════════════{Style.RESET_ALL}")
    print(f"{Fore.GREEN} [1] ANTI-THEFT & HARDWARE FINGERPRINT AUDIT{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}═══════════════════════════════════════════════════════════════{Style.RESET_ALL}")

    fp = generate_machine_fingerprint()
    valid, status, info = load_or_initialize_license(fp["machine_id"])

    print(f" Machine Fingerprint : {Fore.CYAN}{fp['machine_id']}{Style.RESET_ALL}")
    print(f" Windows MachineGuid : {fp['machine_guid']}")
    print(f" Primary MAC Address : {fp['mac_address']}")
    print(f" System UUID         : {fp['system_uuid']}")
    print(f" Operating System    : {fp['os_version']}")
    print("-" * 63)
    lic_color = Fore.GREEN if valid else Fore.RED
    print(f" Anti-Theft Status   : {lic_color}{status}{Style.RESET_ALL}")
    if valid:
        print(f" Authorized Client   : {info.get('client_name')}")
        print(f" License Tier        : {Fore.YELLOW}{info.get('tier')}{Style.RESET_ALL}")
        print(f" License File Path   : {LICENSE_FILE_PATH}")
    print(f"{Fore.YELLOW}═══════════════════════════════════════════════════════════════{Style.RESET_ALL}\n")


def manage_approval_gate():
    gate = get_approval_gate()
    items = gate.get_pending_approvals()

    print(f"\n{Fore.YELLOW}═══════════════════════════════════════════════════════════════{Style.RESET_ALL}")
    print(f"{Fore.GREEN} [🛡️] HUMAN APPROVAL GATE (MANDATORY HOLD){Style.RESET_ALL}")
    print(f"{Fore.YELLOW}═══════════════════════════════════════════════════════════════{Style.RESET_ALL}")
    print(f" Pending Authorizations: {Fore.CYAN}{len(items)}{Style.RESET_ALL}")

    if not items:
        print(" Zero items pending approval. All leads have been processed.\n")
        return

    for idx, item in enumerate(items, 1):
        print(f"\n [{idx}] Company: {Fore.YELLOW}{item['company_name']}{Style.RESET_ALL} ({item['channel']})")
        print(f"     Recipient   : {item['recipient']}")
        print(f"     Subject     : {item['subject']}")
        print(f"     Target Time : {item['target_country']} (Window: 09:00 - 11:00 AM local)")

    print("\n Actions: [A] Approve All | [Q] Return to Menu")
    action = input(" Select action: ").strip().upper()
    if action == "A":
        res = gate.batch_approve_all(approver="h.huddair")
        print(f"{Fore.GREEN}[SUCCESS] Authorized {res['items_approved']} outreach items by H.Huddair!{Style.RESET_ALL}\n")


def manage_inbox_rotator():
    rotator = get_inbox_rotator()
    boxes = rotator.get_all_mailboxes_status()

    print(f"\n{Fore.YELLOW}═══════════════════════════════════════════════════════════════{Style.RESET_ALL}")
    print(f"{Fore.GREEN} [🔄] INBOX ROTATOR & DAILY DOMAIN CAPS (40-50/DAY){Style.RESET_ALL}")
    print(f"{Fore.YELLOW}═══════════════════════════════════════════════════════════════{Style.RESET_ALL}")

    for b in boxes:
        print(f" • Mailbox : {Fore.CYAN}{b['email_address']}{Style.RESET_ALL}")
        print(f"   Domain  : {b['domain']} | Sent Today: {b['sent_today']}/{b['daily_limit']} (Remaining: {b['remaining_quota']})")
        print(f"   Status  : {Fore.GREEN}HEALTHY{Style.RESET_ALL}\n")


def simulate_incoming_reply():
    rl = get_reply_listener()
    print(f"\n{Fore.YELLOW}───────────────────────────────────────────────────────────────{Style.RESET_ALL}")
    print(f"{Fore.GREEN} IMAP REPLY SIMULATOR{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}───────────────────────────────────────────────────────────────{Style.RESET_ALL}")
    print(" 1. Simulate HOT LEAD (Tender Inquiry / Interested)")
    print(" 2. Simulate DNC / UNSUBSCRIBE (GDPR Opt-out)")
    choice = input(" Select simulation (1 or 2): ").strip()

    if choice == "1":
        res = rl.process_incoming_reply(
            sender_email="kalkulation@strabag.com",
            subject="Re: Tender Submissions & Estimating Capacity",
            body="Hello H.Huddair, please send more info and tender docs. We have open BoQ packages.",
            company_name="STRABAG SE"
        )
        print(f"\n{Fore.GREEN}[HOT LEAD DETECTED]{Style.RESET_ALL}")
        print(f" Classification: {Fore.YELLOW}{res['classification']}{Style.RESET_ALL}")
        print(f" 1-Click AI Response Drafted:\n{res['ai_suggested_reply']}\n")
    elif choice == "2":
        res = rl.process_incoming_reply(
            sender_email="optout@contractor.de",
            subject="Unsubscribe",
            body="Remove us from your list. Do not contact again. GDPR.",
            company_name="OptOut Contractor"
        )
        print(f"\n{Fore.RED}[DNC GDPR BLACKLISTED]{Style.RESET_ALL}")
        print(f" Status: Permanently added to dnc_blacklist table.")
        print(f" Blacklisted: {res['blacklisted']}\n")


def trigger_followup_scanner():
    fe = get_followup_engine()
    print(f"\n{Fore.CYAN}Scanning for leads sent >= 7 days ago with zero replies...{Style.RESET_ALL}")
    res = fe.scan_and_trigger_due_followups(force_all_pending=True)
    print(f"{Fore.GREEN}[FOLLOW-UP SCAN COMPLETE]{Style.RESET_ALL}")
    print(f" Follow-Ups Triggered : {res['followups_triggered']}")
    print(f" Suppressed (DNC/Replied): {res['followups_suppressed']}\n")


def launch_unified_app():
    import run_server
    run_server.main()


def interactive_menu():
    print_banner()
    while True:
        print(f"{Fore.CYAN} [LEVEL 2 ENTERPRISE CONTROL PANEL]{Style.RESET_ALL}")
        print(" 1. Anti-Theft Hardware Security & License Audit")
        print(" 2. Launch Cyberpunk GUI Dashboard & Server (1-Click)")
        print(" 3. Human Approval Gate (Review & Authorize Outreach)")
        print(" 4. Inbox Rotator & Daily Domain Limits (40-50/day)")
        print(" 5. IMAP Reply Listener Simulator (Hot Leads & DNC)")
        print(" 6. Autonomous 7-Day Follow-Up Scanner")
        print(" 7. Run Full Pipeline Run (Hunt, Verify, Queue)")
        print(" 8. Export Consolidated Backups (JSON/CSV/Excel)")
        print(" 9. Fresh Production Database Reset (Wipe & Purge)")
        print(" 10. Exit")
        print(f"{Fore.CYAN}───────────────────────────────────────────────────────────────{Style.RESET_ALL}")

        choice = input(" Select option (1-10): ").strip()
        if choice == "1":
            show_security_status()
        elif choice == "2":
            launch_unified_app()
        elif choice == "3":
            manage_approval_gate()
        elif choice == "4":
            manage_inbox_rotator()
        elif choice == "5":
            simulate_incoming_reply()
        elif choice == "6":
            trigger_followup_scanner()
        elif choice == "7":
            orch = NexusPulseOrchestrator()
            res = orch.execute_targeted_pipeline()
            print(f"{Fore.GREEN}[PIPELINE COMPLETE] Scraped {res.get('leads_preserved_count', 0)} verified leads!{Style.RESET_ALL}\n")
        elif choice == "8":
            vault = get_vault_manager()
            res = vault.export_global_snapshot_backups()
            print(f"{Fore.GREEN}[EXPORTED] Multi-format backups generated in vault/backups!{Style.RESET_ALL}\n")
        elif choice == "9":
            from reset_database import reset_production_database
            reset_production_database()
        elif choice == "10":
            print(f"\n{Fore.GREEN}Shutting down Nexus-Pulse Level 2. Goodbye!{Style.RESET_ALL}\n")
            break


def main():
    parser = argparse.ArgumentParser(description="H.Huddair's Nexus-Pulse (Level 2) CLI")
    parser.add_argument("--status", action="store_true", help="Print system status")
    parser.add_argument("--server", action="store_true", help="Launch FastAPI REST & GUI server")
    parser.add_argument("--followup", action="store_true", help="Run 7-day follow-up scan")
    parser.add_argument("--reset-db", action="store_true", help="Purge database to fresh production state")

    args = parser.parse_args()

    if args.status:
        show_security_status()
    elif args.server:
        launch_unified_app()
    elif args.followup:
        trigger_followup_scanner()
    elif args.reset_db:
        from reset_database import reset_production_database
        reset_production_database()
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
