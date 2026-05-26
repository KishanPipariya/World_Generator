import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Globe } from 'lucide-react';
import './App.css';

// Pages
import Home from './pages/Home';
import Worlds from './pages/Worlds';
import WorldWiki from './pages/WorldWiki';

function Navigation() {
  const location = useLocation();
  
  return (
    <nav className="navbar glass">
      <div className="nav-brand">
        <Globe className="nav-brand-icon" size={28} />
        <span>Literary World Generator</span>
      </div>
      <div className="nav-links">
        <Link to="/" className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}>Home</Link>
        <Link to="/worlds" className={`nav-link ${location.pathname.startsWith('/worlds') || location.pathname.startsWith('/wiki') ? 'active' : ''}`}>Worlds</Link>
      </div>
    </nav>
  );
}

function App() {
  return (
    <Router>
      <div className="app-container">
        <Navigation />
        <main className="main-content">
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
