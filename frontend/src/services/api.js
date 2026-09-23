import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

export const api = {
  // Companies
  getCompanies: async () => {
    try {
      const response = await apiClient.get('/companies');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch companies:', error);
      throw error;
    }
  },

  // Claim Analysis
  analyzeClaim: async ({ company_id, claim_text, category = 'Climate' }) => {
    try {
      const response = await apiClient.post('/claims/analyze', {
        company_id,
        claim_text,
        category,
      });
      return response.data;
    } catch (error) {
      console.error('Claim analysis failed:', error);
      throw error;
    }
  },

  // History
  getClaimHistory: async (params = {}) => {
    try {
      const response = await apiClient.get('/claims/history', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to fetch claim history:', error);
      throw error;
    }
  },

  getClaimDetails: async (id) => {
    try {
      const response = await apiClient.get(`/claims/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch claim ${id}:`, error);
      throw error;
    }
  },

  // Document Upload
  uploadDocument: async (formData) => {
    try {
      const response = await apiClient.post('/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Document upload failed:', error);
      throw error;
    }
  },

  getDocuments: async (companyId = null) => {
    try {
      const params = companyId ? { company_id: companyId } : {};
      const response = await apiClient.get('/documents', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to fetch documents:', error);
      throw error;
    }
  },

  // Health
  checkHealth: async () => {
    try {
      const response = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      return { status: 'offline', error: error.message };
    }
  }
};

export default api;
