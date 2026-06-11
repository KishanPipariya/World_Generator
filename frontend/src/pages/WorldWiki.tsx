import { useEffect, useMemo, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft,
  BookOpen,
  CalendarDays,
  CircleDot,
  Clock,
  Link2,
  Search,
  Tags,
  Wrench,
} from 'lucide-react';
import { fetchLoreNotes } from '../lib/api/campaign';
import { fetchEntities, fetchRelationships } from '../lib/api/canon';
import { fetchTimelineEvents } from '../lib/api/planning';
import { fetchWorld } from '../lib/api/worlds';
import {
  type Entity,
  type LoreNote,
  type Relationship,
  type TimelineEvent,
  type World,
} from '../lib/apiTypes';
import './WorldWiki.css';

const formatDate = (value: string) => new Date(value).toLocaleDateString();

const normalize = (value: string | null | undefined) => value?.trim().toLowerCase() ?? '';

const entityTypeLabel = (type: string) => type || 'Other';

const stringifyFields = (fields: Record<string, string>) =>
  Object.entries(fields ?? {})
    .map(([key, value]) => `${key} ${value}`)
    .join(' ');

const matchesQuery = (text: string, query: string) => normalize(text).includes(query);

const sortEntities = (entities: Entity[]) =>
  [...entities].sort((a, b) => a.entity_type.localeCompare(b.entity_type) || a.name.localeCompare(b.name));

const sortTimeline = (events: TimelineEvent[]) =>
  [...events].sort((a, b) => a.event_order - b.event_order || a.title.localeCompare(b.title));

const structuredEntries = (entity: Entity) =>
  Object.entries(entity.structured_fields ?? {}).filter(([, value]) => String(value).trim().length > 0);

const WorldWiki = () => {
  const { worldId } = useParams<{ worldId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedEntityId = searchParams.get('entity');

  const [world, setWorld] = useState<World | null>(null);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  const [loreNotes, setLoreNotes] = useState<LoreNote[]>([]);
  const [visibilityMode, setVisibilityMode] = useState<'dm' | 'player'>('dm');
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTypes, setActiveTypes] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    if (!worldId) return;

    let cancelled = false;

    Promise.all([
      fetchWorld(worldId),
      fetchEntities(worldId),
      fetchRelationships(worldId),
      fetchTimelineEvents(worldId).catch(() => []),
      fetchLoreNotes(worldId).catch(() => []),
    ])
      .then(([worldData, entityData, relationshipData, timelineData, noteData]) => {
        if (cancelled) return;
        setWorld(worldData);
        setEntities(entityData);
        setRelationships(relationshipData);
        setTimelineEvents(timelineData);
        setLoreNotes(noteData);
        setErrorMessage('');
      })
      .catch(() => {
        if (!cancelled) {
          setWorld(null);
          setEntities([]);
          setRelationships([]);
          setTimelineEvents([]);
          setLoreNotes([]);
          setErrorMessage('Unable to load this world wiki.');
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [worldId]);

  const playerKnownEntityIds = useMemo(
    () => new Set(loreNotes
      .filter((note) => note.subject_type === 'entity' && note.subject_id && ['player_visible', 'discovered'].includes(note.visibility))
      .map((note) => note.subject_id as string)),
    [loreNotes],
  );
  const visibleEntities = useMemo(
    () => visibilityMode === 'dm' ? entities : entities.filter((entity) => playerKnownEntityIds.has(entity.id)),
    [entities, playerKnownEntityIds, visibilityMode],
  );
  const visibleLoreNotes = useMemo(
    () => visibilityMode === 'dm'
      ? loreNotes
      : loreNotes.filter((note) => ['player_visible', 'discovered', 'redacted'].includes(note.visibility)),
    [loreNotes, visibilityMode],
  );

  const entityById = useMemo(() => new Map(visibleEntities.map((entity) => [entity.id, entity])), [visibleEntities]);
  const selectedEntity = selectedEntityId ? entityById.get(selectedEntityId) : undefined;

  const entityTypes = useMemo(
    () => Array.from(new Set(visibleEntities.map((entity) => entityTypeLabel(entity.entity_type)))).sort(),
    [visibleEntities],
  );

  const query = normalize(searchTerm);

  const matchedEntityIds = useMemo(() => {
    if (!query) return new Set(visibleEntities.map((entity) => entity.id));

    const matches = new Set<string>();

    visibleEntities.forEach((entity) => {
      const entityText = [
        entity.name,
        entity.entity_type,
        entity.description,
        stringifyFields(entity.structured_fields),
      ].join(' ');
      if (matchesQuery(entityText, query)) matches.add(entity.id);
    });

    relationships.forEach((relationship) => {
      const relationshipText = [
        relationship.relation_type,
        relationship.notes,
        relationship.category,
        relationship.history,
        relationship.stance,
        relationship.source_entity_name,
        relationship.target_entity_name,
      ].join(' ');
      if (matchesQuery(relationshipText, query)) {
        matches.add(relationship.source_entity_id);
        matches.add(relationship.target_entity_id);
      }
    });

    timelineEvents.forEach((event) => {
      const timelineText = [
        event.title,
        event.description,
        event.causes,
        event.consequences,
        event.date_label,
        event.era_label,
      ].join(' ');
      if (matchesQuery(timelineText, query)) {
        event.participants.forEach((entityId) => matches.add(entityId));
      }
    });

    visibleLoreNotes.forEach((note) => {
      if (note.subject_type === 'entity' && note.subject_id && matchesQuery([note.title, note.body, note.handout_text].join(' '), query)) {
        matches.add(note.subject_id);
      }
    });

    return matches;
  }, [query, relationships, timelineEvents, visibleEntities, visibleLoreNotes]);

  const filteredEntities = useMemo(() => {
    const typeFilterEnabled = activeTypes.size > 0;
    return sortEntities(visibleEntities).filter((entity) => {
      const type = entityTypeLabel(entity.entity_type);
      return (!typeFilterEnabled || activeTypes.has(type)) && matchedEntityIds.has(entity.id);
    });
  }, [activeTypes, matchedEntityIds, visibleEntities]);

  const selectedLoreNotes = useMemo(() => {
    if (!selectedEntity) return [];
    return visibleLoreNotes.filter((note) => note.subject_type === 'entity' && note.subject_id === selectedEntity.id);
  }, [selectedEntity, visibleLoreNotes]);

  const groupedEntities = useMemo(() => {
    return filteredEntities.reduce<Record<string, Entity[]>>((groups, entity) => {
      const type = entityTypeLabel(entity.entity_type);
      groups[type] = [...(groups[type] ?? []), entity];
      return groups;
    }, {});
  }, [filteredEntities]);

  const selectedRelationships = useMemo(() => {
    if (!selectedEntity) return [];
    return relationships.filter(
      (relationship) =>
        relationship.source_entity_id === selectedEntity.id || relationship.target_entity_id === selectedEntity.id,
    );
  }, [relationships, selectedEntity]);

  const outboundRelationships = selectedEntity
    ? selectedRelationships.filter((relationship) => relationship.source_entity_id === selectedEntity.id)
    : [];
  const inboundRelationships = selectedEntity
    ? selectedRelationships.filter((relationship) => relationship.target_entity_id === selectedEntity.id)
    : [];

  const selectedTimelineEvents = useMemo(() => {
    if (!selectedEntity) return [];
    return sortTimeline(timelineEvents).filter((event) => event.participants.includes(selectedEntity.id));
  }, [selectedEntity, timelineEvents]);

  const setSelectedEntity = (entityId?: string) => {
    const nextParams = new URLSearchParams(searchParams);
    if (entityId) {
      nextParams.set('entity', entityId);
    } else {
      nextParams.delete('entity');
    }
    setSearchParams(nextParams);
  };

  const toggleType = (type: string) => {
    setActiveTypes((current) => {
      const next = new Set(current);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  };

  const renderEntityLink = (entityId: string, fallback: string) => {
    const entity = entityById.get(entityId);
    return (
      <button
        className="wiki-text-link"
        type="button"
        onClick={() => setSelectedEntity(entityId)}
        aria-current={selectedEntity?.id === entityId ? 'true' : undefined}
      >
        {entity?.name ?? fallback}
      </button>
    );
  };

  if (loading) {
    return <div className="wiki-loading" role="status">Loading world wiki...</div>;
  }

  if (errorMessage || !world) {
    return (
      <div className="wiki-empty">
        <h2>World not found</h2>
        <p>{errorMessage || 'This world could not be loaded.'}</p>
        <Link to="/worlds" className="btn btn-primary">
          Back to Worlds
        </Link>
      </div>
    );
  }

  const hasEntities = visibleEntities.length > 0;
  const overviewTimeline = sortTimeline(timelineEvents).slice(0, 6);

  return (
    <div className="world-wiki-page page-enter">
      <aside className="wiki-sidebar" aria-label="Wiki navigation">
        <Link to="/worlds" className="wiki-back-link">
          <ArrowLeft size={18} />
          <span>Worlds</span>
        </Link>

        <button className="wiki-world-title" type="button" onClick={() => setSelectedEntity()}>
          <BookOpen size={20} />
          <span>{world.title}</span>
        </button>

        <Link to={`/worlds/${world.id}`} className="wiki-back-link">
          <Wrench size={18} />
          <span>Edit Canon</span>
        </Link>

        <label className="wiki-search">
          <span className="sr-only">Search canon</span>
          <Search size={16} />
          <input
            type="search"
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            placeholder="Search canon"
          />
        </label>

        <div className="wiki-filter-block">
          <div className="wiki-sidebar-heading">
            <BookOpen size={14} />
            <span>Visibility</span>
          </div>
          <div className="wiki-type-filters">
            <button
              className={visibilityMode === 'dm' ? 'active' : ''}
              type="button"
              onClick={() => setVisibilityMode('dm')}
              aria-pressed={visibilityMode === 'dm'}
            >
              DM
            </button>
            <button
              className={visibilityMode === 'player' ? 'active' : ''}
              type="button"
              onClick={() => setVisibilityMode('player')}
              aria-pressed={visibilityMode === 'player'}
            >
              Player
            </button>
          </div>
        </div>

        {entityTypes.length > 0 && (
          <div className="wiki-filter-block">
            <div className="wiki-sidebar-heading">
              <Tags size={14} />
              <span>Types</span>
            </div>
            <div className="wiki-type-filters">
              {entityTypes.map((type) => (
                <button
                  key={type}
                  className={activeTypes.has(type) ? 'active' : ''}
                  type="button"
                  onClick={() => toggleType(type)}
                  aria-pressed={activeTypes.has(type)}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>
        )}

        <nav className="wiki-index" aria-label="Entity index">
          <div className="wiki-sidebar-heading">
            <CircleDot size={14} />
            <span>Entities</span>
          </div>
          {!hasEntities ? (
            <p className="wiki-muted">No entities yet.</p>
          ) : filteredEntities.length === 0 ? (
            <p className="wiki-muted">No matches.</p>
          ) : (
            Object.entries(groupedEntities).map(([type, group]) => (
              <div className="wiki-index-group" key={type}>
                <h3>{type}</h3>
                {group.map((entity) => (
                  <button
                    key={entity.id}
                    className={`wiki-index-item ${selectedEntity?.id === entity.id ? 'active' : ''} ${
                      query && matchedEntityIds.has(entity.id) ? 'match' : ''
                    }`}
                    type="button"
                    onClick={() => setSelectedEntity(entity.id)}
                    aria-current={selectedEntity?.id === entity.id ? 'true' : undefined}
                  >
                    {entity.name}
                  </button>
                ))}
              </div>
            ))
          )}
        </nav>
      </aside>

      <div className="wiki-reader" role="region" aria-label="Wiki reader">
        {!hasEntities ? (
          <article className="wiki-article">
            <p className="wiki-kicker">World Overview</p>
            <h1>{world.title}</h1>
            <p className="wiki-lede">This world does not have any canon entities yet.</p>
            {world.era_notes && <p>{world.era_notes}</p>}
          </article>
        ) : selectedEntity ? (
          <article className="wiki-article">
            <p className="wiki-kicker">{selectedEntity.entity_type}</p>
            <h1>{selectedEntity.name}</h1>
            {query && matchedEntityIds.has(selectedEntity.id) && <span className="wiki-match-badge">Search match</span>}
            <p className="wiki-lede">{selectedEntity.description || 'No description has been written yet.'}</p>

            {structuredEntries(selectedEntity).length > 0 && (
              <section className="wiki-section">
                <h2>Details</h2>
                <dl className="wiki-fields">
                  {structuredEntries(selectedEntity).map(([key, value]) => (
                    <div key={key}>
                      <dt>{key.replaceAll('_', ' ')}</dt>
                      <dd>{value}</dd>
                    </div>
                  ))}
                </dl>
              </section>
            )}

            {selectedRelationships.length > 0 && (
              <section className="wiki-section">
                <h2>Relationships</h2>
                <div className="wiki-relation-list">
                  {selectedRelationships.map((relationship) => {
                    const isOutbound = relationship.source_entity_id === selectedEntity.id;
                    const relatedId = isOutbound ? relationship.target_entity_id : relationship.source_entity_id;
                    const relatedName = isOutbound ? relationship.target_entity_name : relationship.source_entity_name;
                    return (
                      <div className="wiki-relation-row" key={relationship.id}>
                        <span className="wiki-relation-direction">{isOutbound ? 'To' : 'From'}</span>
                        {renderEntityLink(relatedId, relatedName)}
                        <span className="wiki-relation-type">{relationship.relation_type}</span>
                        {relationship.notes && <p>{relationship.notes}</p>}
                      </div>
                    );
                  })}
                </div>
              </section>
            )}

            {selectedTimelineEvents.length > 0 && (
              <section className="wiki-section">
                <h2>Timeline References</h2>
                <ol className="wiki-timeline">
                  {selectedTimelineEvents.map((event) => (
                    <li key={event.id}>
                      <div>
                        <strong>{event.title}</strong>
                        {(event.date_label || event.era_label) && (
                          <span>{[event.date_label, event.era_label].filter(Boolean).join(' / ')}</span>
                        )}
                      </div>
                      {event.description && <p>{event.description}</p>}
                    </li>
                  ))}
                </ol>
              </section>
            )}

            {selectedLoreNotes.length > 0 && (
              <section className="wiki-section">
                <h2>Lore Notes</h2>
                <div className="wiki-relation-list">
                  {selectedLoreNotes.map((note) => (
                    <div className="wiki-relation-row" key={note.id}>
                      <span className="wiki-relation-direction">{note.visibility.replace('_', ' ')}</span>
                      <strong>{note.title}</strong>
                      <p>{note.visibility === 'redacted' ? '[redacted]' : note.handout_text || note.body}</p>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </article>
        ) : (
          <article className="wiki-article">
            <p className="wiki-kicker">World Overview</p>
            <h1>{world.title}</h1>
            <p className="wiki-lede">{world.era_notes || 'Browse the entity index to read canon entries.'}</p>
            {world.seed && <p>{world.seed}</p>}

            <section className="wiki-section">
              <h2>Canon Index</h2>
              <div className="wiki-overview-grid">
                {entityTypes.map((type) => (
                  <div className="wiki-overview-stat" key={type}>
                    <strong>{visibleEntities.filter((entity) => entityTypeLabel(entity.entity_type) === type).length}</strong>
                    <span>{type}</span>
                  </div>
                ))}
              </div>
            </section>

            {query && filteredEntities.length > 0 && (
              <section className="wiki-section">
                <h2>Search Matches</h2>
                <div className="wiki-match-list">
                  {filteredEntities.map((entity) => (
                    <button key={entity.id} type="button" onClick={() => setSelectedEntity(entity.id)}>
                      <strong>{entity.name}</strong>
                      <span>{entity.entity_type}</span>
                    </button>
                  ))}
                </div>
              </section>
            )}

            {overviewTimeline.length > 0 && (
              <section className="wiki-section">
                <h2>Timeline</h2>
                <ol className="wiki-timeline">
                  {overviewTimeline.map((event) => (
                    <li key={event.id}>
                      <div>
                        <strong>{event.title}</strong>
                        {(event.date_label || event.era_label) && (
                          <span>{[event.date_label, event.era_label].filter(Boolean).join(' / ')}</span>
                        )}
                      </div>
                      {event.description && <p>{event.description}</p>}
                    </li>
                  ))}
                </ol>
              </section>
            )}
          </article>
        )}
      </div>

      <aside className="wiki-context" aria-label="Wiki context">
        {selectedEntity ? (
          <>
            <section>
              <h2>Links</h2>
              <p>{selectedRelationships.length} relationship references</p>
              <p>{selectedTimelineEvents.length} timeline references</p>
            </section>

            <section>
              <h2>Outbound</h2>
              {outboundRelationships.length === 0 ? (
                <p className="wiki-muted">None</p>
              ) : (
                outboundRelationships.map((relationship) => (
                  <div className="wiki-context-link" key={relationship.id}>
                    <Link2 size={14} />
                    <span>{relationship.relation_type}</span>
                    {renderEntityLink(relationship.target_entity_id, relationship.target_entity_name)}
                  </div>
                ))
              )}
            </section>

            <section>
              <h2>Backlinks</h2>
              {inboundRelationships.length === 0 ? (
                <p className="wiki-muted">None</p>
              ) : (
                inboundRelationships.map((relationship) => (
                  <div className="wiki-context-link" key={relationship.id}>
                    <Link2 size={14} />
                    {renderEntityLink(relationship.source_entity_id, relationship.source_entity_name)}
                    <span>{relationship.relation_type}</span>
                  </div>
                ))
              )}
            </section>

            <section>
              <h2>Metadata</h2>
              <div className="wiki-meta-row">
                <Clock size={14} />
                <span>Created {formatDate(selectedEntity.created_at)}</span>
              </div>
              <div className="wiki-meta-row">
                <CircleDot size={14} />
                <span>{selectedEntity.entity_type}</span>
              </div>
            </section>
          </>
        ) : (
          <>
            <section>
              <h2>World</h2>
              <p>{visibleEntities.length} entities</p>
              <p>{relationships.length} relationships</p>
              <p>{timelineEvents.length} timeline events</p>
              <p>{visibleLoreNotes.length} lore notes</p>
            </section>
            <section>
              <h2>Metadata</h2>
              <div className="wiki-meta-row">
                <Clock size={14} />
                <span>Created {formatDate(world.created_at)}</span>
              </div>
              {world.tone && (
                <div className="wiki-meta-row">
                  <CircleDot size={14} />
                  <span>{world.tone}</span>
                </div>
              )}
            </section>
            {overviewTimeline.length > 0 && (
              <section>
                <h2>Timeline</h2>
                {overviewTimeline.slice(0, 4).map((event) => (
                  <div className="wiki-context-link" key={event.id}>
                    <CalendarDays size={14} />
                    <span>{event.title}</span>
                  </div>
                ))}
              </section>
            )}
          </>
        )}
      </aside>
    </div>
  );
};

export default WorldWiki;
