import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Sparkles, BookOpen, Clock, Bot } from 'lucide-react';
import { fetchWorld, generateAgentic, type World } from '../lib/api';
import './WorldDetail.css';

const WorldDetail = () => {
  const { id } = useParams<{ id: string }>();
  const [world, setWorld] = useState<World | null>(null);
  const [loading, setLoading] = useState(true);
  const [agenticInstruction, setAgenticInstruction] = useState('');
  const [agenticResult, setAgenticResult] = useState<{content: string, entity_id?: string} | null>(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (id) {
      fetchWorld(id)
        .then(setWorld)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [id]);

  const handleAgenticGen = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !agenticInstruction) return;
    
    setGenerating(true);
    try {
      // Basic implementation without saving to a specific entity map for now, 
      // just exploring the generate function.
      const result = await generateAgentic(id, agenticInstruction);
      setAgenticResult(result);
    } catch (err) {
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return <div className="loading-state">Loading world...</div>;
  }

  if (!world) {
    return (
      <div className="empty-state glass">
        <h3>World not found</h3>
        <Link to="/worlds" className="btn btn-primary mt-4">Back to Worlds</Link>
      </div>
    );
  }

  return (
    <div className="world-detail-container">
      <div className="back-nav">
        <Link to="/worlds" className="back-link">
          <ArrowLeft size={20} />
          <span>Back to Worlds</span>
        </Link>
      </div>

      <div className="world-header glass">
        <div className="title-section">
          <h1>{world.title}</h1>
          <div className="tags">
            {world.tone && <span className="badge badge-primary">{world.tone}</span>}
          </div>
        </div>
        <div className="meta-section">
          <div className="meta-item">
            <Clock size={16} />
            <span>Created {new Date(world.created_at).toLocaleDateString()}</span>
          </div>
        </div>
      </div>

      <div className="world-content-grid">
        <div className="world-main-content">
          <section className="glass content-section">
            <div className="section-header">
              <BookOpen className="text-secondary" />
              <h2>Era Notes & Context</h2>
            </div>
            <div className="section-body">
              {world.era_notes ? (
                <p className="era-notes-text">{world.era_notes}</p>
              ) : (
                <p className="text-muted">No era notes provided for this world.</p>
              )}
            </div>
          </section>
          
          {agenticResult && (
            <section className="glass content-section result-section page-enter">
              <div className="section-header">
                <Sparkles className="text-primary" />
                <h2>Generated Lore</h2>
              </div>
              <div className="section-body result-body">
                <pre className="lore-content">{agenticResult.content}</pre>
              </div>
            </section>
          )}
        </div>

        <div className="world-sidebar">
          <section className="glass agent-section">
            <div className="agent-header">
              <Bot className="agent-icon" size={24} />
              <h3>Agentic Generator</h3>
            </div>
            <p className="agent-desc">
              Ask the multi-agent pipeline to generate specific lore, cities, or characters based on the world's context.
            </p>
            
            <form onSubmit={handleAgenticGen} className="agent-form">
              <textarea
                value={agenticInstruction}
                onChange={(e) => setAgenticInstruction(e.target.value)}
                placeholder="e.g. 'Generate 3 major cities for the northern continent, focusing on trade.' "
                rows={4}
                className="form-input"
                required
              />
              <button 
                type="submit" 
                className="btn btn-primary" 
                disabled={generating || !agenticInstruction}
              >
                {generating ? <span className="pulsing">Generating...</span> : 'Generate Lore'}
              </button>
            </form>
          </section>
        </div>
      </div>
    </div>
  );
};

export default WorldDetail;
