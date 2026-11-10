"""
H.Huddair's Nexus-Pulse - Level 2
Authentication Module: Pure-Python Cryptographic JWT & Industry-Standard Bcrypt Hasher
Implements HMAC-SHA256 JWT tokens and Bcrypt password hashing with PBKDF2 backward compatibility.
"""

import base64
import hashlib
import hmac
import json
import time
from typing import Dict, Any, Optional
import bcrypt

# Secret internal signing key bound to H.Huddair's Nexus-Pulse
_JWT_SECRET = b"HHUDDAIR_NEXUS_PULSE_AUTH_SECRET_KEY_LEVEL_2_2026"
_PASSWORD_SALT = b"HHUDDAIR_SALT_2026"
_TOKEN_EXPIRY_SECONDS = 86400 * 7  # 7-day session token


def hash_password(password: str) -> str:
    """
    Hash password using industry-standard Bcrypt with 12 rounds of salting.
    Guarantees robust resistance to GPU/ASIC rainbow attacks.
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed_bytes = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Securely verify password against stored hash.
    Supports Bcrypt ($2a$, $2b$, $2y$) with PBKDF2 backward compatibility.
    """
    if not plain_password or not hashed_password:
        return False

    hashed_str = hashed_password.strip()

    # Bcrypt format detection
    if hashed_str.startswith("$2a$") or hashed_str.startswith("$2b$") or hashed_str.startswith("$2y$"):
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_str.encode("utf-8"))
        except Exception:
            return False

    # PBKDF2-HMAC-SHA256 backward compatibility
    try:
        computed = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            _PASSWORD_SALT,
            100_000
        ).hex()
        return hmac.compare_digest(computed, hashed_str)
    except Exception:
        return False


def create_access_token(
    user_id: str,
    username: str,
    role: str,
    full_name: str,
    device_id: Optional[str] = None,
    expires_in_seconds: int = _TOKEN_EXPIRY_SECONDS
) -> str:
    """
    Creates an RFC 7519 compliant HMAC-SHA256 JWT token with device binding.
    Format: <header_b64>.<payload_b64>.<signature_b64>
    """
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "full_name": full_name,
        "device_id": device_id or "",
        "iat": now,
        "exp": now + expires_in_seconds
    }

    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode("utf-8")).decode("utf-8").rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8").rstrip("=")

    signature_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(_JWT_SECRET, signature_input, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validates signature and expiration of JWT access token.
    Returns decoded payload if valid, None otherwise.
    """
    if not token or not isinstance(token, str):
        return None

    token = token.strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()

    parts = token.split(".")
    if len(parts) != 3:
        return None

    header_b64, payload_b64, sig_b64 = parts

    # Reconstruct signature
    signature_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(_JWT_SECRET, signature_input, hashlib.sha256).digest()
    expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode("utf-8").rstrip("=")

    if not hmac.compare_digest(sig_b64, expected_sig_b64):
        return None

    # Decode payload
    try:
        padding = 4 - (len(payload_b64) % 4)
        if padding != 4:
            payload_b64 += "=" * padding
        payload_bytes = base64.urlsafe_b64decode(payload_b64.encode("utf-8"))
        payload = json.loads(payload_bytes.decode("utf-8"))

        # Check expiration
        if int(time.time()) > payload.get("exp", 0):
            return None

        return payload
    except Exception:
        return None
