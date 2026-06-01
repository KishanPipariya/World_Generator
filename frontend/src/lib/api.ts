import axios from 'axios';

export const AUTH_TOKEN_KEY = 'world_generator_access_token';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(AUTH_TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(AUTH_TOKEN_KEY);
      window.dispatchEvent(new Event('world-generator-auth-expired'));
    }
    return Promise.reject(error);
  },
);

export interface User {
  id: string;
  username: string;
  email: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: 'bearer';
}

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
  stance: 'alliance' | 'conflict' | 'neutral' | 'unknown' | null;
  color: string | null;
  display_priority: number | null;
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

export type ConsistencyIssueStatus = 'open' | 'ignored' | 'resolved' | 'reopened';

export interface ConsistencyIssue {
  issue_id?: string | null;
  code: string;
  severity: 'info' | 'warning' | 'error';
  message: string;
  target_type?: 'world' | 'entity' | 'relationship' | null;
  entity_id: string | null;
  relationship_id: string | null;
  status?: ConsistencyIssueStatus | null;
  note?: string | null;
  first_seen?: string | null;
  last_seen?: string | null;
}

export interface ConsistencyReport {
  world_id: string;
  score: number;
  summary: string;
  issues: ConsistencyIssue[];
}

export interface ConsistencyIssueState extends Required<Omit<ConsistencyIssue, 'issue_id'>> {
  id: string;
  world_id: string;
  fingerprint: string;
  status: ConsistencyIssueStatus;
  target_type: 'world' | 'entity' | 'relationship';
  first_seen: string;
  last_seen: string;
  updated_at: string;
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
  candidate_kind: 'entity' | 'relationship' | 'timeline_event' | 'lore_note' | null;
  source_type: 'draft' | 'generation' | 'session' | 'dm' | null;
  source_id: string | null;
  source_excerpt: string | null;
  payload: Record<string, unknown> | null;
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
  date_label: string | null;
  era_label: string | null;
  depends_on: string[];
  created_at: string;
}

export type GraphLayoutMode = 'manual' | 'force' | 'type_columns' | 'faction_clusters' | 'timeline_order';

export interface GraphView {
  id: string;
  world_id: string;
  name: string;
  layout_mode: GraphLayoutMode;
  filters: Record<string, unknown>;
  camera: { x: number; y: number; zoom: number };
  node_positions: Record<string, { x: number; y: number }>;
  created_at: string;
  updated_at: string;
}

export interface PlanningCard {
  id: string;
  board_id: string;
  world_id: string;
  title: string;
  description: string;
  lane: string;
  position: number;
  entity_links: string[];
  relationship_links: string[];
  timeline_event_links: string[];
  created_at: string;
}

export interface PlanningBoard {
  id: string;
  world_id: string;
  name: string;
  board_type: 'arc' | 'chapter' | 'scene' | 'plot_thread' | 'quest' | 'front' | 'session_prep' | 'custom';
  cards: PlanningCard[];
  created_at: string;
}

export interface CampaignSession {
  id: string;
  world_id: string;
  session_number: number;
  title: string;
  played_date: string | null;
  in_world_date: string | null;
  recap: string;
  player_actions: string;
  consequences: string;
  linked_entity_ids: string[];
  linked_relationship_ids: string[];
  linked_timeline_event_ids: string[];
  created_at: string;
  updated_at: string;
}

export interface LoreNote {
  id: string;
  world_id: string;
  title: string;
  body: string;
  subject_type: 'world' | 'entity' | 'relationship' | 'timeline_event' | 'session';
  subject_id: string | null;
  visibility: 'dm_only' | 'player_visible' | 'discovered' | 'redacted';
  truth_state: 'true' | 'false' | 'partial' | 'unknown';
  reveal_condition: string | null;
  handout_text: string | null;
  created_at: string;
  updated_at: string;
}

export interface FactionClock {
  id: string;
  world_id: string;
  title: string;
  linked_entity_id: string | null;
  segments: number;
  filled_segments: number;
  stakes: string;
  status: 'active' | 'paused' | 'completed' | 'failed';
  linked_session_ids: string[];
  linked_entity_ids: string[];
  linked_relationship_ids: string[];
  linked_timeline_event_ids: string[];
  created_at: string;
  updated_at: string;
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

export interface DraftCheckHistoryItem {
  checked_at: string;
  summary: string;
  issues: PassageCheckIssue[];
}

export interface DraftPassage {
  id: string;
  world_id: string;
  title: string;
  body: string;
  status: 'draft' | 'revising' | 'ready' | 'archived';
  linked_entity_ids: string[];
  linked_relationship_ids: string[];
  linked_timeline_event_ids: string[];
  check_history: DraftCheckHistoryItem[];
  created_at: string;
  updated_at: string;
}

export type DraftExtractionCandidateKind = 'entity' | 'relationship' | 'timeline_event' | 'lore_note';

export interface DraftExtractionCandidate {
  candidate_kind: DraftExtractionCandidateKind;
  suggested_name: string;
  suggested_type: string | null;
  content: string;
  payload: Record<string, unknown>;
}

export interface DraftExtractionPreview {
  world_id: string;
  draft_id: string;
  summary: string;
  excerpt: string;
  candidates: DraftExtractionCandidate[];
}

export interface DraftExtractionResult {
  world_id: string;
  draft_id: string;
  summary: string;
  suggestions: GenerationSuggestion[];
}

export interface HealthStatus {
  status: string;
}

export const registerUser = async (payload: {
  username: string;
  email: string;
  password: string;
}): Promise<User> => {
  const response = await api.post('/auth/register', payload);
  return response.data;
};

export const loginUser = async (payload: { username: string; password: string }): Promise<TokenResponse> => {
  const response = await api.post('/auth/login', payload);
  return response.data;
};

export const fetchMe = async (): Promise<User> => {
  const response = await api.get('/auth/me');
  return response.data;
};

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
    stance?: Relationship['stance'];
    color?: string;
    display_priority?: number;
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

export const fetchConsistencyIssues = async (worldId: string): Promise<ConsistencyIssueState[]> => {
  const response = await api.get(`/worlds/${worldId}/consistency/issues`);
  return response.data.issues;
};

export const updateConsistencyIssue = async (
  worldId: string,
  issueId: string,
  payload: { status?: ConsistencyIssueStatus; note?: string | null },
): Promise<ConsistencyIssueState> => {
  const response = await api.patch(`/worlds/${worldId}/consistency/issues/${issueId}`, payload);
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
    mode: 'create_entity' | 'append_to_entity' | 'replace_entity' | 'discard' | 'create_relationship' | 'create_timeline_event' | 'create_lore_note';
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
  event: Pick<TimelineEvent, 'title' | 'event_order' | 'description' | 'participants' | 'causes' | 'consequences' | 'date_label' | 'era_label' | 'depends_on'>,
): Promise<TimelineEvent> => {
  const response = await api.post(`/worlds/${worldId}/timeline`, event);
  return response.data;
};

export const fetchGraphViews = async (worldId: string): Promise<GraphView[]> => {
  const response = await api.get(`/worlds/${worldId}/graph-views`);
  return response.data.views;
};

export const createGraphView = async (
  worldId: string,
  view: Pick<GraphView, 'name' | 'layout_mode' | 'filters' | 'camera' | 'node_positions'>,
): Promise<GraphView> => {
  const response = await api.post(`/worlds/${worldId}/graph-views`, view);
  return response.data;
};

export const fetchPlanningBoards = async (worldId: string): Promise<PlanningBoard[]> => {
  const response = await api.get(`/worlds/${worldId}/planning-boards`);
  return response.data.boards;
};

export const createPlanningBoard = async (
  worldId: string,
  board: Pick<PlanningBoard, 'name' | 'board_type'>,
): Promise<PlanningBoard> => {
  const response = await api.post(`/worlds/${worldId}/planning-boards`, board);
  return { ...response.data, cards: [] };
};

export const createPlanningCard = async (
  worldId: string,
  boardId: string,
  card: Pick<PlanningCard, 'title' | 'description' | 'lane' | 'position' | 'entity_links' | 'relationship_links' | 'timeline_event_links'>,
): Promise<PlanningCard> => {
  const response = await api.post(`/worlds/${worldId}/planning-boards/${boardId}/cards`, card);
  return response.data;
};

export const fetchCampaignSessions = async (worldId: string): Promise<CampaignSession[]> => {
  const response = await api.get(`/worlds/${worldId}/campaign-sessions`);
  return response.data.sessions;
};

export const fetchDmSessions = async (worldId: string): Promise<CampaignSession[]> => {
  const response = await api.get(`/worlds/${worldId}/dm/sessions`);
  return response.data.sessions;
};

export const createCampaignSession = async (
  worldId: string,
  session: Pick<CampaignSession, 'session_number' | 'title' | 'played_date' | 'in_world_date' | 'recap' | 'player_actions' | 'consequences' | 'linked_entity_ids' | 'linked_relationship_ids' | 'linked_timeline_event_ids'>,
): Promise<CampaignSession> => {
  const response = await api.post(`/worlds/${worldId}/campaign-sessions`, session);
  return response.data;
};

export const createDmSession = async (
  worldId: string,
  session: Pick<CampaignSession, 'session_number' | 'title' | 'played_date' | 'in_world_date' | 'recap' | 'player_actions' | 'consequences' | 'linked_entity_ids' | 'linked_relationship_ids' | 'linked_timeline_event_ids'>,
): Promise<CampaignSession> => {
  const response = await api.post(`/worlds/${worldId}/dm/sessions`, session);
  return response.data;
};

export const createCampaignImpactReview = async (
  worldId: string,
  sessionId: string,
  instruction?: string,
): Promise<GenerationSuggestion> => {
  const response = await api.post(`/worlds/${worldId}/campaign-sessions/${sessionId}/impact-review`, { instruction });
  return response.data.suggestion;
};

export const createDmImpactReview = async (
  worldId: string,
  sessionId: string,
  instruction?: string,
): Promise<GenerationSuggestion> => {
  const response = await api.post(`/worlds/${worldId}/dm/sessions/${sessionId}/impact-review`, { instruction });
  return response.data.suggestion;
};

export const fetchDmSuggestions = async (worldId: string): Promise<GenerationSuggestion[]> => {
  const response = await api.get(`/worlds/${worldId}/dm/suggestions`);
  return response.data.suggestions;
};

export const fetchLoreNotes = async (worldId: string): Promise<LoreNote[]> => {
  const response = await api.get(`/worlds/${worldId}/lore-notes`);
  return response.data.notes;
};

export const fetchDmLoreNotes = async (worldId: string): Promise<LoreNote[]> => {
  const response = await api.get(`/worlds/${worldId}/dm/lore-notes`);
  return response.data.notes;
};

export const createLoreNote = async (
  worldId: string,
  note: Pick<LoreNote, 'title' | 'body' | 'subject_type' | 'subject_id' | 'visibility' | 'truth_state' | 'reveal_condition' | 'handout_text'>,
): Promise<LoreNote> => {
  const response = await api.post(`/worlds/${worldId}/lore-notes`, note);
  return response.data;
};

export const createDmLoreNote = async (
  worldId: string,
  note: Pick<LoreNote, 'title' | 'body' | 'subject_type' | 'subject_id' | 'visibility' | 'truth_state' | 'reveal_condition' | 'handout_text'>,
): Promise<LoreNote> => {
  const response = await api.post(`/worlds/${worldId}/dm/lore-notes`, note);
  return response.data;
};

export const fetchFactionClocks = async (worldId: string): Promise<FactionClock[]> => {
  const response = await api.get(`/worlds/${worldId}/faction-clocks`);
  return response.data.clocks;
};

export const fetchDmFactionClocks = async (worldId: string): Promise<FactionClock[]> => {
  const response = await api.get(`/worlds/${worldId}/dm/faction-clocks`);
  return response.data.clocks;
};

export const createFactionClock = async (
  worldId: string,
  clock: Pick<FactionClock, 'title' | 'linked_entity_id' | 'segments' | 'filled_segments' | 'stakes' | 'status' | 'linked_session_ids' | 'linked_entity_ids' | 'linked_relationship_ids' | 'linked_timeline_event_ids'>,
): Promise<FactionClock> => {
  const response = await api.post(`/worlds/${worldId}/faction-clocks`, clock);
  return response.data;
};

export const createDmFactionClock = async (
  worldId: string,
  clock: Pick<FactionClock, 'title' | 'linked_entity_id' | 'segments' | 'filled_segments' | 'stakes' | 'status' | 'linked_session_ids' | 'linked_entity_ids' | 'linked_relationship_ids' | 'linked_timeline_event_ids'>,
): Promise<FactionClock> => {
  const response = await api.post(`/worlds/${worldId}/dm/faction-clocks`, clock);
  return response.data;
};

export const exportDmMarkdown = async (
  worldId: string,
  preset: 'player_handout' | 'session_brief' | 'dm_campaign_brief' = 'dm_campaign_brief',
): Promise<MarkdownExport> => {
  const response = await api.get(`/worlds/${worldId}/dm/export/markdown`, { params: { preset } });
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

export const fetchDrafts = async (worldId: string): Promise<DraftPassage[]> => {
  const response = await api.get(`/worlds/${worldId}/drafts`);
  return response.data.drafts;
};

export const fetchDraft = async (worldId: string, draftId: string): Promise<DraftPassage> => {
  const response = await api.get(`/worlds/${worldId}/drafts/${draftId}`);
  return response.data;
};

export const createDraft = async (
  worldId: string,
  draft: Pick<DraftPassage, 'title' | 'body'> &
    Partial<Pick<DraftPassage, 'status' | 'linked_entity_ids' | 'linked_relationship_ids' | 'linked_timeline_event_ids'>>,
): Promise<DraftPassage> => {
  const response = await api.post(`/worlds/${worldId}/drafts`, draft);
  return response.data;
};

export const updateDraft = async (
  worldId: string,
  draftId: string,
  draft: Partial<Pick<DraftPassage, 'title' | 'body' | 'status' | 'linked_entity_ids' | 'linked_relationship_ids' | 'linked_timeline_event_ids'>>,
): Promise<DraftPassage> => {
  const response = await api.patch(`/worlds/${worldId}/drafts/${draftId}`, draft);
  return response.data;
};

export const deleteDraft = async (worldId: string, draftId: string): Promise<void> => {
  await api.delete(`/worlds/${worldId}/drafts/${draftId}`);
};

export const checkDraft = async (worldId: string, draftId: string): Promise<PassageCheck> => {
  const response = await api.post(`/worlds/${worldId}/drafts/${draftId}/check`);
  return response.data;
};

export const extractDraftExcerpt = async (
  worldId: string,
  draftId: string,
  payload: { excerpt: string; instruction?: string; max_candidates?: number },
): Promise<DraftExtractionResult> => {
  const response = await api.post(`/worlds/${worldId}/drafts/${draftId}/extract`, payload);
  return response.data;
};

export const previewDraftExtraction = async (
  worldId: string,
  draftId: string,
  payload: { excerpt: string; instruction?: string; max_candidates?: number },
): Promise<DraftExtractionPreview> => {
  const response = await api.post(`/worlds/${worldId}/drafts/${draftId}/extract/preview`, payload);
  return response.data;
};

export const queueDraftExtraction = async (
  worldId: string,
  draftId: string,
  payload: { excerpt: string; instruction?: string; candidates: DraftExtractionCandidate[] },
): Promise<DraftExtractionResult> => {
  const response = await api.post(`/worlds/${worldId}/drafts/${draftId}/extract/queue`, payload);
  return response.data;
};

export default api;
