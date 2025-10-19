#!/usr/bin/env python3
"""
Send ComfyUI workflow to RunPod serverless endpoint
Use this script to submit workflows from your local ComfyUI to RunPod for rendering
"""

import requests
import json
import sys
import os
import time
import base64
from pathlib import Path


# Configuration - UPDATE THESE
RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY", "")
RUNPOD_ENDPOINT_ID = os.environ.get("RUNPOD_ENDPOINT_ID", "")


def send_workflow(workflow_file, models=None, output_dir="./outputs"):
    """
    Send workflow to RunPod serverless endpoint

    Args:
        workflow_file: Path to ComfyUI workflow JSON file
        models: Optional dict of models to use
        output_dir: Directory to save output images
    """

    if not RUNPOD_API_KEY:
        print("Error: RUNPOD_API_KEY not set")
        print("Set it with: export RUNPOD_API_KEY='your-key'")
        return

    if not RUNPOD_ENDPOINT_ID:
        print("Error: RUNPOD_ENDPOINT_ID not set")
        print("Set it with: export RUNPOD_ENDPOINT_ID='your-endpoint-id'")
        return

    # Read workflow
    with open(workflow_file, 'r') as f:
        workflow = json.load(f)

    # Prepare request
    payload = {
        "input": {
            "workflow": workflow,
            "return_base64": True
        }
    }

    # Add models if specified
    if models:
        payload["input"]["models"] = models

    # API endpoint - Queue mode uses api.runpod.ai/v2/{id}/run
    url = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/run"

    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }

    print(f"Sending workflow to RunPod endpoint: {RUNPOD_ENDPOINT_ID}")
    print(f"Workflow: {workflow_file}")
    print(f"Using Queue mode")

    # Submit job
    print("Submitting job...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        print(f"Error submitting job: {response.status_code}")
        print(response.text)
        return

    result = response.json()
    job_id = result.get("id")

    if not job_id:
        print("Error: No job ID returned")
        print(result)
        return

    print(f"Job submitted! ID: {job_id}")
    print("Waiting for completion...")

    # Poll for results
    status_url = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/status/{job_id}"

    while True:
        time.sleep(2)

        status_response = requests.get(status_url, headers=headers)

        if status_response.status_code != 200:
            print(f"Error checking status: {status_response.status_code}")
            break

        status_data = status_response.json()
        job_status = status_data.get("status")

        print(f"Status: {job_status}")

        if job_status == "COMPLETED":
            output = status_data.get("output", {})

            if "error" in output:
                print(f"Job failed with error: {output['error']}")
                if "traceback" in output:
                    print(f"Traceback: {output['traceback']}")
                break

            images = output.get("images", [])
            print(f"\nReceived {len(images)} images!")

            # Save images
            os.makedirs(output_dir, exist_ok=True)

            for i, image_data in enumerate(images):
                filename = image_data.get("filename", f"output_{i}.png")
                image_base64 = image_data.get("data", "")

                output_path = os.path.join(output_dir, filename)

                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(image_base64))

                print(f"Saved: {output_path}")

            print("\nDone!")
            break

        elif job_status in ["FAILED", "CANCELLED"]:
            print(f"Job {job_status}")
            print(status_data)
            break


def main():
    if len(sys.argv) < 2:
        print("Usage: python send-to-runpod.py <workflow.json> [output_dir]")
        print("")
        print("Environment variables:")
        print("  RUNPOD_API_KEY      - Your RunPod API key")
        print("  RUNPOD_ENDPOINT_ID  - Your RunPod endpoint ID")
        print("")
        print("Example:")
        print("  export RUNPOD_API_KEY='your-key'")
        print("  export RUNPOD_ENDPOINT_ID='your-endpoint-id'")
        print("  python send-to-runpod.py workflow_api.json")
        sys.exit(1)

    workflow_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./outputs"

    send_workflow(workflow_file, output_dir=output_dir)


if __name__ == "__main__":
    main()
