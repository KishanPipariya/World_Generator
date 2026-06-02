import api from '../apiClient';
import type { TokenResponse, User } from '../apiTypes';

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
