/**
 * Options page script for BD Lead AI extension.
 * Manages Google OAuth sign-in, client ID configuration, CRM settings, and links.
 */

/**
 * DOM elements cache
 */
const DOM = {
  authStatus: document.getElementById('authStatus'),
  authText: document.getElementById('authText'),
  versionLabel: document.getElementById('versionLabel'),
  signInBtn: document.getElementById('signInBtn'),
  signOutBtn: document.getElementById('signOutBtn'),
  authMsg: document.getElementById('authMsg'),
  googleClientId: document.getElementById('googleClientId'),
  clientIdMsg: document.getElementById('clientIdMsg'),
  redirectUri: document.getElementById('redirectUri'),
  copyRedirectBtn: document.getElementById('copyRedirectBtn'),
  defaultProvider: document.getElementById('defaultProvider'),
  providerMsg: document.getElementById('providerMsg'),
  openConnectionsBtn: document.getElementById('openConnectionsBtn'),
  openDashboardBtn: document.getElementById('openDashboardBtn'),
  openHistoryBtn: document.getElementById('openHistoryBtn'),
  clearDataBtn: document.getElementById('clearDataBtn'),
  clearMsg: document.getElementById('clearMsg'),
  apiBaseDisplay: document.getElementById('apiBaseDisplay'),
};

/**
 * Show a status message with auto-hide
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
  const session = await BDAuth.getSession();

  if (session.state === 'valid' && session.user) {
    DOM.authStatus.className = 'auth-status authenticated';
    DOM.authText.textContent = `✓ Signed in as ${session.user.email}`;
    DOM.signInBtn.classList.add('hidden');
    DOM.signOutBtn.classList.remove('hidden');
  } else {
    DOM.authStatus.className = 'auth-status unauthenticated';
    DOM.authText.textContent = '✗ Not signed in';
    DOM.signInBtn.classList.remove('hidden');
    DOM.signOutBtn.classList.add('hidden');
  }
}

/**
 * Handle sign-in with Google
 */
async function handleSignIn() {
  DOM.signInBtn.disabled = true;
  try {
    await BDAuth.signIn();
    await loadAuthStatus();
    showMsg('authMsg', 'Signed in successfully', 'success');
  } catch (err) {
    let message = err.message || 'Sign-in failed';
    if (err.class === 'setup') {
      message = 'Google OAuth not configured. Please set your Client ID first.';
    }
    showMsg('authMsg', message, 'error');
  } finally {
    DOM.signInBtn.disabled = false;
  }
}

/**
 * Handle sign-out
 */
async function handleSignOut() {
  if (confirm('Sign out? You will need to sign in again to use the extension.')) {
    await BDAuth.signOut();
    await loadAuthStatus();
    showMsg('authMsg', 'Signed out successfully', 'success');
  }
}

/**
 * Load Google Client ID from storage
 */
async function loadGoogleClientId() {
  const data = await chrome.storage.local.get([STORAGE_KEYS.GOOGLE_CLIENT_ID]);
  const clientId = data[STORAGE_KEYS.GOOGLE_CLIENT_ID] || '';
  DOM.googleClientId.value = clientId;
}

/**
 * Save Google Client ID to storage
 */
async function saveGoogleClientId() {
  const clientId = DOM.googleClientId.value.trim();
  await chrome.storage.local.set({
    [STORAGE_KEYS.GOOGLE_CLIENT_ID]: clientId,
  });
  showMsg('clientIdMsg', clientId ? 'Client ID saved' : 'Client ID cleared', 'success');
}

/**
 * Display the extension's redirect URI and set up copy button
 */
async function setupRedirectUri() {
  const redirectUri = chrome.identity.getRedirectURL();
  DOM.redirectUri.textContent = redirectUri;

  DOM.copyRedirectBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(redirectUri).then(() => {
      showMsg('clientIdMsg', 'Redirect URI copied to clipboard', 'success');
    }).catch(() => {
      showMsg('clientIdMsg', 'Failed to copy redirect URI', 'error');
    });
  });
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
  if (confirm(
    'Clear all stored data? This will remove your authentication token, CRM preferences, and Google Client ID configuration. ' +
    'You will need to sign in and reconfigure everything. This action cannot be undone.'
  )) {
    await chrome.storage.local.clear();
    await loadAuthStatus();
    DOM.defaultProvider.value = DEFAULT_PROVIDER;
    DOM.googleClientId.value = '';
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
  await loadGoogleClientId();
  await setupRedirectUri();

  // Update API base display
  DOM.apiBaseDisplay.textContent = `API: ${API_BASE}`;

  // Version comes from the manifest (generated from the root VERSION file by
  // scripts/sync_versions.py), so it never needs hand-editing and cannot go stale.
  DOM.versionLabel.textContent = `BD Lead AI v${chrome.runtime.getManifest().version}`;

  // Set up event listeners
  DOM.signInBtn.addEventListener('click', handleSignIn);
  DOM.signOutBtn.addEventListener('click', handleSignOut);
  DOM.googleClientId.addEventListener('change', saveGoogleClientId);
  DOM.defaultProvider.addEventListener('change', saveProvider);
  DOM.openConnectionsBtn.addEventListener('click', openConnections);
  DOM.openDashboardBtn.addEventListener('click', openDashboard);
  DOM.openHistoryBtn.addEventListener('click', openHistory);
  DOM.clearDataBtn.addEventListener('click', clearAllData);
}

/**
 * Start when DOM is ready
 */
document.addEventListener('DOMContentLoaded', init);
