# ComfyUI RunPod Serverless Docker Image
FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    wget \
    curl \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic links for python
RUN ln -s /usr/bin/python3 /usr/bin/python

# Install uv for faster package installation
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    /root/.local/bin/uv --version
ENV PATH="/root/.local/bin:${PATH}"

# Copy ComfyUI (including custom nodes) into the image
COPY ComfyUI /comfyui

# Set working directory
WORKDIR /comfyui

# Create virtual environment with uv
RUN /root/.local/bin/uv venv /comfyui/.venv

# Install ComfyUI requirements with uv (much faster!)
RUN /root/.local/bin/uv pip install --python /comfyui/.venv/bin/python -r requirements.txt

# Install custom node requirements
RUN if [ -f /comfyui/custom_nodes/ComfyUI-KJNodes/requirements.txt ]; then \
        /root/.local/bin/uv pip install --python /comfyui/.venv/bin/python -r /comfyui/custom_nodes/ComfyUI-KJNodes/requirements.txt; \
    fi

# Install additional packages for serverless
RUN /root/.local/bin/uv pip install --python /comfyui/.venv/bin/python \
    runpod \
    boto3 \
    requests \
    pillow

# Create output and input directories
RUN mkdir -p /comfyui/output /comfyui/input

# Copy model paths config for network storage
COPY model_paths.yaml /model_paths.yaml

# Copy handler script
COPY handler.py /handler.py
COPY utils.py /utils.py

# Set the working directory for the handler
WORKDIR /

# Expose port for ComfyUI (not used in serverless but helpful for testing)
EXPOSE 8188

# Command to run the handler
CMD ["/comfyui/.venv/bin/python", "-u", "/handler.py"]
