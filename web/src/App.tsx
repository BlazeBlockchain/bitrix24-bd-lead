import { BrowserRouter, Routes, Route, NavLink, Link } from 'react-router-dom';
import { useAppStore } from './stores/appStore';
import { Dashboard } from './components/Dashboard';
import { Composer } from './components/Composer';
import { ConnectionsForm } from './components/ConnectionsForm';
import { HistoryList } from './components/HistoryList';
import { MemoryProfile } from './components/MemoryProfile';
import { UsageView } from './components/UsageView';
import { Changelog } from './components/Changelog';
import { LoginPage } from './components/LoginPage';
import { checkHealth } from './api/client';
import { getStoredToken, getStoredUser } from './api/auth';
import './App.css';
import { useState, useEffect } from 'react';

/** The bd-lead mark: bolt on the brand gradient. Mirrors design/mark.svg. */
function BdMark() {
  return (
    <span className="bd-mark" aria-hidden="true">
      <svg width="15" height="15" viewBox="0 0 128 128" fill="none">
        <path
          d="M78 16 L34 74 H57 L50 112 L94 54 H71 Z"
          fill="#fff"
          stroke="#fff"
          strokeWidth="3"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  );
}

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/new', label: 'New lead' },
  { to: '/history', label: 'History' },
  { to: '/connections', label: 'Connections' },
  { to: '/usage', label: 'Usage' },
  { to: '/memory', label: 'Memory' },
  { to: '/account', label: 'Account' },
];

function Sidebar() {
  const { isLoggedIn, user, logout, currentProvider } = useAppStore();

  return (
    <aside className="app-sidebar">
      <Link to="/" className="bd-logo">
        <BdMark />
        BD Lead
      </Link>

      {isLoggedIn && (
        <nav className="sidebar-nav">
          {NAV_ITEMS.map(({ to, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) => (isActive ? 'active' : '')}
            >
              {label}
            </NavLink>
          ))}
        </nav>
      )}

      <div className="sidebar-footer">
        {isLoggedIn && user ? (
          <>
            <span className="user-pill">{user.name} · {currentProvider}</span>
            <button className="secondary" onClick={logout}>Logout</button>
          </>
        ) : (
          <Link to="/login"><button>Sign in with Google</button></Link>
        )}
      </div>
    </aside>
  );
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isLoggedIn } = useAppStore();
  if (!isLoggedIn) {
    return (
      <div className="page" style={{ textAlign: 'center', paddingTop: 60 }}>
        <div className="card">
          <h2>Sign in required</h2>
          <p>Please sign in with Google to access this page.</p>
          <Link to="/login"><button>Sign in with Google</button></Link>
        </div>
      </div>
    );
  }
  return <>{children}</>;
}

function App() {
  const { setAuthFromToken } = useAppStore();
  const [version, setVersion] = useState<string | null>(null);
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    // Restore auth from localStorage on mount
    const token = getStoredToken();
    const user = getStoredUser();
    if (token && user) {
      setAuthFromToken(token, user);
    }
    setInitialized(true);
  }, [setAuthFromToken]);

  useEffect(() => {
    const fetchVersion = async () => {
      try {
        const health = await checkHealth();
        setVersion(health.version);
      } catch (err) {
        console.debug('Failed to fetch version:', err);
      }
    };

    fetchVersion();
  }, []);

  if (!initialized) {
    return null; // prevent flash of login page
  }

  return (
    <BrowserRouter>
      <div className="app-shell">
        <Sidebar />
        <div className="app-main">
          <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<RequireAuth><Dashboard /></RequireAuth>} />
        <Route path="/new" element={<RequireAuth><Composer /></RequireAuth>} />
        <Route path="/history" element={<RequireAuth><HistoryList /></RequireAuth>} />
        <Route path="/connections" element={<RequireAuth><ConnectionsForm /></RequireAuth>} />
        <Route path="/usage" element={<RequireAuth><UsageView /></RequireAuth>} />
        <Route path="/memory" element={<RequireAuth><MemoryProfile /></RequireAuth>} />
        <Route path="/account" element={
          <RequireAuth>
            <div className="page">
              <h1>Account</h1>
              <div className="card">
                <p>{useAppStore.getState().user?.name ?? useAppStore.getState().user?.email} &lt;{useAppStore.getState().user?.email}&gt;</p>
                <button className="secondary" onClick={() => useAppStore.getState().logout()}>Logout</button>
              </div>
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
            </div>
          </RequireAuth>
        } />
        <Route path="/changelog" element={<Changelog />} />
            <Route path="*" element={<div className="page"><p>Page not found. <Link to="/">Go home</Link></p></div>} />
          </Routes>
          <footer className="app-footer">
            {version && <>v{version} • </>}
            <Link to="/changelog">Changelog</Link>
          </footer>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
