#!/usr/bin/env python3
"""
Resize Image for Workflow

Resizes images to the correct dimensions for ComfyUI workflows.
Maintains aspect ratio and uses high-quality resampling.

Usage:
    python resize_for_workflow.py input.png 512 512 output.png
    python resize_for_workflow.py input.png 512          # Auto output name
    python resize_for_workflow.py input.png              # Defaults to 512x512
"""

import sys
import os
from PIL import Image


def resize_image(input_path, width, height, output_path=None, method="contain"):
    """
    Resize image to target dimensions

    Args:
        input_path: Path to input image
        width: Target width
        height: Target height
        output_path: Path to save output (optional)
        method: Resize method - "contain", "cover", "stretch", or "pad"
    """

    # Load image
    img = Image.open(input_path)
    original_size = img.size

    print(f"Input image: {input_path}")
    print(f"  Original size: {original_size[0]}x{original_size[1]}")
    print(f"  Target size: {width}x{height}")

    # Choose resize method
    if method == "stretch":
        # Stretch to exact dimensions (may distort)
        result = img.resize((width, height), Image.Resampling.LANCZOS)
        print(f"  Method: Stretch (may distort aspect ratio)")

    elif method == "cover":
        # Crop to fill entire target size
        aspect_target = width / height
        aspect_img = img.width / img.height

        if aspect_img > aspect_target:
            # Image is wider, scale by height
            new_height = height
            new_width = int(img.width * (height / img.height))
        else:
            # Image is taller, scale by width
            new_width = width
            new_height = int(img.height * (width / img.width))

        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Crop to exact size
        left = (new_width - width) // 2
        top = (new_height - height) // 2
        result = resized.crop((left, top, left + width, top + height))
        print(f"  Method: Cover (crop to fill)")

    elif method == "pad":
        # Fit inside target size with padding
        img.thumbnail((width, height), Image.Resampling.LANCZOS)

        # Create new image with target size and paste centered
        result = Image.new('RGB', (width, height), (0, 0, 0))
        paste_x = (width - img.width) // 2
        paste_y = (height - img.height) // 2
        result.paste(img, (paste_x, paste_y))
        print(f"  Method: Pad (add borders)")

    else:  # "contain" (default)
        # Fit to exact target size maintaining aspect ratio (will upscale if needed)
        aspect_target = width / height
        aspect_img = img.width / img.height

        if aspect_img > aspect_target:
            # Image is wider, scale by width
            new_width = width
            new_height = int(img.height * (width / img.width))
        else:
            # Image is taller, scale by height
            new_height = height
            new_width = int(img.width * (height / img.height))

        result = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # If result doesn't fill target (due to aspect ratio), pad it
        if result.size != (width, height):
            padded = Image.new('RGB', (width, height), (0, 0, 0))
            paste_x = (width - result.width) // 2
            paste_y = (height - result.height) // 2
            padded.paste(result, (paste_x, paste_y))
            result = padded
            print(f"  Method: Contain (scaled and centered with padding)")
        else:
            print(f"  Method: Contain (scaled to fit exactly)")
        print(f"  Result size: {result.size[0]}x{result.size[1]}")

    # Generate output path if not provided
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_{width}x{height}{ext}"

    # Save result
    result.save(output_path, quality=95)
    print(f"✓ Saved: {output_path}")
    print(f"  Final size: {result.size[0]}x{result.size[1]}")

    return output_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python resize_for_workflow.py <input> [width] [height] [output] [method]")
        print("")
        print("Examples:")
        print("  python resize_for_workflow.py image.png")
        print("    → Resize to 512x512 (default)")
        print("")
        print("  python resize_for_workflow.py image.png 1024")
        print("    → Resize to 1024x1024")
        print("")
        print("  python resize_for_workflow.py image.png 512 768")
        print("    → Resize to 512x768")
        print("")
        print("  python resize_for_workflow.py image.png 512 512 output.png")
        print("    → Resize to 512x512, save as output.png")
        print("")
        print("  python resize_for_workflow.py image.png 512 512 output.png cover")
        print("    → Resize with 'cover' method (crop to fill)")
        print("")
        print("Methods:")
        print("  contain - Fit inside dimensions, maintain aspect (default)")
        print("  cover   - Fill dimensions completely, crop if needed")
        print("  stretch - Stretch to exact dimensions (may distort)")
        print("  pad     - Fit inside with black borders")
        print("")
        print("Common sizes:")
        print("  512x512   - SD 1.5 (default)")
        print("  1024x1024 - SDXL")
        print("  768x768   - SD 2.x")
        sys.exit(1)

    input_path = sys.argv[1]

    # Parse arguments
    if len(sys.argv) >= 3:
        width = int(sys.argv[2])
        height = int(sys.argv[3]) if len(sys.argv) >= 4 else width  # Square if only width given
    else:
        width = 512
        height = 512

    output_path = sys.argv[4] if len(sys.argv) >= 5 else None
    method = sys.argv[5] if len(sys.argv) >= 6 else "contain"

    # Validate input
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found!")
        sys.exit(1)

    if method not in ["contain", "cover", "stretch", "pad"]:
        print(f"Error: Unknown method '{method}'")
        print("Valid methods: contain, cover, stretch, pad")
        sys.exit(1)

    # Resize
    print("=" * 60)
    print("IMAGE RESIZE FOR COMFYUI")
    print("=" * 60)
    resize_image(input_path, width, height, output_path, method)
    print("=" * 60)
    print("Done!")
    print("")


if __name__ == "__main__":
    main()
