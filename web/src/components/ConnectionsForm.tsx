import React, { useState, useEffect } from 'react';
import { useAppStore, type Provider } from '../stores/appStore';
import {
  connectBitrix24,
  testBitrix24Connection,
  connectHubSpot,
  testHubSpotConnection,
  getConnections,
  type ConnectionResponse,
  type ConnectionListResponse,
} from '../api/client';

/**
 * Connections form (T012).
 * Real OAuth/webhook validation, encrypted storage via backend.
 * Supports: Bitrix24 webhook + HubSpot private app token.
 * State: stored connections fetched from backend + local input for new connections.
 */
export const ConnectionsForm: React.FC = () => {
  const { currentProvider, setProvider, demoToken, setDemoToken, isLoggedIn } = useAppStore();

  const [connections, setConnections] = useState<ConnectionResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [testLoading, setTestLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Load stored connections on mount
  useEffect(() => {
    if (isLoggedIn) {
      loadConnections();
    }
  }, [isLoggedIn]);

  const loadConnections = async () => {
    try {
      const data: ConnectionListResponse = await getConnections();
      setConnections(data.connections || []);
      setLoadError(null);
    } catch (err) {
      // Distinguish "the list is genuinely empty" from "we could not read it".
      // Rendering a failed read as an empty list previously made an expired
      // session look like a lost CRM connection.
      console.debug('Failed to load connections:', err);
      setConnections([]);
      setLoadError(err instanceof Error ? err.message : 'Could not load your connections.');
    }
  };

  const handleConnect = async () => {
    if (!isLoggedIn) {
      window.location.href = '/login';
      return;
    }

    if (!demoToken.trim()) {
      setMessage({ type: 'error', text: 'Please enter a token/URL' });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      let result;
      if (currentProvider === 'bitrix24') {
        result = await connectBitrix24(demoToken.trim());
      } else {
        result = await connectHubSpot(demoToken.trim());
      }

      setConnections((prev) => {
        const filtered = prev.filter((c) => c.provider !== result.provider);
        return [...filtered, result];
      });

      setMessage({ type: 'success', text: `Connected ${result.provider}!` });
      setDemoToken(''); // Clear input after successful store
    } catch (err) {
      setMessage({ type: 'error', text: `Failed to connect: ${(err as Error).message}` });
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async () => {
    if (!isLoggedIn) {
      window.location.href = '/login';
      return;
    }

    // Test stored connection (no input needed)
    setTestLoading(true);
    setMessage(null);

    try {
      let result;
      if (currentProvider === 'bitrix24') {
        result = await testBitrix24Connection();
      } else {
        result = await testHubSpotConnection();
      }

      if (result.connected) {
        setMessage({ type: 'success', text: `Connection test passed for ${currentProvider}!` });
        // Reload to show updated validation timestamp
        await loadConnections();
      } else {
        setMessage({ type: 'error', text: `Connection test failed: ${result.reason}` });
      }
    } catch (err) {
      setMessage({ type: 'error', text: `Test error: ${(err as Error).message}` });
    } finally {
      setTestLoading(false);
    }
  };

  const storedConnection = connections.find((c) => c.provider === currentProvider);

  return (
    <div className="main-content">
      <div className="card" style={{ maxWidth: 620 }}>
        <h2>Connections</h2>

        <div style={{ marginBottom: 16 }}>
          <label>Active CRM Provider</label>
          <select
            value={currentProvider}
            onChange={(e) => setProvider(e.target.value as Provider)}
          >
            <option value="bitrix24">Bitrix24 (webhook URL)</option>
            <option value="hubspot">HubSpot (private app token)</option>
          </select>
        </div>

        <div style={{ marginBottom: 16 }}>
          <label>
            {currentProvider === 'bitrix24' ? 'Bitrix24 Inbound Webhook URL' : 'HubSpot Private App Access Token'}
          </label>
          <input
            type="password"
            value={demoToken}
            onChange={(e) => setDemoToken(e.target.value)}
            placeholder={currentProvider === 'bitrix24' ? 'https://your.bitrix24.com/rest/1/xxxx/' : 'pat-na1-...'}
            disabled={loading}
          />
          <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>
            Paste your token here. Will be encrypted and stored on the server.
          </div>
        </div>

        {message && (
          <div
            style={{
              marginBottom: 16,
              padding: '8px 12px',
              borderRadius: 4,
              backgroundColor: message.type === 'success' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
              color: message.type === 'success' ? '#22c55e' : '#ef4444',
              fontSize: 13,
            }}
          >
            {message.text}
          </div>
        )}

        <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
          <button
            onClick={handleConnect}
            disabled={loading || !isLoggedIn}
            style={{
              opacity: loading || !isLoggedIn ? 0.6 : 1,
              cursor: loading || !isLoggedIn ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Connecting...' : 'Save Connection'}
          </button>
          <button
            onClick={handleTest}
            className="secondary"
            disabled={testLoading || !storedConnection || !isLoggedIn}
            style={{
              opacity: testLoading || !storedConnection || !isLoggedIn ? 0.6 : 1,
              cursor: testLoading || !storedConnection || !isLoggedIn ? 'not-allowed' : 'pointer',
            }}
          >
            {testLoading ? 'Testing...' : 'Test Connection'}
          </button>
          <button
            onClick={() => setDemoToken('')}
            className="secondary"
          >
            Clear Input
          </button>
        </div>

        <div style={{ marginTop: 20, fontSize: 13, color: 'var(--muted)' }}>
          <strong>Bitrix24 instructions:</strong> In Bitrix24 → Applications → Webhooks → Add inbound → enable CRM + Tasks → copy URL here.
          <br />
          <strong>HubSpot:</strong> Create private app with crm.objects.* + tasks scopes. Copy access token here.
        </div>
      </div>

      {storedConnection && (
        <div className="card">
          <h3>Stored Connection: {storedConnection.provider}</h3>
          <p>
            <strong>Status:</strong> {storedConnection.connected ? '✓ Connected' : '⊘ Not validated'}
          </p>
          <p>
            <strong>Credential:</strong> {storedConnection.masked_credential}
          </p>
          <p>
            <strong>Added:</strong> {storedConnection.created_at ? new Date(storedConnection.created_at).toLocaleDateString() : 'Unknown'}
          </p>
          {storedConnection.last_validated_at && (
            <p>
              <strong>Last tested:</strong> {new Date(storedConnection.last_validated_at).toLocaleString()}
            </p>
          )}
        </div>
      )}

      <div className="card">
        <h3>All Connections{loadError ? '' : ` (${connections.length})`}</h3>
        {loadError ? (
          <p style={{ color: 'var(--danger)' }}>
            {loadError} Your stored credentials are safe — this page just could not read them.
          </p>
        ) : connections.length === 0 ? (
          <p style={{ color: 'var(--muted)' }}>No connections stored yet. Add one above.</p>
        ) : (
          <ul style={{ fontSize: 12, lineHeight: 1.6 }}>
            {connections.map((c) => (
              <li key={c.id}>
                <strong>{c.provider}</strong> {c.connected ? '✓' : '⊘'} {c.masked_credential}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};
