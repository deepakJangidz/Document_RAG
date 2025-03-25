from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.http import JsonResponse
from .models import Document, DocumentChunk
from .serializers import DocumentSerializer, DocumentChunkSerializer
from django.conf import settings
import os
import uuid
from qa.services import DocumentProcessor
import json
from django.core.exceptions import ObjectDoesNotExist
from asgiref.sync import sync_to_async
from django.views import View
from django.shortcuts import render
from .forms import DocumentForm
import magic

from qa.tasks import process_document_task
from django.core.cache import cache
from channels.db import database_sync_to_async
import asyncio
import logging
from celery.result import AsyncResult


logging.basicConfig(
    level=logging.DEBUG, 
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)


# just converting django ORM operations to async
get_document = sync_to_async(Document.objects.get, thread_sensitive=True)
create_document = sync_to_async(lambda **kwargs: Document.objects.create(**kwargs))
delete_chunks = sync_to_async(lambda doc: doc.chunks.all().delete())
save_document = sync_to_async(lambda doc: doc.save())


def upload_form_view(request):
    form = DocumentForm()
    return render(request, "upload_document.html", {"form": form})

# def get_content_type(file):
#         mime = magic.Magic(mime=True)
#         content_type = mime.from_buffer(file.read(1024))  # Read first 1024 bytes to detect type
#         file.seek(0)  # Reset file pointer
        
#         return content_type




class AsyncDocumentView(View):
    permission_classes = [permissions.IsAuthenticated]
    async def get(self, request, pk=None):
        user_id = await asyncio.to_thread(lambda: request.user.id) # since request.user.id is synchronous operation thus using asyncio
        if pk:
            cache_key = f"document:{pk}_createdBy {user_id}"
            cached_document = await sync_to_async(cache.get, thread_sensitive=True)(cache_key)
            
            if cached_document:
                return JsonResponse(cached_document, safe=False)

            try:
                # here i am fetching document from the database asynchronously
                logger.debug("Fetching document id: {pk} from Document model")
                document = await database_sync_to_async(Document.objects.get, thread_sensitive=True)(id=pk, uploaded_by=request.user.id)
                serializer = DocumentSerializer(document)
                data = serializer.data
                
                # here i am asynchronously caching the document
                await sync_to_async(cache.set, thread_sensitive=True)(cache_key, data, timeout=300)  # Cache for 5 min
                logger.info("Successfully saved document to cache with key : {cache_key}")
                return JsonResponse(data, safe=False)
            except Document.DoesNotExist:
                logger.error("Asked Document not found")
                return JsonResponse({"error": "Document NOT FOUND"}, status=404)

        else:
            cache_key = f"user_documents:{user_id}"
            
            cached_documents = await sync_to_async(cache.get, thread_sensitive=True)(cache_key)

            if cached_documents:
                logger.info("Data extract from cache with key : {cache_key}")
                return JsonResponse(cached_documents, safe=False)

            # here i am fetching multiple documents asynchronously
            documents = await database_sync_to_async(lambda: list(Document.objects.filter(uploaded_by=request.user.id)))()
            serializer = DocumentSerializer(documents, many=True)
            data = serializer.data

            # Use sync_to_async for cache set
            await sync_to_async(cache.set)(cache_key, data, timeout=300)  # Cache for 5 min
            logger.info("Successfully cached document")
            return JsonResponse(data, safe=False)

    async def post(self, request):
        """Create a new document"""
        user_id = await asyncio.to_thread(lambda: request.user.id)
        logger.debug("Creating new document")
        data = request.POST.dict()  # converting querydict to a mutable dictionary, because here i am fetching data using Form, request.data fetches Json data
        files = request.FILES  # because file data is stored separately

        # actual_content_type = get_content_type(files.get("file"))
        # if actual_content_type != data.get("content_type"):
        #     return JsonResponse({"error": "Content Type mismatch", "message":f"Actual Content-type is {actual_content_type}"}, status=400)

        serializer = DocumentSerializer(data={**data, "file": files.get("file")}) # ** is just a short version of writing each attributes of data
        if serializer.is_valid():
            # saving document asynchronously
            document = await sync_to_async(Document.objects.create, thread_sensitive=True)(
                title=serializer.validated_data["title"],
                file=serializer.validated_data["file"],
                content_type=serializer.validated_data["content_type"],
                uploaded_by=request.user,  # as i made this field is read-only, so i pass it separately
                processed=False
            )

            #serializing the document
            result = DocumentSerializer(document)
            print("got serialized datat")
            print(f"Dispatching Celery task for document ID: {document.id}")
            # processed = process_document_task.delay(document.id)
            processor = DocumentProcessor()
            processed = await processor.process_document(document.id)
            # processed = await process_document_task.apply_async(args=[document.id])
            # processed = await asyncio.run(process_document_task(document.id))
            # result = AsyncResult(processed.id)
            
            # print(f"The result is: {processed}")
            print(f"Task dispatched: {processed}")
            if processed == True:
                logger.info("Document processed successfully")
            else:
                logger.error("Failed to process document")

            print(f"Task dispatched: {processed}")
            if processed == True:
                logger.info("Document processed successfully")
            else:
                logger.error("Failed to process document")

            
            cache_key = f"document:{document.id}_createdBy {user_id}"
            await sync_to_async(cache.set, thread_sensitive=True)(cache_key, result, timeout=3000)  # Cache for 5 min
            logger.info("Successfully cached data in cache memory")
            return JsonResponse(result.data, status=201)

        return JsonResponse(serializer.errors, status=400)

    async def delete(self, request, pk):
        user_id = await asyncio.to_thread(lambda: request.user.id)

        try:
            logger.debug("Deleting document")
            document = await get_document(id=pk)
            await sync_to_async(document.delete, thread_sensitive=True)()
            cache_key = f"document:{pk}_createdBy {user_id}"
            await sync_to_async(cache.delete, thread_sensitive=True)(cache_key)
            logger.info("Successfully deleted document and cleared cache")
            return JsonResponse({"message":"successfully deleted document"},status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            logger.error("Document not found")
            return JsonResponse({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)


class AsyncDocumentReprocessView(View):
    permission_classes = [permissions.IsAuthenticated]
    
    async def get(self, request, pk):
        user_id = await asyncio.to_thread(lambda: request.user.id)

        try:
            logger.debug("fetching document for reprocessing")
            document = await get_document(id=pk)
            
            # deleting existing chunks
            await delete_chunks(document)
            
            # initially not processed
            document.processed = False
            
            
            processor = DocumentProcessor()
            processed = await processor.process_document(document.id)
            # processed = process_document_task.apply_async((document.id,))

            if processed:
                logger.info("Document reprocessing started")
                document.processed = True
                await save_document(document)
                cache_key = f"document:{pk}_createdBy {user_id}"
                await sync_to_async(cache.set, thread_sensitive=True)(cache_key, DocumentSerializer(document).data, timeout=3000)  # Cache for 5 min
                return JsonResponse({'status': 'Document reprocessing successful'})
            
            return JsonResponse({'status': 'Document queued for reprocessing'})
        except ObjectDoesNotExist:
            return JsonResponse({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Failed to reprocess document: {str(e)}")
            return JsonResponse({'error': 'Failed to reprocess document'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
