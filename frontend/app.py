import streamlit as st
import requests
import json
import os
from datetime import datetime
from typing import List, Dict, Any
import time
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de la página
st.set_page_config(
    page_title="AWS RAG Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS mínimo y limpio
st.markdown("""
<style>
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #FF9900;
        background-color: #f8f9fa;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left-color: #2196f3;
    }
    .bot-message {
        background-color: #f3e5f5;
        border-left-color: #9c27b0;
    }
    .source-card {
        background-color: #fff3e0;
        border: 1px solid #ffcc02;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .confidence-high { color: #4caf50; font-weight: bold; }
    .confidence-medium { color: #ff9800; font-weight: bold; }
    .confidence-low { color: #f44336; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Configuración de la API
BACKEND_URL = os.getenv("BACKEND_URL", "https://smuzri8cak.execute-api.us-east-1.amazonaws.com/Prod")

class ChatbotInterface:
    def __init__(self):
        self.backend_url = BACKEND_URL
        
    def send_message(self, message: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Enviar mensaje al backend"""
        try:
            payload = {
                "message": message,
                "chat_history": chat_history or [],
                "max_results": 5
            }
            
            response = requests.post(
                f"{self.backend_url}/chat",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Error del servidor: {response.status_code}")
                return {"message": "Error al procesar la solicitud", "sources": [], "confidence": 0.0}
                
        except requests.exceptions.RequestException as e:
            st.error(f"Error de conexión: {str(e)}")
            return {"message": "Error de conexión con el servidor", "sources": [], "confidence": 0.0}
    
    def check_backend_status(self) -> bool:
        """Verificar si el backend está disponible"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_confidence_color(self, confidence: float) -> str:
        """Obtener clase CSS basada en la confianza"""
        if confidence >= 0.7:
            return "confidence-high"
        elif confidence >= 0.4:
            return "confidence-medium"
        else:
            return "confidence-low"

def main():
    # Título simple
    st.title("🤖 AWS RAG Chatbot")
    st.markdown("Asistente con tecnología AWS Bedrock")
    st.markdown("---")
    
    # Inicializar chatbot
    chatbot = ChatbotInterface()
    
    # Verificar estado del backend
    backend_status = chatbot.check_backend_status()
    
    # Sidebar simple
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # Estado del sistema
        if backend_status:
            st.success("✅ Sistema conectado")
        else:
            st.error("❌ Sistema desconectado")
        
        # Configuraciones básicas
        show_confidence = st.checkbox("Mostrar confianza", value=True)
        show_sources = st.checkbox("Mostrar fuentes", value=True)
        
        st.markdown("---")
        
        # Botón para limpiar chat
        if st.button("🗑️ Limpiar Chat"):
            st.session_state.messages = []
            st.rerun()
        
        # Estadísticas básicas
        if 'messages' in st.session_state:
            total_messages = len([msg for msg in st.session_state.messages if msg["role"] == "user"])
            st.metric("Consultas realizadas", total_messages)
    
    # Inicializar mensajes si no existen
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Mostrar mensajes usando st.chat_message (más limpio)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
            # Mostrar metadata para respuestas del asistente
            if message["role"] == "assistant" and "metadata" in message:
                metadata = message["metadata"]
                
                if show_confidence and "confidence" in metadata:
                    confidence = metadata["confidence"]
                    confidence_class = chatbot.get_confidence_color(confidence)
                    st.markdown(f'<p class="{confidence_class}">🎯 Confianza: {confidence:.1%}</p>', unsafe_allow_html=True)
                
                if show_sources and "sources" in metadata and metadata["sources"]:
                    st.markdown("**📚 Fuentes:**")
                    for i, source in enumerate(metadata["sources"], 1):
                        score = source.get('score', 0)
                        title = source.get('title', 'Sin título')
                        preview = source.get('content_preview', 'Sin vista previa')
                        
                        with st.expander(f"{i}. {title} (Score: {score:.3f})"):
                            st.write(preview)
                            if source.get('metadata'):
                                st.json(source['metadata'])
    
    # Input de chat
    if prompt := st.chat_input("Escribe tu pregunta aquí..."):
        if not backend_status:
            st.error("⚠️ El backend no está disponible. Por favor, intenta más tarde.")
            return
        
        # Agregar mensaje del usuario
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generar respuesta
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                # Preparar historial para enviar al backend
                chat_history = []
                for msg in st.session_state.messages[:-1]:  # Excluir el mensaje actual
                    if msg["role"] == "user":
                        chat_history.append({"role": "human", "content": msg["content"]})
                    elif msg["role"] == "assistant":
                        chat_history.append({"role": "assistant", "content": msg["content"]})
                
                # Obtener respuesta del chatbot
                response = chatbot.send_message(prompt, chat_history)
                st.write(response["message"])
                
                # Mostrar confianza
                if show_confidence:
                    confidence = response["confidence"]
                    confidence_class = chatbot.get_confidence_color(confidence)
                    st.markdown(f'<p class="{confidence_class}">🎯 Confianza: {confidence:.1%}</p>', unsafe_allow_html=True)
                
                # Mostrar fuentes
                if show_sources and response.get("sources"):
                    st.markdown("**📚 Fuentes:**")
                    for i, source in enumerate(response["sources"], 1):
                        score = source.get('score', 0)
                        title = source.get('title', 'Sin título')
                        preview = source.get('content_preview', 'Sin vista previa')
                        
                        with st.expander(f"{i}. {title} (Score: {score:.3f})"):
                            st.write(preview)
                            if source.get('metadata'):
                                st.json(source['metadata'])
        
        # Guardar respuesta del asistente con metadata
        st.session_state.messages.append({
            "role": "assistant",
            "content": response["message"],
            "metadata": {
                "confidence": response["confidence"],
                "sources": response.get("sources", []),
                "timestamp": response.get("timestamp")
            }
        })

if __name__ == "__main__":
    main()
