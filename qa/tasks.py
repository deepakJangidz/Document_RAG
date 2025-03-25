# from celery import shared_task
# from .services import DocumentProcessor
# from documents.models import Document
# import asyncio

# @shared_task
# def process_document_task(document_id):
#     """Process document asynchronously inside Celery"""
#     try:
#         print("inside process_document_task")
#         document = Document.objects.get(id=document_id)
#         processor = DocumentProcessor()

#         # Run async function in event loop (Celery doesn't support async)
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         processed = loop.run_until_complete(processor.process_document(document.id))
#         print(f"The value of processed is {processed}")
#         if processed == True:
#             document.processed = True
#             document.save()

#         return processed
#     except Document.DoesNotExist:
#         return f"Document {document_id} not found"
#     except Exception as e:
#         return f"Task failed: {str(e)}"



import traceback
import asyncio
from celery import shared_task
from celery.utils.log import get_task_logger
from django.db import transaction

logger = get_task_logger(__name__)

@shared_task(bind=True, max_retries=3)
def process_document_task(self, document_id):
    """
    Improved document processing task with:
    - Detailed logging
    - Error tracking
    - Retry mechanism
    - Transaction management
    """
    try:
        # Use transaction to ensure database consistency
        with transaction.atomic():
            from documents.models import Document
            from .services import DocumentProcessor

            logger.info(f"Starting document processing for ID: {document_id}")
            
            # Fetch document with explicit error handling
            try:
                document = Document.objects.select_for_update().get(id=document_id)
            except Document.DoesNotExist:
                logger.error(f"Document with ID {document_id} not found")
                return False

            # Initialize processor
            processor = DocumentProcessor()

            # Use asyncio.run with timeout to prevent hanging
            try:
                processed = asyncio.run(
                    asyncio.wait_for(
                        processor.process_document(document.id), 
                        timeout=300  # 5-minute timeout
                    )
                )
            except asyncio.TimeoutError:
                logger.error(f"Document processing timed out for ID: {document_id}")
                self.retry(countdown=60)  # Wait 1 minute before retrying
                return False
            except Exception as proc_error:
                logger.error(f"Processing error for document {document_id}: {proc_error}")
                logger.error(traceback.format_exc())
                self.retry(exc=proc_error, countdown=30)  # Retry after 30 seconds
                return False

            # Update document status
            if processed:
                document.processed = True
                document.save()
                logger.info(f"Successfully processed document {document_id}")
                return True
            else:
                logger.warning(f"Document {document_id} processing returned False")
                return False

    except Exception as e:
        logger.critical(f"Unhandled error in document processing: {e}")
        logger.critical(traceback.format_exc())
        return False