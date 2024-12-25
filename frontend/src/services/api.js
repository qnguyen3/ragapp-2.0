import axios from 'axios';
import config from '../config';

const api = axios.create({
  baseURL: config.api.baseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post(config.api.endpoints.documents, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const queryDocument = async (chatId, question, n_results = 5) => {
  const response = await api.post(config.api.endpoints.chatQuery(chatId), {
    question,
    n_results,
  });
  return response.data;
};

export const createChat = async (title, documentName) => {
  const response = await api.post(config.api.endpoints.chats, {
    title,
    document_name: documentName,
  });
  return response.data;
};

export const listChats = async () => {
  const response = await api.get(config.api.endpoints.chats);
  return response.data;
};

export const deleteChat = async (chatId) => {
  const response = await api.delete(`${config.api.endpoints.chats}/${chatId}`);
  return response.data;
};

export const listDocuments = async () => {
  const response = await api.get(config.api.endpoints.documents);
  return response.data;
};

// Error handler wrapper
export const withErrorHandler = async (apiCall) => {
  try {
    return await apiCall();
  } catch (error) {
    console.error('API Error:', error);
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      throw new Error(error.response.data.detail || 'Server error');
    } else if (error.request) {
      // The request was made but no response was received
      throw new Error('No response from server');
    } else {
      // Something happened in setting up the request that triggered an Error
      throw new Error('Error setting up request');
    }
  }
};

export default {
  uploadDocument,
  queryDocument,
  listDocuments,
  withErrorHandler,
};
