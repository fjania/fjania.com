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

## Router Bit Inventory

### Approved product link sources
When adding router bits or linking to product pages, only use these sources:
- woodpeck.com
- bitsandbits.com
- whitesiderouterbits.com

**Never use Amazon.** If none of the approved sources carry a product, ask the user before using any other source.
