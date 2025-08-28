# Supporting Infrastructure

## Postgres
- Port: 5432; Volume: postgres_data

## Redis
- Port: 6379; Volume: redis_data

## Zookeeper
- Port: 2181

## Kafka
- Port: 9092; Depends on Zookeeper

## Elasticsearch
- Port: 9200; Volume: elasticsearch_data

## MinIO
- Ports: 9000 (S3), 9001 (console)

## MongoDB
- Port: 27017; Volume: mongo_data

## MLflow
- Port: 5000; Volume: mlflow_data

## RabbitMQ
- Ports: 5672 (AMQP), 15672 (UI); Volume: rabbitmq_data

## Prometheus
- Port: 9090; Volume: prometheus_data

## Grafana
- Port: 3000; Volume: grafana_data

## Chroma
- Port: 8000; Volume: chroma_data
