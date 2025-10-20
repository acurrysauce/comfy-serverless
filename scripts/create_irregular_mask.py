#!/usr/bin/env python3
"""
Create irregular transition masks for grass-stone boundaries
Uses noise functions to create organic, wavy edges
"""

import numpy as np
from PIL import Image
import sys

def create_wavy_horizontal_mask(width, height, center_y, transition_width, wave_amplitude, wave_frequency, output_path):
    """
    Create a mask with a wavy horizontal transition

    Args:
        width: Image width
        height: Image height
        center_y: Center position of transition (0-1, where 0.5 is middle)
        transition_width: Width of gradient transition zone in pixels
        wave_amplitude: Height of waves in pixels (how much the boundary wobbles)
        wave_frequency: Number of wave cycles across the width
        output_path: Where to save the mask
    """
    # Create coordinate grid
    x = np.linspace(0, 1, width)
    y = np.linspace(0, 1, height)
    X, Y = np.meshgrid(x, y)

    # Create wavy boundary using sine waves
    # Add multiple frequencies for more organic look
    wave1 = np.sin(X * wave_frequency * 2 * np.pi) * wave_amplitude / height
    wave2 = np.sin(X * wave_frequency * 3.7 * 2 * np.pi) * (wave_amplitude * 0.3) / height
    wave3 = np.sin(X * wave_frequency * 7.1 * 2 * np.pi) * (wave_amplitude * 0.15) / height

    boundary_offset = wave1 + wave2 + wave3

    # Create distance from wavy boundary
    distance_from_boundary = Y - (center_y + boundary_offset)

    # Convert distance to mask that peaks at boundary (white) and fades to black away from it
    # Use absolute distance so both sides fade symmetrically
    gradient_factor = (transition_width / 2) / height  # Half width on each side
    mask = 1.0 - np.abs(distance_from_boundary) / gradient_factor

    # Clamp to [0, 1]
    mask = np.clip(mask, 0, 1)

    # Convert to 8-bit grayscale
    mask_img = (mask * 255).astype(np.uint8)

    # Save
    Image.fromarray(mask_img, mode='L').save(output_path)
    print(f"Saved irregular mask to {output_path}")
    print(f"  Size: {width}x{height}")
    print(f"  Center: {center_y * height}px (y)")
    print(f"  Transition width: {transition_width}px")
    print(f"  Wave amplitude: {wave_amplitude}px")
    print(f"  Wave frequency: {wave_frequency} cycles")


def create_scattered_patches_mask(width, height, center_y, num_patches, patch_size_range, output_path):
    """
    Create a mask with scattered circular patches along the boundary
    Good for creating grass tufts in stone or vice versa
    """
    mask = np.ones((height, width), dtype=np.float32) * 0.5  # Start at 0.5 (neutral)

    # Create coordinate grid
    y_coords, x_coords = np.ogrid[:height, :width]

    # Generate random patch centers along the boundary
    np.random.seed(42)  # For reproducibility
    for _ in range(num_patches):
        # Random x position
        px = np.random.randint(0, width)
        # Y position near boundary with some randomness
        py = int(center_y * height + np.random.randn() * height * 0.1)

        # Random patch size
        radius = np.random.randint(patch_size_range[0], patch_size_range[1])

        # Random value (0 or 1 for grass/stone patch)
        value = np.random.choice([0.0, 1.0])

        # Create circular patch
        distance = np.sqrt((x_coords - px)**2 + (y_coords - py)**2)
        patch_mask = np.exp(-(distance / radius)**2)  # Soft circular falloff

        # Blend into main mask
        mask = mask * (1 - patch_mask) + value * patch_mask

    # Clamp to [0, 1]
    mask = np.clip(mask, 0, 1)

    # Convert to 8-bit grayscale
    mask_img = (mask * 255).astype(np.uint8)

    # Save
    Image.fromarray(mask_img, mode='L').save(output_path)
    print(f"Saved scattered patches mask to {output_path}")
    print(f"  Size: {width}x{height}")
    print(f"  Patches: {num_patches}")


if __name__ == "__main__":
    # Create wavy boundary mask for 2048x2048 image
    # White (255) = inpaint fully, Black (0) = keep original, Gray = blend
    # For grass (0-1024) and stone (1024-2048), boundary is at y=1024 (center_y=0.5)

    print("Creating irregular transition mask...")
    create_wavy_horizontal_mask(
        width=2048,
        height=2048,
        center_y=0.5,  # Middle of image (y=1024)
        transition_width=640,  # 640px wide transition zone
        wave_amplitude=80,  # Waves go 80px up/down
        wave_frequency=4,  # 4 complete waves across width
        output_path="irregular_horizontal_mask.png"
    )

    print("\nCreating scattered patches mask...")
    create_scattered_patches_mask(
        width=2048,
        height=2048,
        center_y=0.5,
        num_patches=150,
        patch_size_range=(20, 60),
        output_path="scattered_patches_mask.png"
    )
