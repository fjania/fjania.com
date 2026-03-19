---
name: add-bit
description: Add a router bit to the inventory by SKU — resolves vendor, fetches specs and image, creates a YAML data file.
allowed-tools: Read, Write, Bash, Grep, Glob, WebFetch, WebSearch, Skill
argument-hint: <SKU> [--status backorder|shipped|ordered] [--status-date DATE]
---

# Add Router Bit by SKU

Given a product SKU, resolve the vendor and product page, extract specs, fetch a clean image, and create a YAML data file in the Astro content collection.

## Arguments

`$ARGUMENTS` should contain:
1. The SKU (required) — will be normalized to uppercase
2. `--status backorder|shipped|ordered` (optional) — sets the order status
3. `--status-date DATE` (optional) — date for the status stamp (e.g. `2026-03-15`)

## Step 1: Parse arguments

Normalize the SKU to uppercase. Extract optional `--status` and `--status-date` values.

## Step 2: Check for duplicates

Check if a YAML file already exists in `workshop/src/content/bits/` for this SKU. If the bit already exists, report it and stop — do not add a duplicate.

## Step 3: Resolve vendor and product URL

Determine the vendor from the SKU pattern and find the product page:

| SKU pattern | Vendor | How to find product page |
|---|---|---|
| Starts with `US` | Woodpeckers | WebFetch `https://woodpeck.com/catalogsearch/result/?q={SKU}` and find the product link in the results |
| Numeric only (e.g. `2702`) | Whiteside | URL is `https://whitesiderouterbits.com/products/{SKU}` |
| Other | Bits&Bits | Search `https://www.bitsandbits.com` — image filename convention is `W-{SKU}.jpg` |

If the SKU doesn't match any pattern, WebSearch the approved domains (`woodpeck.com`, `bitsandbits.com`, `whitesiderouterbits.com`) for the SKU. If still ambiguous, ask the user.

**Never use Amazon.** Only use approved sources per CLAUDE.md.

## Step 4: Fetch and parse the product page

WebFetch the product URL. Extract these specs from the page content:

- **Product name** — the main product title
- **Brand** — Woodpeckers, Whiteside, or Bits&Bits
- **Bit type** — see Step 5
- **Shank diameter** — typically 1/4" or 1/2"
- **Diameter** (cutting diameter)
- **Cut length**
- **Number of flutes**
- **Max RPM** (if listed)

## Step 5: Determine bit type

Use both SKU suffix conventions and product name keywords to classify the bit:

**SKU suffix → type mapping:**
| Suffix | Type |
|---|---|
| CSP, PLT | pattern |
| FT, FTC | flush-trim |
| RO | roundover |
| C, CM | compression |
| TD, TU | spiral |
| VG, FGV | vgroove |
| CH | chamfer |
| BD | bowl |
| BNU | ballnose |
| JG | groove |
| SF | spoilboard |
| RBT | rabbeting |

**Product name keywords** (fallback): "pattern", "flush trim", "roundover", "compression", "spiral", "v-groove", "chamfer", "bowl", "ball nose", "groove", "spoilboard", "rabbet"

If the type is ambiguous after checking both, ask the user.

## Step 6: Fetch the product image

Invoke the fetch-bit-image skill to download and trim the product image:

```
/fetch-bit-image {product-url} {SKU}.jpg
```

This chains into trim-bit-image automatically.

## Step 7: Create the YAML file

Determine the filename:
- Woodpeckers (starts with US or U5): `{SKU}.yml`
- Whiteside: `W-{SKU}.yml`
- CMT: `CMT_{SKU}.yml` (replace spaces with underscores)

Create `workshop/src/content/bits/{filename}` with this structure:

```yaml
model: {SKU}
name: "{product name}"
types:
  - {type}
brand: {wp|ws|cmt}
shank: '{shank}"'
max_rpm: {rpm or null}
image: {SKU}.jpg
url: "{product-url}"
qty: 1
status: {status or in-stock}
status_date: {date or null}
specs:
  - label: Diameter
    value: '{value}"'
  - label: Cut Length
    value: '{value}"'
```

Match the format of existing YAML files in `workshop/src/content/bits/`. Quote strings that contain special YAML characters.

## Step 8: Copy the image to public/

Copy the trimmed image to `workshop/public/bit-images/{SKU}.jpg`.

## Step 9: Show result

Display the YAML file content and the trimmed image for the user to verify. Report what was added.

Do NOT commit, push, or deploy — let the user review first.
