# 🚀 Deployment Guide

## Overview

This guide covers deploying the SaaS Market Intelligence Platform with agentic RAG capabilities across different environments, from development to enterprise production.

## Prerequisites

### System Requirements

#### Minimum Requirements
- **CPU**: 4 cores (8 recommended)
- **RAM**: 8GB (16GB recommended for production)
- **Storage**: 50GB SSD (100GB+ for production)
- **Python**: 3.10+ (3.12 recommended)
- **Network**: Stable internet for API calls

#### Production Requirements
- **CPU**: 8+ cores
- **RAM**: 32GB+
- **Storage**: 500GB+ NVMe SSD
- **Load Balancer**: Nginx or AWS ALB
- **Database**: PostgreSQL for metadata
- **Monitoring**: Prometheus + Grafana

### External Dependencies

```bash
# Required API Keys
export OPENAI_API_KEY="sk-..."           # GPT-4 and embeddings
export SERPAPI_KEY="your_serpapi_key"    # Search data (optional)
export REDDIT_CLIENT_ID="your_id"       # Reddit API (optional)
export REDDIT_CLIENT_SECRET="your_secret" # Reddit API (optional)

# Optional Services
export SENTRY_DSN="https://..."         # Error tracking
export SLACK_WEBHOOK_URL="https://..."  # Notifications
```

## Environment Setup

### 1. Development Environment

#### Local Setup

```bash
# Clone repository
git clone https://github.com/yourusername/agent-web-scraper.git
cd agent-web-scraper

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Initialize knowledge bases
python scripts/test_agentic_rag.py

# Start development server
python run.py --dev
```

#### Docker Development

```dockerfile
# Dockerfile.dev
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source code
COPY . .

# Install in development mode
RUN pip install -e .

# Expose port
EXPOSE 8000

# Development command
CMD ["python", "run.py", "--dev", "--reload"]
```

```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - /app/venv  # Exclude venv from volume mount
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PYTHONPATH=/app
    env_file:
      - .env

  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"
    volumes:
      - chroma_data:/chroma/chroma
    environment:
      - IS_PERSISTENT=TRUE

volumes:
  chroma_data:
```

### 2. Production Environment

#### Production Dockerfile

```dockerfile
# Dockerfile
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Production command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "app.main:app"]
```

#### Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - PYTHONPATH=/app
    env_file:
      - .env.prod
    depends_on:
      - chromadb
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  chromadb:
    image: chromadb/chroma:latest
    restart: unless-stopped
    ports:
      - "8001:8000"
    volumes:
      - chroma_data:/chroma/chroma
    environment:
      - IS_PERSISTENT=TRUE
      - CHROMA_SERVER_HOST=0.0.0.0

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app

volumes:
  chroma_data:
  redis_data:
```

## Cloud Deployment Options

### 1. AWS Deployment

#### ECS with Fargate

```yaml
# ecs-task-definition.json
{
  "family": "saas-intel-platform",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "8192",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "saas-intel-app",
      "image": "your-ecr-repo/saas-intel:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:openai-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/saas-intel",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

#### Terraform Configuration

```hcl
# terraform/main.tf
provider "aws" {
  region = var.aws_region
}

# VPC and Networking
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "saas-intel-vpc"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "saas-intel-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "saas-intel-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = true
}

# ECS Service
resource "aws_ecs_service" "main" {
  name            = "saas-intel-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.main.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    security_groups = [aws_security_group.ecs_tasks.id]
    subnets         = aws_subnet.private[*].id
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.main.arn
    container_name   = "saas-intel-app"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.main]
}

# RDS for metadata storage
resource "aws_db_instance" "main" {
  identifier     = "saas-intel-db"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.medium"

  allocated_storage     = 100
  max_allocated_storage = 1000
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = "saas_intel"
  username = var.db_username
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  skip_final_snapshot = false
  final_snapshot_identifier = "saas-intel-final-snapshot"

  tags = {
    Name = "saas-intel-database"
  }
}
```

### 2. Google Cloud Platform

#### Cloud Run Deployment

```yaml
# cloudbuild.yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/saas-intel:$COMMIT_SHA', '.']

  # Push the container image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/saas-intel:$COMMIT_SHA']

  # Deploy container image to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'saas-intel-platform'
      - '--image'
      - 'gcr.io/$PROJECT_ID/saas-intel:$COMMIT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--memory'
      - '8Gi'
      - '--cpu'
      - '4'
      - '--max-instances'
      - '100'
      - '--allow-unauthenticated'
```

#### GKE Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: saas-intel-deployment
  labels:
    app: saas-intel
spec:
  replicas: 3
  selector:
    matchLabels:
      app: saas-intel
  template:
    metadata:
      labels:
        app: saas-intel
    spec:
      containers:
      - name: saas-intel
        image: gcr.io/PROJECT_ID/saas-intel:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai-key
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: saas-intel-service
spec:
  selector:
    app: saas-intel
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
```

### 3. Azure Deployment

#### Container Instances

```yaml
# azure-container-group.yaml
apiVersion: 2019-12-01
location: eastus
name: saas-intel-container-group
properties:
  containers:
  - name: saas-intel-app
    properties:
      image: youracr.azurecr.io/saas-intel:latest
      resources:
        requests:
          cpu: 2
          memoryInGb: 8
      ports:
      - port: 8000
        protocol: TCP
      environmentVariables:
      - name: ENVIRONMENT
        value: production
      - name: OPENAI_API_KEY
        secureValue: your-openai-key
  osType: Linux
  restartPolicy: Always
  ipAddress:
    type: Public
    ports:
    - protocol: TCP
      port: 8000
```

## Configuration Management

### Environment Variables

```bash
# .env.prod
ENVIRONMENT=production

# API Keys
OPENAI_API_KEY=sk-...
SERPAPI_KEY=your_serpapi_key

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://localhost:6379/0

# Vector Storage
CHROMA_HOST=chromadb
CHROMA_PORT=8000
VECTOR_STORE_PATH=/data/vector_stores

# Performance
MAX_WORKERS=4
QUERY_TIMEOUT=30
BATCH_SIZE=100

# Monitoring
SENTRY_DSN=https://...
LOG_LEVEL=INFO
METRICS_ENABLED=true

# Security
SECRET_KEY=your-secret-key
API_KEY_REQUIRED=true
CORS_ORIGINS=https://yourdomain.com
```

### Application Configuration

```python
# app/config/production.py
import os
from .base import BaseConfig

class ProductionConfig(BaseConfig):
    """Production configuration"""

    DEBUG = False
    TESTING = False

    # Database
    DATABASE_URL = os.getenv('DATABASE_URL')

    # Vector Storage
    VECTOR_STORE_CONFIG = {
        'host': os.getenv('CHROMA_HOST', 'localhost'),
        'port': int(os.getenv('CHROMA_PORT', 8000)),
        'persist_directory': os.getenv('VECTOR_STORE_PATH', '/data/vector_stores')
    }

    # Performance
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', 4))
    QUERY_TIMEOUT = int(os.getenv('QUERY_TIMEOUT', 30))

    # Security
    SECRET_KEY = os.getenv('SECRET_KEY')
    API_KEY_REQUIRED = os.getenv('API_KEY_REQUIRED', 'true').lower() == 'true'

    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',')

    # Monitoring
    SENTRY_DSN = os.getenv('SENTRY_DSN')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
```

## Performance Optimization

### 1. Caching Strategy

```python
# app/middleware/caching.py
import redis
from functools import wraps
import json
import hashlib

redis_client = redis.Redis.from_url(os.getenv('REDIS_URL'))

def cache_query(ttl=3600):
    """Cache query results with TTL"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"query:{hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()}"

            # Try to get from cache
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            redis_client.setex(cache_key, ttl, json.dumps(result, default=str))

            return result
        return wrapper
    return decorator
```

### 2. Load Balancing

```nginx
# nginx.conf
upstream saas_intel_backend {
    least_conn;
    server app1:8000 weight=3;
    server app2:8000 weight=3;
    server app3:8000 weight=2;
    keepalive 64;
}

server {
    listen 80;
    server_name api.saasgrowthdispatch.com;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    location / {
        limit_req zone=api burst=20 nodelay;

        proxy_pass http://saas_intel_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 5s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;

        # Buffering
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }
}
```

## Monitoring and Logging

### 1. Application Monitoring

```python
# app/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
query_counter = Counter('queries_total', 'Total queries', ['source', 'status'])
query_duration = Histogram('query_duration_seconds', 'Query duration')
active_connections = Gauge('active_connections', 'Active connections')

class MetricsMiddleware:
    def __init__(self):
        self.start_time = time.time()

    async def __call__(self, request, call_next):
        start_time = time.time()

        try:
            response = await call_next(request)
            status = 'success'
        except Exception as e:
            status = 'error'
            raise
        finally:
            duration = time.time() - start_time
            query_duration.observe(duration)
            query_counter.labels(source='api', status=status).inc()

        return response
```

### 2. Structured Logging

```python
# app/config/logging.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id

        if hasattr(record, 'query_id'):
            log_entry['query_id'] = record.query_id

        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_entry)

def setup_logging():
    """Configure structured logging"""
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
```

### 3. Health Checks

```python
# app/health.py
from fastapi import APIRouter
from app.core.rag_engine import SaaSMarketIntelligenceRAG
from app.core.vector_store import VectorStoreManager
import time

router = APIRouter()

@router.get("/health")
async def health_check():
    """Comprehensive health check"""

    health_status = {
        'status': 'healthy',
        'timestamp': time.time(),
        'services': {},
        'metrics': {}
    }

    try:
        # Check RAG engine
        rag_status = await check_rag_engine()
        health_status['services']['rag_engine'] = rag_status

        # Check vector store
        vector_status = await check_vector_store()
        health_status['services']['vector_store'] = vector_status

        # Check external APIs
        api_status = await check_external_apis()
        health_status['services']['external_apis'] = api_status

        # Overall status
        if any(service['status'] != 'healthy' for service in health_status['services'].values()):
            health_status['status'] = 'degraded'

    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['error'] = str(e)

    return health_status

async def check_rag_engine():
    """Check RAG engine health"""
    try:
        # Quick system status check
        rag = SaaSMarketIntelligenceRAG()
        status = await rag.get_system_status()
        return {'status': 'healthy', 'details': status}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}
```

## Security Configuration

### 1. API Security

```python
# app/middleware/security.py
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
import os

security = HTTPBearer()

async def verify_api_key(token: str = Depends(security)):
    """Verify API key authentication"""

    if not os.getenv('API_KEY_REQUIRED', 'true').lower() == 'true':
        return True

    valid_keys = os.getenv('VALID_API_KEYS', '').split(',')

    if token.credentials not in valid_keys:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    return token.credentials

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.state.limiter = limiter
@app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

### 2. Data Encryption

```python
# app/security/encryption.py
from cryptography.fernet import Fernet
import os
import base64

class DataEncryption:
    def __init__(self):
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            key = Fernet.generate_key()
        self.cipher = Fernet(key)

    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
```

## Disaster Recovery

### 1. Backup Strategy

```bash
#!/bin/bash
# scripts/backup.sh

# Backup vector stores
docker exec chromadb tar -czf /tmp/chroma_backup_$(date +%Y%m%d_%H%M%S).tar.gz /chroma/chroma

# Backup database
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Upload to S3
aws s3 cp backup_*.sql s3://your-backup-bucket/database/
aws s3 cp /tmp/chroma_backup_*.tar.gz s3://your-backup-bucket/vector_stores/

# Cleanup old backups (keep last 30 days)
find /backups -name "*.sql" -mtime +30 -delete
find /tmp -name "chroma_backup_*.tar.gz" -mtime +30 -delete
```

### 2. Recovery Procedures

```bash
#!/bin/bash
# scripts/restore.sh

# Download latest backup
aws s3 cp s3://your-backup-bucket/database/backup_latest.sql ./
aws s3 cp s3://your-backup-bucket/vector_stores/chroma_backup_latest.tar.gz ./

# Restore database
psql $DATABASE_URL < backup_latest.sql

# Restore vector stores
docker exec chromadb tar -xzf /tmp/chroma_backup_latest.tar.gz -C /
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   ```bash
   # Check memory usage
   docker stats

   # Optimize vector store
   python -c "from app.core.vector_store import VectorStoreManager; await VectorStoreManager().optimize_all_indices()"
   ```

2. **Slow Query Performance**
   ```bash
   # Check query metrics
   curl http://localhost:8000/metrics | grep query_duration

   # Clear cache
   redis-cli FLUSHALL
   ```

3. **API Timeouts**
   ```python
   # Check external API status
   curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
   ```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with debugging
python -m debugpy --listen 0.0.0.0:5678 --wait-for-client run.py
```

---

This deployment guide provides comprehensive coverage of deploying the agentic RAG system across different environments and cloud providers. Choose the deployment option that best fits your infrastructure needs and scale requirements.
