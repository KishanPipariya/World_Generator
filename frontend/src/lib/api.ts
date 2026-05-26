import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
});

export interface World {
  id: string;
  title: string;
  tone: string | null;
  era_notes: string | null;
  seed: string | null;
  created_at: string;
}

export interface Entity {
  id: string;
  world_id: string;
  name: string;
  entity_type: string;
  description: string;
  structured_fields: Record<string, string>;
  created_at: string;
}

export interface Relationship {
  id: string;
  world_id: string;
  source_entity_id: string;
  source_entity_name: string;
  target_entity_id: string;
  target_entity_name: string;
  relation_type: string;
  notes: string | null;
  category: string | null;
  strength: number | null;
  history: string | null;
  created_at: string;
}

export interface MarkdownExport {
  world_id: string;
  filename: string;
  content: string;
  preset: string;
}

export interface DemoWorld {
  world: World;
  entities: Entity[];
  relationships: Relationship[];
}

export interface ConsistencyIssue {
  code: string;
  severity: 'info' | 'warning' | 'error';
  message: string;
  entity_id: string | null;
  relationship_id: string | null;
}

export interface ConsistencyReport {
  world_id: string;
  score: number;
  summary: string;
  issues: ConsistencyIssue[];
}

export interface GenerationSuggestion {
  id: string;
  world_id: string;
  instruction: string;
  content: string;
  suggested_name: string | null;
  suggested_type: string | null;
  status: 'pending' | 'accepted' | 'discarded';
  created_at: string;
}

export interface TimelineEvent {
  id: string;
  world_id: string;
  title: string;
  event_order: number;
  description: string;
  participants: string[];
  causes: string | null;
  consequences: string | null;
  created_at: string;
}

export interface RevisionVersion {
  id: string;
  world_id: string;
  entity_id: string | null;
  subject_type: 'entity' | 'world';
  field_name: string;
  previous_value: string | null;
  new_value: string | null;
  source: 'manual' | 'generated' | 'restore';
  created_at: string;
}

export interface PassageCheckIssue {
  code: string;
  severity: 'info' | 'warning' | 'error';
  message: string;
  entity_id: string | null;
}

export interface PassageCheck {
  world_id: string;
  summary: string;
  issues: PassageCheckIssue[];
}

export interface HealthStatus {
  status: string;
  llm: {
    mode: string;
    enabled: boolean;
  };
}

export const fetchWorlds = async (): Promise<World[]> => {
  const response = await api.get('/worlds');
  return response.data;
};

export const fetchWorld = async (id: string): Promise<World> => {
  const response = await api.get(`/worlds/${id}`);
  return response.data;
};

export const createWorld = async (world: Partial<World>): Promise<World> => {
  const response = await api.post('/worlds', world);
  return response.data;
};

export const createDemoWorld = async (): Promise<DemoWorld> => {
  const response = await api.post('/worlds/demo');
  return response.data;
};

export const deleteWorld = async (worldId: string): Promise<void> => {
  await api.delete(`/worlds/${worldId}`);
};

export const fetchEntities = async (worldId: string): Promise<Entity[]> => {
  const response = await api.get(`/worlds/${worldId}/entities`);
  return response.data.entities;
};

export const createEntity = async (
  worldId: string,
  entity: Pick<Entity, 'name' | 'entity_type' | 'description'> & { structured_fields?: Record<string, string> },
): Promise<Entity> => {
  const response = await api.post(`/worlds/${worldId}/entities`, entity);
  return response.data;
};

export const updateEntity = async (
  worldId: string,
  entityId: string,
  entity: Partial<Pick<Entity, 'name' | 'entity_type' | 'description' | 'structured_fields'>>,
): Promise<Entity> => {
  const response = await api.patch(`/worlds/${worldId}/entities/${entityId}`, entity);
  return response.data;
};

export const deleteEntity = async (worldId: string, entityId: string): Promise<void> => {
  await api.delete(`/worlds/${worldId}/entities/${entityId}`);
};

export const fetchRelationships = async (worldId: string): Promise<Relationship[]> => {
  const response = await api.get(`/worlds/${worldId}/relationships`);
  return response.data.relationships;
};

export const createRelationship = async (
  worldId: string,
  relationship: {
    source_entity_id: string;
    target_entity_id: string;
    relation_type: string;
    notes?: string;
    category?: string;
    strength?: number;
    history?: string;
  },
): Promise<Relationship> => {
  const response = await api.post(`/worlds/${worldId}/relationships`, relationship);
  return response.data;
};

export const deleteRelationship = async (
  worldId: string,
  relationshipId: string,
): Promise<void> => {
  await api.delete(`/worlds/${worldId}/relationships/${relationshipId}`);
};

export const exportMarkdown = async (
  worldId: string,
  preset = 'full_bible',
): Promise<MarkdownExport> => {
  const response = await api.get(`/worlds/${worldId}/export/markdown`, { params: { preset } });
  return response.data;
};

export const fetchConsistencyReport = async (worldId: string): Promise<ConsistencyReport> => {
  const response = await api.get(`/worlds/${worldId}/consistency`);
  return response.data;
};

export const fetchHealth = async (): Promise<HealthStatus> => {
  const response = await api.get('/health');
  return response.data;
};

export const generateAgentic = async (
  worldId: string, 
  instruction: string, 
  saveAsConfig?: { entityType: string, name: string }
) => {
  const payload = {
    instruction,
    save_as_entity_type: saveAsConfig?.entityType,
    save_as_name: saveAsConfig?.name
  };
  const response = await api.post(`/worlds/${worldId}/agentic-generate`, payload);
  return response.data;
};

export const fetchSuggestions = async (worldId: string): Promise<GenerationSuggestion[]> => {
  const response = await api.get(`/worlds/${worldId}/suggestions`);
  return response.data.suggestions;
};

export const applySuggestion = async (
  worldId: string,
  suggestionId: string,
  payload: {
    mode: 'create_entity' | 'append_to_entity' | 'replace_entity' | 'discard';
    entity_id?: string;
    name?: string;
    entity_type?: string;
    description?: string;
  },
) => {
  const response = await api.post(`/worlds/${worldId}/suggestions/${suggestionId}/apply`, payload);
  return response.data;
};

export const fetchTimelineEvents = async (worldId: string): Promise<TimelineEvent[]> => {
  const response = await api.get(`/worlds/${worldId}/timeline`);
  return response.data.events;
};

export const createTimelineEvent = async (
  worldId: string,
  event: Pick<TimelineEvent, 'title' | 'event_order' | 'description' | 'participants' | 'causes' | 'consequences'>,
): Promise<TimelineEvent> => {
  const response = await api.post(`/worlds/${worldId}/timeline`, event);
  return response.data;
};

export const fetchRevisions = async (
  worldId: string,
  entityId?: string,
): Promise<RevisionVersion[]> => {
  const response = await api.get(`/worlds/${worldId}/revisions`, { params: { entity_id: entityId } });
  return response.data.versions;
};

export const restoreRevision = async (worldId: string, revisionId: string): Promise<Entity> => {
  const response = await api.post(`/worlds/${worldId}/revisions/${revisionId}/restore`);
  return response.data;
};

export const checkPassage = async (worldId: string, passage: string): Promise<PassageCheck> => {
  const response = await api.post(`/worlds/${worldId}/passage-check`, { passage });
  return response.data;
};

export default api;
