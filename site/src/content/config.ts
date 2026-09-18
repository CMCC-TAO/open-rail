import { defineCollection } from 'astro:content';
import { docsSchema } from '@astrojs/starlight/schema';
import { glob } from 'astro/loaders';
import { fileURLToPath } from 'node:url';

// Load docs from the project-root `docs/` folder (outside `site/`) so that
// relative asset links written in the docs (e.g. `../data/media/...`,
// `../../conf/...`, `../README.md`) resolve against the repository root.
const docsRoot = fileURLToPath(new URL('../../../docs', import.meta.url));

export const collections = {
  docs: defineCollection({
    loader: glob({ pattern: '**/*.md', base: docsRoot }),
    schema: docsSchema(),
  }),
};
