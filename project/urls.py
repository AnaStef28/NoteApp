"""
URL configuration for project project.
"""
from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from project.views import health_check, metrics

def redirect_to_admin(request):
    return redirect('admin:notes_note_changelist')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', redirect_to_admin, name='index'),
    path('health/', health_check, name='health_check'),
    path('metrics/', metrics, name='metrics'),
]

