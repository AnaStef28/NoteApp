"""
URL configuration for project project.
"""
# Import admin config first to ensure site customization is applied
from project.admin import *  # noqa: F401

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from project.views import health_check, metrics, about, admin_about


def redirect_to_admin(request):
    return redirect('admin:notes_note_changelist')

urlpatterns = [
    path('admin/about/', admin_about, name='admin_about'),
    path('admin/', admin.site.urls),
    path('', redirect_to_admin, name='index'),
    path('health/', health_check, name='health_check'),
    path('metrics/', metrics, name='metrics'),
    path('about/', about, name='about'),
]

