---
name: add-manual
description: Add a machine owner's manual — downloads the PDF, extracts text and images, translates to a readable HTML page with inline images, and builds the site.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch, WebSearch, Agent
argument-hint: <manufacturer and model, e.g. "Laguna DP20"> [optional: URL to PDF]
---

# Add Machine Owner's Manual

Given a machine name (and optionally a PDF URL), download the PDF manual, extract its text and images, translate the content into a clean readable HTML page with inline images, and register it in the Astro site.

## Arguments

`$ARGUMENTS` should contain the manufacturer and model name (e.g. "Laguna DP20", "SawStop PCS"). It may optionally include a URL to the PDF. If no URL is provided, search for the official PDF on the manufacturer's website.

## Step 1: Check for duplicates

Check if a YAML file already exists in `workshop/src/content/manuals/` for this machine (match by slug). If it exists, report it and stop.

## Step 2: Determine the slug

Create a slug from the manufacturer and model: lowercase, spaces/special chars to hyphens (e.g. `laguna-dp20`, `sawstop-pcs`).

## Step 3: Download the PDF

If no URL was provided, use WebSearch to find the official PDF on the manufacturer's website. Download with `curl -sL` to `workshop/public/manuals/{slug}.pdf`. Verify the file is a valid PDF (check with `file` command and ensure size > 100KB).

## Step 4: Extract text from the PDF

Use `pypdf` to extract all text, saving to a temp file for reference:

```python
from pypdf import PdfReader
reader = PdfReader('path/to/manual.pdf')
full_text = []
for i, page in enumerate(reader.pages):
    text = page.extract_text()
    full_text.append(f'<!-- PAGE {i+1} -->\n{text}')
with open('/tmp/{slug}-text.txt', 'w') as f:
    f.write('\n\n'.join(full_text))
```

Read the extracted text to understand:
- The table of contents (which sections are on which pages)
- All technical specifications
- All sections and their content
- Safety warnings and notes
- **Whether the manual is multilingual** — many manuals (Bosch, Festool, Mirka) contain English, Spanish, French, etc. in one PDF. Identify the English page range and only extract English content.

## Step 5: Extract images from the PDF

Extract all embedded images using `pypdf`, naming them by page and index:

```python
from pypdf import PdfReader
import os

reader = PdfReader('path/to/manual.pdf')
outdir = 'workshop/public/manuals/{slug}'
os.makedirs(outdir, exist_ok=True)

for i, page in enumerate(reader.pages):
    for j, img in enumerate(page.images):
        ext = os.path.splitext(img.name)[1].lower()
        if ext == '.jp2':
            ext = '.jpg'
        if not ext:
            ext = '.png'
        fname = f'p{i+1:02d}_{j:02d}{ext}'
        path = os.path.join(outdir, fname)
        with open(path, 'wb') as f:
            f.write(img.data)
```

### Post-extraction fixes (CRITICAL)

After extracting all images, fix two common PDF extraction issues:

**1. JPEG 2000 files with `.jpg` extension:** pypdf often extracts JP2 (JPEG 2000) images and names them `.jpg`. Browsers cannot render JP2. Detect and convert all of them:

```bash
find workshop/public/manuals/{slug} -name "*.jpg" -exec sh -c \
  'file "$1" | grep -q "JPEG 2000" && sips -s format jpeg "$1" --out "$1"' _ {} \;
```

**2. CMYK and Grayscale color spaces:** PDF images are often in CMYK (print) or Grayscale color spaces that browsers render incorrectly. Convert all non-RGB images to sRGB:

```bash
find workshop/public/manuals/{slug} -type f \( -name "*.jpg" -o -name "*.png" \) -exec sh -c \
  'space=$(sips -g space "$1" 2>/dev/null | grep space | awk "{print \$2}"); \
  [ "$space" = "CMYK" ] || [ "$space" = "Gray" ] && \
  sips -m /System/Library/ColorSync/Profiles/sRGB\ Profile.icc "$1" --out "$1"' _ {} \;
```

### Dimension check

Check image dimensions with `sips -g pixelWidth -g pixelHeight` on each image. Note which images are:
- **Usable** (reasonable dimensions, not tiny fragments): width > 100px AND height > 100px AND aspect ratio between 1:8 and 8:1
- **Fragments** (tiny icons, slivers, extreme aspect ratios): skip these when placing images

## Step 6: Download a product photo for the card image

The listing card needs a clean, color product photo — **not** a PDF-extracted image (which are often grayscale, CMYK, or low quality).

Use WebSearch to find the product page on the manufacturer's website. WebFetch the page to find the main product image URL. Download it:

```bash
curl -sL -o workshop/public/manuals/{slug}/product.jpg "<image_url>"
```

If the manufacturer's site blocks direct image downloads (403, hotlink protection, JavaScript-rendered), try the product page on rockler.com, acmetools.com, or woodcraft.com instead.

Verify the downloaded image:
- Is a valid JPEG or PNG (`file` command)
- Has reasonable dimensions (at least 300px wide, `sips`)
- Is in RGB color space (convert if needed)
- If downloaded as WebP or PNG, convert to JPEG with `sips -s format jpeg`

## Step 7: Map images to sections

Using the table of contents from Step 4 and the `p{page}_{index}` naming convention, map images to their corresponding manual sections. The page number in the filename tells you which section the image belongs to.

**CRITICAL: Do NOT use the Read tool on extracted images.** PDF-extracted images often have unusual dimensions or encoding that causes the vision API to return `"Could not process image"` errors. Instead, map images to sections purely by page number and the text content of that page.

## Step 8: Create the YAML data file

Write to `workshop/src/content/manuals/{slug}.yml`:

```yaml
name: Full Machine Name
manufacturer: Manufacturer Name
model: Model Number/SKU
category: machine-category
pdf: {slug}.pdf
pages: <page count>
image: {slug}/product.jpg
```

Category should be kebab-case (e.g. `drill-press`, `table-saw`, `bandsaw`, `router-table`).

The `image` field should always point to the downloaded product photo (`product.jpg`), not a PDF-extracted image.

## Step 9: Create the HTML manual page

The manual pages use a dynamic routing shell at `workshop/src/pages/manuals/[slug].astro` that loads individual content components from `workshop/src/pages/manuals/content/{slug}.astro`.

Create `workshop/src/pages/manuals/content/{slug}.astro` with the HTML content for this manual (no frontmatter or layout wrapper needed — the router handles that).

The HTML page should follow these conventions:

### Content translation rules
- Translate the PDF text into clean, readable HTML — not a raw dump
- Condense verbose/repetitive safety boilerplate but preserve all technical content
- For multilingual manuals, only translate the English section
- Use semantic HTML: `<h2>` for major sections, `<h3>` for subsections
- Use `<table>` for specifications and reference data
- Use `<ol>` for step-by-step procedures, `<ul>` for lists
- Use callout divs for warnings/notes:
  - `<div class="danger">` — imminent hazard, red
  - `<div class="warning">` — potential hazard, yellow
  - `<div class="note">` — informational, blue

### Image placement rules
- Reference images as `/workshop/manuals/{slug}/p{page}_{index}.{ext}`
- Only include images that passed the dimension check in Step 5
- **Every content page must include images.** If the PDF had extractable images, they must appear in the HTML. Do not write an image-free content page when images are available.
- Use `<div class="figure">` with `<figcaption>` for standalone diagrams (labeled diagrams, exploded views, wiring diagrams, charts)
- Use `<div class="image-row">` for 2-3 related images shown side by side (assembly steps, before/after, detail views)
- Place images directly after the text they illustrate
- For assembly steps, nest images inside the `<li>` they belong to
- Write descriptive alt text based on what the image should show (based on surrounding text context), not what you visually see
- Skip decorative images (logos, QR codes, cover art)

### Key sections to include
- Specifications table
- Safety (condensed)
- Main components diagram + labeled parts table
- Inventory / what's included
- Assembly steps with inline photos
- Adjustments and setup
- Control panel / interface
- Operating procedures
- Maintenance
- Troubleshooting
- Wiring diagram and exploded views (if present)
- Contact / manufacturer info

## Step 10: Build

Run `npx astro build` from the `workshop/` directory. Confirm the new manual page appears in the build output.

## Step 11: Report

Report what was created:
- The YAML file path
- How many images were extracted and how many were usable
- The page sections that were translated
- Confirmation the build succeeded

Do NOT commit, push, or deploy — let the user review first.
