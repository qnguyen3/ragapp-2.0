from fastapi import FastAPI, HTTPException, Request, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from typing import List

from .config import settings
from .rag import RAGService
from .db import init_db, close_db
from .models.chat import ChatSession, Message
from .schemas import (
    QueryRequest,
    QueryResponse,
    DocumentResponse,
    ErrorResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    MessageResponse
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
rag_service = RAGService()
mongodb_client = None

@app.on_event("startup")
async def startup_event():
    global mongodb_client
    mongodb_client = await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    if mongodb_client:
        await close_db(mongodb_client)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            message="An unexpected error occurred",
            details=str(exc)
        ).dict(),
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

async def get_chat_session(chat_id: str) -> ChatSession:
    """Get chat session by ID."""
    chat = await ChatSession.get(chat_id)
    if not chat or not chat.is_active:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return chat

@app.post(f"{settings.API_V1_STR}/chats", response_model=ChatSessionResponse)
async def create_chat(chat: ChatSessionCreate):
    """Create a new chat session."""
    try:
        chat_session = ChatSession(**chat.dict())
        await chat_session.insert()
        return await chat_session.to_response_dict()
    except Exception as e:
        logger.error(f"Create chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get(f"{settings.API_V1_STR}/chats", response_model=List[ChatSessionResponse])
async def list_chats():
    """List all active chat sessions."""
    try:
        chats = await ChatSession.get_active_chats()
        return [await chat.to_response_dict() for chat in chats]
    except Exception as e:
        logger.error(f"List chats error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete(f"{settings.API_V1_STR}/chats/{{chat_id}}")
async def delete_chat(chat_id: str):
    """Delete a chat session."""
    try:
        chat = await get_chat_session(chat_id)
        await chat.delete_chat()
        return {"message": "Chat deleted successfully"}
    except Exception as e:
        logger.error(f"Delete chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post(f"{settings.API_V1_STR}/chats/{{chat_id}}/query", response_model=QueryResponse)
async def query_documents(
    chat_id: str,
    request: QueryRequest,
    chat: ChatSession = Depends(get_chat_session)
):
    """Query the RAG system with a question"""
    try:
        # Get recent chat history
        recent_messages = await chat.get_recent_messages(settings.MAX_CHAT_HISTORY)
        chat_history = chat.format_chat_history(recent_messages)

        # Save the question first
        await chat.add_message(request.question, "question")
        
        # Query with more context chunks and chat history
        response = rag_service.query(
            question=request.question,
            n_results=settings.MAX_CONTEXT_CHUNKS,
            chat_history=chat_history
        )

        # Save the answer
        await chat.add_message(response, "answer")

        # Get the updated chat session with messages
        updated_chat = await ChatSession.get(chat.id)
        chat_response = await updated_chat.to_response_dict()
        
        return {
            "answer": response,
            "chat": chat_response
        }
    except Exception as e:
        logger.error(f"Query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post(f"{settings.API_V1_STR}/documents")
async def upload_document(file: UploadFile):
    """Upload and ingest a PDF document"""
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Save the uploaded file temporarily
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process the document
        rag_service.ingest_pdf(temp_path)
        
        # Clean up
        import os
        os.remove(temp_path)
        
        return {"message": f"Successfully ingested {file.filename}"}
    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get(f"{settings.API_V1_STR}/documents", response_model=List[DocumentResponse])
async def list_documents():
    """List all ingested documents"""
    try:
        results = rag_service.list_documents()
        return [
            DocumentResponse(source=source)
            for source in results
        ]
    except Exception as e:
        logger.error(f"List documents error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
