# Open-RAIL Website

Project site for [Open-RAIL](https://github.com/CMCC-TAO/open-rail), built with
**Astro + Tailwind CSS**, with documentation powered by **Starlight**.

## Structure

- `src/pages/index.astro` — landing page. Section order:
  Hero → Positioning → Capabilities → Models & Robots → Community →
  Quickstart → Tutorials → Footer.
- `src/components/*` — one file per landing-page section, plus shared pieces
  (`Nav`, `HeroVideo`, `Highlight`, the diagram components, `Footer`).
- `src/content/config.ts` — loads Starlight docs from the repository-root
  `docs/` folder (markdown does **not** live under `site/`). `base` is passed as
  a `URL`, not a path string: a Windows path such as `D:\repo\docs` gets parsed
  downstream as the URL scheme `d:` and breaks `astro build` on Windows.
- `src/data/site.ts` — site name, description, platforms, supported models,
  supported robots, tutorials, paper/citation, contributors.
- `src/i18n.ts` — all landing-page copy. Edit wording here, not in components.
- `public/media/*` — images and demo video. **Generated folder**: the `predev` /
  `prebuild` scripts copy `../data/media` into it, so edit the source files under
  `data/media/` instead.
- `public/og.png` — 1200×630 social-sharing card (`og:image`).
- `public/robots.txt` — crawler policy.
- `.github/workflows/deploy-site.yml` — builds and publishes to GitHub Pages.

## Local development

```bash
npm install
npm run dev      # http://localhost:4321/open-rail/
npm run build    # outputs to dist/
```

> `npm run build` runs a `prebuild` step written for POSIX shells
> (`mkdir -p` / `cp -rf`). On Windows, call `npx astro build` directly —
> `public/media/` is already populated.

## Deployment

Pushing to `main` (paths: `docs/**`, `site/**`, `data/media/**`) triggers
`.github/workflows/deploy-site.yml`, which builds `site/` and publishes it with
`actions/upload-pages-artifact` + `actions/deploy-pages`.

Set **Settings → Pages → Source = GitHub Actions** (not "Deploy from a branch").
There is no `gh-pages` branch.

> The site is served from `/open-rail/`. If you bind a custom domain, change
> `base` in `astro.config.mjs` to `'/'`.

## TODO (awaiting assets)

- [ ] Three of the five tutorial slots in `src/data/site.ts` still have no video
      (`youtube: ''`), so they render the "Video coming soon" placeholder.
- [ ] Downscale `data/media/architecture.png` (currently 10388×5640, ≈2 MB,
      displayed at ≈1024 px) and the four `data/media/robots/*.png` logos
      (1920×1920 each, displayed at ≈48–96 px).
- [ ] Drop the unused `data/media/*.zh-CN.png` diagrams (≈6 MB) — the site is
      English-only.
- [ ] Add `@astrojs/sitemap` so `/open-rail/sitemap.xml` exists.
