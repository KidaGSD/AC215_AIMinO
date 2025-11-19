# Local Testing Guide

This guide explains how to test the frontend-backend connection of the Napari Agent API locally.

## Prerequisites

1. **Install Dependencies**
   ```bash
   conda env create -f environment.yml
   conda activate aimino
   ```

2. **Set Environment Variables**
   You need to set LLM API keys (depending on which model you use):
   ```bash
   export GEMINI_API_KEY=your_gemini_api_key_here
   # or
   export OPENAI_API_KEY=your_openai_api_key_here
   # or
   export HF_TOKEN=your_huggingface_token_here
   ```

3. **Set PYTHONPATH**
   Run from the project root directory, or set:
   ```bash
   export PYTHONPATH=/path/to/AC215_AIMinO:$PYTHONPATH
   ```

## Testing Steps

### Method 1: Using Test Script (Recommended)

#### Step 1: Start API Server

In one terminal window:
```bash
cd /path/to/AC215_AIMinO
conda activate aimino
python -m src.server.start_api
```

You should see output similar to:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

#### Step 2: Run Test Script

In another terminal window:
```bash
cd /path/to/AC215_AIMinO
conda activate aimino
python -m src.server.test_api
```

Or test with custom input:
```bash
python -m src.server.test_api http://localhost:8000 "center on 200,300"
```

### Method 2: Using curl to Test

#### Test Health Check
```bash
curl http://localhost:8000/health
```

#### Test /invoke Endpoint
```bash
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "show nuclei layer",
    "context": null
  }'
```

### Method 3: Full End-to-End Test (Napari + API)

#### Step 1: Start API Server
```bash
python -m src.server.start_api
```

#### Step 2: Start Napari Client
In another terminal:
```bash
python -m napari_app.main
```

Enter commands in the dock on the right side of the Napari window, for example:
- `show nuclei layer`
- `center on 200,300`
- `hide cells layer`

## Troubleshooting

### Issue 1: Cannot Connect to Server
**Error**: `ConnectionError: Unable to connect to API server`

**Solution**:
- Ensure the API server is running
- Check if port 8000 is occupied
- Verify that the `AIMINO_API_URL` environment variable points to the correct address

### Issue 2: API Server Fails to Start
**Error**: `ModuleNotFoundError` or import errors

**Solution**:
- Ensure the conda environment is activated: `conda activate aimino`
- Ensure you're running from the project root directory
- Check PYTHONPATH settings

### Issue 3: LLM API Key Error
**Error**: `403 Forbidden` or authentication errors

**Solution**:
- Check if environment variables are set correctly: `echo $GEMINI_API_KEY`
- Verify the API key is valid
- Check detailed error messages in server logs

### Issue 4: Request Timeout
**Error**: `TimeoutError: API request timeout`

**Solution**:
- LLM responses may take a long time, which is normal
- You can increase the timeout (modify `timeout=60` in `client_agent.py`)
- Check network connection

## Verification Checklist

- [ ] API server starts successfully (see "Application startup complete")
- [ ] Health check returns `{"status": "ok", "runner_initialized": true}`
- [ ] `/invoke` endpoint returns a valid `final_commands` list
- [ ] Napari client can connect to the API server
- [ ] Commands can be executed successfully in Napari

## Next Steps

After testing passes, you can:
1. Deploy the API server to a remote server
2. Update the `AIMINO_API_URL` environment variable in the client
3. Configure CORS settings for production environment (in `api.py`)
