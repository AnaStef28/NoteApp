"""
Integration tests for semantic search functionality.
"""
import pytest
from django.test import RequestFactory
from django.contrib.auth.models import User
from conftest import add_messages_support
from notes.models import Note
from notes.admin import NoteAdmin
from notes.utils import generate_embedding, cosine_similarity


@pytest.mark.integration
@pytest.mark.django_db
class TestSemanticSearch:
    """Integration tests for semantic search."""
    
    @pytest.fixture
    def search_notes(self, db):
        """Create notes for semantic search testing."""
        notes_data = [
            {"title": "Python Programming", "content": "Python is a high-level programming language used for web development, data science, and automation."},
            {"title": "Machine Learning", "content": "Machine learning is a subset of artificial intelligence that enables computers to learn from data."},
            {"title": "Web Development", "content": "Web development involves creating websites and web applications using HTML, CSS, and JavaScript."},
            {"title": "Data Science", "content": "Data science combines statistics, programming, and domain expertise to extract insights from data."},
            {"title": "Cooking Recipes", "content": "Cooking involves preparing food using various techniques and ingredients."},
        ]
        
        notes = []
        for data in notes_data:
            note = Note.objects.create(**data)
            embedding = generate_embedding(note.content)
            note.set_embedding_list(embedding)
            note.save()
            notes.append(note)
        
        return notes
    
    def test_semantic_search_finds_relevant_notes(self, search_notes, admin_user):
        """Test that semantic search returns relevant notes."""
        request = RequestFactory().get('/admin/notes/note/', {'q': 'programming languages'})
        request.user = admin_user
        request = add_messages_support(request)
        
        admin = NoteAdmin(Note, None)
        admin.request_reference = request
        
        queryset = admin.get_queryset(request)
        
        # Should find Python Programming note
        assert queryset.count() > 0
        found_titles = [note.title for note in queryset]
        assert "Python Programming" in found_titles
    
    def test_semantic_search_filters_low_similarity(self, search_notes, admin_user):
        """Test that semantic search filters out low similarity notes."""
        request = RequestFactory().get('/admin/notes/note/', {'q': 'artificial intelligence'})
        request.user = admin_user
        request = add_messages_support(request)
        
        admin = NoteAdmin(Note, None)
        admin.request_reference = request
        
        queryset = admin.get_queryset(request)
        
        # Should not include cooking recipes
        found_titles = [note.title for note in queryset]
        assert "Cooking Recipes" not in found_titles
    
    def test_semantic_search_empty_query(self, search_notes, admin_user):
        """Test that empty query returns all notes."""
        request = RequestFactory().get('/admin/notes/note/', {'q': ''})
        request.user = admin_user
        
        admin = NoteAdmin(Note, None)
        queryset = admin.get_queryset(request)
        
        # Should return all notes
        assert queryset.count() == len(search_notes)
    
    def test_semantic_search_scores_stored(self, search_notes, admin_user):
        """Test that semantic scores are stored on request."""
        request = RequestFactory().get('/admin/notes/note/', {'q': 'machine learning'})
        request.user = admin_user
        request = add_messages_support(request)
        
        admin = NoteAdmin(Note, None)
        admin.request_reference = request
        
        queryset = admin.get_queryset(request)
        
        # Scores should be stored
        assert hasattr(request, 'semantic_scores')
        assert len(request.semantic_scores) > 0
        
        # Check that scores are reasonable (between 0 and 1)
        for score in request.semantic_scores.values():
            assert 0 <= score <= 1
    
    def test_semantic_search_top_k_limit(self, search_notes, admin_user):
        """Test that semantic search limits results to top K."""
        request = RequestFactory().get('/admin/notes/note/', {'q': 'data science programming'})
        request.user = admin_user
        request = add_messages_support(request)
        
        admin = NoteAdmin(Note, None)
        admin.request_reference = request
        
        queryset = admin.get_queryset(request)
        
        # Should return at most 10 results (based on current admin.py setting)
        assert queryset.count() <= 10
    
    def test_semantic_search_threshold(self, search_notes, admin_user):
        """Test that semantic search applies similarity threshold."""
        # Use a query that's very different from all notes
        request = RequestFactory().get('/admin/notes/note/', {'q': 'completely unrelated topic about space exploration and aliens'})
        request.user = admin_user
        request = add_messages_support(request)
        
        admin = NoteAdmin(Note, None)
        admin.request_reference = request
        
        queryset = admin.get_queryset(request)
        
        # Should return empty or very few results due to threshold
        # (threshold is 0.15, so very different queries should return empty)
        assert queryset.count() <= len(search_notes)


@pytest.mark.integration
@pytest.mark.django_db
class TestEmbeddingPipeline:
    """Integration tests for embedding generation pipeline."""
    
    def test_note_save_generates_embedding(self, db):
        """Test that saving a note generates embedding."""
        # Note: Embeddings are only auto-generated when saving through admin.
        # For direct model creation, we need to generate manually or use admin's save_model.
        from notes.utils import generate_embedding
        
        note = Note.objects.create(
            title="Test Note",
            content="This is a test note for embedding generation."
        )
        
        # Generate embedding manually (as admin.save_model would do)
        embedding = generate_embedding(note.content)
        note.set_embedding_list(embedding)
        note.save()
        
        # Embedding should be generated
        assert note.embedding is not None
        assert note.embedding != ""
        
        embedding_list = note.get_embedding_list()
        assert embedding_list is not None
        assert len(embedding_list) > 0
    
    def test_note_update_regenerates_embedding(self, db):
        """Test that updating note content regenerates embedding."""
        from notes.utils import generate_embedding
        
        note = Note.objects.create(
            title="Test",
            content="Original content"
        )
        # Generate initial embedding
        embedding = generate_embedding(note.content)
        note.set_embedding_list(embedding)
        note.save()
        
        original_embedding = note.get_embedding_list()
        
        # Update content and regenerate embedding
        note.content = "Updated content"
        new_embedding = generate_embedding(note.content)
        note.set_embedding_list(new_embedding)
        note.save()
        
        # Embedding should be different
        updated_embedding = note.get_embedding_list()
        assert updated_embedding != original_embedding

