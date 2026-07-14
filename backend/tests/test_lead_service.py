"""
T026: Unit tests for lead_service orchestration (T008 + T007 integration).

Tests create_lead_with_followups function:
- 1 contact created
- 1 deal linked to contact
- 3 tasks with correct due dates (+4/+9/+14 days)
- LLM enrichment called and integrated
- Mock CrmClient and LLM (no real network/DB)
- All adapters (Bitrix24, HubSpot) via factory

Mirrors assertions from scripts/e2e_smoke_t020.py but as isolated pytest units.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from app.services.lead_service import create_lead_with_followups, _add_days


@pytest.mark.service
class TestLeadServiceDateHelpers:
    """Test date helper functions."""

    def test_add_days_returns_correct_format(self):
        """Test _add_days returns YYYY-MM-DD format."""
        result = _add_days(0)
        # Should be today
        today = datetime.utcnow().strftime("%Y-%m-%d")
        # Allow 1 day tolerance for clock skew
        result_date = datetime.strptime(result, "%Y-%m-%d")
        today_date = datetime.strptime(today, "%Y-%m-%d")
        delta = abs((result_date - today_date).days)
        assert delta <= 1

    def test_add_days_positive_offset(self):
        """Test _add_days with positive offset."""
        result = _add_days(4)
        expected = (datetime.utcnow() + timedelta(days=4)).strftime("%Y-%m-%d")
        # Allow 1 day tolerance
        result_date = datetime.strptime(result, "%Y-%m-%d")
        expected_date = datetime.strptime(expected, "%Y-%m-%d")
        delta = abs((result_date - expected_date).days)
        assert delta <= 1


@pytest.mark.service
class TestLeadServiceOrchestration:
    """Tests for lead orchestration (1c+1d+3t flow)."""

    @pytest.mark.asyncio
    async def test_create_lead_basic_flow(
        self,
        mock_lead_input,
        mock_current_user,
        mock_enrichment_result,
        mock_crm_client,
    ):
        """Test basic lead creation flow: contact → deal → 3 tasks."""
        with patch("app.services.lead_service.create_crm_client") as mock_factory, \
             patch("app.services.lead_service.generate_enrichment") as mock_enrich:
            mock_factory.return_value = mock_crm_client
            mock_enrich.return_value = mock_enrichment_result

            result = await create_lead_with_followups(
                mock_lead_input,
                provider="bitrix24",
                token="test-token",
                current_user=mock_current_user,
            )

            # Verify factory was called correctly
            mock_factory.assert_called_once_with("bitrix24", "test-token", current_user=mock_current_user)

            # Verify enrichment was called
            mock_enrich.assert_called_once()

            # Verify result shape
            assert "contact_id" in result
            assert "deal_id" in result
            assert "task1" in result
            assert "task2" in result
            assert "task3" in result
            assert "enriched_preview" in result

    @pytest.mark.asyncio
    async def test_create_lead_returns_correct_ids(
        self,
        mock_lead_input,
        mock_current_user,
        mock_enrichment_result,
        mock_crm_client,
    ):
        """Test that correct IDs are returned from CrmClient calls."""
        mock_crm_client.createContact = AsyncMock(return_value={"id": "contact-abc"})
        mock_crm_client.createDeal = AsyncMock(return_value={"id": "deal-xyz"})
        mock_crm_client.createTask = AsyncMock(side_effect=[
            {"id": "task-1"},
            {"id": "task-2"},
            {"id": "task-3"},
        ])

        with patch("app.services.lead_service.create_crm_client") as mock_factory, \
             patch("app.services.lead_service.generate_enrichment") as mock_enrich:
            mock_factory.return_value = mock_crm_client
            mock_enrich.return_value = mock_enrichment_result

            result = await create_lead_with_followups(
                mock_lead_input,
                provider="bitrix24",
                token="test-token",
                current_user=mock_current_user,
            )

            assert result["contact_id"] == "contact-abc"
            assert result["deal_id"] == "deal-xyz"
            assert result["task1"]["id"] == "task-1"
            assert result["task2"]["id"] == "task-2"
            assert result["task3"]["id"] == "task-3"

    @pytest.mark.asyncio
    async def test_create_lead_task_dates_correct_deltas(
        self,
        mock_lead_input,
        mock_current_user,
        mock_enrichment_result,
        mock_crm_client,
        today,
    ):
        """Test task due dates have correct deltas (+4/+9/+14 days)."""
        with patch("app.services.lead_service.create_crm_client") as mock_factory, \
             patch("app.services.lead_service.generate_enrichment") as mock_enrich:
            mock_factory.return_value = mock_crm_client
            mock_enrich.return_value = mock_enrichment_result

            result = await create_lead_with_followups(
                mock_lead_input,
                provider="bitrix24",
                token="test-token",
                current_user=mock_current_user,
            )

            # Parse dates
            d1 = datetime.strptime(result["task1"]["date"], "%Y-%m-%d").date()
            d2 = datetime.strptime(result["task2"]["date"], "%Y-%m-%d").date()
            d3 = datetime.strptime(result["task3"]["date"], "%Y-%m-%d").date()

            today_date = today.date()

            # Check deltas (allow ±1 day tolerance for clock skew)
            delta1 = (d1 - today_date).days
            delta2 = (d2 - today_date).days
            delta3 = (d3 - today_date).days

            assert 3 <= delta1 <= 5, f"task1 delta {delta1} not ~4"
            assert 8 <= delta2 <= 10, f"task2 delta {delta2} not ~9"
            assert 13 <= delta3 <= 15, f"task3 delta {delta3} not ~14"

    @pytest.mark.asyncio
    async def test_create_lead_deal_linked_to_contact(
        self,
        mock_lead_input,
        mock_current_user,
        mock_enrichment_result,
        mock_crm_client,
    ):
        """Test that deal is correctly linked to contact."""
        call_history = []

        async def track_createDeal(deal):
            call_history.append(("deal", deal))
            return {"id": "deal-456"}

        mock_crm_client.createContact = AsyncMock(return_value={"id": "contact-123"})
        mock_crm_client.createDeal = AsyncMock(side_effect=track_createDeal)
        mock_crm_client.createTask = AsyncMock(return_value={"id": "task-x"})

        with patch("app.services.lead_service.create_crm_client") as mock_factory, \
             patch("app.services.lead_service.generate_enrichment") as mock_enrich:
            mock_factory.return_value = mock_crm_client
            mock_enrich.return_value = mock_enrichment_result

            result = await create_lead_with_followups(
                mock_lead_input,
                provider="bitrix24",
                token="test-token",
                current_user=mock_current_user,
            )

            # Verify deal call included correct contactId
            assert len(call_history) == 1
            _, deal_input = call_history[0]
            assert deal_input["contactId"] == "contact-123"
            assert result["deal_id"] == "deal-456"

    @pytest.mark.asyncio
    async def test_create_lead_tasks_linked_to_deal(
        self,
        mock_lead_input,
        mock_current_user,
        mock_enrichment_result,
        mock_crm_client,
    ):
        """Test that tasks are correctly linked to deal."""
        task_calls = []

        async def track_createTask(task):
            task_calls.append(task)
            idx = len(task_calls)
            return {"id": f"task-{idx}"}

        mock_crm_client.createContact = AsyncMock(return_value={"id": "contact-123"})
        mock_crm_client.createDeal = AsyncMock(return_value={"id": "deal-789"})
        mock_crm_client.createTask = AsyncMock(side_effect=track_createTask)

        with patch("app.services.lead_service.create_crm_client") as mock_factory, \
             patch("app.services.lead_service.generate_enrichment") as mock_enrich:
            mock_factory.return_value = mock_crm_client
            mock_enrich.return_value = mock_enrichment_result

            result = await create_lead_with_followups(
                mock_lead_input,
                provider="bitrix24",
                token="test-token",
                current_user=mock_current_user,
            )

            # Verify all tasks have correct dealId
            assert len(task_calls) == 3
            for task in task_calls:
                assert task["dealId"] == "deal-789"

            assert result["task1"]["id"] == "task-1"
            assert result["task2"]["id"] == "task-2"
            assert result["task3"]["id"] == "task-3"

    @pytest.mark.asyncio
    async def test_create_lead_enriched_preview_included(
        self,
        mock_lead_input,
        mock_current_user,
        mock_enrichment_result,
        mock_crm_client,
    ):
        """Test that enriched preview is included in result."""
        with patch("app.services.lead_service.create_crm_client") as mock_factory, \
             patch("app.services.lead_service.generate_enrichment") as mock_enrich:
            mock_factory.return_value = mock_crm_client
            mock_enrich.return_value = mock_enrichment_result

            result = await create_lead_with_followups(
                mock_lead_input,
                provider="bitrix24",
                token="test-token",
                current_user=mock_current_user,
            )

            assert "enriched_preview" in result
            ep = result["enriched_preview"]

            # Verify enriched shape (from T007)
            assert ep["company_snapshot"] is not None
            assert ep["personalized_opener"] is not None
            assert "follow_ups" in ep
            assert len(ep["follow_ups"]) == 3
            assert ep["model_used"] == "test-mock-model"

    @pytest.mark.asyncio
    async def test_create_lead_enriched_follow_ups_structure(
        self,
        mock_lead_input,
        mock_current_user,
        mock_enrichment_result,
        mock_crm_client,
    ):
        """Test that follow_ups have correct structure from LLM."""
        with patch("app.services.lead_service.create_crm_client") as mock_factory, \
             patch("app.services.lead_service.generate_enrichment") as mock_enrich:
            mock_factory.return_value = mock_crm_client
            mock_enrich.return_value = mock_enrichment_result

            result = await create_lead_with_followups(
                mock_lead_input,
                provider="bitrix24",
                token="test-token",
                current_user=mock_current_user,
            )

            fus = result["enriched_preview"]["follow_ups"]
            assert len(fus) == 3

            for i, fu in enumerate(fus):
                assert "title" in fu
                assert "description" in fu
                assert "due_in_days" in fu
                assert "rationale" in fu
                assert fu["due_in_days"] in (4, 9, 14)

    @pytest.mark.asyncio
    async def test_create_lead_dict_input(
        self,
        mock_current_user,
        mock_enrichment_result,
        mock_crm_client,
    ):
        """Test that dict input (not Pydantic model) works."""
        lead_dict = {
            "company_name": "Dict Corp",
            "deal_name": "Dict Deal",
            "contact_name": "Dict User",
            "contact_role": "CTO",
            "signal": "test",
            "signal_type": "test_type",
            "pain_point": "test",
            "email_subject": "test",
            "notes": "test",
        }

        with patch("app.services.lead_service.create_crm_client") as mock_factory, \
             patch("app.services.lead_service.generate_enrichment") as mock_enrich:
            mock_factory.return_value = mock_crm_client
            mock_enrich.return_value = mock_enrichment_result

            result = await create_lead_with_followups(
                lead_dict,
                provider="bitrix24",
                token="test-token",
                current_user=mock_current_user,
            )

            assert "contact_id" in result
            assert result["contact_id"] == "contact-123"

    @pytest.mark.asyncio
    async def test_create_lead_enrichment_called_with_correct_params(
        self,
        mock_lead_input,
        mock_current_user,
        mock_enrichment_result,
        mock_crm_client,
    ):
        """Test that LLM enrichment is called with correct parameters."""
        with patch("app.services.lead_service.create_crm_client") as mock_factory, \
             patch("app.services.lead_service.generate_enrichment") as mock_enrich:
            mock_factory.return_value = mock_crm_client
            mock_enrich.return_value = mock_enrichment_result

            result = await create_lead_with_followups(
                mock_lead_input,
                provider="bitrix24",
                token="test-token",
                current_user=mock_current_user,
            )

            # Verify enrichment was called with lead input and user
            mock_enrich.assert_called_once()
            call_args = mock_enrich.call_args
            assert call_args[0][0] == mock_lead_input
            assert call_args[1]["current_user"] == mock_current_user

    @pytest.mark.asyncio
    async def test_create_lead_empty_enrichment_fallback(
        self,
        mock_lead_input,
        mock_current_user,
        mock_crm_client,
    ):
        """Test fallback when enrichment returns minimal data."""
        minimal_enrichment = {
            "company_snapshot": None,
            "personalized_opener": None,
            "follow_ups": [],
        }

        with patch("app.services.lead_service.create_crm_client") as mock_factory, \
             patch("app.services.lead_service.generate_enrichment") as mock_enrich:
            mock_factory.return_value = mock_crm_client
            mock_enrich.return_value = minimal_enrichment

            result = await create_lead_with_followups(
                mock_lead_input,
                provider="bitrix24",
                token="test-token",
                current_user=mock_current_user,
            )

            # Should still create all 3 tasks even with minimal enrichment
            assert "task1" in result
            assert "task1" in result and "id" in result["task1"]
            assert "task2" in result
            assert "task3" in result

    @pytest.mark.asyncio
    async def test_create_lead_multiple_providers(
        self,
        mock_lead_input,
        mock_current_user,
        mock_enrichment_result,
    ):
        """Test that function works with different providers."""
        with patch("app.services.lead_service.create_crm_client") as mock_factory, \
             patch("app.services.lead_service.generate_enrichment") as mock_enrich:
            mock_enrich.return_value = mock_enrichment_result

            # Create fresh mocks for each provider
            crm_mock_1 = MagicMock()
            crm_mock_1.createContact = AsyncMock(return_value={"id": "contact-123"})
            crm_mock_1.createDeal = AsyncMock(return_value={"id": "deal-456"})
            crm_mock_1.createTask = AsyncMock(side_effect=[
                {"id": "task-1"},
                {"id": "task-2"},
                {"id": "task-3"},
            ])

            crm_mock_2 = MagicMock()
            crm_mock_2.createContact = AsyncMock(return_value={"id": "contact-789"})
            crm_mock_2.createDeal = AsyncMock(return_value={"id": "deal-999"})
            crm_mock_2.createTask = AsyncMock(side_effect=[
                {"id": "task-4"},
                {"id": "task-5"},
                {"id": "task-6"},
            ])

            # Configure factory to return different mocks for different calls
            mock_factory.side_effect = [crm_mock_1, crm_mock_2]

            # Test with Bitrix24
            result_b24 = await create_lead_with_followups(
                mock_lead_input,
                provider="bitrix24",
                token="bitrix-token",
                current_user=mock_current_user,
            )
            assert "contact_id" in result_b24
            assert result_b24["contact_id"] == "contact-123"

            # Test with HubSpot
            result_hs = await create_lead_with_followups(
                mock_lead_input,
                provider="hubspot",
                token="hubspot-token",
                current_user=mock_current_user,
            )
            assert "contact_id" in result_hs
            assert result_hs["contact_id"] == "contact-789"

            # Verify both provider calls happened
            assert mock_factory.call_count == 2


@pytest.mark.service
class TestLeadServiceEdgeCases:
    """Edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_create_lead_missing_optional_fields(
        self,
        mock_current_user,
        mock_enrichment_result,
        mock_crm_client,
    ):
        """Test handling of lead input with missing optional fields."""
        minimal_lead = {
            "company_name": "Minimal Co",
            "deal_name": "Minimal Deal",
            "contact_name": "John",
        }

        with patch("app.services.lead_service.create_crm_client") as mock_factory, \
             patch("app.services.lead_service.generate_enrichment") as mock_enrich:
            mock_factory.return_value = mock_crm_client
            mock_enrich.return_value = mock_enrichment_result

            result = await create_lead_with_followups(
                minimal_lead,
                provider="bitrix24",
                token="test-token",
                current_user=mock_current_user,
            )

            # Should complete successfully with fallback defaults
            assert "contact_id" in result
            assert "deal_id" in result
            for i in range(1, 4):
                assert f"task{i}" in result

    @pytest.mark.asyncio
    async def test_create_lead_exact_call_sequence(
        self,
        mock_lead_input,
        mock_current_user,
        mock_enrichment_result,
        mock_crm_client,
    ):
        """Test exact sequence of CrmClient calls (contact → deal → 3 tasks)."""
        call_sequence = []

        async def track_contact(c):
            call_sequence.append("createContact")
            return {"id": "contact-1"}

        async def track_deal(d):
            call_sequence.append("createDeal")
            return {"id": "deal-1"}

        async def track_task(t):
            call_sequence.append("createTask")
            return {"id": f"task-{len([x for x in call_sequence if x == 'createTask']) + 1}"}

        mock_crm_client.createContact = AsyncMock(side_effect=track_contact)
        mock_crm_client.createDeal = AsyncMock(side_effect=track_deal)
        mock_crm_client.createTask = AsyncMock(side_effect=track_task)

        with patch("app.services.lead_service.create_crm_client") as mock_factory, \
             patch("app.services.lead_service.generate_enrichment") as mock_enrich:
            mock_factory.return_value = mock_crm_client
            mock_enrich.return_value = mock_enrichment_result

            result = await create_lead_with_followups(
                mock_lead_input,
                provider="bitrix24",
                token="test-token",
                current_user=mock_current_user,
            )

            # Verify exact sequence
            assert call_sequence == [
                "createContact",
                "createDeal",
                "createTask",
                "createTask",
                "createTask",
            ]
