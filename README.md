# AIMinO (Napari + Agentic Control)

AIMinO is an intelligent image analysis plugin for Napari that enables natural language command control of the Napari viewer.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Server (K8s/Docker)                       │
│  /api/v1/invoke → LeadManager → Workers → Command JSON      │
│                                                              │
│  - Parses user intent using Gemini LLM                      │
│  - Generates executable commands                             │
│  - Does NOT access data or execute computations              │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    Returns: [{"action": "special_show_density", ...}]
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Napari Client (Local)                     │
│  handlers/special_analysis/ → Execute commands              │
│                                                              │
│  - Accesses local TIFF/h5ad files                           │
│  - Executes all computations (density, mask, neighborhood)  │
│  - Updates Napari viewer with results                       │
└─────────────────────────────────────────────────────────────┘
```

**Key insight**: Server agents only generate commands; all data access and computation happens on the Napari client locally.

## Prerequisites and Setup Instructions

### System Requirements

- **Python**: >= 3.10
- **Docker**: >= 20.10
- **Napari**: >= 0.4.0

### Installation

1. **Install Frontend Plugin**
   ```bash
   pip install aimino
   ```

2. **Configure Backend**
   ```bash
   cp .env.example .env
   # Edit .env and add: GEMINI_API_KEY=your_api_key_here
   ```

3. **Start Backend Service**
   ```bash
   DOCKER_BUILDKIT=1 docker build -t aimino-api:dev -f src/api_service/Dockerfile .
   docker run --rm -d -p 8000:8000 --name aimino-api --env-file .env aimino-api:dev
   ```

4. **Start Frontend**
   ```bash
   napari
   # In Napari menu: Plugins → AIMinO ChatBox
   ```

### Data Storage

- Default location: `~/AIMINO_DATA`
- Override: set `AIMINO_DATA_ROOT=/path/to/data` in `.env`
- Register existing files: POST to `/api/v1/datasets/register` with dataset info

## Deployment Instructions

### Docker Deployment

The backend service runs in Docker. Build and run as shown in setup instructions above.

### Kubernetes Deployment

1. **Prerequisites**
   - Kubernetes cluster access (GKE or other)
   - `kubectl` configured
   - GitHub Secrets: `GCP_SA_KEY` (for GKE) or `KUBECONFIG`

2. **Create Secrets**
   ```bash
   kubectl create secret generic aimino-secrets \
     --from-literal=gemini-api-key=YOUR_API_KEY
   ```

3. **Deploy**
   ```bash
   kubectl apply -f k8s/deployment.yaml
   kubectl rollout status deployment/aimino-api
   ```

4. **Automatic Deployment**
   - CI/CD pipeline automatically deploys to Kubernetes when code is pushed to `main` branch
   - Requires `GCP_SA_KEY` in GitHub Secrets
   - See `.github/workflows/ci-cd.yml` for details

## Usage Details and Examples

### Supported Commands

**Context Management:**
- `set_dataset` - Switch active dataset
- `set_marker` - Switch active marker column
- `list_datasets` - Show available datasets
- `get_dataset_info` - Show current dataset details

**Analysis:**
- `special_load_marker_data` - Load TIFF + h5ad pair
- `special_show_mask` - Display binary mask
- `special_show_density` - Show density heatmap
- `special_compute_neighborhood` - Tumor microenvironment analysis

**Viewer:**
- Layer visibility (show/hide/toggle)
- Camera control (zoom, center, angles)
- Screenshot and export

### Example Usage

1. Load dataset: "Load the marker data for dataset X"
2. Show analysis: "Show density for marker Y"
3. Switch context: "Set marker to CD8"
4. View layers: "Show all layers"

### Environment Variables

- `AIMINO_DATA_ROOT` - Data storage path (default: `~/AIMINO_DATA`)
- `AIMINO_AUTLOAD_MAX_BYTES` - Auto-load size limit (default: 500MB)
- `AIMINO_DISABLE_AUTOLOAD` - Disable auto-load (0/1)
- `AIMINO_SKIP_16K_CHECK` - Skip dimension check (0/1)

## Known Issues and Limitations

1. **Large Images (>16k pixels)**: May cause Napari to freeze. Use multiscale formats (OME-Zarr or pyramidal OME-TIFF).

2. **Large Files**: Auto-load is skipped when file size exceeds `AIMINO_AUTLOAD_MAX_BYTES`. Adjust threshold or use multiscale data.

3. **Performance**: Heavy computations run on main thread. For very large datasets, precompute or convert to multiscale format.

4. **Recommendations**: 
   - Convert TIFF to multiscale OME-Zarr for best performance
   - Keep auto-load threshold conservative (500MB default)
   - Use "Show current marker layers" button for manual loading
