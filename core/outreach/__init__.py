"""
Outreach package initialization for Nexus-Pulse Multi-Tenant Enterprise.
"""
from .scheduler import TimezoneScheduler, get_scheduler
from .inbox_rotator import InboxRotator, get_inbox_rotator
from .approval_gate import HumanApprovalGate, get_approval_gate, generate_personalized_copy
from .reply_listener import IMAPReplyListener, get_reply_listener, ReplyClassifier
from .template_manager import TemplateManager, get_template_manager
from .blacklist_manager import BlacklistManager, get_blacklist_manager

__all__ = [
    "TimezoneScheduler",
    "get_scheduler",
    "InboxRotator",
    "get_inbox_rotator",
    "HumanApprovalGate",
    "get_approval_gate",
    "generate_personalized_copy",
    "IMAPReplyListener",
    "get_reply_listener",
    "ReplyClassifier",
    "TemplateManager",
    "get_template_manager",
    "BlacklistManager",
    "get_blacklist_manager"
]
