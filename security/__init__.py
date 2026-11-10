"""
Security package initialization for Nexus-Pulse Level 1.
"""
from .machine_fingerprint import generate_machine_fingerprint, get_windows_machine_guid, get_mac_address
from .license_validator import (
    generate_license_key,
    verify_license_key,
    load_or_initialize_license,
    enforce_security_boundary,
    LicenseSecurityError,
    UnauthorizedDeviceError,
    ExpiredLicenseError,
    InvalidSignatureError
)
from .crypto_vault import CryptoVaultEngine, get_crypto_vault

__all__ = [
    "generate_machine_fingerprint",
    "get_windows_machine_guid",
    "get_mac_address",
    "generate_license_key",
    "verify_license_key",
    "load_or_initialize_license",
    "enforce_security_boundary",
    "LicenseSecurityError",
    "UnauthorizedDeviceError",
    "ExpiredLicenseError",
    "InvalidSignatureError",
    "CryptoVaultEngine",
    "get_crypto_vault"
]
