"""
Unit tests for Note model.
"""
import pytest
import json
from django.core.exceptions import ValidationError
from notes.models import Note
from notes.utils import generate_embedding


@pytest.mark.unit
@pytest.mark.django_db
class TestNoteModel:
    """Test cases for the Note model."""
    
    def test_create_note(self):
        """Test creating a basic note."""
        note = Note.objects.create(
            title="Test Title",
            content="Test content"
        )
        assert note.id is not None
        assert note.title == "Test Title"
        assert note.content == "Test content"
        assert note.created_at is not None
        assert note.updated_at is not None
    
    def test_note_str_representation(self):
        """Test string representation of note."""
        note = Note.objects.create(
            title="Test",
            content="Short content"
        )
        assert str(note) == "Short content"
        
        long_content = "A" * 60
        note2 = Note.objects.create(title="Test", content=long_content)
        assert str(note2) == "A" * 50 + "..."
    
    def test_get_embedding_list_empty(self):
        """Test getting embedding when none exists."""
        note = Note.objects.create(title="Test", content="Content")
        assert note.get_embedding_list() is None
    
    def test_set_and_get_embedding_list(self):
        """Test setting and getting embedding list."""
        note = Note.objects.create(title="Test", content="Content")
        embedding = [0.1, 0.2, 0.3, 0.4]
        
        note.set_embedding_list(embedding)
        note.save()
        
        assert note.embedding == json.dumps(embedding)
        assert note.get_embedding_list() == embedding
    
    def test_embedding_round_trip(self):
        """Test that embedding survives save/load cycle."""
        note = Note.objects.create(title="Test", content="Content")
        original_embedding = generate_embedding("Test content for embedding")
        
        note.set_embedding_list(original_embedding)
        note.save()
        
        # Reload from database
        note.refresh_from_db()
        loaded_embedding = note.get_embedding_list()
        
        assert len(loaded_embedding) == len(original_embedding)
        assert all(abs(a - b) < 1e-6 for a, b in zip(loaded_embedding, original_embedding))
    
    def test_note_ordering(self):
        """Test that notes are ordered by created_at descending."""
        note1 = Note.objects.create(title="First", content="Content 1")
        note2 = Note.objects.create(title="Second", content="Content 2")
        
        notes = list(Note.objects.all())
        assert notes[0].id == note2.id  # Most recent first
        assert notes[1].id == note1.id

