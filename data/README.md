```
# Data storage directory

This directory is the default local storage root for development-time data collection and evaluation artifacts.

By default, the project writes recorded datasets under:

- `data/recording/<task>_<date>/`

## Typical layout

```text
data/
├─ media/                     # static media/resources used by demos or docs
├─ recording/                 # default root for recorded robot data
│  └─ <task>_<date>/
│     ├─ data/                # LeRobot-style episode data
│     │  ├─ chunk-000/
│     │  │  ├─ episode_000000.parquet
│     │  │  └─ videos/
│     │  │     ├─ cam.head/
│     │  │     │  └─ episode_000000.mp4
│     │  │     ├─ cam.hand_left/
│     │  │     └─ cam.hand_right/
│     │  └─ ...
│     ├─ meta/                # dataset metadata, info.json, episodes.jsonl, etc.
│     └─ eval/                # evaluation logs, e.g. eval_log.json / eval_log.csv
│        ├─ eval_log.json
│        └─ eval_log.csv
└─ output/                    # legacy/manual output examples, optional and not required by the recorder
```

## Meaning of the main folders

- `data/recording/.../data`: raw episode data saved during robot recording, usually in Parquet format plus camera videos.
- `data/recording/.../meta`: metadata used to describe the dataset and episode structure.
- `data/recording/.../eval`: evaluation results recorded during offline or online model assessment.
- `data/media`: auxiliary media assets used by the project, not the main data output.

## Notes

- The actual save path is configured in `conf/save_conf.py` and defaults to `data/recording`.
- The recorder creates task/date-named subfolders automatically when a new recording session starts.
- This directory is mainly for runtime-generated artifacts, so it may be created and populated during development, data collection, or evaluation.
```