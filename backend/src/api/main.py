from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import boto3
import json
import os
from datetime import datetime

# Importar utilidades
from src.core.utils.environment import get_environment_config, is_lambda_environment

from src.services.rag_service import RAGService
from src.services.opensearch_service import OpenSearchService
from src.services.document_processor_service import DocumentProcessorService
from src.models.chat_models import ChatRequest, ChatResponse, DocumentRequest

# Cargar configuración de entorno
if not is_lambda_environment():
    from dotenv import load_dotenv
    load_dotenv()

# Configuración de la aplicación
app = FastAPI(
    title="AWS RAG Chatbot API",
    description="API para chatbot con Retrieval-Augmented Generation usando AWS",
    version="1.0.0"
)

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servicios (inicializar solo cuando se necesiten)
rag_service = None
opensearch_service = None
document_processor_service = None

def get_rag_service():
    global rag_service
    if rag_service is None:
        rag_service = RAGService()
    return rag_service

def get_opensearch_service():
    global opensearch_service
    if opensearch_service is None:
        opensearch_service = OpenSearchService()
    return opensearch_service

def get_document_processor_service():
    global document_processor_service
    if document_processor_service is None:
        document_processor_service = DocumentProcessorService()
    return document_processor_service

@app.get("/")
async def root():
    return {"message": "AWS RAG Chatbot API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint principal para el chat con RAG
    """
    try:
        opensearch_svc = get_opensearch_service()
        rag_svc = get_rag_service()
        
        # Buscar documentos relevantes
        relevant_docs = await opensearch_svc.search_documents(
            query=request.message,
            max_results=request.max_results or 5
        )
        
        # Generar respuesta usando RAG
        response = await rag_svc.generate_response(
            question=request.message,
            context_documents=relevant_docs,
            chat_history=request.chat_history or []
        )
        
        return ChatResponse(
            message=response["answer"],
            sources=response["sources"],
            confidence=response["confidence"],
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/upload")
async def upload_document(request: DocumentRequest):
    """
    Subir y indexar documentos
    """
    try:
        processor = get_document_processor_service()
        
        # Procesar documento directamente
        result = await processor.process_direct_document(
            title=request.title,
            content=request.content,
            metadata=request.metadata or {}
        )
        
        return {
            "message": "Document processed successfully",
            "document_id": result["document_id"],
            "title": result["title"],
            "content_length": result["content_length"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/process-s3")
async def process_s3_document(bucket: str, key: str):
    """
    Procesar documento desde S3
    """
    try:
        processor = get_document_processor_service()
        
        # Procesar documento desde S3
        result = await processor.process_s3_file(bucket, key)
        
        return {
            "message": "S3 document processed successfully",
            "document_id": result["document_id"],
            "bucket": result["bucket"],
            "key": result["key"],
            "content_length": result["content_length"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def list_documents():
    """
    Listar documentos indexados
    """
    try:
        opensearch_svc = get_opensearch_service()
        documents = await opensearch_svc.list_documents()
        return {"documents": documents}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """
    Eliminar documento
    """
    try:
        opensearch_svc = get_opensearch_service()
        result = await opensearch_svc.delete_document(document_id)
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
async def search_documents(query: str, max_results: int = 10):
    """
    Buscar documentos
    """
    try:
        opensearch_svc = get_opensearch_service()
        results = await opensearch_svc.search_documents(query, max_results)
        return {"results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
