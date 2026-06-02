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
