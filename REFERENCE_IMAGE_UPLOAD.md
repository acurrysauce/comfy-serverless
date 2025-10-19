# Reference Image Upload Feature

## Overview

The system now supports **automatic upload of reference images** with each workflow request. This eliminates the need to:
- Rebuild Docker images when adding new references
- Manually manage network storage for reference images
- Worry about file path mismatches between local and RunPod

## How It Works

### **1. Local Side (send-to-runpod.py)**
- Reads all images from a specified directory
- Encodes them as base64
- Includes them in the request payload

### **2. RunPod Side (handler.py)**
- Receives reference images in request
- Decodes and saves them to `/comfyui/input/`
- ComfyUI can then load them normally

## Usage

```bash
python send-to-runpod.py workflow.json ./outputs ./local-setup/samples/
#                                       ^^^^^^^^^  ^^^^^^^^^^^^^^^^^^^^
#                                       output dir reference images dir
```

### **Example:**

```bash
# Set RunPod credentials
export RUNPOD_API_KEY="your-key"
export RUNPOD_ENDPOINT_ID="your-endpoint"

# Send workflow with reference images from samples folder
python send-to-runpod.py \
    workflows/tile_transition_generator.json \
    ./outputs \
    ./local-setup/samples
```

**What happens:**
1. Script reads all `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp` files from `./local-setup/samples/`
2. Encodes them as base64
3. Sends them along with the workflow
4. Handler saves them to `/comfyui/input/` on RunPod
5. Your workflow's LoadImage nodes can reference them by filename

## Cost Analysis

### **Request Size Impact:**

Typical 512x512 PNG image:
- Original size: ~300KB
- Base64 encoded: ~400KB (33% overhead)

Example scenarios:

| Reference Images | Total Size Added | Upload Time (10 Mbps) | RunPod Cost Impact |
|-----------------|------------------|----------------------|-------------------|
| 2 images        | ~800KB           | <1 second            | Negligible        |
| 5 images        | ~2MB             | ~2 seconds           | Negligible        |
| 10 images       | ~4MB             | ~4 seconds           | Negligible        |

### **Cost Breakdown:**

**Data transfer:** Free (within RunPod's generous limits)
**Processing time:** ~0.1 seconds to decode/save images
**GPU time cost:** 0.1s × $0.0002/s = $0.00002 per request

**Verdict: Essentially free, adds <1 second to request time**

### **When to Avoid This Approach:**

- Very large reference images (>5MB each)
- Many reference images (>20)
- Slow internet connection
- Thousands of requests per day with same references

In those cases, consider:
- Baking images into Docker (rebuild when changed)
- Using network storage (one-time upload)

## Benefits

✅ **Flexibility** - Add/remove reference images instantly
✅ **No Docker rebuilds** - Just drop files in folder
✅ **Version control friendly** - References in repo
✅ **Self-contained requests** - Everything in one payload
✅ **No network storage setup** - Works out of the box

## Limitations

⚠️ **Request size limits** - RunPod has max request size (~10-20MB)
⚠️ **Redundant uploads** - Same images sent with every request
⚠️ **Slower on slow connections** - Upload time depends on bandwidth

## Alternative Approaches

### **Option A: Bake into Docker** (Good for static references)
```dockerfile
COPY reference_images/ /comfyui/input/
```
**Pros:** No upload overhead, faster
**Cons:** Requires Docker rebuild to change

### **Option B: Network Storage** (Good for large/many references)
```bash
# One-time upload to network storage
# Then symlink in handler.py
```
**Pros:** One-time upload, shared across all workers
**Cons:** Requires network storage setup, less flexible

### **Option C: Upload with request** (Good for flexibility) ✅ Current
**Pros:** Maximum flexibility, no infrastructure
**Cons:** Small overhead per request

## Technical Details

### **Supported File Types:**
- `.png`
- `.jpg` / `.jpeg`
- `.webp`
- `.bmp`

### **Encoding:**
- Base64 encoding for JSON compatibility
- Automatic decoding on RunPod side
- Saved to `/comfyui/input/{filename}`

### **Workflow Integration:**
In your ComfyUI workflow, reference images by filename:

```json
{
  "type": "LoadImage",
  "widgets_values": ["stone_floor_512x512.png", "image"]
}
```

No path needed - just filename!

## Example Workflow

```bash
# 1. Create reference images directory
mkdir -p local-setup/samples

# 2. Add your reference images
cp ~/my-textures/grass.png local-setup/samples/
cp ~/my-textures/stone.png local-setup/samples/

# 3. Resize them if needed
.venv/bin/python scripts/resize_for_workflow.py \
    local-setup/samples/grass.png 512 512 \
    local-setup/samples/grass_512x512.png cover

# 4. Send workflow with references
python send-to-runpod.py \
    workflows/my_workflow.json \
    ./outputs \
    ./local-setup/samples

# 5. Handler automatically saves them to /comfyui/input/
# 6. Workflow's LoadImage nodes can access them!
```

## Troubleshooting

### **"Request too large" error**
- Reduce number of reference images
- Compress images before upload
- Use lower resolution
- Consider Docker or network storage approach

### **Images not found in workflow**
- Check filename in LoadImage node matches exactly
- Verify images were uploaded (check handler logs)
- Ensure file extensions are supported

### **Slow upload times**
- Reduce image resolution
- Compress images
- Check internet connection
- Consider baking into Docker for static references

## Summary

This approach gives you **maximum flexibility** with **minimal cost**. Perfect for:
- Development and testing
- Frequently changing reference images
- Small to medium number of references (<10 images)
- Self-contained workflows

As you scale, you can always migrate to Docker or network storage!
