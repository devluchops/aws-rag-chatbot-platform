from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    chat_history: Optional[List[ChatMessage]] = []
    max_results: Optional[int] = 5
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    sources: List[Dict[str, Any]]
    confidence: float
    timestamp: str

class DocumentRequest(BaseModel):
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = {}
    source_url: Optional[str] = None

class DocumentResponse(BaseModel):
    id: str
    title: str
    content: str
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str

class SearchResult(BaseModel):
    id: str
    title: str
    content: str
    score: float
    metadata: Dict[str, Any]
