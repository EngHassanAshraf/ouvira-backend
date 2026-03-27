"""
Celery application configuration.
Auto-discovers tasks from all INSTALLED_APPS.
"""
import os
import django
from celery import Celery

# DJANGO_SETTINGS_MODULE must be set BEFORE importing anything from Django.
# Reading django.conf.settings here causes a circular import crash.
# The correct pattern: read the env var, set a safe default, then let Django configure itself.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("config")

# Read Celery config from Django settings (CELERY_* namespace)
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from all INSTALLED_APPS after Django is configured
django.setup()
app.autodiscover_tasks()
