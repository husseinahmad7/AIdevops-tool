# When to use the original approach:

Need offline/air-gapped deployments
Require custom fine-tuned models
Need maximum performance for embeddings
Have GPU resources available
# natural-language/app/llm.py (ORIGINAL - for learning)
from langchain.llms import Ollama
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import HuggingFaceEmbeddings, OllamaEmbeddings
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
import os
import requests

from .config import settings

# Initialize embeddings model
def get_embeddings():
    """
    Creates embedding models for vector similarity search.
    HuggingFace embeddings run locally and require sentence-transformers (large download).
    Ollama embeddings require a local Ollama server with embedding models.
    """
    if settings.LLM_PROVIDER == "ollama":
        return OllamaEmbeddings(base_url=settings.OLLAMA_BASE_URL, model="nomic-embed-text")
    else:
        # This downloads ~500MB+ models like all-mpnet-base-v2
        return HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)

# Initialize LLM based on provider
def get_llm():
    """
    Creates LLM instances. Local models require large downloads.
    Cloud APIs are more scalable for production.
    """
    if settings.LLM_PROVIDER == "ollama":
        # Requires local Ollama server with models pulled
        return Ollama(base_url=settings.OLLAMA_BASE_URL, model=settings.LLM_MODEL)
    elif settings.LLM_PROVIDER == "openrouter":
        # Cloud API - most scalable option
        return ChatOpenAI(
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base="https://openrouter.ai/api/v1",
            model=settings.LLM_MODEL,
            temperature=0.7
        )
    elif settings.LLM_PROVIDER == "huggingface":
        # Hugging Face Inference API - good middle ground
        api_url = f"https://api-inference.huggingface.co/models/{settings.LLM_MODEL}"
        headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}
        
        def query_huggingface(prompt):
            payload = {"inputs": prompt, "parameters": {"temperature": 0.7}}
            response = requests.post(api_url, headers=headers, json=payload)
            return response.json()[0]["generated_text"]
        
        return query_huggingface
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")

# Process natural language query with context retrieval
async def process_query(query: str, context: str = None):
    """
    Main query processing with optional RAG (Retrieval Augmented Generation).
    Uses LangChain chains for complex prompt management.
    """
    llm = get_llm()
    
    system_prompt = """
    You are an AI DevOps Assistant that helps with DevOps tasks and explains DevOps concepts.
    You can provide information about infrastructure, CI/CD pipelines, monitoring, and other DevOps topics.
    Always provide accurate and helpful information. If you're unsure, say so rather than making up information.
    """
    
    if context:
        # RAG: Use retrieved context to enhance responses
        prompt_template = PromptTemplate(
            input_variables=["context", "query"],
            template="""Based on the following context:\n\n{context}\n\nAnswer the following question: {query}"""
        )
        chain = LLMChain(llm=llm, prompt=prompt_template)
        response = chain.run({"context": context, "query": query})
    else:
        # Direct LLM query without context
        if isinstance(llm, ChatOpenAI):
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=query)
            ]
            response = llm(messages).content
        else:
            prompt = f"{system_prompt}\n\nUser: {query}\n\nAI:"
            response = llm(prompt)
    
    return response

# Generate Infrastructure-as-Code with structured prompts
async def generate_iac(requirements: str, platform: str):
    """
    Specialized IaC generation using LangChain prompt templates.
    Could be extended with few-shot examples or validation chains.
    """
    llm = get_llm()
    
    system_prompt = """
    You are an AI DevOps Assistant specialized in generating Infrastructure-as-Code (IaC).
    You can create Terraform, CloudFormation, Ansible, or Kubernetes manifests based on requirements.
    Always follow best practices for the specific IaC tool and ensure the code is secure and efficient.
    """
    
    prompt_template = PromptTemplate(
        input_variables=["platform", "requirements"],
        template="""Generate Infrastructure-as-Code for {platform} based on the following requirements:\n\n{requirements}\n\nProvide the complete code with explanations."""
    )
    
    chain = LLMChain(llm=llm, prompt=prompt_template)
    response = chain.run({"platform": platform, "requirements": requirements})
    
    return response

# Conversational memory for multi-turn interactions
def create_conversation_chain():
    """
    Creates a conversational chain with memory for multi-turn DevOps consultations.
    Useful for complex troubleshooting sessions.
    """
    llm = get_llm()
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        memory=memory,
        verbose=True
    )
# -------------------------------
# natural-language/app/vector_db.py (ORIGINAL - for learning)
from langchain.vectorstores import Chroma, FAISS, Pinecone
from langchain.document_loaders import TextLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import pinecone

from .config import settings
from .llm import get_embeddings

def init_vector_db():
    """
    Initialize vector database for document similarity search.
    Different backends have different trade-offs:
    - Chroma: Local, good for development
    - FAISS: Fast, CPU-only, good for production
    - Pinecone: Managed cloud service, most scalable
    """
    embeddings = get_embeddings()
    
    if settings.VECTOR_DB_TYPE == "chroma":
        # Local ChromaDB - persists to disk
        db_directory = "./data/chroma_db"
        os.makedirs(db_directory, exist_ok=True)
        return Chroma(persist_directory=db_directory, embedding_function=embeddings)
    
    elif settings.VECTOR_DB_TYPE == "pinecone":
        # Managed Pinecone service
        pinecone.init(
            api_key=settings.VECTOR_DB_API_KEY,
            environment=settings.VECTOR_DB_ENVIRONMENT
        )
        
        # Create index if it doesn't exist
        if settings.VECTOR_DB_INDEX_NAME not in pinecone.list_indexes():
            pinecone.create_index(
                name=settings.VECTOR_DB_INDEX_NAME,
                dimension=768,  # Must match embedding model dimension
                metric="cosine"
            )
        
        return Pinecone.from_existing_index(
            index_name=settings.VECTOR_DB_INDEX_NAME,
            embedding=embeddings
        )
    
    elif settings.VECTOR_DB_TYPE == "faiss":
        # Local FAISS index - fast CPU-based similarity search
        return FAISS(embedding_function=embeddings)
    
    else:
        raise ValueError(f"Unsupported vector database type: {settings.VECTOR_DB_TYPE}")

def load_documents(directory_path=None):
    """
    Load and chunk documents for vector search.
    This is the 'ingestion' phase of RAG systems.
    """
    if directory_path is None:
        directory_path = settings.DOCUMENT_STORE_PATH
    
    os.makedirs(directory_path, exist_ok=True)
    
    # Load all text files from directory
    loader = DirectoryLoader(directory_path, glob="**/*.txt")
    documents = loader.load()
    
    # Split documents into chunks for better retrieval
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,  # Characters per chunk
        chunk_overlap=200  # Overlap to maintain context
    )
    texts = text_splitter.split_documents(documents)
    
    # Initialize vector database and add documents
    vector_db = init_vector_db()
    vector_db.add_documents(texts)
    
    return {"status": "success", "document_count": len(texts)}

async def search_documents(query, k=5):
    """
    Semantic search through document collection.
    Returns most relevant chunks for RAG context.
    """
    vector_db = init_vector_db()
    results = vector_db.similarity_search(query, k=k)
    
    return [
        {
            "content": doc.page_content,
            "metadata": doc.metadata,
            "score": getattr(doc, 'score', None)  # Some DBs provide similarity scores
        }
        for doc in results
    ]

async def add_document(content, metadata=None):
    """
    Add single document to vector store.
    Useful for real-time knowledge base updates.
    """
    if metadata is None:
        metadata = {}
    
    # Chunk the document
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    
    from langchain.schema import Document
    doc = Document(page_content=content, metadata=metadata)
    texts = text_splitter.split_documents([doc])
    
    # Add to vector store
    vector_db = init_vector_db()
    vector_db.add_documents(texts)
    
    return {"status": "success", "chunk_count": len(texts)}

# Advanced RAG patterns
async def hybrid_search(query, k=5, alpha=0.5):
    """
    Combines semantic search with keyword search for better retrieval.
    Alpha controls the balance between semantic and keyword matching.
    """
    # This would require additional setup with keyword search engines
    # like Elasticsearch or implementing BM25 scoring
    pass

async def rerank_results(query, documents, top_k=3):
    """
    Re-rank retrieved documents using cross-encoder models.
    Improves relevance at the cost of additional computation.
    """
    # Would use models like ms-marco-MiniLM-L-12-v2 for reranking
    pass

# ---------------
# natural-language/Dockerfile (ORIGINAL - for learning)
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for ML libraries
RUN apt-get update && apt-get install -y \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (HEAVY - 2GB+ download)
RUN pip install --no-cache-dir --default-timeout=120 \
  fastapi==0.95.2 \
  uvicorn \
  "python-jose[cryptography]" \
  python-multipart \
  "pydantic[email]<2" \
  # LangChain ecosystem
  langchain \
  langchain-openai \
  langchain-community \
  # Vector databases
  chromadb \
  faiss-cpu \
  pinecone-client \
  # ML libraries (LARGE DOWNLOADS)
  sentence-transformers \  # ~500MB+ models
  torch \                  # ~800MB+ PyTorch
  transformers \           # Hugging Face transformers
  # Utilities
  requests \
  numpy \
  pandas

# Copy application code
COPY . .

EXPOSE 8088

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8088"]