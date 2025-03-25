from django.db import models
import uuid
import os
from django.contrib.auth.models import User

# Create your models here
from django.db import models
from django.contrib.postgres.indexes import GinIndex

def document_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return os.path.join('documents', filename)

class Document(models.Model):
    title = models.CharField(max_length=200, db_index=True)  # Index for title-based lookups (if needed)
    file = models.FileField(upload_to=document_upload_path)
    content_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # Speeds up sorting/filtering
    processed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)  # Useful for ordering by updates
    uploaded_by = models.ForeignKey('auth.User', on_delete=models.CASCADE, db_index=True)  # Ensures faster lookups

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
            models.Index(fields=['uploaded_by']),
        ]

    def __str__(self):
        return f"{self.title}"


# def document_upload_path(instance, filename):
#     ext = filename.split('.')[-1]
#     filename = f'{uuid.uuid4()}.{ext}'
#     return os.path.join('documents', filename)

# class Document(models.Model):
#     title = models.CharField(max_length=200)
#     file = models.FileField(upload_to=document_upload_path)
#     content_type = models.CharField(max_length=100)
#     created_at = models.DateTimeField(auto_now_add=True)
#     processed = models.BooleanField(default=False)
#     updated_at = models.DateTimeField(auto_now=True)
#     uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)

#     def __str__(self):
#         return f"{self.title}"
    
# class DocumentChunk(models.Model):
#     document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name= 'chunks')
#     content = models.TextField()
#     chunk_id = models.CharField(max_length=200)
#     embeddings = models.JSONField( null=True, blank = True)

#     class Meta:
#         indexes = [
#             models.Index(fields=['created_at']),  # Index for sorting/filtering
#         ]
#     def __str__(self):
#         # return f"Chunk {self.chunk_id} of {self.document.title}"
#         return f"Chunk {self.chunk_id} of {self.document.title}"
class DocumentChunk(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks', db_index=True)
    content = models.TextField()
    chunk_id = models.CharField(max_length=200, db_index=True)  # Ensures fast lookups by chunk_id
    embeddings = models.JSONField(default=[], blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['chunk_id']),  # Index for chunk ID lookups
            GinIndex(fields=['embeddings']),  # GIN index for fast JSON-based retrieval (if using PostgreSQL)
        ]

    def __str__(self):
        return f"Chunk {self.chunk_id} of {self.document.title}"


