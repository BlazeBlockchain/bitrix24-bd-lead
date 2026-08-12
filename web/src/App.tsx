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

function Header() {
  const { isLoggedIn, user, logout, currentProvider } = useAppStore();

  return (
    <header>
      <Link to="/" className="logo">BD Lead</Link>

      <nav>
        {isLoggedIn && (
          <>
            <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>Dashboard</NavLink>
            <NavLink to="/new" className={({ isActive }) => isActive ? 'active' : ''}>New Lead</NavLink>
            <NavLink to="/history" className={({ isActive }) => isActive ? 'active' : ''}>History</NavLink>
            <NavLink to="/connections" className={({ isActive }) => isActive ? 'active' : ''}>Connections</NavLink>
            <NavLink to="/usage" className={({ isActive }) => isActive ? 'active' : ''}>Usage</NavLink>
            <NavLink to="/memory" className={({ isActive }) => isActive ? 'active' : ''}>Memory</NavLink>
            <NavLink to="/account" className={({ isActive }) => isActive ? 'active' : ''}>Account</NavLink>
          </>
        )}
      </nav>

      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        {isLoggedIn && user ? (
          <>
            <span className="user-pill">{user.name} · {currentProvider}</span>
            <button className="secondary" onClick={logout} style={{ padding: '4px 10px', fontSize: 12 }}>Logout</button>
          </>
        ) : (
          <Link to="/login"><button>Sign in with Google</button></Link>
        )}
      </div>
    </header>
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
      <Header />
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
      <footer style={{ padding: '12px 24px', borderTop: '1px solid var(--border)', fontSize: 12, color: 'var(--muted)', textAlign: 'center' }}>
        {version && <>v{version} • </>}
        <Link to="/changelog">Changelog</Link>
      </footer>
    </BrowserRouter>
  );
}

export default App;
