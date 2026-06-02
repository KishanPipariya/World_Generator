import api from '../apiClient';
import type { ConsistencyIssueState, ConsistencyIssueStatus, ConsistencyReport, GenerationSuggestion, HealthStatus, MarkdownExport } from '../apiTypes';

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
