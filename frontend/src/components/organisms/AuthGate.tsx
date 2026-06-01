import { useState, type FormEvent } from 'react';
import { Globe } from 'lucide-react';
import { AxiosError } from 'axios';
import { AUTH_TOKEN_KEY, fetchMe, loginUser, registerUser, type User } from '../../lib/api';
import { Alert, Button } from '../atoms';

export function AuthGate({ onAuthenticated }: { onAuthenticated: (user: User) => void }) {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const getErrorMessage = (error: unknown) => {
    if (error instanceof AxiosError) {
      const detail = error.response?.data?.detail;
      if (typeof detail === 'string') return detail;
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
          {errorMessage && <Alert>{errorMessage}</Alert>}
          <Button variant="primary" type="submit" disabled={submitting}>
            {submitting ? 'Working...' : mode === 'login' ? 'Login' : 'Register'}
          </Button>
        </form>
      </section>
    </main>
  );
}
