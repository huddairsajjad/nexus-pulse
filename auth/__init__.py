"""
Auth module initialization for Nexus-Pulse Level 2.
"""
from .jwt_handler import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)
from .user_manager import UserManager, get_user_manager

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "UserManager",
    "get_user_manager"
]
