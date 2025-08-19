# 09_Deployment_Package/Dockerfile
# Production-grade Docker container for Adaptive Mind Framework
# Optimized for Azure Container Registry and enterprise deployment

# Use official Python slim image for security and size optimization
FROM python:3.11-slim-bullseye

# Metadata for enterprise tracking
LABEL maintainer="Adaptive Mind Framework Team"
LABEL version="2.3.0"
LABEL description="Enterprise AI Resilience Framework - Production Container"
LABEL org.opencontainers.image.title="Adaptive Mind Framework"
LABEL org.opencontainers.image.description="Enterprise-grade AI provider resilience and optimization"
LABEL org.opencontainers.image.version="2.3.0"
LABEL org.opencontainers.image.created="2025-08-21"
LABEL org.opencontainers.image.documentation="https://docs.adaptivemind.ai"
LABEL org.opencontainers.image.source="https://github.com/adaptivemind/framework"

# Create non-root user for security
RUN groupadd -r adaptivemind && useradd -r -g adaptivemind -u 1001 adaptivemind

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_HOME=/app \
    WORKERS=4 \
    MAX_WORKERS=8 \
    TIMEOUT=120 \
    KEEPALIVE=2 \
    MAX_REQUESTS=1000 \
    MAX_REQUESTS_JITTER=100

# Install system dependencies with security updates
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    postgresql-client \
    supervisor \
    nginx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Create application directory and set ownership
RUN mkdir -p $APP_HOME && chown -R adaptivemind:adaptivemind $APP_HOME
WORKDIR $APP_HOME

# Copy requirements first for better Docker layer caching
COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy application code
COPY --chown=adaptivemind:adaptivemind . .

# Create necessary directories
RUN mkdir -p logs data config metrics \
    && chown -R adaptivemind:adaptivemind logs data config metrics

# Configure nginx for reverse proxy
COPY 09_Deployment_Package/nginx.conf /etc/nginx/nginx.conf
COPY 09_Deployment_Package/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy production configuration files
COPY --chown=adaptivemind:adaptivemind 09_Deployment_Package/dual_mode_config.yml config/
COPY --chown=adaptivemind:adaptivemind 09_Deployment_Package/prometheus_config.yml config/

# Install Prometheus Node Exporter for metrics
RUN curl -L https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz \
    | tar xzf - --strip-components=1 -C /usr/local/bin node_exporter-1.6.1.linux-amd64/node_exporter \
    && chmod +x /usr/local/bin/node_exporter

# Set up health check script
COPY --chown=adaptivemind:adaptivemind 09_Deployment_Package/healthcheck.py ./
RUN chmod +x healthcheck.py

# Create startup script
RUN cat > start.sh << 'EOF'
#!/bin/bash
set -e

# Initialize logging
mkdir -p /app/logs
touch /app/logs/app.log /app/logs/nginx.log /app/logs/metrics.log

# Wait for database if DATABASE_URL is provided
if [ ! -z "$DATABASE_URL" ]; then
    echo "Waiting for database connection..."
    python -c "
import psycopg2
import os
import time
import sys
db_url = os.environ.get('DATABASE_URL')
if db_url:
    for i in range(30):
        try:
            conn = psycopg2.connect(db_url)
            conn.close()
            print('Database connection successful')
            break
        except psycopg2.OperationalError:
            print(f'Database connection attempt {i+1}/30 failed, retrying...')
            time.sleep(2)
    else:
        print('Failed to connect to database after 30 attempts')
        sys.exit(1)
"
fi

# Run database migrations if needed
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    python -c "
import os
import subprocess
if os.path.exists('05_Database_Layer/migrations'):
    subprocess.run(['python', '-m', 'alembic', 'upgrade', 'head'], check=True)
"
fi

# Start supervisor to manage all processes
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
EOF

RUN chmod +x start.sh && chown adaptivemind:adaptivemind start.sh

# Set up health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python healthcheck.py || exit 1

# Expose ports
EXPOSE 8000 9090 9100

# Switch to non-root user
USER adaptivemind

# Set the startup command
CMD ["./start.sh"]

# Production environment variables (can be overridden)
ENV ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    METRICS_ENABLED=true \
    PROMETHEUS_PORT=9090 \
    NODE_EXPORTER_PORT=9100 \
    HEALTH_CHECK_INTERVAL=30