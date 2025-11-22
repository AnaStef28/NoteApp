from sentence_transformers import SentenceTransformer
import numpy as np

# Load model once (singleton pattern)
_model = None


def get_model():
    """Get or initialize the SentenceTransformer model."""
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


def generate_embedding(text):
    """Generate embedding for a given text."""
    model = get_model()
    embedding = model.encode(text)
    return embedding.tolist()


def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors."""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)

