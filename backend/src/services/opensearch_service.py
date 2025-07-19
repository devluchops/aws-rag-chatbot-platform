import os
import json
import boto3
from typing import List, Dict, Any
from opensearchpy import OpenSearch, RequestsHttpConnection
from datetime import datetime
import hashlib
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Importar utilidades
from src.core.utils.environment import get_environment_config, is_lambda_environment
from src.core.utils.service_base import ServiceBase

class OpenSearchService(ServiceBase):
    def __init__(self):
        super().__init__()
        
        # Obtener configuración del entorno
        config = get_environment_config()
        
        self.opensearch_endpoint = config['opensearch_endpoint']
        self.opensearch_username = config['opensearch_username']
        self.opensearch_password = config['opensearch_password']
        self.aws_region = config['aws_region']
        
        # Configurar cliente OpenSearch
        self.client = OpenSearch(
            hosts=[{"host": self.opensearch_endpoint.replace("https://", "").replace("http://", ""), "port": 443}],
            http_auth=(self.opensearch_username, self.opensearch_password),
            http_compress=True,
            use_ssl=True,
            verify_certs=True,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
            connection_class=RequestsHttpConnection,
            timeout=30,  # Aumentar timeout a 30 segundos
            max_retries=3,  # Máximo 3 reintentos
            retry_on_timeout=True
        )
        
        # Configurar Bedrock para embeddings
        self.bedrock_client = boto3.client("bedrock-runtime", region_name=self.aws_region)
        
        # Nombre del índice
        self.index_name = "chatbot-documents"
        
        # Crear índice si no existe (tanto en local como en Lambda)
        self._create_index_if_not_exists()
    
    def _create_index_if_not_exists(self):
        """Crear índice si no existe"""
        try:
            # Verificar si el índice ya existe
            if self.client.indices.exists(index=self.index_name):
                print(f"Índice {self.index_name} ya existe")
                return
                
            print(f"Creando índice {self.index_name}...")
            index_body = {
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0,
                        "analysis": {
                            "analyzer": {
                                "spanish_analyzer": {
                                    "tokenizer": "standard",
                                    "filter": ["lowercase", "spanish_stop", "spanish_stemmer"]
                                }
                            },
                            "filter": {
                                "spanish_stop": {
                                    "type": "stop",
                                    "stopwords": "_spanish_"
                                },
                                "spanish_stemmer": {
                                    "type": "stemmer",
                                    "language": "spanish"
                                }
                            }
                        }
                    },
                    "mappings": {
                        "properties": {
                            "title": {
                                "type": "text",
                                "analyzer": "spanish_analyzer",
                                "fields": {
                                    "keyword": {
                                        "type": "keyword"
                                    }
                                }
                            },
                            "content": {
                                "type": "text",
                                "analyzer": "spanish_analyzer"
                            },
                            "embedding": {
                                "type": "dense_vector",
                                "dims": 1536
                            },
                            "metadata": {
                                "type": "object"
                            },
                            "created_at": {
                                "type": "date"
                            },
                            "updated_at": {
                                "type": "date"
                            }
                        }
                    }
                }
            
            self.client.indices.create(index=self.index_name, body=index_body)
            print(f"Índice {self.index_name} creado exitosamente")
                
        except Exception as e:
            print(f"Error creando índice: {str(e)}")
            # Log the full exception for debugging
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
    
    def _get_embedding_sync(self, text: str) -> List[float]:
        """Obtener embedding usando Bedrock (versión síncrona)"""
        try:
            response = self.bedrock_client.invoke_model(
                modelId="amazon.titan-embed-text-v2:0",
                body=json.dumps({"inputText": text})
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['embedding']
            
        except Exception as e:
            raise Exception(f"Error getting embedding: {str(e)}")
    
    async def get_embedding(self, text: str) -> List[float]:
        """Obtener embedding usando Bedrock"""
        if self._is_async_context():
            return await self._run_in_executor(self._get_embedding_sync, text)
        else:
            return self._get_embedding_sync(text)
    
    def _index_document_sync(self, title: str, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Indexar documento (versión síncrona)"""
        try:
            # Generar ID único
            doc_id = hashlib.md5(f"{title}{content}".encode()).hexdigest()
            
            # Obtener embedding
            embedding = self._get_embedding_sync(content)
            
            # Preparar documento
            doc_body = {
                "title": title,
                "content": content,
                "embedding": embedding,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Indexar documento
            response = self.client.index(
                index=self.index_name,
                id=doc_id,
                body=doc_body
            )
            
            return response
            
        except Exception as e:
            raise Exception(f"Error indexing document: {str(e)}")
    
    async def index_document(self, title: str, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Indexar documento"""
        if self._is_async_context():
            return await self._run_in_executor(self._index_document_sync, title, content, metadata)
        else:
            return self._index_document_sync(title, content, metadata)
    
    async def search_documents(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Buscar documentos usando búsqueda semántica y de texto"""
        try:
            # Para búsqueda por texto no necesitamos embedding por ahora
            # query_embedding = await self.get_embedding(query)
            
            # Búsqueda simplificada solo por texto
            search_body = {
                "size": max_results,
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^2", "content"],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                },
                "_source": ["title", "content", "metadata", "created_at"]
            }
            
            response = self.client.search(index=self.index_name, body=search_body)
            
            # Procesar resultados
            results = []
            for hit in response['hits']['hits']:
                results.append({
                    "id": hit['_id'],
                    "title": hit['_source']['title'],
                    "content": hit['_source']['content'],
                    "metadata": hit['_source']['metadata'],
                    "score": hit['_score'],
                    "created_at": hit['_source']['created_at']
                })
            
            return results
            
        except Exception as e:
            # Si el índice no existe, intentar crearlo
            if "index_not_found_exception" in str(e):
                print(f"Índice no encontrado, intentando crear...")
                try:
                    self._create_index_if_not_exists()
                    print(f"Índice creado, devolviendo resultado vacío por primera vez")
                    return []  # Devolver vacío la primera vez después de crear el índice
                except Exception as create_error:
                    print(f"Error creando índice: {create_error}")
            raise Exception(f"Error searching documents: {str(e)}")
    
    async def list_documents(self, size: int = 100) -> List[Dict[str, Any]]:
        """Listar todos los documentos"""
        try:
            search_body = {
                "size": size,
                "query": {"match_all": {}},
                "_source": ["title", "content", "metadata", "created_at", "updated_at"]
            }
            
            response = self.client.search(index=self.index_name, body=search_body)
            
            documents = []
            for hit in response['hits']['hits']:
                documents.append({
                    "id": hit['_id'],
                    "title": hit['_source']['title'],
                    "content": hit['_source']['content'],
                    "metadata": hit['_source']['metadata'],
                    "created_at": hit['_source']['created_at'],
                    "updated_at": hit['_source']['updated_at']
                })
            
            return documents
            
        except Exception as e:
            raise Exception(f"Error listing documents: {str(e)}")
    
    async def delete_document(self, document_id: str) -> Dict[str, Any]:
        """Eliminar documento"""
        try:
            response = self.client.delete(index=self.index_name, id=document_id)
            return response
            
        except Exception as e:
            raise Exception(f"Error deleting document: {str(e)}")
    
    async def update_document(self, document_id: str, title: str = None, content: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Actualizar documento"""
        try:
            update_body = {
                "doc": {
                    "updated_at": datetime.now().isoformat()
                }
            }
            
            if title:
                update_body["doc"]["title"] = title
            
            if content:
                update_body["doc"]["content"] = content
                # Actualizar embedding también
                update_body["doc"]["embedding"] = await self.get_embedding(content)
            
            if metadata:
                update_body["doc"]["metadata"] = metadata
            
            response = self.client.update(
                index=self.index_name,
                id=document_id,
                body=update_body
            )
            
            return response
            
        except Exception as e:
            raise Exception(f"Error updating document: {str(e)}")
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del índice"""
        try:
            return self.client.indices.stats(index=self.index_name)
        except Exception as e:
            raise Exception(f"Error getting index stats: {str(e)}")
