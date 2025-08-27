FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies directly (no Pipenv)
RUN pip install --no-cache-dir --default-timeout=120 \
  fastapi==0.95.2 \
  uvicorn \
  httpx \
  "python-jose[cryptography]" \
  python-multipart \
  "pydantic[email]<2" \
  requests

# Copy application code
COPY . .

# Expose port
EXPOSE 8088

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8088"]