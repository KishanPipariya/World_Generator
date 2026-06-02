import type { Edge, Node } from '@xyflow/react';
import type { Entity, GraphLayoutMode, Relationship, TimelineEvent } from './apiTypes';

export type EntityGraphNode = Node<{
  label: string;
  entityType: string;
  highlighted: boolean;
  selected: boolean;
  relationshipCount: number;
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

const displayType = (type: string) => {
  const value = normalized(type);
  if (['character', 'person', 'historical figure'].includes(value)) return 'Character';
  if (['location', 'city', 'region', 'landmark', 'continent'].includes(value)) return 'Location';
  if (['faction', 'guild', 'kingdom', 'organization'].includes(value)) return 'Faction';
  if (['concept', 'magic system', 'technology', 'term'].includes(value)) return 'Concept';
  if (['event', 'historical event', 'battle'].includes(value)) return 'Event';
  return 'Other';
};

const layoutPosition = (
  entity: Entity,
  index: number,
  entities: Entity[],
  relationships: Relationship[],
  mode: GraphLayoutMode,
  timelineEvents: TimelineEvent[],
) => {
  if (mode === 'type_columns') {
    const typeOrder = ['Character', 'Faction', 'Location', 'Event', 'Concept', 'Other'];
    const type = displayType(entity.entity_type);
    const column = Math.max(0, typeOrder.indexOf(type));
    const row = entities.filter((item) => displayType(item.entity_type) === type).findIndex((item) => item.id === entity.id);
    return { x: column * 260, y: row * 145 };
  }

  if (mode === 'faction_clusters') {
    const factionRelationships = relationships.filter((relationship) => (
      relationship.source_entity_id === entity.id || relationship.target_entity_id === entity.id
    ));
    const firstFaction = factionRelationships.find((relationship) => {
      const otherId = relationship.source_entity_id === entity.id
        ? relationship.target_entity_id
        : relationship.source_entity_id;
      return displayType(entities.find((item) => item.id === otherId)?.entity_type ?? '') === 'Faction';
    });
    const anchorId = displayType(entity.entity_type) === 'Faction'
      ? entity.id
      : firstFaction?.source_entity_id === entity.id
        ? firstFaction.target_entity_id
        : firstFaction?.source_entity_id;
    const factionIds = entities.filter((item) => displayType(item.entity_type) === 'Faction').map((item) => item.id);
    const cluster = Math.max(0, factionIds.indexOf(anchorId ?? ''));
    const angle = (index % 8) * (Math.PI / 4);
    const radius = displayType(entity.entity_type) === 'Faction' ? 0 : 145 + (index % 3) * 28;
    return {
      x: cluster * 360 + Math.cos(angle) * radius,
      y: 80 + Math.sin(angle) * radius,
    };
  }

  if (mode === 'timeline_order') {
    const timelineIndex = timelineEvents.findIndex((event) => (
      event.participants.includes(entity.id) || normalized(event.title).includes(normalized(entity.name))
    ));
    const column = timelineIndex >= 0 ? timelineIndex : index;
    return { x: column * 240, y: timelineIndex >= 0 ? 40 : 230 + (index % 3) * 120 };
  }

  if (mode === 'force') {
    const degree = relationships.filter((relationship) => (
      relationship.source_entity_id === entity.id || relationship.target_entity_id === entity.id
    )).length;
    const angle = (index / Math.max(1, entities.length)) * Math.PI * 2;
    const radius = Math.max(120, 380 - degree * 45);
    return {
      x: Math.cos(angle) * radius + 360,
      y: Math.sin(angle) * radius + 260,
    };
  }

  const columns = Math.max(1, Math.ceil(Math.sqrt(entities.length)));
  return {
    x: (index % columns) * 240,
    y: Math.floor(index / columns) * 150,
  };
};

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
  layoutMode: GraphLayoutMode = 'manual',
  timelineEvents: TimelineEvent[] = [],
) => {
  const relationshipCounts = relationships.reduce<Record<string, number>>((counts, relationship) => {
    counts[relationship.source_entity_id] = (counts[relationship.source_entity_id] ?? 0) + 1;
    counts[relationship.target_entity_id] = (counts[relationship.target_entity_id] ?? 0) + 1;
    return counts;
  }, {});

  const nodes: EntityGraphNode[] = entities.map((entity, index) => {
    const generatedPosition = layoutPosition(entity, index, entities, relationships, layoutMode, timelineEvents);
    const storedPosition = layoutMode === 'manual' ? positions[entity.id] : undefined;

    return {
      id: entity.id,
      type: 'entity',
      position: storedPosition ?? generatedPosition,
      data: {
        label: entity.name,
        entityType: entity.entity_type,
        highlighted: highlightedEntityIds.has(entity.id),
        selected: selectedEntityId === entity.id,
        relationshipCount: relationshipCounts[entity.id] ?? 0,
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
      style: {
        stroke: relationship.color ?? undefined,
        strokeWidth: relationship.display_priority ? Math.min(5, 1.5 + relationship.display_priority / 3) : undefined,
      },
      className: [
        'world-graph-edge',
        relationship.stance ? `stance-${relationship.stance}` : '',
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
