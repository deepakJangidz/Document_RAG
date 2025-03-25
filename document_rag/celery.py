# document_rag/celery.py
import os
from celery import Celery

# Set default settings module for Celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "document_rag.settings")

celery_app = Celery("document_rag")

# Load task modules from all registered Django apps
celery_app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in installed apps
celery_app.autodiscover_tasks()
