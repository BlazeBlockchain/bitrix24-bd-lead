import React from 'react';
import { useAppStore } from '../stores/appStore';
import { pushLead, type LeadPushInput } from '../api/client';
import { Preview } from './Preview';

export const Composer: React.FC = () => {
  const {
    draft,
    setDraft,
    resetDraft,
    currentProvider,
    demoToken,
    setLastResult,
    addToHistory,
    isLoggedIn,
  } = useAppStore();

  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [result, setResult] = React.useState<any>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setDraft({ [name]: value } as any);
  };

  const buildInput = (): LeadPushInput => ({
    company_name: draft.company_name || 'Acme Corp',
    deal_name: draft.deal_name || `${draft.company_name || 'Acme'} Intro Deal`,
    contact_name: draft.contact_name || 'Jane Doe',
    contact_role: draft.contact_role || 'Head of Growth',
    signal: draft.signal,
    signal_type: 'new_launch',
    pain_point: draft.pain_point,
    email_subject: `Intro to ${draft.company_name || 'Acme'}`,
    notes: draft.notes,
  });

  const handlePush = async () => {
    if (!isLoggedIn) {
      alert('Stub login first (use Login button in header).');
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);

    const input = buildInput();

    try {
      const res = await pushLead(input, currentProvider, demoToken || undefined);
      setResult(res);
      setLastResult(res);
      addToHistory({ input, result: res, provider: currentProvider });
    } catch (e: any) {
      setError(e.message || 'Push failed. Is backend running on :8000? Check token/provider.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    resetDraft();
    setResult(null);
    setError(null);
  };

  // Preview always reflects current draft (stub "Generate with AI" is instant client-side for skeleton)
  const previewData = buildInput();

  return (
    <div className="main-content">
      <div className="stub-note">
        Skeleton: "Generate with AI" is stub (instant preview from form). Push calls real /api/leads/push stub (creates in CRM via backend CrmClient).
        Backend must be up (docker compose or uvicorn). Use Connections to set provider/token for demo.
      </div>

      <div className="split">
        {/* Form */}
        <div className="card">
          <h2>Lead Composer</h2>
          <div className="form-grid">
            <div>
              <label>Company name *</label>
              <input name="company_name" value={draft.company_name} onChange={handleChange} placeholder="Acme Inc" />
            </div>
            <div>
              <label>Deal / Opportunity name *</label>
              <input name="deal_name" value={draft.deal_name} onChange={handleChange} placeholder="Intro deal" />
            </div>
            <div className="form-row">
              <div>
                <label>Contact name *</label>
                <input name="contact_name" value={draft.contact_name} onChange={handleChange} placeholder="Jane Smith" />
              </div>
              <div>
                <label>Role *</label>
                <input name="contact_role" value={draft.contact_role} onChange={handleChange} placeholder="VP Sales" />
              </div>
            </div>
            <div>
              <label>Signal / Trigger</label>
              <input name="signal" value={draft.signal} onChange={handleChange} placeholder="Series B, new leadership..." />
            </div>
            <div>
              <label>Pain point / Why now</label>
              <input name="pain_point" value={draft.pain_point} onChange={handleChange} />
            </div>
            <div>
              <label>Notes (bullets ok)</label>
              <textarea name="notes" value={draft.notes} onChange={handleChange} rows={3} />
            </div>
          </div>

          <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
            <button onClick={handlePush} disabled={loading || !draft.company_name}>
              {loading ? 'Pushing to CRM...' : 'Push to CRM (stub)'}
            </button>
            <button type="button" className="secondary" onClick={handleReset}>Reset</button>
          </div>

          {error && <div className="status" style={{ color: 'var(--danger)', marginTop: 8 }}>{error}</div>}
          {result && (
            <div style={{ marginTop: 12 }}>
              <div className="status" style={{ borderColor: 'var(--accent-3)' }}>
                ✅ Success. See Preview + Result below.
              </div>
              <div className="result" style={{ marginTop: 8 }}>
                {JSON.stringify(result, null, 2)}
              </div>
            </div>
          )}
        </div>

        {/* Preview pane (right) */}
        <div className="card preview">
          <Preview data={previewData} />
        </div>
      </div>
    </div>
  );
};
