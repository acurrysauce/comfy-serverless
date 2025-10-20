#!/bin/bash
# Push Docker image to registry

set -e

IMAGE_NAME="comfyui-serverless"
REGISTRY="${1:-curryberto/comfyui-serverless}"
TAG="${2:-latest}"

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
