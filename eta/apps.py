from django.apps import AppConfig


class EtaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'eta'
    verbose_name = 'Dynamic Train ETA Forecasting'
