import os
import django
import torch
import numpy as np
from transformers import pipeline

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from .models import Note  
from .utils import generate_embedding, cosine_similarity 

print("Loading Gemma...")
gemma_pipe = pipeline(
    "text-generation",
    model="google/gemma-3-1b-it",
    model_kwargs={"torch_dtype": torch.bfloat16},
    device_map="auto"
)

def _guess_title(text: str) -> str:
    head = text.strip().splitlines()[0] if text.strip() else ""
    if len(head) > 80:
        head = head[:77].rstrip() + "..."
    return head or "Untitled note"


def add_note_to_db(text, title=None):
    """Helper to add a note to Django and save its embedding."""
    vector = generate_embedding(text)
    resolved_title = (title or _guess_title(text)).strip() or "Untitled note"
    new_note = Note(title=resolved_title, content=text)
    new_note.set_embedding_list(vector) 
    new_note.save()
    print(f"Saved note '{resolved_title}' ({len(text.split())} words)")

def get_best_notes(query, top_k=3):
    """Finds the most relevant notes using the Django DB."""
    query_vector = generate_embedding(query)
    
    scored_notes = []
    
    # ERROR FIX: Use Django's Note.objects.all(), not 'notes_db'
    all_notes = Note.objects.all()
    
    for note in all_notes:
        # ERROR FIX: Use the method to get the list, not dictionary access ['vector']
        note_vector = note.get_embedding_list()
        
        if note_vector is None:
            continue
            
        score = cosine_similarity(query_vector, note_vector)
        
        # ERROR FIX: Use note.content, not note['text']
        scored_notes.append((score, note.content))
    
    # Sort by score (highest first)
    scored_notes.sort(key=lambda x: x[0], reverse=True)
    
    return [note[1] for note in scored_notes[:top_k]]

def ask_ai(question):
    relevant_notes = get_best_notes(question, top_k=3)
    
    if not relevant_notes:
        return "I don't have any notes to answer that."

    context_block = "\n- ".join(relevant_notes)
    
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
    return outputs[0]["generated_text"][-1]["content"]
