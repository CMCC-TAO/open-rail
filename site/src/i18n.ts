export type Locale = 'en';

export const ui = {
  en: {
    nav: {
      tagline: 'Where inference ends, real robots begin',
      overview: 'Overview',
      capabilities: 'Capabilities',
      architecture: 'Architecture',
      models: 'Models',
      robots: 'Robots',
      showcase: 'Tutorials',
      getInvolved: 'Get Involved',
      quickstart: 'Quick Start',
      docs: 'Docs',
      themeLabel: 'Toggle theme',
    },
    hero: {
      eyebrow: 'INFRA FOR EMBODIED AI · LAY THE RAIL BETWEEN ACTION MODELS AND PHYSICAL ROBOTS',
      titleSuffix: 'A Real-time Asynchronous Inference Linker for VLA/WAM Models and Robots',
      titleHighlight: 'Open-RAIL: ',
      sub: 'Asynchronous Inference · Motion Smoothing & Speed Scaling · Closed-Loop Evolution',
      desc: 'Open‑RAIL is a plug‑and‑play open‑source asynchronous inference middleware for diverse VLA/WAM models and heterogeneous robots. Using two‑stage trajectory smoothing and fusing, it resolves inference‑control mismatch, motion jitter to boost execution speed, motion smoothness and task success rates while preserving original action policies. It supports runtime real‑robot data recording and human‑in‑the‑loop intervention for closed‑loop reinforcement learning.',
      features: [
        'Real-time asynchronous scheduling — bridges VLA/WAM inference and physical robot actuation.',
        'Motion smoothing & speed scaling — eliminates jitter and boosts execution speed and success rate.',
        'Drop-in compatibility — plug mainstream VLA models and heterogeneous humanoids into one pipeline.',
        'Edge-cloud coordination — flexible deployment across edge devices and the cloud.',
        'Closed-loop evolution — real-robot data recording and human-in-the-loop for continuous self-evolution.',
      ],
      btnStart: 'Quick Start',
      btnPaper: 'Technical Paper',
      presented: 'Presented by ',
    },
    pos: {
      eyebrow: 'POSITIONING',
      title: 'Open-RAIL: The Highway Connecting the VLA Brain and the Robot Body',
      body: 'VLA model = brain, understanding instructions and generating action intent; robot body = body, perceiving the environment and executing physical actions; Open-RAIL is the middleware that handles model onboarding, task scheduling, motion buffering & smoothing, real-robot execution, state feedback, and data logging.',
      roles: [
        { name: 'RAIL Server', desc: 'Task Scheduling · Model Inference · Data Management' },
        { name: 'RAIL Client', desc: 'Local Execution · Perception Collection' },
        { name: 'Web Panel', desc: 'Execution Monitoring · Parameter Tuning · Data Review' },
      ],
      diagramCaption: 'Server-Client distributed roles (click to enlarge)',
    },
    cap: {
      eyebrow: 'CORE CAPABILITIES',
      title: 'Three Core Capabilities: Stable ｜ Compatible ｜ Evolvable',
      expand: 'Expand technical details',
      collapse: 'Collapse technical details',
      items: [
        {
          tag: 'Capability 1',
          title: 'Stable',
          subtitle: 'Async pipeline + two-stage online trajectory smoothing',
          summary:
            'A three-thread async pipeline eliminates the 10x+ frequency gap between inference and control; two-stage online smoothing removes intra-segment jitter and inter-segment jumps, cutting joint acceleration std-dev by two orders of magnitude.',
          metrics: [
            { value: '30Hz', label: 'Observation thread' },
            { value: '5–10Hz', label: 'Inference thread' },
            { value: '267Hz', label: 'Control thread' },
            { value: '↓ 0.1 rad/s²', label: 'Accel. std-dev (was 10+)' },
          ],
          details: [
            'Three-thread async pipeline: observation 30Hz, inference 5–10Hz, control 267Hz; supports async / sync dual modes.',
            'Two-stage online smoothing: intra-chunk smoothing (cubic spline / polynomial fitting removes single-segment jitter); inter-chunk fusion (concatenation + PD clamping, min-jerk removes inter-segment jumps).',
            'Result: joint acceleration std-dev drops from 10+ to 0.1 rad/s² — two orders of magnitude lower — eliminating hardware shock.',
          ],
        },
        {
          tag: 'Capability 2',
          title: 'Compatible',
          subtitle: 'Swap models, bodies, or deployments without rewriting upper logic',
          summary:
            'RobotBase unified hardware interface, standardized inference interface, and Server-Client distributed architecture collapse robot swaps, VLA-model swaps, and deployment swaps into low-level configuration.',
          metrics: [
            { value: '4', label: 'Heterogeneous humanoid robots adapted' },
            { value: '10', label: 'Mainstream VLA models supported' },
            { value: '50–100', label: 'Lines of code to integrate a new model' },
          ],
          details: [
            'Swap robots: RobotBase unified hardware interface, action_layout unified action mapping; already adapted Unitree G1, AgileX Spirit G1, China Mobile Lingxi, Zhejiang humanoid.',
            'Swap VLA models: standardized input/output inference interface; already supports 10 models including GR00T, TAO, RDT, DreamZero, PI, ACT; integrating a new model needs only 50–100 lines of business code.',
            'Swap deployments: Server-Client end-edge-cloud distributed architecture; Server can run on local body / edge / cloud, Client on the robot; switch deployment by changing only the comms address with zero upper-logic changes and auto-reconnect heartbeat.',
          ],
        },
        {
          tag: 'Capability 3',
          title: 'Evolve',
          subtitle: 'Running is data, intervention is teaching — the train-collect-evaluate flywheel',
          summary:
            'Automatic real-robot recording, online scoring, and human teleop correction form the train-collect-evaluate loop: inference execution → runtime collection → task evaluation → model retraining.',
          metrics: [
            { value: 'Parquet', label: 'Standard Episode format' },
            { value: 'sub_task', label: 'Online scoring granularity' },
            { value: 'VR', label: 'Teleop human correction' },
          ],
          details: [
            'Collect by running: real-robot runs auto-record images, joints, model outputs, and control commands into standard Parquet Episode data with incremental appends.',
            'Evaluate by executing: sub_task online scoring written synchronously, exportable as JSON / CSV and linked to the Episode.',
            'Teach by intervention: VR teleop human-correction hybrid mode; when the model errs, a human intervenes and the human trajectory is time-aligned with the original inference trajectory to produce high-quality training samples.',
            'Train-collect-evaluate flywheel: inference execution → runtime data collection → task evaluation feedback → model retraining; one pipeline pushes models to the robot and returns real-robot data back for training.',
          ],
        },
      ],
    },
    community: {
      eyebrow: 'OPEN COMMUNITY',
      title: 'Open and Collaborative Open-Source Community',
      vision:
        'Open-sourcing the proven model-to-robot engineering pipeline so developers focus on model innovation, robot bodies, and scenarios instead of rebuilding deployment plumbing.',
      templates: [
        { title: 'Model Template', body: 'Observation input, inference interface, action output specs; 10 VLA models adapted.' },
        { title: 'Robot Template', body: 'Body parameters, action layout, comms adaptation templates; 4 heterogeneous robots referenced.' },
        { title: 'Evaluation Template', body: 'Scoring rules, metric logging, analysis export scripts.' },
        { title: 'Deployment Template', body: 'End-edge-cloud distributed deployment examples.' },
      ],
      entryLabel: 'Open-source entry',
      paperLabel: 'Technical Paper',
      resourcesLabel: 'Resources: full docs · hands-on video tutorials · API manual · troubleshooting guide',
      values: [
        { who: 'Model teams', value: 'Skip real-robot deployment dev, focus on algorithm innovation' },
        { who: 'Robot teams', value: 'Reuse execution, smoothing, and data-collection base, focus on body control' },
        { who: 'Application teams', value: 'Lower scenario-deployment barrier, accelerate from sim demo to physical robots' },
      ],
    },
    quick: {
      eyebrow: 'GET STARTED',
      title: 'Get Started: Run Open-RAIL in Three Steps',
      steps: [
        { title: 'Simulation', body: 'Docker virtual environment; validate algorithms and orchestrate tasks without a real robot.' },
        { title: 'Hardware Access', body: 'Load drivers and connect robot hardware with one click.' },
        { title: 'Debug & Iterate', body: 'Web visualization panel, online tuning, hot model update, fast iteration.' },
      ],
      resourcesLabel: 'Developer resources: hands-on video library ｜ full technical docs ｜ developer community',
      start: 'Get Started',
      docsLabel: 'Documentation',
      docs: [
        { label: 'Getting Started', href: 'getting-started/' },
        { label: 'Architecture', href: 'architecture/' },
        { label: 'Configuration', href: 'configuration/' },
        { label: 'Troubleshooting', href: 'troubleshooting/' },
      ],
    },
    footer: {
      tagline: 'Where inference ends, real robots begin',
      repoLabel: 'Open-source Repos',
      paperLabel: 'Technical Whitepaper PDF',
      contactLabel: 'Contact & Collaboration',
      emailNote: 'Partnership inquiries · technical proposals · community contribution portal',
      copyright: 'Open-source release pending',
      org: 'China Mobile Embodied AI Industry Innovation Center, Open-RAIL Team',
      author: 'Embodied Model Team (TAO Team)',
    },
    diagrams: {
      serverClient: {
        server: 'RAIL Server',
        serverItems: ['Scheduling', 'Inference', 'Data Mgmt'],
        client: 'RAIL Client',
        clientItems: ['Local Exec', 'Sensing', 'Robot Body'],
        action: 'Action (ZMQ)',
        obs: 'Observation / State',
        web: 'Web Panel',
        webItems: 'Monitoring · Tuning · Review',
      },
      edgeCloud: {
        cloud: 'Cloud',
        cloudNote: 'RAIL Server (large-model inference)',
        edge: 'Edge',
        edgeNote: 'RAIL Server (lightweight/relay)',
        robot: 'Robot',
        robotNote: 'RAIL Client (local exec)',
        unified: 'One pipeline · switch deployment by changing only the comms address',
        unifiedNote: 'Zero change to upper logic · auto-reconnect heartbeat · Server flexibly on cloud / edge / on-body',
      },
      flywheel: {
        title: 'Train-Collect',
        sub: 'Self-evolving flywheel',
        deploy: 'Infer & Exec',
        deployNote: 'Deploy',
        collect: 'Collect',
        collectNote: 'Collect',
        evaluate: 'Evaluate',
        evaluateNote: 'Evaluate',
        retrain: 'Retrain',
        retrainNote: 'Retrain',
      },
      threads: {
        title: 'Three-thread async pipeline (10x+ frequency gap)',
        obs: 'Observation 30Hz',
        infer: 'Inference 5–10Hz',
        control: 'Control 267Hz',
        buffer: 'Async buffer / smoothing',
      },
    },
  },
} as const;

export function getUI(_locale: Locale) {
  return ui.en;
}
