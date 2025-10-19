# ComfyUI RunPod Serverless Setup

Run ComfyUI locally for the UI/workflow creation, but execute rendering on RunPod serverless GPUs.

## Overview

This setup allows you to:
- Run ComfyUI's web interface on your local machine (no GPU needed)
- Create and design workflows locally
- Send workflows to RunPod serverless for rendering
- Download the results back to your local machine

## Directory Structure

```
comfy-serverless/
├── docker/                    # Docker image for RunPod serverless
│   ├── Dockerfile
│   ├── handler.py            # RunPod serverless handler
│   └── utils.py              # Helper functions
├── local-setup/              # Local ComfyUI setup
│   ├── setup-local-comfyui.sh
│   └── send-to-runpod.py     # Script to send workflows to RunPod
├── scripts/                  # Build and deployment scripts
│   ├── build.sh
│   ├── push.sh
│   └── test-local.sh
└── README.md                 # This file
```

## Setup Guide

### Part 1: Deploy to RunPod Serverless

#### Step 1: Build Docker Image

```bash
cd comfy-serverless
./scripts/build.sh
```

This creates a Docker image with ComfyUI and the serverless handler.

#### Step 2: Push to Docker Registry

You need to push your image to a container registry. Options:

**Option A: Docker Hub**
```bash
# Login to Docker Hub
docker login

# Push image (replace 'yourusername' with your Docker Hub username)
./scripts/push.sh yourusername/comfyui-serverless latest
```

**Option B: RunPod Registry**
```bash
# Login to RunPod registry
docker login registry.runpod.io

# Push image
./scripts/push.sh registry.runpod.io/yourusername/comfyui-serverless latest
```

#### Step 3: Create RunPod Serverless Endpoint

1. Go to https://www.runpod.io/console/serverless
2. Click "New Endpoint"
3. Configure:
   - **Name**: ComfyUI Serverless
   - **Container Image**: Your image URL (e.g., `yourusername/comfyui-serverless:latest`)
   - **Container Disk**: 10 GB minimum
   - **GPU Types**: Select GPUs you want to use (e.g., RTX 4090, A100)
   - **Workers**: 0 min, 1-3 max (auto-scales)
   - **Idle Timeout**: 30 seconds (to save costs)
4. Click "Deploy"

#### Step 4: Get Your Endpoint ID and API Key

- **Endpoint ID**: Shown on the endpoint page (e.g., `abc123def456`)
- **API Key**: Get from https://www.runpod.io/console/user/settings

Save these for later!

### Part 2: Setup Local ComfyUI

#### Step 1: Install ComfyUI Locally

```bash
cd comfy-serverless/local-setup
./setup-local-comfyui.sh ~/ComfyUI-local
```

This installs ComfyUI in `~/ComfyUI-local` (or your chosen directory).

#### Step 2: Start Local ComfyUI

```bash
cd ~/ComfyUI-local
source venv/bin/activate
python main.py
```

Then open http://localhost:8188 in your browser.

### Part 3: Configure Network Storage (Optional but Recommended)

For models, you have several options:

#### Option A: RunPod Network Volumes

1. Create a Network Volume in RunPod console
2. Upload your models to it
3. Attach it to your endpoint at `/comfyui/models`

#### Option B: Download at Runtime

In your workflow request, specify models to download:

```json
{
  "workflow": {...},
  "models": {
    "checkpoints": [
      {"url": "https://example.com/model.safetensors", "filename": "model.safetensors"}
    ],
    "loras": [
      {"url": "https://example.com/lora.safetensors", "filename": "lora.safetensors"}
    ]
  }
}
```

#### Option C: Bake Models into Docker Image

Edit the Dockerfile to download models during build:

```dockerfile
# Add before CMD
RUN wget -O /comfyui/models/checkpoints/model.safetensors \
    https://example.com/model.safetensors
```

## Usage

### Creating and Running Workflows

1. **Create workflow locally**
   - Open http://localhost:8188
   - Create your workflow in ComfyUI
   - Click "Save (API Format)" to save workflow JSON

2. **Send to RunPod for rendering**

Set your RunPod credentials:
```bash
export RUNPOD_API_KEY="your-api-key-here"
export RUNPOD_ENDPOINT_ID="your-endpoint-id-here"
```

Send the workflow:
```bash
cd comfy-serverless/local-setup
python send-to-runpod.py ~/ComfyUI-local/workflow_api.json
```

3. **Results download automatically** to `./outputs/`

### Example Workflow

Here's a complete example:

```bash
# 1. Start local ComfyUI
cd ~/ComfyUI-local
source venv/bin/activate
python main.py &

# 2. Create a workflow in the browser
# Open http://localhost:8188 and design your workflow
# Save as workflow_api.json

# 3. Set RunPod credentials
export RUNPOD_API_KEY="your-key"
export RUNPOD_ENDPOINT_ID="your-endpoint"

# 4. Send to RunPod
cd ~/comfy-serverless/local-setup
python send-to-runpod.py ~/ComfyUI-local/workflow_api.json

# 5. Images will be saved to ./outputs/
```

## Advanced Configuration

### Custom Model Locations

Edit `handler.py` to customize model paths or add support for additional model types.

### S3 Upload

To automatically upload results to S3, add to your workflow request:

```json
{
  "workflow": {...},
  "s3_upload": {
    "bucket": "my-bucket",
    "prefix": "comfyui-outputs/"
  }
}
```

Make sure your RunPod endpoint has AWS credentials configured.

### GPU Selection

You can specify GPU types when creating your endpoint. Popular options:
- **RTX 4090**: Good balance of performance and cost
- **A100 40GB**: Best for large models
- **RTX A6000**: Good for production workloads

## Troubleshooting

### "Failed to start ComfyUI server"

- Check your Docker image has all dependencies
- Increase container timeout in RunPod settings

### "No workflow provided in input"

- Make sure you're sending the workflow in the correct format
- Use "Save (API Format)" in ComfyUI, not the regular save

### Models not found

- Verify model paths match what's in your workflow
- Use network volumes or download models at runtime
- Check model filenames are correct

### Slow startup times

- Use network volumes for models (faster than downloading)
- Increase min workers to keep instances warm
- Consider baking common models into Docker image

## Cost Optimization

- Set **Min Workers** to 0 (scales to zero when idle)
- Set **Idle Timeout** to 30-60 seconds
- Use cheaper GPU types for testing
- Use network volumes to avoid re-downloading models

## API Reference

### Input Format

```json
{
  "workflow": {
    // ComfyUI workflow JSON (from "Save (API Format)")
  },
  "models": {
    "checkpoints": [
      {"url": "https://...", "filename": "model.safetensors"}
    ],
    "loras": [...],
    "vae": [...],
    "controlnet": [...]
  },
  "return_base64": true,  // Return images as base64
  "s3_upload": {
    "bucket": "my-bucket",
    "prefix": "outputs/"
  }
}
```

### Output Format

```json
{
  "status": "success",
  "images": [
    {
      "filename": "output_001.png",
      "data": "base64_encoded_image..."
    }
  ],
  "prompt_id": "abc123",
  "s3_urls": ["https://..."]  // If S3 upload enabled
}
```

## Next Steps

1. **Install custom nodes**: Modify Dockerfile to include custom ComfyUI nodes
2. **Add authentication**: Protect your endpoint with API keys
3. **Monitoring**: Use RunPod's built-in metrics to monitor usage
4. **Scaling**: Adjust worker counts based on demand

## Resources

- ComfyUI: https://github.com/comfyanonymous/ComfyUI
- RunPod Docs: https://docs.runpod.io/serverless/overview
- Docker Hub: https://hub.docker.com

## Support

For issues:
- RunPod: https://discord.gg/runpod
- ComfyUI: https://github.com/comfyanonymous/ComfyUI/issues
