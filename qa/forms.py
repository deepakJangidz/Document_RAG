from django import forms
from documents.models import Document

class QAForm(forms.Form):
    question = forms.CharField(max_length=255, required=True)
    document_ids = forms.ModelChoiceField(
        queryset=Document.objects.all(),  
        empty_label="Select a document",
        required=False
    )