const config = {
  api: {
    baseUrl: 'http://localhost:3456',
    endpoints: {
      query: '/api/v1/query',
      documents: '/api/v1/documents',
      chats: '/api/v1/chats',
      chatQuery: (chatId) => `/api/v1/chats/${chatId}/query`,
    },
  },
  upload: {
    acceptedFileTypes: {
      'application/pdf': ['.pdf'],
    },
    maxFileSize: 50 * 1024 * 1024, // 50MB
  },
  suggestions: {
    defaultQuestions: [
      "What are the key findings?",
      "What is the main conclusion?",
      "Can you summarize this?",
      "What are the recommendations?"
    ],
  },
};

export default config;
