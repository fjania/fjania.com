# Project Guidelines

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
