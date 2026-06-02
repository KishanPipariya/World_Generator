import api from '../apiClient';
import type { DemoWorld, World } from '../apiTypes';

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
