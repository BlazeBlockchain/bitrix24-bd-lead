import { BrowserRouter, Routes, Route, NavLink, Link } from 'react-router-dom';
import { useAppStore } from './stores/appStore';
import { Composer } from './components/Composer';
import { ConnectionsForm } from './components/ConnectionsForm';
import { HistoryList } from './components/HistoryList';
import { MemoryProfile } from './components/MemoryProfile';
import './App.css';

/**
 * Web app skeleton root (T011+).
 * - React Router for basic pages matching UI_UX.md (Dashboard, New Lead/Composer, History, Connections)
 * - Stub login (no JWT yet)
 * - Zustand state
 * - Native fetch API client to backend stub
 * - Dark theme CSS vars from UI_UX
 * - Minimal for MVP; no real auth, no /enrich (uses /push directly + stub preview)
 */

function Header() {
  const { isLoggedIn, user, login, logout, currentProvider } = useAppStore();

  return (
    <header>
      <Link to="/" className="logo">BD Lead</Link>

      <nav>
        <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>Dashboard</NavLink>
        <NavLink to="/new" className={({ isActive }) => isActive ? 'active' : ''}>New Lead</NavLink>
        <NavLink to="/history" className={({ isActive }) => isActive ? 'active' : ''}>History</NavLink>
        <NavLink to="/connections" className={({ isActive }) => isActive ? 'active' : ''}>Connections</NavLink>
        <NavLink to="/memory" className={({ isActive }) => isActive ? 'active' : ''}>Memory</NavLink>
        <NavLink to="/account" className={({ isActive }) => isActive ? 'active' : ''}>Account</NavLink>
      </nav>

      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        {isLoggedIn && user ? (
          <>
            <span className="user-pill">👤 {user.name} · {currentProvider}</span>
            <button className="secondary" onClick={logout} style={{ padding: '4px 10px', fontSize: 12 }}>Logout (stub)</button>
          </>
        ) : (
          <button onClick={login}>Sign in (stub)</button>
        )}
      </div>
    </header>
  );
}

function Dashboard() {
  const { isLoggedIn, user, history, lastPushResult } = useAppStore();

  return (
    <div className="page">
      <h1>Dashboard</h1>
      {!isLoggedIn && (
        <div className="card">
          <p>Welcome to BD Lead Assistant (skeleton).</p>
          <button onClick={() => (window as any).location = '#login-hint'}>Click "Sign in (stub)" in header to start demo.</button>
        </div>
      )}

      {isLoggedIn && (
        <>
          <div className="card">
            <p>Hello, {user?.name}. Quick stats (stub): {history.length} leads pushed this session.</p>
            <p>Default provider: <strong>{useAppStore.getState().currentProvider}</strong>. Go to Connections to change.</p>
            <Link to="/new"><button>Create new lead</button></Link>
          </div>

          {lastPushResult && (
            <div className="card">
              <h2>Last push result</h2>
              <pre className="result">{JSON.stringify(lastPushResult, null, 2)}</pre>
            </div>
          )}

          <div className="card">
            <h2>Recent leads (T015 + T014)</h2>
            {(history.length > 0 || useAppStore.getState().serverHistory.length > 0) ? (
              (useAppStore.getState().serverHistory.length ? useAppStore.getState().serverHistory : history).slice(0, 3).map((h: any) => (
                <div key={h.id || h.timestamp}>{(h.company_name || h.input?.company_name)} → {(h.crm_contact_id || h.result?.contact_id)}</div>
              ))
            ) : <p>No history yet. <Link to="/history">View full history</Link></p>}
            <Link to="/history">See all history →</Link>
          </div>
        </>
      )}

      <div className="stub-note" style={{ marginTop: 24 }}>
        This is the T011 web skeleton. Full auth (T005), enrich (T007/T013), real history API later. Backend /api/leads/push exercised on push.
      </div>
    </div>
  );
}

function NewLeadPage() {
  const { isLoggedIn, login } = useAppStore();
  return (
    <div className="page">
      <h1>New Lead</h1>
      {!isLoggedIn ? (
        <div className="card">
          <p>Please sign in (stub) to use composer.</p>
          <button onClick={login}>Sign in (stub)</button>
        </div>
      ) : (
        <Composer />
      )}
    </div>
  );
}

function HistoryPage() {
  return (
    <div className="page">
      <HistoryList />
    </div>
  );
}

function ConnectionsPage() {
  const { isLoggedIn, login } = useAppStore();
  return (
    <div className="page">
      <h1>Connections</h1>
      {!isLoggedIn ? (
        <div className="card"><p>Login stub required for demo token use. <button onClick={login}>Sign in</button></p></div>
      ) : null}
      <ConnectionsForm />
    </div>
  );
}

function AccountPage() {
  const { user, logout, isLoggedIn } = useAppStore();
  return (
    <div className="page">
      <h1>Account</h1>
      {isLoggedIn && user ? (
        <div className="card">
          <p>{user.name} &lt;{user.email}&gt;</p>
          <p>Manage your account settings and preferences below.</p>
          <button className="secondary" onClick={logout}>Logout</button>
        </div>
      ) : <p>Not logged in.</p>}

      <div className="card">
        <h2>Memory Profile</h2>
        <p>Customize your personal tone, target industries, and follow-up cadence for AI-powered lead enrichment.</p>
        <Link to="/memory"><button>Edit Memory Profile →</button></Link>
      </div>

      <div className="stub-note">Usage dashboard and additional settings coming soon.</div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Header />
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/new" element={<NewLeadPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/connections" element={<ConnectionsPage />} />
        <Route path="/memory" element={<MemoryProfile />} />
        <Route path="/account" element={<AccountPage />} />
        <Route path="*" element={<div className="page"><p>Page not found. <Link to="/">Go home</Link></p></div>} />
      </Routes>
      <footer style={{ padding: '12px 24px', borderTop: '1px solid var(--border)', fontSize: 12, color: 'var(--muted)', textAlign: 'center' }}>
        BD Lead skeleton • backend http://localhost:8000 • no real auth • <a href="https://github.com" target="_blank" rel="noreferrer">docs</a>
      </footer>
    </BrowserRouter>
  );
}

export default App;
