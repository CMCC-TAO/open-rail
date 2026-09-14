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
      title: 'VLA-RAIL',
      description: 'A Real-Time Asynchronous Inference Linker for VLA Models and Robots',
      // Single, unprefixed English locale (avoids Starlight probing a non-existent `/en/` path).
      defaultLocale: 'root',
      locales: { root: { label: 'English', lang: 'en-US' } },
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/zhaoyongsheng/vla_infer' },
      ],
      sidebar: [
        { label: 'Introduction', link: '/docs/' },
        { label: 'Installation', link: '/docs/installation/' },
        { label: 'Configuration', link: '/docs/configuration/' },
        { label: 'Models & Robots', link: '/docs/models-robots/' },
      ],
    }),
  ],
});
