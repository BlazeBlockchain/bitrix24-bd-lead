/**
 * Dashboard Component (T015).
 *
 * Displays:
 * - Connection status (e.g., "Connected: Bitrix24 ✓ / HubSpot (not connected)")
 * - Compact usage summary (e.g., "X calls today, $Y.YY of $Z.ZZ daily budget")
 * - Real recent leads from server history
 *
 * Fetches data on mount from backend using T012/T025/T014 APIs:
 * - getConnections() for connection status
 * - getUsageSummary() for budget/usage
 * - getHistory() for recent leads
 */

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAppStore } from '../stores/appStore';
import {
  getConnections,
  getUsageSummary,
  getHistory,
  type ConnectionListResponse,
  type UsageSummaryResponse,
} from '../api/client';

export const Dashboard: React.FC = () => {
  const { isLoggedIn, user, history: localHistory, lastPushResult, setServerHistory, serverHistory } = useAppStore();

  // Connection status state
  const [connections, setConnections] = useState<any[]>([]);
  const [connectionsLoading, setConnectionsLoading] = useState(false);
  const [connectionsError, setConnectionsError] = useState<string | null>(null);

  // Usage summary state
  const [usageSummary, setUsageSummary] = useState<UsageSummaryResponse | null>(null);
  const [usageLoading, setUsageLoading] = useState(false);
  const [usageError, setUsageError] = useState<string | null>(null);

  // History state (real server leads)
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);

  // Fetch connections status on mount
  useEffect(() => {
    const loadConnections = async () => {
      if (!isLoggedIn) return;
      setConnectionsLoading(true);
      setConnectionsError(null);
      try {
        const data: ConnectionListResponse = await getConnections();
        setConnections(data.connections || []);
      } catch (err) {
        console.debug('Failed to load connections:', err);
        setConnectionsError('Unable to load connection status');
      } finally {
        setConnectionsLoading(false);
      }
    };

    loadConnections();
  }, [isLoggedIn]);

  // Fetch usage summary on mount
  useEffect(() => {
    const loadUsage = async () => {
      if (!isLoggedIn) return;
      setUsageLoading(true);
      setUsageError(null);
      try {
        const data = await getUsageSummary();
        setUsageSummary(data);
      } catch (err) {
        console.debug('Failed to load usage summary:', err);
        setUsageError('Unable to load usage data');
      } finally {
        setUsageLoading(false);
      }
    };

    loadUsage();
  }, [isLoggedIn]);

  // Fetch history on mount (if not already in serverHistory)
  useEffect(() => {
    const loadHistory = async () => {
      if (!isLoggedIn) return;
      if (serverHistory.length > 0) return; // Already loaded
      setHistoryLoading(true);
      setHistoryError(null);
      try {
        const items = await getHistory(10); // Just recent 10 for dashboard
        setServerHistory(items);
      } catch (err) {
        console.debug('Failed to load history:', err);
        setHistoryError('Unable to load history');
      } finally {
        setHistoryLoading(false);
      }
    };

    loadHistory();
  }, [isLoggedIn, serverHistory.length, setServerHistory]);

  // Render connection status line
  const renderConnectionStatus = () => {
    if (connectionsLoading) {
      return <span style={{ opacity: 0.7 }}>Loading connection status...</span>;
    }

    if (connectionsError) {
      return (
        <span style={{ color: '#ff9999' }}>
          Unable to load connection status. <Link to="/connections">Configure</Link>
        </span>
      );
    }

    const bitrix = connections.find((c) => c.provider === 'bitrix24');
    const hubspot = connections.find((c) => c.provider === 'hubspot');

    if (connections.length === 0) {
      return (
        <span style={{ color: '#ffb366' }}>
          No CRM connected. <Link to="/connections">Connect now</Link>
        </span>
      );
    }

    return (
      <span>
        Connected:{' '}
        {bitrix && <span style={{ color: '#4ecdc4' }}>Bitrix24 ✓</span>}
        {!bitrix && <span style={{ color: '#555' }}>(Bitrix24)</span>}
        {' / '}
        {hubspot && <span style={{ color: '#4ecdc4' }}>HubSpot ✓</span>}
        {!hubspot && <span style={{ color: '#555' }}>(HubSpot)</span>}
      </span>
    );
  };

  // Render compact usage summary
  const renderUsageSummary = () => {
    if (usageLoading) {
      return <span style={{ opacity: 0.7 }}>Loading usage data...</span>;
    }

    if (usageError) {
      return (
        <span style={{ color: '#ff9999' }}>
          Unable to load usage. <Link to="/usage">View details</Link>
        </span>
      );
    }

    if (!usageSummary) {
      return <span>No usage data yet.</span>;
    }

    const todaySpend = (usageSummary.today_cost_cents / 100).toFixed(2);
    const dailyBudget = (usageSummary.daily_budget_cents / 100).toFixed(2);
    const remaining = (usageSummary.remaining_budget_cents / 100).toFixed(2);

    return (
      <span>
        {usageSummary.total_calls} calls today • ${todaySpend} of ${dailyBudget} daily budget
        {usageSummary.remaining_budget_cents > 0 ? (
          <span style={{ color: '#4ecdc4' }}> (${remaining} remaining)</span>
        ) : (
          <span style={{ color: '#ff6b6b' }}> (Budget exceeded!)</span>
        )}
        {' '}
        <Link to="/usage">Details</Link>
      </span>
    );
  };

  // Render recent leads
  const renderRecentLeads = () => {
    // Prefer server history, fallback to local
    const displayItems = serverHistory.length > 0 ? serverHistory : localHistory;

    if (historyLoading && displayItems.length === 0) {
      return <p style={{ opacity: 0.7 }}>Loading recent leads...</p>;
    }

    if (historyError && displayItems.length === 0) {
      return <p style={{ color: '#ff9999' }}>{historyError}</p>;
    }

    if (displayItems.length === 0) {
      return (
        <p>
          No leads yet. <Link to="/new">Create your first lead</Link>
        </p>
      );
    }

    return (
      <>
        {displayItems.slice(0, 3).map((item: any) => (
          <div
            key={item.id || item.timestamp}
            style={{
              padding: '8px 0',
              borderBottom: '1px solid var(--border)',
              fontSize: 14,
            }}
          >
            <strong>{item.company_name || item.input?.company_name || '(no company)'}</strong>
            {' '}
            →{' '}
            {item.crm_contact_id || item.result?.contact_id ? (
              <span style={{ color: '#4ecdc4' }}>✓ created</span>
            ) : (
              <span style={{ color: '#555' }}>(pending)</span>
            )}
            <div style={{ fontSize: 12, opacity: 0.7, marginTop: 2 }}>
              {item.contact_name || item.input?.contact_name} •{' '}
              {item.created_at ? new Date(item.created_at).toLocaleDateString() : item.timestamp ? new Date(item.timestamp).toLocaleDateString() : '(unknown date)'}
            </div>
          </div>
        ))}
        <Link to="/history" style={{ display: 'inline-block', marginTop: 12 }}>
          See all history →
        </Link>
      </>
    );
  };

  return (
    <div className="page">
      <h1>Dashboard</h1>

      {!isLoggedIn && (
        <div className="card">
          <p>Welcome to BD Lead Assistant.</p>
          <p>Sign in (stub) in the header to get started.</p>
          <p style={{ fontSize: 13, color: 'var(--accent)', fontStyle: 'italic', marginTop: 12 }}>
            Powered by our proprietary BD Lead Research engine — a battle-tested B2B research methodology that turns a company name into a complete, CRM-ready lead brief.
          </p>
        </div>
      )}

      {isLoggedIn && (
        <>
          {/* Quick summary */}
          <div className="card">
            <p>Hello, {user?.name}. Here's your dashboard.</p>
            <p style={{ fontSize: 12, color: 'var(--accent)', fontWeight: 500, marginTop: 8 }}>
              BD Lead Research Engine
            </p>
            <Link to="/new">
              <button>Create new lead</button>
            </Link>
          </div>

          {/* Connection status */}
          <div className="card">
            <h2>Connection Status</h2>
            <p>{renderConnectionStatus()}</p>
          </div>

          {/* Usage summary */}
          <div className="card">
            <h2>Usage & Budget</h2>
            <p>{renderUsageSummary()}</p>
          </div>

          {/* Recent leads */}
          <div className="card">
            <h2>Recent Leads</h2>
            {renderRecentLeads()}
          </div>

          {lastPushResult && (
            <div className="card">
              <h2>Last Push Result</h2>
              <pre className="result">{JSON.stringify(lastPushResult, null, 2)}</pre>
            </div>
          )}
        </>
      )}
    </div>
  );
};
