# Setup Network Storage with Models

## Method 1: Using a Temporary Pod (Easiest)

1. Go to RunPod Console → Pods
2. Click "Deploy" or "+ New Pod"
3. Select any cheap GPU or CPU pod
4. Under "Select Network Volume" → Choose your volume
5. Set mount path: `/workspace`
6. Deploy the pod

7. Once running, click "Connect" → "Start Jupyter Lab" or "SSH"

8. In the terminal, download models:

```bash
cd /workspace

# Create folder structure
mkdir -p checkpoints loras vae controlnet embeddings

# Download a model (example: SD 1.5)
cd checkpoints
wget https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors

# Or download from Civitai (get the download link from the site)
wget -O my-model.safetensors "https://civitai.com/api/download/models/XXXXX"
```

9. When done, STOP/DELETE the pod (so you don't keep paying for it)

Your models are now in network storage and will persist!

## Method 2: Using AWS CLI / S3 Tools

You'll need S3 credentials from RunPod:
1. Go to your Network Volume settings
2. Look for "S3 Access Credentials" or "API Credentials"
3. Copy Access Key, Secret Key, and Endpoint URL

Then use tools like:
- **AWS CLI**: `aws s3 cp model.safetensors s3://bucket/checkpoints/ --endpoint-url=https://...`
- **rclone**: Configure with RunPod S3 endpoint
- **Cyberduck**: GUI tool for S3

## Recommended Approach

Use **Temporary Pod** - it's the simplest and fastest for downloading models directly to your network storage.

Total time: ~5-10 minutes to set up and download a model
