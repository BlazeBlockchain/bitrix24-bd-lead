/**
 * Usage View Component (T025).
 *
 * Displays:
 * - Today's spend vs daily budget (bar chart or progress bar)
 * - Total calls and tokens
 * - Recent usage history (last N calls with model + cost)
 *
 * Read-only display of UsageLedger data from backend /api/usage/* endpoints.
 */

import { useEffect, useState } from 'react';
import type { UsageSummaryResponse, UsageHistoryResponse } from '../api/client';
import { getUsageSummary, getUsageHistory } from '../api/client';

export function UsageView() {
  const [summary, setSummary] = useState<UsageSummaryResponse | null>(null);
  const [history, setHistory] = useState<UsageHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchUsageData = async () => {
      try {
        setLoading(true);
        setError(null);
        const [summaryData, historyData] = await Promise.all([
          getUsageSummary(),
          getUsageHistory(20),
        ]);
        setSummary(summaryData);
        setHistory(historyData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load usage data');
        console.error('Failed to load usage data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchUsageData();
  }, []);

  if (loading) {
    return (
      <div className="card">
        <p>Loading usage data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card" style={{ color: '#ff9999' }}>
        <p>Error: {error}</p>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="card">
        <p>No usage data available.</p>
      </div>
    );
  }

  const budgetPercent = summary.daily_budget_cents > 0
    ? (summary.today_cost_cents / summary.daily_budget_cents) * 100
    : 0;
  const budgetStatus = summary.remaining_budget_cents > 0 ? 'ok' : 'exceeded';

  return (
    <div className="usage-view">
      {/* Budget Card */}
      <div className="card">
        <h2>Daily Budget</h2>
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 14, marginBottom: 6 }}>
            <strong>${(summary.today_cost_cents / 100).toFixed(2)}</strong> of{' '}
            <strong>${(summary.daily_budget_cents / 100).toFixed(2)}</strong> spent today
          </div>
          <div
            style={{
              width: '100%',
              height: 16,
              backgroundColor: '#333',
              borderRadius: 4,
              overflow: 'hidden',
              border: '1px solid #555',
            }}
          >
            <div
              style={{
                width: `${Math.min(budgetPercent, 100)}%`,
                height: '100%',
                backgroundColor: budgetStatus === 'exceeded' ? '#ff6b6b' : '#4ecdc4',
                transition: 'width 0.3s ease',
              }}
            />
          </div>
          <div style={{ fontSize: 12, marginTop: 6, opacity: 0.8 }}>
            Remaining: ${(summary.remaining_budget_cents / 100).toFixed(2)}
          </div>
        </div>
      </div>

      {/* Stats Card */}
      <div className="card">
        <h2>Cumulative Usage</h2>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 12,
          }}
        >
          <div>
            <div style={{ fontSize: 12, opacity: 0.7 }}>Total Calls</div>
            <div style={{ fontSize: 20, fontWeight: 'bold' }}>{summary.total_calls}</div>
          </div>
          <div>
            <div style={{ fontSize: 12, opacity: 0.7 }}>Total Cost</div>
            <div style={{ fontSize: 20, fontWeight: 'bold' }}>
              ${(summary.total_estimated_cost_cents / 100).toFixed(2)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 12, opacity: 0.7 }}>Input Tokens</div>
            <div style={{ fontSize: 20, fontWeight: 'bold' }}>{summary.total_input_tokens}</div>
          </div>
          <div>
            <div style={{ fontSize: 12, opacity: 0.7 }}>Output Tokens</div>
            <div style={{ fontSize: 20, fontWeight: 'bold' }}>{summary.total_output_tokens}</div>
          </div>
        </div>
      </div>

      {/* Recent Usage History */}
      {history && history.items.length > 0 && (
        <div className="card">
          <h2>Recent Calls ({history.total_count} total)</h2>
          <div style={{ fontSize: 12, marginBottom: 12 }}>
            Showing last {Math.min(history.items.length, 20)} of {history.total_count}
          </div>
          <div
            style={{
              overflowX: 'auto',
              fontSize: 12,
            }}
          >
            <table
              style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: 12,
              }}
            >
              <thead>
                <tr style={{ borderBottom: '1px solid #555' }}>
                  <th style={{ textAlign: 'left', padding: '6px 8px' }}>Model</th>
                  <th style={{ textAlign: 'right', padding: '6px 8px' }}>In Tokens</th>
                  <th style={{ textAlign: 'right', padding: '6px 8px' }}>Out Tokens</th>
                  <th style={{ textAlign: 'right', padding: '6px 8px' }}>Cost</th>
                  <th style={{ textAlign: 'left', padding: '6px 8px' }}>Date</th>
                </tr>
              </thead>
              <tbody>
                {history.items.map((item, idx) => {
                  const date = new Date(item.created_at);
                  const timeStr = date.toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                  });
                  const dateStr = date.toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                  });

                  return (
                    <tr
                      key={item.id}
                      style={{
                        borderBottom: '1px solid #333',
                        backgroundColor: idx % 2 === 0 ? '#222' : 'transparent',
                      }}
                    >
                      <td style={{ padding: '6px 8px' }}>
                        <code style={{ fontSize: 11 }}>{item.model.split('-').pop() || item.model}</code>
                      </td>
                      <td style={{ textAlign: 'right', padding: '6px 8px' }}>
                        {item.input_tokens}
                      </td>
                      <td style={{ textAlign: 'right', padding: '6px 8px' }}>
                        {item.output_tokens}
                      </td>
                      <td style={{ textAlign: 'right', padding: '6px 8px', fontWeight: 'bold' }}>
                        ${(item.estimated_cost_cents / 100).toFixed(2)}
                      </td>
                      <td style={{ padding: '6px 8px', opacity: 0.7, fontSize: 11 }}>
                        {dateStr} {timeStr}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {history && history.items.length === 0 && (
        <div className="card">
          <p style={{ opacity: 0.7 }}>No usage history yet. Generate leads or enrichments to see data here.</p>
        </div>
      )}
    </div>
  );
}
