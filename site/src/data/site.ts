export const site = {
  name: 'OPEN-RAIL 2026',
  tagline: 'Where inference ends, real robots begin',
  description:
    'Open-source infrastructure bridging VLA (Vision-Language-Action) models and physical robots — stable, compatible, and self-evolving.',
  email: 'vla-rail@opensource.org',
  platforms: [
    { label: 'GitHub', href: 'https://github.com/CMCC-TAO/open-rail', icon: 'github' },
    { label: 'Gitee', href: 'https://gitee.com/cmcc-tao/open-rail', icon: 'gitee' },
    { label: 'HuggingFace', href: '#', icon: 'hf' },
  ],
  whitepaper: '#',
};

// VLA models already adapted / supported by Open-RAIL.
export const supportedModels = [
  { name: 'NVIDIA GR00T', note: 'Foundation model for humanoid manipulation' },
  { name: 'TAO', note: 'Lingxi Shutao VLA base' },
  { name: 'RDT', note: 'Robotic Diffusion Transformer' },
  { name: 'DreamZero', note: 'Zero-shot visuomotor policy' },
  { name: 'π₀ (PI)', note: 'Physical Intelligence vision-action model' },
  { name: 'ACT', note: 'Action Chunking Transformer' },
  { name: 'OpenVLA', note: 'Open vision-language-action model' },
  { name: 'RT-2', note: 'Vision-language-action robot model' },
  { name: 'Octo', note: 'Open generalist robot policy' },
  { name: 'Diffusion Policy', note: 'Denoising action model' },
];

// Heterogeneous humanoid robots already adapted.
export const supportedRobots = [
  { name: 'Unitree G1', note: 'Bipedal humanoid' },
  { name: 'AgileX Spirit G1', note: 'Bipedal humanoid' },
  { name: 'China Mobile Lingxi', note: 'Embodied humanoid' },
  { name: 'Zhejiang Humanoid', note: 'Research humanoid' },
];

// Reserved showcase video section (placeholder until the clip is provided).
export const showcase = {
  caption: 'Robot Tea House — 17-step Chinese tea ceremony',
  note: 'Demo video coming soon. Place your file at public/media/showcase.mp4 and it will render here.',
};

// Paper / citation info.
export const paper = {
  title: 'Open-RAIL 2026: A Real-Time Asynchronous Inference Linker for VLA Models and Robots',
  authors: 'Open-RAIL Team',
  venue: 'arXiv preprint, 2026',
  url: '#',
  bibtex: `@misc{openrail2026,
  title  = {Open-RAIL 2026: A Real-Time Asynchronous Inference Linker for VLA Models and Robots},
  author = {Open-RAIL Team},
  year   = {2026},
  note   = {arXiv preprint}
}`,
};

// Contributors, grouped by role. Replace the placeholders with real names.
export const contributors = [
  { role: 'Technical Leader', members: ['Yongsheng Zhao'] },
  { role: 'Core Developers', members: ['Developer A', 'Developer B', 'Developer C'] },
  { role: 'Testing', members: ['Tester A'] },
  { role: 'Product', members: ['Product Manager A'] },
];
