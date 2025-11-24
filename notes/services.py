"""
Semantic search and AI services for notes.
"""
import json
import numpy as np
from typing import List, Tuple, Optional
from .models import Note
from .utils import generate_embedding


class SemanticSearchService:
    """Service for semantic search operations."""
    
    SIMILARITY_THRESHOLD = 0.15
    DEFAULT_TOP_K = 10
    
    @staticmethod
    def find_relevant_notes(query: str, top_k: int = None, threshold: float = None) -> List[Tuple[int, float, str]]:
        """
        Find relevant notes using semantic search.
        
        Args:
            query: Search query string
            top_k: Number of top results to return (default: 10)
            threshold: Minimum similarity score (default: 0.15)
            
        Returns:
            List of tuples: (note_id, score, content)
        """
        top_k = top_k or SemanticSearchService.DEFAULT_TOP_K
        threshold = threshold or SemanticSearchService.SIMILARITY_THRESHOLD
        
        # Generate query embedding
        query_vec = np.array(generate_embedding(query))
        query_norm = np.linalg.norm(query_vec)
        
        if query_norm == 0:
            return []
        
        # Fetch notes with embeddings
        rows = Note.objects.exclude(embedding='').exclude(embedding__isnull=True).values_list('id', 'embedding', 'content')
        scored_notes = []
        
        for note_id, emb_str, content in rows:
            if not emb_str or not content:
                continue
                
            try:
                vec = json.loads(emb_str)
                if vec and isinstance(vec, list) and len(vec) > 0:
                    note_vec = np.array(vec)
                    note_norm = np.linalg.norm(note_vec)
                    if note_norm > 0:
                        score = np.dot(note_vec, query_vec) / (note_norm * query_norm)
                        if score >= threshold:
                            scored_notes.append((note_id, score, content))
            except (ValueError, TypeError, json.JSONDecodeError):
                continue
        
        # Sort by score (highest first) and return top K
        scored_notes.sort(key=lambda x: x[1], reverse=True)
        return scored_notes[:top_k]
    
    @staticmethod
    def get_semantic_search_results(query: str, top_k: int = 10) -> Tuple[List[int], dict]:
        """
        Get semantic search results for admin queryset filtering.
        
        Returns:
            Tuple of (list of note IDs, dict of {note_id: score})
        """
        results = SemanticSearchService.find_relevant_notes(query, top_k=top_k)
        
        if not results:
            return [], {}
        
        note_ids = [r[0] for r in results]
        scores_dict = {int(r[0]): float(r[1]) for r in results}
        
        return note_ids, scores_dict


class AIService:
    """Service for AI-powered answer generation using Gemma."""
    
    _gemma_pipeline = None
    
    @classmethod
    def _get_gemma_pipeline(cls):
        """Lazy load Gemma pipeline."""
        if cls._gemma_pipeline is None:
            try:
                import torch
                from transformers import pipeline
                
                print("Loading Gemma model...")
                cls._gemma_pipeline = pipeline(
                    "text-generation",
                    model="google/gemma-3-1b-it",  # Using smaller model for faster inference
                    model_kwargs={"torch_dtype": torch.bfloat16},
                    device_map="auto"
                )
                print("Gemma model loaded successfully.")
                print(f"Pipeline type: {type(cls._gemma_pipeline)}")
            except Exception as e:
                print(f"Warning: Could not load Gemma model: {e}")
                print("Falling back to simple answer generation.")
                cls._gemma_pipeline = None
        
        return cls._gemma_pipeline
    
    @classmethod
    def generate_answer(cls, question: str, relevant_notes: List[str]) -> str:
        """
        Generate an AI-powered answer using Gemma model.
        
        Args:
            question: User's question
            relevant_notes: List of relevant note contents
            
        Returns:
            Generated answer string
        """
        if not relevant_notes:
            return "I don't have enough information to answer that question."
        
        # Try to use Gemma if available
        gemma_pipe = cls._get_gemma_pipeline()
        
        if gemma_pipe:
            try:
                return cls._generate_with_gemma(question, relevant_notes, gemma_pipe)
            except Exception as e:
                print(f"Gemma generation failed: {e}, falling back to simple answer")
        
        # Fallback to simple answer generation
        return cls._generate_simple_answer(question, relevant_notes)
    
    @classmethod
    def _generate_with_gemma(cls, question: str, relevant_notes: List[str], gemma_pipe) -> str:
        """Generate answer using Gemma model."""
        # Format context from notes (matching decoder.py format)
        context_block = "\n- ".join(relevant_notes[:3])
        
        messages = [
            {
                "role": "user", 
                "content": f"""You are a helpful assistant. 
Answer the question based ONLY on the provided notes.

NOTES:
- {context_block}

QUESTION: {question}"""
            }
        ]
        
        outputs = gemma_pipe(messages, max_new_tokens=200, do_sample=False)
        
        # Extract the generated text (matching decoder.py format exactly)
        try:
            # Format: outputs[0]["generated_text"][-1]["content"]
            if outputs and len(outputs) > 0:
                generated_text = outputs[0].get("generated_text", [])
                if isinstance(generated_text, list) and len(generated_text) > 0:
                    last_message = generated_text[-1]
                    if isinstance(last_message, dict):
                        content = last_message.get("content", "")
                        if content:
                            return content.strip()
        except (KeyError, IndexError, TypeError, AttributeError) as e:
            print(f"Error parsing Gemma output: {e}")
            print(f"Output structure: {type(outputs)}")
            if outputs:
                print(f"First output type: {type(outputs[0])}")
                print(f"First output keys: {outputs[0].keys() if isinstance(outputs[0], dict) else 'Not a dict'}")
        
        # Fallback if extraction fails
        return cls._generate_simple_answer(question, relevant_notes)
    
    @classmethod
    def _generate_simple_answer(cls, question: str, relevant_notes: List[str]) -> str:
        """Generate a simple answer without AI model (fallback)."""
        if not relevant_notes:
            return "I don't have enough information to answer that question."
        
        # Extract relevant sentences based on question keywords
        question_words = set(question.lower().split())
        answer_parts = []
        
        for note in relevant_notes:
            sentences = note.split('. ')
            for sentence in sentences:
                sentence_words = set(sentence.lower().split())
                if len(question_words & sentence_words) > 0:
                    answer_parts.append(sentence.strip())
                    if len(answer_parts) >= 5:
                        break
            if len(answer_parts) >= 5:
                break
        
        if answer_parts:
            answer = '. '.join(answer_parts)
            if not answer.endswith('.'):
                answer += '.'
            return answer
        else:
            # Fallback: return summaries
            summaries = []
            for note in relevant_notes:
                if len(note) > 200:
                    summaries.append(note[:200] + "...")
                else:
                    summaries.append(note)
            
            if len(summaries) == 1:
                return summaries[0]
            else:
                return "Based on your notes:\n\n" + "\n\n".join([f"• {s}" for s in summaries])

