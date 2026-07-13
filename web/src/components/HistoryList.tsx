import React from 'react';
import { useAppStore } from '../stores/appStore';

/**
 * History list stub (T014). Local only for skeleton.
 * Shows past pushes + "use similar" to prefill draft (simple).
 */
export const HistoryList: React.FC = () => {
  const { history, clearHistory, setDraft, setProvider } = useAppStore();

  const applySimilarFromHistory = (item: any) => {
    const inp = item.input || {};
    setDraft({
      company_name: inp.company_name || '',
      deal_name: inp.deal_name || '',
      contact_name: inp.contact_name || '',
      contact_role: inp.contact_role || '',
      signal: inp.signal || '',
      pain_point: inp.pain_point || '',
      notes: inp.notes || '',
    });
    if (item.provider) setProvider(item.provider);
    window.location.hash = '#composer'; // hint, or use navigate if in route
    alert('Draft pre-filled from history item. Go to New Lead to push again.');
  };

  return (
    <div className="main-content">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>History (stub — local only)</h2>
        {history.length > 0 && <button className="secondary" onClick={clearHistory}>Clear</button>}
      </div>

      {history.length === 0 && (
        <div className="card">No leads yet. Use the Composer to push one (results appear here).</div>
      )}

      {history.map((item) => (
        <div key={item.id} className="card" style={{ marginBottom: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <div>
              <strong>{item.input?.company_name || 'Unknown'}</strong> — {item.input?.contact_name}
              <div style={{ fontSize: 12, color: 'var(--muted)' }}>
                {new Date(item.timestamp).toLocaleString()} · {item.provider}
              </div>
            </div>
            <button className="secondary" onClick={() => applySimilarFromHistory(item)} style={{ fontSize: 12, padding: '4px 10px' }}>
              Use similar
            </button>
          </div>
          <div style={{ marginTop: 8, fontSize: 12 }}>
            Contact: {item.result?.contact_id} | Deal: {item.result?.deal_id} | Tasks: {item.result?.task1?.id}, {item.result?.task2?.id}, {item.result?.task3?.id}
          </div>
        </div>
      ))}

      <div className="stub-note">Full server history + detail modals + filters in T014 after DB + /leads/history API.</div>
    </div>
  );
};
