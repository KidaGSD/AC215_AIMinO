# Shared Storage Deployment Plan (K8s Backend + Local Napari)

Goal: make server-side agents in K8s read data from a shared, server-visible path while local Napari can drive analysis (and optionally view data).

## 1) Prepare Shared Storage
- Provision a shared volume (PVC/NFS/object storage) and mount into the backend pod, e.g. `/data/aimino`.
- Place TIFF/h5ad files into that path (outside of code):
  - CI/CD: job uploads artifacts to the mounted volume.
  - Manual: `rsync`/`scp` to the host or storage, or `kubectl cp <local> <pod>:/data/aimino/`.
  - Ensure the container sees the files at `/data/aimino/...`.

## 2) Configure the Backend
- Set env in K8s or `.env`: `AIMINO_DATA_ROOT=/data/aimino`.
- Register datasets with server-visible paths (no copy):
  ```bash
  curl -X POST http://<api>/api/v1/datasets/register \
    -H "Content-Type: application/json" \
    -d '{
      "image_path": "/data/aimino/LSP16767.ome.tif",
      "h5ad_path": "/data/aimino/LSP16767_10232025.h5ad",
      "dataset_id": "LSP16767",
      "copy_files": false
    }'
  ```
- DataStore writes `manifest.json` under `AIMINO_DATA_ROOT/<dataset_id>/` pointing to the shared paths.

## 3) Local Napari Usage
- If you only trigger backend analysis, Napari just sends commands; it does not need to read the files.
- If you need visualization, ensure Napari can access the same shared path (mount the same NFS/SMB locally), or provide a downsampled/multiscale copy for preview.

## 4) Avoid Freezes/16k Limits
- Provide a multiscale/downsampled asset in shared storage and set `manifest.image_path` to that asset; keep the original for computation if needed.
- Env toggles:
  - `AIMINO_AUTLOAD_MAX_BYTES` (default 500MB) — auto-load guard; set `0` to disable auto-load.
  - `AIMINO_DISABLE_AUTOLOAD=1` — disable all auto-load paths; use “Show current marker layers” to load manually.
- If TIFF dimensions >16k/axis, Napari will downsample; prefer multiscale OME-Zarr or pyramidal OME-TIFF.

## 5) Optional: CI/CD Sync Pattern
- Build step uploads TIFF/h5ad (and multiscale preview) to the shared volume.
- Deploy step sets `AIMINO_DATA_ROOT` to the mounted path and calls `/datasets/register` with server-visible paths and `copy_files=false`.
- For front-end preview, publish a downsampled/multiscale copy and update manifest accordingly.
