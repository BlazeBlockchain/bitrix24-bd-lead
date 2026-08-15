/**
 * Popup script for BD Lead AI extension.
 * Thin launcher: opens the side panel, displays session state and API status.
 */

/**
 * DOM elements cache
 */
const DOM = {
  openPanelBtn: document.getElementById('openPanelBtn'),
  panelAvailable: document.getElementById('panelAvailable'),
  panelUnavailable: document.getElementById('panelUnavailable'),
  dashboardLink: document.getElementById('dashboardLink'),
  apiDot: document.getElementById('apiDot'),
  apiText: document.getElementById('apiText'),
  authDot: document.getElementById('authDot'),
  authText: document.getElementById('authText'),
  openOptions: document.getElementById('openOptions'),
  openWeb: document.getElementById('openWeb'),
  connectionsLink: document.getElementById('connectionsLink'),
  versionLabel: document.getElementById('versionLabel'),
};

/**
 * Open the side panel, with fallback to service worker message if gesture context fails.
 * CRITICAL: chrome.sidePanel.open() must be called during an active user gesture in the
 * extension page (popup) context. If called through a service worker message, the gesture
 * context may not survive the hop. So we try the direct call first, then fall back.
 */
async function openSidePanel() {
  try {
    const win = await chrome.windows.getCurrent();
    await chrome.sidePanel.open({ windowId: win.id });
    window.close();
  } catch (err) {
    // Fallback: send message to service worker
    try {
      await chrome.runtime.sendMessage({ type: 'OPEN_PANEL', windowId: (await chrome.windows.getCurrent()).id });
      window.close();
    } catch (fallbackErr) {
      console.error('[BD Lead AI] Failed to open panel:', fallbackErr);
    }
  }
}

/**
 * Feature-detect chrome.sidePanel.open availability.
 * Shows the panel button only if available; otherwise shows a message about Chrome version.
 */
function checkPanelSupport() {
  const isSupported = typeof chrome.sidePanel?.open === 'function';
  if (!isSupported) {
    DOM.panelAvailable.style.display = 'none';
    DOM.panelUnavailable.style.display = 'block';
    DOM.dashboardLink.href = WEB_BASE;
  }
}

/**
 * Update API status indicator
 */
async function checkApiStatus() {
  try {
    // GET, not HEAD: the backend route only allows GET, so HEAD returned 405 —
    // the dot never went green and every popup open logged a console error.
    const response = await fetch(`${API_BASE}/health`, {
      method: 'GET',
    });
    DOM.apiDot.classList.add(response.ok ? 'online' : 'offline');
    DOM.apiText.textContent = response.ok ? 'API reachable' : 'API unreachable';
  } catch (error) {
    DOM.apiDot.classList.add('offline');
    DOM.apiText.textContent = 'API unreachable';
  }
}

/**
 * Update authentication status display
 */
async function updateAuthStatus() {
  try {
    const session = await BDAuth.getSession();
    if (session.state === 'valid' && session.user) {
      DOM.authDot.classList.add('online');
      DOM.authText.textContent = `Signed in as ${session.user.email}`;
    } else if (session.state === 'expired') {
      DOM.authDot.classList.add('offline');
      DOM.authText.textContent = 'Session expired';
    } else {
      DOM.authDot.classList.add('offline');
      DOM.authText.textContent = 'Not signed in';
    }
  } catch (error) {
    DOM.authDot.classList.add('offline');
    DOM.authText.textContent = 'Not signed in';
  }
}

/**
 * Initialize popup
 */
function init() {
  // Check if side panel is supported
  checkPanelSupport();

  // Read the version from the manifest rather than hardcoding it in the HTML.
  // The manifest version is generated from the root VERSION file by
  // scripts/sync_versions.py, so reading it here keeps this label correct
  // through every `make bump-*` with nothing to hand-edit.
  DOM.versionLabel.textContent = `v${chrome.runtime.getManifest().version}`;

  // Set up event listeners
  DOM.openPanelBtn.addEventListener('click', openSidePanel);

  // Open options page
  DOM.openOptions.addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
  });

  // Open web dashboard
  DOM.openWeb.addEventListener('click', () => {
    chrome.tabs.create({ url: WEB_BASE });
  });

  // Open connections page
  DOM.connectionsLink.addEventListener('click', (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: `${WEB_BASE}/connections` });
  });

  // Load status
  checkApiStatus();
  updateAuthStatus();
}

/**
 * Start when DOM is ready
 */
document.addEventListener('DOMContentLoaded', init);
