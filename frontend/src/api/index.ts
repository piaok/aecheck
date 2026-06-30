import axios from 'axios';
import { ValidateResponse } from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

export const validateStandards = async (text: string): Promise<ValidateResponse> => {
  const response = await api.post('/validate', { text });
  return response.data;
};

export const checkHealth = async (): Promise<{ status: string }> => {
  const response = await api.get('/health');
  return response.data;
};