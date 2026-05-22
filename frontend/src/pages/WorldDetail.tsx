import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Bot,
  BookOpen,
  Clock,
  Download,
  Link2,
  Plus,
  Save,
  Sparkles,
  Trash2,
} from 'lucide-react';
import {
  createEntity,
  createRelationship,
  deleteEntity,
  deleteRelationship,
  exportMarkdown,
  fetchEntities,
  fetchRelationships,
  fetchWorld,
  generateAgentic,
  updateEntity,
  type Entity,
  type Relationship,
  type World,
} from '../lib/api';
import './WorldDetail.css';

const ENTITY_GROUPS = ['Character', 'Location', 'Faction', 'Concept', 'Event', 'Other'];
const ENTITY_TYPES = ['Character', 'Location', 'Faction', 'Concept', 'Event', 'Other'];
const PROMPTS = [
  { label: 'Cities', value: 'Generate three distinct cities with political tensions and trade hooks.' },
  { label: 'Factions', value: 'Generate three factions with goals, resources, and conflicts.' },
  { label: 'Event', value: 'Generate a historical event that still shapes current conflicts.' },
  { label: 'Expand', value: 'Expand the selected entity with history, sensory details, and story hooks.' },
];

type EntityForm = Pick<Entity, 'name' | 'entity_type' | 'description'>;

const blankEntity: EntityForm = {
  name: '',
  entity_type: 'Character',
  description: '',
};

const displayType = (type: string) => {
  const normalized = type.trim().toLowerCase();
  if (['character', 'person', 'historical figure'].includes(normalized)) return 'Character';
  if (['location', 'city', 'region', 'landmark', 'continent'].includes(normalized)) return 'Location';
  if (['faction', 'guild', 'kingdom', 'organization'].includes(normalized)) return 'Faction';
  if (['concept', 'magic system', 'technology', 'term'].includes(normalized)) return 'Concept';
  if (['event', 'historical event', 'battle'].includes(normalized)) return 'Event';
  return 'Other';
};

const WorldDetail = () => {
  const { id } = useParams<{ id: string }>();
  const [world, setWorld] = useState<World | null>(null);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [selectedEntityId, setSelectedEntityId] = useState<string | null>(null);
  const [entityForm, setEntityForm] = useState<EntityForm>(blankEntity);
  const [relationshipForm, setRelationshipForm] = useState({
    source_entity_id: '',
    target_entity_id: '',
    relation_type: '',
    notes: '',
  });
  const [agenticInstruction, setAgenticInstruction] = useState('');
  const [saveGenerated, setSaveGenerated] = useState(false);
  const [generatedName, setGeneratedName] = useState('');
  const [generatedType, setGeneratedType] = useState('Concept');
  const [agenticResult, setAgenticResult] = useState<{ content: string; entity_id?: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const selectedEntity = useMemo(
    () => entities.find((entity) => entity.id === selectedEntityId) ?? null,
    [entities, selectedEntityId],
  );

  const groupedEntities = useMemo(
    () =>
      ENTITY_GROUPS.map((group) => ({
        group,
        items: entities.filter((entity) => displayType(entity.entity_type) === group),
      })),
    [entities],
  );

  const loadWorkspace = async (worldId: string) => {
    setErrorMessage('');
    const [worldData, entityData, relationshipData] = await Promise.all([
      fetchWorld(worldId),
      fetchEntities(worldId),
      fetchRelationships(worldId),
    ]);
    setWorld(worldData);
    setEntities(entityData);
    setRelationships(relationshipData);
    setSelectedEntityId((current) => current ?? entityData[0]?.id ?? null);
  };

  useEffect(() => {
    if (!id) return;
    loadWorkspace(id)
      .catch(() => setErrorMessage('Unable to load this world.'))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (selectedEntity) {
      setEntityForm({
        name: selectedEntity.name,
        entity_type: selectedEntity.entity_type,
        description: selectedEntity.description,
      });
    } else {
      setEntityForm(blankEntity);
    }
  }, [selectedEntity]);

  const refreshEntities = async () => {
    if (!id) return;
    const [entityData, relationshipData] = await Promise.all([
      fetchEntities(id),
      fetchRelationships(id),
    ]);
    setEntities(entityData);
    setRelationships(relationshipData);
  };

  const handleEntitySubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!id || !entityForm.name.trim()) return;
    setBusy(true);
    setErrorMessage('');
    try {
      const saved = selectedEntity
        ? await updateEntity(id, selectedEntity.id, entityForm)
        : await createEntity(id, entityForm);
      await refreshEntities();
      setSelectedEntityId(saved.id);
      setStatusMessage(selectedEntity ? 'Entity updated.' : 'Entity created.');
    } catch {
      setErrorMessage('Unable to save entity.');
    } finally {
      setBusy(false);
    }
  };

  const handleDeleteEntity = async () => {
    if (!id || !selectedEntity) return;
    setBusy(true);
    setErrorMessage('');
    try {
      await deleteEntity(id, selectedEntity.id);
      await refreshEntities();
      setSelectedEntityId(null);
      setStatusMessage('Entity deleted.');
    } catch {
      setErrorMessage('Unable to delete entity.');
    } finally {
      setBusy(false);
    }
  };

  const handleAgenticGen = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!id || !agenticInstruction.trim()) return;
    setGenerating(true);
    setErrorMessage('');
    try {
      const result = await generateAgentic(
        id,
        agenticInstruction,
        saveGenerated && generatedName.trim()
          ? { entityType: generatedType, name: generatedName.trim() }
          : undefined,
      );
      setAgenticResult(result);
      if (result.entity_id) {
        await refreshEntities();
        setSelectedEntityId(result.entity_id);
        setStatusMessage('Generated lore saved.');
      } else {
        setStatusMessage('Generated lore ready.');
      }
    } catch {
      setErrorMessage('Unable to generate lore.');
    } finally {
      setGenerating(false);
    }
  };

  const handleApplyGenerated = async (mode: 'append' | 'replace') => {
    if (!id || !selectedEntity || !agenticResult) return;
    const description =
      mode === 'append'
        ? `${selectedEntity.description.trim()}\n\n${agenticResult.content}`.trim()
        : agenticResult.content;
    setBusy(true);
    try {
      const updated = await updateEntity(id, selectedEntity.id, { description });
      await refreshEntities();
      setSelectedEntityId(updated.id);
      setStatusMessage(mode === 'append' ? 'Generated lore appended.' : 'Description replaced.');
    } catch {
      setErrorMessage('Unable to apply generated lore.');
    } finally {
      setBusy(false);
    }
  };

  const handleRelationshipSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!id || !relationshipForm.source_entity_id || !relationshipForm.target_entity_id) return;
    setBusy(true);
    setErrorMessage('');
    try {
      await createRelationship(id, {
        ...relationshipForm,
        notes: relationshipForm.notes || undefined,
      });
      setRelationshipForm({
        source_entity_id: '',
        target_entity_id: '',
        relation_type: '',
        notes: '',
      });
      setRelationships(await fetchRelationships(id));
      setStatusMessage('Relationship created.');
    } catch {
      setErrorMessage('Unable to create relationship.');
    } finally {
      setBusy(false);
    }
  };

  const handleExport = async () => {
    if (!id) return;
    setBusy(true);
    setErrorMessage('');
    try {
      const exported = await exportMarkdown(id);
      const blob = new Blob([exported.content], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = exported.filename;
      link.click();
      URL.revokeObjectURL(url);
      setStatusMessage('Markdown exported.');
    } catch {
      setErrorMessage('Unable to export Markdown.');
    } finally {
      setBusy(false);
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
            <span className="badge">{entities.length} entities</span>
          </div>
        </div>
        <div className="meta-section">
          <div className="meta-item">
            <Clock size={16} />
            <span>Created {new Date(world.created_at).toLocaleDateString()}</span>
          </div>
          <button className="btn btn-secondary" onClick={handleExport} disabled={busy}>
            <Download size={16} />
            Export
          </button>
        </div>
      </div>

      {(statusMessage || errorMessage) && (
        <div className={`workspace-alert ${errorMessage ? 'error' : 'success'}`}>
          {errorMessage || statusMessage}
        </div>
      )}

      <div className="workspace-grid">
        <aside className="entity-browser glass">
          <div className="panel-title">
            <BookOpen size={18} />
            <h2>World Bible</h2>
            <button
              className="icon-button"
              type="button"
              onClick={() => setSelectedEntityId(null)}
              title="New entity"
            >
              <Plus size={18} />
            </button>
          </div>
          {entities.length === 0 ? (
            <p className="text-muted">No saved entities yet.</p>
          ) : (
            groupedEntities.map(({ group, items }) => (
              items.length > 0 && (
                <div className="entity-group" key={group}>
                  <h3>{group}</h3>
                  {items.map((entity) => (
                    <button
                      className={`entity-list-item ${selectedEntityId === entity.id ? 'active' : ''}`}
                      key={entity.id}
                      onClick={() => setSelectedEntityId(entity.id)}
                      type="button"
                    >
                      <span>{entity.name}</span>
                      <small>{entity.entity_type}</small>
                    </button>
                  ))}
                </div>
              )
            ))
          )}
        </aside>

        <main className="editor-stack">
          <section className="glass content-section">
            <div className="section-header">
              <BookOpen className="text-secondary" />
              <h2>{selectedEntity ? 'Entity Detail' : 'New Entity'}</h2>
            </div>
            <form onSubmit={handleEntitySubmit} className="entity-form">
              <div className="form-row">
                <input
                  value={entityForm.name}
                  onChange={(event) => setEntityForm({ ...entityForm, name: event.target.value })}
                  placeholder="Name"
                  className="form-input"
                  required
                />
                <select
                  value={entityForm.entity_type}
                  onChange={(event) => setEntityForm({ ...entityForm, entity_type: event.target.value })}
                  className="form-input"
                >
                  {ENTITY_TYPES.map((type) => <option key={type}>{type}</option>)}
                </select>
              </div>
              <textarea
                value={entityForm.description}
                onChange={(event) => setEntityForm({ ...entityForm, description: event.target.value })}
                placeholder="Description"
                rows={9}
                className="form-input"
              />
              <div className="form-actions">
                <button type="submit" className="btn btn-primary" disabled={busy}>
                  <Save size={16} />
                  {selectedEntity ? 'Save Entity' : 'Create Entity'}
                </button>
                {selectedEntity && (
                  <button type="button" className="btn btn-danger" onClick={handleDeleteEntity} disabled={busy}>
                    <Trash2 size={16} />
                    Delete
                  </button>
                )}
              </div>
            </form>
          </section>

          <section className="glass content-section relationship-section">
            <div className="section-header">
              <Link2 className="text-primary" />
              <h2>Relationships</h2>
            </div>
            <form onSubmit={handleRelationshipSubmit} className="relationship-form">
              <select
                value={relationshipForm.source_entity_id}
                onChange={(event) => setRelationshipForm({ ...relationshipForm, source_entity_id: event.target.value })}
                className="form-input"
                required
              >
                <option value="">Source</option>
                {entities.map((entity) => <option key={entity.id} value={entity.id}>{entity.name}</option>)}
              </select>
              <input
                value={relationshipForm.relation_type}
                onChange={(event) => setRelationshipForm({ ...relationshipForm, relation_type: event.target.value })}
                placeholder="Relation"
                className="form-input"
                required
              />
              <select
                value={relationshipForm.target_entity_id}
                onChange={(event) => setRelationshipForm({ ...relationshipForm, target_entity_id: event.target.value })}
                className="form-input"
                required
              >
                <option value="">Target</option>
                {entities.map((entity) => <option key={entity.id} value={entity.id}>{entity.name}</option>)}
              </select>
              <input
                value={relationshipForm.notes}
                onChange={(event) => setRelationshipForm({ ...relationshipForm, notes: event.target.value })}
                placeholder="Notes"
                className="form-input"
              />
              <button type="submit" className="btn btn-primary" disabled={busy || entities.length < 2}>
                <Plus size={16} />
                Add
              </button>
            </form>
            <div className="relationship-list">
              {relationships.length === 0 ? (
                <p className="text-muted">No relationships yet.</p>
              ) : (
                relationships.map((relationship) => (
                  <div className="relationship-item" key={relationship.id}>
                    <div>
                      <strong>{relationship.source_entity_name}</strong>
                      <span> {relationship.relation_type} </span>
                      <strong>{relationship.target_entity_name}</strong>
                      {relationship.notes && <p>{relationship.notes}</p>}
                    </div>
                    <button
                      className="icon-button danger"
                      onClick={async () => {
                        if (!id) return;
                        await deleteRelationship(id, relationship.id);
                        setRelationships(await fetchRelationships(id));
                      }}
                      type="button"
                      title="Delete relationship"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))
              )}
            </div>
          </section>
        </main>

        <aside className="generator-stack">
          <section className="glass agent-section">
            <div className="agent-header">
              <Bot className="agent-icon" size={24} />
              <h3>Generator</h3>
            </div>
            <div className="preset-row">
              {PROMPTS.map((prompt) => (
                <button
                  key={prompt.label}
                  className="preset-button"
                  type="button"
                  onClick={() => setAgenticInstruction(prompt.value)}
                >
                  {prompt.label}
                </button>
              ))}
            </div>
            <form onSubmit={handleAgenticGen} className="agent-form">
              <textarea
                value={agenticInstruction}
                onChange={(event) => setAgenticInstruction(event.target.value)}
                placeholder="Generation prompt"
                rows={5}
                className="form-input"
                required
              />
              <label className="checkbox-row">
                <input
                  checked={saveGenerated}
                  onChange={(event) => setSaveGenerated(event.target.checked)}
                  type="checkbox"
                />
                <span>Save as entity</span>
              </label>
              {saveGenerated && (
                <div className="form-row compact">
                  <input
                    value={generatedName}
                    onChange={(event) => setGeneratedName(event.target.value)}
                    placeholder="Entity name"
                    className="form-input"
                  />
                  <select
                    value={generatedType}
                    onChange={(event) => setGeneratedType(event.target.value)}
                    className="form-input"
                  >
                    {ENTITY_TYPES.map((type) => <option key={type}>{type}</option>)}
                  </select>
                </div>
              )}
              <button type="submit" className="btn btn-primary" disabled={generating || !agenticInstruction.trim()}>
                <Sparkles size={16} />
                {generating ? 'Generating...' : 'Generate'}
              </button>
            </form>
          </section>

          {agenticResult && (
            <section className="glass content-section result-section page-enter">
              <div className="section-header">
                <Sparkles className="text-primary" />
                <h2>Generated Lore</h2>
              </div>
              <pre className="lore-content">{agenticResult.content}</pre>
              <div className="form-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => handleApplyGenerated('append')}
                  disabled={!selectedEntity || busy}
                >
                  Append
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => handleApplyGenerated('replace')}
                  disabled={!selectedEntity || busy}
                >
                  Replace
                </button>
              </div>
            </section>
          )}
        </aside>
      </div>
    </div>
  );
};

export default WorldDetail;
