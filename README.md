# AIMinO (Napari + Agentic Control)

AIMinO is an intelligent image analysis plugin for Napari that enables natural language command control of the Napari viewer.

## 🚀 Quick Start

### System Requirements

- **Python**: >= 3.10
- **Docker**: >= 20.10
- **Napari**: >= 0.4.0

### 1. Install Frontend Plugin

```bash
# Install from PyPI (recommended)
pip install aimino


### 2. Configure Backend

```bash
# Create .env file in project root
cd AC215_AIMinO
cp .env.example .env

# Edit .env and add your Google Gemini API Key
# GEMINI_API_KEY=your_api_key_here
```

**Get API Key**:
1. Visit https://ai.google.dev/ to create an API key
2. Enable "Generative Language API" in Google Cloud Console
3. Set up billing account (may be required even for free tier)

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

### Usage Examples

Enter commands in the ChatBox:
- `show layers` - Display all layers
- `zoom in` / `zoom out` - Zoom view
- `center on 200,300` - Center on specified coordinates

### Common Issues

**Backend Connection Failed**
```bash
docker ps | grep aimino-api  # Check if container is running
docker logs aimino-api       # View logs
```

**API Quota Error**
- Check if API key is correct
- Ensure "Generative Language API" is enabled
- Set up billing account

**Plugin Not Showing**
- Ensure plugin is installed in the same Python environment as Napari
- Fully restart Napari
- Check: `pip list | grep aimino`

### Stop Services

```bash
docker stop aimino-api
```

---




