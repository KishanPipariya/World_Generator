import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FilePlus2, Sparkles } from 'lucide-react';
import { Alert, Button, ButtonLink } from '../components/atoms';
import { PageHeader } from '../components/molecules';
import { WorldDashboardPanels } from '../components/organisms';
import { createDemoWorld, fetchWorlds } from '../lib/api/worlds';
import type { World } from '../lib/apiTypes';
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
      navigate(`/wiki/${demo.world.id}`);
    } catch {
      setErrorMessage('Unable to create the demo world.');
    } finally {
      setCreatingDemo(false);
    }
  };

  return (
    <div className="home-container page-enter">
      <PageHeader
        className="dashboard-header"
          kicker="World wiki and canon"
          title="Continue exploring your canon"
          subtitle="Open a recent world wiki, start a blank setting, or load the demo canon."
          actions={(
            <div className="dashboard-actions">
              <ButtonLink to="/worlds/new" variant="primary">
            <FilePlus2 size={18} aria-hidden="true" />
            New World
              </ButtonLink>
              <Button variant="secondary" onClick={handleCreateDemo} disabled={creatingDemo}>
                <Sparkles size={18} aria-hidden="true" />
                {creatingDemo ? 'Creating...' : 'Demo World'}
              </Button>
            </div>
          )}
      />

      {errorMessage && <Alert>{errorMessage}</Alert>}

      <WorldDashboardPanels loading={loading} recentWorlds={recentWorlds} />
    </div>
  );
};

export default Home;
