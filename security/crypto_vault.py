"""
H.Huddair's Nexus-Pulse - Level 1
Security Module: Encrypted Storage Standards & Crypto Vault
Provides AES-256 hardware-locked cryptographic storage for databases, lead vaults, and sensitive credentials.
Derived from the hardware fingerprint so encrypted data cannot be read if copied to another machine.
"""

import base64
import json
import os
from typing import Any, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .machine_fingerprint import generate_machine_fingerprint

# Static salt bound to the enterprise build
_VAULT_SYSTEM_SALT = b"HHUDDAIR_NEXUS_PULSE_ENCRYPTED_VAULT_DB_SALT_2026"


class CryptoVaultEngine:
    """
    AES-256 hardware-derived symmetric cipher engine.
    Binds encryption directly to the physical host hardware GUID & MAC.
    """

    def __init__(self, custom_passphrase: str = "NEXUS_CORE_STORAGE_PASSPHRASE"):
        fp = generate_machine_fingerprint()
        hardware_seed = f"{fp['raw_hash']}::{fp['mac_address']}::{fp['machine_guid']}::{custom_passphrase}"
        
        # Derive 256-bit key using PBKDF2HMAC with SHA-256 and 100,000 iterations
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=_VAULT_SYSTEM_SALT,
            iterations=100_000,
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(hardware_seed.encode("utf-8")))
        self._fernet = Fernet(derived_key)
        self.machine_id = fp["machine_id"]

    def encrypt_bytes(self, data: bytes) -> bytes:
        """Encrypt raw bytes using hardware-locked AES-256."""
        if not data:
            return b""
        return self._fernet.encrypt(data)

    def decrypt_bytes(self, token: bytes) -> bytes:
        """Decrypt AES-256 ciphertext bytes."""
        if not token:
            return b""
        return self._fernet.decrypt(token)

    def encrypt_string(self, text: str) -> str:
        """Encrypt string returning URL-safe base64 string."""
        if not text:
            return ""
        encrypted = self.encrypt_bytes(text.encode("utf-8"))
        return encrypted.decode("utf-8")

    def decrypt_string(self, token: str) -> str:
        """Decrypt encrypted string back to plaintext."""
        if not token:
            return ""
        decrypted = self.decrypt_bytes(token.encode("utf-8"))
        return decrypted.decode("utf-8")

    def encrypt_json(self, data: Any) -> str:
        """Serialize and encrypt Python dictionary or list."""
        json_str = json.dumps(data, ensure_ascii=False)
        return self.encrypt_string(json_str)

    def decrypt_json(self, token: str) -> Any:
        """Decrypt and deserialize back into Python object."""
        if not token:
            return None
        decrypted_str = self.decrypt_string(token)
        return json.loads(decrypted_str)


# Singleton instance
_global_vault_engine = None

def get_crypto_vault() -> CryptoVaultEngine:
    global _global_vault_engine
    if _global_vault_engine is None:
        _global_vault_engine = CryptoVaultEngine()
    return _global_vault_engine
