#!/bin/bash
# Build Docker image for ComfyUI RunPod serverless

set -e

# Configuration
IMAGE_NAME="comfyui-serverless"
TAG="${1:-latest}"
FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"

echo "Building Docker image: ${FULL_IMAGE_NAME}"

# Build from docker directory
cd "$(dirname "$0")/../docker"

docker build -t "${FULL_IMAGE_NAME}" .

echo ""
echo "Build complete!"
echo "Image: ${FULL_IMAGE_NAME}"
echo ""
echo "Next steps:"
echo "1. Test locally: ./scripts/test-local.sh"
echo "2. Push to registry: ./scripts/push.sh [registry]"
