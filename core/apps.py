"""Core app configuration."""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Core app for shared utilities and performance tools."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core Utilities'
