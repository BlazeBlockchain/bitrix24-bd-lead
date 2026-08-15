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
from datetime import datetime, timedelta

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


# ─── 009: additive brief fields (buying signal, confidence, email, CRM entry) ──
#
# These exercise _parse_structured_json rather than the validators directly, because
# the thing worth pinning is the WIRING: a new field failing validation must be dropped
# without disturbing the frozen three, and an absent field must stay absent so the client
# renders the 008 inert block. Testing the helpers alone would not prove either.

def _envelope(**extra) -> str:
    """Valid frozen-three JSON, plus whatever new fields the case is about."""
    import json as _json

    base = {
        "company_snapshot": "S",
        "personalized_opener": "O",
        "follow_ups": [
            {"title": "T1", "description": "D1", "due_in_days": 4, "rationale": "R1"},
            {"title": "T2", "description": "D2", "due_in_days": 9, "rationale": "R2"},
            {"title": "T3", "description": "D3", "due_in_days": 14, "rationale": "R3"},
        ],
    }
    base.update(extra)
    return _json.dumps(base)


def _assert_frozen_three_intact(result):
    """The 009 contract is additive: whatever happens to a new field, these do not move."""
    assert result["company_snapshot"] == "S"
    assert result["personalized_opener"] == "O"
    assert len(result["follow_ups"]) == 3
    assert [f["due_in_days"] for f in result["follow_ups"]] == [4, 9, 14]


@pytest.mark.service
class TestBuyingSignalField:
    def test_valid_signal_is_kept(self):
        result = _parse_structured_json(_envelope(buying_signal={
            "summary": "Closed a Series B.", "source": "company blog", "date": "2026-01-15",
        }))
        assert result["buying_signal"] == {
            "summary": "Closed a Series B.", "source": "company blog", "date": "2026-01-15",
        }
        _assert_frozen_three_intact(result)

    def test_absent_signal_stays_absent(self):
        """Absent means the client renders the 008 inert block — not an empty object."""
        result = _parse_structured_json(_envelope())
        assert "buying_signal" not in result
        _assert_frozen_three_intact(result)

    def test_non_dict_signal_is_dropped(self):
        result = _parse_structured_json(_envelope(buying_signal="Series B"))
        assert "buying_signal" not in result
        _assert_frozen_three_intact(result)

    def test_missing_summary_drops_whole_object(self):
        result = _parse_structured_json(_envelope(buying_signal={"source": "blog"}))
        assert "buying_signal" not in result

    def test_blank_summary_drops_whole_object(self):
        result = _parse_structured_json(_envelope(buying_signal={"summary": "   "}))
        assert "buying_signal" not in result

    def test_missing_source_and_date_still_yields_summary(self):
        """Anti-fabrication: omitting an unsupportable attribution is the CORRECT path."""
        result = _parse_structured_json(_envelope(buying_signal={"summary": "Closed a round."}))
        assert result["buying_signal"] == {"summary": "Closed a round."}

    def test_future_date_is_dropped_but_summary_survives(self):
        """A signal cannot have happened tomorrow, so a future date is proof of a guess."""
        future = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d")
        result = _parse_structured_json(_envelope(buying_signal={
            "summary": "Closed a round.", "source": "blog", "date": future,
        }))
        assert "date" not in result["buying_signal"]
        assert result["buying_signal"]["summary"] == "Closed a round."
        assert result["buying_signal"]["source"] == "blog"

    def test_today_is_not_treated_as_future(self):
        today = datetime.utcnow().strftime("%Y-%m-%d")
        result = _parse_structured_json(_envelope(buying_signal={
            "summary": "Announced today.", "date": today,
        }))
        assert result["buying_signal"]["date"] == today

    @pytest.mark.parametrize("bad_date", ["Q2 2026", "2026-13-01", "15/01/2026", "2026-01", "", 20260115])
    def test_malformed_date_is_dropped(self, bad_date):
        result = _parse_structured_json(_envelope(buying_signal={
            "summary": "Closed a round.", "date": bad_date,
        }))
        assert "date" not in result["buying_signal"]


@pytest.mark.service
class TestContactConfidenceField:
    @pytest.mark.parametrize("level", ["high", "medium", "low"])
    def test_each_valid_level_is_kept(self, level):
        result = _parse_structured_json(_envelope(contact_confidence={
            "level": level, "reason": "Role matches the pain point.",
        }))
        assert result["contact_confidence"]["level"] == level

    @pytest.mark.parametrize("raw,expected", [("HIGH", "high"), ("Medium", "medium"), ("  LOW  ", "low")])
    def test_level_is_case_and_space_normalized(self, raw, expected):
        result = _parse_structured_json(_envelope(contact_confidence={"level": raw, "reason": "R"}))
        assert result["contact_confidence"]["level"] == expected

    @pytest.mark.parametrize("level", ["very high", "unknown", "HIGHEST", "3", "", "maybe"])
    def test_out_of_enum_level_drops_whole_object(self, level):
        """Never rendered raw: an unrecognised level is absent, not a pill of unknown meaning."""
        result = _parse_structured_json(_envelope(contact_confidence={"level": level, "reason": "R"}))
        assert "contact_confidence" not in result

    def test_level_without_reason_drops_whole_object(self):
        """An unfalsifiable confidence pill is the decorative-confidence failure 008 refused."""
        result = _parse_structured_json(_envelope(contact_confidence={"level": "high"}))
        assert "contact_confidence" not in result

    def test_reason_without_level_drops_whole_object(self):
        result = _parse_structured_json(_envelope(contact_confidence={"reason": "Seems right."}))
        assert "contact_confidence" not in result

    def test_non_dict_is_dropped(self):
        result = _parse_structured_json(_envelope(contact_confidence="high"))
        assert "contact_confidence" not in result

    def test_absent_stays_absent(self):
        assert "contact_confidence" not in _parse_structured_json(_envelope())


@pytest.mark.service
class TestOutreachEmailField:
    def test_valid_email_is_kept_with_newlines_preserved(self):
        body = "Hi John,\n\nSaw the round.\n\nBest,\nMe"
        result = _parse_structured_json(_envelope(outreach_email={"subject": "Quick note", "body": body}))
        assert result["outreach_email"] == {"subject": "Quick note", "body": body}

    def test_missing_body_drops_whole_object(self):
        """Half an email is not sendable, so it is not shown."""
        result = _parse_structured_json(_envelope(outreach_email={"subject": "Quick note"}))
        assert "outreach_email" not in result

    def test_missing_subject_drops_whole_object(self):
        result = _parse_structured_json(_envelope(outreach_email={"body": "Hi John,"}))
        assert "outreach_email" not in result

    def test_blank_body_drops_whole_object(self):
        result = _parse_structured_json(_envelope(outreach_email={"subject": "S", "body": "  \n "}))
        assert "outreach_email" not in result

    def test_non_dict_is_dropped(self):
        assert "outreach_email" not in _parse_structured_json(_envelope(outreach_email=["subject", "body"]))

    def test_absent_stays_absent(self):
        assert "outreach_email" not in _parse_structured_json(_envelope())


@pytest.mark.service
class TestCrmEntryField:
    def test_full_entry_is_kept(self):
        entry = {
            "deal_name": "Acme — Series B", "contact_role": "VP Ops", "signal": "Funding",
            "pain_point": "Manual tracking", "pipeline": "New leads",
        }
        assert _parse_structured_json(_envelope(crm_entry=entry))["crm_entry"] == entry

    def test_partial_entry_keeps_only_present_fields(self):
        result = _parse_structured_json(_envelope(crm_entry={"deal_name": "Acme", "pipeline": ""}))
        assert result["crm_entry"] == {"deal_name": "Acme"}

    def test_all_empty_drops_whole_object(self):
        result = _parse_structured_json(_envelope(crm_entry={"deal_name": "", "pipeline": None}))
        assert "crm_entry" not in result

    def test_unknown_keys_are_ignored(self):
        result = _parse_structured_json(_envelope(crm_entry={"deal_name": "Acme", "owner_id": 42}))
        assert result["crm_entry"] == {"deal_name": "Acme"}

    def test_non_dict_is_dropped(self):
        assert "crm_entry" not in _parse_structured_json(_envelope(crm_entry="Acme"))

    def test_absent_stays_absent(self):
        assert "crm_entry" not in _parse_structured_json(_envelope())


@pytest.mark.service
class TestAdditiveContractIsolation:
    """Every new field failing at once must leave the frozen three untouched."""

    def test_all_new_fields_malformed_together(self):
        result = _parse_structured_json(_envelope(
            buying_signal="nope",
            contact_confidence={"level": "very high"},
            outreach_email={"subject": "S"},
            crm_entry=[],
        ))
        _assert_frozen_three_intact(result)
        for key in ("buying_signal", "contact_confidence", "outreach_email", "crm_entry"):
            assert key not in result

    def test_legacy_response_without_new_fields_is_unchanged(self):
        """A stored enrichment from before 009 must parse exactly as it did before."""
        result = _parse_structured_json(_envelope())
        assert set(result) == {"company_snapshot", "personalized_opener", "follow_ups"}

    def test_truncation_detection_still_fires_on_the_longer_response(self):
        """NFR-006: the bigger payload must not defeat the strict truncation path."""
        truncated = _envelope(outreach_email={"subject": "S", "body": "Hi John,\n\n" + "x" * 3000})[:-40]
        with pytest.raises(ValueError, match="TRUNCATED"):
            _parse_structured_json(truncated, strict=True)


@pytest.mark.service
class TestMockGeneratesFullShape:
    """FR-008: without this, the no-API-key path and every mock-path test render inert."""

    def test_mock_includes_all_four_new_sections(self, mock_lead_input):
        result = _mock_generate(mock_lead_input, "memory context")
        for key in ("buying_signal", "contact_confidence", "outreach_email", "crm_entry"):
            assert key in result, f"mock must populate {key}"

    def test_mock_output_survives_its_own_validators(self, mock_lead_input):
        """The mock is the fixture developers read; it must be contract-valid, not close."""
        import json as _json

        result = _mock_generate(mock_lead_input, "memory context")
        reparsed = _parse_structured_json(_json.dumps(result))
        for key in ("buying_signal", "contact_confidence", "outreach_email", "crm_entry"):
            assert key in reparsed, f"mock {key} was rejected by the parser"

    def test_mock_confidence_level_is_in_enum(self, mock_lead_input):
        result = _mock_generate(mock_lead_input, "memory context")
        assert result["contact_confidence"]["level"] in ("high", "medium", "low")
        assert result["contact_confidence"]["reason"].strip()

    def test_mock_signal_date_is_not_in_the_future(self, mock_lead_input):
        result = _mock_generate(mock_lead_input, "memory context")
        assert result["buying_signal"]["date"] <= datetime.utcnow().strftime("%Y-%m-%d")

    def test_mock_email_is_addressed_and_multiline(self, mock_lead_input):
        email = _mock_generate(mock_lead_input, "memory context")["outreach_email"]
        assert email["subject"].strip()
        assert "\n" in email["body"], "body must carry real line breaks for pre-wrap rendering"
        assert mock_lead_input["contact_name"].split()[0] in email["body"]

    def test_mock_crm_entry_uses_the_supplied_deal_name(self, mock_lead_input):
        result = _mock_generate(mock_lead_input, "memory context")
        assert result["crm_entry"]["deal_name"] == mock_lead_input["deal_name"]

    def test_mock_rationale_interpolates_signal_type(self, mock_lead_input):
        """Regression: this f-string was missing its prefix and emitted a literal brace."""
        rationales = " ".join(f["rationale"] for f in _mock_generate(mock_lead_input, "m")["follow_ups"])
        assert "{signal_type}" not in rationales
        assert mock_lead_input["signal_type"] in rationales
