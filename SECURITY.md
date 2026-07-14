# Security Policy

**Last updated:** 2026-07-14  
**Status:** Production-ready for early users

## Overview

This document describes the security architecture of the AI BD Lead Assistant, including authentication, encryption, data handling, and operational security practices.

---

## 1. User Authentication (T005)

**Method:** Google OAuth2 + JWT

- Users sign up/log in via "Sign in with Google" (OAuth2 code flow).
- Backend exchanges the OAuth code for an ID token from Google.
- System extracts the Google `sub` claim and user email, stores minimal user record (email, display_name, google_sub).
- Short-lived JWT (HS256, typically 1 hour) is issued for subsequent API calls.
- Web/extension stores JWT in secure storage (httpOnly cookies or local storage with HTTPS).
- All API endpoints check the JWT via `get_current_user_api` dependency; invalid/expired tokens are rejected.

**Why Google?**
- Zero password friction for non-technical SMB buyers (target audience).
- High trust signal (new tool handling CRM credentials).
- Integrates with existing workforce identity (particularly valuable for EU/Africa teams).

**No passwords.** Email/password fallback is P2.

---

## 2. CRM Token Security (T006, T012)

**Principle:** Envelope encryption, server-only resolution.

### Storage
- Users connect their CRM (Bitrix24 webhook URL or HubSpot OAuth token) via the web app connections flow.
- Credentials are encrypted using **Fernet** (symmetric, authenticated encryption) with a master key (`ENCRYPTION_KEK` from `.env`).
- Encrypted blob is stored in the `CrmConnection` table (PostgreSQL) alongside the user ID and provider name.
- Plaintext tokens are **never written to disk or logs** — only the encrypted ciphertext is persisted.

### Resolution
- When the backend needs to create records in the CRM (`/api/leads/push`), it queries `CrmConnection` by user ID + provider.
- The encrypted credentials are decrypted **server-side only** using the same `ENCRYPTION_KEK`.
- The plaintext token is passed to the `CrmClient` adapter (Bitrix24 or HubSpot) to make the API call.
- The token is never returned to the client, never logged, never sent to third parties.

### Key Management
- `ENCRYPTION_KEK` is set in `.env` (never committed with a real value).
- In **dev mode** (DEBUG=true), if `ENCRYPTION_KEK` is empty, a dev-only fallback key is used (sufficient for local testing; never use in shared/prod).
- In **production**, `ENCRYPTION_KEK` must be a cryptographically random 32-byte secret (or base64-encoded Fernet key).
- Key rotation is manual: change `ENCRYPTION_KEK` in `.env`, re-run the decryption step (callers will use the new key for new encryptions). Existing encrypted tokens remain readable if the old key is available.

**Code references:**
- `backend/app/services/token_vault.py` — encryption/decryption, resolve_token, derive_user_uuid
- `backend/app/api/connections.py` — store/test endpoints
- `backend/app/adapters/crm/factory.py` — token resolution before CrmClient instantiation

---

## 3. Skill IP Protection (T030)

**Principle:** Encrypted at rest, decrypted server-side only, never exposed to clients.

### Architecture
The **BD Lead Research Engine** (the proprietary B2B research methodology) is stored as an encrypted artifact:
- **Plaintext source:** `backend/app/skills/bd_lead_research.source.md` (git-ignored, never committed)
- **Encrypted artifact:** `backend/app/skills/bd_lead_research.md.enc` (committed, versioned with app releases)
- **Encryption method:** Same Fernet + `ENCRYPTION_KEK` as CRM tokens (see §2)

### Loading & Caching
- On backend startup, `backend/app/services/skill_loader.py` reads the `.enc` file.
- Decrypts using `token_vault.decrypt_credentials()` (reuses the same KEK).
- Strips YAML frontmatter and MCP footer, validates that the result is valid markdown.
- Caches the plaintext skill in memory (module-level variable, one load per process lifetime).
- If decryption fails (bad key, missing file, corruption), logs a warning and returns a minimal fallback instruction (app stays up; LLM output is suboptimal).

### Injection
- The decrypted skill is injected into the LLM's system prompt (via `llm_service._build_prompt`) to shape the AI's reasoning.
- The skill is **never returned to the client** — no `/api/skill` endpoint, no embedded in web/extension bundles.
- Web/extension receive only the structured JSON output from enrichment (company_snapshot, personalized_opener, follow_ups).

### Versioning & Re-encryption (T031–T032)
- When the app version is bumped (via `make bump-patch|minor|major`), the `VERSION` file and all component versions are updated (web/package.json, extension/manifest.json, backend/app/config.py).
- If the skill source changes, re-encrypt it: `make encrypt-skill` calls `scripts/encrypt_skill.py`, which reads the plaintext `.source.md`, encrypts with the current `ENCRYPTION_KEK`, and writes the `.enc` artifact.
- The updated `.enc` is committed as part of the release; plaintext never leaves dev/version control.

**Code references:**
- `backend/app/services/skill_loader.py` — load_skill, _strip_yaml_frontmatter, _strip_mcp_footer, get_fallback_skill
- `backend/app/services/llm_service.py` — _build_prompt calls get_skill_methodology()
- `scripts/encrypt_skill.py` — encryption workflow
- `Makefile` — `encrypt-skill` target

---

## 4. LLM Keys & API Secrets (T007)

**Principle:** Server-side only, never exposed to clients.

### Configuration
- `GEMINI_API_KEY` (Google Gemini primary) and `ANTHROPIC_API_KEY` (Claude Haiku fallback) are set in `.env`.
- These are **server environment variables only** — never sent to the web app, extension, or MCP clients.
- If keys are empty, the backend uses internal mocks for dev/testing (exact same structured output shape).

### Usage
- LLM enrichment happens in `backend/app/services/llm_service.py::generate_enrichment()`.
- The backend calls the LLM API (Gemini first, Haiku fallback) with the user's lead brief + memory context + injected skill.
- Results are returned to the client as structured JSON (`company_snapshot`, `personalized_opener`, `follow_ups[3]`).
- No raw LLM prompts, tokens, or API calls are visible to the client.

### Budget & Cost Tracking (T009)
- Per-user daily budget (default $2, configurable via `LLM_DAILY_BUDGET_CENTS`).
- Every LLM call is logged to `UsageLedger` table: user_id, model, input_tokens, output_tokens, estimated_cost_cents, created_at.
- Hard guard: if today's cost exceeds the daily budget, /enrich returns an error (user can retry tomorrow or upgrade).
- Logged cost is approximate (Gemini ~$0.000075/1K input, ~$0.0003/1K output; Haiku ~$0.00080/1K in, ~$0.0024/1K out).

**Code references:**
- `backend/app/services/llm_service.py` — generate_enrichment, _record_usage, budget guard
- `backend/app/config.py` — LLM_DAILY_BUDGET_CENTS, API key settings

---

## 5. Data Handling & Logging

### What is logged
- **API requests/responses:** Path, status code, user_id (no bodies by default).
- **LLM usage:** Model, token counts, estimated cost, timestamp, user_id (no prompts/outputs).
- **Errors:** Exceptions from auth/vault/LLM/CRM, sanitized (no raw credentials or API keys).
- **Skill loading:** Startup message if skill is loaded/failed; no content.

### What is never logged
- Plaintext CRM tokens, OAuth credentials.
- LLM API keys.
- Full API request/response bodies (especially user inputs, lead details).
- Skill methodology plaintext.
- Raw JWT tokens.

### Log destinations
- Stdout (Docker logs, `docker compose logs -f bdlead-backend`).
- In production, redirect to centralized logging (e.g., ELK, CloudWatch, Datadog).
- Logs are kept for 7 days by default (configurable per deployment).

**Code reference:**
- `backend/app/main.py` — logging configuration
- Individual service files — app-level debug logs marked with `logger.debug(...)` or `logger.warning(...)`

---

## 6. Data Retention & Deletion

### User-initiated deletion
- Users can request deletion of their account and all associated data (history, memory profile, usage logs).
- **Scope:** All rows in leads, outreach_history, usage_ledger, user_memory_profiles with matching user_id.
- **CrmConnection:** Stored tokens are deleted (not retrievable, encryption keys are discarded).
- **Timeframe:** Processed within 30 days (to accommodate audit/compliance).

### Automatic deletion (roadmap)
- Lead history older than 1 year is automatically archived and deleted (roadmap, not yet implemented).
- Usage logs older than 1 month are deleted (roadmap).

### Data recovery
- Backups are kept for 30 days (disaster recovery); older backups are deleted.
- In case of data loss, users must re-authenticate and re-enter CRM credentials.

---

## 7. Threat Model & Mitigations

### Threat: Unauthorized API access
**Scenario:** Attacker tries to call /push or /enrich without a valid user JWT.  
**Mitigation:** All protected endpoints require `get_current_user_api` (validates Bearer token). Invalid/expired tokens return 403 Unauthorized. Rate limiting (future T024+) can throttle brute-force attempts.

### Threat: CRM credential theft (database breach)
**Scenario:** Database is compromised; attacker reads `CrmConnection.encrypted_credentials` column.  
**Mitigation:** Encrypted with Fernet (AES-128-CBC + HMAC); attacker would also need the `ENCRYPTION_KEK` (stored in `.env`, not in the database). Without the key, the ciphertext is useless.

### Threat: Skill IP theft (database/code breach)
**Scenario:** Attacker obtains `backend/app/skills/bd_lead_research.md.enc` from git or database backups.  
**Mitigation:** Encrypted with Fernet + `ENCRYPTION_KEK` (same as CRM tokens). Without the key, the `.enc` artifact is unintelligible. Plaintext source is git-ignored; never in version control.

### Threat: LLM API key compromise
**Scenario:** `GEMINI_API_KEY` or `ANTHROPIC_API_KEY` is leaked.  
**Mitigation:** Keys are stored in `.env` (never committed). Web/extension cannot access them (server-only). If leaked, rotate the key in the LLM provider console and update `.env`. Cost limits (LLM_DAILY_BUDGET_CENTS) cap runaway usage.

### Threat: Google OAuth redirect hijacking
**Scenario:** Attacker tricks user into authorizing a malicious app or intercepts OAuth callback.  
**Mitigation:** OAuth code exchange is server-side only (backend directly calls Google servers). State parameter is validated. Redirect URIs are whitelisted in Google Console.

### Threat: User impersonation via JWT forgery
**Scenario:** Attacker tries to forge a JWT to access another user's data.  
**Mitigation:** JWT is signed with `JWT_SECRET` (HS256). Attacker would need the secret (stored in `.env`, not shared). Token expiry (1 hour) limits window. Refresh tokens can be short-lived and server-validated.

### Threat: XSS in web app or extension
**Scenario:** Attacker injects malicious JS that steals user JWT or CRM credentials.  
**Mitigation:**  
- Web app uses React (auto-escapes template expressions).
- Extension uses Manifest V3 (no eval, no inline scripts, Content Security Policy).
- JWTs are stored in secure storage (httpOnly cookies, if possible; or local storage + HTTPS only).
- CRM credentials are never shown in UI; only masked summaries.

### Threat: CSRF attack on state-changing endpoints
**Scenario:** Attacker tricks user's browser into making unauthorized API calls (e.g., connecting a malicious CRM).  
**Mitigation:**  
- Backend checks `Origin` / `Referer` headers (web only).
- API is JSON (not form-encoded), so cross-origin requests are rejected by CORS.
- State-changing operations (connect, push) require explicit user action in the UI.

---

## 8. Production Deployment Checklist

Before going live to real users:

- [ ] Set `ENCRYPTION_KEK` to a real 32-byte secret (not the dev fallback).
  ```bash
  openssl rand -base64 32  # Generate a new key
  ```
  Add to production `.env`.

- [ ] Re-encrypt the skill artifact with the production key:
  ```bash
  make encrypt-skill  # Reads .source.md, encrypts with ENCRYPTION_KEK, writes .enc
  git add backend/app/skills/bd_lead_research.md.enc
  git commit -m "chore: re-encrypt skill with production ENCRYPTION_KEK"
  ```

- [ ] Set `JWT_SECRET` to a real secret (not the dev placeholder).
  ```bash
  openssl rand -hex 32  # Generate a new secret
  ```
  Add to production `.env`.

- [ ] Set `DEBUG = False` in production `.env` (or via config override).

- [ ] Set real LLM keys (`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`) if using real LLM calls (not mocks).

- [ ] Configure Google OAuth:
  - Create a Google Cloud project.
  - Register the redirect URI (e.g., `https://bdlead.example.com/auth/google/callback`).
  - Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`.
  - Add the domain to CORS allowlist (web app origin).

- [ ] Enable HTTPS (TLS cert from Let's Encrypt or your CA).

- [ ] Set up database backups (PostgreSQL dump, daily, 30-day retention).

- [ ] Configure logging (redirect stdout to centralized logging service).

- [ ] Run smoke tests:
  ```bash
  python scripts/e2e_smoke_t020.py --provider bitrix24 --use-backend
  python scripts/e2e_smoke_t020.py --provider hubspot --use-backend
  ```
  Verify that enrichment + CRM creation works end-to-end.

- [ ] Document data retention policy (see §6) and add to terms of service.

- [ ] Conduct a security review (internal or external audit) of `token_vault.py`, `skill_loader.py`, auth endpoints.

---

## 9. Reporting Security Issues

If you discover a security vulnerability, please **do not** open a public GitHub issue. Instead:
1. Email `security@example.com` with details (or use GitHub's private security advisory form).
2. Include the affected version, reproduction steps, and impact assessment.
3. Allow 30 days for a fix before public disclosure.

---

## References

- [Google OAuth2 documentation](https://developers.google.com/identity/protocols/oauth2)
- [Cryptography.io — Fernet (symmetric encryption)](https://cryptography.io/en/latest/fernet/)
- [OWASP — API Security Top 10](https://owasp.org/www-project-api-security/)
- Code: `backend/app/services/token_vault.py`, `backend/app/services/skill_loader.py`, `backend/app/main.py`
