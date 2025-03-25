from django.db import models
from django.contrib.auth.models import User
from documents.models import Document

class QuestionAnswer(models.Model):
    """Model to store question-answer history"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()
    documents_used = models.ManyToManyField(Document)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Q: {self.question[:50]}..."