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
// `soon: true` = adapted but not yet merged into master (shown as "Release soon").
export const supportedModels: { name: string; note: string; soon?: boolean }[] = [
  // Merged into master.
  { name: 'GROOT N1', note: 'NVIDIA GR00T humanoid foundation' },
  { name: 'GROOT N1.5', note: 'NVIDIA GR00T humanoid foundation' },
  { name: 'GROOT N1.6', note: 'NVIDIA GR00T humanoid foundation' },
  { name: 'PI0', note: 'Physical Intelligence VLA' },
  { name: 'PI0.5', note: 'Physical Intelligence VLA' },
  { name: 'TAO', note: 'Lingxi Shutao VLA base' },
  { name: 'GO1', note: 'Generalist VLA policy' },
  { name: 'SmoIVLA', note: 'SmoIVLA VLA policy' },
  { name: 'ACT', note: 'Action Chunking Transformer' },
  { name: 'RDT', note: 'Robotics Diffusion Transformer' },
  // Adapted, pending merge into master.
  { name: 'DM0.5', note: 'Diffusion policy', soon: true },
  { name: 'Wall-oss', note: 'Wall-OSS open model', soon: true },
  { name: 'T-Rex', note: 'Visual-prompt VLA', soon: true },
  { name: 'DeCAL', note: 'DeCAL adaptation', soon: true },
  { name: 'DreamZero', note: 'Zero-shot visuomotor policy', soon: true },
  { name: 'GigaWorld-Policy-0.5', note: 'GigaWorld world-model policy', soon: true },
  { name: 'LingBot-VA', note: 'LingBot VLA model', soon: true },
  { name: 'GROOT N1.7', note: 'NVIDIA GR00T humanoid foundation', soon: true },
  { name: 'GROOT N1.7 EEF', note: 'GROOT N1.7 end-effector variant', soon: true },
  { name: 'XVLA EEF', note: 'XVLA end-effector variant', soon: true },
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
