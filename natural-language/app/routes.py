from fastapi import APIRouter, Depends, HTTPException, Request, Body
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import httpx
import os

from .config import settings
from .llm import process_query, generate_iac, explain_concept
from .vector_db import search_documents, add_document, load_documents

router = APIRouter()

# Verify token with User Management Service
async def verify_token(request: Request):
    if not settings.AUTH_ENABLED:
        return {"id": "anonymous", "username": "anonymous", "role": "user"}
    
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.USER_MANAGEMENT_URL}/api/v1/users/validate",
                headers={"Authorization": auth_header}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid token")
            return response.json()
    except httpx.RequestError:
        # If user service is down, we'll still accept the request in development mode
        if settings.DEBUG:
            return {"id": "debug", "username": "debug", "role": "admin"}
        raise HTTPException(status_code=503, detail="Authentication service unavailable")

# Process natural language query
@router.post("/query")
async def query(request: Request, query_data: Dict[str, Any] = Body(...)):
    user = await verify_token(request)

    query_text = query_data.get("query")
    if not query_text:
        raise HTTPException(status_code=400, detail="Query is required")
    
    # Search for relevant documents if context retrieval is enabled
    context = None
    if query_data.get("use_context", True):
        docs = await search_documents(query_text, k=3)
        if docs:
            context = "\n\n".join([doc["content"] for doc in docs])
    
    # Process the query
    response = await process_query(query_text, context)
    
    return {
        "response": response,
        "context_used": bool(context),
        "user_id": user.get("id")
    }

# Generate Infrastructure-as-Code
@router.post("/generate-iac")
async def generate_infrastructure_code(request: Request, data: Dict[str, Any] = Body(...)):
    user = await verify_token(request)

    requirements = data.get("requirements")
    platform = data.get("platform", "terraform")
    
    if not requirements:
        raise HTTPException(status_code=400, detail="Requirements are required")
    
    # Generate IaC
    code = await generate_iac(requirements, platform)
    
    return {
        "code": code,
        "platform": platform,
        "user_id": user.get("id")
    }

# Explain DevOps concept
@router.get("/explain/{concept}")
async def explain_devops_concept(concept: str, request: Request):
    user = await verify_token(request)

    # Explain the concept
    explanation = await explain_concept(concept)
    
    return {
        "concept": concept,
        "explanation": explanation,
        "user_id": user.get("id")
    }

# Document management endpoints
@router.post("/documents")
async def add_new_document(request: Request, data: Dict[str, Any] = Body(...)):
    user = await verify_token(request)

    # Check if user has admin role
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    content = data.get("content")
    metadata = data.get("metadata", {})
    
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")
    
    # Add document to vector database
    result = await add_document(content, metadata)
    
    return result

@router.post("/documents/load")
async def load_all_documents(request: Request, data: Dict[str, Any] = Body(default={})):
    user = await verify_token(request)

    # Check if user has admin role
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    directory = data.get("directory")
    
    # Load documents from directory
    result = load_documents(directory)
    
    return result

@router.get("/documents/search")
async def search_document_database(request: Request, query: str, limit: int = 5):
    user = await verify_token(request)

    # Search documents
    results = await search_documents(query, k=limit)
    
    return {
        "results": results,
        "query": query,
        "user_id": user.get("id")
    }