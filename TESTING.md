# Local Testing Guide

This guide explains how to test the frontend-backend connection of the Napari Agent API locally.

## Prerequisites

**Set Environment Variables**
   You need to set LLM API keys (depending on which model you use):
   ```bash
   export GEMINI_API_KEY=your_gemini_api_key_here
   # or
   export OPENAI_API_KEY=your_openai_api_key_here
   # or
   export HF_TOKEN=your_huggingface_token_here
   ```


## Testing Steps

#### Step 1: Start API Server
```bash
python -m src.server.start_api
```

#### Step 2: Start Napari Client
In another terminal:
```bash
python -m napari_app.main
```


