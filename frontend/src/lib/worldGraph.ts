import type { Edge, Node } from '@xyflow/react';
import type { Entity, Relationship } from './api';

export type EntityGraphNode = Node<{
  label: string;
  entityType: string;
  highlighted: boolean;
  selected: boolean;
}>;

export type RelationshipGraphEdge = Edge<{
  highlighted: boolean;
  selected: boolean;
}>;

export interface WorldSearchResult {
  query: string;
  filteredEntities: Entity[];
  matchingEntityIds: Set<string>;
  matchingRelationshipIds: Set<string>;
  highlightedEntityIds: Set<string>;
  highlightedRelationshipIds: Set<string>;
}

const normalized = (value: string | null | undefined) => value?.toLowerCase().trim() ?? '';

const includesQuery = (value: string | null | undefined, query: string) => (
  normalized(value).includes(query)
);

export const searchWorldGraph = (
  entities: Entity[],
  relationships: Relationship[],
  rawQuery: string,
): WorldSearchResult => {
  const query = normalized(rawQuery);
  const matchingEntityIds = new Set<string>();
  const matchingRelationshipIds = new Set<string>();
  const highlightedEntityIds = new Set<string>();
  const highlightedRelationshipIds = new Set<string>();

  if (!query) {
    return {
      query,
      filteredEntities: entities,
      matchingEntityIds,
      matchingRelationshipIds,
      highlightedEntityIds,
      highlightedRelationshipIds,
    };
  }

  entities.forEach((entity) => {
    if (
      includesQuery(entity.name, query)
      || includesQuery(entity.entity_type, query)
      || includesQuery(entity.description, query)
    ) {
      matchingEntityIds.add(entity.id);
      highlightedEntityIds.add(entity.id);
    }
  });

  relationships.forEach((relationship) => {
    if (
      includesQuery(relationship.source_entity_name, query)
      || includesQuery(relationship.target_entity_name, query)
      || includesQuery(relationship.relation_type, query)
      || includesQuery(relationship.notes, query)
    ) {
      matchingRelationshipIds.add(relationship.id);
      highlightedRelationshipIds.add(relationship.id);
      highlightedEntityIds.add(relationship.source_entity_id);
      highlightedEntityIds.add(relationship.target_entity_id);
    }
  });

  return {
    query,
    filteredEntities: entities.filter((entity) => highlightedEntityIds.has(entity.id)),
    matchingEntityIds,
    matchingRelationshipIds,
    highlightedEntityIds,
    highlightedRelationshipIds,
  };
};

export const buildWorldGraph = (
  entities: Entity[],
  relationships: Relationship[],
  selectedEntityId: string | null,
  selectedRelationshipId: string | null,
  highlightedEntityIds: Set<string>,
  highlightedRelationshipIds: Set<string>,
  positions: Record<string, { x: number; y: number }> = {},
) => {
  const columns = Math.max(1, Math.ceil(Math.sqrt(entities.length)));
  const xSpacing = 240;
  const ySpacing = 150;

  const nodes: EntityGraphNode[] = entities.map((entity, index) => {
    const row = Math.floor(index / columns);
    const column = index % columns;

    return {
      id: entity.id,
      type: 'entity',
      position: {
        x: positions[entity.id]?.x ?? column * xSpacing,
        y: positions[entity.id]?.y ?? row * ySpacing,
      },
      data: {
        label: entity.name,
        entityType: entity.entity_type,
        highlighted: highlightedEntityIds.has(entity.id),
        selected: selectedEntityId === entity.id,
      },
      className: [
        'world-graph-node',
        highlightedEntityIds.has(entity.id) ? 'highlighted' : '',
        selectedEntityId === entity.id ? 'selected' : '',
      ].filter(Boolean).join(' '),
    };
  });

  const entityIds = new Set(entities.map((entity) => entity.id));
  const edges: RelationshipGraphEdge[] = relationships
    .filter((relationship) => (
      entityIds.has(relationship.source_entity_id) && entityIds.has(relationship.target_entity_id)
    ))
    .map((relationship) => ({
      id: relationship.id,
      source: relationship.source_entity_id,
      target: relationship.target_entity_id,
      label: relationship.relation_type,
      type: 'smoothstep',
      animated: highlightedRelationshipIds.has(relationship.id),
      className: [
        'world-graph-edge',
        highlightedRelationshipIds.has(relationship.id) ? 'highlighted' : '',
        selectedRelationshipId === relationship.id ? 'selected' : '',
      ].filter(Boolean).join(' '),
      markerEnd: {
        type: 'arrowclosed',
      },
      data: {
        highlighted: highlightedRelationshipIds.has(relationship.id),
        selected: selectedRelationshipId === relationship.id,
      },
    }));

  return { nodes, edges };
};
