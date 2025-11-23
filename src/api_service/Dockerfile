FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install backend dependencies
COPY src/api_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Install shared command schema for agents
COPY aimino_frontend/aimino_core /app/aimino_frontend/aimino_core
WORKDIR /app/aimino_frontend/aimino_core
RUN pip install --no-cache-dir .
WORKDIR /app

# Copy API service code
COPY src/api_service /app/src/api_service

EXPOSE 8000

COPY src/api_service/docker-entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

USER 1000

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
