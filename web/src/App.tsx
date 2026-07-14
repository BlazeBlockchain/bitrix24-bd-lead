import { BrowserRouter, Routes, Route, NavLink, Link } from 'react-router-dom';
import { useAppStore } from './stores/appStore';
import { Dashboard } from './components/Dashboard';
import { Composer } from './components/Composer';
import { ConnectionsForm } from './components/ConnectionsForm';
import { HistoryList } from './components/HistoryList';
import { MemoryProfile } from './components/MemoryProfile';
import { UsageView } from './components/UsageView';
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
        <NavLink to="/usage" className={({ isActive }) => isActive ? 'active' : ''}>Usage</NavLink>
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

function UsagePage() {
  const { isLoggedIn, login } = useAppStore();
  return (
    <div className="page">
      <h1>Usage & Budget</h1>
      {!isLoggedIn ? (
        <div className="card">
          <p>Please sign in to view your usage and budget information.</p>
          <button onClick={login}>Sign in (stub)</button>
        </div>
      ) : (
        <UsageView />
      )}
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

      <div className="card">
        <h2>Usage & Budget</h2>
        <p>View your API usage and daily budget consumption.</p>
        <Link to="/usage"><button>View Usage →</button></Link>
      </div>

      <div className="stub-note">Additional settings coming soon.</div>
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
        <Route path="/usage" element={<UsagePage />} />
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
