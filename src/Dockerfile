FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1


RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential g++ curl git \
    libbz2-dev zlib1g-dev libssl-dev \
    libc6-dev linux-libc-dev \
    && rm -rf /var/lib/apt/lists/*


RUN python -V && pip install -U pip setuptools wheel


ENV CFLAGS="-D_GNU_SOURCE"
RUN pip install -f https://downloads.openmicroscopy.org/zeroc-ice/3.6/zeroc-ice-cp310/ zeroc-ice==3.6.5
RUN pip install omero-py


# napari removed - users will install it locally


RUN curl -fsSL https://ollama.com/install.sh | sh


ENV PATH="/usr/local/bin:${PATH}"


RUN pip install \
    "pydantic>=2" requests numpy pandas scikit-learn \
    torch \
    langchain langchain-openai \
    openai \
    huggingface_hub \
    flask flask-cors


RUN groupadd -r appuser && useradd -r -g appuser -m appuser


RUN mkdir -p /app && chown -R appuser:appuser /app

ENV OMERO_HOST=omeroserver \
    OMERO_PORT=4064 \
    PYTHONUNBUFFERED=1 \
    NUMBA_CACHE_DIR=/tmp/numba_cache


USER appuser

EXPOSE 8000


HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1


COPY container_startup.sh /usr/local/bin/container_startup.sh

CMD ["bash", "/usr/local/bin/container_startup.sh"]