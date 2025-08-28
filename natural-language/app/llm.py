import requests
from typing import Callable, Dict, List

from .config import settings

# Provider callables return a string completion given a prompt and optional system instruction


def _ollama_caller() -> Callable[[str, str], str]:
    base = settings.OLLAMA_BASE_URL.rstrip("/")
    model = settings.LLM_MODEL

    def _call(prompt: str, system: str = "") -> str:
        # Use generate endpoint for simplicity
        payload = {"model": model, "prompt": f"{system}\n\n{prompt}", "stream": False}
        resp = requests.post(f"{base}/api/generate", json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "")

    return _call


def _openrouter_caller() -> Callable[[str, str], str]:
    api_key = settings.OPENROUTER_API_KEY
    model = settings.LLM_MODEL
    base = "https://openrouter.ai/api/v1"

    def _call(prompt: str, system: str = "") -> str:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": model, "messages": messages}
        resp = requests.post(
            f"{base}/chat/completions", headers=headers, json=payload, timeout=120
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")

    return _call


def _huggingface_caller() -> Callable[[str, str], str]:
    api_url = f"https://api-inference.huggingface.co/models/{settings.LLM_MODEL}"
    headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}

    def _call(prompt: str, system: str = "") -> str:
        payload = {
            "inputs": f"{system}\n\n{prompt}",
            "parameters": {"temperature": 0.7},
        }
        resp = requests.post(api_url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        # Text generation returns list[dict{"generated_text": str}] or string for some models
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return data[0].get("generated_text", "")
        if isinstance(data, str):
            return data
        return ""

    return _call


def _get_llm_caller() -> Callable[[str, str], str]:
    provider = settings.LLM_PROVIDER.lower()
    if provider == "ollama":
        return _ollama_caller()
    if provider == "openrouter":
        return _openrouter_caller()
    if provider == "huggingface":
        return _huggingface_caller()
    raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")


def _should_stub() -> bool:
    p = settings.LLM_PROVIDER.lower()
    if p == "openrouter" and not settings.OPENROUTER_API_KEY:
        return True
    if p == "huggingface" and not settings.HUGGINGFACE_API_KEY:
        return True
    return settings.DEBUG


# Process natural language query
async def process_query(query: str, context: str | None = None) -> str:
    system_prompt = (
        "You are an AI DevOps Assistant that helps with DevOps tasks and explains DevOps "
        "concepts. You can provide information about infrastructure, CI/CD pipelines, "
        "monitoring, and other DevOps topics. Always provide accurate and helpful information. "
        "If you're unsure, say so rather than making up information."
    )

    user_prompt = (
        query
        if not context
        else (
            f"Based on the following context:\n\n{context}\n\nAnswer the following question: {query}"
        )
    )

    try:
        llm_call = _get_llm_caller()
        return llm_call(user_prompt, system_prompt)
    except Exception:
        if _should_stub():
            return f"[stub] Answer to: {query}"
        raise


# Generate Infrastructure-as-Code
async def generate_iac(requirements: str, platform: str) -> str:
    system_prompt = (
        "You are an AI DevOps Assistant specialized in generating Infrastructure-as-Code (IaC). "
        "You can create Terraform, CloudFormation, Ansible, or Kubernetes manifests based on requirements. "
        "Always follow best practices for the specific IaC tool and ensure the code is secure and efficient."
    )
    prompt = (
        f"Generate Infrastructure-as-Code for {platform} based on the following requirements:\n\n"
        f"{requirements}\n\nProvide the complete code with concise explanations."
    )
    try:
        llm_call = _get_llm_caller()
        return llm_call(prompt, system_prompt)
    except Exception:
        if _should_stub():
            return f"# [stub] {platform} IaC for requirements\n# {requirements}"
        raise


# Explain DevOps concept
async def explain_concept(concept: str) -> str:
    system_prompt = (
        "You are an AI DevOps Assistant that explains DevOps concepts clearly and accurately. "
        "Provide comprehensive explanations with examples where appropriate. Cover the concept's purpose, "
        "how it's used in practice, and its benefits."
    )
    prompt = f"Explain the following DevOps concept in detail: {concept}"
    try:
        llm_call = _get_llm_caller()
        return llm_call(prompt, system_prompt)
    except Exception:
        if _should_stub():
            return f"[stub] Explanation of {concept}: A brief overview of the concept in DevOps."
        raise
