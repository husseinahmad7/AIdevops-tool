# Natural Language Service — Legacy (Commented/Disabled) Reference

This document preserves the previous heavy (LangChain + local embeddings) implementation for learning purposes. Do not re‑enable in production unless you intentionally want local models and vector DBs.

## Legacy app/llm.py (reference only)

```python
# LEGACY IMPLEMENTATION (DISABLED)
# from langchain.llms import Ollama
# from langchain.chat_models import ChatOpenAI
# from langchain.embeddings import HuggingFaceEmbeddings, OllamaEmbeddings
# from langchain.schema import HumanMessage, SystemMessage
# from langchain.prompts import PromptTemplate
# from langchain.chains import LLMChain
# from langchain.memory import ConversationBufferMemory
# import os
# import requests
# from .config import settings
#
# def get_embeddings():
#     if settings.LLM_PROVIDER == "ollama":
#         return OllamaEmbeddings(base_url=settings.OLLAMA_BASE_URL, model="nomic-embed-text")
#     else:
#         return HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)
#
# def get_llm():
#     if settings.LLM_PROVIDER == "ollama":
#         return Ollama(base_url=settings.OLLAMA_BASE_URL, model=settings.LLM_MODEL)
#     elif settings.LLM_PROVIDER == "openrouter":
#         return ChatOpenAI(
#             openai_api_key=settings.OPENROUTER_API_KEY,
#             openai_api_base="https://openrouter.ai/api/v1",
#             model=settings.LLM_MODEL,
#             temperature=0.7
#         )
#     elif settings.LLM_PROVIDER == "huggingface":
#         api_url = f"https://api-inference.huggingface.co/models/{settings.LLM_MODEL}"
#         headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}
#         def query_huggingface(prompt):
#             payload = {"inputs": prompt, "parameters": {"temperature": 0.7}}
#             response = requests.post(api_url, headers=headers, json=payload)
#             return response.json()[0]["generated_text"]
#         return query_huggingface
#     else:
#         raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")
#
# async def process_query(query: str, context: str = None):
#     llm = get_llm()
#     system_prompt = (
#         "You are an AI DevOps Assistant that helps with DevOps tasks and explains DevOps concepts."
#     )
#     if context:
#         prompt_template = PromptTemplate(
#             input_variables=["context", "query"],
#             template="""Based on the following context:\n\n{context}\n\nAnswer the following question: {query}"""
#         )
#         chain = LLMChain(llm=llm, prompt=prompt_template)
#         response = chain.run({"context": context, "query": query})
#     else:
#         if isinstance(llm, ChatOpenAI):
#             messages = [SystemMessage(content=system_prompt), HumanMessage(content=query)]
#             response = llm(messages).content
#         else:
#             prompt = f"{system_prompt}\n\nUser: {query}\n\nAI:"
#             response = llm(prompt)
#     return response
#
# async def generate_iac(requirements: str, platform: str):
#     llm = get_llm()
#     prompt_template = PromptTemplate(
#         input_variables=["platform", "requirements"],
#         template="""Generate Infrastructure-as-Code for {platform} based on the following requirements:\n\n{requirements}\n\nProvide the complete code with explanations."""
#     )
#     chain = LLMChain(llm=llm, prompt=prompt_template)
#     return chain.run({"platform": platform, "requirements": requirements})
#
# async def explain_concept(concept: str):
#     llm = get_llm()
#     prompt_template = PromptTemplate(
#         input_variables=["concept"],
#         template="""Explain the following DevOps concept in detail: {concept}\n\nInclude its purpose, how it's implemented, and real-world examples."""
#     )
#     chain = LLMChain(llm=llm, prompt=prompt_template)
#     return chain.run({"concept": concept})
```

## Legacy app/vector_db.py (reference only)

```python
# LEGACY IMPLEMENTATION (DISABLED)
# from langchain.vectorstores import Chroma, FAISS, Pinecone
# from langchain.document_loaders import TextLoader, DirectoryLoader
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# import os
# import pinecone
# from .config import settings
# from .llm import get_embeddings
#
# def init_vector_db():
#     embeddings = get_embeddings()
#     if settings.VECTOR_DB_TYPE == "chroma":
#         db_directory = "./data/chroma_db"
#         os.makedirs(db_directory, exist_ok=True)
#         return Chroma(persist_directory=db_directory, embedding_function=embeddings)
#     elif settings.VECTOR_DB_TYPE == "pinecone":
#         pinecone.init(api_key=settings.VECTOR_DB_API_KEY, environment=settings.VECTOR_DB_ENVIRONMENT)
#         if settings.VECTOR_DB_INDEX_NAME not in pinecone.list_indexes():
#             pinecone.create_index(name=settings.VECTOR_DB_INDEX_NAME, dimension=768, metric="cosine")
#         return Pinecone.from_existing_index(index_name=settings.VECTOR_DB_INDEX_NAME, embedding=embeddings)
#     elif settings.VECTOR_DB_TYPE == "faiss":
#         return FAISS(embedding_function=embeddings)
#     else:
#         raise ValueError(f"Unsupported vector database type: {settings.VECTOR_DB_TYPE}")
#
# def load_documents(directory_path=None):
#     if directory_path is None:
#         directory_path = settings.DOCUMENT_STORE_PATH
#     os.makedirs(directory_path, exist_ok=True)
#     loader = DirectoryLoader(directory_path, glob="**/*.txt")
#     documents = loader.load()
#     text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
#     texts = text_splitter.split_documents(documents)
#     vector_db = init_vector_db()
#     vector_db.add_documents(texts)
#     return {"status": "success", "document_count": len(texts)}
#
# async def search_documents(query, k=5):
#     vector_db = init_vector_db()
#     results = vector_db.similarity_search(query, k=k)
#     return [{"content": doc.page_content, "metadata": doc.metadata} for doc in results]
#
# async def add_document(content, metadata=None):
#     if metadata is None:
#         metadata = {}
#     text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
#     from langchain.schema import Document
#     doc = Document(page_content=content, metadata=metadata)
#     texts = text_splitter.split_documents([doc])
#     vector_db = init_vector_db()
#     vector_db.add_documents(texts)
#     return {"status": "success", "chunk_count": len(texts)}
```

