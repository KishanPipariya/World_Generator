import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Globe } from 'lucide-react';
import './App.css';

// Pages
import Home from './pages/Home';
import Worlds from './pages/Worlds';
import WorldWiki from './pages/WorldWiki';

function Navigation() {
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
      </div>
    </nav>
  );
}

function App() {
  return (
    <Router>
      <div className="app-container">
        <a className="skip-link" href="#main-content">Skip to main content</a>
        <Navigation />
        <main id="main-content" className="main-content" tabIndex={-1}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/worlds/*" element={<Worlds />} />
            <Route path="/wiki/:worldId" element={<WorldWiki />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
