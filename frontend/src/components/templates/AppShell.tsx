import type { ReactNode } from 'react';
import type { User } from '../../lib/apiTypes';
import { Navigation } from '../organisms/Navigation';

export function AppShell({ user, onLogout, children }: {
  user: User;
  onLogout: () => void;
  children: ReactNode;
}) {
  return (
    <div className="app-container">
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <Navigation user={user} onLogout={onLogout} />
      <main id="main-content" className="main-content" tabIndex={-1}>
        {children}
      </main>
    </div>
  );
}
