/**
 * Extension configuration for API and web app URLs.
 * Mirror .env.example conventions: API_BASE and WEB_BASE.
 * Customize these for dev/prod environments.
 */

// Backend API base URL — matches backend/.env API_BASE
const API_BASE = 'http://localhost:8000/api';

// Web app dashboard base URL — for options page links
const WEB_BASE = 'http://localhost:8080';

/**
 * Google OAuth client ID for the extension's sign-in flow.
 * Ships EMPTY on purpose: config.js is tracked by git, while web/.env (which holds
 * the real client ID) is gitignored. To avoid committing a value the repo deliberately
 * keeps untracked and leaving every developer with a dirty working tree, the real value
 * is configured once on the options page and stored in chrome.storage.local[bd_google_client_id].
 * BDAuth.getClientId() retrieves this stored value, falling back to DEFAULT_GOOGLE_CLIENT_ID.
 * When it resolves empty, signIn() rejects with a 'setup'-classed error pointing at the options page.
 */
const DEFAULT_GOOGLE_CLIENT_ID = '';

/** OAuth 2.0 scopes for the Google ID token exchange. */
const OAUTH_SCOPES = 'openid email profile';

/** Minimum Chrome version supporting chrome.sidePanel.open() */
const MIN_CHROME_FOR_PANEL = 116;

// Storage keys (consistent across popup/options/background)
const STORAGE_KEYS = {
  JWT: 'bd_jwt',
  PROVIDER: 'bd_provider',
  DEMO_TOKEN: 'bd_demo_token',
  USER: 'bd_user',
  JWT_EXPIRES_AT: 'bd_jwt_exp',
  DRAFT: 'bd_draft',
  GOOGLE_CLIENT_ID: 'bd_google_client_id',
};

// Default CRM provider
const DEFAULT_PROVIDER = 'bitrix24';

// Export as module for popup/options
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    API_BASE,
    WEB_BASE,
    DEFAULT_GOOGLE_CLIENT_ID,
    OAUTH_SCOPES,
    MIN_CHROME_FOR_PANEL,
    STORAGE_KEYS,
    DEFAULT_PROVIDER,
  };
}
