import boto3
import json
import os
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import BedrockEmbeddings
from langchain_aws import ChatBedrockConverse
from datetime import datetime

# Importar utilidades
from src.core.utils.environment import get_environment_config, is_lambda_environment
from src.core.utils.service_base import ServiceBase

class RAGService(ServiceBase):
    def __init__(self):
        super().__init__()
        
        # Obtener configuración del entorno
        config = get_environment_config()
        self.aws_region = config['aws_region']
        
        self.bedrock_client = boto3.client("bedrock-runtime", region_name=self.aws_region)
        
        # Configurar embeddings
        self.embeddings = BedrockEmbeddings(
            client=self.bedrock_client,
            model_id="amazon.titan-embed-text-v2:0"
        )
        
        # Configurar LLM - usando Claude 3 Haiku (más económico)
        self.llm = ChatBedrockConverse(
            model_id="anthropic.claude-3-haiku-20240307-v1:0"
            # model_kwargs se pasan directamente como parámetros
            # max_tokens=1000,
            # temperature=0.7,
            # top_p=0.9
        )
        
        # Configurar text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
    
    async def generate_response(
        self, 
        question: str, 
        context_documents: List[Dict[str, Any]], 
        chat_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generar respuesta usando RAG
        """
        try:
            # Preparar contexto
            context = self._prepare_context(context_documents)
            
            # Preparar historial de chat
            history_context = self._prepare_chat_history(chat_history or [])
            
            # Crear prompt
            prompt = self._create_prompt(question, context, history_context)
            
            # Generar respuesta
            response = await self._generate_llm_response(prompt)
            
            # Calcular confianza basada en la relevancia de los documentos
            confidence = self._calculate_confidence(context_documents)
            
            # Preparar fuentes
            sources = self._prepare_sources(context_documents)
            
            return {
                "answer": response,
                "sources": sources,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Error generating RAG response: {str(e)}")
    
    def _prepare_context(self, documents: List[Dict[str, Any]]) -> str:
        """Preparar contexto de documentos"""
        context_parts = []
        for doc in documents:
            context_parts.append(f"Documento: {doc.get('title', 'Sin título')}")
            context_parts.append(f"Contenido: {doc.get('content', '')}")
            context_parts.append("---")
        
        return "\n".join(context_parts)
    
    def _prepare_chat_history(self, chat_history: List[Dict[str, str]]) -> str:
        """Preparar historial de chat"""
        if not chat_history:
            return ""
        
        history_parts = []
        for msg in chat_history[-5:]:  # Solo últimos 5 mensajes
            role = msg.get("role", "")
            content = msg.get("content", "")
            history_parts.append(f"{role.capitalize()}: {content}")
        
        return "\n".join(history_parts)
    
    def _create_prompt(self, question: str, context: str, history: str) -> str:
        """Crear prompt para el LLM"""
        prompt = f"""
Eres un asistente inteligente especializado en AWS y tecnologías de nube.

{"Historial de conversación:" if history else ""}
{history}

Contexto de documentos disponibles:
{context}

Pregunta del usuario: {question}

Instrucciones:
1. Si encuentras información relevante en el contexto, responde basándote en ella y cita las fuentes
2. Si NO encuentras información específica en el contexto:
   - Reconoce que no tienes esa información específica en tus documentos
   - Si es sobre tecnología de nube/AWS, proporciona una respuesta general útil
   - Sugiere temas relacionados que sí puedes responder basándote en tus documentos
3. Mantén un tono profesional y amigable
4. Sé claro y conciso en tu respuesta
5. Si la pregunta es sobre AWS o tecnologías relacionadas, puedes usar conocimiento general

Respuesta:
"""
        return prompt
    
    async def _generate_llm_response(self, prompt: str) -> str:
        """Generar respuesta del LLM usando ChatBedrockConverse"""
        try:
            # Usar la nueva API de mensajes
            messages = [
                ("human", prompt)
            ]
            
            # Llamada síncrona (ChatBedrockConverse no tiene versión async nativa)
            response = self.llm.invoke(messages)
            
            # Extraer contenido de la respuesta
            return response.content
            
        except Exception as e:
            raise Exception(f"Error calling Bedrock: {str(e)}")
    
    def _calculate_confidence(self, documents: List[Dict[str, Any]]) -> float:
        """Calcular confianza basada en scores de documentos"""
        if not documents:
            return 0.0
        
        # Calcular confianza promedio basada en scores
        total_score = sum(doc.get("score", 0) for doc in documents)
        avg_score = total_score / len(documents)
        
        # Normalizar a 0-1
        confidence = min(avg_score, 1.0)
        return round(confidence, 2)
    
    def _prepare_sources(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Preparar información de fuentes"""
        sources = []
        for doc in documents:
            sources.append({
                "title": doc.get("title", "Sin título"),
                "content_preview": doc.get("content", "")[:200] + "..." if len(doc.get("content", "")) > 200 else doc.get("content", ""),
                "score": doc.get("score", 0),
                "metadata": doc.get("metadata", {})
            })
        
        return sources
    
    def process_document(self, content: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Procesar documento en chunks"""
        chunks = self.text_splitter.split_text(content)
        
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            processed_chunks.append({
                "content": chunk,
                "metadata": {
                    **(metadata or {}),
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            })
        
        return processed_chunks
