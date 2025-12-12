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

### Data Storage
- AIMinO stores uploaded TIFF/H5AD datasets and derived artifacts under `~/AIMINO_DATA` by default.
- Override the location by setting `AIMINO_DATA_ROOT=/path/to/data` in your shell or `.env`.
- To register existing files with the backend (remote workflows), POST to `/api/v1/datasets/register` with `{"image_path": "...", "h5ad_path": "...", "dataset_id": "...", "copy_files": false}`; the manifest is created server-side.


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

## Running Guide (env toggles & safety)
- `.env` defaults:
  - `AIMINO_DATA_ROOT=~/AIMINO_DATA` (where manifests/caches are stored)
  - `AIMINO_AUTLOAD_MAX_BYTES=500000000` (auto-load guard; set `0` to disable auto-load entirely)
  - `AIMINO_DISABLE_AUTOLOAD=0` (set `1` to disable all auto-load paths; use "Show current marker layers" to load manually)
  - `AIMINO_SKIP_16K_CHECK=0` (set `1` to skip 16k pixel dimension check; may cause slow loading or freezing)
  - `AIMINO_AUTO_DOWNSAMPLE=0` (auto-downsample factor: 0=auto-calculate to fit 16k, 2=2x, 4=4x; recommended for large images)
- Large image safety:
  - If TIFF dimensions exceed 16k per axis or size exceeds `AIMINO_AUTLOAD_MAX_BYTES`, auto-load is skipped with a status message.
  - For best performance, convert to multiscale (OME-Zarr or pyramidal OME-TIFF) and update `manifest.json` `image_path` to the multiscale asset.
- Manual load: use the “Show current marker layers” button to load mask/density on demand (still respects size/dimension checks).

---

## Kubernetes Deployment with Pulumi

You can deploy the AIMinO API to a GKE cluster using the Pulumi projects copied from the cheese-app deployment. All Pulumi commands are intended to run **inside** the dedicated deployment Docker container.

### Layout

- `pulumi_deployment/src/deployment`: deployment utilities (Dockerfile, docker-shell, shared config).
- `pulumi_deployment/src/deployment/deploy_images`: builds and pushes the `aimino-api-service` image to Google Artifact Registry.
- `pulumi_deployment/src/deployment/deploy_k8s`: creates network + GKE cluster + namespace, and deploys the AIMinO API + load balancer.

### Prerequisites

- A GCP project and billing enabled.
- Docker installed (and access to `/var/run/docker.sock`).
- `gcloud` CLI authenticated to your project.
- Pulumi CLI installed and logged in (in the deployment container image).
- Artifact Registry repository `aimino-repository` created in your chosen region.
- Two GCP service accounts (names are examples; adjust to match your project):
  - `deployment@<YOUR_PROJECT>.iam.gserviceaccount.com` (for GKE nodes).
  - `gcp-service@<YOUR_PROJECT>.iam.gserviceaccount.com` (for Workload Identity).

### 1. Start the deployment container (host machine)

From the AIMinO repo root on your host (Linux/macOS or WSL/Git Bash on Windows):

```bash
cd pulumi_deployment/src/deployment
bash docker-shell.sh
```

This builds (if needed) and starts the `cheese-app-deployment` container, mounting the AIMinO repo at `/AC215_AIMinO` and the deployment code at `/app`, then drops you into a shell inside the container.

All subsequent Pulumi commands in the following steps assume you are **inside** this container shell.

### 2. Configure Pulumi projects (inside container)

Edit the following files inside the container (paths are relative to `/app`):

- `/app/deploy_images/Pulumi.dev.yaml`
  - Set `gcp:project` to your GCP project ID.
- `/app/deploy_k8s/Pulumi.dev.yaml`
  - Set `gcp:project` to your GCP project ID.
  - Set `security:gcp_service_account_email` to your node SA (e.g. `deployment@<YOUR_PROJECT>.iam.gserviceaccount.com`).
  - Set `security:gcp_ksa_service_account_email` to your Workload Identity SA (e.g. `gcp-service@<YOUR_PROJECT>.iam.gserviceaccount.com`).
- `/app/deploy_k8s/setup_containers.py`
  - Update the `StackReference` to point to your Pulumi org/project/stack, for example:
    - `images_stack = pulumi.StackReference("your-org/deploy-images/dev")`

You can edit these either on the host (the files are the same ones under `pulumi_deployment/src/deployment/...`) or from inside the container using a terminal editor.

### 3. Build and push the AIMinO API image (inside container)

```bash
cd /app/deploy_images
# Select or create the dev stack
pulumi stack select dev || pulumi stack init dev

# Set region for builds (must match your Artifact Registry)
export GCP_REGION=us-central1

pulumi up
```

This builds the AIMinO API image from the `/AC215_AIMinO` source mounted into the container and pushes it to Artifact Registry, exporting tags used by the `deploy_k8s` stack.

### 4. Create GKE cluster and deploy AIMinO (inside container)

```bash
cd /app/deploy_k8s
pulumi stack select dev || pulumi stack init dev
pulumi up
```

This creates the network, GKE cluster, namespace, Workload Identity bindings, and the AIMinO API `Deployment` + `Service` + ingress. It also runs `gcloud container clusters get-credentials ...` so that `kubectl` talks to the new cluster.

### 5. Configure Gemini API key in the cluster

The deployment expects a Kubernetes `Secret` containing your Gemini API key:

- Namespace: `aimino-app-namespace`
- Secret name: `aimino-gemini-secret`
- Key: `GEMINI_API_KEY`

Create it after the cluster is ready (can be run from inside the container or on any machine with `kubectl` configured for the cluster):

```bash
kubectl create secret generic aimino-gemini-secret \
  --from-literal=GEMINI_API_KEY=<YOUR_GEMINI_API_KEY> \
  -n aimino-app-namespace
```

After this, the AIMinO API pods in the cluster will have `GEMINI_API_KEY` injected from the secret and will be reachable via the load balancer URL printed in the `deploy_k8s` Pulumi outputs.

---

## Supported Commands

### Context Management
- `set_dataset` - Switch active dataset context
- `set_marker` - Switch active marker column
- `list_datasets` - Show available datasets
- `get_dataset_info` - Show current dataset details
- `clear_processed_cache` - Free disk space

### Analysis Commands
- `special_load_marker_data` - Load TIFF + h5ad pair
- `special_show_mask` - Display binary mask for marker
- `special_show_density` - Show density heatmap
- `special_update_density` - Recompute density with parameters (sigma, colormap)
- `special_compute_neighborhood` - Tumor microenvironment analysis

### Viewer Commands
- Layer visibility (show/hide/toggle)
- Camera control (zoom, center, angles)
- Screenshot and export

## Recent Updates (Data & UI)
- **Context commands**: Added `set_dataset`, `set_marker`, `list_datasets`, `get_dataset_info`, `clear_processed_cache` for session management.
- **Improved LeadManager**: Better error messages when dataset_id or marker is missing; shows available options.
- **Updated handbooks**: All workers now document `force_recompute`, `sigma`, `radius` parameters with defaults.
- Added `DataStore`-based ingest with manifest (auto dataset_id, link-by-default, hash/mtime checks).
- Napari Data Import Dock auto-detects marker columns from h5ad (bool / `*_positive`) and saves to manifest; will auto-load mask/density when safe.
- Added safety guard for large data: auto-load is skipped if file size exceeds `AIMINO_AUTLOAD_MAX_BYTES` (default 500MB) or image dimensions exceed 16k; status panel shows guidance.
- "Show current marker layers" now reuses the same guard; it warns before forcing a large load.
- New cache cleanup and marker-layer highlight buttons; remote register option uses `/api/v1/datasets/register`.
- Added `AIMINO_DISABLE_AUTOLOAD=1` toggle: disables all auto-load paths (dataset selection, marker change, ingest). Use "Show current marker layers" to load manually.
- Agent/Backend updates: added data_ingest/mask_density/neighborhood/context workers and validation in LeadManager; `/api/v1/datasets/register` endpoint; handbooks/task_parser updated.
- Core handlers now resolve via DataStore; command models include dataset_id/sigma/radius/force options.
- Tests: added `tests/test_data_store.py`, `tests/test_pipeline_e2e.py`, and `tests/test_context_commands.py`.

## Known Issues & Mitigations
- **Large images (>16k pixels per axis)**: Napari/VisPy will downsample and may freeze. Use a downsampled/pyramidal copy (OME-Zarr or pyramidal OME-TIFF) for visualization; point `manifest.json` `image_path` to the multiscale asset.
- **Huge files**: auto-load skips when size > `AIMINO_AUTLOAD_MAX_BYTES`. Adjust via `.env` or shell. Forcing load can still be slow; prefer multiscale data.
- **Backend threads for heavy loads**: current Napari handlers run on the main thread. For very large data, precompute/crop or convert to multiscale. (Planned: background load + progress UI.)

## Recommendations for Large Datasets
1) Convert raw TIFF to multiscale (preferred):
   - OME-Zarr pyramid: write multiscale and set `manifest["image_path"]` to the `.zarr` directory.
   - Pyramidal OME-TIFF (SubIFD levels).
2) Keep auto-load threshold conservative (`AIMINO_AUTLOAD_MAX_BYTES=500000000` in `.env`).
3) If you must force-load: use “Show current marker layers” but expect slower performance; consider cropping/ROI instead of full-frame.

### Possible downsample workaround (not tested)
Use a lightweight preview TIFF for napari display, keep the original for computation:
```bash
conda run -n aimino python - <<'PY'
import tifffile
src = "LSP16767.ome.tif"          # path to original
dst = "LSP16767_downsample4x.tif"
with tifffile.TiffFile(src) as tf:
    arr = tf.asarray()
arr_ds = arr[::4, ::4]            # adjust slicing if multichannel
tifffile.imwrite(dst, arr_ds, bigtiff=True)
print("saved:", dst, arr_ds.shape)
PY
```
Then edit `~/AIMINO_DATA/<dataset_id>/manifest.json` to point `image_path` to the downsampled file. For best results, create a multiscale OME-Zarr or pyramidal OME-TIFF and point the manifest to that asset.
