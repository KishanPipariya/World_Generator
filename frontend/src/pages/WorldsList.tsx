import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, Globe2, Clock, Sparkles, Trash2 } from 'lucide-react';
import { createDemoWorld, deleteWorld, fetchWorlds, type World } from '../lib/api';
import './Worlds.css';

const WorldsList = () => {
  const [worlds, setWorlds] = useState<World[]>([]);
  const [loading, setLoading] = useState(true);
  const [creatingDemo, setCreatingDemo] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchWorlds()
      .then(setWorlds)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

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

  const handleDeleteWorld = async (world: World) => {
    if (!window.confirm(`Delete "${world.title}" and all of its entities and relationships?`)) return;
    setErrorMessage('');
    try {
      await deleteWorld(world.id);
      setWorlds((current) => current.filter((item) => item.id !== world.id));
    } catch {
      setErrorMessage('Unable to delete this world.');
    }
  };

  return (
    <div className="worlds-list-container">
      <div className="worlds-header">
        <div>
          <h2>Your Worlds</h2>
          <p className="text-secondary">Manage and explore your created literary universes.</p>
        </div>
        <div className="world-actions">
          <button className="btn btn-secondary" onClick={handleCreateDemo} disabled={creatingDemo} type="button">
            <Sparkles size={18} />
            {creatingDemo ? 'Creating...' : 'Demo World'}
          </button>
          <Link to="/worlds/new" className="btn btn-primary">
            <Plus size={20} />
            New World
          </Link>
        </div>
      </div>

      {errorMessage && <div className="workspace-alert error">{errorMessage}</div>}

      {loading ? (
        <div className="loading-state">Loading...</div>
      ) : worlds.length === 0 ? (
        <div className="empty-state glass">
          <Globe2 size={48} className="text-muted" />
          <h3>No worlds found</h3>
          <p>Create a world from scratch or load a complete demo for a faster walkthrough.</p>
          <div className="world-actions mt-4">
            <button className="btn btn-secondary" onClick={handleCreateDemo} disabled={creatingDemo} type="button">
              <Sparkles size={18} />
              Demo World
            </button>
            <Link to="/worlds/new" className="btn btn-primary">
              Create World
            </Link>
          </div>
        </div>
      ) : (
        <div className="worlds-grid">
          {worlds.map(world => (
            <article key={world.id} className="world-card glass">
              <div className="world-card-header">
                <Link to={`/worlds/${world.id}`} className="world-card-title">
                  <h3>{world.title}</h3>
                </Link>
                <button
                  className="icon-button danger"
                  type="button"
                  onClick={() => handleDeleteWorld(world)}
                  title={`Delete ${world.title}`}
                  aria-label={`Delete ${world.title}`}
                >
                  <Trash2 size={16} />
                </button>
              </div>
              <Link to={`/worlds/${world.id}`} className="world-card-body">
                {world.tone && (
                  <span className="badge badge-primary">{world.tone}</span>
                )}
                <p className="world-era">{world.era_notes || 'No era notes'}</p>
              </Link>
              <Link to={`/worlds/${world.id}`} className="world-card-footer">
                <Clock size={16} />
                <span>{new Date(world.created_at).toLocaleDateString()}</span>
              </Link>
            </article>
          ))}
        </div>
      )}
    </div>
  );
};

export default WorldsList;
