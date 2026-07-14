# Security Notes for AI-Native BD Lead Assistant (T023)

**Status**: Early MVP (as of 2026-07-14). Applies to backend (FastAPI), web, extension, MCP wrapper. Grounded in `docs/ARCHITECTURE.md`, `specs/004-ai-bd-assistant/{plan.md,spec.md,data-model.md}`, `BUILD_COORDINATION.md`, and implementation in `backend/`.

**Audience**: Early users, developers, reviewers. This is a basic note for pre-launch users; full audit + pen-test later.

## 1. CRM Token Handling (T006)
- **Envelope encryption at rest**: CRM credentials (Bitrix24 webhook URLs or HubSpot access tokens) are stored encrypted in `crm_connections.encrypted_credentials` (see `backend/app/models/crm_connection.py`).
- **Implementation**: `backend/app/services/token_vault.py` provides:
  - `encrypt_credentials(plaintext)` / `decrypt_credentials(ciphertext)` using `cryptography.fernet.Fernet`.
  - Master key from `settings.ENCRYPTION_KEK` (see config below).
  - `resolve_token(current_user, provider, override=None)` — precedence: explicit override (?token= for dev), per-user lookup via CrmConnection (decrypt), DEBUG fallback to settings, else error.
- **Never in client**: Tokens resolved **server-side only**. Web app + extension + MCP receive only auth JWT (user identity). Resolved plaintext token is injected only into `CrmClient` ctor inside `backend/app/adapters/crm/__init__.py` factory and `lead_service.py`. No token ever sent to browser/extension/MCP client.
- **References**: `token_vault.py`, `main.py` (push_lead uses `resolve_token`), `lead_service.py`, factory, `CrmConnection` model (unique user+provider).
- **Auth type**: Bitrix webhook (simple URL), HubSpot OAuth (token stored post-exchange). Connect flows (future T012) will store via vault.

**Security: tokens resolved server side only via vault; see backend/app/services/token_vault.py and llm budget checks. For T020 tests avoid logging real tokens.**

## 2. LLM Keys (T007)
- **Server-side only**: `GEMINI_API_KEY` and `ANTHROPIC_API_KEY` (for Gemini 2.5 Flash primary + Claude Haiku fallback) live exclusively in server `backend/app/config.py` (loaded via pydantic-settings from `.env`).
- No exposure to clients, extension, MCP, or frontend. All LLM calls happen in `backend/app/services/llm_service.py` (`_call_gemini`, `_call_haiku`).
- If keys absent or `DEBUG=True` or budget fail: deterministic internal mock used (no external calls).
- Keys never logged or returned in API responses.

## 3. Budgets + Per-User Limits + Usage Logging (T007 + T009)
- **Budgets**: Hard per-user daily cap in `llm_service.py` via `_check_budget()` using `settings.LLM_DAILY_BUDGET_CENTS` (default 200). Exceed → mock response + `"note": "budget_exceeded_mocked"`. Early guard against cost overrun (NFR <$0.01/lead target).
- **Logging of usage**: `_record_usage()` emits structured `LLM_USAGE` log (user, model, in/out tokens, cost_cents, daily_total). Mirrors `usage_ledger` table (see model).
- **T009**: `backend/app/models/usage_ledger.py` + `User`/`Lead` rels ready for persistence (user_id, lead_id nullable, model, tokens, estimated_cost_cents, created_at). In-mem stub today; real INSERT planned for T010+.
- Per-request size guard in prompt builder (truncation >6000 chars).
- No user-facing billing yet (stub); usage visible in future dashboard (T015).

## 4. Authentication
- **Google JWT only**: Sign-in via Google OAuth (FR-001). Backend exchanges → stores `google_sub` + email in `users` table. Issues short-lived JWT (HS256 via `JWT_SECRET`).
- **No passwords stored**: Zero password fields or hashing. `User` model: id, email (unique), google_sub (nullable), display_name, timestamps. See `backend/app/models/user.py`.
- Protected routes: `Depends(get_current_user)` in `main.py` (placeholder decode + DEBUG fallbacks for skeleton; real `python-jose` + Google token validation later). Returns minimal `{id, email, display_name}`.
- JWT carried by web/extension; never CRM tokens.
- Extension: thin client uses stored JWT for backend calls.

## 5. Logging
- **What is logged** (via `logging.getLogger(__name__)`):
  - Usage events: `LLM_USAGE` (structured, includes user id/email, model, tokens, cost; NO credentials or prompts).
  - Lead creation events: debug on `/push` (user email/id, provider), orchestration success (ids returned via lead_service).
  - Auth: debug on `get_current_user` (stub user notes, placeholder JWT decode failures — token_preview truncated only).
  - Startup/shutdown, warnings (budget exceed, decrypt fail in DEBUG only), errors (with traceback but no secrets).
- **Levels**: INFO (startup, usage), DEBUG (auth details, token resolve in dev), WARNING (budget, fallback), ERROR/EXCEPTION (CRM/LLM failures).
- **No secrets ever**: Explicit policy — tokens, keys, JWT payloads (beyond user claims), full prompts, or raw credentials never in logs. `token_preview` truncated. DEBUG fallbacks safe for local.
- Logs go to stdout (container-friendly); no PII beyond necessary user id for ops/budgets.

## 6. Data Retention for Leads / History
- Leads + enriched data (snapshot, opener, follow_ups) + `outreach_history` + `user_memory_profiles` stored per-user (FKs in Postgres + pgvector).
- Retention: User-owned. No automatic purge policy yet; documented intent per ARCHITECTURE + dev-options: "user can request purge of history".
- GDPR-aligned for target (CEE/Africa) users: export/delete on request (future admin/endpoint). Memory profiles improve personalization but scoped to user-provided leads + outcomes (not full CRM scrape).
- Encrypted fields (tokens) never exposed in history/ledgers.
- See: `data-model.md` (entities + indexes on user_id+created_at), `models/lead.py`, `outreach_history.py`, `user_memory_profile.py`.

## 7. Code References (Current Impl)
- Token vault + resolve: `backend/app/services/token_vault.py` (Fernet + KEK, resolve_token).
- LLM budgets/logging: `backend/app/services/llm_service.py` (_check_budget, _record_usage, generate_enrichment).
- Config: `backend/app/config.py` (GEMINI_*, ANTHROPIC_*, LLM_DAILY_BUDGET_CENTS, JWT_SECRET, future ENCRYPTION_KEK; load from .env).
- Protected entry: `backend/app/main.py` (get_current_user dep, /api/leads/{enrich,push}).
- Models: `backend/app/models/{user.py, crm_connection.py (encrypted_credentials), usage_ledger.py, lead.py}`.
- Orchestration: `backend/app/services/lead_service.py` (passes current_user; enrichment before Crm).
- Adapters: `backend/app/adapters/crm/__init__.py` (factory accepts current_user for vault).
- ARCH refs: "Security & Compliance Highlights", Google Auth section.
- .env.example + quickstart.md document vars (add `ENCRYPTION_KEK=...` for prod; 32+ bytes recommended).

## 8. Basic Threat Model for Early Users
**Assumptions (early / small user base)**: Single VPS Docker; no high-value targets yet; trust in Google + cheap LLM providers; users are SMB BD reps (not adversarial).

**In scope / protected**:
- CRM token compromise (at rest or transit): Mitigated by server-only resolution + envelope encryption (Fernet). Breach of DB yields ciphertext only (needs KEK). No tokens in browser storage.
- LLM cost abuse / runaway: Per-user daily hard budget + request cap + mock fallback. Usage ledger for monitoring.
- Auth bypass / token theft: Google OAuth + short JWT (no passwords). Placeholder validation in skeleton (hardened in T005+).
- Data exposure (leads/memory): Per-user isolation via FKs + auth dep. No cross-user access in current paths.
- Logging / observability leaks: Explicit no-secrets rule + truncation.

**Out of scope / residual (early)**:
- Full supply-chain (deps like cryptography, google-genai, FastAPI) — pin + review later.
- Side-channel on VPS (container escape, host access) — use secrets mgmt (e.g. Docker secrets / env from vault) in prod.
- Malicious lead input (prompt injection): Basic "JSON ONLY" + short prompts; sanitize later.
- Extension storage: JWT only (not CRM tokens); MV3 limits.
- No rate-limit on public paths yet (CORS open in skeleton).
- No audit log for memory reads (future).
- Real KMS/DEK-per-user envelope vs current master Fernet stub (T006 noted as stub; upgrade before paid users).
- GDPR full compliance / DPO (policy + request handlers later).

**Recommendations for early users**:
- Set strong unique `ENCRYPTION_KEK`, `JWT_SECRET` in prod `.env` (never commit).
- Run behind TLS reverse proxy.
- Monitor usage_ledger + LLM logs for anomalies.
- For T020 sandbox tests: use demo tokens only; **avoid logging real tokens** (see shared note).
- Report issues via project channels; request data purge.
- Do not paste sensitive CRM data beyond minimal brief until v1 hardened.

## 9. Future / Hardening (post early)
- Real per-connection DEK + KMS wrapping.
- Full JWT verification + refresh + Google token validation.
- Structured audit logging.
- Request rate limiting + input sanitization.
- Data retention policy + self-serve delete.
- Security review + bug bounty before public launch.
- Redis for distributed budgets/rate limits (vs in-mem).

See also:
- `docs/ARCHITECTURE.md` §Security & Compliance + Google Auth.
- `docs/development-options.md` §Risks (custodians of tokens/keys/data).
- `specs/004-ai-bd-assistant/data-model.md` (encrypted fields, retention notes).
- `BUILD_COORDINATION.md` (T006/T007/T009 logs + "Security: ..." share).
- `REVIEW_FOR_T007.md`, `REVIEW_FOR_T009.md`, `REVIEW_FOR_T023.md`.

**Last updated**: 2026-07-14 by T023 Implementer. Accurate to current backend impl (no changes to vault/llm/config/main code; docs only).

If you find a security issue, treat as high priority.