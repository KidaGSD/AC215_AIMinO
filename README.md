# AIMinO (Napari + Agentic Control)

AIMinO is an intelligent image analysis plugin for Napari that enables natural language command control of the Napari viewer.

## Quick Start

### System Requirements

- **Python**: >= 3.10
- **Docker**: >= 20.10
- **Napari**: >= 0.4.0

### 1. Install Frontend Plugin

```bash
# Install from PyPI 
pip install aimino
```


### 2. Configure Backend

```bash
# Create .env file in project root
cp .env.example .env

# Edit .env and add your Google Gemini API Key
# GEMINI_API_KEY=your_api_key_here
```


### 3. Start Backend Service

```bash
# Build and start Docker container
DOCKER_BUILDKIT=1 docker build -t aimino-api:dev -f src/api_service/Dockerfile .
docker run --rm -d -p 8000:8000 --name aimino-api --env-file .env aimino-api:dev


```

### 4. Start Frontend

```bash
# Launch Napari
napari

# In Napari menu: Plugins → AIMinO ChatBox
```



---




