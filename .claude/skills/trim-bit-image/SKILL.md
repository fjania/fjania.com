---
name: trim-bit-image
description: Visually inspect a router bit image, determine the bounding box of the bit, crop to that region, and resize for the inventory page.
allowed-tools: Read, Bash
argument-hint: <image-path>
---

# Trim Router Bit Image

Crop a router bit product image to just the bit itself, removing marketing text, captions, accessories, and excess whitespace.

## Steps

1. **Read the image** at the path provided in `$ARGUMENTS` using the Read tool to visually inspect it.

2. **Isolate objects** using `isolate-objects.py`. This uses connected component analysis to find distinct objects on the white background and saves each as a separate image:

   ```bash
   ./workshop/router-bits/isolate-objects.py <image-path>
   ```

   Output is one line per object (largest first):
   ```
   <index> <outfile> <top>,<left>,<width>,<height> <pixel-area>
   ```

   Use `--max-y N` to exclude caption text (default: 85% of image height).
   Use `--threshold N` to adjust white detection (default: 252).

3. **Visually inspect each object** using the Read tool. Identify which are router bits vs accessories (hex keys, collars, bearings, packaging). If there are multiple bits, each one will need to be processed.

4. **For each router bit object**, copy its isolated image file to the target path and resize with `trim-image.sh`:

   ```bash
   cp <object-file> <image-path>
   ./workshop/router-bits/trim-image.sh <image-path>
   ```

5. **Read the final image** to verify — the bit should be centered, isolated on white, with no other objects or text visible.

6. If isolation isn't clean (objects too close together, non-white background), adjust `--threshold` or `--padding` and re-run.
