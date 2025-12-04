FROM python:3.12-slim-bookworm

ARG DEBIAN_PACKAGES="build-essential curl"
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/home/app/.venv
ENV PATH="/home/app/.venv/bin:${PATH}"
# Make both the application sources and /app root importable so that
# `import aimino_core` resolves to /app/aimino_core/__init__.py
ENV PYTHONPATH="/app/src:/app"

RUN set -ex; \
    apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends $DEBIAN_PACKAGES && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip && \
    pip install uv && \
    useradd -ms /bin/bash app -d /home/app -u 1000 && \
    mkdir -p /app && chown app:app /app

USER app
WORKDIR /app

# Copy dependency metadata first for caching
COPY --chown=app:app src/api_service/pyproject.toml src/api_service/uv.lock ./

# Install deps (cheese-style)
RUN uv sync --frozen

# Copy api_service contents (preserve src layout)
COPY --chown=app:app src/api_service /app/src/api_service

# Copy entrypoint to a path unaffected by /app mounts
COPY --chown=app:app src/api_service/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Copy shared core (no installation needed, PYTHONPATH already includes /app/aimino_core)
COPY --chown=app:app aimino_frontend/src/aimino_frontend/aimino_core /app/aimino_core

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
