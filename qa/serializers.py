from rest_framework import serializers
from .models import QuestionAnswer
from documents.serializers import DocumentSerializer

class QuestionAnswerSerializer(serializers.ModelSerializer):
    documents_used = DocumentSerializer(many=True, read_only=True)
    
    class Meta:
        model = QuestionAnswer
        fields = ['id', 'user', 'question', 'answer', 'documents_used', 'created_at']
        read_only_fields = ['user', 'answer', 'documents_used', 'created_at']

class QuestionSerializer(serializers.Serializer):
    question = serializers.CharField()
    document_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
