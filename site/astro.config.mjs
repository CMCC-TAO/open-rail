import { defineConfig } from 'astro/config';
import { fileURLToPath } from 'node:url';
import tailwind from '@astrojs/tailwind';
import starlight from '@astrojs/starlight';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import remarkDocsLinks from './src/plugins/remark-docs-links.mjs';

// GitHub Pages project site is served from /open-rail/.
// If you bind a custom domain later, change BASE to '/'.
const BASE = '/open-rail/';

// The docs live outside the Astro project root, so Astro leaves the relative
// `.md` links in them unresolved. `remarkDocsLinks` rewrites those into real
// URLs (site route or GitHub), and needs the filesystem path to do it.
const docsRoot = fileURLToPath(new URL('../docs', import.meta.url));

export default defineConfig({
  base: BASE,
  site: 'https://cmcc-tao.github.io',
  // `$...$` / `$$...$$` in the docs render as math instead of raw text.
  // The KaTeX stylesheet is pulled in through Starlight's `customCss`.
  markdown: {
    remarkPlugins: [remarkMath, [remarkDocsLinks, { docsRoot, base: BASE }]],
    rehypePlugins: [rehypeKatex],
  },
  integrations: [
    tailwind({ applyBaseStyles: false }),
    starlight({
      title: 'Open-RAIL',
      description: 'A Real-Time Asynchronous Inference Linker for VLA Models and Robots',
      // Single, unprefixed English locale (avoids Starlight probing a non-existent `/en/` path).
      defaultLocale: 'root',
      locales: { root: { label: 'English', lang: 'en-US' } },
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/CMCC-TAO/open-rail' },
      ],
      components: {
        SiteTitle: './src/components/starlight/SiteTitle.astro',
      },
      customCss: ['./src/styles/katex.css'],
      sidebar: [
        { label: 'Getting Started', link: '/getting-started/' },
        { label: 'Architecture', link: '/architecture/' },
        { label: 'Configuration', link: '/configuration/' },
        { label: 'Troubleshooting', link: '/troubleshooting/' },
        { label: 'Dataset Demo', link: '/demo-running-on-dataset/' },
        {
          label: 'Guides',
          items: [
            { label: 'Add a VLA Model', link: '/guides/add-new-model/' },
            { label: 'Add a Robot', link: '/guides/add-new-robot/' },
          ],
        },
      ],
    }),
  ],
});
