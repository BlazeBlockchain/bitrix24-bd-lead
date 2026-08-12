/**
 * BDAuth: Google OAuth sign-in and session management.
 * Reuses the web app's Google client ID and exchanges ID tokens via POST /api/auth/google.
 * Stores JWT, user info, and expiry in chrome.storage.local.
 * CRITICAL: Never logs token values, id_tokens, or Authorization headers (NFR-006).
 */

/**
 * Decode a JWT payload (the middle segment, base64url-encoded).
 * Returns the parsed JSON object, or throws on malformed input.
 */
function decodeJwtPayload(token) {
  const parts = token.split('.');
  if (parts.length !== 3) {
    throw new Error('Invalid JWT format');
  }
  // JWT segments are base64URL, not plain base64: '-' and '_' must be
  // translated back to '+' and '/' before atob() can decode them.
  const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
  const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4);
  const decoded = atob(padded);
  return JSON.parse(decoded);
}

/**
 * Classify network errors and HTTP errors into the categories FR-014 requires.
 * Named distinctly from lead-api.js's classifyError: both files load together
 * on sidepanel.html/options.html, and classic-script `function` declarations
 * silently overwrite same-named globals across scripts (no SyntaxError, just
 * the last one wins) — colliding names here would have made auth.js's 501
 * ('setup') classification vanish whenever lead-api.js loaded after it.
 */
function classifyAuthError(fetchError, httpStatus, serverDetail) {
  if (fetchError) {
    return { class: 'unreachable', message: "Can't reach the BD Lead service" };
  }
  if (httpStatus === 401) {
    return { class: 'session', message: 'Signed out or session expired' };
  }
  if (httpStatus === 422) {
    return { class: 'input', message: serverDetail || 'Invalid request' };
  }
  if (httpStatus === 501) {
    return {
      class: 'setup',
      message: 'Google OAuth not configured on the server. Visit the options page to set up.',
    };
  }
  return {
    class: 'service',
    message: serverDetail || `Server error (${httpStatus})`,
  };
}

/**
 * Global BDAuth object exposing sign-in, sign-out, and session queries.
 */
const BDAuth = {
  /**
   * Get the stored Google client ID from chrome.storage, or the default.
   */
  async getClientId() {
    const data = await chrome.storage.local.get([STORAGE_KEYS.GOOGLE_CLIENT_ID]);
    return data[STORAGE_KEYS.GOOGLE_CLIENT_ID] || DEFAULT_GOOGLE_CLIENT_ID;
  },

  /**
   * Sign in via Google OAuth and exchange the ID token for a JWT.
   * Verifies the nonce round-tripped, posts to /api/auth/google, stores the session.
   * Rejects with a classified error if setup is incomplete or auth fails.
   */
  async signIn() {
    const clientId = await BDAuth.getClientId();
    if (!clientId) {
      const err = new Error(
        'Google OAuth not configured. Visit the options page to set up.'
      );
      err.class = 'setup';
      throw err;
    }

    const nonce = crypto.randomUUID();
    const redirectUri = chrome.identity.getRedirectURL();

    const params = new URLSearchParams({
      client_id: clientId,
      response_type: 'id_token',
      scope: OAUTH_SCOPES,
      nonce: nonce,
      redirect_uri: redirectUri,
    });

    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?${params}`;

    let responseUrl;
    try {
      responseUrl = await chrome.identity.launchWebAuthFlow({
        url: authUrl,
        interactive: true,
      });
    } catch (err) {
      // User cancelled or browser-level error
      const classError = new Error(err.message || 'Google sign-in cancelled');
      classError.class = 'session';
      throw classError;
    }

    // Parse the fragment (not query string)
    const fragmentStart = responseUrl.indexOf('#');
    if (fragmentStart === -1) {
      const err = new Error('Malformed OAuth response (no fragment)');
      err.class = 'service';
      throw err;
    }

    const fragment = responseUrl.substring(fragmentStart + 1);
    const fragParams = new URLSearchParams(fragment);
    const idToken = fragParams.get('id_token');

    if (!idToken) {
      const err = new Error('No ID token in OAuth response');
      err.class = 'service';
      throw err;
    }

    // Verify nonce round-tripped
    let payload;
    try {
      payload = decodeJwtPayload(idToken);
    } catch (err) {
      const classError = new Error('Failed to decode ID token');
      classError.class = 'service';
      throw classError;
    }

    if (payload.nonce !== nonce) {
      const err = new Error('Nonce mismatch (possible replay attack)');
      err.class = 'service';
      throw err;
    }

    // Exchange the ID token for a JWT at the backend
    let session;
    try {
      const response = await fetch(`${API_BASE}/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id_token: idToken }),
      });

      if (!response.ok) {
        const serverError = await response.json().catch(() => ({}));
        const classified = classifyAuthError(
          false,
          response.status,
          serverError.detail
        );
        const err = new Error(classified.message);
        err.class = classified.class;
        throw err;
      }

      session = await response.json();
    } catch (err) {
      // If it was already classified, rethrow as-is
      if (err.class) {
        throw err;
      }
      // Network error
      const classError = new Error(
        err.message || "Can't reach the BD Lead service"
      );
      classError.class = 'unreachable';
      throw classError;
    }

    // Store the session
    const expiresAt = Date.now() + session.expires_in * 1000;
    await chrome.storage.local.set({
      [STORAGE_KEYS.JWT]: session.access_token,
      [STORAGE_KEYS.USER]: session.user,
      [STORAGE_KEYS.JWT_EXPIRES_AT]: expiresAt,
    });

    return { state: 'valid', user: session.user };
  },

  /**
   * Sign out by clearing JWT, USER, and JWT_EXPIRES_AT.
   * Never clears PROVIDER or GOOGLE_CLIENT_ID (those are UI preferences, not credentials).
   */
  async signOut() {
    await chrome.storage.local.remove([
      STORAGE_KEYS.JWT,
      STORAGE_KEYS.USER,
      STORAGE_KEYS.JWT_EXPIRES_AT,
    ]);
  },

  /**
   * Get the current session state without a network call.
   * Returns { state: 'absent' | 'expired' | 'valid', user: {...} | undefined }.
   */
  async getSession() {
    const data = await chrome.storage.local.get([
      STORAGE_KEYS.JWT,
      STORAGE_KEYS.USER,
      STORAGE_KEYS.JWT_EXPIRES_AT,
    ]);

    const token = data[STORAGE_KEYS.JWT];
    const user = data[STORAGE_KEYS.USER];
    const expiresAt = data[STORAGE_KEYS.JWT_EXPIRES_AT];

    if (!token) {
      return { state: 'absent', user: undefined };
    }

    if (expiresAt && Date.now() > expiresAt) {
      return { state: 'expired', user: undefined };
    }

    return { state: 'valid', user };
  },

  /**
   * Validate the stored session with the backend (GET /api/auth/me).
   * Returns { state, user }; on 401, clears the session and returns expired state.
   * Caller should assume 'expired' means "prompt sign-in".
   */
  async validate() {
    const session = await BDAuth.getSession();
    if (session.state !== 'valid') {
      return session;
    }

    const token = (
      await chrome.storage.local.get([STORAGE_KEYS.JWT])
    )[STORAGE_KEYS.JWT];

    try {
      const response = await fetch(`${API_BASE}/auth/me`, {
        method: 'GET',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.status === 401) {
        // Session expired server-side; clear it locally
        await BDAuth.signOut();
        return { state: 'expired', user: undefined };
      }

      if (!response.ok) {
        // Other errors: return current state (don't clear)
        return session;
      }

      return { state: 'valid', user: session.user };
    } catch (err) {
      // Network error: return current state
      return session;
    }
  },

  /**
   * Get an Authorization header for API calls.
   * Throws a 'session'-classed error if no valid session exists.
   * Callers use this to guard every API call, ensuring unauthenticated requests never reach the backend.
   */
  async authHeaders() {
    const session = await BDAuth.getSession();
    if (session.state !== 'valid') {
      const err = new Error(
        'Signed out or session expired. Please sign in.'
      );
      err.class = 'session';
      throw err;
    }

    const token = (
      await chrome.storage.local.get([STORAGE_KEYS.JWT])
    )[STORAGE_KEYS.JWT];

    return { Authorization: `Bearer ${token}` };
  },
};
