# RAG Application Frontend

An Electron-based desktop application for document question-answering using Retrieval-Augmented Generation (RAG).

## Features

- PDF document upload with drag & drop support
- Interactive chat interface with message history
- Persistent chat sessions
- Suggested questions
- Real-time responses
- Error handling and loading states
- Desktop native experience

## Prerequisites

- Node.js (v14 or higher)
- npm (v6 or higher)
- Python backend server running (see main README.md)

## Installation

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Create a `.env` file in the frontend directory (optional):
```
REACT_APP_API_URL=http://localhost:3456
```

## Development

Run the application in development mode:
```bash
npm run dev
```

This will:
1. Start the React development server
2. Launch the Electron application
3. Enable hot-reloading for both React and Electron

## Building

Build the application for production:
```bash
npm run build
```

This will create a production build in the `build` directory.

## Project Structure

```
frontend/
├── public/              # Static files
├── src/                 # Source code
│   ├── components/      # React components
│   │   ├── Chat.js           # Chat interface
│   │   ├── ChatSidebar.js    # Chat sessions sidebar
│   │   ├── FileUpload.js     # File upload component
│   │   ├── ErrorSnackbar.js  # Error handling component
│   │   └── ScrollToBottom.js # Scroll button component
│   ├── services/        # API services
│   │   └── api.js      # API client
│   ├── config.js       # Application configuration
│   ├── App.js          # Main React component
│   └── index.js        # Application entry point
├── main.js             # Electron main process
└── package.json        # Project dependencies and scripts
```

## Features

### Chat Sessions
- Create multiple chat sessions for different documents
- View chat history with timestamps
- Delete chat sessions
- Clear chat history
- Scroll through long conversations with ease

### Document Upload
- Drag and drop PDF files
- File size limit: 50MB
- Automatic chat session creation

### Chat Interface
- Real-time message updates
- Message timestamps
- Loading indicators
- Error handling
- Suggested questions
- Keyboard shortcuts (Enter to send)
- Scroll to bottom button for long conversations

## Usage

1. Start the Python backend server first (see main README.md)
2. Launch the Electron application using `npm run dev`
3. Upload a PDF document using the file upload interface
4. Start chatting with the document using the chat interface
5. Use suggested questions or type your own questions
6. Create new chats or switch between existing ones using the sidebar
7. Delete chats or create new ones as needed

## Notes

- The application requires the backend server to be running on `http://localhost:3456`
- Only PDF files are currently supported
- Maximum file size is 50MB by default (configurable in config.js)
- Chat history is persisted in MongoDB
- Document embeddings are stored in ChromaDB
