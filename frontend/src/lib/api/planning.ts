import api from '../apiClient';
import type { GraphView, PlanningBoard, PlanningCard, TimelineEvent } from '../apiTypes';

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
