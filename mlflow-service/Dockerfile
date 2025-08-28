FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir mlflow boto3 gunicorn

EXPOSE 5000

# Default to sqlite backend; override via args/env at runtime
CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000", "--backend-store-uri", "sqlite:///mlflow.db", "--default-artifact-root", "s3://mlflow/"]
