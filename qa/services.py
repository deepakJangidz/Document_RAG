import os
import numpy as np
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.document_loaders import PyPDFLoader
# from langchain.document_loaders import TextLoader
from langchain_community.document_loaders import PyPDFLoader, TextLoader
import sklearn.metrics.pairwise as pw
from django.conf import settings
import json
import uuid
from documents.models import Document, DocumentChunk
from documents.serializers import DocumentChunkSerializer
from asgiref.sync import sync_to_async
import asyncio
from sentence_transformers import SentenceTransformer
import logging
from django.http import JsonResponse
import torch
import numpy as np
from sentence_transformers import SentenceTransformer
from documents.models import DocumentChunk
import torch.nn.functional as F
from asgiref.sync import sync_to_async
import channels
from channels.db import database_sync_to_async


logging.basicConfig(
    level=logging.DEBUG,  
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)



async def save_chunk(chunk):
    print("inside save chunk")
    try:
        logger.debug(f"Saving chunk: {chunk.chunk_id} ")
        await sync_to_async(chunk.save)()
        logger.info(f"Successfully saved chunk: {chunk.chunk_id}")
    except Exception as e:
        logger.error(f"Failed to save chunk {chunk.chunk_id}: {e}", exc_info=True)

# Load model once
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


# converting django ORM operations to async
get_document_by_id = sync_to_async(Document.objects.get)
get_chunk_by_id = sync_to_async(DocumentChunk.objects.get)
create_document_chunk = sync_to_async(DocumentChunk.objects.create)
save_chunk = sync_to_async(lambda chunk: chunk.save())
update_document = sync_to_async(lambda doc: doc.save())
get_chunks = database_sync_to_async(lambda: list(DocumentChunk.objects.all()))
# class OpenAIClient:
#     """Class to handle interactions with OpenAI API"""
#     def __init__(self):
#         try:
#             import openai
#             self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#         except ImportError:
#             raise ImportError("OpenAI package not installed. Run 'pip install openai'")
#         except Exception as e:
#             raise Exception(f"Error initializing OpenAI client: {str(e)}")
    
#     async def get_embeddings(self, texts):
#         """Get embeddings for a list of texts"""
#         try:
#             response = await self.client.embeddings.create(
#                 model="text-embedding-3-small",
#                 input=texts
#             )
#             return [item.embedding for item in response.data]
#         except Exception as e:
#             raise Exception(f"Error getting embeddings: {str(e)}")
    
#     async def generate_answer(self, question, context):
#         """Generate an answer based on the question and context"""
#         try:
#             prompt = f"""
#             You are a helpful assistant that answers questions based on the provided context.
            
#             Context:
#             {context}
            
#             Question: {question}
            
#             Answer the question based only on the provided context. If you cannot find the answer in the context, say "I don't have enough information to answer this question."
#             """
            
#             response = await self.client.chat.completions.create(
#                 model="gpt-3.5-turbo",
#                 messages=[
#                     {"role": "system", "content": "You are a helpful assistant."},
#                     {"role": "user", "content": prompt}
#                 ]
#             )
#             return response.choices[0].message.content
#         except Exception as e:
#             raise Exception(f"Error generating answer: {str(e)}")

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        # self.openai_client = OpenAIClient()
    
    async def process_document(self, document_id):
        try:
            logger.debug("Processing document")
            print("inside process document")
            document = await get_document_by_id(id=document_id)
            print("got document")
            file_path = document.file.path
            print("extracted file path")
            content = await sync_to_async(self._extract_text)(file_path, document.content_type)
            print("got file content")
            chunks = self.text_splitter.split_text(content)
            print("got chunks")
            
            # creating document chunks in the database
            chunk_objects = []
            for idx, chunk_content in enumerate(chunks):
                chunk_id = f"{document.id}-{idx}"
                chunk = await create_document_chunk(
                    document=document,
                    content=chunk_content,
                    chunk_id=chunk_id
                )
                chunk_objects.append(chunk)
            
            # generating embeddings for chunks in batches
            batch_size = 20  # we can adjust it based on API limits
            for i in range(0, len(chunk_objects), batch_size):
                batch = chunk_objects[i:i+batch_size]
                texts = [chunk.content for chunk in batch]
                # await asyncio.sleep(1)  # Wait 1 second between requests
                # embeddings = await self.openai_client.get_embeddings(texts)
                # embeddings = await get_embeddings_with_retry(self.openai_client, texts)
                embeddings = embedding_model.encode(texts)  # No API call needed!


                # here i am updating chunks with embeddings
                print("outside for loop of embeddings")
                for j, chunk in enumerate(batch):
                    chunk.embeddings = embeddings[j].tolist()
                    print(chunk)
                    await save_chunk(chunk)
                    # await sync_to_async(chunk.save, thread_sensitive=True)()

            
            # as now document is processed
            document.processed = True
            await update_document(document)
            
            return True
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            return False
    
    def _extract_text(self, file_path, content_type):
        """Extract text from a document based on its content type"""
        try:
            logger.debug("Extracting text from file: {file_path}")
            if content_type == 'application/pdf':
                loader = PyPDFLoader(file_path)
                pages = loader.load_and_split()
                return "\n".join([page.page_content for page in pages])
            elif content_type in ['text/plain', 'text/markdown']:
                loader = TextLoader(file_path)
                documents = loader.load()
                return "\n".join([doc.page_content for doc in documents])
            else:
                # Handle other file types or use a fallback
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            raise Exception(f"Error extracting text: {str(e)}")


from channels.db import database_sync_to_async  # Correct way to wrap Django ORM queries

# Load the embedding model once
model = SentenceTransformer("all-MiniLM-L6-v2")

def get_embeddings(texts):
    """Generate embeddings for a list of texts using a local model."""
    return model.encode(texts, convert_to_tensor=False)  # Keep as list for storage

# @database_sync_to_async
# def get_chunks_list():
#     """Fetch document chunks synchronously"""
#     return list(DocumentChunk.objects.all())  # Ensur

async def get_document_chunks():
    """Fetch document chunks asynchronously"""
    return await get_chunks()  # Use database_sync_to_async to ensure synchronous execution

class RAGService:
    """Service to handle RAG-based Q&A"""

    async def answer_question(self, question, document_ids=None):
        """Answer a question using RAG with local embeddings"""
        try:
            # Get question embedding
            logger.debug("Answring Question using RAG Services")
            question_embedding = get_embeddings([question])[0]  # Extract first item
            question_embedding = torch.tensor(question_embedding, dtype=torch.float32)  # Ensure tensor format
            
            # Query relevant chunks
            print("above chunks")
            chunks = await get_document_chunks()
            print("got chunks")
            chunks = DocumentChunkSerializer(chunks, many=True)
            print("got serialized chunks")
            print(type(chunks))
            print(type(chunks.data))
            
            if not chunks:
                return "No relevant documents found."

            #  Collect chunk embeddings
            chunk_data = []
            print("above for loop")
            for chunk in chunks.data:
                print("inside for loop")
                # print(chunk)
                if chunk['embeddings'] and isinstance(chunk['embeddings'], list):  # Ensure embeddings exist
                    chunk_data.append({
                        'chunk': chunk,
                        'embeddings': torch.tensor(chunk['embeddings'], dtype=torch.float32)  # Convert to tensor
                    })
            
            if not chunk_data:
                return "No processed document chunks found."

            # Compute similarity scores
            print("computing chunk embedding scores")
            chunk_embeddings = torch.stack([item['embeddings'] for item in chunk_data])  # Stack into tensor
            print("got embedding scores")

            similarities = F.cosine_similarity(
                question_embedding,  
                chunk_embeddings,  
                dim=1  # Compute across embedding dimensions
            )
            print("got similarity scores")

            # Get top 5 most relevant chunks
            top_k = 5
            top_indices = torch.argsort(similarities, descending=True)[:top_k]
            
            # Prepare context from top chunks
            context = "\n\n".join([
                chunk_data[i]['chunk']['content'] for i in top_indices
                if 'content' in chunk_data[i]['chunk']
            ])

            # Ensure document references are extracted correctly
            docs_used = set()
            for i in top_indices:
                chunk = chunk_data[i]['chunk']
                if isinstance(chunk, dict) and 'document' in chunk:
                    docs_used.add(chunk['document'])
                elif hasattr(chunk, 'document'):
                    docs_used.add(chunk.document.id)  # Store document ID
            
            return {
                'answer': f"Based on the documents, the answer is:\n{context[:300]}...",  # Truncate for readability
                'documents_used': list(docs_used)
            }
        except Exception as e:
            logger.error(f"Error in RAG service: {str(e)}")
            raise Exception(f"Error in RAG service: {str(e)}")

    # @database_sync_to_async
    # def filter_chunks(self):
    #     """Fetch relevant document chunks asynchronously"""
    #     print("i am inside filter_chunks")
    #     print(document_ids)
    #     # if document_ids:
    #     #     return await sync_to_async(lambda: list(DocumentChunk.objects.all()), thread_sensitive=True)()
    #     # return await sync_to_async(lambda: list(DocumentChunk.objects.all()), thread_sensitive=True)()
    #     return list(DocumentChunk.objects.all())

