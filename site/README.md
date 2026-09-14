# VLA-RAIL Website

Project site for [VLA-RAIL](https://github.com/zhaoyongsheng/vla_infer), built with
**Astro + Tailwind CSS**, with documentation powered by **Starlight**.

## Structure

- `src/pages/index.astro` — landing page (Hero, Teaser, Features, Framework,
  Chunk Transition, Results, Quickstart, Models & Robots, Citation).
- `src/components/*` — landing page sections.
- `src/content/docs/*` — Starlight documentation.
- `public/media/*` — images and demo video (copied from `../data/media`).
- `.github/workflows/deploy-site.yml` — builds and publishes to the
  `gh-pages` branch.

## Local development

```bash
npm install
npm run dev      # http://localhost:4321/vla_infer/
npm run build    # outputs to dist/
```

## Deployment

Pushing to the deploy branch (`main` by default — adjust in
`deploy-site.yml`) builds the site and publishes it to the `gh-pages` branch
via GitHub Pages. Set **Settings → Pages → Source = Deploy from a branch /
gh-pages** and enable Actions write permission.

> The site is served from `/vla_infer/`. If you bind a custom domain, change
> `base` in `astro.config.mjs` to `'/'`.

## TODO (awaiting assets)

- [ ] Real robot demonstration videos for the Results section.
- [ ] Core performance metrics (inference frequency, latency, success rate).
- [ ] `public/og.png` (1200×630) for social sharing.
