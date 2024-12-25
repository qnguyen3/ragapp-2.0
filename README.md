# RAG Application

A desktop application for document question-answering using Retrieval-Augmented Generation (RAG).

## Features

- PDF document upload and processing
- Interactive chat interface
- Persistent chat history
- Document management
- Efficient context retrieval
- macOS native application

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Node.js 14 or higher
- MongoDB
- Docker Desktop for Mac

### Backend Setup

1. Start MongoDB for development:
```bash
docker-compose -f docker-compose.dev.yml up -d
```

2. Create a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Start the backend server:
```bash
python run.py
```

The backend server will run on http://localhost:3456.

5. To stop MongoDB when done:
```bash
docker-compose -f docker-compose.dev.yml down
```

### Data Persistence

The application uses two databases for data storage:

1. MongoDB (running in Docker):
   - Stores chat sessions and message history
   - Data is persisted in ./data/mongodb during development
   - Production data is stored in ~/.ragapp/mongodb_data

2. ChromaDB:
   - Stores document embeddings for semantic search
   - Development data in ./data/chroma_db
   - Production data in ~/.ragapp/chroma_db

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

## Building for Distribution

### Prerequisites

- Docker Desktop for Mac
- Node.js and npm
- Python 3.10+

### Build Steps

1. Make the build script executable:
```bash
chmod +x build_mac_app.sh
```

2. Run the build script:
```bash
./build_mac_app.sh
```

This will:
- Build the Docker images for the backend services
- Package the Electron application
- Create a distributable package in the `dist` directory

The final package will be available as `dist/RAGApp-macOS.zip`

## Distribution Package Contents

The distribution package includes:
- RAG Application (macOS app)
- Docker images for backend services
- Installation and startup scripts
- Documentation

## Installation (for end users)

1. Install Docker Desktop for Mac
2. Unzip RAGApp-macOS.zip
3. Run the installer:
```bash
./install.sh
```
4. Start the backend services:
```bash
./start_ragapp.sh
```
5. Launch the application from the Applications folder

## Architecture

The application consists of three main components:

1. Frontend (Electron + React):
   - User interface
   - Document upload
   - Chat interface
   - Session management

2. Backend (FastAPI):
   - Document processing
   - RAG implementation
   - API endpoints
   - PDF handling

3. Databases:
   - MongoDB (chat sessions, messages)
   - ChromaDB (document embeddings)

## Development Notes

- The backend runs on port 3456
- MongoDB runs on default port 27017
- All data is stored in ~/.ragapp directory
- Docker containers auto-restart unless stopped

## Troubleshooting

Common issues and solutions:

1. Port conflicts:
   - Check if ports 3456 or 27017 are in use
   - Use `lsof -i :PORT` to check port usage

2. Docker issues:
   - Ensure Docker Desktop is running
   - Check container logs: `docker-compose logs`

3. Application not starting:
   - Check backend services: `docker ps`
   - View logs: `docker-compose logs backend`

## License

MIT License
