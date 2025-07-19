import pytest
import requests
import json
import os

class TestChatbotAPI:
    """Test suite for the chatbot API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self, test_config):
        """Setup test environment"""
        self.config = test_config
        self.base_url = os.getenv("API_GATEWAY_URL", "http://localhost:8000")
        
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        response = requests.get(f"{self.base_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_chat_endpoint(self):
        """Test the chat endpoint"""
        payload = {
            "message": self.config["test_message"],
            "max_results": 5
        }
        
        response = requests.post(
            f"{self.base_url}/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "sources" in data
        assert "confidence" in data
        assert "timestamp" in data
    
    def test_chat_endpoint_with_history(self):
        """Test chat endpoint with conversation history"""
        payload = {
            "message": "What is AWS?",
            "chat_history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hello! How can I help you?"}
            ],
            "max_results": 3
        }
        
        response = requests.post(
            f"{self.base_url}/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert isinstance(data["sources"], list)
        assert isinstance(data["confidence"], float)
    
    def test_upload_document(self):
        """Test document upload endpoint"""
        payload = {
            "title": self.config["test_document"]["title"],
            "content": self.config["test_document"]["content"],
            "metadata": {"test": True}
        }
        
        response = requests.post(
            f"{self.base_url}/documents/upload",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "document_id" in data
    
    def test_list_documents(self):
        """Test list documents endpoint"""
        response = requests.get(f"{self.base_url}/documents")
        
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert isinstance(data["documents"], list)
    
    def test_search_documents(self):
        """Test document search endpoint"""
        params = {
            "query": "AWS",
            "max_results": 5
        }
        
        response = requests.get(f"{self.base_url}/search", params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)
    
    def test_invalid_chat_request(self):
        """Test chat endpoint with invalid request"""
        payload = {}  # Missing required message field
        
        response = requests.post(
            f"{self.base_url}/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_invalid_document_upload(self):
        """Test document upload with invalid data"""
        payload = {
            "title": "Test",
            # Missing content field
        }
        
        response = requests.post(
            f"{self.base_url}/documents/upload",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
