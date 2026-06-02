import { BookOpen, Plus, Search } from 'lucide-react';
import type { Entity } from '../../../lib/apiTypes';
import { IconButton } from '../../atoms';

export function EntityBrowser({
  groupedEntities,
  entityCount,
  query,
  selectedEntityId,
  matchingEntityIds,
  filteredCount,
  onQueryChange,
  onNewEntity,
  onSelectEntity,
}: {
  groupedEntities: { group: string; items: Entity[] }[];
  entityCount: number;
  query: string;
  selectedEntityId: string | null;
  matchingEntityIds: Set<string>;
  filteredCount: number;
  onQueryChange: (value: string) => void;
  onNewEntity: () => void;
  onSelectEntity: (entityId: string) => void;
}) {
  return (
    <aside className="entity-browser glass" aria-label="World bible entity browser">
      <div className="panel-title">
        <BookOpen size={18} />
        <h2>World Bible</h2>
        <IconButton onClick={onNewEntity} title="New entity" aria-label="Create new entity">
          <Plus size={18} />
        </IconButton>
      </div>
      <label className="entity-search">
        <Search size={16} />
        <input
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Search this world"
          type="search"
        />
      </label>
      {entityCount === 0 ? (
        <p className="text-muted">No saved entities yet.</p>
      ) : query && filteredCount === 0 ? (
        <p className="text-muted">No matches in this world.</p>
      ) : (
        groupedEntities.map(({ group, items }) => (
          items.length > 0 && (
            <div className="entity-group" key={group}>
              <h3>{group}</h3>
              {items.map((entity) => (
                <button
                  className={[
                    'entity-list-item',
                    selectedEntityId === entity.id ? 'active' : '',
                    matchingEntityIds.has(entity.id) ? 'search-match' : '',
                  ].filter(Boolean).join(' ')}
                  key={entity.id}
                  onClick={() => onSelectEntity(entity.id)}
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
  );
}
