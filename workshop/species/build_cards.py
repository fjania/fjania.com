#!/usr/bin/env python3
"""
Build printable wood species reference cards from YAML data files.

Usage:
    python build_cards.py                  # build all species in species/
    python build_cards.py white_oak.yml    # build one species

Each YAML file in species/ produces a self-contained HTML file with two pages:
  - Front: species info grouped into "About This Wood" + "Workshop Guide"
  - Back: photos, colour reference, FAQ
"""

import os
import sys
import glob

import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SPECIES_DIR = os.path.join(SCRIPT_DIR, "species")

# ── CSS ─────────────────────────────────────────────────────────
CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }

@page {
  size: letter;
  margin: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background: #f5f0ea;
  color: #2c1810;
  font-size: 9.5pt;
  line-height: 1.4;
  max-width: 8.5in;
  margin: 0 auto;
}

.page {
  background: #fff;
  display: flex;
  flex-direction: column;
}

/* ── Banner ── */
.banner {
  background: linear-gradient(135deg, #3B2714 0%, #5a3a1e 50%, #3B2714 100%);
  color: #F5E6D3;
  padding: 12px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.banner-text {
  text-align: left;
}
.banner h1 {
  font-size: 18pt;
  font-weight: 700;
  letter-spacing: 0.5px;
  margin-bottom: 1px;
}
.banner .subtitle {
  font-size: 9.5pt;
  opacity: 0.85;
  font-style: italic;
}
.banner-thumbs {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}
.banner-thumbs img {
  width: 52px;
  height: 52px;
  object-fit: cover;
  border-radius: 4px;
  border: 1.5px solid rgba(245, 230, 211, 0.5);
}

/* ── Stats strip ── */
.stats-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  background: #F5E6D3;
  padding: 8px 20px;
  border-bottom: 2px solid #C4973B;
}
.stat {
  text-align: center;
  padding: 2px 4px;
}
.stat .label {
  font-weight: 700;
  color: #6B4226;
  text-transform: uppercase;
  font-size: 7pt;
  letter-spacing: 0.6px;
}
.stat .value {
  color: #3B2714;
  font-weight: 600;
  font-size: 8.5pt;
}

/* ── Group header (About / Workshop) ── */
.group-header {
  font-size: 11pt;
  font-weight: 700;
  color: #3B2714;
  text-transform: uppercase;
  letter-spacing: 1px;
  padding: 8px 0 6px 0;
  border-bottom: 2.5px solid #C4973B;
  margin-bottom: 8px;
}

/* ── Two-column main layout ── */
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
  padding: 10px 16px 6px 16px;
}
.two-col > .group {
  padding: 0 12px;
}
.two-col > .group:first-child {
  border-right: 1.5px solid #e0d5c8;
  padding-left: 0;
}
.two-col > .group:last-child {
  padding-right: 0;
}

/* ── Section headings ── */
.section-title {
  font-size: 8.5pt;
  font-weight: 700;
  color: #6B4226;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1.5px solid #d8cfc2;
  padding-bottom: 2px;
  margin-bottom: 3px;
  margin-top: 8px;
}
.section-title:first-of-type,
.group-header + .section-title {
  margin-top: 0;
}

/* ── Body text ── */
.section-text {
  font-size: 8.5pt;
  line-height: 1.4;
  color: #3a2a1a;
}

/* ── Janka bar (full-width) ── */
.janka-strip {
  padding: 8px 16px;
  background: #faf6f0;
  border-top: 1px solid #e0d5c8;
  border-bottom: 1px solid #e0d5c8;
}
.janka-strip .janka-label {
  font-size: 7.5pt;
  font-weight: 700;
  color: #6B4226;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 3px;
}
.janka-bar-container {
  background: #f0e8de;
  border-radius: 5px;
  height: 18px;
  overflow: hidden;
  position: relative;
  border: 1px solid #d8cfc2;
}
.janka-bar-fill {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, #C4973B, #8B6914);
  position: relative;
}
.janka-bar-label {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 8pt;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0,0,0,0.4);
}

/* ── Comparison tables (full-width, side by side) ── */
.comparisons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  padding: 8px 16px 10px 16px;
}
.comp-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 8pt;
  margin-top: 3px;
}
.comp-table th {
  background: #3B2714;
  color: #F5E6D3;
  padding: 4px 6px;
  text-align: left;
  font-weight: 600;
  font-size: 7.5pt;
}
.comp-table td {
  padding: 3.5px 6px;
  border-bottom: 1px solid #ebe3d8;
  font-size: 8pt;
}
.comp-table tr:nth-child(even) td {
  background: #faf6f0;
}
.comp-label {
  font-size: 8pt;
  font-weight: 700;
  color: #6B4226;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}

/* ── Lists ── */
.uses-list, .tips-list, .buying-list {
  list-style: none;
  padding: 0;
  font-size: 8.5pt;
}
.uses-list li, .tips-list li, .buying-list li {
  padding: 1.5px 0 1.5px 12px;
  position: relative;
  line-height: 1.35;
}
.uses-list li::before {
  content: "\\2022";
  position: absolute;
  left: 0;
  color: #C4973B;
  font-weight: 700;
}
.tips-list li::before {
  content: "\\2022";
  position: absolute;
  left: 0;
  color: #888;
}
.buying-list li::before {
  content: "\\2022";
  position: absolute;
  left: 0;
  color: #6B4226;
}

/* ── Advantages / Challenges ── */
.adv-list, .chal-list {
  list-style: none;
  padding: 0;
  font-size: 8.5pt;
}
.adv-list li, .chal-list li {
  padding: 1.5px 0 1.5px 14px;
  position: relative;
  line-height: 1.35;
}
.adv-list li::before {
  content: "\\2713";
  position: absolute;
  left: 0;
  color: #2e7d32;
  font-weight: 700;
}
.chal-list li::before {
  content: "\\25B8";
  position: absolute;
  left: 0;
  color: #c62828;
  font-weight: 700;
}

/* ── Fun fact footer ── */
.fun-fact {
  background: #F5E6D3;
  padding: 8px 20px;
  font-size: 8.5pt;
  color: #3B2714;
  border-top: 2px solid #C4973B;
  text-align: center;
  line-height: 1.4;
  margin-top: auto;
}
.fun-fact strong {
  color: #6B4226;
}

/* ── BACK PAGE ── */
.back .banner {
  background: linear-gradient(135deg, #5a3a1e 0%, #3B2714 50%, #5a3a1e 100%);
}

/* ── Colour reference ── */
.colour-ref {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  gap: 12px;
  padding: 10px 20px;
  background: #faf6f0;
  border-bottom: 1px solid #e0d5c8;
}
.colour-item .colour-label {
  font-size: 7pt;
  font-weight: 700;
  color: #6B4226;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}
.colour-item .colour-value {
  font-size: 8.5pt;
  color: #3a2a1a;
  line-height: 1.35;
}

/* ── Photo grid ── */
.photo-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
  padding: 14px 20px;
}
.photo-card {
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #d8cfc2;
  background: #f5f0ea;
}
.photo-card img {
  width: 100%;
  height: 220px;
  object-fit: cover;
  display: block;
}
.photo-card .photo-caption {
  font-size: 7.5pt;
  text-align: center;
  padding: 5px;
  color: #6B4226;
  font-weight: 600;
  background: #F5E6D3;
}

.no-photos {
  grid-column: 1 / -1;
  text-align: center;
  padding: 50px 24px;
  color: #999;
  font-size: 10pt;
  font-style: italic;
  background: #faf6f0;
  border-radius: 6px;
  border: 2px dashed #d8cfc2;
}

/* ── FAQ section ── */
.faq-section {
  flex: 1;
  padding: 14px 20px;
}
.faq-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px 18px;
}
.faq-item {
  padding: 8px 10px;
  background: #faf6f0;
  border-radius: 4px;
  border-left: 3px solid #C4973B;
}
.faq-q {
  font-size: 9pt;
  font-weight: 700;
  color: #3B2714;
  margin-bottom: 3px;
}
.faq-a {
  font-size: 8.5pt;
  color: #5a4a3a;
  line-height: 1.4;
}

/* ── Source bar ── */
.source-bar {
  background: #3B2714;
  color: #F5E6D3;
  padding: 8px 20px;
  font-size: 7.5pt;
  text-align: center;
  opacity: 0.9;
}

/* ── Print ── */
@media print {
  body {
    background: white;
    max-width: none;
  }
  .page {
    height: 11in;
    min-height: 11in;
    max-height: 11in;
    overflow: hidden;
    page-break-after: always;
    page-break-inside: avoid;
  }
  .page:last-child {
    page-break-after: auto;
  }
  * {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
}
"""


# ── Helpers ─────────────────────────────────────────────────────

def safe_name(name):
    """Convert species name to filesystem-safe slug."""
    return name.lower().replace(" ", "_")


def find_images(species_name):
    """Find all images for a species in the images/ directory."""
    slug = safe_name(species_name)
    pattern = os.path.join(SCRIPT_DIR, "images", f"{slug}_*")
    files = sorted(glob.glob(pattern))
    return [os.path.basename(f) for f in files]


def render_list(items, cls):
    """Render a styled list."""
    lis = "".join(f"<li>{item}</li>" for item in items)
    return f'<ul class="{cls}">{lis}</ul>'


def render_table(comp):
    """Render a comparison table from a YAML comparisons entry.

    Each comp has:
      title: str
      rows: list of dicts (each dict is one data row, keys are column headers)
    """
    title = comp["title"]
    rows = comp["rows"]
    if not rows:
        return ""
    headers = list(rows[0].keys())
    th = "".join(f"<th>{h}</th>" for h in headers)
    trs = ""
    for row in rows:
        tds = "".join(f"<td>{row[h]}</td>" for h in headers)
        trs += f"<tr>{tds}</tr>\n"
    return f"""<div>
<div class="comp-label">{title}</div>
<table class="comp-table">
<tr>{th}</tr>
{trs}</table>
</div>"""


# ── Card renderer ───────────────────────────────────────────────

def render_card(sp, max_janka):
    """Render the full HTML for a species card from a parsed YAML dict."""
    name = sp["name"]
    app = sp["appearance"]
    props = sp["properties"]
    janka = props["janka"]
    janka_pct = min(100, (janka / max_janka) * 100)

    images = find_images(name)

    # ── Thumbnails for banner ──
    if images:
        thumb_imgs = "".join(
            f'<img src="./images/{img}" alt="{name}">'
            for img in images[:3]
        )
        thumbs_html = f'<div class="banner-thumbs">{thumb_imgs}</div>'
    else:
        thumbs_html = ""

    # ── Front page ──
    front = f"""<div class="page front">
  <header class="banner">
    <div class="banner-text">
      <h1>{name}</h1>
      <div class="subtitle">{sp['scientific']} &mdash; {sp['origin']}</div>
    </div>
    {thumbs_html}
  </header>

  <div class="stats-strip">
    <div class="stat"><div class="label">Janka Hardness</div><div class="value">{janka:,} lbf</div></div>
    <div class="stat"><div class="label">Density</div><div class="value">{props['density']}</div></div>
    <div class="stat"><div class="label">Origin</div><div class="value">{sp['origin']}</div></div>
    <div class="stat"><div class="label">Grain</div><div class="value">{app['grain']}</div></div>
  </div>

  <div class="two-col">
    <div class="group">
      <div class="group-header">About This Wood</div>

      <div class="section-title">Appearance</div>
      <div class="section-text"><strong>Heartwood:</strong> {app['heartwood']}<br><strong>Sapwood:</strong> {app['sapwood']}<br><strong>Texture:</strong> {app['texture']}<br><strong>Lustre:</strong> {app['luster']}</div>

      <div class="section-title">Why Choose It</div>
      {render_list(sp['advantages'], 'adv-list')}

      <div class="section-title">Common Uses</div>
      {render_list(sp['uses'], 'uses-list')}
    </div>

    <div class="group">
      <div class="group-header">Workshop Guide</div>

      <div class="section-title">Working Properties</div>
      <div class="section-text">
        <strong>Workability:</strong> {props['workability']}<br>
        <strong>Turning:</strong> {props['turning']}<br>
        <strong>Gluing:</strong> {props['gluing']}<br>
        <strong>Finishing:</strong> {props['finishing']}
      </div>

      <div class="section-title">Watch Out For</div>
      {render_list(sp['challenges'], 'chal-list')}

      <div class="section-title">Finishing Tips</div>
      {render_list(sp['finishing_tips'], 'tips-list')}

      <div class="section-title">Buying Tips</div>
      {render_list(sp['buying_tips'], 'buying-list')}
    </div>
  </div>

  <div class="janka-strip">
    <div class="janka-label">Janka Hardness &mdash; {janka:,} lbf</div>
    <div class="janka-bar-container">
      <div class="janka-bar-fill" style="width: {janka_pct:.1f}%">
        <span class="janka-bar-label">{janka:,}</span>
      </div>
    </div>
  </div>

  <div class="comparisons">
    {render_table(sp['comparisons'][0])}
    {render_table(sp['comparisons'][1])}
  </div>

  <footer class="fun-fact">
    <strong>Did you know?</strong> {sp['fun_fact']}
  </footer>
</div>"""

    # ── Back page ──
    captions = ["Product Example 1", "Product Example 2", "Product Example 3"]
    if images:
        photo_cards = ""
        for i, img in enumerate(images[:3]):
            cap = captions[i] if i < len(captions) else f"Image {i+1}"
            photo_cards += f"""<div class="photo-card">
        <img src="./images/{img}" alt="{name} — {cap}">
        <div class="photo-caption">{cap}</div>
      </div>\n"""
    else:
        photo_cards = f'<div class="no-photos">No product images available for {name}</div>'

    faq_items = ""
    for faq in sp["faqs"]:
        faq_items += f"""<div class="faq-item">
        <div class="faq-q">{faq['q']}</div>
        <div class="faq-a">{faq['a']}</div>
      </div>\n"""

    back = f"""<div class="page back">
  <header class="banner">
    <div class="banner-text">
      <h1>{name}</h1>
      <div class="subtitle">Visual Reference &amp; FAQ</div>
    </div>
    {thumbs_html}
  </header>

  <div class="colour-ref">
    <div class="colour-item"><div class="colour-label">Heartwood</div><div class="colour-value">{app['heartwood']}</div></div>
    <div class="colour-item"><div class="colour-label">Sapwood</div><div class="colour-value">{app['sapwood']}</div></div>
    <div class="colour-item"><div class="colour-label">Texture</div><div class="colour-value">{app['texture']}</div></div>
    <div class="colour-item"><div class="colour-label">Lustre</div><div class="colour-value">{app['luster']}</div></div>
  </div>

  <div class="photo-grid">
    {photo_cards}
  </div>

  <div class="faq-section">
    <div class="section-title" style="margin-bottom: 6px;">Frequently Asked Questions</div>
    <div class="faq-grid">
      {faq_items}
    </div>
  </div>

  <footer class="source-bar">
    {name} Wood Species Reference Card &bull; Data compiled from industry sources &bull; For educational use
  </footer>
</div>"""

    return front, back


def wrap_html(title, body_content):
    """Wrap page content in a full HTML document."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>{CSS}</style>
</head>
<body>
{body_content}
</body>
</html>"""


# ── Main ────────────────────────────────────────────────────────

def load_species(yml_paths):
    """Load and return a list of species dicts from YAML files."""
    species = []
    for path in yml_paths:
        with open(path, "r", encoding="utf-8") as f:
            species.append(yaml.safe_load(f))
    return species


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Build wood species reference cards from YAML.")
    parser.add_argument("files", nargs="*", help="Specific YAML files to build (default: all)")
    parser.add_argument("--all-in-one", action="store_true",
                        help="Also generate all_species.html with every species in one file")
    args = parser.parse_args()

    build_dir = os.path.join(SCRIPT_DIR, "build")
    os.makedirs(build_dir, exist_ok=True)

    # Symlink images/ into build/ so relative paths work
    images_link = os.path.join(build_dir, "images")
    images_src = os.path.join(SCRIPT_DIR, "images")
    if not os.path.exists(images_link):
        os.symlink(images_src, images_link)

    # Determine which YAML files to build
    if args.files:
        yml_paths = []
        for arg in args.files:
            if os.path.isfile(arg):
                yml_paths.append(arg)
            else:
                candidate = os.path.join(SPECIES_DIR, arg)
                if os.path.isfile(candidate):
                    yml_paths.append(candidate)
                else:
                    print(f"  WARNING: {arg} not found, skipping")
    else:
        yml_paths = sorted(glob.glob(os.path.join(SPECIES_DIR, "*.yml")))

    if not yml_paths:
        print("No YAML files found in species/ directory.")
        sys.exit(1)

    # Load all species to compute max Janka across the full set
    all_paths = sorted(glob.glob(os.path.join(SPECIES_DIR, "*.yml")))
    all_species = load_species(all_paths)
    max_janka = max(sp["properties"]["janka"] for sp in all_species)

    # Build individual HTML files
    to_build = load_species(yml_paths)
    all_pages = []
    for sp in to_build:
        front, back = render_card(sp, max_janka)
        all_pages.append(front)
        all_pages.append(back)

        slug = safe_name(sp["name"])
        filename = f"{slug}.html"
        filepath = os.path.join(build_dir, filename)
        html = wrap_html(f"{sp['name']} — Wood Species Reference Card", f"{front}\n{back}")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        images = find_images(sp["name"])
        print(f"  {filename} ({len(images)} images)")

    # Build combined file
    if args.all_in_one:
        combined_path = os.path.join(build_dir, "all_species.html")
        combined_body = "\n".join(all_pages)
        combined_html = wrap_html("All Wood Species — Reference Cards", combined_body)
        with open(combined_path, "w", encoding="utf-8") as f:
            f.write(combined_html)
        print(f"  all_species.html ({len(to_build)} species)")

    print(f"\nBuilt {len(to_build)} cards in {build_dir}/")


if __name__ == "__main__":
    main()
