import React from 'react';
import type { EnrichedPreview } from '../api/client';

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
 * Sections the design specifies but the enrichment contract does not populate.
 *
 * Rendered inert on purpose: styled in the product's visual language, labelled
 * unavailable, and never filled with invented values. Deliberately not a
 * spinner or skeleton — those imply data is on its way. This is a permanent,
 * honest "not yet", which keeps the AI output trustworthy.
 */
const INERT_SECTIONS = [
  { title: 'Buying signal', note: 'Source and date not available yet.' },
  { title: 'Contact confidence', note: 'Verification not available yet.' },
  { title: 'Outreach email', note: 'Full draft not available yet — use the opener above.' },
  { title: 'CRM entry', note: 'Field mapping preview not available yet.' },
];

const InertSections: React.FC = () => (
  <div style={{ marginTop: 16 }}>
    {INERT_SECTIONS.map(({ title, note }) => (
      <div key={title} className="inert" role="note" aria-label={`${title}: not available yet`}>
        <p className="inert-title">{title}</p>
        <p className="inert-note">{note}</p>
      </div>
    ))}
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

        <InertSections />
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
