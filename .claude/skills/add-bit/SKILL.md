---
name: add-bit
description: Add a router bit to the inventory by SKU — resolves vendor, fetches specs and image, inserts the card HTML.
allowed-tools: Read, Edit, Bash, Grep, Glob, WebFetch, WebSearch, Skill
argument-hint: <SKU> [--status backorder|shipped] [--status-date DATE]
---

# Add Router Bit by SKU

Given a product SKU, resolve the vendor and product page, extract specs, fetch a clean image, and insert a fully-formed card into the inventory HTML.

## Arguments

`$ARGUMENTS` should contain:
1. The SKU (required) — will be normalized to uppercase
2. `--status backorder|shipped` (optional) — sets the order status stamp
3. `--status-date DATE` (optional) — date for the status stamp (e.g. `2026-03-15`)

## Step 1: Parse arguments

Normalize the SKU to uppercase. Extract optional `--status` and `--status-date` values.

## Step 2: Check for duplicates

Grep `workshop/router-bits/index.html` for the SKU. If the bit already exists, report it and stop — do not add a duplicate.

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

## Step 7: Build the card HTML

Read `workshop/router-bits/index.html` and match the existing card structure exactly. A typical card looks like:

```html
<a href="{product-url}" class="card-link" target="_blank" rel="noopener">
  <div class="card">
    <span class="brand-badge badge-{WP|WS}">{WP|WS}</span>
    <img src="bit-images/{SKU}.jpg" alt="{product name}">
    <div class="card-info">
      <h3>{product name}</h3>
      <p class="specs">{shank}" shank · {diameter}" dia · {cut-length}" cut · {flutes}F</p>
    </div>
  </div>
</a>
```

- Brand badge: `WP` for Woodpeckers, `WS` for Whiteside, `BB` for Bits&Bits
- If `--status` is provided, add the status class and stamp:
  - Add `backorder` or `shipped` to the card's class list
  - Insert `<span class="order-stamp">Backorder ~DATE</span>` or `<span class="order-stamp">Shipped DATE</span>` as the first child of the card div (before the brand badge)

**Important:** Read the actual HTML first to match the exact structure, classes, and formatting currently in use. The example above is a guide — defer to what's actually in the file.

## Step 8: Insert the card

Find the correct `.type-section` by its ID (e.g. `id="rabbeting"` for rabbeting bits). Insert the new `<a class="card-link">` block before the closing `</div>` of that section's `.grid` container.

If the type section doesn't exist yet, ask the user where to add it rather than creating a new section automatically.

## Step 9: Update counts

After inserting the card:

1. **Nav count** — Find the `<span class="nav-count">` inside the nav link for this bit type and increment it by 1.
2. **Header total** — Find the total count in the page header and increment it by 1.

## Step 10: Show result

Display the final card HTML and the trimmed image for the user to verify. Report what was added and where.

Do NOT commit, push, or deploy — let the user review first.
