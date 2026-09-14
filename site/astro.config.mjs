import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import starlight from '@astrojs/starlight';

// GitHub Pages project site is served from /vla_infer/.
// If you bind a custom domain later, change base to '/'.
export default defineConfig({
  base: '/vla_infer/',
  site: 'https://zhaoyongsheng.github.io',
  integrations: [
    tailwind({ applyBaseStyles: false }),
    starlight({
      title: 'Open-RAIL',
      description: 'A Real-Time Asynchronous Inference Linker for VLA Models and Robots',
      // Single, unprefixed English locale (avoids Starlight probing a non-existent `/en/` path).
      defaultLocale: 'root',
      locales: { root: { label: 'English', lang: 'en-US' } },
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/zhaoyongsheng/vla_infer' },
      ],
      components: {
        SiteTitle: './src/components/starlight/SiteTitle.astro',
      },
      sidebar: [
        { label: 'Getting Started', link: '/getting-started/' },
        { label: 'Architecture', link: '/architecture/' },
        { label: 'Configuration', link: '/configuration/' },
        { label: 'Troubleshooting', link: '/troubleshooting/' },
        { label: 'Dataset Demo', link: '/demo-running-on-dataset/' },
        {
          label: 'Guides',
          items: [
            { label: 'Add a VLA Model', link: '/guides/add-new-vla-model/' },
            { label: 'Add a Robot', link: '/guides/add-new-robot/' },
          ],
        },
      ],
    }),
  ],
});
