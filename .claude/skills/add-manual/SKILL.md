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

After extraction, check image dimensions with `sips -g pixelWidth -g pixelHeight` on each image. Note which images are:
- **Usable** (reasonable dimensions, not tiny fragments): width > 100px AND height > 100px AND aspect ratio between 1:8 and 8:1
- **Fragments** (tiny icons, slivers, extreme aspect ratios): skip these when placing images

## Step 6: Map images to sections

Using the table of contents from Step 4 and the `p{page}_{index}` naming convention, map images to their corresponding manual sections. The page number in the filename tells you which section the image belongs to.

**CRITICAL: Do NOT use the Read tool on extracted images.** PDF-extracted images often have unusual dimensions or encoding that causes the vision API to return `"Could not process image"` errors. Instead, map images to sections purely by page number and the text content of that page.

## Step 7: Create the YAML data file

Write to `workshop/src/content/manuals/{slug}.yml`:

```yaml
name: Full Machine Name
manufacturer: Manufacturer Name
model: Model Number/SKU
category: machine-category
pdf: {slug}.pdf
pages: <page count>
```

Category should be kebab-case (e.g. `drill-press`, `table-saw`, `bandsaw`, `router-table`).

## Step 8: Create the HTML manual page

The manual detail page is at `workshop/src/pages/manuals/[slug].astro`. Currently this file contains hardcoded content for a single manual. When adding a new manual, you have two options:

**If this is the second manual being added:** Refactor `[slug].astro` into a routing shell and create individual content pages per manual. Create `workshop/src/pages/manuals/content/{slug}.astro` with the full HTML for this manual, and update `[slug].astro` to dynamically include the correct content component.

**If there are already multiple manuals:** Follow the existing pattern for content pages.

The HTML page should follow these conventions:

### Page structure
- Wrap in `<Base title="{name} — Owner's Manual">` with the manual-detail/manual-header/manual-content div structure
- Use the existing CSS classes from `workshop/src/styles/manuals.css`

### Content translation rules
- Translate the PDF text into clean, readable HTML — not a raw dump
- Condense verbose/repetitive safety boilerplate but preserve all technical content
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

## Step 9: Build

Run `npx astro build` from the `workshop/` directory. Confirm the new manual page appears in the build output.

## Step 10: Report

Report what was created:
- The YAML file path
- How many images were extracted and how many were usable
- The page sections that were translated
- Confirmation the build succeeded

Do NOT commit, push, or deploy — let the user review first.
