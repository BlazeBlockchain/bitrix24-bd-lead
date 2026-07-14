"""
Skill Loader (T030).

Loads and decrypts the encrypted BD Lead Research skill methodology.
Provides cached access to the skill for prompt injection.

The skill is stored as an encrypted artifact (backend/app/skills/bd_lead_research.md.enc)
and loaded once per process, with the plaintext methodology cached in memory.

The skill is NEVER returned to clients and NEVER appears in API responses — it is
server-side IP used only to shape the LLM's reasoning in _build_prompt.
"""

import logging
from pathlib import Path
from typing import Optional

from app.services.token_vault import decrypt_credentials

logger = logging.getLogger(__name__)

# ─── Module-level cache (load once per process) ───────────────────────────────
_cached_skill: Optional[str] = None
_skill_load_attempted: bool = False


def _strip_yaml_frontmatter(text: str) -> str:
    """Remove leading YAML frontmatter (--- ... ---)."""
    lines = text.split("\n")
    if not lines or not lines[0].strip().startswith("---"):
        return text

    # Find closing ---
    for i in range(1, len(lines)):
        if lines[i].strip().startswith("---"):
            # Return everything after the closing ---
            return "\n".join(lines[i + 1:])

    # If no closing found, return as-is
    return text


def _strip_mcp_footer(text: str) -> str:
    """Remove the MCP tool-call footer at the end of the skill.

    Looks for the line starting with 'IMPORTANT: After writing the BITRIX24 section...'
    and removes it plus any text after it.
    """
    # Find the MCP footer marker
    marker = "IMPORTANT: After writing the BITRIX24 section"
    idx = text.find(marker)
    if idx != -1:
        return text[:idx].rstrip()
    return text


def load_skill() -> str:
    """Load and decrypt the skill methodology from the encrypted artifact.

    Returns the plaintext skill (without YAML frontmatter and MCP footer).
    Cached in memory for the process lifetime.

    If decryption fails or the file is missing, logs a warning and returns
    a safe fallback instruction string (app never crashes).
    """
    global _cached_skill, _skill_load_attempted

    if _cached_skill is not None:
        return _cached_skill

    if _skill_load_attempted:
        # Already tried to load and failed; return fallback
        return _get_fallback_skill()

    _skill_load_attempted = True

    # Try to read the encrypted file
    enc_path = Path(__file__).parent.parent / "skills" / "bd_lead_research.md.enc"

    if not enc_path.exists():
        logger.warning(f"Encrypted skill file not found: {enc_path}")
        return _get_fallback_skill()

    try:
        ciphertext = enc_path.read_text(encoding="utf-8")
        if not ciphertext:
            logger.warning("Encrypted skill file is empty")
            return _get_fallback_skill()

        # Decrypt using token_vault mechanism (same key as CRM credentials)
        plaintext = decrypt_credentials(ciphertext)

        # Guard against silent corruption: in settings.DEBUG, token_vault's
        # decrypt_credentials() intentionally swallows InvalidToken/decrypt
        # errors and returns the raw ciphertext unchanged (a dev convenience
        # for CRM tokens that may be stored unencrypted in dev). That means a
        # bad key or a corrupted/tampered .enc file would NOT raise here in
        # DEBUG mode, and we'd otherwise cache the undecrypted ciphertext
        # blob as if it were the real skill text. Validate that decryption
        # actually produced the expected skill markdown (starts with the
        # YAML frontmatter fence) before trusting it; otherwise treat it the
        # same as any other decrypt failure and use the safe fallback.
        if not plaintext.strip().startswith("---"):
            logger.warning(
                "Decrypted skill does not look like valid skill markdown "
                "(missing YAML frontmatter) — treating as decrypt failure"
            )
            return _get_fallback_skill()

        # Strip YAML frontmatter and MCP footer
        plaintext = _strip_yaml_frontmatter(plaintext)
        plaintext = _strip_mcp_footer(plaintext)
        plaintext = plaintext.strip()

        if not plaintext:
            logger.warning("Decrypted skill is empty after stripping")
            return _get_fallback_skill()

        _cached_skill = plaintext
        logger.info(f"Skill methodology loaded and cached ({len(plaintext)} bytes)")
        return _cached_skill

    except Exception as e:
        logger.warning(f"Failed to load/decrypt skill: {e}")
        return _get_fallback_skill()


def _get_fallback_skill() -> str:
    """Return a safe minimal fallback instruction when skill loading fails.

    This is NOT the real skill, just enough to keep the app running without crashing.
    The LLM will produce less optimized output, but the system remains operational.
    """
    return (
        "SKILL METHODOLOGY (FALLBACK — encrypted skill unavailable):\n"
        "Generate a B2B sales research insight with:\n"
        "1. company_snapshot: brief factual statement about the company\n"
        "2. personalized_opener: short cold email (2-4 sentences, benefit-focused, reference the signal)\n"
        "3. follow_ups: exactly 3 follow-up actions at days 4, 9, and 14\n"
        "Tone: professional, specific, no generic phrases.\n"
        "CRITICAL: Output MUST be valid JSON only — no prose or markdown.\n"
    )


def get_skill_methodology() -> str:
    """Public accessor for the loaded skill methodology.

    Returns the plaintext skill text (stripped of frontmatter and footer).
    Used by llm_service._build_prompt to inject methodology into the LLM's system prompt.
    """
    return load_skill()


# Convenience for testing: reset cache
def _reset_skill_cache_for_tests() -> None:
    """Test helper: clear the cached skill to force reload on next call."""
    global _cached_skill, _skill_load_attempted
    _cached_skill = None
    _skill_load_attempted = False
