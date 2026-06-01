import { lazy, Suspense, useEffect, useState, type FormEvent } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Globe, LogOut } from 'lucide-react';
import { AxiosError } from 'axios';
import { AUTH_TOKEN_KEY, fetchMe, loginUser, registerUser, type User } from './lib/api';
import './App.css';

const Home = lazy(() => import('./pages/Home'));
const Worlds = lazy(() => import('./pages/Worlds'));
const WorldWiki = lazy(() => import('./pages/WorldWiki'));

function Navigation({ user, onLogout }: { user: User; onLogout: () => void }) {
  const location = useLocation();
  const homeActive = location.pathname === '/';
  const worldsActive = location.pathname.startsWith('/worlds') || location.pathname.startsWith('/wiki');
  
  return (
    <nav className="navbar glass" aria-label="Primary">
      <div className="nav-brand">
        <Globe className="nav-brand-icon" size={28} aria-hidden="true" />
        <span>Literary World Generator</span>
      </div>
      <div className="nav-links">
        <Link to="/" className={`nav-link ${homeActive ? 'active' : ''}`} aria-current={homeActive ? 'page' : undefined}>Home</Link>
        <Link to="/worlds" className={`nav-link ${worldsActive ? 'active' : ''}`} aria-current={worldsActive ? 'page' : undefined}>Worlds</Link>
        <span className="nav-user">{user.username}</span>
        <button className="icon-button" type="button" onClick={onLogout} aria-label="Log out" title="Log out">
          <LogOut size={18} aria-hidden="true" />
        </button>
      </div>
    </nav>
  );
}

function AuthGate({ onAuthenticated }: { onAuthenticated: (user: User) => void }) {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const getErrorMessage = (error: unknown) => {
    if (error instanceof AxiosError) {
      const detail = error.response?.data?.detail;
      if (typeof detail === 'string') {
        return detail;
      }
      if (Array.isArray(detail)) {
        return detail
          .map((issue) => {
            const field = Array.isArray(issue.loc) ? issue.loc[issue.loc.length - 1] : 'field';
            return `${field}: ${issue.msg}`;
          })
          .join(' ');
      }
    }
    return mode === 'login' ? 'Invalid username or password.' : 'Unable to create that account.';
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setErrorMessage('');
    try {
      if (mode === 'register') {
        await registerUser({ username, email, password });
      }
      const token = await loginUser({ username, password });
      localStorage.setItem(AUTH_TOKEN_KEY, token.access_token);
      onAuthenticated(await fetchMe());
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="auth-shell">
      <section className="auth-panel" aria-label="Account access">
        <div className="auth-heading">
          <Globe size={30} aria-hidden="true" />
          <h1>Literary World Generator</h1>
        </div>
        <div className="auth-tabs" role="tablist" aria-label="Authentication mode">
          <button type="button" className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>
            Login
          </button>
          <button type="button" className={mode === 'register' ? 'active' : ''} onClick={() => setMode('register')}>
            Register
          </button>
        </div>
        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            Username
            <input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              autoComplete="username"
              minLength={mode === 'register' ? 3 : 1}
              maxLength={mode === 'register' ? 80 : 320}
              pattern={mode === 'register' ? '[A-Za-z0-9_.-]+' : undefined}
              required
            />
          </label>
          {mode === 'register' && (
            <label>
              Email
              <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required />
            </label>
          )}
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              minLength={mode === 'register' ? 8 : 1}
              maxLength={1024}
              required
            />
          </label>
          {errorMessage && <div className="workspace-alert error" role="alert">{errorMessage}</div>}
          <button className="btn btn-primary" type="submit" disabled={submitting}>
            {submitting ? 'Working...' : mode === 'login' ? 'Login' : 'Register'}
          </button>
        </form>
      </section>
    </main>
  );
}

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [checkingAuth, setCheckingAuth] = useState(() => Boolean(localStorage.getItem(AUTH_TOKEN_KEY)));

  useEffect(() => {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (!token) {
      return;
    }
    fetchMe()
      .then(setUser)
      .catch(() => localStorage.removeItem(AUTH_TOKEN_KEY))
      .finally(() => setCheckingAuth(false));
  }, []);

  useEffect(() => {
    const handleExpired = () => setUser(null);
    window.addEventListener('world-generator-auth-expired', handleExpired);
    return () => window.removeEventListener('world-generator-auth-expired', handleExpired);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    setUser(null);
  };

  if (checkingAuth) {
    return <div className="loading-state" role="status">Loading workspace...</div>;
  }

  if (!user) {
    return <AuthGate onAuthenticated={setUser} />;
  }

  return (
    <Router>
      <div className="app-container">
        <a className="skip-link" href="#main-content">Skip to main content</a>
        <Navigation user={user} onLogout={handleLogout} />
        <main id="main-content" className="main-content" tabIndex={-1}>
          <Suspense fallback={<div className="loading-state" role="status">Loading workspace...</div>}>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/worlds/*" element={<Worlds />} />
              <Route path="/wiki/:worldId" element={<WorldWiki />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </Router>
  );
}

export default App;
