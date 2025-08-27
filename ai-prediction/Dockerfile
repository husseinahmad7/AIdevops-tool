FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for numerical libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install runtime dependencies directly (no Pipenv)
RUN pip install --no-cache-dir --default-timeout=120 \
  fastapi==0.95.2 \
  uvicorn \
  "pydantic<2" \
  "python-jose[cryptography]" \
  requests \
  httpx \
  numpy \
  pandas \
  scikit-learn \
  joblib \
  matplotlib \
  seaborn \
  prophet \
  statsmodels \
  redis \
  mlflow \
  boto3

# Copy application code
COPY . .

# Expose port
EXPOSE 8083

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8083"]