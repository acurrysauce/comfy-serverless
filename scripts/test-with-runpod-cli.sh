#!/bin/bash
# Test using RunPod CLI to simulate serverless environment locally
# This is the closest to real RunPod behavior

set -e

IMAGE_NAME="comfyui-serverless:latest"

echo "Testing with RunPod CLI..."
echo ""

# Check if runpodctl is installed
if ! command -v runpodctl &> /dev/null; then
    echo "RunPod CLI not installed. Installing..."
    echo ""
    wget -qO- https://github.com/runpod/runpodctl/releases/latest/download/runpodctl-linux-amd64 -O /tmp/runpodctl
    chmod +x /tmp/runpodctl
    sudo mv /tmp/runpodctl /usr/local/bin/runpodctl
    echo "✅ RunPod CLI installed"
fi

# Check if image exists
if ! docker image inspect "${IMAGE_NAME}" &> /dev/null; then
    echo "Error: Image ${IMAGE_NAME} not found"
    echo "Build it first with: ./scripts/build.sh"
    exit 1
fi

echo "Starting local serverless simulation..."
echo ""
echo "This will start your container in RunPod's serverless mode"
echo "You can send test requests to http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

runpodctl project dev "${IMAGE_NAME}"
