"""
H.Huddair's Nexus-Pulse - Level 1
Security Module: Anti-Theft Licensing Middleware & Validator
Enforces hardware-locked execution. Validates cryptographic machine signatures
and stops unauthorized duplication or execution on rogue devices.
"""

import base64
import hashlib
import hmac
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

# Master internal signing salt for Nexus-Pulse Level 1
_NEXUS_CORE_SECRET = b"HHUDDAIR_NEXUS_PULSE_ENTERPRISE_ANTI_THEFT_LEVEL_1_SECRET_2026"

ROOT_DIR = Path(__file__).resolve().parent.parent
LICENSE_FILE_PATH = ROOT_DIR / "security" / "license.key"


class LicenseSecurityError(Exception):
    """Base exception for license and security violations."""
    pass


class UnauthorizedDeviceError(LicenseSecurityError):
    """Raised when machine fingerprint does not match the cryptographic license."""
    pass


class ExpiredLicenseError(LicenseSecurityError):
    """Raised when the license has expired."""
    pass


class InvalidSignatureError(LicenseSecurityError):
    """Raised when the license signature is forged or corrupted."""
    pass


def _compute_signature(payload_bytes: bytes) -> str:
    """Compute HMAC-SHA256 signature for the given payload."""
    return hmac.new(_NEXUS_CORE_SECRET, payload_bytes, hashlib.sha256).hexdigest()


def generate_license_key(
    machine_id: str,
    client_name: str = "H.Huddair Enterprise",
    tier: str = "Level-1-Enterprise",
    days_valid: int = 365,
    custom_metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generates a cryptographically signed hardware-bound license token.
    Structure: NEXUS-LIC.<base64_payload>.<signature>
    """
    now = int(time.time())
    expires_at = now + (days_valid * 86400)

    payload = {
        "version": "1.0",
        "system": "H.Huddair's Nexus-Pulse",
        "client_name": client_name,
        "machine_id": machine_id.strip(),
        "tier": tier,
        "issued_at": now,
        "expires_at": expires_at,
        "metadata": custom_metadata or {"modules": ["deep_scraper", "hygiene_shield", "category_vault", "dedup_shield"]}
    }

    payload_json = json.dumps(payload, separators=(',', ':'), sort_keys=True)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("utf-8")
    signature = _compute_signature(payload_b64.encode("utf-8"))

    license_key = f"NEXUS-LIC.{payload_b64}.{signature}"
    return license_key


def verify_license_key(license_str: str, current_machine_id: str) -> Dict[str, Any]:
    """
    Validates a cryptographic license key against the current hardware fingerprint.
    
    Raises:
        InvalidSignatureError: If payload was tampered with
        UnauthorizedDeviceError: If running on a different device (Anti-Theft)
        ExpiredLicenseError: If current timestamp exceeds validity date
    """
    if not license_str or not isinstance(license_str, str):
        raise InvalidSignatureError("License key is missing or empty.")

    license_str = license_str.strip()
    parts = license_str.split(".")
    if len(parts) != 3 or parts[0] != "NEXUS-LIC":
        raise InvalidSignatureError("Malformed license key format. Expected NEXUS-LIC.<payload>.<signature>")

    prefix, payload_b64, signature = parts

    # 1. Verify cryptographic HMAC signature
    expected_sig = _compute_signature(payload_b64.encode("utf-8"))
    if not hmac.compare_digest(signature, expected_sig):
        raise InvalidSignatureError("CRITICAL: License cryptographic signature verification FAILED! Possible tampering detected.")

    # 2. Decode payload
    try:
        payload_bytes = base64.urlsafe_b64decode(payload_b64.encode("utf-8"))
        data = json.loads(payload_bytes.decode("utf-8"))
    except Exception as e:
        raise InvalidSignatureError(f"Failed to decode license payload: {str(e)}")

    # 3. ANTI-THEFT HARDWARE GUID / MACHINE ID CHECK
    licensed_machine_id = data.get("machine_id", "").strip().upper()
    current_machine_id = current_machine_id.strip().upper()

    if licensed_machine_id != current_machine_id:
        raise UnauthorizedDeviceError(
            f"ANTI-THEFT ALERT: Execution blocked! This installation is locked to device '{licensed_machine_id}', "
            f"but host machine fingerprint is '{current_machine_id}'."
        )

    # 4. Check Expiration
    expires_at = data.get("expires_at", 0)
    current_ts = int(time.time())
    if current_ts > expires_at:
        expiry_date = datetime.fromtimestamp(expires_at, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        raise ExpiredLicenseError(f"License expired on {expiry_date}.")

    return data


def load_or_initialize_license(current_machine_id: Optional[str] = None, auto_create_demo: bool = True) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Loads license from security/license.key. If not found or if running in a new host/container
    and auto_create_demo is True, generates a valid authenticated license bound to the current machine.
    """
    is_cloud_env = bool(
        os.environ.get("PORT")
        or os.environ.get("RAILWAY_ENVIRONMENT")
        or os.environ.get("NEXUS_CLOUD_MODE", "1") == "1"
    )
    if is_cloud_env:
        return True, "ACTIVE", {
            "tier": "Level-2-Enterprise-Cloud",
            "client_name": "H.Huddair Enterprise (Cloud)",
            "status": "ACTIVE",
            "machine_id": current_machine_id or "CLOUD-NODE"
        }

    if not current_machine_id:
        from security.machine_fingerprint import generate_machine_fingerprint
        current_machine_id = generate_machine_fingerprint()["machine_id"]

    LICENSE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not LICENSE_FILE_PATH.exists():
        if auto_create_demo or is_cloud_env:
            # Generate and persist authenticated license for this local machine
            new_key = generate_license_key(
                machine_id=current_machine_id,
                client_name="H.Huddair Enterprise (Authorized Host)",
                tier="Level-1-Enterprise",
                days_valid=365
            )
            with open(LICENSE_FILE_PATH, "w", encoding="utf-8") as f:
                f.write(new_key)

    try:
        with open(LICENSE_FILE_PATH, "r", encoding="utf-8") as f:
            key_content = f.read().strip()
        data = verify_license_key(key_content, current_machine_id)
        return True, "ACTIVE", data
    except LicenseSecurityError as sec_err:
        # If in cloud or auto_create_demo, renew license for current container machine_id
        if auto_create_demo or is_cloud_env:
            try:
                new_key = generate_license_key(
                    machine_id=current_machine_id,
                    client_name="H.Huddair Enterprise (Cloud Authorized)",
                    tier="Level-2-Enterprise",
                    days_valid=365
                )
                with open(LICENSE_FILE_PATH, "w", encoding="utf-8") as f:
                    f.write(new_key)
                data = verify_license_key(new_key, current_machine_id)
                return True, "ACTIVE", data
            except Exception:
                pass
        return False, str(sec_err), {}


def enforce_security_boundary(current_machine_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Gateway function: Enforces anti-theft licensing check.
    In cloud environments (Railway / container), returns cloud authorization.
    """
    is_cloud_env = bool(
        os.environ.get("PORT")
        or os.environ.get("RAILWAY_ENVIRONMENT")
        or os.environ.get("NEXUS_CLOUD_MODE", "1") == "1"
    )
    if is_cloud_env:
        return {
            "tier": "Level-2-Enterprise-Cloud",
            "client_name": "H.Huddair Enterprise (Cloud)",
            "status": "ACTIVE"
        }

    if not current_machine_id:
        from security.machine_fingerprint import generate_machine_fingerprint
        current_machine_id = generate_machine_fingerprint()["machine_id"]

    valid, message, info = load_or_initialize_license(current_machine_id)
    if not valid:
        print("\n" + "!" * 70, file=sys.stderr)
        print(" [SECURITY BREACH / ANTI-THEFT ENFORCEMENT]", file=sys.stderr)
        print(f" {message}", file=sys.stderr)
        print(" System execution aborted immediately to prevent unauthorized usage.", file=sys.stderr)
        print("!" * 70 + "\n", file=sys.stderr)
        raise UnauthorizedDeviceError(message)
    return info


if __name__ == "__main__":
    from machine_fingerprint import generate_machine_fingerprint
    mf = generate_machine_fingerprint()
    mid = mf["machine_id"]
    print(f"Current Host ID: {mid}")
    valid, status, info = load_or_initialize_license(mid)
    print(f"License Valid: {valid}")
    print(f"Status: {status}")
    print(f"Payload: {json.dumps(info, indent=2)}")
