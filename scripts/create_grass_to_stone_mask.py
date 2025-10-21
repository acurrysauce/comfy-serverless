#!/usr/bin/env python3
"""
Create a transition mask for grass-to-stone blending.

Strategy:
- Cover the entire grass side (full white)
- Add scattered organic patches on the stone side
- This allows grass to be consistent AND bleed into stone areas naturally
"""

import numpy as np
from PIL import Image
import sys


def create_grass_to_stone_mask(
    width=2048,
    height=2048,
    grass_side='top',  # 'top', 'bottom', 'left', 'right'
    patch_density=0.15,  # How much of stone side gets grass patches (0-1)
    patch_size_range=(50, 200),  # Min/max size of patches in pixels
    num_patches=20,  # Number of scattered patches
    edge_fade=100,  # Fade width at the boundary
    output_path='grass_to_stone_mask.png'
):
    """
    Create a mask for grass-to-stone transition.

    Args:
        width: Mask width
        height: Mask height
        grass_side: Which side is grass ('top', 'bottom', 'left', 'right')
        patch_density: Coverage of patches on stone side (0-1)
        patch_size_range: (min, max) patch size in pixels
        num_patches: Number of scattered patches on stone side
        edge_fade: Fade width at boundary in pixels
        output_path: Where to save the mask
    """

    # Create base mask (all black)
    mask = np.zeros((height, width), dtype=np.float32)

    # Fill grass side with white
    if grass_side == 'top':
        mask[:height//2, :] = 1.0
        grass_boundary = height // 2
        stone_area = (height//2, height, 0, width)  # y_start, y_end, x_start, x_end
        fade_direction = 'vertical'
    elif grass_side == 'bottom':
        mask[height//2:, :] = 1.0
        grass_boundary = height // 2
        stone_area = (0, height//2, 0, width)
        fade_direction = 'vertical'
    elif grass_side == 'left':
        mask[:, :width//2] = 1.0
        grass_boundary = width // 2
        stone_area = (0, height, width//2, width)
        fade_direction = 'horizontal'
    elif grass_side == 'right':
        mask[:, width//2:] = 1.0
        grass_boundary = width // 2
        stone_area = (0, height, 0, width//2)
        fade_direction = 'horizontal'
    else:
        raise ValueError(f"Invalid grass_side: {grass_side}")

    # Add scattered patches on stone side using Perlin-like noise
    y_start, y_end, x_start, x_end = stone_area

    # Create random patches using multiple frequency noise
    np.random.seed(42)  # For reproducibility

    for i in range(num_patches):
        # Random patch center
        patch_x = np.random.randint(x_start + 50, x_end - 50)
        patch_y = np.random.randint(y_start + 50, y_end - 50)

        # Random patch size
        patch_size = np.random.randint(patch_size_range[0], patch_size_range[1])

        # Create circular-ish patch with some irregularity
        for dy in range(-patch_size, patch_size):
            for dx in range(-patch_size, patch_size):
                py = patch_y + dy
                px = patch_x + dx

                # Check bounds
                if py < 0 or py >= height or px < 0 or px >= width:
                    continue

                # Distance from patch center
                dist = np.sqrt(dx**2 + dy**2)

                # Add some noise to make patch irregular
                noise = np.random.random() * 0.3
                effective_radius = patch_size * (0.6 + noise)

                if dist < effective_radius:
                    # Smooth falloff from center
                    falloff = 1.0 - (dist / effective_radius)
                    falloff = falloff ** 1.5  # Make edges softer
                    mask[py, px] = max(mask[py, px], falloff)

    # Add some additional smaller scattered spots
    num_small_spots = num_patches * 2
    for i in range(num_small_spots):
        spot_x = np.random.randint(x_start + 10, x_end - 10)
        spot_y = np.random.randint(y_start + 10, y_end - 10)
        spot_size = np.random.randint(10, 40)

        for dy in range(-spot_size, spot_size):
            for dx in range(-spot_size, spot_size):
                py = spot_y + dy
                px = spot_x + dx

                if py < 0 or py >= height or px < 0 or px >= width:
                    continue

                dist = np.sqrt(dx**2 + dy**2)
                if dist < spot_size:
                    falloff = 1.0 - (dist / spot_size)
                    falloff = falloff ** 2
                    mask[py, px] = max(mask[py, px], falloff)

    # Apply fade at the grass-stone boundary
    if fade_direction == 'vertical':
        # Vertical fade (for top/bottom grass)
        y_coords = np.arange(height)
        fade_mask = np.ones(height)

        # Fade on both sides of boundary
        fade_mask = np.where(
            np.abs(y_coords - grass_boundary) < edge_fade,
            0.5 + 0.5 * np.cos(np.abs(y_coords - grass_boundary) / edge_fade * np.pi),
            1.0
        )

        # Apply fade to each column
        mask *= fade_mask[:, np.newaxis]

    else:  # horizontal
        # Horizontal fade (for left/right grass)
        x_coords = np.arange(width)
        fade_mask = np.ones(width)

        fade_mask = np.where(
            np.abs(x_coords - grass_boundary) < edge_fade,
            0.5 + 0.5 * np.cos(np.abs(x_coords - grass_boundary) / edge_fade * np.pi),
            1.0
        )

        # Apply fade to each row
        mask *= fade_mask[np.newaxis, :]

    # Convert to 8-bit image
    mask_img = (mask * 255).astype(np.uint8)

    # Save as grayscale PNG
    img = Image.fromarray(mask_img, mode='L')
    img.save(output_path)

    print(f"Created grass-to-stone mask: {output_path}")
    print(f"  Size: {width}x{height}")
    print(f"  Grass side: {grass_side}")
    print(f"  Patches: {num_patches} large + {num_small_spots} small")
    print(f"  Edge fade: {edge_fade}px")

    return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Create grass-to-stone transition mask')
    parser.add_argument('--width', type=int, default=2048, help='Mask width')
    parser.add_argument('--height', type=int, default=2048, help='Mask height')
    parser.add_argument('--grass-side', choices=['top', 'bottom', 'left', 'right'],
                       default='top', help='Which side is grass')
    parser.add_argument('--num-patches', type=int, default=20,
                       help='Number of large patches on stone side')
    parser.add_argument('--edge-fade', type=int, default=100,
                       help='Fade width at boundary (pixels)')
    parser.add_argument('--output', type=str, default='grass_to_stone_mask.png',
                       help='Output filename')

    args = parser.parse_args()

    create_grass_to_stone_mask(
        width=args.width,
        height=args.height,
        grass_side=args.grass_side,
        num_patches=args.num_patches,
        edge_fade=args.edge_fade,
        output_path=args.output
    )
