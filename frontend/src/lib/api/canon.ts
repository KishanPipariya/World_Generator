import api from '../apiClient';
import type { Entity, Relationship } from '../apiTypes';

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
