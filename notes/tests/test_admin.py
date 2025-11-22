"""
Unit tests for admin functionality.
"""
import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.contrib.auth.models import User
from notes.admin import NoteAdmin
from notes.models import Note
from notes.utils import generate_embedding


@pytest.mark.unit
@pytest.mark.django_db
class TestNoteAdmin:
    """Test cases for NoteAdmin."""
    
    @pytest.fixture
    def admin_site(self):
        """Create an admin site instance."""
        return AdminSite()
    
    @pytest.fixture
    def note_admin(self, admin_site):
        """Create a NoteAdmin instance."""
        return NoteAdmin(Note, admin_site)
    
    @pytest.fixture
    def request_factory(self):
        """Create a request factory."""
        return RequestFactory()
    
    def test_match_score_no_request(self, note_admin, sample_note):
        """Test match_score when no request is available."""
        result = note_admin.match_score(sample_note)
        assert result == "—"
    
    def test_match_score_no_scores(self, note_admin, sample_note, mock_request):
        """Test match_score when no scores are set."""
        note_admin.request_reference = mock_request
        result = note_admin.match_score(sample_note)
        assert result == "—"
    
    def test_match_score_with_score(self, note_admin, sample_note, mock_request):
        """Test match_score when score is available."""
        note_admin.request_reference = mock_request
        mock_request.semantic_scores = {sample_note.id: 0.75}
        
        result = note_admin.match_score(sample_note)
        assert "75.0%" in result
        assert "color: #198754" in result  # Green for high match
    
    def test_match_score_low_score(self, note_admin, sample_note, mock_request):
        """Test match_score with low score (grey color)."""
        note_admin.request_reference = mock_request
        mock_request.semantic_scores = {sample_note.id: 0.3}
        
        result = note_admin.match_score(sample_note)
        assert "30.0%" in result
        assert "color: #6c757d" in result  # Grey for low match
    
    def test_title_display(self, note_admin, sample_note):
        """Test title_display method."""
        result = note_admin.title_display(sample_note)
        assert sample_note.title in result
        assert "href" in result
    
    def test_content_preview(self, note_admin, sample_note):
        """Test content_preview method."""
        result = note_admin.content_preview(sample_note)
        assert isinstance(result, str)
        assert len(result) <= 103  # 100 chars + "..."
    
    def test_content_preview_long_content(self, note_admin, db):
        """Test content_preview with long content."""
        long_content = "A" * 200
        note = Note.objects.create(title="Test", content=long_content)
        result = note_admin.content_preview(note)
        assert result.endswith("...")
        assert len(result) == 103
    
    def test_embedding_preview_with_embedding(self, note_admin, sample_note):
        """Test embedding_preview when embedding exists."""
        embedding = generate_embedding(sample_note.content)
        sample_note.set_embedding_list(embedding)
        sample_note.save()
        
        result = note_admin.embedding_preview(sample_note)
        assert result == "Ready"
    
    def test_embedding_preview_without_embedding(self, note_admin, db):
        """Test embedding_preview when no embedding exists."""
        note = Note.objects.create(title="Test", content="Content")
        result = note_admin.embedding_preview(note)
        assert result == "Missing"

