/**
 * Popup script for BD Lead AI extension.
 * Handles form submission, API calls to /enrich and /push, and preview rendering.
 * Uses chrome.storage.local for JWT token and settings.
 */

// Import config (populated by config.js in manifest)
// API_BASE, WEB_BASE, STORAGE_KEYS, DEFAULT_PROVIDER come from global scope after config.js loads

const DOM = {
  form: document.getElementById('leadForm'),
  generateBtn: document.getElementById('generateBtn'),
  pushBtn: document.getElementById('pushBtn'),
  status: document.getElementById('status'),
  preview: document.getElementById('preview'),
  previewContent: document.getElementById('previewContent'),
  provider: document.getElementById('provider'),
  company: document.getElementById('company_name'),
  contact: document.getElementById('contact_name'),
  role: document.getElementById('contact_role'),
  signal: document.getElementById('signal'),
  painPoint: document.getElementById('pain_point'),
  notes: document.getElementById('notes'),
  openOptions: document.getElementById('openOptions'),
  openWeb: document.getElementById('openWeb'),
  apiStatus: document.getElementById('apiStatus'),
};

let enrichedData = null;

/**
 * Show a status message (loading, success, error)
 */
function showStatus(message, type = 'loading') {
  DOM.status.textContent = message;
  DOM.status.className = `status ${type}`;
  DOM.status.classList.remove('hidden');
}

function clearStatus() {
  DOM.status.classList.add('hidden');
}

/**
 * Get the stored JWT token for Authorization header
 */
async function getAuthToken() {
  const data = await chrome.storage.local.get([STORAGE_KEYS.JWT]);
  return data[STORAGE_KEYS.JWT] || null;
}

/**
 * Build the lead input from form data (matches LeadPushInput shape from web/src/api/client.ts)
 */
function buildLeadInput() {
  return {
    company_name: DOM.company.value || 'Acme Corp',
    deal_name: `${DOM.company.value || 'Acme'} Intro Deal`,
    contact_name: DOM.contact.value || 'Jane Doe',
    contact_role: DOM.role.value || 'Head of Growth',
    signal: DOM.signal.value || undefined,
    signal_type: 'new_launch',
    pain_point: DOM.painPoint.value || undefined,
    email_subject: `Intro to ${DOM.company.value || 'Acme'}`,
    notes: DOM.notes.value || undefined,
  };
}

/**
 * Render the enriched preview (company_snapshot, personalized_opener, 3 follow_ups)
 * Matches Preview.tsx component output structure.
 */
function renderPreview(enriched) {
  if (!enriched || !enriched.company_snapshot) {
    DOM.previewContent.innerHTML = '<p style="color: var(--muted);">Failed to render preview</p>';
    return;
  }

  const snapshot = enriched.company_snapshot || 'No snapshot';
  const opener = enriched.personalized_opener || 'No opener';
  const followUps = enriched.follow_ups || [];

  let html = `
    <div class="preview-section">
      <strong>Company Snapshot</strong>
      <p>${escapeHtml(snapshot)}</p>
    </div>

    <div class="preview-section">
      <strong>Suggested Opener</strong>
      <div style="background: var(--bg); padding: 8px; border-radius: var(--radius); margin-top: 4px; font-style: italic; font-size: 11px; line-height: 1.4;">
        ${escapeHtml(opener)}
      </div>
    </div>

    <div class="preview-section">
      <strong>Follow-up Plan (3 tasks)</strong>
  `;

  if (followUps.length > 0) {
    followUps.slice(0, 3).forEach((task, idx) => {
      const dueDays = task.due_in_days || 0;
      html += `
        <div class="task-item">
          <strong>${escapeHtml(task.title)}</strong>
          <span class="task-due">(+${dueDays} days)</span>
          ${task.description ? `<div>${escapeHtml(task.description)}</div>` : ''}
          <div class="task-rationale">${escapeHtml(task.rationale || 'No rationale')}</div>
        </div>
      `;
    });
  }

  html += `
    <div style="margin-top: 8px; font-size: 10px; color: var(--muted);">
      ${enriched.model_used ? `Model: ${escapeHtml(enriched.model_used)}` : ''}
      ${enriched.memory_note ? ` · Memory: ${escapeHtml(enriched.memory_note)}` : ''}
    </div>
  `;

  DOM.previewContent.innerHTML = html;
  DOM.preview.classList.add('active');
  DOM.pushBtn.disabled = false;
}

/**
 * Call /api/leads/enrich with the lead input
 */
async function handleGenerate() {
  clearStatus();
  showStatus('Generating AI preview...', 'loading');

  try {
    // Token is optional: backend falls back to a DEBUG stub user when no
    // Authorization header is sent (same as the web app today). If a token
    // IS stored (set via the options page), attach it so real auth works
    // once T005 OAuth is wired up end-to-end.
    const token = await getAuthToken();
    const input = buildLeadInput();

    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE}/leads/enrich`, {
      method: 'POST',
      headers,
      body: JSON.stringify(input),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `Enrich failed: ${response.status}`);
    }

    enrichedData = await response.json();
    renderPreview(enrichedData);
    showStatus('✓ Preview generated successfully', 'success');
  } catch (error) {
    showStatus(`Error: ${error.message}`, 'error');
    DOM.pushBtn.disabled = true;
  }
}

/**
 * Call /api/leads/push to create contact, deal, and tasks in CRM
 */
async function handlePush() {
  if (!enrichedData || !enrichedData.company_snapshot) {
    showStatus('Please generate a preview first', 'error');
    return;
  }

  clearStatus();
  showStatus('Pushing to CRM...', 'loading');
  DOM.pushBtn.disabled = true;

  try {
    // Token optional, same rationale as handleGenerate (DEBUG stub fallback server-side).
    const token = await getAuthToken();
    const provider = DOM.provider.value || DEFAULT_PROVIDER;
    const input = buildLeadInput();

    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE}/leads/push?provider=${encodeURIComponent(provider)}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(input),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `Push failed: ${response.status}`);
    }

    const result = await response.json();
    showStatus(`✓ Pushed successfully! Contact: ${result.contact_id}, Deal: ${result.deal_id}`, 'success');

    // Reset form
    setTimeout(() => {
      DOM.form.reset();
      DOM.preview.classList.remove('active');
      enrichedData = null;
      DOM.pushBtn.disabled = true;
      clearStatus();
    }, 2000);
  } catch (error) {
    showStatus(`Push error: ${error.message}`, 'error');
    DOM.pushBtn.disabled = false;
  }
}

/**
 * Utility to escape HTML special chars
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Load stored provider from chrome.storage
 */
async function loadStoredSettings() {
  const data = await chrome.storage.local.get([STORAGE_KEYS.PROVIDER]);
  if (data[STORAGE_KEYS.PROVIDER]) {
    DOM.provider.value = data[STORAGE_KEYS.PROVIDER];
  } else {
    DOM.provider.value = DEFAULT_PROVIDER;
  }
}

/**
 * Save provider preference to chrome.storage
 */
async function saveProvider() {
  await chrome.storage.local.set({
    [STORAGE_KEYS.PROVIDER]: DOM.provider.value,
  });
}

/**
 * Initialize event listeners
 */
function init() {
  DOM.generateBtn.addEventListener('click', handleGenerate);
  DOM.pushBtn.addEventListener('click', handlePush);

  DOM.provider.addEventListener('change', saveProvider);

  // Open options page
  DOM.openOptions.addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
  });

  // Open web dashboard
  DOM.openWeb.addEventListener('click', () => {
    chrome.tabs.create({ url: WEB_BASE });
  });

  // Load stored settings
  loadStoredSettings();

  // Check API connectivity (best effort)
  checkApiStatus();
}

/**
 * Check if API is reachable
 */
async function checkApiStatus() {
  try {
    const response = await fetch(`${API_BASE}/health`, {
      method: 'HEAD',
    });
    DOM.apiStatus.textContent = response.ok ? '✓ API' : '⚠ API';
  } catch (error) {
    DOM.apiStatus.textContent = '✗ API';
  }
}

/**
 * Start the popup when DOM is ready
 */
document.addEventListener('DOMContentLoaded', init);
