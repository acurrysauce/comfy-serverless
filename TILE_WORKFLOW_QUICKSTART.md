# Tile Transition Workflow - Quick Start Guide

## Overview

This automated workflow helps you create seamless transition tiles between different terrain types (grass, stone, etc.) in FFT style.

**The Magic:** Python script handles grid assembly and mask generation automatically. You just generate tiles and inpaint!

---

## Complete Workflow

### Step 1: Generate Base Tiles

**Load workflow:** `workflows/tile_transition_generator.json`

This workflow generates two base tiles:
- **Grass tile** (top section)
- **Stone brick tile** (bottom section, uses ControlNet with tmp.png)

**What to do:**
1. Open ComfyUI
2. Load the workflow (Drag JSON file onto ComfyUI window)
3. Make sure you have:
   - SD model loaded (SDXL or SD 1.5)
   - ControlNet model: `control_v11f1e_sd15_tile.pth` (for SD1.5)
   - tmp.png in your ComfyUI input folder
4. **Generate!**
5. You'll get two files:
   - `grass_tile_00001_.png`
   - `stone_tile_00001_.png`

**Tips:**
- Change the seed in KSampler nodes for different variations
- Adjust prompts if you want different styles
- Generate multiple variations and pick the best

---

### Step 2: Prepare Grid & Masks (Automated!)

**Run Python script:**

```bash
cd /home/acurry/comfy-serverless

python scripts/prepare_tile_grid.py \
    /path/to/grass_tile_00001_.png \
    /path/to/stone_tile_00001_.png \
    ./tile_grid_output/
```

**What this does:**
- ✅ Creates 2x2 grid automatically
- ✅ Generates vertical seam mask
- ✅ Generates horizontal seam mask
- ✅ Generates combined seam mask
- ✅ Saves everything in `tile_grid_output/`

**Output files:**
```
tile_grid_output/
├── grid.png              - 2x2 tile arrangement
├── mask_vertical.png     - Mask for vertical seam
├── mask_horizontal.png   - Mask for horizontal seam
└── mask_combined.png     - Both seams (for single-pass)
```

**Optional: Adjust seam width**

Default is 128 pixels. For wider/narrower seams:
```bash
python scripts/prepare_tile_grid.py grass.png stone.png ./output/ 64
#                                                          ^^
#                                                    seam width in pixels
```

---

### Step 3: Inpaint Seams in ComfyUI

**Load workflow:** `workflows/tile_inpainting.json`

**What to do:**
1. Load the workflow in ComfyUI
2. Update the "LoadImage" nodes:
   - Node 1: Point to `tile_grid_output/grid.png`
   - Node 2: Point to `tile_grid_output/mask_vertical.png`
3. **Generate!**
4. You'll get `grid_inpainted_00001_.png` with vertical seam blended

**Optional: Inpaint horizontal seam too**

If you want both seams blended:
- Save the result from step 3
- Change Node 1 to load the inpainted result
- Change Node 2 to load `mask_horizontal.png`
- Generate again

**Or use single-pass:**
- Use `mask_combined.png` instead
- One generation blends both seams at once
- Faster but sometimes less control

---

### Step 4: Extract Final Tiles

**Manual method** (for now):

Open `grid_inpainted_00001_.png` in image editor:

1. **Pure grass tile:**
   - Crop: X=0-512, Y=0-512
   - Save as `grass_pure.png`

2. **Grass-to-stone transition (vertical):**
   - Crop: X=384-896, Y=0-512
   - (512px wide, centered on seam at X=512)
   - Save as `grass_stone_transition.png`

3. **Pure stone tile:**
   - Crop: X=512-1024, Y=0-512
   - Save as `stone_pure.png`

4. **Optional: Horizontal transition:**
   - Crop: X=0-512, Y=384-896
   - Save as `grass_stone_h_transition.png`

**Automated method** (future enhancement):

I can write a script for this too if needed!

---

## Complete Example Run

```bash
# Step 1: Generate tiles in ComfyUI
# (Use tile_transition_generator.json)
# Results: grass_tile_00001_.png, stone_tile_00001_.png

# Step 2: Prepare grid
cd /home/acurry/comfy-serverless
python scripts/prepare_tile_grid.py \
    ~/ComfyUI/output/grass_tile_00001_.png \
    ~/ComfyUI/output/stone_tile_00001_.png \
    ./my_tiles/

# Output:
#   ✓ Created grid: my_tiles/grid.png
#   ✓ Created vertical seam mask: my_tiles/mask_vertical.png
#   ✓ Created horizontal seam mask: my_tiles/mask_horizontal.png
#   ✓ Created combined seam mask: my_tiles/mask_combined.png

# Step 3: Copy files to ComfyUI input folder
cp my_tiles/grid.png ~/ComfyUI/input/
cp my_tiles/mask_vertical.png ~/ComfyUI/input/

# Step 4: Load tile_inpainting.json in ComfyUI and generate!
# Result: grid_inpainted_00001_.png

# Step 5: Extract tiles in image editor or wait for extraction script
```

---

## Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'PIL'"

Install Pillow:
```bash
pip install Pillow
```

### Problem: Tiles aren't seamless with themselves

The base tiles need to be seamless first. Options:
1. Use seamless/tiling nodes in generation workflow
2. Use texture-synthesis tool on base tiles
3. Generate at higher resolution with "seamless tile" in prompts

### Problem: Inpainted seam looks wrong / changes tile types

Adjust denoise in KSampler (Node 8):
- **Lower (0.5-0.6):** Less change, subtle blend
- **Higher (0.8-0.9):** More creative, stronger blend
- Default: 0.7

### Problem: Seam is still visible

Try:
1. Wider seam mask (re-run script with 192 or 256 instead of 128)
2. Multiple inpaint passes
3. Stronger prompts emphasizing "seamless, no edge, continuous"

### Problem: Pixel art style is lost

After inpainting, post-process:
```bash
# Reduce to 16 colors
convert grid_inpainted.png -colors 16 -dither FloydSteinberg output.png

# Optional: Pixelate effect
convert output.png -scale 50% -scale 200% final.png
```

---

## Next Steps

### Add More Tile Types

Want dirt, water, lava, etc.?

1. Generate new base tiles (modify prompts in tile_transition_generator.json)
2. Run prepare_tile_grid.py with different combinations:
   - Grass + Dirt
   - Dirt + Water
   - Stone + Lava
   - etc.
3. Build up your tile library!

### Automate Everything

Once you validate this works:
- Script can be enhanced to loop through all tile pairs
- Batch generate entire tileset
- Auto-extract final tiles
- One command = complete tileset!

### Future: 3x3 or 4x4 Grids

For more complex transitions (3-way corners, 4-way intersections):
- Modify script to handle larger grids
- Generate masks for all seams
- More tile combinations in one pass

---

## Files Reference

```
comfy-serverless/
├── workflows/
│   ├── tile_transition_generator.json  - Generate base tiles
│   └── tile_inpainting.json           - Inpaint seams
├── scripts/
│   └── prepare_tile_grid.py           - Grid & mask automation
├── local-setup/
│   └── samples/
│       └── tmp.png                    - Stone reference texture
└── TILE_WORKFLOW_QUICKSTART.md        - This file
```

---

## Pixel Art Strategy Recap

**The Problem:** SD doesn't generate good pixel art natively

**The Solution:**
1. Generate at normal resolution (512x512)
2. Use prompts: "pixel art, tactical rpg, FFT style, flat colors, low detail"
3. Use ControlNet with FFT reference (tmp.png) to maintain style
4. **Post-process:** Reduce to 16 colors + optional pixelation
5. Result: FFT-style textures from modern SD

**Key insight:** Generate "simplified, flat color" textures, then post-process to create pixel art aesthetic. Don't fight SD's nature!

---

## Questions?

If something doesn't work:
1. Check file paths in LoadImage nodes
2. Verify SD model is loaded
3. Check ControlNet model is available
4. Try adjusting denoise strength
5. Generate multiple variations with different seeds

Good luck! You're building a texture synthesis pipeline! 🎮
