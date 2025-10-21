# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ComfyUI RunPod Serverless Setup - Run ComfyUI locally for UI/workflow creation, but execute rendering on RunPod serverless GPUs. This project focuses on procedural texture generation, specifically creating seamless tile-based terrain textures (grass, stone) using AI generation and inpainting.

## Python Environment

This project uses `uv` for Python environment management.

**Always use the virtual environment when running Python scripts:**

```bash
.venv/bin/python script.py
```

Or activate first:
```bash
source .venv/bin/activate
python script.py
```

## Key Commands

### Docker Build & Deploy
```bash
# Build the ComfyUI serverless Docker image
./scripts/build.sh

# Push to Docker registry (replace 'yourusername')
./scripts/push.sh yourusername/comfyui-serverless latest
```

### Running Workflows on RunPod

Set environment variables first:
```bash
export RUNPOD_API_KEY="your-api-key"
export RUNPOD_ENDPOINT_ID="your-endpoint-id"
```

Execute workflow:
```bash
.venv/bin/python local-setup/send-to-runpod.py workflows/<workflow-file>.json ./outputs
```

The script polls for completion and automatically downloads results to `./outputs/`.

### Testing Handler Locally
```bash
./scripts/test-local.sh
./scripts/test-interactive.sh
```

## Architecture

### Directory Structure

- **`docker/`** - RunPod serverless Docker image
  - `handler.py` - Main serverless handler (processes workflow requests, manages ComfyUI server)
  - `utils.py` - Helper functions (model downloads, S3 upload, cleanup)
  - `Dockerfile` - Builds ComfyUI with dependencies
  - `ComfyUI/` - ComfyUI installation with custom nodes

- **`local-setup/`** - Local ComfyUI development environment
  - `setup-local-comfyui.sh` - Installs ComfyUI locally (no GPU needed)
  - `send-to-runpod.py` - Client script to submit workflows to RunPod endpoint

- **`scripts/`** - Utility scripts
  - `build.sh`, `push.sh` - Docker build/push automation
  - `create_irregular_mask.py` - Generate procedural masks for texture blending
  - `prepare_tile_grid.py`, `resize_for_workflow.py` - Image preprocessing
  - `test-*.sh`, `test-handler.py` - Testing scripts

- **`workflows/`** - ComfyUI workflow JSON files (API format)
  - `phase5c_smart_blending.json` - Latest: 2x2 grid with grass/stone tiles + smart inpainting
  - `generate_base_tiles.json` - Base tile generation
  - Various test and experimental workflows

### Handler Architecture (docker/handler.py)

The serverless handler follows this flow:

1. **Startup**: Start ComfyUI server on first request (persistent between requests if min_workers > 0)
2. **Reference Images**: Save any uploaded reference images to `/comfyui/input/` BEFORE starting ComfyUI
3. **Model Loading**: Uses RunPod network volume at `/runpod-volume/comfyui/models/`
4. **Workflow Execution**: Queue workflow via ComfyUI API, poll for completion
5. **Output Handling**: Collect generated images, encode as base64, optionally upload to S3
6. **Cleanup**: Remove old outputs to save disk space

**Important**: ComfyUI server runs persistently within each worker. The handler starts it on first request and keeps it alive for subsequent requests.

### Model Storage

Models are stored on RunPod network volumes at:
```
/runpod-volume/comfyui/models/
├── checkpoints/
├── loras/
├── vae/
├── controlnet/
└── upscale_models/
```

The Docker image creates a symlink from `/comfyui/models/` → `/runpod-volume/comfyui/models/` so ComfyUI can find models.

### Workflow Input Format

The handler expects this JSON structure:

```json
{
  "workflow": { /* ComfyUI workflow from "Save (API Format)" */ },
  "reference_images": {
    "filename.png": "base64_encoded_data..."
  },
  "models": {
    "checkpoints": [{"url": "...", "filename": "..."}],
    "loras": [...]
  },
  "return_base64": true,
  "s3_upload": {
    "bucket": "my-bucket",
    "prefix": "outputs/"
  }
}
```

## Tile Generation Workflow

Current focus is on **procedural seamless texture generation** through phases:

1. **Phase 1-2**: Generate individual tiles (grass/stone) with varied seeds
2. **Phase 3**: Composite tiles into grids (2x1, 2x2)
3. **Phase 4-5**: Inpaint seams between tiles for seamless transitions
4. **Phase 5c** (current): Smart material-aware blending - different inpainting strategies for grass-grass, stone-stone, and grass-stone transitions

### Key Workflow: phase5c_smart_blending.json

Generates a 2x2 grid (2048x2048) with:
- Top row: 2 grass tiles (different seeds)
- Bottom row: 2 stone tiles (different seeds)

Then performs 3-stage inpainting:
1. Vertical seams (grass-grass and stone-stone) - light blending
2. Horizontal seam (grass-stone transition) - heavy organic blending with irregular wavy mask
3. Stone patches in grass area - adds natural scattered stones

Uses custom masks:
- `irregular_horizontal_mask.png` - Wavy boundary for organic grass/stone transition
- `stone_patches_in_grass.png` - Scattered patches for material mixing

## Local Development Workflow

1. Run ComfyUI locally to design workflows:
   ```bash
   cd ~/ComfyUI-local
   source venv/bin/activate
   python main.py
   # Open http://localhost:8188
   ```

2. Create placeholder model files locally that match RunPod network storage:
   ```bash
   touch ~/ComfyUI-local/models/checkpoints/sd_xl_base_1.0.safetensors
   touch ~/ComfyUI-local/models/loras/Hand-Painted_2d_Seamless_Textures-000007.safetensors
   ```

3. Save workflow as "API Format" JSON

4. Upload reference images if needed (placed in `local-setup/samples/` or specified directory)

5. Test locally with `./scripts/test-local.sh` or send to RunPod with `send-to-runpod.py`

## Important Notes

- **Worker Configuration**:
  - `min_workers: 1` = models stay loaded, fast subsequent requests
  - `min_workers: 0` = cheaper but every request reloads models (30-60s startup)

- **Reference Images**: Must be saved to ComfyUI input directory BEFORE server starts to be visible to LoadImage nodes

- **API Format**: Always use "Save (API Format)" in ComfyUI, not regular save - this is the format the handler expects

- **Mask Generation**: The `create_irregular_mask.py` script generates procedural masks using Perlin noise and sine waves for organic terrain boundaries
