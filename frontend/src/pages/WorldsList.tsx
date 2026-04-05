import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Globe2, Clock } from 'lucide-react';
import { fetchWorlds, type World } from '../lib/api';
import './Worlds.css';

const WorldsList = () => {
  const [worlds, setWorlds] = useState<World[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchWorlds()
      .then(setWorlds)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="worlds-list-container">
      <div className="worlds-header">
        <div>
          <h2>Your Worlds</h2>
          <p className="text-secondary">Manage and explore your created literary universes.</p>
        </div>
        <Link to="/worlds/new" className="btn btn-primary">
          <Plus size={20} />
          New World
        </Link>
      </div>

      {loading ? (
        <div className="loading-state">Loading...</div>
      ) : worlds.length === 0 ? (
        <div className="empty-state glass">
          <Globe2 size={48} className="text-muted" />
          <h3>No worlds found</h3>
          <p>Create your first literary world to begin your journey.</p>
          <Link to="/worlds/new" className="btn btn-primary mt-4">
            Create World
          </Link>
        </div>
      ) : (
        <div className="worlds-grid">
          {worlds.map(world => (
            <Link to={`/worlds/${world.id}`} key={world.id} className="world-card glass">
              <div className="world-card-header">
                <h3>{world.title}</h3>
              </div>
              <div className="world-card-body">
                {world.tone && (
                  <span className="badge badge-primary">{world.tone}</span>
                )}
                <p className="world-era">{world.era_notes || 'No era notes'}</p>
              </div>
              <div className="world-card-footer">
                <Clock size={16} />
                <span>{new Date(world.created_at).toLocaleDateString()}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};

export default WorldsList;
