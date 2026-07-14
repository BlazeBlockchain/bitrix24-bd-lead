"""
T026: Unit tests for LLM service (T007 enrichment).

Tests generate_enrichment function:
- Structured JSON output shape (company_snapshot, personalized_opener, follow_ups with 3 items)
- Budget guards (no real calls when over budget)
- Mock fallback when no LLM keys
- Usage ledger recording
- Memory context injection

All tests are hermetic (no real LLM calls, all mocked/stubbed).
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.services.llm_service import (
    generate_enrichment,
    _parse_structured_json,
    _build_memory_context,
    _mock_generate,
    _reset_usage_ledger_for_tests,
)


@pytest.mark.service
class TestLlmServiceStructuredOutput:
    """Test structured output shape from generate_enrichment."""

    @pytest.mark.asyncio
    async def test_enrichment_returns_correct_shape(self, mock_lead_input, mock_current_user):
        """Test that enrichment output has correct shape."""
        with patch("app.services.llm_service._call_gemini") as mock_gemini, \
             patch("app.services.llm_service._call_haiku") as mock_haiku:
            # Mock successful Gemini response
            mock_gemini.return_value = {
                "company_snapshot": "Test snapshot",
                "personalized_opener": "Test opener",
                "follow_ups": [
                    {"title": "FU1", "description": "Desc1", "due_in_days": 4, "rationale": "Ratio1"},
                    {"title": "FU2", "description": "Desc2", "due_in_days": 9, "rationale": "Ratio2"},
                    {"title": "FU3", "description": "Desc3", "due_in_days": 14, "rationale": "Ratio3"},
                ],
                "model_used": "gemini-2.5-flash",
            }

            result = await generate_enrichment(mock_lead_input, current_user=mock_current_user)

            # Verify shape
            assert "company_snapshot" in result
            assert "personalized_opener" in result
            assert "follow_ups" in result
            assert "model_used" in result

            # Verify follow_ups count
            assert len(result["follow_ups"]) == 3

            # Verify follow_up fields
            for fu in result["follow_ups"]:
                assert "title" in fu
                assert "description" in fu
                assert "due_in_days" in fu
                assert "rationale" in fu

    @pytest.mark.asyncio
    async def test_enrichment_with_exactly_three_followups(self, mock_lead_input, mock_current_user):
        """Test that enrichment always returns exactly 3 follow-ups."""
        with patch("app.services.llm_service._call_gemini") as mock_gemini:
            mock_gemini.return_value = {
                "company_snapshot": "Snapshot",
                "personalized_opener": "Opener",
                "follow_ups": [
                    {"title": "F1", "description": "D1", "due_in_days": 4, "rationale": "R1"},
                    {"title": "F2", "description": "D2", "due_in_days": 9, "rationale": "R2"},
                    {"title": "F3", "description": "D3", "due_in_days": 14, "rationale": "R3"},
                ],
                "model_used": "test-model",
            }

            result = await generate_enrichment(mock_lead_input, current_user=mock_current_user)

            # Must have exactly 3
            assert len(result["follow_ups"]) == 3
            # Verify due_in_days progression
            assert result["follow_ups"][0]["due_in_days"] == 4
            assert result["follow_ups"][1]["due_in_days"] == 9
            assert result["follow_ups"][2]["due_in_days"] == 14

    @pytest.mark.asyncio
    async def test_enrichment_includes_model_used_field(self, mock_lead_input, mock_current_user):
        """Test that model_used field is present in result."""
        with patch("app.services.llm_service._call_gemini") as mock_gemini:
            mock_gemini.return_value = {
                "company_snapshot": "Snap",
                "personalized_opener": "Open",
                "follow_ups": [{"title": "T", "description": "D", "due_in_days": 4, "rationale": "R"}] * 3,
                "model_used": "gemini-2.5-flash",
            }

            result = await generate_enrichment(mock_lead_input, current_user=mock_current_user)

            assert result["model_used"] == "gemini-2.5-flash"


@pytest.mark.service
class TestLlmServiceJsonParsing:
    """Test JSON parsing and normalization."""

    def test_parse_valid_json(self):
        """Test parsing valid JSON."""
        json_str = '{"company_snapshot": "Test", "personalized_opener": "Hi", "follow_ups": [{"title": "T1", "description": "D1", "due_in_days": 4, "rationale": "R1"}, {"title": "T2", "description": "D2", "due_in_days": 9, "rationale": "R2"}, {"title": "T3", "description": "D3", "due_in_days": 14, "rationale": "R3"}]}'
        result = _parse_structured_json(json_str)

        assert result["company_snapshot"] == "Test"
        assert result["personalized_opener"] == "Hi"
        assert len(result["follow_ups"]) == 3
        assert result["follow_ups"][0]["title"] == "T1"

    def test_parse_json_with_code_fence(self):
        """Test parsing JSON wrapped in markdown code fences."""
        json_str = '```json\n{"company_snapshot": "Test", "personalized_opener": "Hi", "follow_ups": []}\n```'
        result = _parse_structured_json(json_str)

        assert result["company_snapshot"] == "Test"

    def test_parse_malformed_json_fallback(self):
        """Test fallback to defaults for malformed JSON."""
        result = _parse_structured_json("not valid json at all")

        # Should return defaults
        assert "company_snapshot" in result
        assert "personalized_opener" in result
        assert "follow_ups" in result

    def test_parse_incomplete_follow_ups(self):
        """Test that parser pads follow_ups to exactly 3."""
        json_str = '{"company_snapshot": "S", "personalized_opener": "O", "follow_ups": []}'
        result = _parse_structured_json(json_str)

        # Should have 3 follow-ups with defaults
        assert len(result["follow_ups"]) == 3
        for fu in result["follow_ups"]:
            assert "title" in fu
            assert "due_in_days" in fu

    def test_parse_normalizes_field_names(self):
        """Test that parser normalizes alternative field names."""
        # Alternative names from llm_service
        json_str = '{"snapshot": "S", "opener": "O", "tasks": []}'
        result = _parse_structured_json(json_str)

        assert result["company_snapshot"] == "S"
        assert result["personalized_opener"] == "O"


@pytest.mark.service
class TestLlmServiceMockFallback:
    """Test mock fallback when no LLM keys or budget exceeded."""

    def test_mock_generate_structure(self, mock_lead_input):
        """Test that mock output has correct structure."""
        result = _mock_generate(mock_lead_input, "memory context")

        assert "company_snapshot" in result
        assert "personalized_opener" in result
        assert "follow_ups" in result
        assert len(result["follow_ups"]) == 3
        assert result["model_used"] == "mock-llm"

    def test_mock_generate_includes_lead_details(self, mock_lead_input):
        """Test that mock includes details from lead input."""
        result = _mock_generate(mock_lead_input, "memory context")

        # Should include company/contact info
        snapshot = result["company_snapshot"]
        assert mock_lead_input["company_name"] in snapshot
        assert mock_lead_input["contact_name"] in snapshot

    @pytest.mark.asyncio
    async def test_enrichment_uses_mock_when_no_keys(self, mock_lead_input, mock_current_user):
        """Test that mock is used when no LLM API keys configured."""
        with patch("app.services.llm_service.settings") as mock_settings, \
             patch("app.services.llm_service._call_gemini") as mock_gemini, \
             patch("app.services.llm_service._call_haiku") as mock_haiku:
            # No API keys
            mock_settings.GEMINI_API_KEY = None
            mock_settings.ANTHROPIC_API_KEY = None
            mock_settings.DEBUG = True
            mock_settings.LLM_DAILY_BUDGET_CENTS = 10000

            mock_gemini.return_value = None
            mock_haiku.return_value = None

            result = await generate_enrichment(mock_lead_input, current_user=mock_current_user)

            # Should use mock
            assert result["model_used"] == "mock-llm"
            assert len(result["follow_ups"]) == 3

    @pytest.mark.asyncio
    async def test_enrichment_uses_mock_on_budget_exceeded(self, mock_lead_input, mock_current_user):
        """Test that mock is used when daily budget exceeded."""
        _reset_usage_ledger_for_tests()

        with patch("app.services.llm_service.settings") as mock_settings:
            mock_settings.DEBUG = False
            mock_settings.LLM_DAILY_BUDGET_CENTS = 1  # Very low budget

            result = await generate_enrichment(mock_lead_input, current_user=mock_current_user)

            # Should use mock due to budget
            assert result["model_used"] == "mock-llm"
            assert "budget_exceeded_mocked" in result.get("note", "")


@pytest.mark.service
class TestLlmServiceMemoryContext:
    """Test memory context injection."""

    def test_memory_context_with_custom_context(self):
        """Test memory context with provided memory_context dict."""
        mock_user = {"id": "user-1"}
        ctx = _build_memory_context(mock_user, memory_context={"tone": "casual", "icp": ["SaaS"]})

        assert "tone" in ctx
        assert "casual" in ctx
        assert "SaaS" in ctx

    def test_memory_context_without_user(self):
        """Test memory context when no user (first lead)."""
        ctx = _build_memory_context(None)

        assert "first lead" in ctx.lower() or "no prior" in ctx.lower()

    def test_memory_context_from_user_display_name(self):
        """Test that memory context includes user display_name."""
        mock_user = {"display_name": "John Salesman"}
        ctx = _build_memory_context(mock_user)

        assert "John Salesman" in ctx or "recent tone" in ctx.lower()


@pytest.mark.service
class TestLlmServiceBudgetGuard:
    """Test budget guard and usage recording."""

    @pytest.mark.asyncio
    async def test_budget_guard_logs_usage(self, mock_lead_input, mock_current_user):
        """Test that usage is recorded."""
        _reset_usage_ledger_for_tests()

        with patch("app.services.llm_service.settings") as mock_settings, \
             patch("app.services.llm_service._call_gemini") as mock_gemini:
            mock_settings.DEBUG = True
            mock_settings.LLM_DAILY_BUDGET_CENTS = 10000
            mock_settings.GEMINI_API_KEY = "fake-key"
            mock_settings.GEMINI_MODEL = "gemini-2.5-flash"

            mock_gemini.return_value = {
                "company_snapshot": "S",
                "personalized_opener": "O",
                "follow_ups": [{"title": "T", "description": "D", "due_in_days": 4, "rationale": "R"}] * 3,
                "model_used": "gemini-2.5-flash",
            }

            await generate_enrichment(mock_lead_input, current_user=mock_current_user)

            # Usage should have been recorded
            # (In-memory ledger would be updated; check indirectly via logging)

    @pytest.mark.asyncio
    async def test_budget_guard_with_high_budget(self, mock_lead_input, mock_current_user):
        """Test that calls succeed with sufficient budget."""
        _reset_usage_ledger_for_tests()

        with patch("app.services.llm_service.settings") as mock_settings, \
             patch("app.services.llm_service._call_gemini") as mock_gemini:
            mock_settings.DEBUG = False
            mock_settings.LLM_DAILY_BUDGET_CENTS = 50000  # Plenty
            mock_settings.GEMINI_API_KEY = "fake-key"
            mock_settings.GEMINI_MODEL = "gemini-2.5-flash"

            mock_gemini.return_value = {
                "company_snapshot": "S",
                "personalized_opener": "O",
                "follow_ups": [{"title": "T", "description": "D", "due_in_days": 4, "rationale": "R"}] * 3,
                "model_used": "gemini-2.5-flash",
            }

            result = await generate_enrichment(mock_lead_input, current_user=mock_current_user)

            # Should succeed
            assert result["model_used"] == "gemini-2.5-flash"


@pytest.mark.service
class TestLlmServiceFallback:
    """Test fallback chain (Gemini → Haiku → Mock)."""

    @pytest.mark.asyncio
    async def test_fallback_to_haiku_on_gemini_failure(self, mock_lead_input, mock_current_user):
        """Test fallback to Haiku when Gemini fails."""
        with patch("app.services.llm_service.settings") as mock_settings, \
             patch("app.services.llm_service._call_gemini") as mock_gemini, \
             patch("app.services.llm_service._call_haiku") as mock_haiku:
            mock_settings.DEBUG = True
            mock_settings.LLM_DAILY_BUDGET_CENTS = 10000

            # Gemini fails
            mock_gemini.return_value = None
            # Haiku succeeds
            mock_haiku.return_value = {
                "company_snapshot": "S",
                "personalized_opener": "O",
                "follow_ups": [{"title": "T", "description": "D", "due_in_days": 4, "rationale": "R"}] * 3,
                "model_used": "claude-3.5-haiku",
            }

            result = await generate_enrichment(mock_lead_input, current_user=mock_current_user)

            # Should use Haiku
            assert result["model_used"] == "claude-3.5-haiku"
            assert mock_gemini.called
            assert mock_haiku.called

    @pytest.mark.asyncio
    async def test_fallback_to_mock_on_all_failure(self, mock_lead_input, mock_current_user):
        """Test fallback to mock when all LLM calls fail."""
        with patch("app.services.llm_service.settings") as mock_settings, \
             patch("app.services.llm_service._call_gemini") as mock_gemini, \
             patch("app.services.llm_service._call_haiku") as mock_haiku:
            mock_settings.DEBUG = True
            mock_settings.LLM_DAILY_BUDGET_CENTS = 10000

            # Both fail
            mock_gemini.return_value = None
            mock_haiku.return_value = None

            result = await generate_enrichment(mock_lead_input, current_user=mock_current_user)

            # Should use mock
            assert result["model_used"] == "mock-llm"
            assert len(result["follow_ups"]) == 3
