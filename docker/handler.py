#!/usr/bin/env python3
"""
RunPod Serverless Handler for ComfyUI
Processes workflow requests and returns generated images
"""

HANDLER_VERSION = "3.0-runpod-volume"  # Version marker for debugging

import runpod
import json
import os
import sys
import time
import subprocess
import requests
import base64
import shutil
from pathlib import Path
from utils import download_models, upload_to_s3, cleanup_outputs

# ComfyUI path
COMFYUI_PATH = "/comfyui"
COMFYUI_OUTPUT = f"{COMFYUI_PATH}/output"
COMFYUI_INPUT = f"{COMFYUI_PATH}/input"
COMFYUI_PYTHON = "/comfyui/.venv/bin/python"

# Models path - RunPod mounts network volumes at /runpod-volume
MODELS_PATH = "/runpod-volume/comfyui/models"

# Custom nodes paths
NETWORK_CUSTOM_NODES = "/runpod-volume/comfyui/custom_nodes"
COMFYUI_CUSTOM_NODES = f"{COMFYUI_PATH}/custom_nodes"

# ComfyUI server process
comfyui_process = None
custom_nodes_synced = False


def sync_custom_nodes():
    """Copy custom nodes from network volume to local container at startup"""
    global custom_nodes_synced

    if custom_nodes_synced:
        print("Custom nodes already synced, skipping...")
        return

    print("Syncing custom nodes from network volume...")

    # Create network custom_nodes directory if it doesn't exist
    if not os.path.exists(NETWORK_CUSTOM_NODES):
        os.makedirs(NETWORK_CUSTOM_NODES, exist_ok=True)
        print(f"  Created network custom_nodes directory: {NETWORK_CUSTOM_NODES}")
        custom_nodes_synced = True
        return

    # Ensure local custom_nodes directory exists
    os.makedirs(COMFYUI_CUSTOM_NODES, exist_ok=True)

    # Copy each custom node folder from network to local
    synced_count = 0
    for node_dir in os.listdir(NETWORK_CUSTOM_NODES):
        src = os.path.join(NETWORK_CUSTOM_NODES, node_dir)
        dst = os.path.join(COMFYUI_CUSTOM_NODES, node_dir)

        # Only sync directories (skip files)
        if os.path.isdir(src):
            try:
                # Remove old version if exists
                if os.path.exists(dst):
                    shutil.rmtree(dst)

                # Copy to local
                shutil.copytree(src, dst)
                print(f"  ✓ Synced: {node_dir}")
                synced_count += 1
            except Exception as e:
                print(f"  ✗ Failed to sync {node_dir}: {e}")

    if synced_count > 0:
        print(f"Successfully synced {synced_count} custom node(s)")
    else:
        print("No custom nodes found on network volume")

    custom_nodes_synced = True


def start_comfyui_server():
    """Start ComfyUI server in background"""
    global comfyui_process

    if comfyui_process is None:
        # Sync custom nodes from network volume BEFORE starting ComfyUI
        sync_custom_nodes()

        print("Starting ComfyUI server...")
        print(f"Models path: {MODELS_PATH}")

        # Point ComfyUI to the network storage models location
        comfyui_process = subprocess.Popen(
            [COMFYUI_PYTHON, "main.py",
             "--listen", "0.0.0.0",
             "--port", "8188",
             "--input-directory", COMFYUI_INPUT,
             "--output-directory", COMFYUI_OUTPUT,
             # Use base path for models on network storage
             "--extra-model-paths-config", "/model_paths.yaml"],
            cwd=COMFYUI_PATH,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait for server to be ready
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get("http://localhost:8188/history")
                if response.status_code == 200:
                    print("ComfyUI server is ready!")
                    return True
            except requests.exceptions.ConnectionError:
                time.sleep(1)
                print(f"Waiting for ComfyUI server... ({i+1}/{max_retries})")

        print("Failed to start ComfyUI server")
        return False

    return True


def queue_prompt(workflow):
    """Queue a prompt/workflow in ComfyUI"""
    url = "http://localhost:8188/prompt"

    payload = {
        "prompt": workflow
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to queue prompt: {response.text}")


def wait_for_completion(prompt_id):
    """Wait for a prompt to complete and return output files"""
    max_wait = 300  # 5 minutes max
    start_time = time.time()

    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"http://localhost:8188/history/{prompt_id}")
            history = response.json()

            if prompt_id in history:
                prompt_history = history[prompt_id]

                print(f"History for prompt {prompt_id}: {json.dumps(prompt_history, indent=2)}")

                # Check for errors
                if "status" in prompt_history and prompt_history["status"].get("status_str") == "error":
                    error_msg = prompt_history["status"].get("messages", [])
                    raise Exception(f"ComfyUI workflow error: {error_msg}")

                # Check if completed
                if "outputs" in prompt_history:
                    outputs = prompt_history["outputs"]
                    output_files = []

                    # Extract output files
                    print(f"DEBUG: Processing outputs from {len(outputs)} nodes")
                    for node_id, node_output in outputs.items():
                        print(f"DEBUG: Node {node_id} output: {node_output.keys()}")
                        if "images" in node_output:
                            print(f"DEBUG: Node {node_id} has {len(node_output['images'])} images")
                            for image in node_output["images"]:
                                filename = image["filename"]
                                output_files.append(filename)
                                print(f"DEBUG: Added image: {filename}")

                    print(f"DEBUG: Total output files collected: {len(output_files)}")
                    return output_files

        except Exception as e:
            print(f"Error checking completion: {e}")

        time.sleep(2)

    raise Exception("Timeout waiting for prompt completion")


def get_output_images(filenames, return_base64=True):
    """Get output images as base64 or file paths"""
    results = []

    for filename in filenames:
        filepath = os.path.join(COMFYUI_OUTPUT, filename)

        if os.path.exists(filepath):
            if return_base64:
                with open(filepath, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                    results.append({
                        "filename": filename,
                        "data": image_data
                    })
            else:
                results.append({
                    "filename": filename,
                    "path": filepath
                })

    return results


def handler(event):
    """
    Main handler function for RunPod serverless

    Expected input format:
    {
        "workflow": {...},  # ComfyUI workflow JSON
        "models": {         # Optional: models to download
            "checkpoints": ["model.safetensors"],
            "loras": ["lora.safetensors"]
        },
        "return_base64": true,  # Return images as base64 (default: true)
        "s3_upload": {          # Optional: upload to S3
            "bucket": "my-bucket",
            "prefix": "outputs/"
        }
    }
    """
    try:
        input_data = event.get('input', {})

        # Save reference images BEFORE starting ComfyUI so it can see them
        if "reference_images" in input_data:
            print("Saving reference images to input folder...")
            reference_images = input_data["reference_images"]
            for filename, image_base64 in reference_images.items():
                filepath = os.path.join(COMFYUI_INPUT, filename)
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(image_base64))
                print(f"  Saved: {filepath}")

        # Start ComfyUI server if not running
        if not start_comfyui_server():
            return {
                "error": "Failed to start ComfyUI server"
            }

        # Download models if specified
        if "models" in input_data:
            print("Downloading models...")
            download_models(input_data["models"])

        # Get workflow
        workflow = input_data.get("workflow")
        if not workflow:
            return {
                "error": "No workflow provided in input"
            }

        print("Queueing workflow...")
        print(f"DEBUG: Workflow has {len(workflow)} nodes")

        # Debug: List model directories
        print("\nDEBUG: Listing model directories:")
        checkpoints_dir = "/runpod-volume/comfyui/models/checkpoints"
        controlnet_dir = "/runpod-volume/comfyui/models/controlnet"

        if os.path.exists(checkpoints_dir):
            checkpoints = os.listdir(checkpoints_dir)
            print(f"  Checkpoints dir: {checkpoints}")
        else:
            print(f"  Checkpoints dir DOES NOT EXIST: {checkpoints_dir}")

        if os.path.exists(controlnet_dir):
            controlnets = os.listdir(controlnet_dir)
            print(f"  ControlNet dir: {controlnets}")
        else:
            print(f"  ControlNet dir DOES NOT EXIST: {controlnet_dir}")

        if os.path.exists(COMFYUI_INPUT):
            input_files = os.listdir(COMFYUI_INPUT)
            print(f"  Input dir: {input_files}")
        else:
            print(f"  Input dir DOES NOT EXIST: {COMFYUI_INPUT}")

        # Debug: Check for missing files
        print("\nDEBUG: Checking workflow requirements:")
        for node_id, node_data in workflow.items():
            if node_data.get("class_type") == "CheckpointLoaderSimple":
                ckpt = node_data["inputs"]["ckpt_name"]
                ckpt_path = f"/runpod-volume/comfyui/models/checkpoints/{ckpt}"
                if os.path.exists(ckpt_path):
                    print(f"  ✓ Found checkpoint: {ckpt}")
                else:
                    print(f"  ✗ MISSING checkpoint: {ckpt} at {ckpt_path}")

            elif node_data.get("class_type") == "ControlNetLoader":
                cn = node_data["inputs"]["control_net_name"]
                cn_path = f"/runpod-volume/comfyui/models/controlnet/{cn}"
                if os.path.exists(cn_path):
                    print(f"  ✓ Found ControlNet: {cn}")
                else:
                    print(f"  ✗ MISSING ControlNet: {cn} at {cn_path}")

            elif node_data.get("class_type") == "LoadImage":
                img = node_data["inputs"]["image"]
                img_path = f"{COMFYUI_INPUT}/{img}"
                if os.path.exists(img_path):
                    print(f"  ✓ Found image: {img}")
                else:
                    print(f"  ✗ MISSING image: {img} at {img_path}")

        result = queue_prompt(workflow)
        prompt_id = result.get("prompt_id")

        if not prompt_id:
            return {
                "error": "Failed to get prompt_id from ComfyUI"
            }

        print(f"Waiting for completion (prompt_id: {prompt_id})...")
        output_files = wait_for_completion(prompt_id)

        print(f"Generated {len(output_files)} images")
        print(f"Output files: {output_files}")
        print(f"Output directory contents: {os.listdir(COMFYUI_OUTPUT) if os.path.exists(COMFYUI_OUTPUT) else 'DIR NOT FOUND'}")

        # Get output images
        return_base64 = input_data.get("return_base64", True)
        images = get_output_images(output_files, return_base64)

        # Upload to S3 if configured
        s3_urls = []
        if "s3_upload" in input_data:
            print("Uploading to S3...")
            s3_config = input_data["s3_upload"]
            for image in images:
                filepath = os.path.join(COMFYUI_OUTPUT, image["filename"])
                s3_url = upload_to_s3(
                    filepath,
                    s3_config["bucket"],
                    s3_config.get("prefix", "")
                )
                s3_urls.append(s3_url)

        # Cleanup old outputs
        cleanup_outputs(COMFYUI_OUTPUT)

        response = {
            "status": "success",
            "images": images,
            "prompt_id": prompt_id
        }

        if s3_urls:
            response["s3_urls"] = s3_urls

        return response

    except Exception as e:
        print(f"Error in handler: {str(e)}")
        import traceback
        traceback.print_exc()

        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


if __name__ == "__main__":
    print(f"Starting RunPod Serverless Handler for ComfyUI - Version {HANDLER_VERSION}")
    print(f"Checking symlink: /comfyui/models -> {os.readlink('/comfyui/models') if os.path.islink('/comfyui/models') else 'NOT A SYMLINK'}")
    runpod.serverless.start({"handler": handler})
