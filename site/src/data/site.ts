export const site = {
  name: 'Open-RAIL',
  tagline: 'Where inference ends, real robots begin',
  description:
    'Open-RAIL: plug-and-play async inference middleware linking 20 VLA/WAM models to 4 heterogeneous robots. 50–100 lines per model, no retraining, Apache-2.0.',
  email: 'zhengjiahui@cmhi.chinamobile.com',
  platforms: [
    { label: 'GitHub', href: 'https://github.com/CMCC-TAO/open-rail', icon: 'github' },
    { label: 'Gitee', href: 'https://gitee.com/cmcc-tao/open-rail', icon: 'gitee' },
    { label: 'AI.Huanxin', href: 'https://aihuanxin.cn/project/detail/CMHI_EAI/open-rail/type=org', icon: 'hf' },
  ],
  whitepaper: 'https://arxiv.org/abs/2512.24673',
  // Optional hero overview video. Set to a YouTube watch URL, embed URL,
  // or 11-char video id; leave '' to show a placeholder.
  heroVideo: 'https://www.youtube.com/watch?v=1dpdDsb8Trg',
};

// VLA models already adapted / supported by Open-RAIL.
// `soon: true` = adapted but not yet included in this release (shown as "Release soon").
export const supportedModels: { name: string; note: string; soon?: boolean }[] = [
  // Merged into master.
  { name: 'GR00T N1', note: 'NVIDIA GR00T humanoid foundation' },
  { name: 'GR00T N1.5', note: 'NVIDIA GR00T humanoid foundation' },
  { name: 'GR00T N1.6', note: 'NVIDIA GR00T humanoid foundation' },
  { name: 'π0', note: 'Physical Intelligence VLA' },
  { name: 'π0.5', note: 'Physical Intelligence VLA' },
  { name: 'TAO', note: 'China Mobile TAO Team VLA base model' },
  { name: 'GO1', note: 'AgiBot GO-1 generalist VLA policy' },
  { name: 'SmolVLA', note: 'HuggingFace SmolVLA VLA policy' },
  { name: 'ACT', note: 'Action Chunking Transformer' },
  { name: 'RDT', note: 'Robotics Diffusion Transformer' },
  { name: 'DM0.5', note: 'OpenDM diffusion policy' },
  { name: 'WALL-X', note: 'Wall-X policy' },
  // Adapted, pending release.
  { name: 'T-Rex', note: 'Visual-prompt VLA', soon: true },
  { name: 'DeCAL', note: 'DeCAL adaptation', soon: true },
  { name: 'DreamZero', note: 'Zero-shot visuomotor policy', soon: true },
  { name: 'GigaWorld-Policy-0.5', note: 'GigaWorld world-model policy', soon: true },
  { name: 'LingBot-VA', note: 'LingBot VLA model', soon: true },
  { name: 'GR00T N1.7', note: 'NVIDIA GR00T humanoid foundation', soon: true },
  { name: 'GR00T N1.7 EEF', note: 'GR00T N1.7 end-effector variant', soon: true },
  { name: 'XVLA EEF', note: 'XVLA end-effector variant', soon: true },
];

// Heterogeneous humanoid robots adapted by Open-RAIL.
// `soon: true`  = adapter ready, ships in the next release (badge: "Coming soon").
// `kind: 'sim'` = simulation backend, listed on its own; it is not a robot body.
export const supportedRobots: {
  name: string;
  note: string;
  tags?: string[];
  soon?: boolean;
  kind?: 'sim';
}[] = [
  // Adapted and shipped in the current release.
  { name: 'AgiBot G1', note: 'Dual-arm wheeled humanoid', tags: ['Gripper', 'Hand'] },
  { name: 'China Mobile Lingxi', note: 'Folding wheeled dual-arm humanoid', tags: ['Gripper', 'Hand'] },
  { name: 'NAVIAI-WA2', note: 'Dual-arm wheeled humanoid', tags: ['Hand'] },
  // Adapter ready, shipping in the next release.
  { name: 'Unitree G1', note: 'Dual-arm bipedal humanoid', tags: ['Hand'], soon: true },
  // Simulation backend.
  { name: 'Mock', note: 'LeRobot simulation backend, no hardware needed', kind: 'sim' },
];

// Tutorials: a series of walkthrough videos (YouTube or Bilibili).
// For YouTube set `youtube` to a watch/embed URL or 11-char id.
// For Bilibili set `bilibili` to a bilibili.com/video/BV... URL.
// Leave both empty to show a placeholder for that slot.
export const tutorials = [
  {
    title: 'Quick Start: Get Familiar with Open-RAIL',
    subtitle: 'Walk through the Quick Start video and learn the basic workflow, core controls, and key features of Open-RAIL.',
    bilibili: 'https://www.bilibili.com/video/BV1awe36gEqF/',
  },
  {
    title: 'Run Open-RAIL on a Real Robot',
    subtitle: 'See how to connect a real robot, use the Web Client for configuration and control, monitor execution, and debug the VLA&WAM pipeline in real time.',
    bilibili: 'https://www.bilibili.com/video/BV1Ywe36gEMM/',
  },
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
  title: 'VLA-RAIL: A Real-Time Asynchronous Inference Linker for VLA Models and Robots',
  authors: 'Yongsheng Zhao and Lei Zhao and Baoping Cheng and Gongxin Yao and Xuanzhang Wen and Han Gao',
  venue: 'arXiv:2512.24673, 2025',
  url: 'https://arxiv.org/abs/2512.24673',
  pdf: 'https://arxiv.org/pdf/2512.24673',
  bibtex: `@misc{zhao2025vlarailrealtimeasynchronousinference,
      title={VLA-RAIL: A Real-Time Asynchronous Inference Linker for VLA Models and Robots},
      author={Yongsheng Zhao and Lei Zhao and Baoping Cheng and Gongxin Yao and Xuanzhang Wen and Han Gao},
      year={2025},
      eprint={2512.24673},
      archivePrefix={arXiv},
      primaryClass={cs.RO},
      url={https://arxiv.org/abs/2512.24673},
}`,
};

// Contributors, grouped by role. Replace the placeholders with real names.
export const contributors = [
  { role: 'Project Leader', members: ['Yongsheng Zhao'] },
  { role: 'Core Developers', members: ['Lei Zhao', 'Gongxin Yao', 'Jiayin Deng', 'Xuanzhang Wen', 'Han Gao', 'Zean Liu', 'Wen Li', 'Taotao Tian'] },
  { role: 'Test Engineers', members: ['Yingying Yan'] },
  { role: 'Product Managers', members: ['Jiahui Zheng', 'Chaohua Lin', 'Yafei Peng'] },
];
