import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Globe2, Sparkles } from 'lucide-react';
import { Alert, Button, ButtonLink, EmptyState, LoadingState } from '../components/atoms';
import { WorldGrid, WorldToolbar } from '../components/organisms';
import { createDemoWorld, deleteWorld, fetchWorlds } from '../lib/api/worlds';
import type { World } from '../lib/apiTypes';
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
      navigate(`/wiki/${demo.world.id}`);
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
          <p className="text-secondary">Explore world wikis and manage canon tools when needed.</p>
        </div>
        <div className="world-actions">
          <Button variant="secondary" onClick={handleCreateDemo} disabled={creatingDemo}>
            <Sparkles size={18} />
            {creatingDemo ? 'Creating...' : 'Demo World'}
          </Button>
          <ButtonLink to="/worlds/new" variant="primary">
            <Plus size={20} />
            New World
          </ButtonLink>
        </div>
      </div>

      {errorMessage && <Alert>{errorMessage}</Alert>}

      {loading ? (
        <LoadingState>Loading worlds...</LoadingState>
      ) : worlds.length === 0 ? (
        <EmptyState className="glass">
          <Globe2 size={48} className="text-muted" aria-hidden="true" />
          <h3>No worlds found</h3>
          <p>Create a world from scratch or load a complete demo to start exploring the wiki.</p>
          <div className="world-actions mt-4">
            <Button variant="secondary" onClick={handleCreateDemo} disabled={creatingDemo}>
              <Sparkles size={18} />
              Demo World
            </Button>
            <ButtonLink to="/worlds/new" variant="primary">
              Create World
            </ButtonLink>
          </div>
        </EmptyState>
      ) : (
        <>
          <WorldToolbar
            query={query}
            toneFilter={toneFilter}
            tones={tones}
            onQueryChange={setQuery}
            onToneFilterChange={setToneFilter}
          />
          <WorldGrid
            worlds={filteredWorlds}
            onDelete={handleDeleteWorld}
            onClearFilters={() => {
              setQuery('');
              setToneFilter('All');
            }}
          />
        </>
      )}
    </div>
  );
};

export default WorldsList;
