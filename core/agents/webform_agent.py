"""
H.Huddair's Nexus-Pulse - Level 2
Agent Module: Backup Web-Form Outreach Agent
If direct valid emails are missing or invalid, formats clean, structured outreach messages
for the target enterprise's official 'Contact Us' / 'Tenders' web form.
"""

from typing import Dict, Any, Optional
from urllib.parse import urlparse
from ..outreach.approval_gate import get_approval_gate


class BackupWebFormAgent:
    """
    Constructs structured web-form submission payloads for companies without direct emails.
    """

    DEFAULT_SENDER = {
        "full_name": "H.Huddair",
        "company": "Nexus-Pulse Commercial Estimating",
        "email": "estimating@huddair-global.com",
        "phone": "+44 20 7946 0988",
        "title": "Commercial Director"
    }

    @classmethod
    def format_web_form_payload(
        cls,
        company_name: str,
        website_url: str,
        niche: str,
        country: str,
        contact_page_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a clean, formatted web form payload ready for submission or manual dispatch.
        """
        domain = urlparse(website_url).netloc.replace("www.", "")
        target_form_url = contact_page_url or f"https://www.{domain}/contact"

        clean_niche = niche or "Commercial Contracting"
        subject = f"Tender Estimation & Prequalification // {company_name}"

        # Clean web-form message formatted for form textarea fields
        message_body = (
            f"Dear Estimating & Commercial Department at {company_name},\n\n"
            f"We are submitting our commercial capabilities and prequalification credentials for upcoming {clean_niche} "
            f"tender packages in {country}.\n\n"
            f"Our team provides high-precision bill-of-quantities takeoff, fast estimating turnaround, and competitive "
            f"subcontractor package pricing.\n\n"
            f"Please let us know where we can forward our commercial credentials, or add our estimating team "
            f"(estimating@huddair-global.com) to your active tender distribution list.\n\n"
            f"Thank you,\n"
            f"H.Huddair | Commercial Director | Nexus-Pulse"
        )

        return {
            "form_url": target_form_url,
            "fields": {
                "name": cls.DEFAULT_SENDER["full_name"],
                "company": cls.DEFAULT_SENDER["company"],
                "email": cls.DEFAULT_SENDER["email"],
                "phone": cls.DEFAULT_SENDER["phone"],
                "subject": subject,
                "inquiry_type": "Tenders & Subcontracting",
                "message": message_body
            },
            "channel": "WEB_FORM",
            "company_name": company_name,
            "country": country,
            "domain": domain
        }

    @classmethod
    def queue_web_form_in_approval_gate(
        cls,
        lead_id: str,
        company_name: str,
        website_url: str,
        niche: str,
        country: str,
        contact_page_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Formats web-form outreach and places it directly into the Human Approval Gate.
        """
        payload = cls.format_web_form_payload(company_name, website_url, niche, country, contact_page_url)
        gate = get_approval_gate()

        gate_res = gate.queue_outreach(
            lead_id=lead_id,
            company_name=company_name,
            recipient=payload["form_url"],
            country=country,
            niche=niche,
            channel="WEB_FORM",
            custom_subject=payload["fields"]["subject"],
            custom_body=payload["fields"]["message"]
        )

        return {
            "success": True,
            "channel": "WEB_FORM",
            "form_url": payload["form_url"],
            "queue_id": gate_res["queue_id"],
            "status": "PENDING_APPROVAL",
            "hold_message": "Web-Form outreach held in Human Approval Gate for H.Huddair."
        }
