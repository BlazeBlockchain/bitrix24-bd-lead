/**
 * Background service worker for BD Lead AI extension (MV3).
 * Minimal implementation for lifecycle logging.
 * Future: can add message passing, alarms, or other background tasks.
 */

// Log extension lifecycle events
console.log('[BD Lead AI] Service worker installing...');

// Extension installed
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('[BD Lead AI] Extension installed');
    // Could open onboarding page here
  } else if (details.reason === 'update') {
    console.log('[BD Lead AI] Extension updated');
  }
});

// Service worker activated
chrome.runtime.onStartup.addListener(() => {
  console.log('[BD Lead AI] Service worker started');
});

// Listen for messages from popup/options (future use)
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('[BD Lead AI] Message received:', message);
  // Future: handle background tasks, sync, etc.
  sendResponse({ status: 'received' });
});

console.log('[BD Lead AI] Service worker ready');
