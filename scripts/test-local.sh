#!/bin/bash
# Test Docker image locally with RunPod simulation

set -e

IMAGE_NAME="comfyui-serverless:latest"

echo "Testing ${IMAGE_NAME} locally..."
echo ""
echo "Note: Running without GPU (testing structure only)"
echo "This will start the container and you can test the handler"
echo "Press Ctrl+C to stop"
echo ""

# Try with GPU first, fall back to CPU if no GPU support
if docker run --rm --gpus all hello-world &> /dev/null 2>&1; then
    echo "GPU support detected, running with --gpus all"
    docker run --rm -it \
        --gpus all \
        -p 8188:8188 \
        -e RUNPOD_AI_API_KEY="${RUNPOD_AI_API_KEY}" \
        "${IMAGE_NAME}"
else
    echo "No GPU support (this is fine for testing structure)"
    docker run --rm -it \
        -p 8188:8188 \
        -e RUNPOD_AI_API_KEY="${RUNPOD_AI_API_KEY}" \
        "${IMAGE_NAME}"
fi
