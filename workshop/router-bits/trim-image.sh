#!/usr/bin/env bash
# Crop and resize router bit images for the inventory page.
# Uses sips (macOS built-in) — no dependencies required.
#
# Usage:
#   ./trim-image.sh bit-images/FILE.jpg                          # resize only
#   ./trim-image.sh --crop-bottom 10 bit-images/FILE.jpg         # crop 10% off bottom, then resize
#   ./trim-image.sh --box T,L,W,H bit-images/FILE.jpg            # crop to pixel bounding box, then resize
#   ./trim-image.sh --dry-run bit-images/*.jpg                    # preview only
#
# --crop-bottom: removes a percentage from the bottom (quick mode for captions)
# --box T,L,W,H: crops to an exact bounding box in pixels (top, left, width, height)
#                 Use this when you know the exact region to keep.
set -euo pipefail

MAX=700
DRY_RUN=false
CROP_BOTTOM=0
BOX=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --crop-bottom)
      CROP_BOTTOM="$2"
      shift 2
      ;;
    --box)
      BOX="$2"
      shift 2
      ;;
    *)
      break
      ;;
  esac
done

if [[ $# -eq 0 ]]; then
  echo "Usage: $0 [--dry-run] [--crop-bottom PERCENT | --box T,L,W,H] <image> [image...]"
  exit 1
fi

for img in "$@"; do
  if [[ ! -f "$img" ]]; then
    echo "skip: $img (not found)"
    continue
  fi

  w=$(sips -g pixelWidth "$img" 2>/dev/null | awk '/pixelWidth/{print $2}')
  h=$(sips -g pixelHeight "$img" 2>/dev/null | awk '/pixelHeight/{print $2}')
  orig="${w}x${h}"

  # Bounding box crop (precise pixel region)
  if [[ -n "$BOX" ]]; then
    IFS=',' read -r box_t box_l box_w box_h <<< "$BOX"

    if $DRY_RUN; then
      echo "box:  ${orig} -> ${box_w}x${box_h} (at ${box_t},${box_l})  $img (dry run)"
    else
      sips --cropToHeightWidth "$box_h" "$box_w" --cropOffset "$box_t" "$box_l" "$img" >/dev/null 2>&1
      w=$box_w
      h=$box_h
    fi

  # Bottom percentage crop
  elif [[ "$CROP_BOTTOM" -gt 0 ]]; then
    crop_px=$(( h * CROP_BOTTOM / 100 ))
    new_h=$(( h - crop_px ))

    if $DRY_RUN; then
      echo "crop: ${orig} -> ${w}x${new_h} (remove bottom ${CROP_BOTTOM}%)  $img (dry run)"
    else
      sips --cropToHeightWidth "$new_h" "$w" "$img" >/dev/null 2>&1
      h=$new_h
    fi
  fi

  # Resize if larger than MAX
  if [[ "$w" -le "$MAX" && "$h" -le "$MAX" ]]; then
    if [[ -n "$BOX" || "$CROP_BOTTOM" -gt 0 ]] && [[ "$DRY_RUN" == "false" ]]; then
      echo "crop: ${orig} -> ${w}x${h}  $img"
    else
      echo "ok:   ${w}x${h}  $img"
    fi
    continue
  fi

  if $DRY_RUN; then
    echo "trim: ${w}x${h} -> fit ${MAX}x${MAX}  $img (dry run)"
  else
    sips --resampleHeightWidthMax "$MAX" "$img" >/dev/null 2>&1
    nw=$(sips -g pixelWidth "$img" 2>/dev/null | awk '/pixelWidth/{print $2}')
    nh=$(sips -g pixelHeight "$img" 2>/dev/null | awk '/pixelHeight/{print $2}')
    echo "trim: ${orig} -> ${nw}x${nh}  $img"
  fi
done
