# Data Model: AI-Native BD Lead Assistant

**Feature**: 004-ai-bd-assistant
**Date**: 2026-07-13
**Source**: ARCHITECTURE.md + spec.md

## Entities

### users
- id: UUID (PK)
- email: string (unique, indexed)
- google_sub: string (nullable, for OAuth)
- display_name: string
- created_at: timestamp
- updated_at: timestamp

### user_memory_profiles
- id: UUID (PK)
- user_id: UUID (FK → users, unique)
- tone_samples: JSON (array of {opener, outcome, accepted_at})
- icp_industries: JSON (array<string>)
- typical_cadence: JSON (e.g. [4,9,14])
- profile_embedding: vector (pgvector, optional aggregated profile)
- created_at / updated_at

### leads
- id: UUID (PK)
- user_id: UUID (FK → users)
- company_name: string
- contact_name: string
- contact_role: string
- signal: text
- signal_type: enum (new_leadership | funding | hiring_gap | ...)
- pain_point: text
- notes: text
- email: string (nullable)
- linkedin_url: string (nullable)
- enriched: JSON (snapshot, opener, tasks: [{title, description, due_in_days, rationale}])
- crm_provider: string
- crm_contact_id: string
- crm_deal_id: string
- created_at

### crm_connections
- id: UUID (PK)
- user_id: UUID (FK)
- provider: string ('bitrix24' | 'hubspot')
- auth_type: string ('webhook' | 'oauth')
- encrypted_credentials: bytea or JSON (envelope encrypted)
- scopes: JSON
- expires_at: timestamp (nullable)
- last_validated_at: timestamp
- created_at
- UNIQUE(user_id, provider)

### outreach_history
- id: UUID (PK)
- lead_id: UUID (FK → leads)
- user_id: UUID (FK)
- action: string (e.g. 'email_sent', 'linkedin_connect', 'closed_won')
- outcome: string (nullable)
- notes: text
- embedding: vector (optional, for semantic recall)
- created_at

### usage_ledger
- id: UUID (PK)
- user_id: UUID
- lead_id: UUID (nullable)
- model: string
- input_tokens: int
- output_tokens: int
- estimated_cost_cents: int
- created_at

## Relationships & Indexes

- users 1:N leads, 1:N crm_connections, 1:N outreach_history, 1:1 user_memory_profiles
- leads 1:N outreach_history
- Heavy indexes on (user_id, created_at) for history and memory queries.
- pgvector indexes on profile_embedding and history.embedding (HNSW or IVFFlat as appropriate).

## State Transitions (leads)

Draft (in composer) → Enriched (preview shown) → Pushed (CRM IDs recorded) → (later) Outcome recorded (via history).

## Validation Rules

- All required lead fields per BdLeadSchema in current code.
- CRM connections validated on connect and before push.
- Encrypted fields never logged in plaintext.

## Migration Notes

Use Alembic. Initial migration creates all tables + vector extension enable.

See also ARCHITECTURE.md for full schema description.
