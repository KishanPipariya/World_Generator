import api from '../apiClient';
import type { DraftExtractionCandidate, DraftExtractionPreview, DraftExtractionResult, DraftPassage, Entity, PassageCheck, RevisionVersion } from '../apiTypes';

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
