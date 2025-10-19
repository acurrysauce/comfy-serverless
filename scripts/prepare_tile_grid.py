#!/usr/bin/env python3
"""
Prepare Tile Grid for ComfyUI Inpainting

Takes two base tiles (grass, stone) and:
1. Assembles them into a 2x2 grid
2. Generates seam masks for inpainting
3. Saves everything ready for ComfyUI

Usage:
    python prepare_tile_grid.py grass.png stone.png output_dir/
"""

import sys
import os
from PIL import Image
import numpy as np


def create_2x2_grid(tile1_path, tile2_path, output_path):
    """
    Create 2x2 grid from two tiles:
    [tile1] [tile2]
    [tile1] [tile2]
    """
    # Load tiles
    tile1 = Image.open(tile1_path)
    tile2 = Image.open(tile2_path)

    # Get tile dimensions
    w, h = tile1.size

    # Ensure tiles are same size
    if tile1.size != tile2.size:
        print(f"Warning: Tiles are different sizes!")
        print(f"  {tile1_path}: {tile1.size}")
        print(f"  {tile2_path}: {tile2.size}")
        print(f"Resizing tile2 to match tile1...")
        tile2 = tile2.resize(tile1.size, Image.Resampling.LANCZOS)
        w, h = tile1.size

    # Create grid canvas (2x2 = width*2, height*2)
    grid = Image.new('RGB', (w * 2, h * 2))

    # Place tiles
    grid.paste(tile1, (0, 0))      # Top-left
    grid.paste(tile2, (w, 0))      # Top-right
    grid.paste(tile1, (0, h))      # Bottom-left
    grid.paste(tile2, (w, h))      # Bottom-right

    # Save grid
    grid.save(output_path)
    print(f"✓ Created grid: {output_path}")
    print(f"  Grid size: {grid.size}")

    return grid.size


def create_vertical_seam_mask(grid_width, grid_height, seam_width, output_path):
    """
    Create mask for vertical seam (between left and right columns)

    Mask is white where we want to inpaint, black elsewhere
    """
    # Create black image
    mask = Image.new('L', (grid_width, grid_height), 0)

    # Calculate seam position (center of image)
    seam_center = grid_width // 2
    seam_left = seam_center - (seam_width // 2)
    seam_right = seam_center + (seam_width // 2)

    # Draw white rectangle for seam
    pixels = mask.load()
    for y in range(grid_height):
        for x in range(seam_left, seam_right):
            pixels[x, y] = 255

    mask.save(output_path)
    print(f"✓ Created vertical seam mask: {output_path}")
    print(f"  Seam position: X={seam_left} to X={seam_right} (width: {seam_width}px)")

    return mask


def create_horizontal_seam_mask(grid_width, grid_height, seam_width, output_path):
    """
    Create mask for horizontal seam (between top and bottom rows)
    """
    # Create black image
    mask = Image.new('L', (grid_width, grid_height), 0)

    # Calculate seam position (center of image)
    seam_center = grid_height // 2
    seam_top = seam_center - (seam_width // 2)
    seam_bottom = seam_center + (seam_width // 2)

    # Draw white rectangle for seam
    pixels = mask.load()
    for y in range(seam_top, seam_bottom):
        for x in range(grid_width):
            pixels[x, y] = 255

    mask.save(output_path)
    print(f"✓ Created horizontal seam mask: {output_path}")
    print(f"  Seam position: Y={seam_top} to Y={seam_bottom} (width: {seam_width}px)")

    return mask


def create_combined_seam_mask(grid_width, grid_height, seam_width, output_path):
    """
    Create mask with both vertical and horizontal seams (cross pattern)
    This can be used for a single-pass inpaint if you want
    """
    # Create black image
    mask = Image.new('L', (grid_width, grid_height), 0)
    pixels = mask.load()

    # Vertical seam
    seam_center_x = grid_width // 2
    seam_left = seam_center_x - (seam_width // 2)
    seam_right = seam_center_x + (seam_width // 2)

    for y in range(grid_height):
        for x in range(seam_left, seam_right):
            pixels[x, y] = 255

    # Horizontal seam
    seam_center_y = grid_height // 2
    seam_top = seam_center_y - (seam_width // 2)
    seam_bottom = seam_center_y + (seam_width // 2)

    for y in range(seam_top, seam_bottom):
        for x in range(grid_width):
            pixels[x, y] = 255

    mask.save(output_path)
    print(f"✓ Created combined seam mask: {output_path}")

    return mask


def main():
    if len(sys.argv) < 3:
        print("Usage: python prepare_tile_grid.py <tile1.png> <tile2.png> [output_dir] [seam_width]")
        print("")
        print("Example:")
        print("  python prepare_tile_grid.py grass.png stone.png ./grid_output/")
        print("")
        print("Arguments:")
        print("  tile1.png     - First tile (e.g., grass)")
        print("  tile2.png     - Second tile (e.g., stone)")
        print("  output_dir    - Directory for output files (default: ./tile_grid/)")
        print("  seam_width    - Width of inpaint seam in pixels (default: 128)")
        sys.exit(1)

    tile1_path = sys.argv[1]
    tile2_path = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "./tile_grid"
    seam_width = int(sys.argv[4]) if len(sys.argv) > 4 else 128

    # Validate inputs
    if not os.path.exists(tile1_path):
        print(f"Error: {tile1_path} not found!")
        sys.exit(1)

    if not os.path.exists(tile2_path):
        print(f"Error: {tile2_path} not found!")
        sys.exit(1)

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("TILE GRID PREPARATION")
    print("=" * 60)
    print(f"Tile 1: {tile1_path}")
    print(f"Tile 2: {tile2_path}")
    print(f"Output: {output_dir}")
    print(f"Seam width: {seam_width}px")
    print("")

    # Create grid
    grid_path = os.path.join(output_dir, "grid.png")
    grid_size = create_2x2_grid(tile1_path, tile2_path, grid_path)
    print("")

    # Create masks
    mask_v_path = os.path.join(output_dir, "mask_vertical.png")
    mask_h_path = os.path.join(output_dir, "mask_horizontal.png")
    mask_combined_path = os.path.join(output_dir, "mask_combined.png")

    create_vertical_seam_mask(grid_size[0], grid_size[1], seam_width, mask_v_path)
    create_horizontal_seam_mask(grid_size[0], grid_size[1], seam_width, mask_h_path)
    create_combined_seam_mask(grid_size[0], grid_size[1], seam_width, mask_combined_path)

    print("")
    print("=" * 60)
    print("COMPLETE!")
    print("=" * 60)
    print("\nGenerated files:")
    print(f"  1. {grid_path} - 2x2 tile grid")
    print(f"  2. {mask_v_path} - Vertical seam mask")
    print(f"  3. {mask_h_path} - Horizontal seam mask")
    print(f"  4. {mask_combined_path} - Combined seam mask")
    print("\nNext steps:")
    print("  1. Load grid.png into ComfyUI")
    print("  2. Use inpaint workflow with mask_vertical.png")
    print("  3. Then inpaint result with mask_horizontal.png")
    print("  4. Or use mask_combined.png for single-pass inpainting")
    print("")


if __name__ == "__main__":
    main()
