from django.urls import path
from .views import AsyncDocumentView, AsyncDocumentReprocessView, upload_form_view

urlpatterns = [
    path('', AsyncDocumentView.as_view(), name='document-list-create'),
    path('<int:pk>/', AsyncDocumentView.as_view(), name='document-detail'),
    path('<int:pk>/reprocess/', AsyncDocumentReprocessView.as_view(), name='document-reprocess'),
    path('upload/', upload_form_view, name='upload-form')
]