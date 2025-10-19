#!/bin/bash
# Setup ComfyUI locally (for UI only - rendering happens on RunPod)

set -e

echo "Setting up ComfyUI locally..."

# Create directory
INSTALL_DIR="${1:-$HOME/ComfyUI-local}"

echo "Installation directory: ${INSTALL_DIR}"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed"
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Clone ComfyUI if not exists
if [ ! -d "${INSTALL_DIR}" ]; then
    echo "Cloning ComfyUI..."
    git clone https://github.com/comfyanonymous/ComfyUI.git "${INSTALL_DIR}"
else
    echo "ComfyUI already exists at ${INSTALL_DIR}"
fi

cd "${INSTALL_DIR}"

# Create virtual environment with uv
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment with uv..."
    uv venv
fi

# Install requirements with uv
echo "Installing requirements with uv..."
uv pip install -r requirements.txt

echo ""
echo "Setup complete!"
echo ""
echo "To start ComfyUI locally:"
echo "  cd ${INSTALL_DIR}"
echo "  source .venv/bin/activate"
echo "  python main.py"
echo ""
echo "Or use uv directly:"
echo "  cd ${INSTALL_DIR}"
echo "  uv run python main.py"
echo ""
echo "Then open: http://localhost:8188"
echo ""
echo "Note: You'll create workflows locally, but send them to RunPod for rendering"
