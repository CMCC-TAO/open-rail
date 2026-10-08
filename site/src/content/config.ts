import { defineCollection } from 'astro:content';
import { docsSchema } from '@astrojs/starlight/schema';
import { glob } from 'astro/loaders';

// Load docs from the project-root `docs/` folder (outside `site/`) so that
// relative asset links written in the docs (e.g. `../data/media/...`,
// `../../conf/...`, `../README.md`) resolve against the repository root.
//
// Pass the URL itself, not `fileURLToPath(...)`: the glob loader runs
// `new URL(base, config.root)`, and a Windows path such as `D:\repo\docs` is
// parsed there as the URL scheme `d:` — which makes `fileURLToPath` throw
// "The URL must be of scheme file" and breaks `astro build` on Windows.
const docsRoot = new URL('../../../docs', import.meta.url);

export const collections = {
  docs: defineCollection({
    loader: glob({ pattern: '**/*.md', base: docsRoot }),
    schema: docsSchema(),
  }),
};
