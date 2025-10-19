# Automated Tile Transition Workflow
## Grass ↔ Stone Brick Floor

### Goal
Create seamless transition tiles between grass and stone brick floor textures in FFT style using an automated ComfyUI workflow.

---

## Tile Types

### 1. Grass
**Description:** FFT-style tactical RPG grass texture
- Green, simple, low-detail
- Pixel art aesthetic
- Limited color palette

### 2. Stone Brick Floor
**Reference:** `local-setup/samples/tmp.png`
- Brown/tan stone blocks
- Darker mortar/grout lines
- Block pattern texture
- FFT style

---

## Workflow Overview

```
Step 1: Generate Base Tiles
    ↓
Step 2: Assemble 2x2 Grid
    [Grass]  [Stone]
    [Grass]  [Stone]
    ↓
Step 3: Create Seam Masks
    - Vertical seam between grass and stone
    - Horizontal seam between top and bottom
    ↓
Step 4: Inpaint Seams
    ↓
Step 5: Extract 4 Tiles
    - grass_pure
    - grass_to_stone (transition)
    - stone_pure
    - stone_to_grass (transition)
```

---

## ComfyUI Workflow Steps

### **Step 1: Generate Base Tiles**

**Option A: Use ControlNet with tmp.png reference**

Nodes needed:
```
[Load Image: tmp.png] → [ControlNet Preprocessor: Tile/Reference]
    ↓
[Load Checkpoint: SD 1.5]
    ↓
[CLIP Text Encode Positive]:
    "stone brick floor texture, tactical rpg, PSX style,
     pixel art, brown stone blocks, simple, flat colors"

[CLIP Text Encode Negative]:
    "photorealistic, detailed, 3d, complex, gradient, modern"
    ↓
[ControlNet Apply: strength 0.7-0.9]
    ↓
[KSampler: steps 20-30, cfg 7]
    ↓
[VAE Decode] → Stone Tile (512x512)
```

For grass:
```
[Empty Latent: 512x512]
    ↓
[CLIP Text Encode]:
    "grass texture, tactical rpg, FFT style, pixel art,
     simple green grass, low detail, flat colors, PSX graphics"
    ↓
[KSampler]
    ↓
[VAE Decode] → Grass Tile (512x512)
```

**Option B: Simple generation without ControlNet**

Just use text prompts for both, but results may vary more from FFT style.

---

### **Step 2: Assemble 2x2 Grid**

**Manual Method (Start Here):**

In an image editor (GIMP, Photoshop, etc.):
1. Create 1024x1024 canvas
2. Place tiles:
   ```
   Top-left (0,0):     Grass tile
   Top-right (512,0):  Stone tile
   Bottom-left (0,512): Grass tile
   Bottom-right (512,512): Stone tile
   ```
3. Save as `grid_input.png`

**ComfyUI Method (For Automation Later):**

Custom node or workflow:
```
[Load Image: grass.png]
[Load Image: stone.png]
    ↓
[Image Batch] or [Grid Combiner Node]
    Layout: 2x2
    Arrangement: [grass, stone, grass, stone]
    ↓
Output: 1024x1024 grid
```

---

### **Step 3: Create Seam Masks**

We need to inpaint:
1. **Vertical seam** (between grass and stone columns)
2. **Horizontal seam** (between top and bottom rows)

**Mask Specifications:**

**Vertical Seam Mask:**
- Position: X = 512 (center of image)
- Width: 64-128 pixels (32-64px on each side)
- Height: Full height (1024px)
- White (255) in seam area, Black (0) elsewhere

**Horizontal Seam Mask:**
- Position: Y = 512 (center of image)
- Width: Full width (1024px)
- Height: 64-128 pixels (32-64px on each side)
- White in seam area, Black elsewhere

**Creating Masks:**

**Method A: Image Editor (Manual)**
1. Create new 1024x1024 image, fill with black
2. For vertical seam:
   - Select rectangle: X=480 to X=544 (64px wide centered on 512)
   - Fill with white
   - Save as `mask_vertical.png`
3. For horizontal seam:
   - New black image
   - Select rectangle: Y=480 to Y=544
   - Fill with white
   - Save as `mask_horizontal.png`

**Method B: ComfyUI Mask Nodes**
```
[Empty Image: 1024x1024, black]
    ↓
[Draw Mask Node]:
    - Rectangle mode
    - X: 480, Y: 0, Width: 64, Height: 1024
    - Fill: White
    ↓
Save as mask_vertical

[Empty Image: 1024x1024, black]
    ↓
[Draw Mask Node]:
    - Rectangle mode
    - X: 0, Y: 480, Width: 1024, Height: 64
    - Fill: White
    ↓
Save as mask_horizontal
```

---

### **Step 4: Inpaint Seams**

**First Inpaint: Vertical Seam**

```
[Load Image: grid_input.png]
[Load Mask: mask_vertical.png]
    ↓
[VAE Encode]
    ↓
[CLIP Text Encode Positive]:
    "seamless transition, grass to stone brick floor,
     blended edge, continuous texture, tactical rpg,
     pixel art, no hard line"

[CLIP Text Encode Negative]:
    "hard edge, visible seam, line, border, gap,
     disconnected, photorealistic"
    ↓
[Load Inpaint Model] (or use regular model with InpaintModelConditioning)
    ↓
[KSampler Inpaint]:
    - Denoise: 0.6-0.8 (experiment!)
    - Steps: 25-35
    - CFG: 7-8
    ↓
[VAE Decode] → grid_with_vertical_blend.png
```

**Second Inpaint: Horizontal Seam**

```
[Load Image: grid_with_vertical_blend.png]
[Load Mask: mask_horizontal.png]
    ↓
[VAE Encode]
    ↓
[CLIP Text Encode Positive]:
    "seamless continuation, smooth blend,
     continuous texture, no seam"

[CLIP Text Encode Negative]:
    "seam, edge, line, border, gap"
    ↓
[KSampler Inpaint]:
    - Denoise: 0.6-0.8
    - Steps: 25-35
    ↓
[VAE Decode] → grid_final_seamless.png
```

---

### **Step 5: Extract Individual Tiles**

**Manual Method:**

In image editor:
1. Open `grid_final_seamless.png`
2. Crop regions:
   - **Tile 1 (grass_pure):** X=0-512, Y=0-512
   - **Tile 2 (grass_to_stone):** X=384-896, Y=0-512 (centered on seam)
   - **Tile 3 (stone_pure):** X=512-1024, Y=0-512
   - **Tile 4 (grass_to_stone_v2):** X=0-512, Y=384-896 (different perspective)

**ComfyUI Method:**

```
[Load Image: grid_final_seamless.png]
    ↓
[Crop Image Node]:
    X: 0, Y: 0, Width: 512, Height: 512
    ↓
Save: grass_tile.png

[Crop Image Node]:
    X: 384, Y: 0, Width: 512, Height: 512
    ↓
Save: grass_stone_transition.png

[Crop Image Node]:
    X: 512, Y: 0, Width: 512, Height: 512
    ↓
Save: stone_tile.png
```

---

## Testing the Tiles

### **Test Seamless Tiling:**

1. In image editor, create 2048x2048 canvas
2. Tile `grass_tile.png` in 2x2 grid
   - Should be perfectly seamless with itself
3. Place `grass_stone_transition.png` between grass and stone areas
   - Should blend smoothly on both sides

### **Test in Game Engine:**

If you have your procedural map system:
1. Load tiles into map renderer
2. Create test map with grass and stone areas
3. Use transition tiles at boundaries
4. Check for visible seams

---

## Prompt Refinements

### **For Initial Tile Generation:**

**Grass Prompts:**
```
Positive:
"grass texture, tactical rpg, final fantasy tactics style,
 PSX graphics, pixel art, simple green grass, low detail,
 flat colors, 16bit, non-busy, clean, top-down view"

Negative:
"photorealistic, 3d, detailed, complex, busy, gradient,
 smooth, blurry, modern, high resolution"
```

**Stone Brick Prompts:**
```
Positive:
"stone brick floor texture, brown stone blocks, mortar,
 tactical rpg, FFT style, pixel art, PSX graphics,
 simple, flat colors, block pattern, low detail"

Negative:
"photorealistic, 3d render, detailed, complex, modern,
 smooth, gradient, realistic lighting"
```

### **For Inpainting Seams:**

```
Positive:
"seamless blend between grass and stone brick floor,
 smooth transition, natural edge, continuous texture,
 tactical rpg style, pixel art, no visible line"

Negative:
"hard edge, seam, border line, gap, disconnected,
 sharp boundary, cut, photorealistic"
```

---

## Post-Processing

After generating tiles, you may want to:

### **1. Reduce to 16-Color Palette**

Using ImageMagick:
```bash
convert input.png -colors 16 -dither FloydSteinberg output.png
```

Or GIMP:
- Image → Mode → Indexed
- Maximum colors: 16
- Dithering: Floyd-Steinberg

### **2. Pixelate (Optional)**

For more authentic FFT look:
```bash
# Scale down then back up with nearest-neighbor
convert input.png -scale 25% -scale 400% output.png
```

### **3. Verify Seamlessness**

Tile test script:
```bash
# Create 2x2 tiled version
convert input.png \( +clone \) +append \
        \( input.png \( +clone \) +append \) -append \
        tiled_test.png
```

Open `tiled_test.png` and look for seams.

---

## Automation Strategy

Once you confirm this works manually:

### **Phase 1: Semi-Automated**
- Generate base tiles manually (grass, stone)
- Use ComfyUI for grid assembly + inpainting
- Extract tiles manually

### **Phase 2: Fully Automated**
- Create custom ComfyUI node: "TileTransitionGenerator"
- Input: 2 base tiles
- Output: 4+ transition tiles
- Handles grid, masks, inpainting, extraction automatically

### **Phase 3: Batch Generation**
- Loop through multiple tile type pairs:
  - Grass ↔ Stone
  - Grass ↔ Dirt
  - Stone ↔ Water
  - Dirt ↔ Sand
  - etc.
- Generate entire tileset in one workflow run

---

## Expected Results

After this workflow, you should have:

**4 Tiles:**
1. `grass.png` - Pure grass, seamless with itself
2. `stone.png` - Pure stone, seamless with itself
3. `grass_stone_transition_h.png` - Horizontal transition (grass left, stone right)
4. `grass_stone_transition_v.png` - Vertical transition (grass top, stone bottom)

**Usage in Procedural Map:**
```
Map tile selection logic:
- If surrounded by grass → use grass.png
- If surrounded by stone → use stone.png
- If grass on left, stone on right → use grass_stone_transition_h.png
- If grass on top, stone on bottom → use grass_stone_transition_v.png
```

For more complex corners, you might need:
- 3-way corners (grass, stone, dirt meet)
- 4-way intersections
- This requires larger grids (3x3, 4x4)

---

## Troubleshooting

### **Problem: Inpainting changes tile types**
- **Solution:** Reduce denoise strength (try 0.5-0.6)
- Add stronger negative prompts

### **Problem: Seam still visible**
- **Solution:** Wider inpaint mask (try 128px instead of 64px)
- Multiple inpaint passes
- Adjust CFG scale

### **Problem: Tiles don't match FFT style**
- **Solution:** Use ControlNet with tmp.png reference
- Stronger style prompts ("PSX", "FFT", "16bit")
- Post-process with color reduction

### **Problem: Tiles aren't seamless with themselves**
- **Solution:** Generate base tiles using seamless/tiling methods first
- Or use texture-synthesis on base tiles before grid assembly

---

## Next Steps

1. ✅ **Generate grass base tile** in ComfyUI
2. ✅ **Generate stone base tile** using tmp.png as ControlNet reference
3. ✅ **Manually create 2x2 grid** in image editor
4. ✅ **Create seam masks** (vertical and horizontal)
5. ✅ **Run inpainting workflow** in ComfyUI
6. ✅ **Extract tiles** and test seamlessness
7. ✅ **Iterate on prompts/settings** until quality is good
8. ✅ **Automate** once process is validated

---

## Files to Create

```
/comfy-serverless/
├── tiles/
│   ├── base/
│   │   ├── grass.png (generated)
│   │   └── stone.png (generated)
│   ├── grids/
│   │   ├── grass_stone_grid.png (assembled)
│   │   └── grass_stone_grid_seamless.png (inpainted)
│   ├── masks/
│   │   ├── vertical_seam.png
│   │   └── horizontal_seam.png
│   └── final/
│       ├── grass.png
│       ├── stone.png
│       ├── grass_stone_h.png
│       └── grass_stone_v.png
```

---

## Questions Before Starting

1. **Tile resolution:** 512x512 per tile? (making grid 1024x1024)
2. **Inpaint seam width:** 64px or 128px overlap?
3. **Model:** Do you have SD 1.5 or SDXL checkpoint ready?
4. **ControlNet:** Do you have ControlNet models installed in ComfyUI?
5. **Post-process:** Should I include color reduction in workflow, or keep it separate?

Let me know and I can help you build the actual ComfyUI workflow JSON!
