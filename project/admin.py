"""
Admin site configuration - must be imported before admin URLs
"""
from django.contrib import admin

# Customize admin site header and titles
admin.site.site_header = "AI Notes Administration"
admin.site.site_title = "AI Notes Admin"
admin.site.index_title = "Semantic Notes Management"

