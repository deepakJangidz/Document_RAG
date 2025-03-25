from rest_framework import serializers
from .models import Document, DocumentChunk

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'file', 'content_type', 'uploaded_by', 'processed', 'updated_at','created_at'
        ]
        read_only_fields = ['uploaded_by', 'processed']

class DocumentChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChunk
        fields = [
            'id', 'document', 'content', 'chunk_id', 'embeddings'
        ]