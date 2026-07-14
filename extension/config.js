/**
 * Extension configuration for API and web app URLs.
 * Mirror .env.example conventions: API_BASE and WEB_BASE.
 * Customize these for dev/prod environments.
 */

// Backend API base URL — matches backend/.env API_BASE
const API_BASE = 'http://localhost:8000/api';

// Web app dashboard base URL — for options page links
const WEB_BASE = 'http://localhost:5173';

// Storage keys (consistent across popup/options/background)
const STORAGE_KEYS = {
  JWT: 'bd_jwt',
  PROVIDER: 'bd_provider',
  DEMO_TOKEN: 'bd_demo_token',
};

// Default CRM provider
const DEFAULT_PROVIDER = 'bitrix24';

// Export as module for popup/options
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { API_BASE, WEB_BASE, STORAGE_KEYS, DEFAULT_PROVIDER };
}
