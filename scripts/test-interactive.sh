#!/bin/bash
# Test the Docker image interactively
# This lets you poke around inside the container and verify everything works

set -e

IMAGE_NAME="comfyui-serverless:latest"

echo "Starting interactive Docker container..."
echo "This will give you a shell inside the container to test things"
echo ""

# Check if image exists
if ! docker image inspect "${IMAGE_NAME}" &> /dev/null; then
    echo "Error: Image ${IMAGE_NAME} not found"
    echo "Build it first with: ./scripts/build.sh"
    exit 1
fi

echo "Running container with shell access..."
echo "Inside the container, you can:"
echo "  - Check if ComfyUI is installed: ls -la /comfyui"
echo "  - Test Python imports: /comfyui/.venv/bin/python -c 'import torch; print(torch.__version__)'"
echo "  - Run the handler manually: /comfyui/.venv/bin/python /handler.py"
echo ""
echo "Press Ctrl+D or type 'exit' to leave the container"
echo ""

docker run --rm -it \
    --entrypoint /bin/bash \
    "${IMAGE_NAME}"
