#!/bin/bash
# Push Docker image to registry

set -e

IMAGE_NAME="comfyui-serverless"
TAG="${2:-latest}"
REGISTRY="${1}"

if [ -z "$REGISTRY" ]; then
    echo "Usage: $0 <registry> [tag]"
    echo ""
    echo "Examples:"
    echo "  $0 username/comfyui-serverless latest"
    echo "  $0 registry.runpod.io/username/comfyui-serverless v1.0"
    exit 1
fi

FULL_IMAGE_NAME="${REGISTRY}:${TAG}"

echo "Tagging image..."
# Always tag from :latest (which build.sh creates)
docker tag "${IMAGE_NAME}:latest" "${FULL_IMAGE_NAME}"

echo "Pushing to registry: ${FULL_IMAGE_NAME}"
docker push "${FULL_IMAGE_NAME}"

echo ""
echo "Push complete!"
echo "Image URL: ${FULL_IMAGE_NAME}"
echo ""
echo "Use this image in RunPod serverless endpoint configuration"
