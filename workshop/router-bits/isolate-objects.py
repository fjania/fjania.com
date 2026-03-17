#!/usr/bin/env python3
"""Isolate distinct objects from a white-background product image.

Uses connected component analysis to find separate objects, saves each
as its own image file, and prints metadata for each.

Usage:
    ./isolate-objects.py <image-path> [--outdir DIR] [--threshold N] [--max-y N] [--padding N]

Output (one line per object, sorted largest-first):
    <index> <outfile> <top>,<left>,<width>,<height> <pixel-area>

The output files are named object-1.jpg, object-2.jpg, etc. in the output dir.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image


def label_components(mask):
    """Label connected components in a boolean 2D array using flood-fill.

    Returns an integer array of the same shape where each connected region
    has a unique label (1, 2, 3, ...) and background is 0.
    """
    h, w = mask.shape
    labels = np.zeros((h, w), dtype=np.int32)
    current_label = 0

    for y in range(h):
        for x in range(w):
            if mask[y, x] and labels[y, x] == 0:
                current_label += 1
                # BFS flood fill
                queue = [(y, x)]
                labels[y, x] = current_label
                head = 0
                while head < len(queue):
                    cy, cx = queue[head]
                    head += 1
                    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1),
                                   (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and labels[ny, nx] == 0:
                            labels[ny, nx] = current_label
                            queue.append((ny, nx))

    return labels, current_label


def dilate(mask, radius=3):
    """Simple binary dilation to bridge small gaps."""
    h, w = mask.shape
    out = mask.copy()
    for y in range(h):
        for x in range(w):
            if mask[y, x]:
                y0 = max(0, y - radius)
                y1 = min(h, y + radius + 1)
                x0 = max(0, x - radius)
                x1 = min(w, x + radius + 1)
                out[y0:y1, x0:x1] = True
    return out


def fast_dilate(mask, radius=3):
    """Dilate using numpy rolling — much faster than per-pixel."""
    out = mask.copy()
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dy == 0 and dx == 0:
                continue
            shifted = np.roll(np.roll(mask, dy, axis=0), dx, axis=1)
            # Zero out wrapped edges
            if dy > 0:
                shifted[:dy, :] = False
            elif dy < 0:
                shifted[dy:, :] = False
            if dx > 0:
                shifted[:, :dx] = False
            elif dx < 0:
                shifted[:, dx:] = False
            out |= shifted
    return out


def isolate(image_path, outdir, threshold=252, max_y=None, padding_pct=8,
            min_area_pct=0.5):
    img = Image.open(image_path)
    rgb = img.convert("RGB")
    gray = img.convert("L")
    w, h = gray.size
    arr = np.array(gray)

    if max_y is None:
        max_y = int(h * 0.85)

    # Create binary mask: True = non-white (object pixel)
    mask = arr < threshold
    # Zero out everything below max_y (caption text area)
    mask[max_y:, :] = False

    # Dilate to bridge small gaps (screw holes, thin lines between parts)
    dilated = fast_dilate(mask, radius=5)

    # Find connected components
    sys.setrecursionlimit(w * h + 100)
    labels, num_labels = label_components(dilated)

    if num_labels == 0:
        print("error: no objects found", file=sys.stderr)
        sys.exit(1)

    # Collect bounding boxes and areas
    objects = []
    total_pixels = w * h
    for label_id in range(1, num_labels + 1):
        ys, xs = np.where(labels == label_id)
        area = len(ys)
        # Skip tiny components (noise)
        if area < total_pixels * (min_area_pct / 100):
            continue
        top = int(ys.min())
        bot = int(ys.max())
        left = int(xs.min())
        right = int(xs.max())
        objects.append((label_id, top, left, bot, right, area))

    # Sort by area descending
    objects.sort(key=lambda o: o[5], reverse=True)

    os.makedirs(outdir, exist_ok=True)

    rgb_arr = np.array(rgb)

    for i, (label_id, top, left, bot, right, area) in enumerate(objects, 1):
        bw = right - left
        bh = bot - top
        pad_x = int(bw * padding_pct / 100)
        pad_y = int(bh * padding_pct / 100)

        crop_t = max(0, top - pad_y)
        crop_l = max(0, left - pad_x)
        crop_b = min(h, bot + pad_y)
        crop_r = min(w, right + pad_x)

        # Create cropped image with white background where other objects were
        cropped = np.full((crop_b - crop_t, crop_r - crop_l, 3), 255, dtype=np.uint8)
        # Use the dilated component label to find which original pixels belong
        # to this object: any original non-white pixel that falls within the
        # dilated region of this component.
        region_labels = labels[crop_t:crop_b, crop_l:crop_r]
        region_component = region_labels == label_id
        region_orig = mask[crop_t:crop_b, crop_l:crop_r]
        object_mask = region_component & region_orig
        cropped[object_mask] = rgb_arr[crop_t:crop_b, crop_l:crop_r][object_mask]

        outfile = os.path.join(outdir, f"object-{i}.jpg")
        Image.fromarray(cropped).save(outfile, quality=95)

        crop_w = crop_r - crop_l
        crop_h = crop_b - crop_t
        print(f"{i} {outfile} {crop_t},{crop_l},{crop_w},{crop_h} {area}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", help="Path to the image")
    parser.add_argument("--outdir", default="/tmp/bit-objects",
                        help="Directory to save isolated objects (default: /tmp/bit-objects)")
    parser.add_argument("--threshold", type=int, default=252,
                        help="Grayscale threshold for 'not white' (default: 252)")
    parser.add_argument("--max-y", type=int, default=None,
                        help="Stop scanning at this row (exclude caption text)")
    parser.add_argument("--padding", type=int, default=8,
                        help="Padding around each object as %% of its size (default: 8)")
    args = parser.parse_args()
    isolate(args.image, args.outdir, threshold=args.threshold,
            max_y=args.max_y, padding_pct=args.padding)
