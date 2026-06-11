import { lazy, Suspense, useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthGate } from './components/organisms';
import { LoadingState } from './components/atoms';
import { AppShell } from './components/templates';
import { AUTH_TOKEN_KEY } from './lib/apiClient';
import { fetchMe } from './lib/api/auth';
import type { User } from './lib/apiTypes';
import './App.css';

const Home = lazy(() => import('./pages/Home'));
const Worlds = lazy(() => import('./pages/Worlds'));
const WorldWiki = lazy(() => import('./pages/WorldWiki'));

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
    return <LoadingState>Loading canon...</LoadingState>;
  }

  if (!user) {
    return <AuthGate onAuthenticated={setUser} />;
  }

  return (
    <Router>
      <AppShell user={user} onLogout={handleLogout}>
        <Suspense fallback={<LoadingState>Loading canon...</LoadingState>}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/worlds/*" element={<Worlds />} />
            <Route path="/wiki/:worldId" element={<WorldWiki />} />
          </Routes>
        </Suspense>
      </AppShell>
    </Router>
  );
}

export default App;
