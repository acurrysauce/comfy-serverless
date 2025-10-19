#!/usr/bin/env python3
"""
Utility functions for ComfyUI serverless handler
"""

import os
import shutil
import requests
import boto3
from pathlib import Path
from datetime import datetime, timedelta


def download_file(url, destination):
    """Download a file from URL to destination"""
    print(f"Downloading {url} to {destination}")

    response = requests.get(url, stream=True)
    response.raise_for_status()

    os.makedirs(os.path.dirname(destination), exist_ok=True)

    with open(destination, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"Downloaded {destination}")


def download_models(models_config):
    """
    Download models from URLs or S3

    models_config format:
    {
        "checkpoints": [
            {"url": "https://...", "filename": "model.safetensors"},
            {"s3": "s3://bucket/path/model.safetensors", "filename": "model.safetensors"}
        ],
        "loras": [...],
        "vae": [...]
    }
    """
    COMFYUI_PATH = "/comfyui"

    model_types = {
        "checkpoints": f"{COMFYUI_PATH}/models/checkpoints",
        "loras": f"{COMFYUI_PATH}/models/loras",
        "vae": f"{COMFYUI_PATH}/models/vae",
        "embeddings": f"{COMFYUI_PATH}/models/embeddings",
        "controlnet": f"{COMFYUI_PATH}/models/controlnet",
    }

    for model_type, models in models_config.items():
        if model_type not in model_types:
            print(f"Unknown model type: {model_type}")
            continue

        destination_dir = model_types[model_type]

        for model in models:
            if isinstance(model, str):
                # Simple string URL
                filename = os.path.basename(model)
                destination = os.path.join(destination_dir, filename)

                if not os.path.exists(destination):
                    download_file(model, destination)
            elif isinstance(model, dict):
                filename = model.get("filename")

                if not filename:
                    print("Model config missing filename")
                    continue

                destination = os.path.join(destination_dir, filename)

                # Skip if already exists
                if os.path.exists(destination):
                    print(f"Model already exists: {destination}")
                    continue

                if "url" in model:
                    download_file(model["url"], destination)
                elif "s3" in model:
                    download_from_s3(model["s3"], destination)


def download_from_s3(s3_path, destination):
    """Download file from S3"""
    # Parse s3://bucket/key format
    if s3_path.startswith("s3://"):
        s3_path = s3_path[5:]

    parts = s3_path.split("/", 1)
    bucket = parts[0]
    key = parts[1] if len(parts) > 1 else ""

    print(f"Downloading from S3: s3://{bucket}/{key}")

    s3 = boto3.client('s3')
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    s3.download_file(bucket, key, destination)

    print(f"Downloaded {destination}")


def upload_to_s3(filepath, bucket, prefix=""):
    """Upload file to S3 and return URL"""
    s3 = boto3.client('s3')

    filename = os.path.basename(filepath)
    key = f"{prefix}{filename}" if prefix else filename

    print(f"Uploading {filepath} to s3://{bucket}/{key}")

    s3.upload_file(filepath, bucket, key)

    # Generate URL (valid for 7 days)
    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': key},
        ExpiresIn=604800  # 7 days
    )

    return url


def cleanup_outputs(output_dir, max_age_minutes=60):
    """Clean up old output files"""
    now = datetime.now()

    for filename in os.listdir(output_dir):
        filepath = os.path.join(output_dir, filename)

        if os.path.isfile(filepath):
            file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            age = now - file_time

            if age > timedelta(minutes=max_age_minutes):
                print(f"Removing old file: {filepath}")
                os.remove(filepath)
