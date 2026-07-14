/**
 * Auth API client for Google OAuth + JWT flow.
 * Handles token exchange, storage, and refresh.
 */

const API_BASE = import.meta.env.BASE_URL.endsWith('/') ? import.meta.env.BASE_URL.slice(0, -1) : import.meta.env.BASE_URL;

const TOKEN_KEY = 'bd_lead_jwt';
const USER_KEY = 'bd_lead_user';

export interface AuthUser {
  id: string;
  email: string;
  display_name: string;
  created_at?: string | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
}

function getBaseUrl(): string {
  return API_BASE || '';
}

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function getStoredUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function clearStoredAuth(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  } catch {
    // localStorage may be unavailable
  }
}

export function storeAuth(response: AuthResponse): void {
  try {
    localStorage.setItem(TOKEN_KEY, response.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(response.user));
  } catch {
    // localStorage may be unavailable
  }
}

export async function exchangeGoogleToken(idToken: string): Promise<AuthResponse> {
  const baseUrl = getBaseUrl();
  const url = `${baseUrl}/api/auth/google`;

  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id_token: idToken }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: 'Authentication failed' }));
    throw new Error(body.detail || `Auth failed (${res.status})`);
  }

  return res.json();
}

export async function fetchCurrentUser(token: string): Promise<AuthUser> {
  const baseUrl = getBaseUrl();
  const url = `${baseUrl}/api/auth/me`;

  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    throw new Error('Failed to fetch user info');
  }

  return res.json();
}
