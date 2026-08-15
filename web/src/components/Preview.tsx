import React from 'react';
import { CONFIDENCE_LEVELS, type ConfidenceLevel, type EnrichedPreview } from '../api/client';

interface PreviewProps {
  data?: {
    company_name: string;
    contact_name: string;
    contact_role: string;
    signal?: string;
    pain_point?: string;
    notes?: string;
  };
  enriched?: EnrichedPreview | null;
}

/**
 * Preview component for T013: renders enriched from /enrich (snapshot, opener, 3 follow_ups).
 * Matches UI_UX: Company Snapshot, Suggested Opener (copy), Follow-up Plan (title/desc/rationale + due).
 * Falls back to input-derived stub if no enriched (skeleton compat, T012 etc).
 * Uses snake_case from backend T007/T010.
 */
/**
 * The four sections the design specifies beyond snapshot / opener / follow-ups.
 *
 * Each renders populated when the server sent valid data for it, and inert
 * otherwise: styled in the product's visual language, labelled unavailable, and
 * never filled with invented values. Deliberately not a spinner or skeleton —
 * those imply data is on its way. This is an honest "not this time".
 *
 * 009 made the populated branch reachable; it did not relax the rule that made
 * these inert in the first place. NOTHING here is derived client-side. No
 * confidence computed from heuristics, no subject synthesised from a company
 * name, no source inferred from a domain. If the server did not send it, the
 * section is inert — which is why every guard below tests the payload rather
 * than reaching for a fallback value.
 */
const InertSection: React.FC<{ title: string; note: string }> = ({ title, note }) => (
  <div className="inert" role="note" aria-label={`${title}: not available yet`}>
    <p className="inert-title">{title}</p>
    <p className="inert-note">{note}</p>
  </div>
);

/** A non-empty string, or null. Whitespace-only is not a value. */
const text = (value: unknown): string | null => {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  return trimmed || null;
};

/**
 * Re-checks the enum the server already checked.
 *
 * Not redundant: EnrichedPreview carries an index signature, so the compiler
 * cannot prove what arrived, and a stored enrichment could predate the
 * server-side validator entirely. An unrecognised level must never reach the
 * DOM as a pill of unknown meaning.
 */
const asConfidenceLevel = (value: unknown): ConfidenceLevel | null =>
  CONFIDENCE_LEVELS.includes(value as ConfidenceLevel) ? (value as ConfidenceLevel) : null;

/**
 * Re-validates the citation URL the server already validated.
 *
 * Same reasoning as asConfidenceLevel — a stored enrichment can predate the
 * server-side validator — with more at stake, because this value ends up in an
 * href. https only: javascript: and data: are the attack cases, and http is
 * refused because a link we invite the user to click should not be
 * downgradeable in transit.
 *
 * Returns the parsed URL so the caller renders the hostname as link text. That
 * is not the client-side derivation this brief forbids: it makes no new claim,
 * it renders the datum the server sent. It also guarantees the link text cannot
 * misrepresent where the link goes, which a model-supplied publisher name
 * ("TechCrunch" over a link to somewhere else) could.
 */
const httpsUrl = (value: unknown): URL | null => {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  let parsed: URL;
  try {
    parsed = new URL(trimmed);
  } catch {
    return null;
  }
  if (parsed.protocol !== 'https:' || !parsed.hostname) return null;
  return parsed;
};

/**
 * Google's Search Suggestions block, rendered verbatim inside a shadow root.
 *
 * The one place in this component that assigns markup rather than text, and a
 * deliberate narrow exception. The Gemini API terms REQUIRE grounded results be
 * displayed with their Search Suggestions and separately FORBID modifying them, so
 * rebuilding the chips as JSX would itself be a violation.
 *
 * The fragment is checked server-side before it is ever sent — no script, no on*
 * handlers, no javascript:/data:, https links only, size-capped — and refused outright
 * rather than cleaned, which drops the whole citation. Nothing unsafe is ever "made
 * safe" and then rendered.
 *
 * The shadow root is for style, not security: Google ships unscoped global CSS for
 * `.container`, `.chip` and `.carousel`, which would otherwise leak into the app.
 */
const SearchSuggestions: React.FC<{ html: string }> = ({ html }) => {
  const hostRef = React.useRef<HTMLDivElement>(null);
  React.useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const root = host.shadowRoot ?? host.attachShadow({ mode: 'open' });
    root.innerHTML = html;
  }, [html]);
  return <div className="search-suggestions" ref={hostRef} />;
};

const BuyingSignalSection: React.FC<{ enriched: EnrichedPreview }> = ({ enriched }) => {
  const signal = enriched.buying_signal;
  const summary = signal && typeof signal === 'object' ? text(signal.summary) : null;

  if (!summary) {
    return <InertSection title="Buying signal" note="Source and date not available yet." />;
  }

  // Source and date are independently optional: the model is instructed to omit
  // an attribution it cannot support rather than invent one, so a summary with
  // no source is the expected honest case, not a degraded one.
  const source = text(signal!.source);
  const date = text(signal!.date);

  // 010: the citation. The finding is what a grounded search returned, attributed
  // by the provider to these sources — not a quotation from any of them. It cannot
  // outlive the links that make it checkable, since an unattributable claim is a
  // fabrication surface rather than evidence. The server enforces the same
  // pairing; this is the both-sides re-check.
  //
  // ALL sources render, not the best one. A grounded sentence is routinely a
  // synthesis across several pages, and a single link beside it would assert that
  // one page says the whole thing.
  const raw = Array.isArray(signal!.sources)
    ? signal!.sources
    : // Pre-multi-source 010 enrichments carried one source_url. Read rather than
      // derive: this is the stored value, not something inferred client-side.
      signal!.source_url
      ? [{ url: signal!.source_url }]
      : [];
  const sources = raw
    .map((s) => ({ url: httpsUrl(s?.url), publisher: text(s?.publisher) }))
    .filter((s): s is { url: URL; publisher: string | null } => s.url !== null);
  const finding = sources.length ? text(signal!.finding) : null;
  const unverified = sources.length > 0 && signal!.unverified_by_company === true;
  const suggestions = text(signal!.search_suggestions);

  return (
    <div className="brief-section">
      <p className="brief-title">Buying signal</p>
      <p className="brief-text">{summary}</p>
      {finding && <p className="brief-finding">Search found: {finding}</p>}
      {unverified && (
        <p className="brief-caution" role="note">
          No source from {'the company itself'} — this signal may not be accurate. Check before sending.
        </p>
      )}
      {(source || date || sources.length > 0) && (
        <div className="brief-meta">
          {/* Real links replace the plain attribution rather than joining it: source
              chips that disagree are worse than ones that are checkable, and each
              hostname already carries its publisher identity. */}
          {sources.length > 0
            ? sources.map((s, i) => (
                <span className="brief-meta-item" key={s.url.href}>
                  {i === 0 && 'Source: '}
                  <a
                    className="brief-link"
                    href={s.url.href}
                    title={s.url.href}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {s.url.hostname}
                  </a>
                </span>
              ))
            : source && <span className="brief-meta-item">Source: {source}</span>}
          {date && <span className="brief-meta-item">{date}</span>}
        </div>
      )}
      {/* Required by the Gemini API terms whenever grounded results are shown. The
          server drops the whole citation when it cannot supply a displayable
          fragment, so if there are sources there are suggestions. */}
      {sources.length > 0 && suggestions && <SearchSuggestions html={suggestions} />}
    </div>
  );
};

const ContactConfidenceSection: React.FC<{ enriched: EnrichedPreview }> = ({ enriched }) => {
  const confidence = enriched.contact_confidence;
  const level = confidence && typeof confidence === 'object' ? asConfidenceLevel(confidence.level) : null;
  const reason = confidence && typeof confidence === 'object' ? text(confidence.reason) : null;

  // Both or neither. A pill with no reason is unfalsifiable, which is exactly
  // the decorative-confidence failure this section was held back to avoid.
  if (!level || !reason) {
    return <InertSection title="Contact confidence" note="Verification not available yet." />;
  }

  return (
    <div className="brief-section">
      <p className="brief-title">Contact confidence</p>
      <div className="confidence-row">
        <span className={`confidence-pill ${level}`}>{level}</span>
      </div>
      <p className="brief-text">{reason}</p>
    </div>
  );
};

/**
 * The outreach email, or null when the server did not send a complete one.
 *
 * Exported shape matters: the email supersedes the "Suggested Opener" card when
 * it is present, so the same validation has to gate both. `personalized_opener`
 * itself is untouched in the response — it stays frozen and still builds the CRM
 * deal comment on the push path. This is purely which of the two the brief shows.
 */
export const validOutreachEmail = (
  enriched: EnrichedPreview,
): { subject: string; body: string } | null => {
  const email = enriched.outreach_email;
  if (!email || typeof email !== 'object') return null;
  const subject = text(email.subject);
  const body = text(email.body);
  return subject && body ? { subject, body } : null;
};

const OutreachEmailSection: React.FC<{ enriched: EnrichedPreview; recipient?: string }> = ({
  enriched,
  recipient,
}) => {
  const email = validOutreachEmail(enriched);
  const subject = email?.subject;
  const body = email?.body;

  if (!subject || !body) {
    return (
      <InertSection
        title="Outreach email"
        note="Full draft not available yet — use the opener above."
      />
    );
  }

  return (
    <div className="brief-section">
      <p className="brief-title">Outreach email</p>
      <div className="email-headers">
        {/* The recipient echoes what the user typed into the form. That is not a
            derivation of model output — it is their own input, shown back. */}
        {recipient && (
          <div className="email-header-row">
            <span className="email-header-key">To</span>
            <span className="email-header-value">{recipient}</span>
          </div>
        )}
        <div className="email-header-row">
          <span className="email-header-key">Subject</span>
          <span className="email-header-value">{subject}</span>
        </div>
      </div>
      <p className="email-body">{body}</p>
      <button
        className="secondary"
        style={{ marginTop: 10, fontSize: 12, padding: '4px 8px' }}
        onClick={() => navigator.clipboard?.writeText(`Subject: ${subject}\n\n${body}`)}
      >
        Copy email
      </button>
    </div>
  );
};

const CRM_FIELD_LABELS: Array<[string, string]> = [
  ['deal_name', 'Deal name'],
  ['contact_role', 'Contact role'],
  ['signal', 'Signal'],
  ['pain_point', 'Pain point'],
  ['pipeline', 'Pipeline'],
];

const CrmEntrySection: React.FC<{ enriched: EnrichedPreview }> = ({ enriched }) => {
  const entry = enriched.crm_entry;
  const fields =
    entry && typeof entry === 'object' && !Array.isArray(entry)
      ? CRM_FIELD_LABELS.map(([key, label]) => [label, text((entry as any)[key])] as const).filter(
          (pair): pair is readonly [string, string] => pair[1] !== null,
        )
      : [];

  if (fields.length === 0) {
    return <InertSection title="CRM entry" note="Field mapping preview not available yet." />;
  }

  return (
    <div className="brief-section">
      {/* Display-only. This feature does not change /api/leads/push or the CRM
          adapters, so this shows what the model proposes, not what will be sent. */}
      <p className="brief-title">CRM entry (preview)</p>
      <div className="crm-grid">
        {fields.map(([label, value]) => (
          <div className="crm-field" key={label}>
            <p className="crm-key">{label}</p>
            <p className="crm-value">{value}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

const BriefSections: React.FC<{ enriched: EnrichedPreview; recipient?: string }> = ({
  enriched,
  recipient,
}) => (
  <div style={{ marginTop: 16 }}>
    <BuyingSignalSection enriched={enriched} />
    <ContactConfidenceSection enriched={enriched} />
    <OutreachEmailSection enriched={enriched} recipient={recipient} />
    <CrmEntrySection enriched={enriched} />
  </div>
);

export const Preview: React.FC<PreviewProps> = ({ data, enriched }) => {
  if (enriched) {
    const snapshot = enriched.company_snapshot || 'No snapshot';
    const opener = enriched.personalized_opener || 'No opener';
    const tasks = enriched.follow_ups || [];
    const model = enriched.model_used || (enriched.mock ? 'mock' : 'unknown');

    return (
      <>
        <h3>AI Preview{enriched.mock ? ' (mock)' : ''} · {model}</h3>

        <div style={{ marginBottom: 16 }}>
          <strong>Company Snapshot</strong>
          <p style={{ color: 'var(--muted)', margin: '4px 0 0' }}>{snapshot}</p>
        </div>

        {/* The full outreach email supersedes the opener when there is one: they
            are two openings for the same lead, and showing both invites the user
            to send a message that contradicts the one below it. When the email is
            absent the card stays, which is also what keeps the inert email
            block's "use the opener above" copy true. */}
        {!validOutreachEmail(enriched) && (
          <div style={{ marginBottom: 16 }}>
            <strong>Suggested Opener</strong>
            <div className="card" style={{ background: 'var(--bg)', marginTop: 4, fontStyle: 'italic' }}>
              {opener}
              <button
                className="secondary"
                style={{ marginTop: 8, fontSize: 12, padding: '4px 8px' }}
                onClick={() => navigator.clipboard?.writeText(opener)}
              >
                Copy
              </button>
            </div>
          </div>
        )}

        <div>
          <strong>Follow-up Plan (3 tasks)</strong>
          {tasks.map((t: any, i: number) => (
            <div key={i} className="task">
              <div>
                <strong>{t.title}</strong>{' '}
                <span style={{ color: 'var(--accent3)' }}>(+{t.due_in_days} days)</span>
              </div>
              {t.description && (
                <div style={{ fontSize: 13, color: 'var(--text)' }}>{t.description}</div>
              )}
              <div style={{ fontSize: 13, color: 'var(--muted)' }}>{t.rationale}</div>
            </div>
          ))}
          <div className="stub-note">
            Personalized using memory {enriched.memory_note ? `(${enriched.memory_note})` : '(stub)'} · Matches T010/T013 shape
          </div>
        </div>

        <BriefSections enriched={enriched} recipient={data?.contact_name} />
      </>
    );
  }

  // Fallback stub for pre-T013 skeleton / no generate (compat with T012 conn etc)
  const company = data?.company_name || 'Acme';
  const contact = data?.contact_name || 'Jane';
  const role = data?.contact_role || 'Decision Maker';
  const signal = data?.signal || 'recent trigger';
  const pain = data?.pain_point || 'process friction';

  const snapshot = `${company} appears to be scaling after ${signal}. Key decision maker: ${contact} (${role}).`;
  const opener = `Hi ${contact.split(' ')[0]}, saw the ${signal} at ${company} — thought this might help with ${pain.toLowerCase()}.`;
  const tasks = [
    { title: 'Follow-up 1 — Check + Connect', due: '+4 days', rationale: 'Prompt timing after initial signal.' },
    { title: 'Follow-up 2 — Short Bump', due: '+9 days', rationale: 'Keep momentum without pressure.' },
    { title: 'Follow-up 3 — Close the Loop', due: '+14 days', rationale: 'Address pain point directly.' },
  ];

  return (
    <>
      <h3>AI Preview (stub — real via /enrich in T013)</h3>

      <div style={{ marginBottom: 16 }}>
        <strong>Company Snapshot</strong>
        <p style={{ color: 'var(--muted)', margin: '4px 0 0' }}>{snapshot}</p>
      </div>

      <div style={{ marginBottom: 16 }}>
        <strong>Suggested Opener</strong>
        <div className="card" style={{ background: 'var(--bg)', marginTop: 4, fontStyle: 'italic' }}>
          {opener}
          <button
            className="secondary"
            style={{ marginTop: 8, fontSize: 12, padding: '4px 8px' }}
            onClick={() => navigator.clipboard?.writeText(opener)}
          >
            Copy
          </button>
        </div>
      </div>

      <div>
        <strong>Follow-up Plan (3 tasks)</strong>
        {tasks.map((t, i) => (
          <div key={i} className="task">
            <div><strong>{t.title}</strong> <span style={{ color: 'var(--accent3)' }}>({t.due})</span></div>
            <div style={{ fontSize: 13, color: 'var(--muted)' }}>{t.rationale}</div>
          </div>
        ))}
        <div className="stub-note">Personalized using memory (stub) · Regenerate will be added later</div>
      </div>
    </>
  );
};
