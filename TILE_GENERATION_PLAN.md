# Procedural Tile Generation with Seam Inpainting - Implementation Plan

## Overview
Create a ComfyUI workflow that generates large seamless texture maps by:
1. Generating individual tiles (grass/stone) with different seeds for variation
2. Compositing tiles together into a grid
3. Inpainting seams between adjacent tiles to create seamless transitions

## Current State
We have a working workflow (`stone_and_grass_final.json`) that generates:
- Stone texture (cropped 384x384 → upscaled to 1024x1024)
- Grass texture (1024x1024 with hand-painted LoRA)

Both use SDXL base model with different LoRAs and prompts.

---

## Phase 1: Single Tile Generation with Variable Seeds ✓ (CURRENT)
**Goal:** Ensure we can generate multiple variations of grass and stone tiles

**Status:** ✓ Complete - we have `stone_and_grass_final.json`

**Workflow:**
- Input: Tile type (grass/stone), seed
- Output: Single 1024x1024 tile

**Test:** Generate 3 grass tiles with seeds 42, 100, 200 - verify they look different

---

## Phase 2: Multi-Tile Generation (No Compositing)
**Goal:** Generate multiple tiles in a single workflow run

**What to Build:**
1. Duplicate the grass generation nodes 2-3 times
2. Each duplicate uses a different seed (e.g., 42, 100, 200)
3. Save each tile separately (grass_tile_0, grass_tile_1, grass_tile_2)

**Changes to Workflow:**
- Add nodes 19-27: Second grass tile (seed 100)
- Add nodes 28-36: Third grass tile (seed 200)
- All use same LoRA, prompts, just different seeds

**Test Criteria:**
- Run workflow once
- Get 3 grass tiles + 1 stone tile (4 total images)
- Verify grass tiles look different from each other
- All tiles are 1024x1024

**Success State:** Workflow generates multiple varied tiles in one run

---

## Phase 3: Simple 2x1 Horizontal Composite (No Inpainting)
**Goal:** Place two tiles side-by-side without blending

**What to Build:**
1. Generate 2 tiles (grass_0 and grass_1)
2. Use `ImageComposite` or similar node to place them horizontally
3. Output: Single 2048x1024 image with visible seam

**New Nodes Needed:**
- `ImageComposite` or `ImageBatch` + custom positioning
- May need to research ComfyUI's image composition nodes

**Changes to Workflow:**
- After generating grass_tile_0 and grass_tile_1
- Add composition node that places them at x=0 and x=1024
- Save composite as `composite_2x1_no_blend`

**Test Criteria:**
- Output is 2048x1024
- Left half is grass_tile_0
- Right half is grass_tile_1
- Visible seam in the middle (expected)

**Success State:** Can composite multiple tiles into larger image

---

## Phase 4: 2x1 Composite with Seam Inpainting
**Goal:** Blend the seam between two horizontal tiles

**What to Build:**
1. Take the 2x1 composite from Phase 3
2. Create a vertical mask over the seam (e.g., 128px wide stripe at x=960-1088)
3. Use inpainting to blend the seam
4. Output: 2048x1024 image with seamless transition

**New Nodes Needed:**
- Mask generation (create vertical stripe mask)
- `VAEEncode` (encode composite to latent)
- `SetLatentNoiseMask` (apply mask to latent)
- `KSampler` with denoise ~0.5-0.7 for inpainting
- Positive/negative prompts for the inpaint area

**Inpainting Strategy:**
- Mask: Vertical stripe covering the seam area
- Prompt: "seamless grass texture transition, blended grass"
- Denoise: 0.5-0.7 (preserve most of the image, only blend the seam)
- Should see left and right tiles, but no visible line between them

**Test Criteria:**
- Output is 2048x1024
- No visible seam between tiles
- Tiles still look distinct (different patterns) but blend smoothly
- Edge areas are preserved (only middle stripe was inpainted)

**Success State:** Can generate seamless transitions between two tiles

---

## Phase 5: 2x2 Grid with Cross Inpainting
**Goal:** Composite 4 tiles (2x2) and inpaint both horizontal and vertical seams

**What to Build:**
1. Generate 4 tiles: grass_0, grass_1, stone_0, stone_1
2. Composite into 2x2 grid:
   ```
   [grass_0] [grass_1]
   [stone_0] [stone_1]
   ```
3. Inpaint vertical seam (between columns)
4. Inpaint horizontal seam (between rows)
5. Output: 2048x2048 seamless texture

**Challenges:**
- Need to inpaint seams in sequence (vertical first, then horizontal, or vice versa)
- Cross-junction at center needs special attention
- Different terrain types (grass-to-stone) need appropriate prompts

**Inpainting Sequence:**
1. Composite all 4 tiles → 2048x2048 base
2. Inpaint vertical seam at x=1024 (full height)
3. Inpaint horizontal seam at y=1024 (full width)
4. Optional: Inpaint center cross area where seams intersect

**Prompt Strategy for Mixed Terrain:**
- For grass-to-grass seam: "seamless grass texture transition"
- For stone-to-stone seam: "seamless stone texture transition"
- For grass-to-stone seam: "grass and stone transition, natural boundary"

**Test Criteria:**
- Output is 2048x2048
- 4 distinct quadrants visible
- No visible seams (horizontal or vertical)
- Grass-to-stone transition looks natural

**Success State:** Can create seamless 2x2 grid with mixed terrain types

---

## Phase 6: Parameterized Grid Generator
**Goal:** Accept arbitrary grid configuration and generate full texture

**What to Build:**
1. Input: Grid definition like `[['G','G','S'],['S','G','G'],['G','S','S']]`
2. For each cell, generate appropriate tile with unique seed
3. Composite all tiles
4. Inpaint all seams (vertical first, then horizontal)
5. Output: Large seamless texture

**This Phase Requires:**
- Either: Custom ComfyUI node (Python) to parse grid and generate workflow dynamically
- Or: External script that generates the workflow JSON based on grid input

**Likely Implementation:**
- Python script: `generate_tile_workflow.py`
- Input: Grid configuration (JSON or text file)
- Output: ComfyUI workflow JSON
- User runs the generated workflow

**Example Usage:**
```bash
python generate_tile_workflow.py --grid "GGS,SGG,GSS" --output tile_workflow.json
python send-to-runpod.py tile_workflow.json ./outputs
```

**Test Criteria:**
- Generate a 3x3 grid with mixed grass/stone
- Verify all seams are blended
- Verify tiles have variation (different seeds)
- Output is correct size (3072x3072 for 3x3 with 1024px tiles)

**Success State:** Can generate arbitrary-sized seamless tile maps

---

## Phase 7: Optimization & Advanced Features
**Goal:** Improve quality, add features

**Potential Enhancements:**
1. **Tile size variation:** Support 512x512, 1024x1024, 2048x2048 tiles
2. **More terrain types:** Add water, dirt, sand, etc.
3. **Edge blending modes:** Different inpainting strategies for different terrain combos
4. **Seam width control:** Make inpaint mask width configurable
5. **Batch processing:** Generate multiple map variations in one run
6. **Tiling check:** Ensure final output tiles seamlessly when repeated

**Lower Priority Features:**
- Normal map generation
- Height map generation
- Export to game-ready formats
- Integration with existing FFT tilemap tools

---

## Technical Notes

### ComfyUI Nodes to Research
- **Image Composition:** How to place images at specific coordinates
- **Mask Generation:** Create rectangular/stripe masks programmatically
- **Inpainting:** VAEEncode → SetLatentNoiseMask → KSampler workflow
- **Batch Processing:** Generate multiple variations efficiently

### Inpainting Parameters
- **Denoise strength:** 0.5-0.7 (too low = visible seam, too high = destroys original tiles)
- **Mask blur/feather:** Probably want 10-20px feather for smooth transition
- **Steps:** 20-30 should be enough for small inpaint areas
- **CFG:** 7-8 (same as generation)

### Potential Issues
1. **Seam visibility:** May need to tune denoise/mask width
2. **Pattern repetition:** Same seed = identical tiles (need seed variation)
3. **Memory:** Large grids may hit VRAM limits (need tiled processing)
4. **Prompt bleeding:** Inpainting might affect areas outside mask (test mask feathering)

---

## Questions for Discussion

1. **Tile size:** Should we stick with 1024x1024 or make it configurable?
2. **Seam width:** How wide should the inpaint mask be? (64px? 128px? 256px?)
3. **Inpainting order:** Does it matter if we do vertical seams first vs horizontal?
4. **Terrain transitions:** Do we need custom prompts for each terrain pair (G→S, G→G, S→S)?
5. **Phase 6 implementation:** Custom ComfyUI node or external workflow generator script?
6. **Stone tile cropping:** Should Phase 2+ continue using the 384→1024 crop/upscale for stone, or generate at 1024 directly?

---

## Next Steps

1. **Review this plan** - discuss and refine approach
2. **Phase 2:** Add multi-tile generation to existing workflow
3. **Test Phase 2:** Verify we get varied tiles
4. **Research:** ComfyUI image composition and masking nodes
5. **Phase 3:** Implement simple compositing
6. **Continue through phases...**
