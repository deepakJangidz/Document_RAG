📄 Django DOCUMENT_RAG
🚀 DOCUMENT_RAG is a simple yet powerful Django project designed to handle:
✔ Document Ingestion 📥
✔ Embedding Generation 🔍
✔ Retrieval-based Q&A (RAG) 🤖

⚡ Key Features
📌 Document Ingestion API
✅ Accepts document data
✅ Generates embeddings using a Large Language Model (LLM) library
✅ Stores embeddings for future retrieval

❓ Q&A API
✅ Accepts user questions
✅ Retrieves relevant document embeddings
✅ Generates precise answers using Retrieval-Augmented Generation (RAG)

🗂️ Document Selection API
✅ Allows users to specify which documents should be considered in the RAG-based Q&A process


🛠️ Prerequisites
Ensure you have the required dependencies listed in requirements.txt installed before proceeding.


📥 Installation
  1️⃣ Clone the Repository
    git clone https://github.com/deepakJangidz/Document_RAG.git
    cd document_rag
  2️⃣ Create a Virtual Environment
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
  3️⃣ Install Dependencies
    pip install -r requirements.txt
  4️⃣ Database Setup
    python manage.py migrate
    python manage.py createsuperuser
  5️⃣ Run the Development Server
    uvicorn document_rag.asgi:application --reload


📁 Project Structure
  document_rag/
  │
  ├── manage.py
  ├── document_rag/
  │   ├── __init__.py
  │   ├── settings.py
  │   ├── urls.py
  │   └── asgi.py
  ├── documents/
  │   └── qa/
  ├── templates/
  ├── static/
  └── media/


🔑 Environment Variables (Create a .env file and add your secret key:)
    SECRET_KEY=your-secret-key

