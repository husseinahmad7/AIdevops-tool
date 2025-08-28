# Natural Language Service

- URL (direct): http://localhost:8088
- Gateway: http://localhost/api/v1/nlp
- Health: GET /health

## Purpose
API-only LLM calls (OpenRouter/HF/Ollama). No heavy local ML deps. In DEBUG or without keys, returns stub responses.

## Endpoints
- GET /api/v1/nlp/explain/{concept}
- POST /api/v1/nlp/query {query, use_context}
- GET /api/v1/nlp/documents/search?query=&limit=

## Config
- LLM_PROVIDER=openrouter|huggingface|ollama
- OPENROUTER_API_KEY, HUGGINGFACE_API_KEY, OLLAMA_BASE_URL
- AUTH_ENABLED=true (default)

## Example
curl -sS -H "Authorization: Bearer $TOKEN" http://localhost/api/v1/nlp/explain/devops

## Troubleshooting
- 500: set API keys or use DEBUG=true; check gateway/body forwarding; see service logs
