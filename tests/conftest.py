import pytest
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test configuration
pytest_plugins = []

@pytest.fixture(scope="session")
def test_config():
    """Test configuration fixture"""
    return {
        "aws_region": "us-east-1",
        "test_message": "Hello, this is a test message",
        "test_document": {
            "title": "Test Document",
            "content": "This is a test document for the RAG chatbot system."
        }
    }
