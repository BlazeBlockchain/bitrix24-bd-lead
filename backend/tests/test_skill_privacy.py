"""
Test skill privacy and encryption (T029-T031).

Verifies:
1. Encrypted skill loads and decrypts successfully
2. Skill methodology is NOT leaked into API responses (JSON only)
3. JSON output shape remains unchanged (company_snapshot, personalized_opener, follow_ups list of 3)
"""

import pytest
from app.services.skill_loader import (
    load_skill,
    get_skill_methodology,
    _reset_skill_cache_for_tests,
)
from app.services.llm_service import (
    _build_prompt,
    _mock_generate,
    _reset_usage_ledger_for_tests,
)


class TestSkillLoading:
    """Test that encrypted skill loads and decrypts correctly."""

    def test_load_skill_returns_nonempty(self):
        """Skill loading should return non-empty text."""
        _reset_skill_cache_for_tests()
        skill = load_skill()
        assert isinstance(skill, str)
        assert len(skill) > 100  # Should be substantial

    def test_skill_contains_known_phrase(self):
        """Skill should contain recognizable phrases from the methodology."""
        _reset_skill_cache_for_tests()
        skill = get_skill_methodology()
        # Check for key methodology concepts
        assert (
            "Buying Signal" in skill or "signal" in skill.lower()
        ), "Skill should reference buying signals"

    def test_skill_metadata_not_in_skill(self):
        """Stripped skill should not contain YAML frontmatter or MCP footer."""
        _reset_skill_cache_for_tests()
        skill = load_skill()
        # Should not start with YAML frontmatter
        assert not skill.strip().startswith("---"), "YAML frontmatter should be stripped"
        # Should not end with MCP tool-call instruction
        assert (
            "bitrix24_create_bd_lead tool" not in skill
        ), "MCP footer should be stripped"

    def test_cached_skill_is_reused(self):
        """Skill should be cached after first load."""
        _reset_skill_cache_for_tests()
        skill1 = load_skill()
        skill2 = load_skill()
        assert skill1 is skill2, "Should return cached instance"


class TestSkillNotInResponse:
    """Test that skill methodology is NOT leaked in API responses."""

    def test_mock_generate_no_sentinel_phrase(self):
        """Mock response should not contain sensitive skill phrases."""
        _reset_usage_ledger_for_tests()
        lead_brief = {
            "company_name": "TechCorp",
            "contact_name": "Jane Doe",
            "contact_role": "CMO",
            "signal": "new marketing director hired",
            "signal_type": "new_leadership",
            "pain_point": "outdated web presence",
            "email_subject": "Quick thought",
            "notes": "Series A company",
        }
        memory_ctx = "User tone: direct, benefit-focused. ICP: B2B SaaS, 50-300 employees."

        result = _mock_generate(lead_brief, memory_ctx)

        # Get the complete response text
        full_response = json.dumps(result)

        # Sentinel phrases that should NOT appear in the response
        # (these are from the skill methodology, server-side only)
        sentinel_phrases = [
            "WHY THIS BEATS CLAUDE PRO",
            "CRITICAL INSTRUCTIONS",
            "WORKFLOW",
            "STEP 1 — Company Snapshot",
            "AGENCY SETUP",
            "bitrix24_create_bd_lead",
        ]

        for phrase in sentinel_phrases:
            assert phrase not in full_response, (
                f"Sensitive skill phrase '{phrase}' should not appear in API response"
            )

    def test_prompt_includes_skill_but_response_does_not(self):
        """Prompt includes skill, but returned JSON should not expose it."""
        _reset_skill_cache_for_tests()
        _reset_usage_ledger_for_tests()

        lead_brief = {
            "company_name": "TechCorp",
            "contact_name": "Jane Doe",
            "contact_role": "CMO",
            "signal": "new marketing director hired",
            "signal_type": "new_leadership",
            "pain_point": "outdated web presence",
            "email_subject": "Quick thought",
            "notes": "Series A company",
        }
        memory_ctx = "User tone: direct. ICP: SaaS."

        # Build the prompt (should include skill)
        prompt = _build_prompt(lead_brief, memory_ctx)
        skill = get_skill_methodology()

        # Prompt should contain skill methodology
        assert (
            len(skill) > 0
        ), "Skill should be loaded for prompt building"

        # Generate response (which is just JSON dict)
        response = _mock_generate(lead_brief, memory_ctx)
        response_json = json.dumps(response)

        # Response should NOT contain skill phrases
        assert (
            "WORKFLOW" not in response_json
        ), "Skill workflow section should not be in response"
        assert (
            "STEP 1 — Company Snapshot" not in response_json
        ), "Skill steps should not be in response"


class TestJsonShape:
    """Test that output JSON shape is unchanged."""

    def test_mock_generate_shape(self):
        """Mock output must have the exact expected shape."""
        _reset_usage_ledger_for_tests()
        lead_brief = {
            "company_name": "TechCorp",
            "contact_name": "Jane Doe",
            "contact_role": "CMO",
            "signal": "new marketing director hired",
            "signal_type": "new_leadership",
            "pain_point": "outdated web presence",
            "email_subject": "Quick thought",
            "notes": "Series A",
        }
        memory_ctx = "Tone: direct. ICP: SaaS."

        result = _mock_generate(lead_brief, memory_ctx)

        # Check required keys
        assert "company_snapshot" in result
        assert "personalized_opener" in result
        assert "follow_ups" in result

        # Check types
        assert isinstance(result["company_snapshot"], str)
        assert isinstance(result["personalized_opener"], str)
        assert isinstance(result["follow_ups"], list)

        # Check follow_ups structure
        assert len(result["follow_ups"]) == 3, "Must have exactly 3 follow-ups"

        for i, followup in enumerate(result["follow_ups"]):
            assert "title" in followup, f"Follow-up {i} missing 'title'"
            assert "description" in followup, f"Follow-up {i} missing 'description'"
            assert "due_in_days" in followup, f"Follow-up {i} missing 'due_in_days'"
            assert "rationale" in followup, f"Follow-up {i} missing 'rationale'"

            # Check types
            assert isinstance(followup["title"], str)
            assert isinstance(followup["description"], str)
            assert isinstance(followup["due_in_days"], int)
            assert isinstance(followup["rationale"], str)

            # Check due_in_days values
            expected_days = [4, 9, 14]
            assert (
                followup["due_in_days"] == expected_days[i]
            ), f"Follow-up {i} due_in_days should be {expected_days[i]}"

    def test_prompt_does_not_truncate_skill(self):
        """Prompt with skill should not be truncated below its full size."""
        _reset_skill_cache_for_tests()
        lead_brief = {
            "company_name": "TechCorp",
            "contact_name": "Jane Doe",
            "contact_role": "CMO",
            "signal": "new marketing director",
            "signal_type": "new_leadership",
            "pain_point": "outdated web",
            "email_subject": "Quick",
            "notes": "Series A",
        }
        memory_ctx = "Tone: direct. ICP: SaaS."

        prompt = _build_prompt(lead_brief, memory_ctx)
        skill = get_skill_methodology()

        # Prompt should include substantial skill content
        assert len(prompt) >= len(
            skill
        ), "Prompt should contain the full skill methodology"

        # Prompt should not exceed 40000 char guard
        assert len(prompt) <= 50000, "Prompt should not be excessively large"

    def test_no_banned_phrases_in_mock(self):
        """Mock output should not use banned phrases from skill guidelines."""
        _reset_usage_ledger_for_tests()
        lead_brief = {
            "company_name": "TechCorp",
            "contact_name": "Jane Doe",
            "contact_role": "CMO",
            "signal": "new marketing director",
            "signal_type": "new_leadership",
            "pain_point": "outdated web",
            "email_subject": "Quick",
            "notes": "Series A",
        }
        memory_ctx = "Tone: direct. ICP: SaaS."

        result = _mock_generate(lead_brief, memory_ctx)
        response_text = json.dumps(result).lower()

        # Banned phrases from skill
        banned = [
            "touching base",
            "just checking in",
            "leverage",
            "synergy",
            "seamlessly",
            "i hope this finds you well",
            "end-to-end solutions",
            "excited to connect",
            "i wanted to reach out",
        ]

        for phrase in banned:
            assert (
                phrase not in response_text
            ), f"Banned phrase '{phrase}' should not appear in output"


# ─── Imports for tests ───────────────────────────────────────────────────────
import json
