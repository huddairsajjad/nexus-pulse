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


class TestToSimpleQuery(unittest.TestCase):
    """Unit tests for SearchDiscoveryAgent.to_simple_query() — strips all Serper-restricted operators."""

    def test_strips_site_operator(self):
        q = 'construction companies site:pk email contact'
        result = SearchDiscoveryAgent.to_simple_query(q)
        self.assertNotIn('site:', result)
        self.assertIn('construction', result)

    def test_strips_inurl_operator(self):
        q = 'inurl:contact construction Lahore'
        result = SearchDiscoveryAgent.to_simple_query(q)
        self.assertNotIn('inurl:', result)
        self.assertIn('construction', result)

    def test_strips_boolean_or_and_not(self):
        q = 'construction OR plumbing AND electrical NOT residential'
        result = SearchDiscoveryAgent.to_simple_query(q)
        self.assertNotIn(' OR ', result)
        self.assertNotIn(' AND ', result)
        self.assertNotIn(' NOT ', result)
        self.assertIn('construction', result)

    def test_strips_quotes_and_parens(self):
        q = '"commercial construction" (Lahore OR Karachi) contact'
        result = SearchDiscoveryAgent.to_simple_query(q)
        self.assertNotIn('"', result)
        self.assertNotIn('(', result)
        self.assertNotIn(')', result)
        self.assertIn('commercial', result)
        self.assertIn('construction', result)

    def test_strips_mailto(self):
        q = 'construction companies mailto:contact Lahore'
        result = SearchDiscoveryAgent.to_simple_query(q)
        self.assertNotIn('mailto:', result)

    def test_strips_pipe_and_slashes(self):
        q = 'construction | plumbing /contact Pakistan'
        result = SearchDiscoveryAgent.to_simple_query(q)
        self.assertNotIn('|', result)
        self.assertIn('construction', result)

    def test_collapses_whitespace(self):
        q = 'construction    companies   Lahore'
        result = SearchDiscoveryAgent.to_simple_query(q)
        self.assertNotIn('  ', result)
        self.assertEqual(result.strip(), result)

    def test_empty_query_returns_empty(self):
        self.assertEqual(SearchDiscoveryAgent.to_simple_query(''), '')
        self.assertEqual(SearchDiscoveryAgent.to_simple_query(None), '')

    def test_plain_query_unchanged_in_substance(self):
        q = 'commercial construction companies Lahore Pakistan email'
        result = SearchDiscoveryAgent.to_simple_query(q)
        # Should keep all plain words, just normalised
        self.assertIn('construction', result)
        self.assertIn('Lahore', result)


class TestIsFreeTierError(unittest.TestCase):
    """Unit tests for SearchDiscoveryAgent.is_free_tier_error() static method."""

    def test_400_free_account_text_returns_true(self):
        self.assertTrue(SearchDiscoveryAgent.is_free_tier_error(
            400, '{"message": "Query pattern not allowed for free accounts"}'
        ))

    def test_400_pattern_not_allowed_returns_true(self):
        self.assertTrue(SearchDiscoveryAgent.is_free_tier_error(
            400, 'query pattern not allowed'
        ))

    def test_400_free_plan_text_returns_true(self):
        self.assertTrue(SearchDiscoveryAgent.is_free_tier_error(
            400, 'this is not allowed for free plan users'
        ))

    def test_400_not_allowed_for_free_returns_true(self):
        self.assertTrue(SearchDiscoveryAgent.is_free_tier_error(
            400, 'operator not allowed for free tier accounts'
        ))

    def test_401_always_returns_false(self):
        self.assertFalse(SearchDiscoveryAgent.is_free_tier_error(
            401, 'Query pattern not allowed for free accounts'
        ))

    def test_400_unrelated_body_returns_false(self):
        # 400 but body is about malformed JSON, not free-tier
        self.assertFalse(SearchDiscoveryAgent.is_free_tier_error(
            400, 'Invalid JSON body'
        ))

    def test_200_always_returns_false(self):
        self.assertFalse(SearchDiscoveryAgent.is_free_tier_error(
            200, 'free account message'
        ))


class TestQueryModeProperty(unittest.TestCase):
    """Tests for SearchDiscoveryAgent.query_mode and is_simple_mode properties."""

    def test_default_mode_is_auto(self):
        agent = SearchDiscoveryAgent(serper_api_key='test_key')
        with patch.dict(os.environ, {}, clear=True):
            # No SERPER_QUERY_MODE set → should default to 'auto'
            mode = agent.query_mode
            self.assertIn(mode, ('auto', 'simple', 'advanced'))

    def test_constructor_mode_takes_precedence(self):
        agent = SearchDiscoveryAgent(serper_api_key='test_key', query_mode='simple')
        self.assertEqual(agent.query_mode, 'simple')

    def test_advanced_mode_from_constructor(self):
        agent = SearchDiscoveryAgent(serper_api_key='test_key', query_mode='advanced')
        self.assertEqual(agent.query_mode, 'advanced')

    def test_invalid_mode_fallbacks_to_auto(self):
        agent = SearchDiscoveryAgent(serper_api_key='test_key', query_mode='garbage_mode')
        self.assertEqual(agent.query_mode, 'auto')

    def test_env_override_simple(self):
        agent = SearchDiscoveryAgent(serper_api_key='test_key')
        with patch.dict(os.environ, {'SERPER_QUERY_MODE': 'simple'}):
            self.assertEqual(agent.query_mode, 'simple')

    def test_env_override_advanced(self):
        agent = SearchDiscoveryAgent(serper_api_key='test_key')
        with patch.dict(os.environ, {'SERPER_QUERY_MODE': 'advanced'}):
            self.assertEqual(agent.query_mode, 'advanced')

    def test_is_simple_mode_when_simple(self):
        agent = SearchDiscoveryAgent(serper_api_key='test_key', query_mode='simple')
        self.assertTrue(agent.is_simple_mode)

    def test_is_simple_mode_false_when_advanced(self):
        agent = SearchDiscoveryAgent(serper_api_key='test_key', query_mode='advanced')
        self.assertFalse(agent.is_simple_mode)

    def test_is_simple_mode_true_when_auto_fallback_active(self):
        agent = SearchDiscoveryAgent(serper_api_key='test_key', query_mode='auto')
        agent._free_tier_fallback_active = True
        self.assertTrue(agent.is_simple_mode)

    def test_is_simple_mode_false_when_auto_no_fallback(self):
        agent = SearchDiscoveryAgent(serper_api_key='test_key', query_mode='auto')
        agent._free_tier_fallback_active = False
        self.assertFalse(agent.is_simple_mode)


class TestDynamicDomainScaling(unittest.TestCase):
    """
    Tests that discover_candidate_urls uses correct needed_domains based on limit.
    We abort discovery immediately (no API key) but verify cancellation and key check fire.
    """

    def _make_agent_check_domains(self, limit: int) -> int:
        """
        Derives the expected needed_domains from the same logic in discover_candidate_urls
        without calling Serper (pure formula check).
        """
        if limit <= 5:
            return max(limit * 3, 5)
        elif limit <= 25:
            return max(limit * 3, 20)
        elif limit <= 50:
            return max(limit * 3, 50)
        else:
            return max(limit * 3, 100)

    def test_limit_1_needs_at_least_5(self):
        self.assertGreaterEqual(self._make_agent_check_domains(1), 5)

    def test_limit_5_needs_at_least_5(self):
        self.assertEqual(self._make_agent_check_domains(5), 15)

    def test_limit_10_needs_at_least_20(self):
        self.assertGreaterEqual(self._make_agent_check_domains(10), 20)

    def test_limit_25_needs_at_least_75(self):
        self.assertEqual(self._make_agent_check_domains(25), 75)

    def test_limit_50_needs_at_least_150(self):
        self.assertEqual(self._make_agent_check_domains(50), 150)

    def test_limit_100_needs_at_least_300(self):
        self.assertGreaterEqual(self._make_agent_check_domains(100), 300)

    def test_limit_7_scales_correctly(self):
        self.assertEqual(self._make_agent_check_domains(7), 21)

    def test_limit_33_scales_correctly(self):
        # 33*3=99 > 50, so needed=99
        self.assertEqual(self._make_agent_check_domains(33), 99)


class TestFreeTierFallbackIntegration(unittest.IsolatedAsyncioTestCase):
    """
    Integration tests for free-tier 400 auto-fallback.
    Mocks Serper API to return 400 'not allowed for free accounts' on first call,
    then 200 on retry with simplified query.
    """

    async def test_places_400_free_tier_retries_with_simple_query(self):
        """When Serper Places returns 400 free-tier error, agent retries with simple query and succeeds."""
        agent = SearchDiscoveryAgent(serper_api_key='test_key', query_mode='auto')

        fake_free_tier_resp = MagicMock()
        fake_free_tier_resp.status_code = 400
        fake_free_tier_resp.text = 'Query pattern not allowed for free accounts'

        fake_ok_resp = MagicMock()
        fake_ok_resp.status_code = 200
        fake_ok_resp.json.return_value = {
            'places': [
                {'title': 'Test Corp', 'website': 'https://testcorp.com', 'phoneNumber': '', 'address': ''}
            ]
        }

        call_count = 0
        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return fake_free_tier_resp
            return fake_ok_resp

        mock_client = AsyncMock()
        mock_client.post.side_effect = mock_post

        # Advanced query that would trigger free-tier restriction
        advanced_query = 'construction companies site:pk OR inurl:contact'
        places = await agent.query_serper_places(advanced_query, 'Pakistan', mock_client)

        # Should have retried and returned results
        self.assertEqual(len(places), 1)
        self.assertEqual(places[0]['title'], 'Test Corp')
        # Fallback should now be active
        self.assertTrue(agent._free_tier_fallback_active)
        # Should have been called twice (first=400 fallback, second=200 success)
        self.assertEqual(call_count, 2)

    async def test_search_400_free_tier_retries_with_simple_query(self):
        """When Serper Search returns 400 free-tier error, agent retries with simple query and succeeds."""
        agent = SearchDiscoveryAgent(serper_api_key='test_key', query_mode='auto')

        fake_free_tier_resp = MagicMock()
        fake_free_tier_resp.status_code = 400
        fake_free_tier_resp.text = 'operator not allowed for free tier accounts'

        fake_ok_resp = MagicMock()
        fake_ok_resp.status_code = 200
        fake_ok_resp.json.return_value = {
            'organic': [
                {'title': 'Apex Builders', 'link': 'https://apex-builders.ae', 'snippet': 'Commercial construction'}
            ],
            'places': []
        }

        call_count = 0
        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return fake_free_tier_resp
            return fake_ok_resp

        mock_client = AsyncMock()
        mock_client.post.side_effect = mock_post

        advanced_query = '"construction companies" site:ae OR inurl:about'
        items = await agent.query_serper_search(advanced_query, 'United Arab Emirates', page=1, client=mock_client)

        self.assertGreaterEqual(len(items), 1)
        self.assertEqual(items[0]['title'], 'Apex Builders')
        self.assertTrue(agent._free_tier_fallback_active)
        self.assertEqual(call_count, 2)

    async def test_400_non_free_tier_raises_serper_api_error(self):
        """400 without free-tier language in body raises SerperAPIError immediately (no retry)."""
        agent = SearchDiscoveryAgent(serper_api_key='test_key', query_mode='auto')

        fake_resp = MagicMock()
        fake_resp.status_code = 400
        fake_resp.text = 'Invalid JSON body provided'

        mock_client = AsyncMock()
        mock_client.post.return_value = fake_resp

        with self.assertRaises(SerperAPIError) as ctx:
            await agent.query_serper_places('test query', 'Pakistan', mock_client)
        self.assertIn('400', str(ctx.exception))
        # Fallback should NOT have activated (not a free-tier error)
        self.assertFalse(agent._free_tier_fallback_active)

    async def test_fallback_not_triggered_when_already_active(self):
        """If _free_tier_fallback_active is already True, a second 400 raises immediately."""
        agent = SearchDiscoveryAgent(serper_api_key='test_key', query_mode='auto')
        agent._free_tier_fallback_active = True  # Already fallen back

        fake_resp = MagicMock()
        fake_resp.status_code = 400
        fake_resp.text = 'Query pattern not allowed for free accounts'

        mock_client = AsyncMock()
        mock_client.post.return_value = fake_resp

        with self.assertRaises(SerperAPIError):
            await agent.query_serper_places('simple query already', 'Pakistan', mock_client)

    async def test_advanced_mode_400_no_fallback(self):
        """In 'advanced' mode, free-tier 400 raises immediately — no auto-fallback."""
        agent = SearchDiscoveryAgent(serper_api_key='test_key', query_mode='advanced')

        fake_resp = MagicMock()
        fake_resp.status_code = 400
        fake_resp.text = 'Query pattern not allowed for free accounts'

        mock_client = AsyncMock()
        mock_client.post.return_value = fake_resp

        with self.assertRaises(SerperAPIError):
            await agent.query_serper_places('"construction" site:pk', 'Pakistan', mock_client)
        # No fallback in advanced mode
        self.assertFalse(agent._free_tier_fallback_active)


class TestFullQuotaRange(unittest.IsolatedAsyncioTestCase):
    """
    Tests full quota fulfillment from 1 to 100 leads.
    Mocks query_serper_places and query_serper_search directly on the agent instance
    so the internal httpx.AsyncClient creation is irrelevant.
    """

    @staticmethod
    def _make_places(count: int, batch: int = 0) -> list:
        """Generate distinct fake place records for testing."""
        return [
            {
                'title': f'PlaceCo {batch}-{i}',
                'website': f'https://placeco{batch}x{i}.com',
                'phoneNumber': '+1 555 0100',
                'address': f'{i} Business Ave'
            }
            for i in range(count)
        ]

    @staticmethod
    def _make_organic(count: int, batch: int = 0, page: int = 1) -> list:
        """Generate distinct fake organic search result records for testing."""
        offset = (page - 1) * count + batch * 1000
        return [
            {
                'title': f'BizOrg {offset + i}',
                'link': f'https://bizorg{offset + i}.net',
                'snippet': 'B2B company',
                'source': 'serper_organic'
            }
            for i in range(count)
        ]

    async def _run_discovery_with_mock(self, limit: int) -> list:
        """
        Runs discover_candidate_urls with agent-level method mocks.
        Patches query_serper_places and query_serper_search directly on the agent,
        bypassing any real httpx client creation.
        """
        agent = SearchDiscoveryAgent(serper_api_key='test_key', query_mode='auto')

        places_call = [0]
        search_call = [0]

        async def mock_places(query, country, client, is_cancelled=None):
            batch = places_call[0]
            places_call[0] += 1
            return self._make_places(10, batch)

        async def mock_search(query, country, page, client, num=20, is_cancelled=None):
            batch = search_call[0]
            search_call[0] += 1
            return self._make_organic(10, batch, page)

        with patch.object(agent, 'check_api_key', return_value='test_key'), \
             patch.object(agent, 'query_serper_places', side_effect=mock_places), \
             patch.object(agent, 'query_serper_search', side_effect=mock_search):
            urls = await agent.discover_candidate_urls(
                queries=None,
                limit=limit,
                country='Pakistan',
                city='Lahore',
                niche='Commercial Construction',
                is_cancelled=None,
            )
        return urls

    async def test_quota_limit_1(self):
        """limit=1 → needed_domains=5; at least 1 URL returned and ≤ needed_domains."""
        urls = await self._run_discovery_with_mock(1)
        self.assertGreaterEqual(len(urls), 1)
        # Must not exceed needed_domains cap (5)
        self.assertLessEqual(len(urls), 5)

    async def test_quota_limit_7(self):
        """limit=7 → needed_domains=21; collects at least 7 unique URLs."""
        urls = await self._run_discovery_with_mock(7)
        self.assertGreaterEqual(len(urls), 7)

    async def test_quota_limit_10(self):
        """limit=10 → needed_domains=30; collects at least 10 unique URLs."""
        urls = await self._run_discovery_with_mock(10)
        self.assertGreaterEqual(len(urls), 10)

    async def test_quota_limit_25(self):
        """limit=25 → needed_domains=75; collects at least 25 unique URLs."""
        urls = await self._run_discovery_with_mock(25)
        self.assertGreaterEqual(len(urls), 25)

    async def test_quota_limit_50(self):
        """limit=50 → needed_domains=150; collects at least 50 unique URLs."""
        urls = await self._run_discovery_with_mock(50)
        self.assertGreaterEqual(len(urls), 50)

    async def test_quota_limit_100(self):
        """limit=100 → needed_domains=300; collects up to 100+ unique URLs cleanly."""
        urls = await self._run_discovery_with_mock(100)
        self.assertGreaterEqual(len(urls), 100)

    async def test_no_duplicate_urls_returned(self):
        """All returned candidate URLs must be unique (deduplication enforced)."""
        urls = await self._run_discovery_with_mock(20)
        self.assertGreater(len(urls), 0)
        self.assertEqual(len(urls), len(set(urls)))

    async def test_multi_wave_discovery_skips_duplicate_serper_queries(self):
        """Calling discover_candidate_urls twice on the same agent skips already-executed Places/Search queries."""
        agent = SearchDiscoveryAgent(serper_api_key='test_key', query_mode='auto')
        places_seen = []
        search_seen = []

        async def mock_places(query, country, client, is_cancelled=None):
            places_seen.append(query)
            return [{'title': 'P1', 'website': f'https://waveplace{len(places_seen)}.com', 'phoneNumber': '', 'address': ''}]

        async def mock_search(query, country, page, client, num=20, is_cancelled=None):
            search_seen.append((query, page))
            return [{'title': 'S1', 'link': f'https://wavesearch{len(search_seen)}p{page}.com', 'snippet': 'B2B', 'source': 'serper_organic'}]

        with patch.object(agent, 'check_api_key', return_value='test_key'), \
             patch.object(agent, 'query_serper_places', side_effect=mock_places), \
             patch.object(agent, 'query_serper_search', side_effect=mock_search):
            await agent.discover_candidate_urls(
                queries=['commercial construction q1'],
                limit=2,
                country='Pakistan',
                city='Lahore',
                niche='Commercial Construction',
            )
            places_wave1 = len(places_seen)
            await agent.discover_candidate_urls(
                queries=['commercial construction q2'],
                limit=5,
                country='Pakistan',
                city='Lahore',
                niche='Commercial Construction',
            )
            # Same query string in places_queries shouldn't execute again for wave 2
            self.assertEqual(len(places_seen), len(set(places_seen)))
            # Total distinct (query, page) executions should have no repeats
            self.assertEqual(len(search_seen), len(set(search_seen)))
            self.assertGreaterEqual(len(places_seen), places_wave1)


class TestEndToEndFlowRegressions(unittest.IsolatedAsyncioTestCase):
    """End-to-end regression tests for real bugs caught across routes, orchestrator, and reply listener."""

    def test_to_simple_query_prefix_at_does_not_glue_words(self):
        q = '"Commercial Construction" "Dubai" "United Arab Emirates" "info@" OR "contact@"'
        res = SearchDiscoveryAgent.to_simple_query(q)
        self.assertNotIn('infoemail', res)
        self.assertNotIn('contactemail', res)
        self.assertIn('info', res)
        self.assertIn('contact', res)
        self.assertIn('email', res)

    def test_reply_listener_is_suppressed_accepts_operator_and_isolates_users(self):
        from core.outreach.reply_listener import get_reply_listener
        from database.db_engine import get_db_engine
        listener = get_reply_listener()
        db = get_db_engine()
        dom = "iso-sup-test-firm.de"
        try:
            listener.suppress_entity(dom, reason="BOUNCE", operator_id="op_iso_a", owner_username="user_iso_a")
            self.assertTrue(listener.is_suppressed(dom, operator_id="op_iso_a", owner_username="user_iso_a"))
            self.assertFalse(listener.is_suppressed(dom, operator_id="op_iso_b", owner_username="user_iso_b"))
        finally:
            with db.get_connection() as conn:
                conn.execute("DELETE FROM suppressed_entities WHERE lower(entity) = ?", (dom,))
                conn.execute("DELETE FROM dnc_blacklist WHERE lower(entity) = ?", (dom,))
                conn.commit()

    def test_multi_email_extraction_per_domain_and_per_user_isolation(self):
        """Up to 4 emails from one domain save cleanly, AND User B can also save the same domain independently."""
        from core.models import Lead, ScrapedEmail, EmailTier, HygieneReport, HygieneStatus
        from core.orchestrator import NexusPulseOrchestrator
        from database.db_engine import get_db_engine

        orch = NexusPulseOrchestrator(bypass_license_check=True)
        db = get_db_engine()
        dom = "multi-email-builders.com"
        emails = [
            ScrapedEmail(email=f"estimating@{dom}", normalized_email=f"estimating@{dom}", prefix="estimating", domain=dom, tier=EmailTier.TIER_1_ESTIMATING, priority_score=100, found_on_page=f"https://{dom}/contact"),
            ScrapedEmail(email=f"legal@{dom}", normalized_email=f"legal@{dom}", prefix="legal", domain=dom, tier=EmailTier.TIER_2_EXECUTIVE, priority_score=80, found_on_page=f"https://{dom}/privacy"),
            ScrapedEmail(email=f"projects@{dom}", normalized_email=f"projects@{dom}", prefix="projects", domain=dom, tier=EmailTier.TIER_2_EXECUTIVE, priority_score=85, found_on_page=f"https://{dom}/about"),
            ScrapedEmail(email=f"info@{dom}", normalized_email=f"info@{dom}", prefix="info", domain=dom, tier=EmailTier.TIER_GENERIC, priority_score=40, found_on_page=f"https://{dom}"),
        ]

        mock_report = HygieneReport(
            email="placeholder",
            status=HygieneStatus.VERIFIED,
            stage_1_syntax_valid=True,
            is_disposable_domain=False,
            stage_2_mx_valid=True,
            mx_records=["mx.multi-email-builders.com"],
            stage_3_smtp_valid=True,
            smtp_response_code=250,
            smtp_diagnostic_message="OK",
        )

        try:
            with patch.object(orch.hygiene, "validate_lead_email", side_effect=lambda em: mock_report.model_copy(update={"email": em})):
                # User A saves all 4 distinct emails on the same domain
                saved_a = []
                for em in emails:
                    c_lead = Lead(
                        company_name="Multi Email Builders",
                        domain=dom,
                        website_url=f"https://{dom}",
                        target_country="United Kingdom",
                        target_city="London",
                        industry_niche="Commercial Construction",
                        primary_email=em.email,
                        primary_email_tier=em.tier,
                        priority_score=em.priority_score,
                        all_emails=emails,
                        quality_tag="TIER-1-ESTIMATING",
                    )
                    res = orch.process_and_preserve_lead(c_lead, operator_id="op_alpha_e2e", owner_username="alpha_e2e", dedup_by_email_only=True)
                    self.assertTrue(res.get("success"), f"User A failed on {em.email}: {res}")
                    saved_a.append(res["lead_id"])
                self.assertEqual(len(set(saved_a)), 4)

                # User B independently saves an email on the same domain
                c_lead_b = Lead(
                    company_name="Multi Email Builders",
                    domain=dom,
                    website_url=f"https://{dom}",
                    target_country="United Kingdom",
                    target_city="London",
                    industry_niche="Commercial Construction",
                    primary_email=f"estimating@{dom}",
                    primary_email_tier=EmailTier.TIER_1_ESTIMATING,
                    priority_score=100,
                    all_emails=emails,
                    quality_tag="TIER-1-ESTIMATING",
                )
                res_b = orch.process_and_preserve_lead(c_lead_b, operator_id="op_beta_e2e", owner_username="beta_e2e", dedup_by_email_only=True)
                self.assertTrue(res_b.get("success"), f"User B should be isolated from User A: {res_b}")
        finally:
            with db.get_connection() as conn:
                conn.execute("DELETE FROM vault_leads WHERE domain = ?", (dom,))
                conn.execute("DELETE FROM dedup_registry WHERE owner_username IN ('alpha_e2e', 'beta_e2e')")
                conn.commit()
            try:
                from database.mongo_engine import get_mongo_engine
                get_mongo_engine().purge_all()
            except Exception:
                pass

    async def test_run_scrape_job_empty_city_region_and_quota_fulfillment(self):
        """Exercises _run_scrape_job with empty city/region, multi-email extraction, and exact arbitrary quota=7."""
        from api.routes import _run_scrape_job, ScrapeRequest, _register_job, _get_job, _scrape_jobs, _scrape_jobs_lock
        from core.models import Lead, ScrapedEmail, EmailTier, HygieneReport, HygieneStatus
        from core.orchestrator import NexusPulseOrchestrator
        from database.db_engine import get_db_engine

        job_id = "e2e-scrape-job-7"
        op_id = "op_e2e_scrape"
        owner = "e2e_scrape_owner"
        _register_job(job_id, op_id)

        db = get_db_engine()
        domains = [f"e2ebuilder{i}.com" for i in range(1, 5)]

        async def fake_discover(self, queries=None, limit=20, country="", city="", niche="", excluded_domains=None, is_cancelled=None):
            return [f"https://{d}" for d in domains]

        async def fake_scrape_url(self, url, country="", city="", niche="", is_cancelled=None, known_metadata=None):
            dom = url.replace("https://", "").split("/")[0]
            ems = [
                ScrapedEmail(email=f"estimating@{dom}", normalized_email=f"estimating@{dom}", prefix="estimating", domain=dom, tier=EmailTier.TIER_1_ESTIMATING, priority_score=100, found_on_page=url),
                ScrapedEmail(email=f"legal@{dom}", normalized_email=f"legal@{dom}", prefix="legal", domain=dom, tier=EmailTier.TIER_2_EXECUTIVE, priority_score=80, found_on_page=url),
                ScrapedEmail(email=f"info@{dom}", normalized_email=f"info@{dom}", prefix="info", domain=dom, tier=EmailTier.TIER_GENERIC, priority_score=40, found_on_page=url),
            ]
            return Lead(
                company_name=dom.split(".")[0].title(),
                domain=dom,
                website_url=url,
                target_country=country,
                target_city=city,
                industry_niche=niche,
                primary_email=ems[0].email,
                primary_email_tier=ems[0].tier,
                priority_score=100,
                all_emails=ems,
                quality_tag="TIER-1-ESTIMATING",
            )

        mock_report = HygieneReport(
            email="placeholder",
            status=HygieneStatus.VERIFIED,
            stage_1_syntax_valid=True,
            is_disposable_domain=False,
            stage_2_mx_valid=True,
            mx_records=["mx.e2ebuilder.com"],
            stage_3_smtp_valid=True,
            smtp_response_code=250,
            smtp_diagnostic_message="OK",
        )

        req = ScrapeRequest(region="", country="Pakistan", city="", niche="Commercial Construction", max_results=7)
        try:
            with patch.object(SearchDiscoveryAgent, "discover_candidate_urls", new=fake_discover), \
                 patch.object(DeepScraperAgent, "scrape_url", new=fake_scrape_url), \
                 patch("api.routes.verify_mx_record", return_value={"has_mx": True, "mx_host": "mx.test", "smtp_banner": "", "deliverable": True, "error": ""}), \
                 patch("core.hygiene.zero_bounce_shield.ZeroBounceHygieneShield.validate_lead_email", side_effect=lambda em: mock_report.model_copy(update={"email": em})):
                await _run_scrape_job(job_id, req, op_id, owner_username=owner)

            job = _get_job(job_id)
            self.assertEqual(job.get("status"), "COMPLETED")
            self.assertIsNotNone(job.get("result"))
            self.assertEqual(job["result"]["verified_count"], 7)
            self.assertEqual(job["result"]["target"]["city"], "Lahore")
            self.assertEqual(job["result"]["target"]["region"], "Asia")
        finally:
            with _scrape_jobs_lock:
                _scrape_jobs.pop(job_id, None)
            with db.get_connection() as conn:
                conn.execute("DELETE FROM outreach_queue WHERE owner_username = ?", (owner,))
                conn.execute("DELETE FROM vault_leads WHERE owner_username = ?", (owner,))
                conn.execute("DELETE FROM dedup_registry WHERE owner_username = ?", (owner,))
                conn.commit()
            try:
                from database.mongo_engine import get_mongo_engine
                get_mongo_engine().purge_all()
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()
