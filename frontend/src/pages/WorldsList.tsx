import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, Globe2, Clock, Sparkles, Trash2, BookOpen, Search, Filter } from 'lucide-react';
import { createDemoWorld, deleteWorld, fetchWorlds, type World } from '../lib/api';
import './Worlds.css';

const WorldsList = () => {
  const [worlds, setWorlds] = useState<World[]>([]);
  const [loading, setLoading] = useState(true);
  const [creatingDemo, setCreatingDemo] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [query, setQuery] = useState('');
  const [toneFilter, setToneFilter] = useState('All');
  const navigate = useNavigate();

  useEffect(() => {
    fetchWorlds()
      .then(setWorlds)
      .catch(() => setErrorMessage('Unable to load worlds.'))
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
    const confirmation = window.prompt(`Type "${world.title}" to delete this world and all of its entities and relationships.`);
    if (confirmation !== world.title) return;
    setErrorMessage('');
    try {
      await deleteWorld(world.id);
      setWorlds((current) => current.filter((item) => item.id !== world.id));
    } catch {
      setErrorMessage('Unable to delete this world.');
    }
  };

  const tones = useMemo(
    () => Array.from(new Set(worlds.map((world) => world.tone).filter(Boolean) as string[])).sort(),
    [worlds],
  );

  const filteredWorlds = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return worlds.filter((world) => {
      const matchesTone = toneFilter === 'All' || world.tone === toneFilter;
      const matchesQuery = !normalizedQuery
        || [world.title, world.tone, world.era_notes, world.seed]
          .filter(Boolean)
          .some((value) => value?.toLowerCase().includes(normalizedQuery));
      return matchesTone && matchesQuery;
    });
  }, [query, toneFilter, worlds]);

  return (
    <div className="worlds-list-container">
      <div className="worlds-header">
        <div>
          <h1>Your Worlds</h1>
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

      {errorMessage && <div className="workspace-alert error" role="alert">{errorMessage}</div>}

      {loading ? (
        <div className="loading-state" role="status">Loading worlds...</div>
      ) : worlds.length === 0 ? (
        <div className="empty-state glass" role="status">
          <Globe2 size={48} className="text-muted" aria-hidden="true" />
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
        <>
          <div className="worlds-toolbar" aria-label="World filters">
            <label className="world-search">
              <Search size={16} aria-hidden="true" />
              <span className="sr-only">Search worlds</span>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search title, tone, notes, or seed"
                type="search"
              />
            </label>
            <label className="world-filter">
              <Filter size={16} aria-hidden="true" />
              <span>Tone</span>
              <select value={toneFilter} onChange={(event) => setToneFilter(event.target.value)}>
                <option>All</option>
                {tones.map((tone) => <option key={tone}>{tone}</option>)}
              </select>
            </label>
          </div>

          {filteredWorlds.length === 0 ? (
            <div className="empty-state compact-empty" role="status">
              <Globe2 size={34} className="text-muted" aria-hidden="true" />
              <h3>No worlds match these filters</h3>
              <p>Adjust the search or tone filter to return to your saved worlds.</p>
              <button className="btn btn-secondary" type="button" onClick={() => {
                setQuery('');
                setToneFilter('All');
              }}>
                Clear Filters
              </button>
            </div>
          ) : (
            <div className="worlds-grid">
              {filteredWorlds.map(world => (
                <article key={world.id} className="world-card">
                  <div className="world-card-header">
                    <Link to={`/worlds/${world.id}`} className="world-card-title">
                      <h2>{world.title}</h2>
                    </Link>
                  </div>
                  <Link to={`/worlds/${world.id}`} className="world-card-body">
                    {world.tone && (
                      <span className="badge badge-primary">{world.tone}</span>
                    )}
                    <p className="world-era">{world.era_notes || 'No era notes'}</p>
                  </Link>
                  <div className="world-card-footer">
                    <Link to={`/worlds/${world.id}`} className="world-card-action">
                      <Clock size={16} aria-hidden="true" />
                      <span>{new Date(world.created_at).toLocaleDateString()}</span>
                    </Link>
                    <Link to={`/wiki/${world.id}`} className="world-card-action">
                      <BookOpen size={16} aria-hidden="true" />
                      <span>Wiki</span>
                    </Link>
                    <button
                      className="text-danger-button"
                      type="button"
                      onClick={() => handleDeleteWorld(world)}
                    >
                      <Trash2 size={15} aria-hidden="true" />
                      Delete
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default WorldsList;
