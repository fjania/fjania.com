#!/usr/bin/env python3
"""
Generate printable wood species reference cards (letter-size, double-sided PDFs).
Each species gets a 2-page PDF:
  - Side 1 (front): Dense 3-column text layout with all properties
  - Side 2 (back): Product photos, colour reference, FAQ
"""

import os
import io
import json
import requests
from PIL import Image as PILImage

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Frame, PageTemplate, BaseDocTemplate, Image,
    HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# ── Colour palette ──────────────────────────────────────────────
DARK_BROWN   = HexColor('#3B2714')
MED_BROWN    = HexColor('#6B4226')
LIGHT_TAN    = HexColor('#F5E6D3')
WARM_CREAM   = HexColor('#FDF8F0')
ACCENT_GOLD  = HexColor('#C4973B')
WHITE        = HexColor('#FFFFFF')
BLACK        = HexColor('#000000')
GREY         = HexColor('#666666')
LIGHT_GREY   = HexColor('#CCCCCC')

PAGE_W, PAGE_H = letter  # 612 x 792
MARGIN = 0.4 * inch

# ── Species data ────────────────────────────────────────────────
SPECIES = [
    {
        "name": "White Oak",
        "scientific": "Quercus alba",
        "origin": "North America",
        "heartwood": "Light to medium brown with olive or golden undertones",
        "sapwood": "Pale cream to white",
        "grain": "Straight, tight, even; prominent rays when quarter-sawn",
        "texture": "Fine to medium, dense and consistent",
        "luster": "Natural sheen; finishes beautifully in satin or matte",
        "janka": 1360,
        "density": "0.68 sg (heavy)",
        "workability": "Very good with sharp tools; balances hardness with predictability",
        "turning": "Dense, smooth, easy to finish on the lathe",
        "gluing": "Excellent when surfaces are properly prepared",
        "finishing": "Outstanding stain and oil absorption",
        "uses": ["Fine furniture & cabinetry", "Flooring & stair treads", "Doors & architectural trim", "Paneling & millwork", "Barrel staves & boatbuilding", "Turning & decorative accents"],
        "advantages": ["Exceptional durability & natural rot resistance", "Neutral colour for classic & modern aesthetics", "Strong and dimensionally stable", "Distinctive ray fleck when quarter-sawn", "Accepts oils, stains, and sealers beautifully"],
        "challenges": ["Reacts with ferrous metals (tannin staining)", "Heavier than many domestic hardwoods", "Quarter-sawn stock commands premium pricing"],
        "finishing_tips": ["Use water-based or oil-based finishes freely", "Avoid ferrous clamps directly on wet surfaces", "Pre-stain conditioner not typically needed", "Quarter-sawn takes stain more evenly"],
        "fun_fact": "White Oak's tyloses make it watertight — that's why it's the only wood suitable for whiskey and wine barrels.",
        "buying_tips": ["Available flat-sawn and quarter-sawn", "Quarter-sawn offers ray fleck figure and stability", "Check for consistent colour across boards", "FAS grade for furniture; #1 Common for character"],
        "comp1_title": "Flat-Sawn vs Quarter-Sawn White Oak",
        "comp1": [
            ["Property", "Flat-Sawn", "Quarter-Sawn"],
            ["Grain Pattern", "Cathedral arches", "Straight lines + ray fleck"],
            ["Stability", "Good", "Excellent"],
            ["Shrinkage", "More movement", "Minimal movement"],
            ["Price", "Standard", "Premium (15-30% more)"],
            ["Best For", "Rustic/traditional", "Modern/refined"],
        ],
        "comp2_title": "White Oak vs Red Oak",
        "comp2": [
            ["Property", "White Oak", "Red Oak"],
            ["Janka Hardness", "1,360 lbf", "1,290 lbf"],
            ["Colour", "Olive/golden brown", "Pinkish-red tone"],
            ["Rot Resistance", "Excellent (tyloses)", "Poor"],
            ["Grain", "Tighter, finer", "More open pores"],
            ["Outdoor Use", "Yes", "Not recommended"],
        ],
        "faqs": [
            ("Is White Oak waterproof?", "Not waterproof, but its tyloses block liquid penetration, making it water-resistant and ideal for barrels and boats."),
            ("Can I use White Oak outdoors?", "Yes — it has natural rot resistance and is one of the best domestic hardwoods for exterior use."),
            ("White Oak vs Red Oak for furniture?", "White Oak is more versatile: tighter grain, better rot resistance, and a more neutral colour palette."),
        ],
        "collection_slug": "white-oak",
    },
    {
        "name": "Purpleheart",
        "scientific": "Peltogyne spp.",
        "origin": "Central & South America",
        "heartwood": "Grayish-brown freshly cut; oxidizes to bright violet-purple",
        "sapwood": "Pale yellow or gray, narrow and distinct",
        "grain": "Generally straight, occasionally wavy or irregular",
        "texture": "Fine to medium",
        "luster": "Naturally high; silky, reflective surface",
        "janka": 2520,
        "density": "0.86 sg (very heavy; sinks in water)",
        "workability": "Moderate; machines well but dulls blades faster",
        "turning": "Excellent; yields clean edges and glassy finish",
        "gluing": "Reliable with fresh surfaces and quality adhesive",
        "finishing": "Takes oils, varnishes, and waxes superbly",
        "uses": ["Fine furniture & cabinetry", "Turning blanks (bowls, pens, handles)", "Flooring & stair treads", "Instrument parts & inlays", "Decorative panels & accents", "Tables, countertops & art pieces"],
        "advantages": ["Vibrant natural colour — no dye needed", "Exceptional hardness (2,520 lbf Janka)", "Impressive dimensional stability", "Striking conversation-piece appearance", "Purple tones last decades with UV protection"],
        "challenges": ["Extremely dense — hard on tools", "Dulls cutting edges faster than domestics", "Heat from dull tools can darken colour", "Expensive compared to domestic hardwoods"],
        "finishing_tips": ["Keep tools razor-sharp to avoid heat buildup", "Use clear UV-protective finish to preserve purple", "Avoid excessive sanding — heat darkens the wood", "Alcohol-based shellac as sealer works well"],
        "fun_fact": "Purpleheart's colour comes from an oxidation reaction — freshly cut wood is grey-brown, then magically turns vivid purple over hours of air exposure.",
        "buying_tips": ["Source from reputable exotic wood suppliers", "Verify sustainability certifications", "Examine colour consistency before purchase", "Account for extra tool sharpening costs"],
        "comp1_title": "Purpleheart Colour Stages",
        "comp1": [
            ["Stage", "Colour", "Timeframe"],
            ["Fresh Cut", "Grey-brown", "Minutes"],
            ["Oxidized", "Bright violet-purple", "Hours to days"],
            ["Aged (unfinished)", "Dark brown-purple", "Years"],
            ["Aged (UV finish)", "Rich plum-purple", "Decades"],
        ],
        "comp2_title": "Purpleheart vs Popular Hardwoods",
        "comp2": [
            ["Property", "Purpleheart", "Hard Maple"],
            ["Janka Hardness", "2,520 lbf", "1,450 lbf"],
            ["Density", "Very heavy", "Heavy"],
            ["Colour", "Vivid purple", "Cream/white"],
            ["Workability", "Moderate (dense)", "Good"],
            ["Price", "Premium exotic", "Moderate domestic"],
        ],
        "faqs": [
            ("What causes Purpleheart's colour change?", "Oxidation transforms the grey-brown freshly cut wood to bright violet-purple over hours of air exposure."),
            ("Is Purpleheart suitable for beginners?", "It requires sharp tools and patience due to extreme density — better for intermediate+ woodworkers."),
            ("How long does the purple colour last?", "With UV-protective finish, the vibrant purple tones can last for decades."),
        ],
        "collection_slug": "purpleheart",
    },
    {
        "name": "Hickory",
        "scientific": "Carya spp.",
        "origin": "Eastern North America",
        "heartwood": "Light to medium brown with reddish undertones",
        "sapwood": "Creamy white to pale tan; strong contrast with heartwood",
        "grain": "Typically straight, often wavy or irregular",
        "texture": "Medium to coarse",
        "luster": "Moderate natural sheen",
        "janka": 1820,
        "density": "0.72 sg (extremely dense)",
        "workability": "Challenging but manageable with sharp tooling",
        "turning": "Good results with sharp tools; dramatic grain shows well",
        "gluing": "Excellent when pre-drilled for fasteners",
        "finishing": "Accepts stains and clear coats well",
        "uses": ["Cutting boards & butcher blocks", "Cabinetry & furniture", "Tool handles & mallets", "Stair treads & flooring", "Workbenches & shop fixtures", "Tabletops & heavy-use surfaces"],
        "advantages": ["Exceptional strength & impact resistance", "Dramatic visual character (heartwood/sapwood contrast)", "Outstanding wear resistance", "Legendary durability for high-use items", "Domestic availability and sustainability"],
        "challenges": ["Requires sharp tooling at all times", "Can tear out with aggressive passes", "Difficult to work with dull blades", "Significant density variation between boards"],
        "finishing_tips": ["Use sharp blades — dull tools cause tear-out", "Sand progressively to 220+ grit", "Oil finishes highlight the grain contrast", "Pre-drill for all fasteners"],
        "fun_fact": "Hickory was the go-to wood for wagon wheels, ladder rungs, and tool handles throughout American history — failure simply wasn't acceptable.",
        "buying_tips": ["Select kiln-dried stock for stability", "Verify careful milling", "Expect dramatic colour variation board-to-board", "Calico (mixed heartwood/sapwood) adds character"],
        "comp1_title": "Hickory Heartwood vs Sapwood",
        "comp1": [
            ["Property", "Heartwood", "Sapwood"],
            ["Colour", "Medium brown, reddish", "Creamy white"],
            ["Hardness", "Same (1,820 lbf)", "Same (1,820 lbf)"],
            ["Character", "Rich, warm", "Clean, bright"],
            ["Popular For", "Rustic furniture", "Contemporary looks"],
        ],
        "comp2_title": "Hickory vs White Oak",
        "comp2": [
            ["Property", "Hickory", "White Oak"],
            ["Janka Hardness", "1,820 lbf", "1,360 lbf"],
            ["Impact Resistance", "Exceptional", "Good"],
            ["Weight", "Heavier", "Heavy"],
            ["Workability", "Challenging", "Moderate"],
            ["Colour Range", "Wide variation", "Consistent"],
        ],
        "faqs": [
            ("Is Hickory too hard to work by hand?", "It's challenging but not impossible — keep tools sharp and take light passes."),
            ("Hickory vs Maple for cutting boards?", "Both excellent. Hickory adds dramatic visual contrast; Maple offers a cleaner look."),
            ("Does Hickory stain well?", "Yes, but test first — the sapwood and heartwood absorb stain differently."),
        ],
        "collection_slug": "hickory-wood",
    },
    {
        "name": "Hard Maple",
        "scientific": "Acer saccharum",
        "origin": "North America",
        "heartwood": "Cream to light reddish brown with warm golden tone",
        "sapwood": "Nearly white to pale cream; often preferred for uniform look",
        "grain": "Generally straight; occasional curly, wavy, or birdseye figure",
        "texture": "Fine and even; glass-like surfaces when sanded",
        "luster": "Naturally bright and reflective",
        "janka": 1450,
        "density": "0.63 sg (heavy and strong)",
        "workability": "Excellent with sharp tools; dull blades cause burning",
        "turning": "Produces crisp detail and clean edges on the lathe",
        "gluing": "Very good when pre-drilled; tight bonds",
        "finishing": "Outstanding; accepts oils and clear coats evenly",
        "uses": ["Furniture & cabinetry", "Cutting boards & butcher blocks", "Flooring & stair treads", "Wood turning projects", "Musical instruments", "Bowling lanes & gym floors"],
        "advantages": ["Exceptional density and wear resistance", "Fine grain for ultra-smooth finishes", "Uniform appearance (sapwood)", "Versatile for modern & traditional styles", "Available with figured variants (curly, birdseye)"],
        "challenges": ["Hardness requires consistently sharp tools", "Dull blades cause burning or tear-out", "Can be difficult to stain evenly", "Heavy — plan for weight in large projects"],
        "finishing_tips": ["Use pre-stain conditioner if staining", "Oil finishes give a warm, natural look", "Sand to 320+ grit for glass-like surface", "Water-based finishes keep colour light"],
        "fun_fact": "Hard Maple is the same wood found in classic bowling lanes, gym floors, and professional-grade cutting boards — it thrives under punishment.",
        "buying_tips": ["Select sapwood for uniform light appearance", "Consider figured variants for decorative pieces", "Prioritize sharp tooling before starting", "FAS grade for clear, consistent boards"],
        "comp1_title": "Hard Maple vs Soft Maple",
        "comp1": [
            ["Property", "Hard Maple", "Soft Maple"],
            ["Janka Hardness", "1,450 lbf", "700–950 lbf"],
            ["Density", "Higher", "Lower"],
            ["Grain", "Tighter, finer", "Slightly coarser"],
            ["Workability", "Needs sharp tools", "Easier to work"],
            ["Price", "Higher", "More affordable"],
        ],
        "comp2_title": "Hard Maple vs Cherry",
        "comp2": [
            ["Property", "Hard Maple", "Cherry"],
            ["Janka Hardness", "1,450 lbf", "995 lbf"],
            ["Colour", "Pale cream/white", "Pinkish to deep red"],
            ["Grain Visibility", "Subtle", "Moderate"],
            ["Darkens Over Time", "Slightly", "Significantly"],
            ["Best For", "Modern/clean look", "Warm/traditional"],
        ],
        "faqs": [
            ("What's the difference between Hard and Soft Maple?", "Hard Maple (Sugar Maple) is denser, harder, and more wear-resistant. Soft Maple is easier to work but less durable."),
            ("Why does Hard Maple burn when cutting?", "Its density creates friction — always use sharp blades and appropriate feed rates."),
            ("Is Hard Maple good for beginners?", "It's forgiving in design but demands sharp, well-maintained tools."),
        ],
        "collection_slug": "hard-maple",
    },
    {
        "name": "Cherry",
        "scientific": "Prunus serotina",
        "origin": "Eastern United States & Southern Canada",
        "heartwood": "Light pinkish brown; matures to deep reddish brown",
        "sapwood": "Creamy white to pale yellow",
        "grain": "Straight and fine, with occasional curls or waves",
        "texture": "Smooth and satiny",
        "luster": "Natural lustre with satiny finish",
        "janka": 995,
        "density": "0.50 sg (moderate)",
        "workability": "Excellent; machines smoothly with minimal tear-out",
        "turning": "Cuts cleanly and polishes easily on the lathe",
        "gluing": "Excellent adhesion and holding strength",
        "finishing": "Outstanding; accepts oils, varnishes, and stains evenly",
        "uses": ["Fine furniture & cabinetry", "Architectural millwork & paneling", "Flooring & stair parts", "Turned bowls & platters", "Musical instruments", "Decorative carving"],
        "advantages": ["Colour deepens beautifully with age", "Excellent workability — forgiving wood", "Balanced strength-to-weight ratio", "Versatile for traditional & modern design", "Premium appearance at moderate cost"],
        "challenges": ["Softer than Oak or Maple (995 lbf Janka)", "Prone to blotching if staining without conditioner", "Colour variation between boards", "Sapwood/heartwood contrast can be dramatic"],
        "finishing_tips": ["Always use pre-stain conditioner before staining", "Clear finishes showcase the natural colour evolution", "Oil finishes deepen the warm tones", "UV exposure accelerates the darkening patina"],
        "fun_fact": "Cherry's colour transformation is one of woodworking's great pleasures — what begins as light pinkish tan gradually becomes a deep reddish brown patina over months and years.",
        "buying_tips": ["Expect colour to darken significantly over time", "Mix boards from same lot for consistent ageing", "Sapwood can be stained to blend or left for contrast", "Select for grain figure if making show pieces"],
        "comp1_title": "Cherry Fresh vs Aged",
        "comp1": [
            ["Property", "Fresh Cut", "Aged (1-2 years)"],
            ["Colour", "Light pinkish tan", "Deep reddish brown"],
            ["Lustre", "Moderate", "Rich, warm glow"],
            ["Character", "Subtle", "Dramatic patina"],
            ["UV Effect", "Accelerates change", "Stabilizes over time"],
        ],
        "comp2_title": "Cherry vs Black Walnut",
        "comp2": [
            ["Property", "Cherry", "Black Walnut"],
            ["Janka Hardness", "995 lbf", "1,010 lbf"],
            ["Colour", "Pinkish → deep red", "Rich dark brown"],
            ["Workability", "Excellent", "Excellent"],
            ["Weight", "Moderate", "Moderate-heavy"],
            ["Colour Change", "Darkens significantly", "Lightens slightly"],
        ],
        "faqs": [
            ("Why does Cherry change colour?", "UV light and oxidation cause natural chemical changes that deepen the pink tones into rich reddish brown."),
            ("How do I prevent blotching?", "Always apply a pre-stain wood conditioner before staining. Or use a gel stain for more control."),
            ("Is Cherry durable enough for furniture?", "Absolutely — it's been a premier furniture wood for centuries. It's softer than Oak but more than adequate."),
        ],
        "collection_slug": "cherry-wood",
    },
    {
        "name": "Black Walnut",
        "scientific": "Juglans nigra",
        "origin": "Eastern North America",
        "heartwood": "Rich dark brown to purplish black; deepens with age",
        "sapwood": "Pale cream to light grey",
        "grain": "Generally straight; occasionally wavy or curly",
        "texture": "Fine and even with natural lustre",
        "luster": "Natural lustre under finish",
        "janka": 1010,
        "density": "0.55 sg (moderately heavy)",
        "workability": "Excellent; planes, sands, turns, and glues effortlessly",
        "turning": "Performs beautifully for bowls and lathe projects",
        "gluing": "Responds well; reliable bonds",
        "finishing": "Accepts oil, shellac, and varnish flawlessly without blotching",
        "uses": ["Fine furniture & cabinetry", "Gunstocks & musical instruments", "Architectural millwork & wall panels", "Veneer & marquetry", "Turned bowls & lathe projects", "Custom tables & countertops"],
        "advantages": ["Striking natural dark colour — no stain needed", "Dramatic heartwood/sapwood contrast", "Machines cleanly and holds fine detail", "Stable and durable", "Premium appearance prized worldwide"],
        "challenges": ["Premium pricing — most expensive domestic hardwood", "Narrower boards (smaller trees)", "Sapwood waste if uniform colour needed", "Can stain hands and clothes"],
        "finishing_tips": ["Clear coats showcase natural beauty best", "Oil finishes deepen the rich brown tones", "No pre-stain conditioner needed — won't blotch", "Danish oil is a classic Walnut finish"],
        "fun_fact": "Black Walnut is one of the only domestic North American species with naturally dark heartwood — most 'dark' furniture woods get their colour from stain.",
        "buying_tips": ["Curly, crotch, or burl variants command premiums", "Sapwood contrast is desirable for visual impact", "Steamed Walnut has more uniform (lighter) colour", "Live edge slabs are spectacular in this species"],
        "comp1_title": "Steamed vs Unsteamed Walnut",
        "comp1": [
            ["Property", "Steamed", "Unsteamed (Natural)"],
            ["Heartwood", "More uniform brown", "Rich dark brown to purple"],
            ["Sapwood", "Blends more", "Sharp cream contrast"],
            ["Character", "Consistent", "More dramatic"],
            ["Typical Use", "Production furniture", "Show pieces"],
        ],
        "comp2_title": "Black Walnut vs Cherry",
        "comp2": [
            ["Property", "Black Walnut", "Cherry"],
            ["Janka Hardness", "1,010 lbf", "995 lbf"],
            ["Colour", "Dark brown/purple", "Pink → deep red"],
            ["Grain", "Straight, fine", "Straight, fine"],
            ["Price", "Premium", "Moderate"],
            ["Stain Needed", "No", "No (colour develops)"],
        ],
        "faqs": [
            ("Why is Black Walnut so expensive?", "Smaller trees, slower growth, and worldwide demand for its unique dark colour drive premium pricing."),
            ("Does Walnut darken or lighten over time?", "Unlike most woods, Walnut actually lightens slightly over years of UV exposure."),
            ("Steamed vs natural Walnut?", "Steaming blends sapwood/heartwood colour for uniformity. Natural has more dramatic contrast."),
        ],
        "collection_slug": "black-walnut",
    },
    {
        "name": "Black Limba",
        "scientific": "Terminalia superba",
        "origin": "West & Central Africa (Ghana, Ivory Coast)",
        "heartwood": "Light golden-yellow with deep black/dark brown streaks",
        "sapwood": "Pale white or cream, blending softly into heartwood",
        "grain": "Straight to interlocked; dramatic figure",
        "texture": "Medium to coarse",
        "luster": "Good natural sheen under finish",
        "janka": 670,
        "density": "0.45 sg (medium-light; excellent strength-to-weight)",
        "workability": "Exceptionally easy to work; machines, sands, and glues easily",
        "turning": "Produces fine, clean finish on the lathe",
        "gluing": "Glues easily with standard adhesives",
        "finishing": "Accepts oils and clear coats beautifully; grain comes alive",
        "uses": ["Furniture & cabinetry", "Guitar bodies & musical instruments", "Decorative veneers & inlays", "Live edge slabs & tabletops", "Turned objects & sculptural pieces", "Accent walls & fine joinery"],
        "advantages": ["Visually striking natural figure", "Lightweight yet strong", "Easy machining & clean cutting", "Excellent finishing potential", "Stable and reliable", "Outstanding for bookmatching"],
        "challenges": ["Interlocked grain may cause tear-out", "Requires sharp cutters for best results", "Exotic pricing (imported)", "Colour/figure varies significantly board to board"],
        "finishing_tips": ["Use sharp cutters to prevent tear-out", "Satin or gloss clear coats enhance grain", "Oil finishes bring out the golden tones", "Light sanding between coats for best results"],
        "fun_fact": "Black Limba (known locally as 'Akom') comes from the same species as White Limba — the dramatic dark streaking is what sets it apart and makes it prized.",
        "buying_tips": ["Select boards with bold streaking patterns", "Consider bookmatching for dramatic symmetry", "Inspect for figure quality and consistency", "Pairs beautifully with lighter woods as accents"],
        "comp1_title": "Black Limba vs White Limba",
        "comp1": [
            ["Property", "Black Limba", "White Limba"],
            ["Colour", "Golden + black streaks", "Uniform pale yellow"],
            ["Figure", "Dramatic, varied", "Subtle, even"],
            ["Hardness", "670 lbf (same)", "670 lbf (same)"],
            ["Price", "Premium (figure)", "More affordable"],
            ["Appeal", "Show pieces", "Utility / subtle"],
        ],
        "comp2_title": "Black Limba vs Mahogany",
        "comp2": [
            ["Property", "Black Limba", "Mahogany"],
            ["Janka Hardness", "670 lbf", "800–900 lbf"],
            ["Weight", "Lightweight", "Moderate"],
            ["Workability", "Excellent", "Good"],
            ["Figure", "Dramatic streaking", "Subtle ribbon grain"],
            ["Common Use", "Guitars, art furniture", "Traditional furniture"],
        ],
        "faqs": [
            ("How does Black Limba compare to White Limba?", "Same species — Black Limba has dramatic dark streaks and contrasting figure that White Limba lacks."),
            ("Is Black Limba difficult to work?", "No — it's one of the most user-friendly tropical hardwoods with excellent machining properties."),
            ("What finishes work best?", "Oils and clear coats enhance the grain beautifully, particularly satin or gloss finishes."),
        ],
        "collection_slug": "black-limba",
    },
    {
        "name": "Aromatic Cedar",
        "scientific": "Juniperus virginiana",
        "origin": "Eastern North America",
        "heartwood": "Rich reddish-purple; ages to warm golden reddish-brown",
        "sapwood": "Pale yellow or creamy white",
        "grain": "Fine, uniform with tight knots and colour streaks",
        "texture": "Fine and uniform",
        "luster": "Warm natural glow",
        "janka": 900,
        "density": "0.47 sg (light to moderate)",
        "workability": "Machines well with sharp tools; soft enough for hand work",
        "turning": "Good for small turned items; aromatic shavings",
        "gluing": "Good with standard wood glues",
        "finishing": "Ages beautifully; many leave unfinished for aroma",
        "uses": ["Closet lining & storage chests", "Furniture interiors & drawers", "Decorative panels & accent walls", "Heirloom blanket chests", "Jewellery boxes", "Moth-repellent applications"],
        "advantages": ["Distinctive pleasant fragrance", "Natural moth & insect repellent", "Vivid heartwood/sapwood colour contrast", "Fine, workable grain", "Aroma persists for years in enclosed spaces", "Naturally decay resistant"],
        "challenges": ["Softwood — dents more easily than hardwoods", "Knots can be challenging to work around", "Not suitable for food contact (aromatic oils)", "Narrow boards from smaller trees"],
        "finishing_tips": ["Leave unfinished in closets to preserve aroma", "Light sanding renews the scent over time", "If finishing, use clear shellac or lacquer", "Avoid polyurethane — it seals in the scent"],
        "fun_fact": "Aromatic Cedar isn't a true cedar at all — it's actually a juniper species! The scent comes from natural essential oils that effectively repel moths and insects.",
        "buying_tips": ["Smell the wood — fresh stock should be fragrant", "Look for dramatic heartwood/sapwood contrast", "Select based on end use (closet vs decorative)", "Wider boards are rarer and command premiums"],
        "comp1_title": "Finished vs Unfinished Aromatic Cedar",
        "comp1": [
            ["Property", "Unfinished", "Finished"],
            ["Aroma", "Full fragrance", "Reduced/sealed"],
            ["Colour", "Vivid red-purple", "Preserved but muted"],
            ["Best For", "Closets, chests", "Decorative panels"],
            ["Maintenance", "Sand to renew scent", "Standard care"],
        ],
        "comp2_title": "Aromatic Cedar vs Western Red Cedar",
        "comp2": [
            ["Property", "Aromatic (Eastern Red)", "Western Red"],
            ["Species", "Juniperus virginiana", "Thuja plicata"],
            ["Aroma", "Strong, distinctive", "Mild"],
            ["Hardness", "~900 lbf", "~350 lbf"],
            ["Primary Use", "Interior/closets", "Exterior/decking"],
            ["Insect Repellent", "Excellent", "Moderate"],
        ],
        "faqs": [
            ("Does the scent fade?", "It lasts years in enclosed spaces. Light sanding with fine grit renews the fragrance."),
            ("Is Aromatic Cedar safe for food contact?", "No — the aromatic oils make it unsuitable for cutting boards or food storage."),
            ("Can I use it outdoors?", "It has some rot resistance but is better suited to interior applications. Western Red Cedar is better for outdoor use."),
        ],
        "collection_slug": "aromatic-cedar",
    },
    {
        "name": "Ambrosia Maple",
        "scientific": "Acer rubrum (beetle-figured)",
        "origin": "North America",
        "heartwood": "Light creamy beige with grey, brown & blue-green streaking",
        "sapwood": "Creamy beige base colour",
        "grain": "Linear or feathery streaks from beetle tunnels",
        "texture": "Fine to medium; tiny bore holes throughout",
        "luster": "Moderate natural sheen",
        "janka": 950,
        "density": "0.54 sg (moderate; typical of soft maple)",
        "workability": "Cuts cleanly with sharp tools; tear-out possible around holes",
        "turning": "Excellent — visual character shines on the lathe",
        "gluing": "Excellent adhesion with standard wood glues",
        "finishing": "Sands smoothly; fine grit maintains grain contrast",
        "uses": ["Accent furniture & feature pieces", "Tabletops & dining tables", "Turned bowls & vessels", "Cutting boards", "Decorative conversation pieces", "Wall art & live edge projects"],
        "advantages": ["Unique, unrepeatable natural patterns", "Excellent workability", "Affordable compared to other figured woods", "Stunning visual character", "Great strength-to-beauty ratio"],
        "challenges": ["Variable figure — board selection is critical", "Small bore holes throughout the wood", "Tear-out risk around figured areas", "No two boards are alike (matching is difficult)"],
        "finishing_tips": ["Use fine-grit sandpaper to preserve contrast", "Matte finishes highlight the blue-grey tones", "Test finish on scrap first", "Clear coats showcase the natural patterns best"],
        "fun_fact": "Ambrosia Maple isn't actually a species — it's the creative result of the Ambrosia beetle boring into soft maple and leaving behind artistic fungal staining. Every board is one-of-a-kind.",
        "buying_tips": ["Select boards for figure consistency and pattern appeal", "All insect activity ceases after kiln-drying — wood is safe", "Inspect bore hole density for your taste", "Consider visual impact in the final design"],
        "comp1_title": "Ambrosia Maple vs Standard Soft Maple",
        "comp1": [
            ["Property", "Ambrosia Maple", "Standard Soft Maple"],
            ["Appearance", "Grey/blue streaks + bore holes", "Uniform light colour"],
            ["Janka Hardness", "700–950 lbf", "700–950 lbf"],
            ["Visual Character", "High artistic appeal", "Minimal pattern"],
            ["Price", "Higher (unique figure)", "Lower baseline"],
            ["Workability", "Excellent", "Excellent"],
        ],
        "comp2_title": "Ambrosia Maple vs Spalted Maple",
        "comp2": [
            ["Property", "Ambrosia Maple", "Spalted Maple"],
            ["Cause", "Beetle + fungal staining", "Fungal decay (spalting)"],
            ["Structural Integrity", "Fully sound", "Can be soft/punky"],
            ["Colour Palette", "Grey, blue, brown streaks", "Black zone lines"],
            ["Workability", "Standard maple", "Varies (soft spots)"],
            ["Stability", "Reliable", "Unpredictable"],
        ],
        "faqs": [
            ("Are there live bugs in the wood?", "No — kiln-drying halts all insect activity. The wood is completely safe and stable."),
            ("Is it as strong as regular Maple?", "Yes — the beetle tunnels are cosmetic. Structural integrity is the same as soft maple."),
            ("Why is it called 'wormy maple'?", "Historical name, though beetles (not worms) create the characteristic patterns."),
        ],
        "collection_slug": "ambrosia-maple",
    },
    {
        "name": "Ash",
        "scientific": "Fraxinus americana",
        "origin": "North America",
        "heartwood": "Light beige to creamy brown with gentle golden tint",
        "sapwood": "Slightly lighter; blends with heartwood",
        "grain": "Straight, bold, open with cathedral-like patterns",
        "texture": "Medium to coarse; smoother than Oak",
        "luster": "Natural satin glow that brightens with finish",
        "janka": 1320,
        "density": "0.60 sg (medium-heavy)",
        "workability": "Machines, turns, sands, and finishes easily",
        "turning": "Excellent for bowls, pens, and spindle work",
        "gluing": "Excellent adhesion and strong fastener hold",
        "finishing": "Accepts stain exceptionally well; grain filler recommended",
        "uses": ["Furniture & cabinetry", "Table legs & chair frames", "Flooring & stair parts", "Baseball bats & tool handles", "Turned bowls & pens", "Veneers & decorative panels"],
        "advantages": ["Exceptional strength-to-weight ratio", "Bold, beautiful cathedral grain", "Versatile finish options — mimics other species", "Sustainably sourced across North America", "Excellent steam-bending properties"],
        "challenges": ["Open pores require grain filler for smooth finish", "Supply impacted by Emerald Ash Borer", "Not naturally rot-resistant outdoors", "Can look 'busy' in large flat panels"],
        "finishing_tips": ["Use grain filler or pre-sealer for smooth finish", "Takes stain evenly and predictably", "Can mimic Oak, Walnut, or other species with stain", "Oil finishes highlight the bold grain pattern"],
        "fun_fact": "Ash has been the wood of choice for baseball bats and axe handles for centuries — its incredible impact resistance and natural elasticity make it unmatched for tools that take a beating.",
        "buying_tips": ["Great value — premium look at domestic pricing", "Choose for projects needing strength without excess weight", "Ideal if you prefer bright, clean aesthetic over Oak", "Source soon — Emerald Ash Borer is reducing supply"],
        "comp1_title": "Ash: Oil Finish vs Film Finish",
        "comp1": [
            ["Property", "Oil Finish", "Film Finish (Poly)"],
            ["Grain Feel", "Natural, tactile", "Smooth, sealed"],
            ["Pore Filling", "Minimal", "Fills with coats"],
            ["Repairability", "Easy touch-up", "Requires full resand"],
            ["Best For", "Rustic/natural look", "High-wear surfaces"],
        ],
        "comp2_title": "Ash vs Red Oak",
        "comp2": [
            ["Property", "Ash", "Red Oak"],
            ["Janka Hardness", "1,320 lbf", "1,290 lbf"],
            ["Colour", "Light beige-brown", "Pinkish-red tone"],
            ["Grain Pattern", "Cathedral, bold", "Open, prominent"],
            ["Workability", "Excellent", "Good"],
            ["Steam Bending", "Excellent", "Good"],
        ],
        "faqs": [
            ("Is Ash suitable for beginners?", "Yes — its excellent workability makes it forgiving for new woodworkers."),
            ("Does Ash bend well?", "Exceptionally — high shock resistance and elasticity make it ideal for steam bending."),
            ("Can Ash replace Oak?", "In many applications, yes — with a brighter aesthetic and comparable durability."),
        ],
        "collection_slug": "ash-wood",
    },
    {
        "name": "Afromosia",
        "scientific": "Pericopsis elata",
        "origin": "West & Central Africa (Ghana, Cameroon, Congo)",
        "heartwood": "Golden to medium brown with olive or copper undertones",
        "sapwood": "Pale yellow, sharply distinct from heartwood",
        "grain": "Straight to slightly interlocked; ribbon figure on QS",
        "texture": "Fine and uniform with satiny lustre",
        "luster": "Naturally bright and reflective; polishes to soft glow",
        "janka": 1570,
        "density": "0.62 sg (medium-heavy)",
        "workability": "Excellent — planes, sands, and carves cleanly",
        "turning": "Outstanding; crisp edges and high sheen",
        "gluing": "Very good on freshly abraded surfaces",
        "finishing": "Superb — takes oil beautifully and polishes naturally",
        "uses": ["Fine furniture & cabinetry", "Flooring & stairwork", "Exterior architecture", "Boatbuilding", "Decorative millwork", "Turned objects & bowls"],
        "advantages": ["Natural decay resistance", "Dimensional stability", "Workability rivalling domestic hardwoods", "Develops rich patina over time", "Easier finishing than Teak (fewer oils)", "Sustainable sourcing available"],
        "challenges": ["Higher cost than domestic hardwoods", "Requires fresh surfaces for optimal gluing", "Some boards have interlocked grain", "CITES Appendix II — verify sourcing"],
        "finishing_tips": ["Oil finishes bring out natural golden sheen", "Sands to silky smoothness easily", "Avoid heavy film finishes — they mask natural beauty", "Develops richer amber tone over time"],
        "fun_fact": "Over time, Afromosia darkens to a richer amber tone, developing a patina that rivals genuine Teak — at a fraction of the cost and with easier workability.",
        "buying_tips": ["Select quarter-sawn for ribbon figure", "Inspect sapwood/heartwood contrast", "Source from certified sustainable suppliers", "Compare pricing with Teak — often significantly less"],
        "comp1_title": "Afromosia vs Teak",
        "comp1": [
            ["Property", "Afromosia", "Teak"],
            ["Janka Hardness", "1,570 lbf", "1,000 lbf"],
            ["Natural Oils", "Moderate", "High"],
            ["Workability", "Excellent", "Good"],
            ["Cost", "Moderate", "Premium"],
            ["Gluing", "Easier", "Requires special prep"],
        ],
        "comp2_title": "Afromosia vs White Oak",
        "comp2": [
            ["Property", "Afromosia", "White Oak"],
            ["Janka Hardness", "1,570 lbf", "1,360 lbf"],
            ["Colour", "Golden-brown", "Pale tan/olive"],
            ["Decay Resistance", "Excellent", "Good"],
            ["Origin", "Tropical (Africa)", "Domestic (N. America)"],
            ["Grain Pattern", "Fine, ribbon", "Open, coarse"],
        ],
        "faqs": [
            ("Is Afromosia sustainable?", "Certified sustainable sources are available. It's CITES Appendix II — always verify sourcing with your supplier."),
            ("How does it compare to Teak?", "Similar appearance and durability, with easier finishing, better hardness, and lower cost."),
            ("Will it darken over time?", "Yes — it develops a richer amber patina similar to aged Teak."),
        ],
        "collection_slug": None,  # No collection page
    },
    {
        "name": "African Blackwood",
        "scientific": "Dalbergia melanoxylon",
        "origin": "East Africa (Tanzania, Mozambique)",
        "heartwood": "Jet black to deep violet-brown with dark streaks",
        "sapwood": "Pale yellow-white; sharp contrast when visible",
        "grain": "Straight to slightly interlocked",
        "texture": "Very fine and uniform; naturally oily",
        "luster": "Subtle natural polish even before finishing",
        "janka": 3670,
        "density": "1.27 sg (extremely heavy; sinks readily)",
        "workability": "Excellent for turning and fine cutting; tough on dull tools",
        "turning": "Exceptional — ideal for fine detail and mirror finishes",
        "gluing": "Requires fresh surfaces due to natural oils",
        "finishing": "Superb — polishes to glass-like sheen without topcoat",
        "uses": ["Musical instruments (clarinets, oboes, bagpipes)", "Fine turning (pens, bowls, handles)", "Knife handles & precision tools", "Luxury furniture inlays", "Sculptural art & jewellery boxes", "High-end woodwind instruments"],
        "advantages": ["One of the world's hardest woods (3,670 lbf)", "Dimensional stability — minimal climate movement", "Natural mirror-like polish without coatings", "Acoustic properties unmatched for woodwinds", "Extremely fine, uniform texture"],
        "challenges": ["Extremely hard on cutting tools", "Very expensive — often sold by the piece", "Heavy and dense — small pieces only practical", "Dust can be irritating — use respiratory protection", "Slow-growing — sustainability concerns"],
        "finishing_tips": ["Often needs no finish — polishes naturally", "Buff with fine compound for mirror sheen", "If finishing, use thin oil or wax only", "Avoid thick film finishes — unnecessary"],
        "fun_fact": "African Blackwood is often priced higher than gold by weight in instrument-grade billets. It's the world's most expensive commercial timber and the gold standard for professional clarinets and oboes.",
        "buying_tips": ["Sold by the piece, not by the board foot", "Instrument-grade commands extreme premiums", "Smaller turning blanks are more accessible", "Verify sustainable/legal sourcing (CITES listed)"],
        "comp1_title": "African Blackwood by Grade",
        "comp1": [
            ["Property", "Instrument Grade", "Craft/Turning Grade"],
            ["Colour", "Jet black, uniform", "May have streaks"],
            ["Defects", "None", "Minor permitted"],
            ["Size", "Larger billets", "Smaller blanks"],
            ["Price", "Extreme premium", "More accessible"],
            ["Use", "Pro instruments", "Pens, bowls, handles"],
        ],
        "comp2_title": "African Blackwood vs Ebony",
        "comp2": [
            ["Property", "African Blackwood", "Gabon Ebony"],
            ["Janka Hardness", "3,670 lbf", "3,080 lbf"],
            ["Colour", "Black with violet tones", "Jet black"],
            ["Oiliness", "Naturally oily", "Dry"],
            ["Primary Use", "Woodwinds", "Piano keys, inlays"],
            ["Turning", "Exceptional", "Good but brittle"],
        ],
        "faqs": [
            ("Why is it so expensive?", "Slow growth, small trees, extreme demand for instruments, and limited supply drive prices above many precious metals by weight."),
            ("Can beginners work with it?", "For turning, yes — it cuts beautifully. For joinery, the extreme hardness makes it challenging."),
            ("Is it sustainable?", "It's CITES-listed. Always buy from verified sustainable sources and support reforestation efforts."),
        ],
        "collection_slug": None,  # No collection page
    },
]

# ── Image download ──────────────────────────────────────────────

IMG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
os.makedirs(IMG_DIR, exist_ok=True)

def get_collection_images(slug, max_images=3):
    """Download product images from Shopify collection JSON API."""
    if not slug:
        return []
    url = f"https://theknottylumberco.ca/collections/{slug}/products.json"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return []
        products = r.json().get("products", [])
        image_urls = []
        for p in products:
            for img in p.get("images", []):
                src = img.get("src", "")
                if src and len(image_urls) < max_images:
                    image_urls.append(src)
            if len(image_urls) >= max_images:
                break
        return image_urls
    except Exception as e:
        print(f"  Warning: Could not fetch images for {slug}: {e}")
        return []

def download_image(url, species_name, index):
    """Download an image and return the local path."""
    safe_name = species_name.lower().replace(" ", "_")
    ext = "jpg"
    if ".png" in url.lower():
        ext = "png"
    local_path = os.path.join(IMG_DIR, f"{safe_name}_{index}.{ext}")
    if os.path.exists(local_path):
        return local_path
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            with open(local_path, "wb") as f:
                f.write(r.content)
            return local_path
    except Exception as e:
        print(f"  Warning: Could not download {url}: {e}")
    return None

# ── Blog page image fallback ────────────────────────────────────

def get_blog_images(species_name):
    """Scrape images from the blog page for species without collection pages."""
    from bs4 import BeautifulSoup
    slug_map = {
        "Afromosia": "afromosia-lumber",
        "African Blackwood": "african-blackwood",
    }
    slug = slug_map.get(species_name)
    if not slug:
        return []
    url = f"https://theknottylumberco.ca/blogs/woodworkers-species-guide/{slug}"
    try:
        r = requests.get(url, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        imgs = []
        for img in soup.find_all("img"):
            src = img.get("src", "") or img.get("data-src", "") or ""
            if "cdn.shopify.com" in src and src not in imgs:
                clean = src.split("?")[0]
                if clean.startswith("//"):
                    clean = "https:" + clean
                if clean not in imgs:
                    imgs.append(clean)
        return imgs[:3]
    except Exception:
        return []

# ── PDF generation helpers ──────────────────────────────────────

def make_styles():
    """Create paragraph styles for the reference cards."""
    styles = {}

    styles["title"] = ParagraphStyle(
        "Title", fontName="Helvetica-Bold", fontSize=20, leading=22,
        textColor=WHITE, alignment=TA_CENTER
    )
    styles["subtitle"] = ParagraphStyle(
        "Subtitle", fontName="Helvetica-Oblique", fontSize=10, leading=12,
        textColor=LIGHT_TAN, alignment=TA_CENTER
    )
    styles["section_head"] = ParagraphStyle(
        "SectionHead", fontName="Helvetica-Bold", fontSize=10, leading=13,
        textColor=DARK_BROWN, spaceBefore=5, spaceAfter=2,
    )
    styles["body"] = ParagraphStyle(
        "Body", fontName="Helvetica", fontSize=8, leading=10.5,
        textColor=BLACK,
    )
    styles["body_bold"] = ParagraphStyle(
        "BodyBold", fontName="Helvetica-Bold", fontSize=8, leading=10.5,
        textColor=DARK_BROWN,
    )
    styles["bullet"] = ParagraphStyle(
        "Bullet", fontName="Helvetica", fontSize=8, leading=10.5,
        textColor=BLACK, leftIndent=8, bulletIndent=0,
        bulletFontName="Helvetica", bulletFontSize=7,
    )
    styles["stat_label"] = ParagraphStyle(
        "StatLabel", fontName="Helvetica-Bold", fontSize=7, leading=9,
        textColor=MED_BROWN,
    )
    styles["stat_value"] = ParagraphStyle(
        "StatValue", fontName="Helvetica", fontSize=8, leading=10,
        textColor=BLACK,
    )
    styles["fun_fact"] = ParagraphStyle(
        "FunFact", fontName="Helvetica-Oblique", fontSize=7.5, leading=10,
        textColor=DARK_BROWN,
    )
    styles["faq_q"] = ParagraphStyle(
        "FAQQ", fontName="Helvetica-Bold", fontSize=8.5, leading=11,
        textColor=DARK_BROWN, spaceBefore=4, spaceAfter=1,
    )
    styles["faq_a"] = ParagraphStyle(
        "FAQA", fontName="Helvetica", fontSize=8, leading=10.5,
        textColor=BLACK, spaceAfter=4,
    )
    styles["photo_title"] = ParagraphStyle(
        "PhotoTitle", fontName="Helvetica-Bold", fontSize=18, leading=20,
        textColor=WHITE, alignment=TA_CENTER
    )
    styles["photo_subtitle"] = ParagraphStyle(
        "PhotoSubtitle", fontName="Helvetica-Oblique", fontSize=10, leading=12,
        textColor=LIGHT_TAN, alignment=TA_CENTER
    )
    styles["colour_label"] = ParagraphStyle(
        "ColourLabel", fontName="Helvetica-Bold", fontSize=8, leading=10,
        textColor=MED_BROWN,
    )
    styles["colour_value"] = ParagraphStyle(
        "ColourValue", fontName="Helvetica", fontSize=8, leading=10,
        textColor=BLACK,
    )
    return styles

def draw_header_banner(c, y, title, subtitle, page_w):
    """Draw the dark brown header banner with species name."""
    banner_h = 48
    c.setFillColor(DARK_BROWN)
    c.rect(0, y - banner_h, page_w, banner_h, fill=1, stroke=0)
    # Gold accent line
    c.setStrokeColor(ACCENT_GOLD)
    c.setLineWidth(2)
    c.line(0, y - banner_h, page_w, y - banner_h)
    # Title text
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(page_w / 2, y - 24, title)
    # Subtitle
    c.setFillColor(LIGHT_TAN)
    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString(page_w / 2, y - 40, subtitle)
    return y - banner_h - 2

def draw_stats_strip(c, y, sp, page_w, margin):
    """Draw the quick-stats strip below the header."""
    strip_h = 30
    c.setFillColor(LIGHT_TAN)
    c.rect(0, y - strip_h, page_w, strip_h, fill=1, stroke=0)

    stats = [
        ("JANKA", f"{sp['janka']:,} lbf"),
        ("DENSITY", sp["density"]),
        ("ORIGIN", sp["origin"]),
        ("GRAIN", sp["grain"].split(";")[0].split(",")[0].strip()),
    ]

    x_positions = [margin + i * ((page_w - 2 * margin) / len(stats)) for i in range(len(stats))]
    for i, (label, value) in enumerate(stats):
        x = x_positions[i] + 5
        c.setFillColor(MED_BROWN)
        c.setFont("Helvetica-Bold", 6.5)
        c.drawString(x, y - 10, label)
        c.setFillColor(DARK_BROWN)
        c.setFont("Helvetica-Bold", 8.5)
        val_text = value if len(value) < 25 else value[:23] + "…"
        c.drawString(x, y - 23, val_text)

    # Separators
    c.setStrokeColor(MED_BROWN)
    c.setLineWidth(0.4)
    for i in range(1, len(stats)):
        x = x_positions[i]
        c.line(x, y - 5, x, y - strip_h + 5)

    return y - strip_h

def draw_janka_bar(c, x, y, width, janka, max_janka=4000):
    """Draw a horizontal Janka hardness bar."""
    bar_h = 10
    # Background
    c.setFillColor(LIGHT_TAN)
    c.rect(x, y, width, bar_h, fill=1, stroke=0)
    # Fill
    fill_w = min(width * (janka / max_janka), width)
    c.setFillColor(ACCENT_GOLD)
    c.rect(x, y, fill_w, bar_h, fill=1, stroke=0)
    # Border
    c.setStrokeColor(MED_BROWN)
    c.setLineWidth(0.4)
    c.rect(x, y, width, bar_h, fill=0, stroke=1)
    # Label
    c.setFillColor(DARK_BROWN)
    c.setFont("Helvetica-Bold", 6.5)
    c.drawString(x + 3, y + 2, f"{janka:,} lbf")

def draw_fun_fact_footer(c, y_bottom, text, page_w, margin):
    """Draw the fun fact footer bar."""
    bar_h = 36
    y = y_bottom
    c.setFillColor(DARK_BROWN)
    c.rect(0, y, page_w, bar_h, fill=1, stroke=0)
    # Gold line on top
    c.setStrokeColor(ACCENT_GOLD)
    c.setLineWidth(1.5)
    c.line(0, y + bar_h, page_w, y + bar_h)
    # Label
    c.setFillColor(ACCENT_GOLD)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin, y + bar_h - 12, "FUN FACT")
    c.setFillColor(LIGHT_TAN)
    c.setFont("Helvetica-Oblique", 7.5)
    # Word-wrap the fun fact
    max_w = page_w - 2 * margin
    words = text.split()
    lines = []
    current = ""
    for w in words:
        test = current + " " + w if current else w
        if c.stringWidth(test, "Helvetica-Oblique", 7.5) < max_w:
            current = test
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)
    for i, line in enumerate(lines[:2]):
        c.drawString(margin, y + bar_h - 23 - i * 10, line)

def make_comparison_table(title, data, col_widths):
    """Create a formatted comparison table."""
    styles = make_styles()
    elements = []
    elements.append(Paragraph(f'<b>{title}</b>', styles["section_head"]))

    if not data or len(data) < 2:
        return elements

    # Build table
    table_data = []
    for row in data:
        is_header = (data.index(row) == 0)
        table_data.append([
            Paragraph(f'<b>{cell}</b>' if is_header else str(cell),
                      ParagraphStyle("tc", fontName="Helvetica-Bold" if is_header else "Helvetica",
                                     fontSize=7, leading=9, textColor=WHITE if is_header else BLACK))
            for cell in row
        ])

    t = Table(table_data, colWidths=col_widths)
    header_style = [
        ("BACKGROUND", (0, 0), (-1, 0), MED_BROWN),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("BACKGROUND", (0, 1), (-1, -1), WARM_CREAM),
        ("GRID", (0, 0), (-1, -1), 0.3, LIGHT_GREY),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WARM_CREAM, WHITE]),
    ]
    t.setStyle(TableStyle(header_style))
    elements.append(t)
    return elements

def build_bullet_list(items, style):
    """Build a list of bullet-pointed paragraphs."""
    return [Paragraph(f"• {item}", style) for item in items]

# ── Front page (Side 1) ────────────────────────────────────────

def generate_front_page(c, sp, styles):
    """Generate the front (text content) page."""
    y_top = PAGE_H

    # Header banner
    y = draw_header_banner(c, y_top, sp["name"],
                           f'{sp["scientific"]}  ·  {sp["origin"]}', PAGE_W)

    # Stats strip
    y = draw_stats_strip(c, y, sp, PAGE_W, MARGIN)

    # Fun fact footer (draw first so columns don't overlap)
    draw_fun_fact_footer(c, 0, sp["fun_fact"], PAGE_W, MARGIN)

    # Three-column layout
    col_gap = 8
    usable_w = PAGE_W - 2 * MARGIN
    col_w = (usable_w - 2 * col_gap) / 3
    footer_h = 38
    col_top = y - 4
    col_bottom = footer_h + 4

    frames = []
    for i in range(3):
        x = MARGIN + i * (col_w + col_gap)
        frames.append(Frame(x, col_bottom, col_w, col_top - col_bottom,
                           leftPadding=2, rightPadding=2, topPadding=2, bottomPadding=2,
                           showBoundary=0))

    # Build separate content lists for each column
    col1 = []
    col2 = []
    col3 = []

    # ── COLUMN 1: Appearance + Working Properties ──
    col1.append(Paragraph('<b>APPEARANCE</b>', styles["section_head"]))
    appearance_items = [
        ("Heartwood:", sp["heartwood"]),
        ("Sapwood:", sp["sapwood"]),
        ("Grain:", sp["grain"]),
        ("Texture:", sp["texture"]),
        ("Lustre:", sp["luster"]),
    ]
    for label, value in appearance_items:
        col1.append(Paragraph(f'<b>{label}</b> {value}', styles["body"]))

    col1.append(Spacer(1, 4))
    col1.append(Paragraph('<b>WORKING PROPERTIES</b>', styles["section_head"]))
    col1.append(Paragraph(f'<b>Janka Hardness:</b> {sp["janka"]:,} lbf', styles["body"]))
    col1.append(Spacer(1, 10))  # Space for the bar
    props = [
        ("Density:", sp["density"]),
        ("Workability:", sp["workability"]),
        ("Turning:", sp["turning"]),
        ("Gluing:", sp["gluing"]),
        ("Finishing:", sp["finishing"]),
    ]
    for label, value in props:
        col1.append(Paragraph(f'<b>{label}</b> {value}', styles["body"]))

    col1.append(Spacer(1, 4))
    col1.append(Paragraph('<b>COMMON USES</b>', styles["section_head"]))
    for use in sp["uses"]:
        col1.append(Paragraph(f'• {use}', styles["bullet"]))

    # ── COLUMN 2: Advantages, Challenges, Finishing, Buying ──
    col2.append(Paragraph('<b>ADVANTAGES</b>', styles["section_head"]))
    for item in sp["advantages"]:
        col2.append(Paragraph(f'<font color="#2d7a2d">\u2713</font> {item}', styles["bullet"]))

    col2.append(Spacer(1, 4))
    col2.append(Paragraph('<b>CHALLENGES</b>', styles["section_head"]))
    for item in sp["challenges"]:
        col2.append(Paragraph(f'<font color="#aa3333">\u25b8</font> {item}', styles["bullet"]))

    col2.append(Spacer(1, 4))
    col2.append(Paragraph('<b>FINISHING TIPS</b>', styles["section_head"]))
    for tip in sp["finishing_tips"]:
        col2.append(Paragraph(f'\u2022 {tip}', styles["bullet"]))

    col2.append(Spacer(1, 4))
    col2.append(Paragraph('<b>BUYING TIPS</b>', styles["section_head"]))
    for tip in sp["buying_tips"]:
        col2.append(Paragraph(f'\u2022 {tip}', styles["bullet"]))

    # ── COLUMN 3: Comparison tables ──
    comp_col_w = (col_w - 6) / 3
    comp_widths = [comp_col_w] * 3

    if sp.get("comp1") and len(sp["comp1"]) > 1:
        col3.extend(make_comparison_table(sp["comp1_title"], sp["comp1"], comp_widths))
        col3.append(Spacer(1, 6))

    if sp.get("comp2") and len(sp["comp2"]) > 1:
        col3.extend(make_comparison_table(sp["comp2_title"], sp["comp2"], comp_widths))

    # Draw column separators
    for i in range(1, 3):
        x_sep = MARGIN + i * (col_w + col_gap) - col_gap / 2
        c.setStrokeColor(LIGHT_TAN)
        c.setLineWidth(0.5)
        c.line(x_sep, col_top - 2, x_sep, col_bottom + 2)

    # Render each column into its frame
    for i, col_content in enumerate([col1, col2, col3]):
        frames[i].addFromList(col_content, c)

    # Draw the Janka hardness bar in column 1
    bar_x = MARGIN + 4
    bar_y = col_top - 148  # Approximate position after the Janka text
    bar_w = col_w - 10
    draw_janka_bar(c, bar_x, bar_y, bar_w, sp["janka"])

# ── Back page (Side 2) ─────────────────────────────────────────

def generate_back_page(c, sp, image_paths, styles):
    """Generate the back (photos + FAQ) page."""
    y_top = PAGE_H
    footer_h = 22

    # Header banner
    y = draw_header_banner(c, y_top, sp["name"],
                           "Product Gallery & Quick Reference", PAGE_W)

    # Colour reference section
    y -= 6
    ref_h = 56
    c.setFillColor(LIGHT_TAN)
    c.rect(MARGIN, y - ref_h, PAGE_W - 2 * MARGIN, ref_h, fill=1, stroke=0)
    c.setStrokeColor(MED_BROWN)
    c.setLineWidth(0.4)
    c.rect(MARGIN, y - ref_h, PAGE_W - 2 * MARGIN, ref_h, fill=0, stroke=1)

    # Colour details — larger fonts
    ref_x = MARGIN + 10
    c.setFillColor(DARK_BROWN)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(ref_x, y - 14, "COLOUR REFERENCE")

    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(MED_BROWN)
    c.drawString(ref_x, y - 28, "Heartwood:")
    c.setFillColor(BLACK)
    c.setFont("Helvetica", 7.5)
    hw_text = sp["heartwood"][:55] + ("..." if len(sp["heartwood"]) > 55 else "")
    c.drawString(ref_x + 55, y - 28, hw_text)

    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(MED_BROWN)
    c.drawString(ref_x, y - 41, "Sapwood:")
    c.setFillColor(BLACK)
    c.setFont("Helvetica", 7.5)
    sw_text = sp["sapwood"][:55] + ("..." if len(sp["sapwood"]) > 55 else "")
    c.drawString(ref_x + 55, y - 41, sw_text)

    # Second column
    ref_x2 = PAGE_W / 2 + 10
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(MED_BROWN)
    c.drawString(ref_x2, y - 28, "Texture:")
    c.setFillColor(BLACK)
    c.setFont("Helvetica", 7.5)
    c.drawString(ref_x2 + 42, y - 28, sp["texture"][:35])

    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(MED_BROWN)
    c.drawString(ref_x2, y - 41, "Lustre:")
    c.setFillColor(BLACK)
    c.setFont("Helvetica", 7.5)
    luster_text = sp["luster"][:35] + ("..." if len(sp["luster"]) > 35 else "")
    c.drawString(ref_x2 + 42, y - 41, luster_text)

    y -= ref_h + 6

    # Footer (draw early so we know where photos/FAQ must stop)
    c.setFillColor(DARK_BROWN)
    c.rect(0, 0, PAGE_W, footer_h, fill=1, stroke=0)
    c.setStrokeColor(ACCENT_GOLD)
    c.setLineWidth(1)
    c.line(0, footer_h, PAGE_W, footer_h)
    c.setFillColor(LIGHT_TAN)
    c.setFont("Helvetica-Oblique", 6.5)
    c.drawCentredString(PAGE_W / 2, 7, "Source: The Knotty Lumber Co.  \u00b7  theknottylumberco.ca  \u00b7  Woodworker's Species Guide")

    # Calculate remaining space for photos + FAQ
    remaining_h = y - footer_h - 4
    num_images = len(image_paths)
    faqs = sp.get("faqs", [])

    # Allocate: ~60% photos, ~40% FAQ (adjust if no images)
    if num_images > 0 and faqs:
        photo_area_h = remaining_h * 0.60
        faq_area_h = remaining_h * 0.40
    elif num_images > 0:
        photo_area_h = remaining_h * 0.80
        faq_area_h = remaining_h * 0.20
    else:
        photo_area_h = remaining_h * 0.30
        faq_area_h = remaining_h * 0.70

    # ── Product photos ──
    if num_images > 0:
        c.setFillColor(DARK_BROWN)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(MARGIN, y, "PRODUCT GALLERY")
        y -= 12

        usable_w = PAGE_W - 2 * MARGIN
        img_gap = 8
        ph = photo_area_h - 14  # after heading

        if num_images == 1:
            img_w = usable_w * 0.7
            _draw_photo(c, image_paths[0], MARGIN + (usable_w - img_w) / 2, y - ph, img_w, ph)
        elif num_images == 2:
            img_w = (usable_w - img_gap) / 2
            _draw_photo(c, image_paths[0], MARGIN, y - ph, img_w, ph)
            _draw_photo(c, image_paths[1], MARGIN + img_w + img_gap, y - ph, img_w, ph)
        else:  # 3 images
            large_h = (ph - img_gap) * 0.55
            _draw_photo(c, image_paths[0], MARGIN, y - large_h, usable_w, large_h)
            small_h = (ph - img_gap) * 0.45
            small_w = (usable_w - img_gap) / 2
            bottom_y = y - large_h - img_gap - small_h
            _draw_photo(c, image_paths[1], MARGIN, bottom_y, small_w, small_h)
            _draw_photo(c, image_paths[2], MARGIN + small_w + img_gap, bottom_y, small_w, small_h)

        y -= photo_area_h
    else:
        # Placeholder
        ph = photo_area_h - 10
        c.setFillColor(LIGHT_TAN)
        c.rect(MARGIN, y - ph, PAGE_W - 2 * MARGIN, ph, fill=1, stroke=0)
        c.setStrokeColor(MED_BROWN)
        c.setLineWidth(0.5)
        c.rect(MARGIN, y - ph, PAGE_W - 2 * MARGIN, ph, fill=0, stroke=1)
        c.setFillColor(MED_BROWN)
        c.setFont("Helvetica-Oblique", 11)
        c.drawCentredString(PAGE_W / 2, y - ph / 2 - 4, f"Visit theknottylumberco.ca for {sp['name']} products")
        y -= photo_area_h

    # ── FAQs using Frames for proper text wrapping ──
    y -= 4
    c.setFillColor(DARK_BROWN)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(MARGIN, y, "FREQUENTLY ASKED QUESTIONS")
    # Gold underline
    c.setStrokeColor(ACCENT_GOLD)
    c.setLineWidth(0.8)
    c.line(MARGIN, y - 3, MARGIN + 215, y - 3)
    y -= 8

    faq_bottom = footer_h + 6
    faq_h = y - faq_bottom
    usable_w = PAGE_W - 2 * MARGIN
    faq_gap = 10
    faq_col_w = (usable_w - faq_gap) / 2

    # Split FAQs into two columns
    faq_left = []
    faq_right = []
    for i, (q, a) in enumerate(faqs):
        target = faq_left if i % 2 == 0 else faq_right
        target.append(Paragraph(f'<b>Q: {q}</b>', styles["faq_q"]))
        target.append(Paragraph(a, styles["faq_a"]))

    # Create frames and render
    left_frame = Frame(MARGIN, faq_bottom, faq_col_w, faq_h,
                       leftPadding=0, rightPadding=4, topPadding=0, bottomPadding=0,
                       showBoundary=0)
    right_frame = Frame(MARGIN + faq_col_w + faq_gap, faq_bottom, faq_col_w, faq_h,
                        leftPadding=4, rightPadding=0, topPadding=0, bottomPadding=0,
                        showBoundary=0)
    left_frame.addFromList(faq_left, c)
    right_frame.addFromList(faq_right, c)

def _draw_photo(c, img_path, x, y, max_w, max_h):
    """Draw an image scaled to fit within max_w x max_h, with border."""
    try:
        pil_img = PILImage.open(img_path)
        iw, ih = pil_img.size
        # Scale to fit
        scale = min(max_w / iw, max_h / ih)
        draw_w = iw * scale
        draw_h = ih * scale
        # Center in the allocated space
        dx = x + (max_w - draw_w) / 2
        dy = y + (max_h - draw_h) / 2
        # Background
        c.setFillColor(WARM_CREAM)
        c.rect(x, y, max_w, max_h, fill=1, stroke=0)
        # Image
        c.drawImage(ImageReader(img_path), dx, dy, draw_w, draw_h, preserveAspectRatio=True)
        # Border
        c.setStrokeColor(MED_BROWN)
        c.setLineWidth(0.5)
        c.rect(x, y, max_w, max_h, fill=0, stroke=1)
    except Exception as e:
        # Fallback: draw placeholder
        c.setFillColor(LIGHT_TAN)
        c.rect(x, y, max_w, max_h, fill=1, stroke=0)
        c.setStrokeColor(MED_BROWN)
        c.setLineWidth(0.5)
        c.rect(x, y, max_w, max_h, fill=0, stroke=1)
        c.setFillColor(GREY)
        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(x + max_w / 2, y + max_h / 2, "Image unavailable")

def _wrap_text(c, text, font, size, max_w):
    """Simple word-wrap helper."""
    words = text.split()
    lines = []
    current = ""
    for w in words:
        test = current + " " + w if current else w
        if c.stringWidth(test, font, size) <= max_w:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines

# ── Main ────────────────────────────────────────────────────────

def main():
    output_dir = os.path.dirname(os.path.abspath(__file__))
    styles = make_styles()

    for sp in SPECIES:
        name = sp["name"]
        safe_name = name.lower().replace(" ", "_")
        pdf_path = os.path.join(output_dir, f"{safe_name}_reference_card.pdf")

        print(f"\n{'='*50}")
        print(f"Generating: {name}")
        print(f"{'='*50}")

        # Download images
        print(f"  Downloading images...")
        image_paths = []
        if sp["collection_slug"]:
            img_urls = get_collection_images(sp["collection_slug"], max_images=3)
        else:
            img_urls = get_blog_images(name)

        for i, url in enumerate(img_urls):
            path = download_image(url, name, i)
            if path:
                image_paths.append(path)
                print(f"    ✓ Image {i+1}: {os.path.basename(path)}")

        # Create PDF
        print(f"  Building PDF...")
        c = canvas.Canvas(pdf_path, pagesize=letter)

        # Page 1: Front (text content)
        # Background
        c.setFillColor(WARM_CREAM)
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        generate_front_page(c, sp, styles)
        c.showPage()

        # Page 2: Back (photos + FAQ)
        c.setFillColor(WARM_CREAM)
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        generate_back_page(c, sp, image_paths, styles)
        c.showPage()

        c.save()
        print(f"  ✓ Saved: {pdf_path}")

    print(f"\n{'='*50}")
    print(f"Done! Generated {len(SPECIES)} reference cards.")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
