import React from 'react';

interface PreviewProps {
  data: {
    company_name: string;
    contact_name: string;
    contact_role: string;
    signal?: string;
    pain_point?: string;
    notes?: string;
  };
}

/**
 * Preview component stub matching UI_UX: shows snapshot, opener, follow-up plan (3 tasks).
 * No real AI yet (T013 will call /enrich when available). Uses simple templated preview for skeleton.
 */
export const Preview: React.FC<PreviewProps> = ({ data }) => {
  const company = data.company_name || 'Acme';
  const contact = data.contact_name || 'Jane';
  const role = data.contact_role || 'Decision Maker';
  const signal = data.signal || 'recent trigger';
  const pain = data.pain_point || 'process friction';

  // Stub "AI" output (mirrors tool.ts cadence + UI_UX expectation)
  const snapshot = `${company} appears to be scaling after ${signal}. Key decision maker: ${contact} (${role}).`;
  const opener = `Hi ${contact.split(' ')[0]}, saw the ${signal} at ${company} — thought this might help with ${pain.toLowerCase()}.`;
  const tasks = [
    { title: 'Follow-up 1 — Check + Connect', due: '+4 days', rationale: 'Prompt timing after initial signal.' },
    { title: 'Follow-up 2 — Short Bump', due: '+9 days', rationale: 'Keep momentum without pressure.' },
    { title: 'Follow-up 3 — Close the Loop', due: '+14 days', rationale: 'Address pain point directly.' },
  ];

  return (
    <>
      <h3>AI Preview (stub — will use backend LLM in T007/T013)</h3>

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
            <div><strong>{t.title}</strong> <span style={{ color: 'var(--accent-3)' }}>({t.due})</span></div>
            <div style={{ fontSize: 13, color: 'var(--muted)' }}>{t.rationale}</div>
          </div>
        ))}
        <div className="stub-note">Personalized using memory (stub) · Regenerate will be added later</div>
      </div>
    </>
  );
};
