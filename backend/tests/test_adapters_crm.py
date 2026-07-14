"""
T026: Unit tests for CRM adapters (Bitrix24, HubSpot).

Tests adapter behavior with mocked httpx layer:
- createContact, createDeal, createTask methods
- Field mapping and normalization
- Error handling
- Response parsing and ID extraction

All tests use mocked HTTP (no real network calls).
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import httpx

from app.adapters.crm.bitrix24 import Bitrix24Client
from app.adapters.crm.hubspot import HubspotClient
from app.adapters.crm.types import CrmContact, CrmDeal, CrmTask


@pytest.mark.adapter
class TestBitrix24Adapter:
    """Tests for Bitrix24Client implementation."""

    @pytest.mark.asyncio
    async def test_create_contact_dict_input(self, bitrix24_webhook_url):
        """Test createContact with dict input."""
        client = Bitrix24Client(bitrix24_webhook_url)

        with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = 123

            contact = {
                "name": "John Doe",
                "role": "VP Sales",
                "company": "Test Corp",
            }
            result = await client.createContact(contact)

            assert result == {"id": "123"}
            mock_call.assert_called_once()
            call_args = mock_call.call_args
            assert call_args[0][0] == "crm.contact.add"
            fields = call_args[0][1]["fields"]
            assert fields["NAME"] == "John"
            assert fields["LAST_NAME"] == "Doe"
            assert fields["POST"] == "VP Sales"
            assert fields["COMPANY_TITLE"] == "Test Corp"

    @pytest.mark.asyncio
    async def test_create_contact_dataclass_input(self, bitrix24_webhook_url):
        """Test createContact with dataclass input."""
        client = Bitrix24Client(bitrix24_webhook_url)

        with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = 456

            contact = CrmContact(
                name="Jane Smith",
                company="Another Corp",
                role="Head of Ops",
                email="jane@test.com",
            )
            result = await client.createContact(contact)

            assert result == {"id": "456"}
            call_args = mock_call.call_args
            fields = call_args[0][1]["fields"]
            assert fields["NAME"] == "Jane"
            assert fields["LAST_NAME"] == "Smith"

    @pytest.mark.asyncio
    async def test_create_deal(self, bitrix24_webhook_url):
        """Test createDeal with contact linking."""
        client = Bitrix24Client(bitrix24_webhook_url)

        with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = 789

            deal = {
                "title": "Test Deal",
                "contactId": "123",
                "comments": "Test comments",
            }
            result = await client.createDeal(deal)

            assert result == {"id": "789"}
            call_args = mock_call.call_args
            assert call_args[0][0] == "crm.deal.add"
            fields = call_args[0][1]["fields"]
            assert fields["TITLE"] == "Test Deal"
            assert fields["CONTACT_ID"] == 123  # Numeric coercion
            assert fields["COMMENTS"] == "Test comments"

    @pytest.mark.asyncio
    async def test_create_task(self, bitrix24_webhook_url):
        """Test createTask with deal linking and date handling."""
        client = Bitrix24Client(bitrix24_webhook_url)

        with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {"task": {"id": "999"}}

            task = {
                "title": "Follow-up 1",
                "description": "Test task description",
                "dueDate": "2025-07-18",
                "dealId": "456",
            }
            result = await client.createTask(task)

            assert result == {"id": "999"}
            call_args = mock_call.call_args
            assert call_args[0][0] == "tasks.task.add"
            fields = call_args[0][1]["fields"]
            assert fields["TITLE"] == "Follow-up 1"
            assert fields["DEADLINE"] == "2025-07-18T09:00:00+00:00"
            assert fields["UF_CRM_TASK"] == ["D_456"]

    @pytest.mark.asyncio
    async def test_create_task_iso_date(self, bitrix24_webhook_url):
        """Test createTask normalizes ISO dates to YYYY-MM-DD."""
        client = Bitrix24Client(bitrix24_webhook_url)

        with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {"task": {"id": "1000"}}

            task = {
                "title": "Task",
                "description": "Test",
                "dueDate": "2025-07-18T14:30:00Z",
                "dealId": "789",
            }
            result = await client.createTask(task)

            call_args = mock_call.call_args
            fields = call_args[0][1]["fields"]
            # Date normalized, but time always 09:00
            assert fields["DEADLINE"] == "2025-07-18T09:00:00+00:00"

    @pytest.mark.asyncio
    async def test_network_error_handling(self, bitrix24_webhook_url):
        """Test exception handling for network errors."""
        client = Bitrix24Client(bitrix24_webhook_url)

        with patch("httpx.AsyncClient") as mock_ac:
            mock_instance = AsyncMock()
            mock_ac.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.side_effect = Exception("Network timeout")

            with pytest.raises(RuntimeError, match="Network error calling Bitrix24"):
                await client.createContact({"name": "Test", "company": "Test"})

    @pytest.mark.asyncio
    async def test_http_error_handling(self, bitrix24_webhook_url):
        """Test exception handling for HTTP errors."""
        client = Bitrix24Client(bitrix24_webhook_url)

        with patch("httpx.AsyncClient") as mock_ac:
            mock_instance = AsyncMock()
            mock_ac.return_value.__aenter__.return_value = mock_instance

            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_response.reason_phrase = "Forbidden"
            mock_response.json.return_value = {"error": "auth_failed"}
            mock_instance.post.return_value = mock_response

            with pytest.raises(RuntimeError, match="HTTP 403"):
                await client.createContact({"name": "Test", "company": "Test"})

    @pytest.mark.asyncio
    async def test_api_error_handling(self, bitrix24_webhook_url):
        """Test exception handling for API errors in response body."""
        client = Bitrix24Client(bitrix24_webhook_url)

        with patch("httpx.AsyncClient") as mock_ac:
            mock_instance = AsyncMock()
            mock_ac.return_value.__aenter__.return_value = mock_instance

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"error": "invalid_token"}
            mock_instance.post.return_value = mock_response

            with pytest.raises(RuntimeError, match="invalid_token"):
                await client.createContact({"name": "Test", "company": "Test"})

    def test_name_splitting(self, bitrix24_webhook_url):
        """Test name splitting logic."""
        client = Bitrix24Client(bitrix24_webhook_url)

        # Single name
        first, last = client._split_name("John")
        assert first == "John"
        assert last == ""

        # Full name
        first, last = client._split_name("John Doe")
        assert first == "John"
        assert last == "Doe"

        # Multiple parts
        first, last = client._split_name("Jean Paul Martin")
        assert first == "Jean"
        assert last == "Paul Martin"

    def test_date_normalization(self, bitrix24_webhook_url):
        """Test date normalization."""
        client = Bitrix24Client(bitrix24_webhook_url)

        # Already normalized
        assert client._normalize_date("2025-07-18") == "2025-07-18"

        # ISO with time
        assert client._normalize_date("2025-07-18T14:30:00Z") == "2025-07-18"


@pytest.mark.adapter
class TestHubSpotAdapter:
    """Tests for HubspotClient implementation."""

    @pytest.mark.asyncio
    async def test_create_contact_dict_input(self, hubspot_access_token):
        """Test createContact with dict input."""
        client = HubspotClient(hubspot_access_token)

        with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {"id": "contact-abc123"}

            contact = {
                "name": "John Doe",
                "role": "VP Sales",
                "company": "Test Corp",
                "email": "john@test.com",
            }
            result = await client.createContact(contact)

            assert result == {"id": "contact-abc123"}
            mock_call.assert_called_once()
            call_args = mock_call.call_args
            assert call_args[0][0] == "/crm/v3/objects/contacts"
            body = call_args[0][1]
            props = body["properties"]
            assert props["firstname"] == "John"
            assert props["lastname"] == "Doe"
            assert props["jobtitle"] == "VP Sales"
            assert props["company"] == "Test Corp"
            assert props["email"] == "john@test.com"

    @pytest.mark.asyncio
    async def test_create_contact_dataclass_input(self, hubspot_access_token):
        """Test createContact with dataclass input."""
        client = HubspotClient(hubspot_access_token)

        with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {"id": "contact-def456"}

            contact = CrmContact(
                name="Jane Smith",
                company="Another Corp",
                role="Head of Ops",
            )
            result = await client.createContact(contact)

            assert result == {"id": "contact-def456"}
            call_args = mock_call.call_args
            props = call_args[0][1]["properties"]
            assert props["firstname"] == "Jane"
            assert props["lastname"] == "Smith"

    @pytest.mark.asyncio
    async def test_create_deal(self, hubspot_access_token):
        """Test createDeal with contact association."""
        client = HubspotClient(hubspot_access_token)

        with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {"id": "deal-xyz789"}

            deal = {
                "title": "Test Deal",
                "contactId": "contact-abc123",
                "comments": "Test comments",
            }
            result = await client.createDeal(deal)

            assert result == {"id": "deal-xyz789"}
            call_args = mock_call.call_args
            assert call_args[0][0] == "/crm/v3/objects/deals"
            body = call_args[0][1]

            # Verify properties
            assert body["properties"]["dealname"] == "Test Deal"
            assert body["properties"]["description"] == "Test comments"
            assert body["properties"]["pipeline"] == "default"

            # Verify association to contact
            assoc = body["associations"][0]
            assert assoc["to"]["id"] == "contact-abc123"
            assert assoc["types"][0]["associationTypeId"] == 3

    @pytest.mark.asyncio
    async def test_create_task(self, hubspot_access_token):
        """Test createTask with deal association."""
        client = HubspotClient(hubspot_access_token)

        with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {"id": "task-task123"}

            task = {
                "title": "Follow-up 1",
                "description": "Check email open",
                "dueDate": "2025-07-18",
                "dealId": "deal-xyz789",
            }
            result = await client.createTask(task)

            assert result == {"id": "task-task123"}
            call_args = mock_call.call_args
            assert call_args[0][0] == "/crm/v3/objects/tasks"
            body = call_args[0][1]

            # Verify properties
            props = body["properties"]
            assert props["hs_task_subject"] == "Follow-up 1"
            assert props["hs_task_body"] == "Check email open"
            assert props["hs_task_status"] == "NOT_STARTED"
            assert isinstance(props["hs_timestamp"], int)

            # Verify association to deal
            assoc = body["associations"][0]
            assert assoc["to"]["id"] == "deal-xyz789"
            assert assoc["types"][0]["associationTypeId"] == 216

    def test_timestamp_conversion(self, hubspot_access_token):
        """Test timestamp conversion to milliseconds since epoch."""
        client = HubspotClient(hubspot_access_token)

        # YYYY-MM-DD format
        ts = client._to_hubspot_timestamp("2025-07-18")
        assert isinstance(ts, int)
        assert ts > 0

        # ISO format
        ts_iso = client._to_hubspot_timestamp("2025-07-18T14:30:00Z")
        assert isinstance(ts_iso, int)

    def test_name_splitting(self, hubspot_access_token):
        """Test name splitting logic matches Bitrix24."""
        client = HubspotClient(hubspot_access_token)

        # Single name
        first, last = client._split_name("John")
        assert first == "John"
        assert last == ""

        # Full name
        first, last = client._split_name("John Doe")
        assert first == "John"
        assert last == "Doe"

    @pytest.mark.asyncio
    async def test_network_error_handling(self, hubspot_access_token):
        """Test exception handling for network errors."""
        client = HubspotClient(hubspot_access_token)

        with patch("httpx.AsyncClient") as mock_ac:
            mock_instance = AsyncMock()
            mock_ac.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.side_effect = Exception("Connection refused")

            with pytest.raises(RuntimeError, match="Network error calling HubSpot"):
                await client.createContact({"name": "Test", "company": "Test"})

    @pytest.mark.asyncio
    async def test_http_error_handling(self, hubspot_access_token):
        """Test exception handling for HTTP errors."""
        client = HubspotClient(hubspot_access_token)

        with patch("httpx.AsyncClient") as mock_ac:
            mock_instance = AsyncMock()
            mock_ac.return_value.__aenter__.return_value = mock_instance

            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.reason_phrase = "Unauthorized"
            mock_response.json.return_value = {"message": "Invalid API key"}
            mock_instance.post.return_value = mock_response

            with pytest.raises(RuntimeError, match="HTTP 401"):
                await client.createContact({"name": "Test", "company": "Test"})

    @pytest.mark.asyncio
    async def test_missing_id_error(self, hubspot_access_token):
        """Test exception when response lacks 'id' field."""
        client = HubspotClient(hubspot_access_token)

        with patch("httpx.AsyncClient") as mock_ac:
            mock_instance = AsyncMock()
            mock_ac.return_value.__aenter__.return_value = mock_instance

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"properties": {}}  # No id
            mock_instance.post.return_value = mock_response

            with pytest.raises(RuntimeError, match="returned no id"):
                await client.createContact({"name": "Test", "company": "Test"})

    def test_invalid_token_init(self):
        """Test that invalid token raises on init."""
        with pytest.raises(ValueError):
            HubspotClient(None)

        with pytest.raises(ValueError):
            HubspotClient("")


@pytest.mark.adapter
class TestAdapterFieldMapping:
    """Test that field mappings match contract (CrmContactDict, etc.)."""

    @pytest.mark.asyncio
    async def test_bitrix24_optional_fields(self, bitrix24_webhook_url):
        """Test Bitrix24 handles optional fields gracefully."""
        client = Bitrix24Client(bitrix24_webhook_url)

        with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = 100

            # Minimal contact
            contact = {"name": "John", "company": "Test"}
            result = await client.createContact(contact)

            call_args = mock_call.call_args
            fields = call_args[0][1]["fields"]
            assert "NAME" in fields
            assert "COMPANY_TITLE" in fields
            # role is optional, should be None if missing
            assert fields.get("POST") is None

    @pytest.mark.asyncio
    async def test_hubspot_optional_fields(self, hubspot_access_token):
        """Test HubSpot handles optional fields gracefully."""
        client = HubspotClient(hubspot_access_token)

        with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {"id": "contact-test"}

            # Minimal contact
            contact = {"name": "Jane", "company": "Corp"}
            result = await client.createContact(contact)

            call_args = mock_call.call_args
            props = call_args[0][1]["properties"]
            assert "firstname" in props
            assert "company" in props
            # Optional fields should not be included if empty
            assert "jobtitle" not in props or props.get("jobtitle") == ""
