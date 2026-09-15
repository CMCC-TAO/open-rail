export const site = {
  name: 'OPEN-RAIL 2026',
  tagline: 'Where inference ends, real robots begin',
  description:
    'Open-source infrastructure bridging VLA (Vision-Language-Action) models and physical robots — stable, compatible, and self-evolving.',
  email: 'vla-rail@opensource.org',
  platforms: [
    { label: 'GitHub', href: 'https://github.com/CMCC-TAO/open-rail', icon: 'github' },
    { label: 'Gitee', href: 'https://gitee.com/cmcc-tao/open-rail', icon: 'gitee' },
    { label: 'AI.Huanxin', href: '#', icon: 'hf' },
  ],
  whitepaper: '#',
  // Optional hero overview video. Set to a YouTube watch URL, embed URL,
  // or 11-char video id; leave '' to show a placeholder.
  heroVideo: 'https://www.youtube.com/watch?v=1cllCVK-9lo',
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

// Tutorials: a series of YouTube-embedded walkthrough videos.
// Set `youtube` to a YouTube watch URL, embed URL, or an 11-char video id.
// Leave it '' to show a placeholder for that slot.
export const tutorials = [
  {
    title: 'Robot Tea House — 17-step Chinese tea ceremony',
    subtitle: 'Open-RAIL orchestrates a full tea-serving routine on a humanoid robot.',
    youtube: '',
  },
  {
    title: 'Demo: Running on a dataset',
    subtitle: 'Replay recorded episodes and visualize real-time inference end to end.',
    youtube: '',
  },
  {
    title: 'Add a new VLA model in 5 minutes',
    subtitle: 'Plug a checkpoint into Open-RAIL without touching upper-layer logic.',
    youtube: '',
  },
];

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
