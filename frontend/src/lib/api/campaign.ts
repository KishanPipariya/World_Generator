import api from '../apiClient';
import type { CampaignSession, FactionClock, GenerationSuggestion, LoreNote, MarkdownExport } from '../apiTypes';

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
