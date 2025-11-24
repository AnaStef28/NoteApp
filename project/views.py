"""
Health check and monitoring views.
"""
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
from django.db import connection
from notes.models import Note
from notes.utils import get_model
import json


@require_http_methods(["GET"])
def health_check(request):
    """
    Health check endpoint for monitoring.
    Returns 200 if healthy, 503 if unhealthy.
    """
    health_status = {
        'status': 'healthy',
        'checks': {}
    }
    overall_healthy = True
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['checks']['database'] = f'error: {str(e)}'
        overall_healthy = False
    
    # Embedding model check
    try:
        model = get_model()
        test_embedding = model.encode("test")
        health_status['checks']['embedding_model'] = 'ok'
    except Exception as e:
        health_status['checks']['embedding_model'] = f'error: {str(e)}'
        overall_healthy = False
    
    # Basic statistics
    try:
        total_notes = Note.objects.count()
        notes_with_embeddings = Note.objects.exclude(
            embedding=''
        ).exclude(
            embedding__isnull=True
        ).count()
        
        health_status['checks']['notes'] = {
            'total': total_notes,
            'with_embeddings': notes_with_embeddings,
            'without_embeddings': total_notes - notes_with_embeddings
        }
    except Exception as e:
        health_status['checks']['notes'] = f'error: {str(e)}'
        overall_healthy = False
    
    if not overall_healthy:
        health_status['status'] = 'unhealthy'
        return JsonResponse(health_status, status=503)
    
    return JsonResponse(health_status, status=200)


@require_http_methods(["GET"])
def metrics(request):
    """
    Metrics endpoint for monitoring.
    Returns basic metrics about the system.
    """
    metrics_data = {
        'notes': {
            'total': Note.objects.count(),
            'with_embeddings': Note.objects.exclude(
                embedding=''
            ).exclude(
                embedding__isnull=True
            ).count(),
        }
    }
    
    # Database size (if SQLite)
    try:
        from django.conf import settings
        import os
        db_path = settings.DATABASES['default']['NAME']
        if os.path.exists(db_path):
            db_size = os.path.getsize(db_path)
            metrics_data['database'] = {
                'size_bytes': db_size,
                'size_mb': round(db_size / (1024 * 1024), 2)
            }
    except Exception:
        pass
    
    return JsonResponse(metrics_data)


@require_http_methods(["GET"])
def about(request):
    """
    About page displaying project information and contributors.
    """
    contributors = [
        "Anamaria Stefanescu",
        "Paul Trescovan",
        "Mincic Denis",
        "Marta Rares",
        "Andrei Piscoran",
    ]
    
    context = {
        'contributors': contributors,
    }
    
    return render(request, 'about.html', context)


@staff_member_required
def admin_about(request):
    """
    About page integrated into the admin interface.
    """
    contributors = [
        "Anamaria Stefanescu",
        "Paul Trescovan",
        "Mincic Denis",
        "Marta Rares",
        "Andrei Piscoran",
    ]
    
    context = {
        'contributors': contributors,
        'title': 'About AI Notes',
        'site_header': 'AI Notes Administration',
        'site_title': 'AI Notes Admin',
        'has_permission': True,
    }
    
    return render(request, 'admin/about.html', context)

