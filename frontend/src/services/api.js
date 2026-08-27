import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

export const createSession = async (title = "New Chat") => {
  const response = await axios.post(`${API_BASE}/sessions`, null, {
    params: { title }
  });
  return response.data;
};

export const getSessions = async () => {
  const response = await axios.get(`${API_BASE}/sessions`);
  return response.data;
};

export const getSessionMessages = async (sessionId) => {
  const response = await axios.get(`${API_BASE}/sessions/${sessionId}/messages`);
  return response.data;
};

export const getSessionDocuments = async (sessionId) => {
  const response = await axios.get(`${API_BASE}/sessions/${sessionId}/documents`);
  return response.data;
};

export const deleteSession = async (sessionId) => {
  const response = await axios.delete(`${API_BASE}/sessions/${sessionId}`);
  return response.data;
};

export const deleteDocument = async (documentId) => {
  const response = await axios.delete(`${API_BASE}/documents/${documentId}`);
  return response.data;
};

export const uploadPdf = async (file, sessionId = null) => {
  const formData = new FormData();
  formData.append('file', file);
  if (sessionId) {
    formData.append('session_id', sessionId);
  }
  
  const response = await axios.post(`${API_BASE}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const queryDocument = async (question, sessionId) => {
  const response = await axios.post(`${API_BASE}/query`, null, {
    params: { question, session_id: sessionId },
  });
  return response.data;
};

