---
name: fetch-bit-image
description: Fetch the cleanest product image from a router bit product page, save it, and pass it to the trim skill.
allowed-tools: Read, Bash, WebFetch, Skill
argument-hint: <product-url> <output-filename>
---

# Fetch Router Bit Image

Given a product page URL and a target filename, find the best product image (clean, white/light background, bit clearly visible) and save it ready for trimming.

## Arguments

`$ARGUMENTS` should contain:
1. The product page URL
2. The output filename (just the name, e.g. `2703.jpg` — it will be saved to `workshop/public/bit-images/`). Note: `isolate-objects.py` and `trim-image.sh` live in `workshop/router-bits/`.

## Steps

1. **Fetch the product page** using WebFetch. Ask it to extract ALL product image URLs from the page — every `img src`, `data-src`, `data-zoom-image`, or gallery/thumbnail URL that looks like a product photo. Exclude icons, logos, UI chrome, and SVGs.

2. **Deduplicate the images.** Product pages often serve the same image at multiple sizes via different cache paths or query strings. Group URLs by their base filename (the last path segment, ignoring cache/resize directories). Pick the largest version of each unique image. **Important:** After downloading each candidate, check its actual pixel dimensions with `sips -g pixelWidth -g pixelHeight` — some cache paths serve thumbnails (e.g. 75x75) even though the URL looks similar. If a candidate is tiny, try alternate cache paths for the same filename to find the full-size version.

3. **Download all unique images** to `/tmp/bit-fetch-candidates/` (create the directory first, clearing any previous contents). Name them `candidate-1.jpg`, `candidate-2.jpg`, etc.

4. **Visually inspect each candidate** using the Read tool. Score each image on these criteria (best to worst):
   - **White/plain background** with the bit clearly isolated — this is ideal
   - **Light solid-color background** with the bit isolated
   - **Lifestyle photo** showing the bit standing upright on a surface with minimal clutter
   - **In-use photo** showing the bit in a router or cutting wood — avoid these
   - **Marketing image** with text overlays, logos, or badges — avoid these

   Also prefer images where:
   - The full bit is visible (shank to cutting head)
   - The bit is the dominant subject (not a tiny element in a larger scene)
   - The image is high resolution

5. **Select the best image.** Copy it to `workshop/public/bit-images/<output-filename>`.

6. **Invoke the trim-bit-image skill** on the saved image:
   ```
   /trim-bit-image workshop/public/bit-images/<output-filename>
   ```

7. **Show the final result** by reading the trimmed image so the user can verify it.
