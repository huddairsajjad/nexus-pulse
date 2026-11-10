# H.Huddair’s Nexus-Pulse [Level 2 Full Enterprise Build]
### Autonomous Multi-Agent B2B Lead Engine & Anti-Theft Fortress

---

## 1. Executive Summary

**H.Huddair’s Nexus-Pulse** is an enterprise-grade autonomous multi-agent B2B lead generation engine with hardware-locked anti-theft protection, multi-lingual linguistic discovery, deep website entity scraping with tech-stack detection, high-value email prioritization, persistent deduplication, hierarchical category vaulting, a zero-bounce 3-stage hygiene engine, human authorization gates, timezone-aware scheduling, mailbox rotation, automated reply classification, and context-aware follow-ups.

All system source code, databases, launcher scripts, configuration files, and lead vault exports strictly reside inside the dedicated workspace on the User's Windows Desktop:
```
C:\Users\STONE\Desktop\rabbi
```

---

## 2. Complete Architecture & Directory Layout

```
C:\Users\STONE\Desktop\rabbi/
├── Launch_Nexus_Pulse.bat            # 1-Click Desktop App Launcher
├── Launch_Nexus_Pulse.vbs            # Silent background launcher
├── create_shortcut.py                # Desktop shortcut generator
├── run_server.py                     # Unified multi-service runner (FastAPI + GUI + Browser)
├── requirements.txt                  # Project dependencies
├── test_suite.py                     # Level 1 automated verification test suite
├── test_suite_level2.py              # Level 2 automated verification test suite
├── generate_license.py               # Administrator license inspector and generator
├── cli.py                            # Unified terminal control center
├── README.md                         # Complete enterprise documentation
├── auth/
│   ├── jwt_handler.py                # Pure-Python HMAC-SHA256 JWT tokens & PBKDF2 password hashing
│   ├── user_manager.py               # User authentication & RBAC (Admin for H.Huddair, Operator)
│   └── __init__.py
├── config/
│   ├── settings.yaml                 # Dynamic YAML runtime config
│   ├── settings.json                 # Synchronized JSON runtime config
│   ├── config_manager.py             # Hot-reload dynamic configuration manager
│   └── __init__.py
├── database/
│   ├── nexus_vault.db                # SQLite database (WAL mode, indexed O(1) deduplication)
│   ├── db_engine.py                  # Schema manager, context-managed connections, encrypted storage
│   ├── deduplication_shield.py       # Persistent global deduplication check
│   └── __init__.py
├── security/
│   ├── machine_fingerprint.py        # Windows MachineGuid + MAC + CPU + BIOS hardware fingerprinting
│   ├── license_validator.py          # HMAC-SHA256 hardware-locked cryptographic validator & anti-theft
│   ├── crypto_vault.py               # AES-256 PBKDF2 hardware-derived cryptographic storage
│   ├── license.key                   # Cryptographically signed license key bound to this host
│   └── __init__.py
├── core/
│   ├── models.py                     # Pydantic models (Lead, TechStack, KanbanStage, AgentIconState, etc.)
│   ├── orchestrator.py               # Master autonomous lead pipeline orchestrator
│   ├── agents/
│   │   ├── localization_engine.py    # Native query generator for non-English regions (DE, FR, RU, ES, etc.)
│   │   ├── scraper_agent.py          # Deep website scraper, contact parser, and tech-stack detector
│   │   ├── priority_finder.py        # Direct email classifier (estimating@, bids@, tenders@, qs@ vs info@)
│   │   ├── webform_agent.py          # Backup Web-Form Outreach Agent
│   │   ├── followup_engine.py        # Autonomous 7-Day Follow-Up Engine
│   │   └── __init__.py
│   ├── hygiene/
│   │   ├── zero_bounce_shield.py     # 3-Stage Zero-Bounce validation (RFC 5322, DNS MX, Silent SMTP Ping)
│   │   └── __init__.py
│   └── outreach/
│       ├── scheduler.py              # Time-Zone Smart Scheduler (strictly 9:00 - 11:00 AM local time)
│       ├── inbox_rotator.py          # Inbox Rotator with daily caps (40-50/day per domain)
│       ├── approval_gate.py          # Human Approval Gate (Hold & Review mechanism for H.Huddair)
│       ├── reply_listener.py         # IMAP Reply Listener, AI Classifier, Hot Lead Alerts, GDPR DNC
│       └── __init__.py
├── vault/
│   ├── partitions/                   # Partitioned vaults: Country -> Niche -> Quality Tag
│   │   └── Germany/Commercial_Construction_&_General_Contractors/TIER-1-ESTIMATING/
│   │       ├── leads.json            # Structured partition JSON
│   │       ├── leads.csv             # Spreadsheet CSV format
│   │       └── leads.xlsx            # Formatted Excel (.xlsx) workbook
│   ├── backups/                      # Timestamped consolidated snapshot backups
│   │   ├── nexus_leads_backup_*.json
│   │   ├── nexus_leads_backup_*.csv
│   │   └── nexus_leads_backup_*.xlsx
│   ├── vault_manager.py              # Category vault organizer and multi-format exporter
│   └── __init__.py
├── ui/
│   ├── index.html                    # Dark-Mode Cyberpunk React + Tailwind Dashboard SPA
│   ├── css/
│   │   └── cyberpunk.css             # Cyberpunk animations, radar scan, pulse rings, neon styling
│   └── js/
│       └── app.js                    # React/Tailwind client logic (Kanban, Approval Gate, Biometric Scan Login, Hot Leads)
└── api/
    ├── app.py                        # FastAPI application mounting REST API & GUI at root (/)
    ├── routes.py                     # Full REST API endpoints (Auth, Kanban, Approval, Outreach, Vault)
    └── __init__.py
```

---

## 3. Level 2 Technical Capabilities

### 1. One-Click Desktop App Launcher & Desktop Shortcut
* **Launcher Script**: [`Launch_Nexus_Pulse.bat`](file:///C:/Users/STONE/Desktop/rabbi/Launch_Nexus_Pulse.bat) boots the FastAPI backend and GUI server in one execution.
* **Desktop Shortcut**: Automatically placed on the user's Windows Desktop at `C:\Users\STONE\Desktop\H.Huddair Nexus-Pulse.lnk`.
* **Zero-URL Experience**: Double-clicking the shortcut boots the backend in the background and automatically opens the user's default browser directly into the GUI at `http://127.0.0.1:8000/`.

### 2. Animated High-Tech Login & Role Management
* **Cyberpunk Dark-Mode UI**: Obsidian dark palette (`#08090d`), neon cyan (`#00f3ff`), neon gold (`#ffd700`), neon red (`#ff0055`), and subtle grid backdrops.
* **Biometric Radar Scan Animation**: Retinal/fingerprint sweep line on login submit with visual pulse effects that simulate verifying the hardware GUID signature and license token.
* **Role-Based Access Control (RBAC)**:
  * **Master Admin (`h.huddair`)**: Full authorization rights to approve outreach, dispatch communications, edit subjects/messages, manage operators, and update configurations.
  * **Operator (`operator`)**: Restricted field access to run discovery and review leads, but prevented from bypassing the Human Approval Gate or dispatching messages.

### 2.1 User & Security Management Suite (Admin Dashboard)
* **Dynamic Admin Profile Control (`Settings > Account Security`)**:
  * H.Huddair (Admin) can view and modify his **Username**, **Corporate Email**, and **Password** directly from the GUI without touching code or database files.
  * Password modifications are re-hashed with **Bcrypt (12 rounds of salting)** directly into persistent SQLite storage.
* **Role-Based Operator Management Portal (`Operator Management`)**:
  * Accessible **ONLY** by Admin (`h.huddair`).
  * **Create Operators**: Set Username, Password (Bcrypt), Full Name, Email, Device Lock Machine-ID, Subscription Expiry Date, and Daily Quotas.
  * **Single Toggle Revocation Switch**: 1-Click toggle (`ACTIVE` <-> `REVOKED`) to instantly cut off or restore operator access.
  * **Operator Password Reset**: Admin can reset any operator's password directly from the UI with Bcrypt encryption.
  * **Session & Device Lock Telemetry**: View live login timestamps and hardware Machine-IDs bound to each account.
* **License & Expiry Control Module (`License & Subscriptions`)**:
  * Control card allowing the admin to inspect hardware telemetry (Host ID, Windows MachineGuid, MAC interface, HMAC signature).
  * 1-Click Subscription Extension (+30 Days, +90 Days, +1 Year) and dynamic adjustment of Daily Scraping Quotas and Daily Sending Quotas.

### 3. Human Approval Gate (Hold & Review Mechanism)
* **Authoritative Hold**: Zero emails or web-form messages are dispatched without manual authorization from H.Huddair.
* **Review & Edit**: Allows the admin to inspect candidate recipient, target company, local target office hours, edit subject lines, and customize message bodies before releasing the hold.
* **Batch Authorization**: Master "Batch Approve All" capability for efficient bulk processing.

### 4. Backup Web-Form Outreach Agent
* **Automated Fallback**: If a verified direct email is missing or fails hygiene, the backup web-form agent formats clean, structured outreach copy tailored for official "Contact Us" / "Request a Quote" / "Tenders" web forms.
* **Clean Field Mapping**: Prepares `contact_name`, `company`, `email`, `phone`, `subject`, `inquiry_type`, and clean `message` payloads, entering them into the Human Approval Gate under channel `WEB_FORM`.

### 5. Time-Zone Smart Scheduler & Inbox Rotator
* **Target Office Hours (9 AM - 11 AM Local)**: Computes local time across Germany (CET), France (CET), UK (GMT), Russia (MSK), US (EST), and UAE (GST). If outside the 9:00 - 11:00 AM window, outreach is queued for the next eligible 9:00 AM local slot.
* **Inbox Rotator**: Rotates secondary sending mailboxes across domains, strictly enforcing daily caps (40-50 emails/day per domain) to safeguard sender domain reputation.

### 6. IMAP Reply Listener, AI Classifier & Hot Lead Alerts
* **Response Classifier**:
  * **INTERESTED / HOT LEAD**: Positive buying signals ("send tender docs", "pricing", "call me", "interested") trigger immediate Hot Lead alerts.
  * **UNSUBSCRIBE / DNC**: Automatically adds the recipient and domain to `dnc_blacklist` table, marking them `BLACKLISTED` in deduplication tables for permanent GDPR compliance.
  * **BOUNCE / OUT OF OFFICE**: Gracefully logged without re-contacting.
* **1-Click AI Response**: Generates context-aware executive response templates ready for 1-click dispatch.

### 7. Autonomous 7-Day Follow-Up Engine
* **Automated Cadence**: Tracks timestamps of initial outreach. If 7 days elapse with no response logged, context-aware Step 2 follow-ups are automatically generated and queued into the Human Approval Gate.
* **Suppression Protection**: Automatically suppresses follow-ups if the lead has already replied, booked a call, or opted out.

### 8. Visual Kanban CRM & Cyber-Pulse Agent Icon
* **8 Pipeline Stages**:
  1. `Scraped`
  2. `Verified (Zero-Bounce)`
  3. `Pending Approval (Human Gate)`
  4. `Approved / Scheduled`
  5. `Sent / Dispatched`
  6. `Replied`
  7. `Hot Lead (Illuminated Gold/Red Border)`
  8. `Closed / Won`
* **Animated Top-Bar Cyber-Pulse Agent Icon**:
  * **Idle**: Ambient slow-pulse cyan glow.
  * **Active Hunting/Sending**: Fast radar-scan rotation effect.
  * **Hot Lead Alert**: High-priority red and gold flashing pulse effect.

---

## 4. Verification & Automated Test Suites

### Level 1 Test Suite (7 Core Requirements)
```powershell
python C:\Users\STONE\Desktop\rabbi\test_suite.py
```
*Result: 7/7 tests passed in ~1.5s.*

### Level 2 Test Suite (8 Enterprise Requirements)
```powershell
python C:\Users\STONE\Desktop\rabbi\test_suite_level2.py
```
*Result: 8/8 tests passed in ~0.9s.*

### User & Security Management Suite Tests
```powershell
python C:\Users\STONE\Desktop\rabbi\test_suite_security_mgmt.py
```
*Result: 3/3 tests passed (Admin profile control, Bcrypt re-hashing, Operator management, Revoke/Enable toggle, Device locks, and Quotas).*

---

## 5. How to Launch & Use the Application

### Option A: 1-Click Desktop Shortcut (Recommended)
Simply double-click the shortcut on your Windows Desktop:
```
H.Huddair Nexus-Pulse.lnk
```
This automatically boots the backend and opens your default web browser directly into the GUI at `http://127.0.0.1:8000/`.

### Option B: Batch Launcher
Double-click or run from PowerShell:
```powershell
C:\Users\STONE\Desktop\rabbi\Launch_Nexus_Pulse.bat
```

### Option C: Unified CLI Terminal
```powershell
python C:\Users\STONE\Desktop\rabbi\cli.py
```

### Default Login Credentials (Pre-Seeded)
* **Master Admin (H.Huddair)**:
  * Username: `h.huddair`
  * Password: `NexusPulse2026!`
  * Role: `admin` (Master authorization rights)
* **Restricted Operator**:
  * Username: `operator`
  * Password: `Operator2026!`
  * Role: `operator` (Restricted field user)
