"""
Pytest configuration and fixtures for the AI Notes project.
"""
import pytest
import json
from django.contrib.auth.models import User
from notes.models import Note
from notes.utils import generate_embedding


@pytest.fixture
def admin_user(db):
    """Create an admin user for testing."""
    return User.objects.create_user(
        username='admin',
        email='admin@test.com',
        password='testpass123',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def regular_user(db):
    """Create a regular user for testing."""
    return User.objects.create_user(
        username='user',
        email='user@test.com',
        password='testpass123'
    )


@pytest.fixture
def sample_note(db):
    """Create a sample note with embedding."""
    note = Note.objects.create(
        title="Test Note",
        content="This is a test note about machine learning and AI."
    )
    embedding = generate_embedding(note.content)
    note.set_embedding_list(embedding)
    note.save()
    return note


@pytest.fixture
def multiple_notes(db):
    """Create multiple notes with embeddings for testing."""
    notes_data = [
        {"title": "Python Basics", "content": "Python is a programming language used for data science."},
        {"title": "Machine Learning", "content": "Machine learning algorithms learn from data."},
        {"title": "Deep Learning", "content": "Deep learning uses neural networks with multiple layers."},
        {"title": "Web Development", "content": "Django is a web framework for building applications."},
        {"title": "Data Science", "content": "Data science combines statistics and programming."},
    ]
    
    notes = []
    for data in notes_data:
        note = Note.objects.create(**data)
        embedding = generate_embedding(note.content)
        note.set_embedding_list(embedding)
        note.save()
        notes.append(note)
    
    return notes


@pytest.fixture
def mock_request():
    """Create a mock request object for admin testing."""
    from django.contrib.messages.storage.base import BaseStorage
    
    class TestMessagesStorage(BaseStorage):
        """Test messages storage that doesn't require sessions or cookies."""
        def __init__(self, request):
            super().__init__(request)
            self._test_messages = []
        
        def _get(self, *args, **kwargs):
            """Retrieve messages."""
            return self._test_messages
        
        def _store(self, messages, response, *args, **kwargs):
            """Store messages (no-op for testing)."""
            # Store messages for potential retrieval, but don't require response
            self._test_messages = list(messages)
            return []
    
    class MockRequest:
        def __init__(self):
            self.GET = {}
            self.semantic_scores = {}
            self._messages = TestMessagesStorage(self)
    
    return MockRequest()


def add_messages_support(request):
    """Add messages framework support to a RequestFactory request."""
    from django.contrib.messages.storage.base import BaseStorage
    
    class TestMessagesStorage(BaseStorage):
        """Test messages storage that doesn't require sessions or cookies."""
        def __init__(self, request):
            super().__init__(request)
            self._test_messages = []
        
        def _get(self, *args, **kwargs):
            """Retrieve messages."""
            return self._test_messages
        
        def _store(self, messages, response, *args, **kwargs):
            """Store messages (no-op for testing)."""
            # Store messages for potential retrieval, but don't require response
            self._test_messages = list(messages)
            return []
    
    request._messages = TestMessagesStorage(request)
    return request

