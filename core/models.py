"""
H.Huddair's Nexus-Pulse - Level 1
Data Models: Enterprise Pydantic Models for Leads, Targets, Priorities, and Vault Partitions.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class EmailTier(str, Enum):
    TIER_1_ESTIMATING = "TIER_1_ESTIMATING"    # estimating@, bids@, tenders@, qs@, procurement@, rfp@
    TIER_2_EXECUTIVE = "TIER_2_EXECUTIVE"      # director@, commercial@, projects@, contracts@, operations@
    TIER_3_OPERATIONAL = "TIER_3_OPERATIONAL"  # admin@, accounts@, office@, contact@
    TIER_GENERIC = "TIER_GENERIC"              # info@, hello@, support@
    UNKNOWN = "UNKNOWN"


class HygieneStatus(str, Enum):
    VERIFIED = "VERIFIED"                      # Passed all 3 stages: Syntax + DNS MX + SMTP Ping
    SYNTAX_INVALID = "SYNTAX_INVALID"          # Failed RFC 5322 or disposable email domain
    DOMAIN_NO_MX = "DOMAIN_NO_MX"              # Domain does not have active MX records
    SMTP_REJECTED = "SMTP_REJECTED"            # SMTP Ping returned 550 User Unknown / Mailbox not found
    SMTP_INDETERMINATE = "SMTP_INDETERMINATE"  # Port 25 blocked or SMTP Greylisted / Anti-spam timeout


class TechStack(BaseModel):
    cms: List[str] = Field(default_factory=list, description="Content management systems (WordPress, Webflow, Shopify, etc.)")
    frontend_frameworks: List[str] = Field(default_factory=list, description="UI frameworks (React, Next.js, Vue, Tailwind, etc.)")
    crm_and_marketing: List[str] = Field(default_factory=list, description="Marketing & CRM tools (HubSpot, Salesforce, Klaviyo, GA4, etc.)")
    web_server_and_cdn: List[str] = Field(default_factory=list, description="Server & CDN (Cloudflare, Nginx, Apache, Vercel, etc.)")
    raw_technologies: List[str] = Field(default_factory=list)


class ScrapedEmail(BaseModel):
    email: str
    normalized_email: str
    prefix: str
    domain: str
    tier: EmailTier
    priority_score: int = Field(description="Score from 0 to 100 based on value density")
    found_on_page: str
    context_snippet: Optional[str] = None


class HygieneReport(BaseModel):
    email: str
    status: HygieneStatus
    stage_1_syntax_valid: bool = False
    is_disposable_domain: bool = False
    stage_2_mx_valid: bool = False
    mx_records: List[str] = Field(default_factory=list)
    stage_3_smtp_valid: Optional[bool] = None
    smtp_response_code: Optional[int] = None
    smtp_diagnostic_message: Optional[str] = None
    verification_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Lead(BaseModel):
    id: Optional[str] = None
    company_name: str
    domain: str
    website_url: str
    target_country: str
    target_city: str
    industry_niche: str
    primary_email: str
    primary_email_tier: EmailTier
    priority_score: int = 0
    all_emails: List[ScrapedEmail] = Field(default_factory=list)
    phone_numbers: List[str] = Field(default_factory=list)
    address: Optional[str] = None
    tech_stack: TechStack = Field(default_factory=TechStack)
    hygiene_report: Optional[HygieneReport] = None
    quality_tag: str = "UNTAGGED"
    scraped_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    ready_to_send: bool = False
    dedup_hash: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScrapeTarget(BaseModel):
    query: str
    country: str
    city: str
    niche: str
    language_code: str
    estimated_results: int = 10


# -------------------------------------------------------------
# LEVEL 2 ENTERPRISE MODELS
# -------------------------------------------------------------
class KanbanStage(str, Enum):
    SCRAPED = "SCRAPED"
    VERIFIED = "VERIFIED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    SENT = "SENT"
    REPLIED = "REPLIED"
    HOT_LEAD = "HOT_LEAD"
    CLOSED = "CLOSED"


class AgentIconState(str, Enum):
    IDLE = "IDLE"              # Ambient slow-pulse glow
    HUNTING = "HUNTING"        # Fast radar-scan rotation effect
    HOT_ALERT = "HOT_ALERT"    # High-priority red/gold flashing pulse effect


class OutreachItemModel(BaseModel):
    id: str
    lead_id: Optional[str] = None
    channel: str = "EMAIL"
    recipient: str
    company_name: str
    subject: str
    message_body: str
    status: str = "PENDING_APPROVAL"
    target_country: str = "Germany"
    target_timezone: str = "CET"
    scheduled_for: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    sent_at: Optional[str] = None
    mailbox_used: Optional[str] = None
    created_at: Optional[str] = None


class InboxReplyModel(BaseModel):
    id: str
    lead_id: Optional[str] = None
    sender_email: str
    company_name: str
    subject: str
    message_body: str
    classification: str
    is_hot_lead: bool = False
    ai_suggested_reply: Optional[str] = None
    received_at: Optional[str] = None
    status: str = "UNREAD"


class UserProfile(BaseModel):
    id: str
    username: str
    role: str
    full_name: str


class AuthResponse(BaseModel):
    token: str
    user: UserProfile

