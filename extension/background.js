/**
 * Background service worker for BD Lead AI extension (MV3).
 * Handles side panel registration, lifecycle, and messaging.
 * CRITICAL: Never log full message payloads or token values (NFR-006).
 */

console.log('[BD Lead AI] Service worker installing...');

/**
 * Check if chrome.sidePanel API is available.
 */
function isPanelAvailable() {
  return typeof chrome.sidePanel?.open === 'function';
}

/**
 * Open the side panel for the given window.
 */
function openPanel(windowId) {
  if (!isPanelAvailable()) {
    console.warn(
      '[BD Lead AI] chrome.sidePanel.open is not available. Requires Chrome 116+'
    );
    return;
  }
  chrome.sidePanel.open({ windowId });
}

// Extension installed or updated.
// The context menu must be (re)created on BOTH 'install' and 'update': an update clears
// previously registered menu items, so creating it only on 'install' would silently lose
// the menu entry for every existing user after the next version bump.
chrome.runtime.onInstalled.addListener((details) => {
  console.log(`[BD Lead AI] onInstalled: ${details.reason}`);

  // Register the panel. The manifest's side_panel.default_path already covers the
  // common case; this makes the enabled state explicit and survives reloads.
  if (isPanelAvailable()) {
    chrome.sidePanel.setOptions({ path: 'sidepanel.html', enabled: true });
  }

  // removeAll() first so an update doesn't hit "duplicate id" errors.
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: 'open-bd-lead-panel',
      title: 'Open BD Lead panel',
      contexts: ['all'],
    });
  });
});

// Context menu click handler.
// `tab` is optional in the contextMenus API, so fall back to the current window
// rather than throwing on tab.windowId.
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId !== 'open-bd-lead-panel') return;
  if (tab && tab.windowId !== undefined) {
    openPanel(tab.windowId);
  } else {
    chrome.windows.getCurrent({}, (win) => openPanel(win.id));
  }
});

// Keyboard shortcut handler
chrome.commands.onCommand.addListener((command) => {
  if (command === 'open-side-panel') {
    // Get the current window and open the panel
    chrome.windows.getCurrent({}, (window) => {
      openPanel(window.id);
    });
  }
});

// Service worker activated
chrome.runtime.onStartup.addListener(() => {
  console.log('[BD Lead AI] Service worker started');
});

/**
 * Listen for messages from popup/options.
 * Handles only OPEN_PANEL messages; ignores everything else.
 * Logs only the message type, never the payload (NFR-006).
 *
 * NOTE: this is a FALLBACK path, not the primary one. chrome.sidePanel.open() must be
 * called while a user gesture is still active, and the gesture context does NOT reliably
 * survive a chrome.runtime.sendMessage hop into the service worker — routing the click
 * through here can fail with "sidePanel.open() may only be called in response to a user
 * gesture". The popup therefore calls chrome.sidePanel.open() DIRECTLY in its own page
 * context (extension pages may call it), and only falls back to this message if that
 * throws. Keep both paths.
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message && message.type === 'OPEN_PANEL') {
    console.log('[BD Lead AI] Message received: OPEN_PANEL');
    openPanel(message.windowId);
    sendResponse({ status: 'ok' });
  }
  // Silently ignore all other messages
});

console.log('[BD Lead AI] Service worker ready');
