/**
 * Options page script for BD Lead AI extension.
 * Manages authentication, CRM settings, and links to web dashboard.
 */

// DOM elements
const DOM = {
  authStatus: document.getElementById('authStatus'),
  authText: document.getElementById('authText'),
  tokenDisplay: document.getElementById('tokenDisplay'),
  viewTokenBtn: document.getElementById('viewTokenBtn'),
  signOutBtn: document.getElementById('signOutBtn'),
  authMsg: document.getElementById('authMsg'),
  tokenInput: document.getElementById('tokenInput'),
  saveTokenBtn: document.getElementById('saveTokenBtn'),
  defaultProvider: document.getElementById('defaultProvider'),
  providerMsg: document.getElementById('providerMsg'),
  openConnectionsBtn: document.getElementById('openConnectionsBtn'),
  openDashboardBtn: document.getElementById('openDashboardBtn'),
  openHistoryBtn: document.getElementById('openHistoryBtn'),
  clearDataBtn: document.getElementById('clearDataBtn'),
  clearMsg: document.getElementById('clearMsg'),
  apiBaseDisplay: document.getElementById('apiBaseDisplay'),
};

let tokenVisible = false;

/**
 * Show a status message
 */
function showMsg(elementId, message, type = 'success') {
  const element = document.getElementById(elementId);
  element.textContent = message;
  element.className = `status-msg ${type}`;
  element.classList.remove('hidden');

  setTimeout(() => {
    element.classList.add('hidden');
  }, 3000);
}

/**
 * Load and display authentication status
 */
async function loadAuthStatus() {
  const data = await chrome.storage.local.get([STORAGE_KEYS.JWT]);
  const jwt = data[STORAGE_KEYS.JWT];

  if (jwt) {
    DOM.authStatus.className = 'auth-status authenticated';
    DOM.authText.textContent = '✓ Authenticated';
    DOM.viewTokenBtn.style.display = 'inline-block';
    DOM.signOutBtn.style.display = 'inline-block';

    // Try to parse JWT and show user info (basic)
    try {
      const parts = jwt.split('.');
      if (parts.length === 3) {
        const payload = JSON.parse(atob(parts[1]));
        if (payload.sub) {
          DOM.authText.textContent = `✓ Authenticated as ${payload.sub.split('@')[0] || 'user'}`;
        }
      }
    } catch (e) {
      // Ignore parsing errors
    }
  } else {
    DOM.authStatus.className = 'auth-status unauthenticated';
    DOM.authText.textContent = '✗ Not authenticated. Sign in via web dashboard.';
    DOM.viewTokenBtn.style.display = 'none';
    DOM.signOutBtn.style.display = 'none';
  }
}

/**
 * Toggle token visibility
 */
async function toggleTokenVisibility() {
  const data = await chrome.storage.local.get([STORAGE_KEYS.JWT]);
  const jwt = data[STORAGE_KEYS.JWT];

  if (!jwt) {
    showMsg('authMsg', 'No token stored', 'error');
    return;
  }

  tokenVisible = !tokenVisible;

  if (tokenVisible) {
    DOM.tokenDisplay.textContent = jwt;
    DOM.tokenDisplay.classList.remove('hidden');
    DOM.viewTokenBtn.textContent = 'Hide Token';
  } else {
    DOM.tokenDisplay.classList.add('hidden');
    DOM.viewTokenBtn.textContent = 'View JWT Token';
  }
}

/**
 * Sign out and clear token
 */
async function signOut() {
  if (confirm('Clear your authentication token? You will need to sign in again.')) {
    await chrome.storage.local.remove([STORAGE_KEYS.JWT]);
    tokenVisible = false;
    DOM.tokenDisplay.classList.add('hidden');
    DOM.viewTokenBtn.textContent = 'View JWT Token';
    loadAuthStatus();
    showMsg('authMsg', 'Signed out. Please authenticate via the web dashboard.', 'success');
  }
}

/**
 * Save a manually-pasted JWT/demo token (T017: "stored JWT or token").
 * There is no real sign-in flow yet (T005 OAuth is still a stub across the
 * whole project), so this is the only way to populate STORAGE_KEYS.JWT today.
 */
async function saveToken() {
  const value = DOM.tokenInput.value.trim();
  if (!value) {
    showMsg('authMsg', 'Enter a token first', 'error');
    return;
  }
  await chrome.storage.local.set({ [STORAGE_KEYS.JWT]: value });
  DOM.tokenInput.value = '';
  await loadAuthStatus();
  showMsg('authMsg', 'Token saved', 'success');
}

/**
 * Load stored provider preference
 */
async function loadProvider() {
  const data = await chrome.storage.local.get([STORAGE_KEYS.PROVIDER]);
  if (data[STORAGE_KEYS.PROVIDER]) {
    DOM.defaultProvider.value = data[STORAGE_KEYS.PROVIDER];
  }
}

/**
 * Save provider preference
 */
async function saveProvider() {
  const provider = DOM.defaultProvider.value;
  await chrome.storage.local.set({
    [STORAGE_KEYS.PROVIDER]: provider,
  });
  showMsg('providerMsg', `Default CRM set to ${provider}`, 'success');
}

/**
 * Open web app links
 */
function openConnections() {
  const url = `${WEB_BASE}/connections`;
  chrome.tabs.create({ url });
  window.close();
}

function openDashboard() {
  chrome.tabs.create({ url: WEB_BASE });
  window.close();
}

function openHistory() {
  const url = `${WEB_BASE}/history`;
  chrome.tabs.create({ url });
  window.close();
}

/**
 * Clear all stored data
 */
async function clearAllData() {
  if (confirm('Clear all stored data? This includes your token, settings, and preferences. This action cannot be undone.')) {
    await chrome.storage.local.clear();
    tokenVisible = false;
    DOM.tokenDisplay.classList.add('hidden');
    DOM.viewTokenBtn.textContent = 'View JWT Token';
    loadAuthStatus();
    DOM.defaultProvider.value = DEFAULT_PROVIDER;
    showMsg('clearMsg', 'All data cleared', 'success');
  }
}

/**
 * Initialize the options page
 */
async function init() {
  // Load initial state
  await loadAuthStatus();
  await loadProvider();

  // Update API base display
  DOM.apiBaseDisplay.textContent = `API: ${API_BASE}`;

  // Set up event listeners
  DOM.viewTokenBtn.addEventListener('click', toggleTokenVisibility);
  DOM.signOutBtn.addEventListener('click', signOut);
  DOM.saveTokenBtn.addEventListener('click', saveToken);
  DOM.defaultProvider.addEventListener('change', saveProvider);
  DOM.openConnectionsBtn.addEventListener('click', openConnections);
  DOM.openDashboardBtn.addEventListener('click', openDashboard);
  DOM.openHistoryBtn.addEventListener('click', openHistory);
  DOM.clearDataBtn.addEventListener('click', clearAllData);
}

// Start when page loads
document.addEventListener('DOMContentLoaded', init);
