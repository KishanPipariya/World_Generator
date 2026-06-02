import { Globe, LogOut } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import type { User } from '../../lib/apiTypes';
import { IconButton } from '../atoms';

export function Navigation({ user, onLogout }: { user: User; onLogout: () => void }) {
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
        <IconButton onClick={onLogout} aria-label="Log out" title="Log out">
          <LogOut size={18} aria-hidden="true" />
        </IconButton>
      </div>
    </nav>
  );
}
