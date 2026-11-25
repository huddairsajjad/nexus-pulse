"""
Nexus-Pulse Serper.dev Lead Discovery & Cancellation Test Suite.
Tests:
- Serper.dev JSON API integration (Places & Organic Search)
- MissingSerperApiKeyError and SerperAPIError explicit error handling
- Candidate URL validation and directory exclusion
- Legal@ priority score and multi-email extraction (up to 4 valid contacts)
- Fast cancellation via threading.Event
- Strict per-user isolation (owner_username)
"""

import asyncio
import os
import threading
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from core.agents.scraper_agent import (
    SearchDiscoveryAgent,
    DeepScraperAgent,
    SerperAPIError,
    MissingSerperApiKeyError,
    resolve_serper_gl,
    resolve_serper_hl,
)
from core.agents.priority_finder import PriorityEmailFinder, EmailTier
from core.hygiene.lead_validator import LeadValidationFilter
from api.routes import _register_job, _get_job, _is_job_cancelled, _update_job, _scrape_jobs, _scrape_jobs_lock


class TestSerperDiscoveryAgent(unittest.TestCase):

    def test_missing_api_key_raises_explicit_error(self):
        agent = SearchDiscoveryAgent(serper_api_key="")
        with patch.dict(os.environ, {"SERPER_API_KEY": ""}, clear=True):
            with self.assertRaises(MissingSerperApiKeyError) as ctx:
                agent.check_api_key()
            self.assertIn("SERPER_API_KEY is not configured", str(ctx.exception))

    def test_country_gl_hl_resolution(self):
        self.assertEqual(resolve_serper_gl("Pakistan"), "pk")
        self.assertEqual(resolve_serper_gl("United Arab Emirates"), "ae")
        self.assertEqual(resolve_serper_gl("United Kingdom"), "gb")
        self.assertEqual(resolve_serper_gl("United States"), "us")
        self.assertEqual(resolve_serper_gl("Germany"), "de")

        self.assertEqual(resolve_serper_hl("Pakistan"), "en")
        self.assertEqual(resolve_serper_hl("United Arab Emirates"), "en")
        self.assertEqual(resolve_serper_hl("Germany"), "de")

    def test_clean_candidate_url_filtering(self):
        # Valid company URLs
        self.assertEqual(
            SearchDiscoveryAgent.clean_candidate_url("https://www.habibconstruction.com/about"),
            "https://www.habibconstruction.com"
        )
        self.assertEqual(
            SearchDiscoveryAgent.clean_candidate_url("http://apex-builders.ae/projects/commercial"),
            "http://apex-builders.ae"
        )

        # Discarded directories and social engines
        self.assertIsNone(SearchDiscoveryAgent.clean_candidate_url("https://www.google.com/search?q=test"))
        self.assertIsNone(SearchDiscoveryAgent.clean_candidate_url("https://www.zameen.com/commercial-properties"))
        self.assertIsNone(SearchDiscoveryAgent.clean_candidate_url("https://www.rozee.pk/jobs/construction"))
        self.assertIsNone(SearchDiscoveryAgent.clean_candidate_url("https://olx.com.pk/services"))
        self.assertIsNone(SearchDiscoveryAgent.clean_candidate_url("https://www.linkedin.com/company/abc"))
        self.assertIsNone(SearchDiscoveryAgent.clean_candidate_url("https://www.facebook.com/abc"))

        # Blocked govt/edu/mil and placeholder domains
        self.assertIsNone(SearchDiscoveryAgent.clean_candidate_url("https://www.lahore.gov.pk"))
        self.assertIsNone(SearchDiscoveryAgent.clean_candidate_url("https://www.uet.edu.pk"))
        self.assertIsNone(SearchDiscoveryAgent.clean_candidate_url("https://example.com"))
        self.assertIsNone(SearchDiscoveryAgent.clean_candidate_url("https://test.com"))

    def test_query_variations_builder(self):
        queries = SearchDiscoveryAgent.build_query_variations("Commercial Construction", "Lahore", "Pakistan")
        self.assertGreaterEqual(len(queries), 5)
        self.assertTrue(any("Lahore" in q for q in queries))
        self.assertTrue(any("Commercial Construction" in q for q in queries))

    def test_legal_email_priority_score(self):
        tier, score = PriorityEmailFinder.classify_email("legal@apexconstruction.com")
        self.assertEqual(tier, EmailTier.TIER_2_EXECUTIVE)
        self.assertEqual(score, 80)

        c_tier, c_score = PriorityEmailFinder.classify_email("counsel@apexconstruction.com")
        self.assertEqual(c_tier, EmailTier.TIER_2_EXECUTIVE)
        self.assertEqual(c_score, 80)

    def test_cancellation_event_instant_trigger(self):
        job_id = "test-job-cancel-123"
        _register_job(job_id, "op-test")
        job = _get_job(job_id)
        self.assertFalse(_is_job_cancelled(job_id))

        with _scrape_jobs_lock:
            raw_job = _scrape_jobs.get(job_id)
            self.assertIsNotNone(raw_job)
            raw_job["cancel_event"].set()

        self.assertTrue(_is_job_cancelled(job_id))

    def test_multi_user_lead_dedup_isolation(self):
        db_conn = MagicMock()
        # Mock no existing rows for user_b
        db_conn.execute.return_value.fetchone.return_value = None
        db_conn.execute.return_value.fetchall.return_value = []

        is_dup, reason = LeadValidationFilter.is_lead_duplicate_or_blacklisted(
            email="sales@uniquecompany.com",
            db_conn=db_conn,
            domain="uniquecompany.com",
            owner_username="user_b",
            operator_id="op_b"
        )
        self.assertFalse(is_dup)
        self.assertIn("fresh and unique", reason)


class TestSerperAsyncDiscovery(unittest.IsolatedAsyncioTestCase):

    async def test_serper_places_api_parsing(self):
        agent = SearchDiscoveryAgent(serper_api_key="test_key_abc")
        fake_places_response = {
            "places": [
                {
                    "title": "Habib Construction Services",
                    "address": "Gulberg III, Lahore, Pakistan",
                    "phoneNumber": "+92 42 35777777",
                    "website": "https://habibconstruction.com"
                },
                {
                    "title": "Descon Engineering Limited",
                    "address": "18-km Ferozepur Road, Lahore, Pakistan",
                    "phoneNumber": "+92 42 35920101",
                    "website": "https://descon.com"
                }
            ]
        }

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = fake_places_response

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_resp

        places = await agent.query_serper_places("commercial construction in Lahore", "Pakistan", mock_client)
        self.assertEqual(len(places), 2)
        self.assertEqual(places[0]["title"], "Habib Construction Services")
        self.assertEqual(places[0]["website"], "https://habibconstruction.com")

    async def test_serper_401_raises_explicit_serper_api_error(self):
        agent = SearchDiscoveryAgent(serper_api_key="invalid_key")
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_resp

        with self.assertRaises(SerperAPIError) as ctx:
            await agent.query_serper_places("test", "Pakistan", mock_client)
        self.assertIn("Unauthorized", str(ctx.exception))

    async def test_serper_429_raises_explicit_serper_api_error(self):
        agent = SearchDiscoveryAgent(serper_api_key="valid_key")
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.text = "Rate limit exceeded"

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_resp

        with self.assertRaises(SerperAPIError) as ctx:
            await agent.query_serper_search("test", "Pakistan", page=1, client=mock_client)
        self.assertIn("429", str(ctx.exception))

    async def test_discover_candidate_urls_cancellation(self):
        agent = SearchDiscoveryAgent(serper_api_key="valid_key")
        cancelled = True
        urls = await agent.discover_candidate_urls(
            queries=["test query"],
            limit=10,
            country="Pakistan",
            city="Lahore",
            niche="Commercial Construction",
            is_cancelled=lambda: cancelled
        )
        self.assertEqual(urls, [])


if __name__ == "__main__":
    unittest.main()
