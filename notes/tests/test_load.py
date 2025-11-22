"""
Load tests for semantic search performance.
"""
import pytest
import time
from django.test import TestCase
from django.test import RequestFactory
from django.contrib.auth.models import User
from conftest import add_messages_support
from notes.models import Note
from notes.admin import NoteAdmin
from notes.utils import generate_embedding


@pytest.mark.slow
@pytest.mark.load
@pytest.mark.django_db
class TestLoadPerformance:
    """Load tests for performance."""
    
    def test_search_performance_with_many_notes(self, db):
        """Test search performance with a large number of notes."""
        # Create 100 notes
        notes = []
        for i in range(100):
            note = Note.objects.create(
                title=f"Note {i}",
                content=f"This is note number {i} about various topics including technology, science, and programming."
            )
            embedding = generate_embedding(note.content)
            note.set_embedding_list(embedding)
            note.save()
            notes.append(note)
        
        # Perform search
        request = RequestFactory().get('/admin/notes/note/', {'q': 'technology'})
        request.user = User.objects.create_user('test', 'test@test.com', 'pass')
        request = add_messages_support(request)
        
        admin = NoteAdmin(Note, None)
        admin.request_reference = request
        
        start_time = time.time()
        queryset = admin.get_queryset(request)
        elapsed_time = time.time() - start_time
        
        # Should complete in reasonable time (< 5 seconds for 100 notes)
        assert elapsed_time < 5.0, f"Search took {elapsed_time:.2f} seconds, expected < 5.0"
        assert queryset.count() > 0
    
    def test_embedding_generation_performance(self, db):
        """Test embedding generation performance."""
        texts = [f"This is test text number {i} for performance testing." for i in range(50)]
        
        start_time = time.time()
        embeddings = [generate_embedding(text) for text in texts]
        elapsed_time = time.time() - start_time
        
        # Should generate embeddings at reasonable speed
        avg_time_per_embedding = elapsed_time / len(texts)
        assert avg_time_per_embedding < 0.5, f"Average embedding time: {avg_time_per_embedding:.3f}s, expected < 0.5s"
    
    def test_concurrent_searches(self, db):
        """Test that multiple concurrent searches work correctly."""
        # Create test data
        for i in range(20):
            note = Note.objects.create(
                title=f"Note {i}",
                content=f"Content {i} about machine learning"
            )
            embedding = generate_embedding(note.content)
            note.set_embedding_list(embedding)
            note.save()
        
        # Perform multiple searches
        queries = ['machine learning', 'programming', 'data science', 'technology']
        request_factory = RequestFactory()
        user = User.objects.create_user('test', 'test@test.com', 'pass')
        
        results = []
        for query in queries:
            request = request_factory.get('/admin/notes/note/', {'q': query})
            request.user = user
            request = add_messages_support(request)
            
            admin = NoteAdmin(Note, None)
            admin.request_reference = request
            queryset = admin.get_queryset(request)
            results.append(queryset.count())
        
        # All searches should return results
        assert all(count > 0 for count in results), "Some searches returned no results"

