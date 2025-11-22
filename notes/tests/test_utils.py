"""
Unit tests for utility functions.
"""
import pytest
import numpy as np
from notes.utils import generate_embedding, cosine_similarity, get_model


@pytest.mark.unit
class TestEmbeddingUtils:
    """Test cases for embedding utilities."""
    
    def test_generate_embedding(self):
        """Test embedding generation."""
        text = "This is a test sentence."
        embedding = generate_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, (int, float)) for x in embedding)
    
    def test_embedding_consistency(self):
        """Test that same text produces same embedding."""
        text = "Consistent test text"
        embedding1 = generate_embedding(text)
        embedding2 = generate_embedding(text)
        
        assert len(embedding1) == len(embedding2)
        # Embeddings should be identical (deterministic)
        assert all(abs(a - b) < 1e-6 for a, b in zip(embedding1, embedding2))
    
    def test_embedding_different_texts(self):
        """Test that different texts produce different embeddings."""
        text1 = "Machine learning is great"
        text2 = "Cooking recipes are delicious"
        
        emb1 = generate_embedding(text1)
        emb2 = generate_embedding(text2)
        
        # Should be different
        assert emb1 != emb2
    
    def test_cosine_similarity_identical(self):
        """Test cosine similarity with identical vectors."""
        vec = [1.0, 2.0, 3.0]
        similarity = cosine_similarity(vec, vec)
        assert abs(similarity - 1.0) < 1e-6
    
    def test_cosine_similarity_orthogonal(self):
        """Test cosine similarity with orthogonal vectors."""
        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]
        similarity = cosine_similarity(vec1, vec2)
        assert abs(similarity) < 1e-6
    
    def test_cosine_similarity_zero_vector(self):
        """Test cosine similarity with zero vector."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [0.0, 0.0, 0.0]
        similarity = cosine_similarity(vec1, vec2)
        assert similarity == 0.0
    
    def test_cosine_similarity_similar_texts(self):
        """Test that similar texts have higher cosine similarity."""
        text1 = "Machine learning algorithms"
        text2 = "Machine learning models"
        text3 = "Cooking recipes"
        
        emb1 = generate_embedding(text1)
        emb2 = generate_embedding(text2)
        emb3 = generate_embedding(text3)
        
        sim_12 = cosine_similarity(emb1, emb2)
        sim_13 = cosine_similarity(emb1, emb3)
        
        # Similar texts should have higher similarity
        assert sim_12 > sim_13
    
    def test_get_model_singleton(self):
        """Test that get_model returns the same instance."""
        model1 = get_model()
        model2 = get_model()
        assert model1 is model2

