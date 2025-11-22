from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.urls import reverse
from django.db import models
from django.db.models import Case, When, IntegerField, Value
from .models import Note
from .utils import generate_embedding  # Removed unused cosine_similarity
import numpy as np
import json

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    # change_list_template = "admin/notes/note/change_list.html"

    # 1. Added 'match_score' back so you can see the % match
    list_display = ['id', 'match_score', 'title_display', 'content_preview', 'created_at', 'updated_at']
    list_display_links = ['title_display']
    list_filter = ['created_at', 'updated_at']
    search_fields = []
    readonly_fields = ['created_at', 'updated_at', 'embedding_preview']
    list_per_page = 25
    date_hierarchy = 'created_at'
    empty_value_display = '—'

    formfield_overrides = {
        models.TextField: {
            'widget': admin.widgets.AdminTextareaWidget(
                attrs={
                    'rows': 12,
                    'style': 'width: 95%; font-family: "SFMono-Regular", monospace; background-color: #f9fafb; padding: 1rem;'
                }
            )
        }
    }

    # --- DISPLAY HELPERS ---

    def match_score(self, obj):
        """Displays the similarity score if a semantic search is active."""
        # Retrieve score from the request (saved in get_queryset)
        request = getattr(self, 'request_reference', None)
        if not request:
            return "—"
        
        scores = getattr(request, 'semantic_scores', {})
        if not scores:
            return "—"
        
        score = scores.get(obj.id)
        if score is None:
            return "—"
        
        # Green for high match, Grey for low
        color = "#198754" if score > 0.5 else "#6c757d"
        score_percent = f"{score * 100:.1f}"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>', 
            color, score_percent
        )
    match_score.short_description = "Relevance"

    def title_display(self, obj):
        url = reverse('admin:notes_note_change', args=[obj.pk])
        title = obj.title or 'Untitled'
        content_length = len(obj.content) if obj.content else 0
        updated = obj.updated_at.strftime('%b %d, %Y · %H:%M')
        return format_html(
            '<a href="{}" style="font-weight:600; color:#2c3e50;">{}</a><br><small style="color:#6f7a87;">{} chars</small>',
            url, title, content_length
        )
    title_display.short_description = 'Title'

    def content_preview(self, obj):
        content = obj.content or ''
        preview = content[:100] + ('...' if len(content) > 100 else '')
        return preview
    content_preview.short_description = 'Content Preview'

    def embedding_preview(self, obj):
        if obj.embedding:
            return "Ready"
        return "Missing"
    embedding_preview.short_description = "Embedding"

    # --- LOGIC HANDLERS ---

    def save_model(self, request, obj, form, change):
        if not change or 'content' in form.changed_data or 'title' in form.changed_data:
            if obj.content:
                try:
                    embedding = generate_embedding(obj.content)
                    obj.set_embedding_list(embedding)
                except Exception as e:
                    messages.error(request, f"Embedding Error: {e}")
        super().save_model(request, obj, form, change)

    # IMPORTANT: This method must be indented INSIDE the class!
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        # Store request for match_score to use later
        self.request_reference = request 
        
        semantic_query = request.GET.get('q', '').strip()
        
        # If no search, return normal list
        if not semantic_query:
            return qs

        try:
            # 1. Vectorize Query
            query_vec = np.array(generate_embedding(semantic_query))
            query_norm = np.linalg.norm(query_vec)
            
            if query_norm == 0:
                messages.warning(request, "Could not generate query embedding.")
                return qs
            
            # 2. Fast Fetch (ID + Embedding only)
            rows = Note.objects.exclude(embedding='').exclude(embedding__isnull=True).values_list('id', 'embedding')
            if not rows:
                messages.info(request, "No notes with embeddings found.")
                return qs.none()

            # 3. Prepare Matrix
            ids = []
            vectors = []
            for note_id, emb_str in rows:
                if not emb_str:
                    continue
                try:
                    vec = json.loads(emb_str)
                    if vec and isinstance(vec, list) and len(vec) > 0:
                        vectors.append(vec)
                        ids.append(note_id)
                except (ValueError, TypeError, json.JSONDecodeError):
                    continue
            
            if not vectors or len(vectors) == 0:
                messages.info(request, "No valid embeddings found.")
                return qs.none()

            # 4. Matrix Math (Fast)
            matrix = np.array(vectors)
            matrix_norms = np.linalg.norm(matrix, axis=1)
            
            # Prevent divide by zero
            matrix_norms[matrix_norms == 0] = 1e-10
            
            dot_products = np.dot(matrix, query_vec)
            scores = dot_products / (matrix_norms * query_norm)

            # 5. Sort & Top K
            results = list(zip(ids, scores))
            
            # Filter out noise (< 15% match)
            results = [r for r in results if r[1] > 0.15]
            
            # Sort Highest -> Lowest
            results.sort(key=lambda x: x[1], reverse=True)
            
            # Keep top 3 results
            top_results = results[:10]
            
            if not top_results:
                messages.warning(request, "No notes match that meaning (threshold: 15%).")
                return qs.none()
            
            top_ids = [r[0] for r in top_results]
            scores_dict = {int(r[0]): float(r[1]) for r in top_results}

            # Save scores for UI - store on request object
            if not hasattr(request, 'semantic_scores'):
                request.semantic_scores = {}
            request.semantic_scores.update(scores_dict)

            messages.success(request, f"Found {len(top_ids)} relevant notes.")
            
            # Use Note.objects directly to bypass any admin filters
            # Return filtered queryset - ordering by similarity will be handled by the order of IDs
            # SQLite preserves IN clause order in some cases, but we'll use Case/When for reliability
            try:
                if len(top_ids) > 1:
                    ordering_cases = [When(pk=pk, then=Value(idx)) for idx, pk in enumerate(top_ids)]
                    order_field = Case(
                        *ordering_cases,
                        default=Value(999),
                        output_field=IntegerField(),
                    )
                    return Note.objects.filter(pk__in=top_ids).order_by(order_field)
                else:
                    return Note.objects.filter(pk__in=top_ids)
            except (Exception, ValueError, TypeError) as order_error:
                # Fallback: return without ordering if Case/When fails
                return Note.objects.filter(pk__in=top_ids)

        except Exception as e:
            import traceback
            error_msg = f"Search Error: {str(e)}"
            messages.error(request, error_msg)
            # Log the full traceback for debugging
            print(f"Semantic search error: {error_msg}")
            traceback.print_exc()
            # Return normal queryset instead of empty to avoid redirect issues
            return qs
    
    def changelist_view(self, request, extra_context=None):
        # Store request for match_score to use later
        self.request_reference = request
        extra_context = extra_context or {}
        extra_context['semantic_search_query'] = request.GET.get('q', '')
        return super().changelist_view(request, extra_context)
