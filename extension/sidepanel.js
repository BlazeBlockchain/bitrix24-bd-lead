/**
 * Side Panel Workspace Controller
 * Manages lead drafts, preview rendering, auth UI, page capture, and form persistence.
 * Implements T060-T066 (all Wave C tasks).
 */

/**
 * Panel state and lifecycle.
 * - formDraft: current form values, persisted to chrome.storage.session
 * - currentEnrichment: generated preview, invalidated when form changes
 * - isGenerating: request in flight
 * - isPushing: request in flight
 */
const PanelState = {
  formDraft: {},
  currentEnrichment: null,
  isGenerating: false,
  isPushing: false,
  lastValidatedFormHash: null,
};

/**
 * DOM elements cache for efficient access.
 */
const DOM = {
  // Header
  authArea: document.getElementById('authArea'),
  authAction: document.getElementById('authAction'),
  apiStatus: document.getElementById('apiStatus'),

  // Form
  leadForm: document.getElementById('leadForm'),
  company_name: document.getElementById('company_name'),
  contact_name: document.getElementById('contact_name'),
  contact_role: document.getElementById('contact_role'),
  signal: document.getElementById('signal'),
  pain_point: document.getElementById('pain_point'),
  notes: document.getElementById('notes'),
  provider: document.getElementById('provider'),
  grabButton: document.getElementById('grabButton'),

  // Status
  statusMessage: document.getElementById('statusMessage'),

  // Preview
  previewSection: document.getElementById('previewSection'),
  snapshotContainer: document.getElementById('snapshotContainer'),
  openerContainer: document.getElementById('openerContainer'),
  followupsContainer: document.getElementById('followupsContainer'),
  previewFooter: document.getElementById('previewFooter'),
  briefSections: document.getElementById('briefSections'),

  // Actions
  generateBtn: document.getElementById('generateBtn'),
  pushBtn: document.getElementById('pushBtn'),
  closePanelBtn: document.getElementById('closePanelBtn'),
};

/**
 * Debounce utility for draft persistence.
 */
function debounce(fn, delayMs) {
  let timeoutId;
  return function debounced(...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delayMs);
  };
}

/**
 * Collect current form values into a plain object.
 */
function getFormValues() {
  return {
    company_name: DOM.company_name.value,
    contact_name: DOM.contact_name.value,
    contact_role: DOM.contact_role.value,
    signal: DOM.signal.value,
    pain_point: DOM.pain_point.value,
    notes: DOM.notes.value,
    provider: DOM.provider.value,
  };
}

/**
 * Apply form values to input fields.
 */
function setFormValues(values) {
  if (values.company_name !== undefined) DOM.company_name.value = values.company_name;
  if (values.contact_name !== undefined) DOM.contact_name.value = values.contact_name;
  if (values.contact_role !== undefined) DOM.contact_role.value = values.contact_role;
  if (values.signal !== undefined) DOM.signal.value = values.signal;
  if (values.pain_point !== undefined) DOM.pain_point.value = values.pain_point;
  if (values.notes !== undefined) DOM.notes.value = values.notes;
  if (values.provider !== undefined) DOM.provider.value = values.provider;
}

/**
 * Hash the form values to detect changes (T063: lifecycle validation).
 */
function hashFormValues(values) {
  const str = JSON.stringify(values);
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return hash;
}

/**
 * Persist form values to chrome.storage.session (T061).
 *
 * The generated preview is stored alongside the form values, per data-model.md
 * ("held in memory only, alongside the draft in storage.session"). The panel document
 * survives page navigation and tab switches on its own, so in-memory state alone would
 * satisfy the letter of FR-005 — but the panel IS torn down when the user closes and
 * reopens it, and restoring the form while silently dropping the preview the user just
 * generated is a confusing half-restore. Both are session-scoped, so neither reaches disk.
 */
async function persistDraft(values) {
  const draft = { ...values };
  await chrome.storage.session.set({
    [STORAGE_KEYS.DRAFT]: {
      values: draft,
      enrichment: PanelState.currentEnrichment || null,
    },
  });
}

/**
 * Retrieve draft from chrome.storage.session (T061).
 * Returns { values, enrichment } — enrichment may be null.
 */
async function loadDraft() {
  const data = await chrome.storage.session.get([STORAGE_KEYS.DRAFT]);
  const stored = data[STORAGE_KEYS.DRAFT];
  if (!stored) return { values: {}, enrichment: null };
  return {
    values: stored.values || {},
    enrichment: stored.enrichment || null,
  };
}

/**
 * Clear draft after successful push (T061).
 */
async function clearDraft() {
  await chrome.storage.session.remove([STORAGE_KEYS.DRAFT]);
}

/**
 * Debounced draft saver (~400ms).
 */
const debouncedSaveDraft = debounce(async (values) => {
  await persistDraft(values);
}, 400);

/**
 * Render company snapshot in the preview.
 */
function renderSnapshot(snapshot) {
  DOM.snapshotContainer.innerHTML = '';

  const card = document.createElement('div');
  card.className = 'snapshot-card';

  const p = document.createElement('p');
  p.className = 'snapshot-text';
  p.textContent = snapshot;

  card.appendChild(p);
  DOM.snapshotContainer.appendChild(card);
}

/**
 * Render personalized opener with copy button (T062).
 */
function renderOpener(opener) {
  DOM.openerContainer.innerHTML = '';

  // null means the outreach email is carrying the opening instead — leave the
  // container empty rather than rendering an empty card.
  if (!opener) {
    return;
  }

  const card = document.createElement('div');
  card.className = 'opener-card';

  const quote = document.createElement('p');
  quote.className = 'opener-quote';
  quote.textContent = opener;

  const copyBtn = document.createElement('button');
  copyBtn.type = 'button';
  copyBtn.className = 'btn btn-ghost btn-sm opener-copy-btn';
  copyBtn.textContent = 'Copy';
  copyBtn.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(opener);
      const originalText = copyBtn.textContent;
      copyBtn.textContent = 'Copied!';
      setTimeout(() => {
        copyBtn.textContent = originalText;
      }, 2000);
    } catch (err) {
      console.error('Copy failed:', err.message);
    }
  });

  card.appendChild(quote);
  card.appendChild(copyBtn);
  DOM.openerContainer.appendChild(card);
}

/**
 * Render all follow-ups from the enrichment response (T062).
 * Handles case where fewer than 3 entries exist.
 */
function renderFollowups(followups) {
  DOM.followupsContainer.innerHTML = '';

  const count = followups ? followups.length : 0;

  // data-model.md: fewer than 3 follow_ups => render what exists and note
  // the shortfall (never pad with placeholders, never render silently).
  if (count < 3) {
    const note = document.createElement('p');
    note.className = 'followup-rationale';
    note.textContent =
      count === 0
        ? 'No follow-up tasks were generated.'
        : `Only ${count} of 3 follow-up tasks were generated.`;
    DOM.followupsContainer.appendChild(note);
  }

  if (count === 0) {
    return;
  }

  const list = document.createElement('div');
  list.className = 'followups-list';

  for (let i = 0; i < followups.length; i++) {
    const fu = followups[i];

    const card = document.createElement('div');
    card.className = 'followup-card';

    // Header: title and due
    const header = document.createElement('div');
    header.className = 'followup-header';

    const title = document.createElement('h4');
    title.className = 'followup-title';
    title.textContent = fu.title;

    const due = document.createElement('span');
    due.className = 'followup-due';
    due.textContent = `+${fu.due_in_days} days`;

    header.appendChild(title);
    header.appendChild(due);

    // Description
    const desc = document.createElement('p');
    desc.className = 'followup-description';
    desc.textContent = fu.description;

    // Rationale
    const rationale = document.createElement('p');
    rationale.className = 'followup-rationale';
    rationale.textContent = fu.rationale;

    card.appendChild(header);
    card.appendChild(desc);
    card.appendChild(rationale);
    list.appendChild(card);
  }

  DOM.followupsContainer.appendChild(list);
}

// ─── Brief sections: buying signal, confidence, email, CRM entry (009) ───────
//
// Each section renders populated when the server sent valid data for it, and
// inert otherwise. 009 made the populated branch reachable; it did not relax the
// rule that made these inert in 008. NOTHING here is derived client-side: no
// confidence computed from heuristics, no subject synthesised from a company
// name, no source inferred from a domain. If the server did not send it, the
// section is inert — which is why every guard below interrogates the payload
// instead of reaching for a fallback value.
//
// Mirrors web/src/components/Preview.tsx section for section, down to the inert
// copy, so the two surfaces render the same brief from the same data.

/** The only confidence values that may ever reach the DOM. */
const CONFIDENCE_LEVELS = ['high', 'medium', 'low'];

/** A non-empty trimmed string, or null. Whitespace-only is not a value. */
function briefText(value) {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  return trimmed || null;
}

/** A plain object (not null, not an array), or null. */
function briefObject(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
  return value;
}

/**
 * Re-checks the enum the server already checked.
 *
 * Not redundant: a stored enrichment could predate the server-side validator,
 * and an unrecognised level must never be rendered raw as a pill of unknown
 * meaning. Out of range is treated exactly like absent.
 */
function confidenceLevel(value) {
  const level = briefText(value);
  return level && CONFIDENCE_LEVELS.indexOf(level) !== -1 ? level : null;
}

/**
 * Re-validates the citation URL the server already validated.
 *
 * Same reason as confidenceLevel — a stored enrichment can predate the
 * server-side validator — with more at stake, because this value ends up in an
 * href. https only: javascript: and data: are the attack cases, and http is
 * refused because a link we invite the rep to click should not be downgradeable
 * in transit. Returns the parsed URL so the caller never re-parses it.
 */
function httpsUrl(value) {
  const raw = briefText(value);
  if (!raw) return null;
  let parsed;
  try {
    parsed = new URL(raw);
  } catch (e) {
    return null;
  }
  if (parsed.protocol !== 'https:' || !parsed.hostname) return null;
  return parsed;
}

/** <p class="{className}">{value}</p> — textContent, never innerHTML. */
function makeText(tag, className, value) {
  const el = document.createElement(tag);
  el.className = className;
  el.textContent = value;
  return el;
}

/** The 008 inert presentation: styled, labelled unavailable, never invented. */
function makeInertSection(title, note) {
  const box = document.createElement('div');
  box.className = 'inert';
  box.setAttribute('role', 'note');
  box.setAttribute('aria-label', `${title}: not available yet`);
  box.appendChild(makeText('p', 'inert-title', title));
  box.appendChild(makeText('p', 'inert-note', note));
  return box;
}

/**
 * The source chip, carrying a real link.
 *
 * Assembled node by node on purpose: href is assigned only after httpsUrl has
 * passed, and the anchor is never built from a template string. Link text is
 * the hostname, so what the rep clicks always matches what they read — a
 * model-supplied publisher name over a link to somewhere else is exactly the
 * mismatch this avoids. rel="noopener noreferrer" because target="_blank"
 * otherwise hands the opened page a handle on this one.
 */
function makeSourceLinkChip(url, withLabel) {
  const chip = document.createElement('span');
  chip.className = 'brief-meta-item';
  if (withLabel) chip.appendChild(document.createTextNode('Source: '));
  const link = document.createElement('a');
  link.className = 'brief-link';
  link.textContent = url.hostname;
  link.href = url.href;
  link.title = url.href;
  link.target = '_blank';
  link.rel = 'noopener noreferrer';
  chip.appendChild(link);
  return chip;
}

/** A populated section shell: solid border + uppercase title. */
function makeBriefSection(title) {
  const box = document.createElement('div');
  box.className = 'brief-section';
  box.appendChild(makeText('p', 'brief-title', title));
  return box;
}

function renderBuyingSignal(enrichment) {
  const signal = briefObject(enrichment.buying_signal);
  const summary = signal ? briefText(signal.summary) : null;

  if (!summary) {
    return makeInertSection('Buying signal', 'Source and date not available yet.');
  }

  const box = makeBriefSection('Buying signal');
  box.appendChild(makeText('p', 'brief-text', summary));

  // Source and date are independently optional: the model is instructed to omit
  // an attribution it cannot support rather than invent one, so a summary with
  // no source is the expected honest case, not a degraded one.
  // 010: the citation. The finding is what a grounded search returned, attributed
  // by the provider to these sources — not a quotation from any of them. It cannot
  // outlive the links that make it checkable, since an unattributable claim is a
  // fabrication surface rather than evidence. The server enforces the same
  // pairing; this is the both-sides re-check.
  //
  // ALL sources render, not the best one. A grounded sentence is routinely a
  // synthesis across several pages, and a single link beside it would assert that
  // one page says the whole thing.
  const rawSources = Array.isArray(signal.sources)
    ? signal.sources
    // Pre-multi-source 010 enrichments carried one source_url. Read rather than
    // derive: this is the stored value, not something inferred client-side.
    : (signal.source_url ? [{ url: signal.source_url }] : []);
  const sources = [];
  for (let i = 0; i < rawSources.length; i++) {
    const entry = briefObject(rawSources[i]);
    const url = entry ? httpsUrl(entry.url) : null;
    if (url) sources.push(url);
  }

  const finding = sources.length ? briefText(signal.finding) : null;
  if (finding) box.appendChild(makeText('p', 'brief-finding', `Search found: ${finding}`));

  if (sources.length && signal.unverified_by_company === true) {
    const caution = makeText('p', 'brief-caution',
      'No source from the company itself — this signal may not be accurate. Check before sending.');
    caution.setAttribute('role', 'note');
    box.appendChild(caution);
  }

  const source = briefText(signal.source);
  const date = briefText(signal.date);
  if (source || date || sources.length) {
    const meta = document.createElement('div');
    meta.className = 'brief-meta';
    // Real links replace the plain attribution rather than joining it: source chips
    // that disagree are worse than ones that are checkable, and each hostname
    // already carries its publisher identity.
    if (sources.length) {
      for (let i = 0; i < sources.length; i++) {
        meta.appendChild(makeSourceLinkChip(sources[i], i === 0));
      }
    } else if (source) {
      meta.appendChild(makeText('span', 'brief-meta-item', `Source: ${source}`));
    }
    if (date) meta.appendChild(makeText('span', 'brief-meta-item', date));
    box.appendChild(meta);
  }

  return box;
}

function renderContactConfidence(enrichment) {
  const confidence = briefObject(enrichment.contact_confidence);
  const level = confidence ? confidenceLevel(confidence.level) : null;
  const reason = confidence ? briefText(confidence.reason) : null;

  // Both or neither. A pill with no reason is unfalsifiable, which is exactly
  // the decorative-confidence failure this section was held back to avoid.
  if (!level || !reason) {
    return makeInertSection('Contact confidence', 'Verification not available yet.');
  }

  const box = makeBriefSection('Contact confidence');

  const row = document.createElement('div');
  row.className = 'confidence-row';
  // Safe as a class name because level passed the enum check above; an
  // unvalidated value would never reach this line.
  row.appendChild(makeText('span', `confidence-pill ${level}`, level));
  box.appendChild(row);

  box.appendChild(makeText('p', 'brief-text', reason));
  return box;
}

/**
 * The outreach email, or null when the server did not send a complete one.
 *
 * Shared on purpose: the email supersedes the "Suggested Opener" card when it is
 * present, so the same validation gates both. `personalized_opener` itself is
 * untouched in the response — it stays frozen and still builds the CRM deal
 * comment on the push path. This is only about which of the two the brief shows.
 */
function validOutreachEmail(enrichment) {
  const email = briefObject(enrichment.outreach_email);
  if (!email) return null;
  const subject = briefText(email.subject);
  const body = briefText(email.body);
  return subject && body ? { subject, body } : null;
}

function renderOutreachEmail(enrichment, recipient) {
  const email = validOutreachEmail(enrichment);
  const subject = email ? email.subject : null;
  const body = email ? email.body : null;

  if (!subject || !body) {
    return makeInertSection(
      'Outreach email',
      'Full draft not available yet — use the opener above.',
    );
  }

  const box = makeBriefSection('Outreach email');

  const headers = document.createElement('div');
  headers.className = 'email-headers';

  // The recipient echoes what the user typed into the form. That is not a
  // derivation of model output — it is their own input, shown back.
  if (recipient) {
    const toRow = document.createElement('div');
    toRow.className = 'email-header-row';
    toRow.appendChild(makeText('span', 'email-header-key', 'To'));
    toRow.appendChild(makeText('span', 'email-header-value', recipient));
    headers.appendChild(toRow);
  }

  const subjRow = document.createElement('div');
  subjRow.className = 'email-header-row';
  subjRow.appendChild(makeText('span', 'email-header-key', 'Subject'));
  subjRow.appendChild(makeText('span', 'email-header-value', subject));
  headers.appendChild(subjRow);

  box.appendChild(headers);

  // pre-wrap keeps the model's paragraph breaks without any markup, so the body
  // stays one text node and never goes near innerHTML.
  box.appendChild(makeText('p', 'email-body', body));

  const copyBtn = document.createElement('button');
  copyBtn.type = 'button';
  copyBtn.className = 'btn btn-ghost btn-sm email-copy-btn';
  copyBtn.textContent = 'Copy email';
  copyBtn.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(`Subject: ${subject}\n\n${body}`);
      copyBtn.textContent = 'Copied!';
      setTimeout(() => {
        copyBtn.textContent = 'Copy email';
      }, 2000);
    } catch (err) {
      console.error('Copy failed:', err.message);
    }
  });
  box.appendChild(copyBtn);

  return box;
}

const CRM_FIELD_LABELS = [
  ['deal_name', 'Deal name'],
  ['contact_role', 'Contact role'],
  ['signal', 'Signal'],
  ['pain_point', 'Pain point'],
  ['pipeline', 'Pipeline'],
];

function renderCrmEntry(enrichment) {
  const entry = briefObject(enrichment.crm_entry);
  const fields = [];
  if (entry) {
    for (let i = 0; i < CRM_FIELD_LABELS.length; i++) {
      const key = CRM_FIELD_LABELS[i][0];
      const value = briefText(entry[key]);
      if (value) fields.push([CRM_FIELD_LABELS[i][1], value]);
    }
  }

  if (fields.length === 0) {
    return makeInertSection('CRM entry', 'Field mapping preview not available yet.');
  }

  // Display-only. This feature does not change /api/leads/push or the CRM
  // adapters, so this shows what the model proposes, not what will be sent.
  const box = makeBriefSection('CRM entry (preview)');

  const grid = document.createElement('div');
  grid.className = 'crm-grid';
  for (let i = 0; i < fields.length; i++) {
    const cell = document.createElement('div');
    cell.className = 'crm-field';
    cell.appendChild(makeText('p', 'crm-key', fields[i][0]));
    cell.appendChild(makeText('p', 'crm-value', fields[i][1]));
    grid.appendChild(cell);
  }
  box.appendChild(grid);

  return box;
}

/**
 * Render all four brief sections, each populated or inert on its own.
 */
function renderBriefSections(enrichment, recipient) {
  DOM.briefSections.innerHTML = '';
  DOM.briefSections.appendChild(renderBuyingSignal(enrichment));
  DOM.briefSections.appendChild(renderContactConfidence(enrichment));
  DOM.briefSections.appendChild(renderOutreachEmail(enrichment, recipient));
  DOM.briefSections.appendChild(renderCrmEntry(enrichment));
}

/**
 * Render provenance footer if model_used or memory_note exists (T062).
 */
function renderPreviewFooter(enrichment) {
  DOM.previewFooter.innerHTML = '';

  const parts = [];
  if (enrichment.model_used) {
    parts.push(`Model: ${enrichment.model_used}`);
  }
  if (enrichment.memory_note) {
    parts.push(`Memory: ${enrichment.memory_note}`);
  }

  if (parts.length > 0) {
    const footer = document.createElement('div');
    footer.className = 'preview-footer';
    footer.textContent = parts.join(' • ');
    DOM.previewFooter.appendChild(footer);
  }
}

/**
 * Render the complete preview from enrichment response (T062).
 * Shows snapshot, opener, follow-ups, and provenance.
 * Uses DOM construction, never innerHTML with interpolated data.
 */
function renderPreview(enrichment) {
  // Validate: company_snapshot is required
  if (!enrichment.company_snapshot) {
    showErrorStatus('service', 'Cannot render preview: missing company snapshot');
    return;
  }

  DOM.previewSection.style.display = 'flex';

  renderSnapshot(enrichment.company_snapshot);
  // The full outreach email supersedes the opener when there is one: they are two
  // openings for the same lead, and showing both invites the user to send a
  // message that contradicts the one below it. When the email is absent the card
  // stays, which is also what keeps the inert email block's "use the opener
  // above" copy true.
  renderOpener(validOutreachEmail(enrichment) ? null : enrichment.personalized_opener);
  renderFollowups(enrichment.follow_ups);
  // The email's "To" line is the contact the user typed, read back off the form
  // rather than taken from the model — the recipient is the user's own input.
  renderBriefSections(enrichment, getFormValues().contact_name);
  renderPreviewFooter(enrichment);

  // Update form hash to track validation state
  PanelState.lastValidatedFormHash = hashFormValues(getFormValues());

  // Enable push button now that preview exists
  updatePushButtonState();
}

/**
 * Clear preview display (T063: when form changes after generate).
 */
function clearPreview() {
  DOM.previewSection.style.display = 'none';
  DOM.snapshotContainer.innerHTML = '';
  DOM.openerContainer.innerHTML = '';
  DOM.followupsContainer.innerHTML = '';
  DOM.briefSections.innerHTML = '';
  DOM.previewFooter.innerHTML = '';
  PanelState.currentEnrichment = null;
  PanelState.lastValidatedFormHash = null;
  updatePushButtonState();
}

/**
 * Show status message with appropriate styling.
 * Type: 'loading', 'success', 'error', 'session-error'
 */
function showStatus(type, message, secondaryAction = null) {
  const el = DOM.statusMessage;
  el.innerHTML = '';
  el.className = `status-message active ${type}`;

  if (type === 'session-error' && secondaryAction) {
    const textSpan = document.createElement('span');
    textSpan.textContent = message;

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'session-error-action';
    btn.textContent = secondaryAction.label;
    btn.addEventListener('click', secondaryAction.action);

    el.appendChild(textSpan);
    el.appendChild(btn);
  } else {
    el.textContent = message;
  }
}

/**
 * Hide status message.
 */
function hideStatus() {
  DOM.statusMessage.className = 'status-message';
  DOM.statusMessage.innerHTML = '';
}

/**
 * Show error based on error class (FR-014).
 */
function showErrorStatus(errorClass, message) {
  if (errorClass === 'session') {
    showStatus('session-error', message, {
      label: 'Sign in',
      action: async () => {
        DOM.authAction.disabled = true;
        try {
          await BDAuth.signIn();
          await updateAuthUI();
          hideStatus();
        } catch (err) {
          showErrorStatus(err.class || 'service', err.message);
        } finally {
          DOM.authAction.disabled = false;
        }
      },
    });
  } else if (errorClass === 'setup') {
    showStatus('error', message);
  } else if (errorClass === 'unreachable') {
    showStatus(
      'error',
      `${message} — check that your backend is running at ${API_BASE}`
    );
  } else {
    // 'input', 'service', 'restricted', 'permission', or other.
    // These all carry a self-explanatory message from their source, so they render
    // as-is rather than getting extra UI affordances bolted on.
    showStatus('error', message);
  }
}

/**
 * Render capture error based on error class (T066: edge cases).
 */
function showCaptureError(errorClass, message) {
  showErrorStatus(errorClass, message);
}

/**
 * Update push button enabled state (T063: FR-016 lifecycle).
 * Disabled until a preview exists, while push is in flight,
 * and again if form changes after preview was generated.
 */
function updatePushButtonState() {
  const hasPreview = PanelState.currentEnrichment !== null;
  const formChanged = hasPreview
    ? hashFormValues(getFormValues()) !== PanelState.lastValidatedFormHash
    : false;

  DOM.pushBtn.disabled =
    !hasPreview || PanelState.isPushing || formChanged;
}

/**
 * Check backend reachability and update API status indicator.
 */
async function updateAPIStatus() {
  const isOnline = await BDApi.health();
  if (isOnline) {
    DOM.apiStatus.classList.add('online');
    DOM.apiStatus.title = 'Backend is reachable';
  } else {
    DOM.apiStatus.classList.remove('online');
    DOM.apiStatus.title = 'Backend is unreachable';
  }
}

/**
 * Update auth UI based on session state (T064).
 */
async function updateAuthUI() {
  const session = await BDAuth.getSession();

  if (session.state === 'valid' && session.user) {
    DOM.authArea.className = 'auth-area valid';
    DOM.authArea.innerHTML = '';

    const span = document.createElement('span');
    span.textContent = `Signed in as ${session.user.email}`;
    span.style.marginRight = '8px';

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'auth-button';
    btn.textContent = 'Sign out';
    btn.addEventListener('click', async () => {
      btn.disabled = true;
      try {
        await BDAuth.signOut();
        await updateAuthUI();
      } finally {
        btn.disabled = false;
      }
    });

    DOM.authArea.appendChild(span);
    DOM.authArea.appendChild(btn);
  } else if (session.state === 'expired') {
    DOM.authArea.className = 'auth-area';
    DOM.authArea.innerHTML = '';

    const span = document.createElement('span');
    span.textContent = 'Session expired — ';

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'auth-button';
    btn.textContent = 'Sign in';
    btn.addEventListener('click', async () => {
      btn.disabled = true;
      try {
        await BDAuth.signIn();
        await updateAuthUI();
      } catch (err) {
        showErrorStatus(err.class || 'service', err.message);
      } finally {
        btn.disabled = false;
      }
    });

    DOM.authArea.appendChild(span);
    DOM.authArea.appendChild(btn);
  } else {
    // absent
    DOM.authArea.className = 'auth-area';
    DOM.authArea.innerHTML = '';

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'auth-button';
    btn.textContent = 'Sign in';
    btn.addEventListener('click', async () => {
      btn.disabled = true;
      try {
        await BDAuth.signIn();
        await updateAuthUI();
      } catch (err) {
        showErrorStatus(err.class || 'service', err.message);
      } finally {
        btn.disabled = false;
      }
    });

    DOM.authArea.appendChild(btn);
  }
}

/**
 * Validate session on panel open (T064, scenario 6).
 * This is a network call to confirm expiry, distinct from getSession() which uses stored expiry.
 */
async function validateSessionOnOpen() {
  const session = await BDAuth.validate();
  if (session.state !== 'valid') {
    await updateAuthUI();
  }
}

/**
 * Handle Generate button click (T063).
 * Builds input, calls BDApi.enrich(), renders preview or error.
 */
async function handleGenerate() {
  hideStatus();
  PanelState.isGenerating = true;
  DOM.generateBtn.disabled = true;

  try {
    showStatus('loading', 'Generating preview with AI...');

    const values = getFormValues();
    const input = BDApi.buildInput(values);

    const enrichment = await BDApi.enrich(input);

    // Validate enrichment shape
    if (!enrichment.company_snapshot) {
      showErrorStatus('service', 'Cannot render preview: missing company snapshot');
      return;
    }

    PanelState.currentEnrichment = enrichment;
    hideStatus();
    renderPreview(enrichment);

    // Save draft immediately when preview is generated (T061)
    await persistDraft(values);

    showStatus('success', 'Preview generated successfully');
  } catch (err) {
    console.error('Generate failed:', err.message);
    showErrorStatus(err.class || 'service', err.message);
  } finally {
    PanelState.isGenerating = false;
    DOM.generateBtn.disabled = false;
  }
}

/**
 * Handle Push button click (T063).
 * Calls BDApi.push(), shows result or error.
 */
async function handlePush() {
  hideStatus();
  PanelState.isPushing = true;
  DOM.pushBtn.disabled = true;
  DOM.generateBtn.disabled = true;

  try {
    showStatus('loading', 'Pushing to CRM...');

    const values = getFormValues();
    const input = BDApi.buildInput(values);
    const provider = values.provider || DEFAULT_PROVIDER;

    const result = await BDApi.push(input, provider);

    // Show success with contact/deal ids
    const detail = `Contact ID: ${result.contact_id || '?'} | Deal ID: ${result.deal_id || '?'}`;
    showStatus('success', `Lead pushed successfully — ${detail}`);

    // Clear draft after successful push (T061)
    await clearDraft();

    // Reset form and preview
    setFormValues({
      company_name: '',
      contact_name: '',
      contact_role: '',
      signal: '',
      pain_point: '',
      notes: '',
    });
    clearPreview();
  } catch (err) {
    console.error('Push failed:', err.message);
    showErrorStatus(err.class || 'service', err.message);
  } finally {
    PanelState.isPushing = false;
    DOM.pushBtn.disabled = false;
    DOM.generateBtn.disabled = false;
    updatePushButtonState();
  }
}

/**
 * Handle "Grab from this page" button click (T066).
 * Captures page context and merges into form with conflict handling.
 */
async function handleCapture() {
  DOM.grabButton.disabled = true;
  hideStatus();

  try {
    const pageContext = await BDCapture.fromActiveTab();

    // Edge case 2: no usable details found
    if (
      !pageContext.company &&
      !pageContext.signal &&
      !pageContext.url &&
      !pageContext.title
    ) {
      showCaptureError(
        'service',
        'No usable details found on this page'
      );
      return;
    }

    const formValues = getFormValues();
    const { patch, conflicts } = BDCapture.merge(pageContext, formValues);

    // If there are conflicts, ask before overwriting
    if (conflicts.length > 0) {
      const confirmMsg = `Overwrite these fields: ${conflicts.join(', ')}?`;
      if (!confirm(confirmMsg)) {
        // User declined: apply only non-conflicting patch
        setFormValues(patch);
        showStatus('success', 'Prefilled available fields (skipped conflicts)');
        return;
      }
    }

    // Apply full patch (including conflicts if confirmed)
    const mergedValues = { ...formValues, ...patch };
    if (conflicts.length > 0) {
      for (const field of conflicts) {
        if (pageContext.company && field === 'company_name') {
          mergedValues.company_name = pageContext.company;
        } else if (pageContext.signal && field === 'signal') {
          mergedValues.signal = pageContext.signal;
        } else if (pageContext.url && field === 'source_url') {
          // source_url doesn't map directly to notes; compose it
          mergedValues.notes = pageContext.url +
            (mergedValues.notes ? '\n' + mergedValues.notes : '');
        }
      }
    }

    // Also compose title + url into notes if we have both (T066)
    // Only append if notes is currently empty
    if (pageContext.title && pageContext.url && !formValues.notes) {
      mergedValues.notes = `${pageContext.title}\n${pageContext.url}`;
    } else if (pageContext.url && !formValues.notes) {
      mergedValues.notes = pageContext.url;
    }

    setFormValues(mergedValues);

    // Invalidate preview if one exists (editing after generate)
    if (PanelState.currentEnrichment) {
      clearPreview();
    }

    // Persist the updated draft (T061)
    await persistDraft(mergedValues);

    showStatus('success', 'Prefilled form from page');
  } catch (err) {
    if (err.class === 'restricted') {
      showCaptureError('restricted', err.message || "Can't read this page (try a normal web page)");
    } else {
      showCaptureError(err.class || 'service', err.message);
    }
  } finally {
    DOM.grabButton.disabled = false;
  }
}

/**
 * Initialize panel on load (T061, T064).
 * Rehydrate form, check auth, validate session, set up event listeners.
 */
async function initializePanel() {
  // Rehydrate form values from the draft (T061, FR-005)
  const draft = await loadDraft();
  if (Object.keys(draft.values).length > 0) {
    setFormValues(draft.values);
    PanelState.formDraft = draft.values;
  }

  // Load persisted provider preference (T063)
  const data = await chrome.storage.local.get([STORAGE_KEYS.PROVIDER]);
  const provider = data[STORAGE_KEYS.PROVIDER] || DEFAULT_PROVIDER;
  DOM.provider.value = provider;

  // Restore a previously generated preview LAST, after every form field (including
  // provider, above) has its final value. renderPreview() snapshots the form hash that
  // Push-invalidation compares against; if it ran before the provider was applied, that
  // baseline would disagree with the live form and Push would sit wrongly disabled.
  if (draft.enrichment && draft.enrichment.company_snapshot) {
    PanelState.currentEnrichment = draft.enrichment;
    renderPreview(draft.enrichment);
  }

  // Check API reachability
  updateAPIStatus();

  // Check auth state on panel open (T064)
  await updateAuthUI();

  // Validate session with backend (T064, scenario 6)
  await validateSessionOnOpen();

  // Set up form input listeners (T061)
  const formInputs = [
    DOM.company_name,
    DOM.contact_name,
    DOM.contact_role,
    DOM.signal,
    DOM.pain_point,
    DOM.notes,
  ];

  formInputs.forEach((input) => {
    input.addEventListener('input', () => {
      const values = getFormValues();

      // Invalidate preview if form changes after generate (T063: lifecycle)
      if (PanelState.currentEnrichment) {
        clearPreview();
      }

      // Debounced persistence (T061, ~400ms)
      debouncedSaveDraft(values);
    });
  });

  // Provider change: persist to local storage (T063)
  DOM.provider.addEventListener('change', async () => {
    await chrome.storage.local.set({
      [STORAGE_KEYS.PROVIDER]: DOM.provider.value,
    });

    // Invalidate preview if form changes after generate (T063: lifecycle).
    // `provider` is part of the LeadDraft and included in hashFormValues(),
    // so it must invalidate the same way the other form inputs do below —
    // otherwise the push button's disabled state goes stale relative to the hash.
    if (PanelState.currentEnrichment) {
      clearPreview();
    }

    const values = getFormValues();
    await persistDraft(values);
  });

  // Generate button
  DOM.generateBtn.addEventListener('click', handleGenerate);

  // Push button
  DOM.pushBtn.addEventListener('click', handlePush);

  // Grab from page button (T066)
  DOM.grabButton.addEventListener('click', handleCapture);

  // Close the panel from inside it. A side panel is an extension page, so
  // window.close() dismisses it.
  //
  // This control lives in the FOOTER on purpose. Chrome renders its own close
  // X in the side-panel header; putting ours in our top-right would give the
  // user two competing dismiss affordances in the same corner.
  if (DOM.closePanelBtn) {
    DOM.closePanelBtn.addEventListener('click', () => {
      window.close();
    });
  }
}

/**
 * Start the panel.
 */
initializePanel().catch((err) => {
  console.error('Panel initialization failed:', err.message);
});
