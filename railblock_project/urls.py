"""
URL configuration for railblock_project project.
SIH 2026 PS 26028 (TrackPulse AI Dynamic Train ETA) at '/'
SIH 2026 PS 26027 (RailBlock AI Maintenance Block Planning) preserved at '/block-planning/'
"""
from django.contrib import admin
from django.urls import path, include
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # SIH 2026 PS 26028 — Primary Dynamic Train ETA Forecast System
    path('', include('eta.urls')),

    # SIH 2026 PS 26027 — Preserved Maintenance Block Planning System
    path('block-planning/', include('core.urls')),

    # Direct legacy routes for 26027 AJAX endpoints
    path('api/timeline-data/', core_views.api_timeline_data),
    path('api/lagrangian-telemetry/', core_views.api_lagrangian_telemetry),
    path('api/optimize/', core_views.api_lagrangian_telemetry),
    path('api/submit-request/', core_views.submit_request),
    path('api/cancel-request/<int:req_id>/', core_views.cancel_request),
    path('api/approve-schedule/', core_views.api_toggle_schedule_approval),
    path('api/reset/', core_views.api_reset_data),
]
