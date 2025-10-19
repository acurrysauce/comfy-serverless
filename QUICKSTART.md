# Quick Start Guide

Get ComfyUI running on RunPod serverless in 15 minutes!

## Prerequisites

- Docker installed
- RunPod account (sign up at https://runpod.io)
- Basic familiarity with terminal/command line

## Step-by-Step

### 1. Build the Docker Image (5 min)

```bash
cd comfy-serverless
./scripts/build.sh
```

Wait for the build to complete.

### 2. Push to Docker Hub (3 min)

```bash
# Login to Docker Hub
docker login

# Push (replace 'yourusername')
./scripts/push.sh yourusername/comfyui-serverless latest
```

### 3. Deploy to RunPod (5 min)

1. Go to https://www.runpod.io/console/serverless
2. Click **"+ New Endpoint"**
3. Fill in:
   - **Name**: `ComfyUI Serverless`
   - **Container Image**: `yourusername/comfyui-serverless:latest`
   - **Container Disk**: `10 GB`
   - **GPU Types**: Check `RTX 4090` (or cheaper option)
   - **Min Workers**: `0`
   - **Max Workers**: `1`
   - **Idle Timeout**: `30`
4. Click **"Deploy"**

### 4. Get Your Credentials

From the endpoint page:
- Copy your **Endpoint ID** (e.g., `abc123def456`)

From https://www.runpod.io/console/user/settings:
- Copy your **API Key**

### 5. Setup Local ComfyUI (2 min)

```bash
cd local-setup
./setup-local-comfyui.sh ~/ComfyUI-local
```

### 6. Test It!

```bash
# Set credentials
export RUNPOD_API_KEY="your-api-key"
export RUNPOD_ENDPOINT_ID="your-endpoint-id"

# Start ComfyUI locally
cd ~/ComfyUI-local
source venv/bin/activate
python main.py
```

Open http://localhost:8188 in your browser

1. Load a default workflow (or create one)
2. Click "Save (API Format)" - save as `workflow_api.json`
3. Send to RunPod:

```bash
cd ~/comfy-serverless/local-setup
python send-to-runpod.py ~/ComfyUI-local/workflow_api.json
```

Your rendered images will appear in `./outputs/`!

## What's Next?

- Add models (see README.md "Network Storage" section)
- Install custom nodes in the Docker image
- Create more complex workflows

## Need Help?

Check the full README.md for detailed documentation and troubleshooting.
