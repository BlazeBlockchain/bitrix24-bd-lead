"""
T026: Pytest configuration and shared fixtures.

Provides mocked httpx client, test data, and setup/teardown.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from app.config import settings


@pytest.fixture(autouse=True)
def no_live_retrieval(monkeypatch):
    """010: keep the suite offline by construction rather than by luck.

    generate_enrichment now runs a grounded web search before calling the model.
    Retrieval short-circuits when GEMINI_API_KEY is unset, which is the normal state of
    a dev checkout — but that is a coincidence of configuration, not a guarantee. Run
    the suite in a shell that exports a real key, or inside the backend image which has
    one, and every enrichment test would quietly start hitting the network.

    Disabled for every test. The retrieval tests opt back in explicitly and install a
    mock transport, so they exercise the real parser without opening a socket.
    """
    monkeypatch.setattr(settings, "RETRIEVAL_ENABLED", False)


@pytest.fixture
def mock_current_user():
    """Mock current_user dict (from get_current_user)."""
    return {
        "id": "test-user-123",
        "email": "test@example.com",
        "display_name": "Test User",
    }


@pytest.fixture
def mock_lead_input():
    """Minimal lead input for testing."""
    return {
        "company_name": "Test Corp",
        "deal_name": "Test Deal",
        "contact_name": "John Doe",
        "contact_role": "VP Sales",
        "signal": "Recent funding",
        "signal_type": "new_funding",
        "pain_point": "Manual lead tracking",
        "email_subject": "Intro",
        "notes": "Test notes",
    }


@pytest.fixture
def mock_enrichment_result():
    """Mock LLM enrichment output (T007)."""
    return {
        "company_snapshot": "Test Corp is a scaling SaaS company focused on automation.",
        "personalized_opener": "Hi John, saw your recent funding round — this is a good moment to discuss how we help with lead tracking.",
        "follow_ups": [
            {
                "title": "Follow-up 1 — Check + Connect",
                "description": "Check email open and connect on LinkedIn.",
                "due_in_days": 4,
                "rationale": "Prompt timing after initial signal.",
            },
            {
                "title": "Follow-up 2 — Short Bump",
                "description": "Brief follow-up referencing the funding.",
                "due_in_days": 9,
                "rationale": "Keep momentum without pressure.",
            },
            {
                "title": "Follow-up 3 — Close the Loop",
                "description": "Final touch on pain point.",
                "due_in_days": 14,
                "rationale": "Address core need directly.",
            },
        ],
        # 009: the four sections 008 shipped inert. Additive and optional — consumers
        # that predate this feature ignore them, and a stored enrichment without them
        # still renders, just inert.
        # 010: source_url + finding are the retrieval-sourced citation. Only the server
        # may set them, never the model — see _validate_citation.
        "buying_signal": {
            "summary": "Test Corp closed a funding round, which usually front-loads tooling decisions.",
            "source": "Example Newsroom",
            "date": "2026-08-01",
            "source_url": "https://example.com/newsroom/test-corp-series-b",
            "finding": "Test Corp has closed a $40M Series B led by Example Ventures.",
        },
        "contact_confidence": {
            "level": "medium",
            "reason": "VP Sales plausibly owns lead tracking, but the fit is unconfirmed.",
        },
        "outreach_email": {
            "subject": "Test Corp — recent funding",
            "body": "Hi John,\n\nSaw the funding round.\n\nWorth a short call?\n\nBest,\nThe team",
        },
        "crm_entry": {
            "deal_name": "Test Deal",
            "contact_role": "VP Sales",
            "signal": "Recent funding",
            "pain_point": "Manual lead tracking",
            "pipeline": "New leads",
        },
        "model_used": "test-mock-model",
        "memory_note": "Using test memory context",
    }


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient for testing without real HTTP."""
    mock = AsyncMock()
    return mock


@pytest.fixture
def mock_crm_client():
    """Mock CrmClient (Protocol) with all required methods."""
    mock = MagicMock()
    mock.createContact = AsyncMock(return_value={"id": "contact-123"})
    mock.createDeal = AsyncMock(return_value={"id": "deal-456"})
    mock.createTask = AsyncMock(side_effect=[
        {"id": "task-1"},
        {"id": "task-2"},
        {"id": "task-3"},
    ])
    return mock


@pytest.fixture
def bitrix24_webhook_url():
    """Test Bitrix24 webhook URL."""
    return "https://test.bitrix24.com/rest/1/test-user-123/test-token-abc123/"


@pytest.fixture
def hubspot_access_token():
    """Test HubSpot access token."""
    return "pat-na1-test-token-hubspot-123456789"


# Utility fixtures for date testing
@pytest.fixture
def today():
    """Today's date as datetime."""
    return datetime.utcnow()


@pytest.fixture
def expected_task_dates(today):
    """Expected task due dates (+4/+9/+14 days from now)."""
    return {
        "task1": (today + timedelta(days=4)).strftime("%Y-%m-%d"),
        "task2": (today + timedelta(days=9)).strftime("%Y-%m-%d"),
        "task3": (today + timedelta(days=14)).strftime("%Y-%m-%d"),
    }
