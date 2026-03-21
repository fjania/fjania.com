---
name: add-species
description: Add a wood species sheet — researches the species online, creates a YAML data file, finds and downloads images, and builds the site.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch, WebSearch, Agent
argument-hint: <species common name>
---

# Add Wood Species Sheet

Given a wood species common name, research its properties online, create a YAML data file, find and download reference images, and build the Astro site.

## Arguments

`$ARGUMENTS` should contain the common name of the wood species (e.g. "Bloodwood", "Zebrawood").

## Step 1: Check for duplicates

Check if a YAML file already exists in `src/content/species/` for this species (match by slug: lowercase, spaces to underscores). If it exists, report it and stop.

## Step 2: Understand the YAML structure

Read one existing species YAML (e.g. `src/content/species/purpleheart.yml`) to confirm required fields. All of these fields are required:

- `name`, `scientific`, `origin`
- `appearance`: heartwood, sapwood, grain, texture, luster
- `properties`: janka (number), density, workability, turning, gluing, finishing
- `uses` (array, ~6 items)
- `advantages` (array, ~5 items)
- `challenges` (array, ~5 items)
- `finishing_tips` (array, ~4 items)
- `buying_tips` (array, ~4 items)
- `fun_fact` (string)
- `comparisons` (array of tables with title + rows)
- `faqs` (array of q/a pairs, ~3 items)

## Step 3: Research the species

Use an Agent with WebSearch and WebFetch to gather accurate data from reliable sources (wood-database.com, woodworkerssource.com, etc.). The agent should return all fields needed for the YAML. Key requirements:

- Janka hardness must be a verified number
- Include two comparison tables (one comparing to a similar species, one showing another interesting dimension like colour over time or grades)
- Use British/Canadian spelling (colour, favour, etc.) to match existing sheets
- Data must come from real sources — do not fabricate

## Step 4: Create the YAML file

Write the YAML to **both** locations:
- `workshop/species/species/{slug}.yml` (card builder)
- `src/content/species/{slug}.yml` (Astro content collection)

The slug is: lowercase name, spaces replaced with underscores (e.g. `hard_maple`).

Match the style of existing YAML files — no quotes on simple strings, use `>` or flow style for long strings only when needed.

## Step 5: Find and download images

Find 3 images of the species from different angles/contexts:
- **Image 0 (card image — most important):** A photo of an actual board or stack of boards. This is the thumbnail shown on the species listing page. It must clearly show a physical piece of lumber — NOT a flat grain swatch/texture sample, NOT a turning blank/block, NOT a botanical illustration, NOT a room/furniture photo. The ideal style is a board photographed at an angle on a clean light/white background showing the face grain and natural colour (see existing images from The Knotty Lumber Co. as the gold standard). Product photos from lumber retailers work well.
- **Image 1:** Board, lumber stack, or finished surface from a different angle
- **Image 2:** Grain detail, end grain, or alternate view

### Image quality criteria
- Must be a photograph (not an illustration, render, or colour swatch)
- Should show the wood's actual colour and grain character
- Clean background preferred (white, light grey, or simple)
- No heavy watermarks, text overlays, or distracting elements
- No messy workshop/warehouse backgrounds with markings or chalk lines

### Where to find good images
Search for "[species name] lumber board" or "[species name] wood boards". Good sources:
- Lumber retailers: bellforestproducts.com, hearnehardwoods.com, cookwoods.com, ocoochhardwoods.com, woodworkerssource.com, irionlumber.com
- Wikimedia Commons (often has high-quality public domain wood photos)
- Specialty dealers for exotic species: cookwoods.com, exoticwoodzone.com

### Download process
1. WebSearch for the species + "lumber board photo"
2. WebFetch promising product/reference pages to extract image URLs
3. Download with `curl -sL` to `workshop/species/images/{slug}_0.jpg`, `{slug}_1.jpg`, `{slug}_2.jpg`
4. Verify each image: check file size (>5KB) and dimensions with `sips -g pixelWidth -g pixelHeight`. If an image is broken (<1KB or nil dimensions), try another source.
5. **Visually confirm every image with the Read tool** — especially image 0. If image 0 is not a clear board photo, reject it and find another.

## Step 6: Copy images to public directory

Copy all valid images to `public/species-images/` so the Astro page template picks them up.

## Step 7: Build

Run `npx astro build` from the repo root. Confirm the new species page appears in the build output (e.g. `/workshop/species/{slug}/index.html`).

## Step 8: Show result

Report what was created:
- The YAML file path and a brief summary of the data
- Which images were downloaded and their sources
- Confirmation the build succeeded

Do NOT commit, push, or deploy — let the user review first.
