const API_BASE = '/api';

export const getAuthToken = () => localStorage.getItem('token');
export const setAuthToken = (token) => localStorage.setItem('token', token);
export const removeAuthToken = () => localStorage.removeItem('token');

async function request(path, options = {}) {
  const token = getAuthToken();
  const headers = {
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (options.body && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(options.body);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMsg = 'An error occurred';
    try {
      const errData = await response.json();
      errorMsg = errData.detail || errData.message || errorMsg;
    } catch {
      errorMsg = `HTTP ${response.status}: ${response.statusText}`;
    }
    throw new Error(errorMsg);
  }

  // Handle empty responses
  if (response.status === 204) return null;
  return response.json();
}

export const api = {
  // Auth
  login: async (email, password) => {
    const data = await request('/auth/login', {
      method: 'POST',
      body: { email, password },
    });
    if (data.access_token) {
      setAuthToken(data.access_token);
    }
    return data;
  },
  getCurrentUser: () => request('/auth/me'),
  logout: () => {
    removeAuthToken();
  },

  // Runs
  getRuns: (page = 1, per_page = 20) => request(`/runs/?page=${page}&per_page=${per_page}`),
  getRun: (id) => request(`/runs/${id}`),
  uploadFiles: (formData) => {
    return request('/runs/', {
      method: 'POST',
      body: formData,
    });
  },

  // Reports
  getReports: (runId) => request(`/runs/${runId}/results`),
  getReport: (id) => request(`/reports/${id}`),

  // Metrics
  getMetrics: (runId) => request(`/reports/metrics/${runId}`),
  getGlobalMetrics: () => request('/reports/summary'),

  // Health
  getHealth: () => request('/health'),
};
