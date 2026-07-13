/**
 * API client stub for BD Lead web app (T011 skeleton).
 * Uses native fetch (per project "use native fetch" guideline).
 * Targets backend at http://localhost:8000 (current state: /api/health + /api/leads/push stub).
 * Supports provider + token query params for demo (matches backend stub; real JWT later T005+).
 */

const API_BASE = 'http://localhost:8000/api';

export interface LeadPushInput {
  company_name: string;
  deal_name: string;
  contact_name: string;
  contact_role: string;
  signal?: string;
  signal_type?: string;
  pain_point?: string;
  email_subject?: string;
  notes?: string;
}

export interface PushResult {
  contact_id: string;
  deal_id: string;
  task1: { id: string; date: string };
  task2: { id: string; date: string };
  task3: { id: string; date: string };
  provider: string;
  note?: string;
  [key: string]: any;
}

export interface HealthResponse {
  status: string;
  version: string;
  provider_default: string;
}

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

/**
 * POST to /api/leads/push using stub backend.
 * For demo: pass provider and optional token (will be sent as query params).
 * In future: will use auth header + full enrich flow.
 */
export async function pushLead(
  input: LeadPushInput,
  provider: 'bitrix24' | 'hubspot' = 'bitrix24',
  token?: string
): Promise<PushResult> {
  const params = new URLSearchParams({ provider });
  if (token) params.set('token', token);

  const res = await fetch(`${API_BASE}/leads/push?${params.toString()}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      // JWT will go here later: 'Authorization': `Bearer ${jwt}`
    },
    body: JSON.stringify(input),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Push failed: ${res.status}`);
  }

  return res.json();
}

// Future: enrichLead(input) etc. for T013 full when /api/enrich exists.
