import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { BookOpen, Clock, Database, FilePlus2, FolderOpen, Sparkles } from 'lucide-react';
import { createDemoWorld, fetchWorlds, type World } from '../lib/api';
import './Home.css';

const Home = () => {
  const navigate = useNavigate();
  const [worlds, setWorlds] = useState<World[]>([]);
  const [loading, setLoading] = useState(true);
  const [creatingDemo, setCreatingDemo] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    fetchWorlds()
      .then(setWorlds)
      .catch(() => setErrorMessage('Unable to load recent worlds.'))
      .finally(() => setLoading(false));
  }, []);

  const recentWorlds = useMemo(
    () => [...worlds]
      .sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at))
      .slice(0, 4),
    [worlds],
  );

  const handleCreateDemo = async () => {
    setCreatingDemo(true);
    setErrorMessage('');
    try {
      const demo = await createDemoWorld();
      navigate(`/worlds/${demo.world.id}`);
    } catch {
      setErrorMessage('Unable to create the demo world.');
    } finally {
      setCreatingDemo(false);
    }
  };

  return (
    <div className="home-container page-enter">
      <header className="dashboard-header">
        <div>
          <p className="dashboard-kicker">World authoring workspace</p>
          <h1>Continue building your canon</h1>
          <p className="dashboard-subtitle">
            Open a recent world, start a blank setting, or load the demo workspace.
          </p>
        </div>
        <div className="dashboard-actions">
          <Link to="/worlds/new" className="btn btn-primary">
            <FilePlus2 size={18} aria-hidden="true" />
            New World
          </Link>
          <button className="btn btn-secondary" type="button" onClick={handleCreateDemo} disabled={creatingDemo}>
            <Sparkles size={18} aria-hidden="true" />
            {creatingDemo ? 'Creating...' : 'Demo World'}
          </button>
        </div>
      </header>

      {errorMessage && <div className="workspace-alert error" role="alert">{errorMessage}</div>}

      <section className="dashboard-grid" aria-label="Authoring dashboard">
        <div className="dashboard-panel recent-panel">
          <div className="panel-heading">
            <FolderOpen size={18} aria-hidden="true" />
            <h2>Recent Worlds</h2>
          </div>
          {loading ? (
            <p className="text-muted">Loading worlds...</p>
          ) : recentWorlds.length === 0 ? (
            <div className="dashboard-empty">
              <Database size={26} aria-hidden="true" />
              <p>No worlds yet. Create one or use the demo to explore the workspace.</p>
            </div>
          ) : (
            <div className="recent-world-list">
              {recentWorlds.map((world) => (
                <Link className="recent-world" to={`/worlds/${world.id}`} key={world.id}>
                  <span>
                    <strong>{world.title}</strong>
                    <small>{world.tone || 'No tone set'}</small>
                  </span>
                  <span className="recent-date">
                    <Clock size={14} aria-hidden="true" />
                    {new Date(world.created_at).toLocaleDateString()}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>

        <div className="dashboard-panel quick-panel">
          <div className="panel-heading">
            <BookOpen size={18} aria-hidden="true" />
            <h2>Quick Links</h2>
          </div>
          <Link to="/worlds" className="quick-link">
            <FolderOpen size={18} aria-hidden="true" />
            <span>
              <strong>World Management</strong>
              <small>Search, filter, open, and maintain worlds.</small>
            </span>
          </Link>
          {recentWorlds[0] ? (
            <>
              <Link to={`/worlds/${recentWorlds[0].id}`} className="quick-link">
                <Database size={18} aria-hidden="true" />
                <span>
                  <strong>Workspace</strong>
                  <small>Canon, drafts, timeline, planning, graph, and campaign tools.</small>
                </span>
              </Link>
              <Link to={`/wiki/${recentWorlds[0].id}`} className="quick-link">
                <BookOpen size={18} aria-hidden="true" />
                <span>
                  <strong>Wiki</strong>
                  <small>Read the latest world bible view.</small>
                </span>
              </Link>
            </>
          ) : (
            <p className="text-muted">Quick wiki and workspace links appear after a world exists.</p>
          )}
        </div>
      </section>
    </div>
  );
};

export default Home;
