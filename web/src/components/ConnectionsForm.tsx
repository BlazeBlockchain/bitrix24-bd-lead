import React from 'react';
import { useAppStore, type Provider } from '../stores/appStore';

/**
 * Connections form stub (T012). No real OAuth/webhook validation yet.
 * Demo: select provider + paste token (sent as ?token to /push stub).
 * Matches UI_UX: cards for providers, instructions.
 */
export const ConnectionsForm: React.FC = () => {
  const { currentProvider, setProvider, demoToken, setDemoToken, isLoggedIn } = useAppStore();

  const handleTest = () => {
    if (!isLoggedIn) {
      alert('Login (stub) first.');
      return;
    }
    alert(`(Stub) Would test connection for ${currentProvider} with token length ${demoToken.length || 0}. Backend health separate.`);
  };

  return (
    <div className="main-content">
      <div className="stub-note">Stub only. Real connect flows + encryption in T006/T012. Token here used only for demo push calls.</div>

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
            type="text"
            value={demoToken}
            onChange={(e) => setDemoToken(e.target.value)}
            placeholder={currentProvider === 'bitrix24' ? 'https://your.bitrix24.com/rest/1/xxxx/' : 'pat-na1-...'}
          />
          <div className="stub-note" style={{ marginTop: 4 }}>
            Paste your sandbox token here for demo pushes. Stored only in-memory for this session.
          </div>
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={handleTest} className="secondary">Test Connection (stub)</button>
          <button onClick={() => setDemoToken('')}>Clear</button>
        </div>

        <div style={{ marginTop: 20, fontSize: 13, color: 'var(--muted)' }}>
          <strong>Bitrix24 instructions (stub):</strong> In Bitrix24 → Applications → Webhooks → Add inbound → enable CRM + Tasks → copy URL.
          <br />
          <strong>HubSpot:</strong> Create private app with crm.objects.* + tasks scopes. Copy token.
        </div>
      </div>

      <div className="card">
        Current selection: <strong>{currentProvider}</strong> {demoToken ? '(token set)' : '(no token; may use backend .env)'}
      </div>
    </div>
  );
};
