/**
 * API client stub for BD Lead web app (T011 skeleton).
 * Uses native fetch (per project "use native fetch" guideline).
 * In dev: proxies to http://localhost:8000 via Vite dev server.
 * In prod: nginx reverse proxies /api -> backend service.
 * Supports provider + token query params for demo (matches backend stub; real JWT later T005+).
 */

const base = import.meta.env.BASE_URL.replace(/\/$/, '');
const API_BASE = base + '/api';

/** Get stored JWT for Authorization header. */
function getAuthToken(): string | null {
  try {
    return localStorage.getItem('bd_lead_jwt');
  } catch {
    return null;
  }
}

/** Helper: merge auth header into fetch options. */
function authHeaders(): Record<string, string> {
  const token = getAuthToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/** An API failure that carries the HTTP status, so callers can tell 401 from 500. */
export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

let onUnauthorized: (() => void) | null = null;

/**
 * Register what should happen when the API rejects our token (401).
 * appStore wires this to logout() so an expired session sends the user to
 * sign-in instead of leaving them on a dashboard full of empty states.
 */
export function setUnauthorizedHandler(fn: () => void): void {
  onUnauthorized = fn;
}

/**
 * Throw on 401 rather than letting a caller degrade to empty data.
 *
 * Several read endpoints below return an empty payload when the response is not
 * ok, which is a reasonable degradation when the backend is down but is actively
 * misleading for 401: an expired session rendered as "no connections stored yet",
 * an empty History, and zeroed Usage — indistinguishable from a new account.
 * JWTs here last 60 minutes, so this is the normal state of any tab left open.
 */
function rejectIfUnauthorized(res: Response): void {
  if (res.status === 401) {
    onUnauthorized?.();
    throw new ApiError('Your session expired. Please sign in again.', 401);
  }
}

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
      ...authHeaders(),
    },
    body: JSON.stringify(input),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Push failed: ${res.status}`);
  }

  return res.json();
}

// T014 + T013: history + enrich (additive, no breakage to push)
export async function getHistory(limit = 20): Promise<any[]> {
  const res = await fetch(`${API_BASE}/leads/history?limit=${limit}`, { headers: authHeaders() });
  if (!res.ok) {
    rejectIfUnauthorized(res);
    // graceful for stub/demo without rows or backend
    return [];
  }
  return res.json();
}

export async function enrichLead(input: LeadPushInput): Promise<any> {
  const res = await fetch(`${API_BASE}/leads/enrich`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Enrich failed: ${res.status}`);
  }
  return res.json();
}

export interface EnrichedPreview {
  company_snapshot: string;
  personalized_opener: string;
  follow_ups: Array<{
    title: string;
    description: string;
    due_in_days: number;
    rationale: string;
  }>;
  model_used?: string;
  mock?: boolean;
  memory_note?: string;
  authenticated_as?: string;
  [key: string]: any;
}

// Future: real JWT header etc. Current demo uses DEBUG fallback on backend.

// T012: Connections API (store/test CRM tokens)

export interface ConnectionResponse {
  id: string;
  provider: 'bitrix24' | 'hubspot';
  connected: boolean;
  auth_type: string;
  created_at?: string;
  last_validated_at?: string;
  masked_credential?: string;
}

export interface ConnectionListResponse {
  connections: ConnectionResponse[];
}

export async function connectBitrix24(webhookUrl: string): Promise<ConnectionResponse> {
  const res = await fetch(`${API_BASE}/connections/bitrix24`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify({ webhook_url: webhookUrl }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to connect Bitrix24: ${res.status}`);
  }
  return res.json();
}

export async function testBitrix24Connection(webhookUrl?: string): Promise<{ provider: string; connected: boolean; reason: string }> {
  const res = await fetch(`${API_BASE}/connections/bitrix24/test`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify(webhookUrl ? { webhook_url: webhookUrl } : {}),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to test Bitrix24 connection: ${res.status}`);
  }
  return res.json();
}

export async function connectHubSpot(accessToken: string): Promise<ConnectionResponse> {
  const res = await fetch(`${API_BASE}/connections/hubspot`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify({ access_token: accessToken }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to connect HubSpot: ${res.status}`);
  }
  return res.json();
}

export async function testHubSpotConnection(accessToken?: string): Promise<{ provider: string; connected: boolean; reason: string }> {
  const res = await fetch(`${API_BASE}/connections/hubspot/test`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify(accessToken ? { access_token: accessToken } : {}),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to test HubSpot connection: ${res.status}`);
  }
  return res.json();
}

export async function getConnections(): Promise<ConnectionListResponse> {
  const res = await fetch(`${API_BASE}/connections`, { headers: authHeaders() });
  if (!res.ok) {
    rejectIfUnauthorized(res);
    // Graceful for stub/demo
    return { connections: [] };
  }
  return res.json();
}

// T024: Memory Profile API

export interface ToneSampleRequest {
  opener: string;
  outcome?: string;
}

export interface MemoryProfileRequest {
  icp_industries?: string[];
  typical_cadence?: number[];
  tone_samples?: ToneSampleRequest[];
}

export interface MemoryProfileResponse {
  id: string;
  user_id: string;
  icp_industries?: string[];
  typical_cadence?: number[];
  tone_samples?: Array<{
    opener: string;
    outcome?: string;
    accepted_at?: string;
  }>;
  created_at?: string;
  updated_at?: string;
}

export async function getMemoryProfile(): Promise<MemoryProfileResponse> {
  const res = await fetch(`${API_BASE}/memory/profile`, { headers: authHeaders() });
  if (!res.ok) {
    rejectIfUnauthorized(res);
    // Graceful for stub/demo without backend
    return {
      id: '',
      user_id: '',
      icp_industries: [],
      typical_cadence: [4, 9, 14],
      tone_samples: [],
      created_at: undefined,
      updated_at: undefined,
    };
  }
  return res.json();
}

export async function saveMemoryProfile(profile: MemoryProfileRequest): Promise<MemoryProfileResponse> {
  const res = await fetch(`${API_BASE}/memory/profile`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify(profile),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to save memory profile: ${res.status}`);
  }
  return res.json();
}

// T025: Usage Ledger API (read-only; display cost + budget tracking)

export interface UsageSummaryResponse {
  total_calls: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_estimated_cost_cents: number;
  today_cost_cents: number;
  remaining_budget_cents: number;
  daily_budget_cents: number;
}

export interface UsageHistoryItem {
  id: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  estimated_cost_cents: number;
  created_at: string;
  lead_id?: string;
}

export interface UsageHistoryResponse {
  items: UsageHistoryItem[];
  total_count: number;
  limit: number;
}

export async function getUsageSummary(): Promise<UsageSummaryResponse> {
  const res = await fetch(`${API_BASE}/usage/summary`, { headers: authHeaders() });
  if (!res.ok) {
    rejectIfUnauthorized(res);
    // Graceful for stub/demo without backend
    return {
      total_calls: 0,
      total_input_tokens: 0,
      total_output_tokens: 0,
      total_estimated_cost_cents: 0,
      today_cost_cents: 0,
      remaining_budget_cents: 200, // default from backend config
      daily_budget_cents: 200,
    };
  }
  return res.json();
}

export async function getUsageHistory(limit = 50): Promise<UsageHistoryResponse> {
  const res = await fetch(`${API_BASE}/usage/history?limit=${limit}`, { headers: authHeaders() });
  if (!res.ok) {
    rejectIfUnauthorized(res);
    // Graceful for stub/demo without backend
    return {
      items: [],
      total_count: 0,
      limit,
    };
  }
  return res.json();
}
