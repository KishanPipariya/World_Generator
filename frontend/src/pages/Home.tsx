import { Link } from 'react-router-dom';
import { Sparkles, Map, Database } from 'lucide-react';
import './Home.css';

const Home = () => {
  return (
    <div className="home-container page-enter">
      <header className="hero-section">
        <h1 className="hero-title">
          Forge <span className="gradient-text">Infinite Realms</span>
        </h1>
        <p className="hero-subtitle">
          An agentic platform for authors to build, manage, and explore rich literary worlds with AI assistance.
        </p>
        <div className="hero-actions">
          <Link to="/worlds" className="btn btn-primary">
            <Sparkles size={20} aria-hidden="true" />
            Start Creating
          </Link>
        </div>
      </header>

      <section className="features-grid" aria-labelledby="home-features-heading">
        <h2 id="home-features-heading" className="sr-only">Core features</h2>
        <div className="feature-card glass">
          <div className="feature-icon-wrapper">
            <Map className="feature-icon" size={24} aria-hidden="true" />
          </div>
          <h3>World Visualization</h3>
          <p>Bring your lore to life with dynamic relationships between characters, factions, and deep historical timelines.</p>
        </div>
        <div className="feature-card glass">
          <div className="feature-icon-wrapper">
            <Database className="feature-icon" size={24} aria-hidden="true" />
          </div>
          <h3>Agentic Lore Generation</h3>
          <p>Collaborate with multi-agent pipelines to craft deeply immersive worlds with complete consistency.</p>
        </div>
      </section>
    </div>
  );
};

export default Home;
