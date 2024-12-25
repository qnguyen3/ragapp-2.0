from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class MessageBase(BaseModel):
    content: str
    type: str

class MessageResponse(MessageBase):
    id: str
    chat_id: str
    created_at: datetime

class ChatSessionBase(BaseModel):
    title: str
    document_name: str

class ChatSessionCreate(ChatSessionBase):
    pass

class ChatSessionResponse(BaseModel):
    id: str
    title: str
    document_name: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []
    is_active: bool = True

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ErrorResponse(BaseModel):
    message: str
    details: Optional[str] = None

class QueryRequest(BaseModel):
    question: str = Field(..., description="The question to ask about the documents")
    n_results: int = Field(default=3, ge=1, le=10, description="Number of relevant chunks to consider")

class QueryResponse(BaseModel):
    answer: str = Field(..., description="The generated answer to the question")
    chat: ChatSessionResponse = Field(..., description="Updated chat session with new messages")

class DocumentResponse(BaseModel):
    source: str = Field(..., description="The source/path of the document")

class DocumentList(BaseModel):
    documents: List[DocumentResponse]
