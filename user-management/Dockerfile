FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies directly (no Pipenv)
RUN pip install --no-cache-dir --default-timeout=120 \
  fastapi \
  uvicorn \
  "python-jose[cryptography]" \
  passlib[bcrypt] \
  python-multipart \
  "pydantic[email]" \
  psycopg2-binary \
  sqlalchemy \
  alembic \
  email-validator

# Copy application code
COPY . .

# Expose port
EXPOSE 8081

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"]