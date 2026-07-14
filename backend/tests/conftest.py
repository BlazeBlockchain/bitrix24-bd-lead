"""
T026: Pytest configuration and shared fixtures.

Provides mocked httpx client, test data, and setup/teardown.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta


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
