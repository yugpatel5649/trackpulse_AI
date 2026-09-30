from django.urls import path
from eta import views

urlpatterns = [
    # Main Dynamic ETA Dashboard (SIH 2026 PS 26028)
    path('', views.eta_dashboard, name='eta_dashboard'),

    # REST APIs for Dynamic ETA
    path('api/eta/', views.api_eta_summary, name='api_eta_summary'),
    path('api/eta/train/<str:train_number>/', views.api_eta_train_detail, name='api_eta_train_detail'),
    path('api/eta/simulate-event/', views.api_simulate_event, name='api_simulate_event'),
    path('api/eta/reset/', views.api_reset_simulation, name='api_reset_simulation'),
]
