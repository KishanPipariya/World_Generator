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
  created_at: string;
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

export default api;
