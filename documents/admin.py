
# Register your models here.
from django.contrib import admin
from django.contrib.postgres.fields import JSONField
from django_json_widget.widgets import JSONEditorWidget  # this widget i am using for better UI
from .models import Document, DocumentChunk

class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'chunk_id', 'content', 'embeddings_preview')  # i have redefined embeddings below as embeddings preview
    search_fields = ('chunk_id'"django_json_widget", ) 
    formfield_overrides = {
        JSONField: {"widget": JSONEditorWidget}  # Use JSON editor for better visualization
    }

    def embeddings_preview(self, obj):
        return str(obj.embeddings)[:100] if obj.embeddings else "No embeddings"
    embeddings_preview.short_description = "Embeddings (Preview)"

# here i have registered my models with admin
admin.site.register(Document)
admin.site.register(DocumentChunk, DocumentChunkAdmin)  # Register with custom admin class

