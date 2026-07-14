import React from 'react';
import { useAppStore } from '../stores/appStore';
import { getHistory, enrichLead } from '../api/client';

/**
 * T014: History page - list + detail of past leads (from GET /api/leads/history per T010),
 * persisted via T009 Lead model. "Use similar" pre-fills Composer (T013) with lead data/signal/company
 * and/or re-calls enrich.
 * Uses web patterns: Zustand, protected (via backend), native fetch.
 * List shows: company, contact, date, crm ids, brief signal.
 * Click/detail: full enriched (snapshot, opener, tasks) + CRM outcome (ids + provider).
 * Decision: simple limit=20 (no advanced pagination yet; documented for others).
 * Shapes shared: server history item = {id, company_name, contact_name, created_at, crm_*, signal, enriched?}
 * use-similar contract: applyLeadToDraft(leadItem) => sets draft fields + provider; optionally await enrich.
 * Integrates with Dashboard T015 (recent from store/serverHistory).
 * No breakage to T013 Composer (enhances generate) or /push /enrich API shapes.
 */
export const HistoryList: React.FC = () => {
  const { history: localHistory, setDraft, setProvider, serverHistory, setServerHistory, isLoggedIn } = useAppStore();
  const [loading, setLoading] = React.useState(false);
  const [selected, setSelected] = React.useState<any>(null); // detail item
  const [error, setError] = React.useState<string | null>(null);

  // Fetch server history (T014). Falls back gracefully.
  const loadHistory = React.useCallback(async () => {
    if (!isLoggedIn) return;
    setLoading(true);
    setError(null);
    try {
      const items = await getHistory(20);
      setServerHistory(items);
    } catch (e: any) {
      setError('Could not load server history (using local). Backend up?');
      // keep prior
    } finally {
      setLoading(false);
    }
  }, [isLoggedIn, setServerHistory]);

  React.useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  // Combined for display: prefer server (persisted), fallback local for this session
  const displayItems = React.useMemo(() => {
    if (serverHistory && serverHistory.length > 0) return serverHistory;
    // map local to similar shape for unified render
    return localHistory.map((h: any) => ({
      id: h.id,
      company_name: h.input?.company_name,
      contact_name: h.input?.contact_name,
      created_at: h.timestamp,
      crm_provider: h.provider,
      crm_contact_id: h.result?.contact_id,
      crm_deal_id: h.result?.deal_id,
      signal: h.input?.signal,
      _local: true,
      _raw: h,
    }));
  }, [serverHistory, localHistory]);

  // "Use similar" action (T014 contract): prefill Composer form with lead's data (or signal/company)
  // and/or call enrich again. Then hint navigate to /new.
  const applySimilar = async (item: any) => {
    const isServer = !item._local;
    const inp = isServer ? item : (item._raw?.input || {});
    const provider = item.crm_provider || item.provider || 'bitrix24';

    setDraft({
      company_name: inp.company_name || item.company_name || '',
      deal_name: (inp.deal_name || `${inp.company_name || item.company_name || 'Lead'} Intro Deal`),
      contact_name: inp.contact_name || item.contact_name || '',
      contact_role: inp.contact_role || item.contact_role || '',
      signal: inp.signal || item.signal || '',
      pain_point: inp.pain_point || '',
      notes: inp.notes || '',
    });
    setProvider(provider);

    // Optionally re-enrich for fresh preview (uses signal/company etc from history)
    try {
      if (isLoggedIn) {
        const enrichInput = {
          company_name: inp.company_name || item.company_name || '',
          deal_name: (inp.deal_name || `${inp.company_name || item.company_name || 'Lead'} Intro Deal`),
          contact_name: inp.contact_name || item.contact_name || '',
          contact_role: inp.contact_role || item.contact_role || '',
          signal: inp.signal || item.signal || '',
          pain_point: inp.pain_point || '',
          notes: inp.notes || '',
        };
        // fire-and-forget; Composer will see draft updated
        enrichLead(enrichInput).catch(() => {});
      }
    } catch {}

    // Navigate hint to composer (matches skeleton routing)
    window.location.hash = '';
    window.location.href = '/new';
    // alert kept minimal; in real would use toast/navigate
  };

  const showDetail = (item: any) => {
    setSelected(item);
  };

  const closeDetail = () => setSelected(null);

  const enriched = selected?.enriched || (selected?._raw?.result?.enriched_preview) || {};

  return (
    <div className="main-content">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>History</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="secondary" onClick={loadHistory} disabled={loading}>Refresh</button>
          {displayItems.length > 0 && <button className="secondary" onClick={() => { setServerHistory([]); /* local clear separate */ }}>Clear view</button>}
        </div>
      </div>

      {error && <div className="status" style={{ color: 'var(--danger)' }}>{error}</div>}
      {loading && <div className="stub-note">Loading history…</div>}

      {displayItems.length === 0 && (
        <div className="card">No past leads yet. Push via New Lead (persisted to server history).</div>
      )}

      {displayItems.map((item: any) => {
        const briefSignal = item.signal || (item._raw?.input?.signal) || '—';
        const dateStr = item.created_at ? new Date(item.created_at).toLocaleString() : '—';
        const crm = `${item.crm_provider || '—'} • c:${item.crm_contact_id || '?'} d:${item.crm_deal_id || '?'}`;
        return (
          <div key={item.id} className="card" style={{ marginBottom: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div onClick={() => showDetail(item)} style={{ cursor: 'pointer', flex: 1 }}>
                <strong>{item.company_name || 'Unknown'}</strong> — {item.contact_name || '—'}
                <div style={{ fontSize: 12, color: 'var(--muted)' }}>
                  {dateStr} · {crm}
                </div>
                <div style={{ fontSize: 12, marginTop: 4 }}>Signal: {briefSignal}</div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'flex-end' }}>
                <button className="secondary" onClick={() => applySimilar(item)} style={{ fontSize: 12, padding: '4px 10px' }}>
                  Use similar
                </button>
                <button onClick={() => showDetail(item)} style={{ fontSize: 11 }}>Detail</button>
              </div>
            </div>
          </div>
        );
      })}

      {/* Detail view (inline, shows full enriched snapshot/opener/tasks + CRM outcome) */}
      {selected && (
        <div className="card" style={{ border: '2px solid var(--accent)', marginTop: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <h3>Lead Detail: {selected.company_name}</h3>
            <button className="secondary" onClick={closeDetail}>Close</button>
          </div>
          <div style={{ fontSize: 12, color: 'var(--muted)' }}>
            {selected.created_at ? new Date(selected.created_at).toLocaleString() : ''} · Provider: {selected.crm_provider || selected.provider}
          </div>

          <div style={{ margin: '12px 0' }}>
            <strong>CRM Outcome:</strong> Contact {selected.crm_contact_id || '—'} | Deal {selected.crm_deal_id || '—'}
            <div style={{ fontSize: 12 }}>Pushed via {selected.crm_provider || 'CRM'}. (Full outcomes via outreach_history later.)</div>
          </div>

          {enriched.company_snapshot && (
            <div>
              <strong>Company Snapshot</strong>
              <p>{enriched.company_snapshot}</p>
            </div>
          )}
          {enriched.personalized_opener && (
            <div>
              <strong>Personalized Opener</strong>
              <p style={{ fontStyle: 'italic' }}>{enriched.personalized_opener}</p>
            </div>
          )}

          <div>
            <strong>Follow-up Tasks</strong>
            <ul style={{ paddingLeft: 18 }}>
              {(enriched.follow_ups || []).map((t: any, i: number) => (
                <li key={i}>
                  {t.title} (due +{t.due_in_days || (i===0?4:i===1?9:14)}d) — {t.rationale || t.description}
                </li>
              ))}
              {(!enriched.follow_ups || enriched.follow_ups.length === 0) && selected._raw && (
                <>
                  <li>Task1: {selected._raw.result?.task1?.id} on {selected._raw.result?.task1?.date}</li>
                  <li>Task2: {selected._raw.result?.task2?.id} on {selected._raw.result?.task2?.date}</li>
                  <li>Task3: {selected._raw.result?.task3?.id} on {selected._raw.result?.task3?.date}</li>
                </>
              )}
            </ul>
          </div>

          <button onClick={() => applySimilar(selected)} style={{ marginTop: 8 }}>Use similar (prefill + enrich)</button>
          <div className="stub-note" style={{ marginTop: 8 }}>Full enriched from push snapshot. Use similar pre-fills form data (T013) + re-enriches.</div>
        </div>
      )}

      <div className="stub-note">Server-backed via GET /api/leads/history (T010). Persisted on successful push. Local session items shown if no server rows. Decision: limit pagination (20). Shapes + use-similar contract in REVIEW_FOR_T014.md.</div>
    </div>
  );
};
