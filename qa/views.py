from rest_framework.views import APIView, View
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import QuestionAnswer
from .serializers import QuestionAnswerSerializer, QuestionSerializer
from .services import RAGService
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async
from documents.models import Document
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from .forms import QAForm
from django.shortcuts import render
from django.core.cache import cache
import logging
import asyncio

logging.basicConfig(
    level=logging.DEBUG,  
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)



get_qa = sync_to_async(QuestionAnswer.objects.get, thread_sensitive=True)
get_serialized_qa = sync_to_async(lambda: QuestionAnswerSerializer(qa).data, thread_sensitive=True)

def ask_form_view(request):
    form = QAForm()
    return render(request, "QA_ask.html", {"form": form})

class AsyncQAView(View):
    permission_classes = [IsAuthenticated]
    
    async def get(self, request, pk=None):
        user_id = await asyncio.to_thread(lambda: request.user.id) # asynchrously fetching user id

        if pk:
            cache_key = f"QA_history_{pk}_created_by_{user_id}"
            logger.debug("Checking data in cached memory")
            cached_document = await sync_to_async(cache.get, thread_sensitive=True)(cache_key)
            
            if cached_document:
                logger.info("Found QA history in cached memory")
                return JsonResponse(cached_document, safe=False)
            try:
                qa = await get_qa(id=pk)
                serialized_data = await sync_to_async(lambda: QuestionAnswerSerializer(qa).data, thread_sensitive=True)()
                
                await sync_to_async(cache.set, thread_sensitive=True)(cache_key, serialized_data, timeout=300)  # Cache for 5 min
                logger.info("Found QA history and also cached in cached memory")
                return JsonResponse(serialized_data, safe=False)
            except ObjectDoesNotExist:
                logger.error("Asked QA not found")
                return JsonResponse({"error": "Question not found"}, status=status.HTTP_404_NOT_FOUND, safe=False)
        else:
            # qa_history = await sync_to_async(lambda: list(QuestionAnswer.objects.filter(user=request.user).order_by('-created_at')), thread_sensitive=True)()
            cache_key = f"QA_history_created_by_{user_id}"
            cached_documents = await sync_to_async(cache.get, thread_sensitive=True)(cache_key)

            if cached_documents:
                logger.info("Found QA history in cached memory")
                return JsonResponse(cached_documents, safe=False)
            qa_history = await sync_to_async(
                lambda: list(
                    QuestionAnswer.objects
                    .filter(user_id=request.user.id)
                    .order_by('-created_at')
                    .prefetch_related("documents_used")  # using prefetch_related to improve performance
                    .only("question", "answer", "created_at")[:10]  # limiting the response to improve performance
                ),
                thread_sensitive=True
            )()
            serialized_data = await sync_to_async(lambda: QuestionAnswerSerializer(qa_history, many=True).data, thread_sensitive=True)()
            await sync_to_async(cache.set)(cache_key, serialized_data, timeout=300)  # Cache for 5 min
            logger.info("QA history fetched and also stored in cache")
            return JsonResponse(serialized_data, safe=False)

class AsyncAskView(View):
    """Async view for asking questions"""
    permission_classes = [IsAuthenticated]
    
    async def post(self, request):
        """Ask a question using RAG"""
        data = request.POST.dict()  # converting QueryDict to a mutable dictionary
        if data["document_ids"] == "":
            data["document_ids"] = []
        else:
            data["document_ids"] = [(data["document_ids"])]
        print(data)
        print(type(data["document_ids"]))
        

        serializer = QuestionSerializer(data={**data})
        if serializer.is_valid():
            print(serializer.validated_data)
            question = serializer.validated_data['question']
            document_ids = serializer.validated_data.get('document_ids', None)
            print(document_ids)
            # using RAG service to answer the question
            rag_service = RAGService()

            try:
                result = await rag_service.answer_question(question, document_ids)
                if isinstance(result, str):
                    # Error occurred
                    return JsonResponse({'error': result}, status=status.HTTP_400_BAD_REQUEST)
                
                # Create question-answer record (convert to async)
          
                qa_record = await sync_to_async(QuestionAnswer.objects.create, thread_sensitive=True)(
                    user=request.user,
                    question=question,
                    answer=result['answer']
                )
                await sync_to_async(qa_record.documents_used.set, thread_sensitive=True)(result['documents_used'])  # adding ManyToMany relations
                
                # adding document_used (asynchromously)
                for doc in result['documents_used']:
                    await sync_to_async(qa_record.documents_used.add)(doc)
                
                print("now sending data")
                return JsonResponse({
                    # 'id': qa_record.id,
                    'question': question,
                    'answer': result['answer'],
                    # 'documents_used': [doc.id for doc in result['documents_used']]
                    'documents_used': result['documents_used']  # If it already contains IDs, return directly

                })
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
