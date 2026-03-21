# Project Guidelines

## Build & Deploy

### Main site (`site/`)
- Static site with pre-built output in `site/_build/`

### Workshop (`workshop/`)
- Astro static site, base path `/workshop/`
- Build: `cd workshop && npm run build` (outputs to `workshop/dist/`)
- Dev: `cd workshop && npm run dev`

### Deploy
Deploy both the main site and workshop to the server:
```sh
# Main site (all 3 domains)
rsync -rv site/_build/* fjania.com:~/sites/fjania.com
rsync -rv site/_build/* fjania.com:~/sites/franklyjania.com
rsync -rv site/_build/* fjania.com:~/sites/frankjania.com

# Workshop
rsync -rv workshop/dist/* fjania.com:~/sites/fjania.com/workshop/
rsync -rv workshop/dist/* fjania.com:~/sites/franklyjania.com/workshop/
rsync -rv workshop/dist/* fjania.com:~/sites/frankjania.com/workshop/
```

## Router Bit Inventory

### Approved product link sources
When adding router bits or linking to product pages, only use these sources:
- woodpeck.com
- bitsandbits.com
- whitesiderouterbits.com

**Never use Amazon.** If none of the approved sources carry a product, ask the user before using any other source.
