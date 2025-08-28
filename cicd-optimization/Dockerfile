FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies directly (no Pipenv)
RUN pip install --no-cache-dir --default-timeout=120 \
  fastapi==0.95.2 \
  uvicorn \
  psycopg2-binary \
  redis \
  requests \
  "pydantic<2" \
  python-multipart

COPY . .

EXPOSE 8085

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8085"]
