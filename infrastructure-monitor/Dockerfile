FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies directly (no Pipenv)
RUN pip install --no-cache-dir --default-timeout=120 \
  fastapi==0.95.2 \
  uvicorn \
  "pydantic<2" \
  "python-jose[cryptography]" \
  requests \
  prometheus-client \
  psutil \
  docker \
  kubernetes \
  pytz \
  httpx \
  redis \
  pika

# Copy application code
COPY . .

# Expose port
EXPOSE 8082

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8082"]
