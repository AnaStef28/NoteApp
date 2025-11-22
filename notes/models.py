from django.db import models
import json


class Note(models.Model):
    title = models.TextField()
    content = models.TextField()
    embedding = models.TextField(blank=True)  # Stored as JSON string
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.content[:50] + ('...' if len(self.content) > 50 else '')

    def get_embedding_list(self):
        """Convert embedding JSON string to list."""
        if self.embedding:
            return json.loads(self.embedding)
        return None

    def set_embedding_list(self, embedding_list):
        """Convert embedding list to JSON string."""
        self.embedding = json.dumps(embedding_list)

