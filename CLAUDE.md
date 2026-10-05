# Project Guidelines

## Git

- Commit after making changes, once the work is complete and the build passes. Don't commit a knowingly broken state.
- Don't `push` or deploy unless asked.

## Build & Deploy

- Astro static site at repo root
- Build: `npm run build` (outputs to `dist/`)
- Dev: `npm run dev`

### Deploy
```sh
rsync -rv --delete dist/* fjania.com:~/sites/fjania.com
rsync -rv --delete dist/* fjania.com:~/sites/franklyjania.com
rsync -rv --delete dist/* fjania.com:~/sites/frankjania.com
```

## Travel page (`/travel/`)

Interactive visualization of Frank's flight history.

- Source of truth: `~/.claude-second-brain/my-brain/flight-history/flights.csv`.
- Mirror it into the repo with `npm run sync-flights` (one-line `cp`; checked in so the build is reproducible from a fresh clone).
- Build-time parse happens in `src/lib/parseFlights.ts`. Data is embedded inline in the page as two `<script type="application/json">` islands (flights + world-110m topology).
- Client modules live in `src/scripts/travel/` — `state.js` is the central pub/sub; `map.js`, `timeline.js`, `stats.js`, `leaderboards.js`, `filters.js`, `tooltip.js`, `format.js` are views/helpers.
- Map uses modular D3 (`d3-geo`/`d3-selection`/`d3-zoom`) + `topojson-client` with `world-atlas/countries-110m.json` vendored in `src/data/world-110m.json`.

When the CSV grows past ~5,000 rows, switch from embedding to fetching a JSON file from `public/data/`.

## Router Bit Inventory

### Approved product link sources
When adding router bits or linking to product pages, only use these sources:
- woodpeck.com
- bitsandbits.com
- whitesiderouterbits.com
- rockler.com

**Never use Amazon.** If none of the approved sources carry a product, ask the user before using any other source.

## Turning Tools (`/workshop/turning/`)

- Content collection `src/content/turning/*.yml` (one file per tool; schema in `src/content/config.ts`), images in `public/turning/{slug}.jpg`.
- Pages are fully data-driven: `src/pages/workshop/turning/index.astro` (grouped listing) and `[slug].astro` (detail). Adding a tool needs only a YAML file and an image.
- YAML gotchas: quote any value containing `#` (e.g. `"#2 Morse"`) or `: `, and quote ISO dates in `purchased`.
- Sharpening guidance in these entries references the Tormek jigs documented under `/workshop/manuals/tormek-*`.

## Manuals: videos and merged PDFs

- Manual content pages may embed Tormek/vendor YouTube videos with the `.video` / `.video-row` markup styled in `src/styles/manuals.css` (youtube-nocookie iframes).
- The three Tormek manuals host merged PDFs built with pypdf from Tormek's per-jig leaflets (plus the full HB-10 handbook on `tormek-t8`). Source PDFs are re-downloadable from each product page on tormek.com under `/download/`.
