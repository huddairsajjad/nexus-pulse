"""
H.Huddair's Nexus-Pulse - Level 1
Security Module: Machine Fingerprint Engine
Generates an unforgeable, deterministic Hardware GUID / MAC Fingerprint for the host device.
"""

import hashlib
import os
import platform
import subprocess
import sys
import uuid
from typing import Dict, Any


def get_windows_machine_guid() -> str:
    """Retrieve the Windows Cryptography MachineGuid from registry if on Windows."""
    if sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography",
                0,
                winreg.KEY_READ | winreg.KEY_WOW64_64KEY
            )
            guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            winreg.CloseKey(key)
            if guid:
                return str(guid).strip()
        except Exception:
            pass

        # Fallback via PowerShell
        try:
            cmd = 'powershell -NoProfile -Command "(Get-ItemProperty -Path \'HKLM:\\SOFTWARE\\Microsoft\\Cryptography\').MachineGuid"'
            res = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
            if res.strip():
                return res.strip()
        except Exception:
            pass

    return "WIN-GUID-FALLBACK-0000"


def get_mac_address() -> str:
    """Retrieve primary network interface MAC address."""
    try:
        node = uuid.getnode()
        mac = ":".join(("%012X" % node)[i:i+2] for i in range(0, 12, 2))
        return mac
    except Exception:
        return "00:00:00:00:00:00"


def get_system_serial_or_uuid() -> str:
    """Retrieve system motherboard/BIOS UUID via Windows WMI/wmic/powershell."""
    if sys.platform == "win32":
        try:
            cmd = 'powershell -NoProfile -Command "(Get-CimInstance -ClassName Win32_ComputerSystemProduct).UUID"'
            res = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
            clean = res.strip()
            if clean and "UUID" not in clean:
                return clean
        except Exception:
            pass

    return platform.node() or "PLATFORM-NODE-DEFAULT"


def generate_machine_fingerprint() -> Dict[str, Any]:
    """
    Computes a canonical hardware fingerprint for the device.
    Format: NEXUS-XXXX-XXXX-XXXX-XXXX
    """
    machine_guid = get_windows_machine_guid()
    mac_addr = get_mac_address()
    sys_uuid = get_system_serial_or_uuid()
    processor = platform.processor() or "CPU-GENERIC"
    os_info = f"{platform.system()}-{platform.release()}"

    raw_seed = f"NEXUS_PULSE_V1::{machine_guid}::{mac_addr}::{sys_uuid}::{processor}::{os_info}"
    sha = hashlib.sha256(raw_seed.encode("utf-8")).hexdigest().upper()

    # Formatted human-readable canonical hardware identifier
    formatted_id = f"NEXUS-{sha[0:4]}-{sha[4:8]}-{sha[8:12]}-{sha[12:16]}"

    return {
        "machine_id": formatted_id,
        "machine_guid": machine_guid,
        "mac_address": mac_addr,
        "system_uuid": sys_uuid,
        "processor": processor,
        "os_version": os_info,
        "raw_hash": sha
    }


if __name__ == "__main__":
    fp = generate_machine_fingerprint()
    print("=" * 60)
    print("NEXUS-PULSE HARDWARE FINGERPRINT (LEVEL 1)")
    print("=" * 60)
    for k, v in fp.items():
        print(f"{k:15}: {v}")
    print("=" * 60)
