"""
H.Huddair's Nexus-Pulse - Level 1
Admin License Generator & Device Fingerprint Inspector
Usage:
    python generate_license.py --inspect
    python generate_license.py --generate --days 365 --tier Level-1-Enterprise
    python generate_license.py --verify NEXUS-LIC.xxx.yyy
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from security.machine_fingerprint import generate_machine_fingerprint
from security.license_validator import (
    generate_license_key,
    verify_license_key,
    load_or_initialize_license,
    LICENSE_FILE_PATH,
    UnauthorizedDeviceError,
    ExpiredLicenseError,
    InvalidSignatureError
)


def main():
    parser = argparse.ArgumentParser(description="Nexus-Pulse Anti-Theft License Generator & Inspector")
    parser.add_argument("--inspect", action="store_true", help="Inspect current machine hardware fingerprint")
    parser.add_argument("--generate", action="store_true", help="Generate a new signed license key")
    parser.add_argument("--machine-id", type=str, default="", help="Target machine ID (defaults to current host)")
    parser.add_argument("--client", type=str, default="H.Huddair Enterprise", help="Client name")
    parser.add_argument("--tier", type=str, default="Level-1-Enterprise", help="License tier")
    parser.add_argument("--days", type=int, default=365, help="Validity period in days")
    parser.add_argument("--save", action="store_true", default=True, help="Save to security/license.key")
    parser.add_argument("--verify", type=str, default="", help="Verify a given license key against this host")

    args = parser.parse_args()

    fp = generate_machine_fingerprint()
    current_mid = fp["machine_id"]

    if args.inspect:
        print("=" * 65)
        print("       NEXUS-PULSE HARDWARE FINGERPRINT AUDIT")
        print("=" * 65)
        print(f" Machine Fingerprint : {current_mid}")
        print(f" Windows MachineGuid : {fp['machine_guid']}")
        print(f" Primary MAC Address : {fp['mac_address']}")
        print(f" System Product UUID : {fp['system_uuid']}")
        print(f" Host Processor      : {fp['processor']}")
        print(f" Operating System    : {fp['os_version']}")
        print("=" * 65)
        
        # Check existing license
        valid, status, info = load_or_initialize_license(current_mid, auto_create_demo=False)
        print(f" Existing License    : {'ACTIVE' if valid else 'NOT FOUND / INVALID'}")
        if valid:
            print(f" Licensed Client     : {info.get('client_name')}")
            print(f" Licensed Tier       : {info.get('tier')}")
            print(f" Bound Machine ID    : {info.get('machine_id')}")
        print("=" * 65)
        return

    if args.verify:
        print(f"Verifying license against host ID: {current_mid} ...")
        try:
            payload = verify_license_key(args.verify, current_mid)
            print("[SUCCESS] License is VALID and AUTHENTICATED for this host device.")
            print(json.dumps(payload, indent=2))
        except (UnauthorizedDeviceError, ExpiredLicenseError, InvalidSignatureError) as err:
            print(f"[FAILED] Security Violation: {err}", file=sys.stderr)
            sys.exit(1)
        return

    # Default action: Generate license
    target_mid = args.machine_id.strip() if args.machine_id else current_mid
    key = generate_license_key(
        machine_id=target_mid,
        client_name=args.client,
        tier=args.tier,
        days_valid=args.days
    )

    print("=" * 65)
    print("       NEXUS-PULSE LICENSE GENERATOR")
    print("=" * 65)
    print(f" Target Machine ID  : {target_mid}")
    print(f" Client             : {args.client}")
    print(f" Tier               : {args.tier}")
    print(f" Duration           : {args.days} days")
    print("-" * 65)
    print(f" Generated Key:\n{key}")
    print("-" * 65)

    if args.save:
        LICENSE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LICENSE_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(key)
        print(f" Saved license key to: {LICENSE_FILE_PATH}")
    print("=" * 65)


if __name__ == "__main__":
    main()
