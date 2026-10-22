"""Dataset selection, outcome export and parallel merging for simulation."""

import json
import logging
import os
import shutil
from pathlib import Path

import numpy as np


def _array_stats(values):
    values = np.asarray(values, dtype=np.float64)
    if values.ndim == 1:
        values = values[:, None]
    return {
        "mean": values.mean(axis=0).tolist(),
        "std": values.std(axis=0).tolist(),
        "min": values.min(axis=0).tolist(),
        "max": values.max(axis=0).tolist(),
        "q01": np.quantile(values, 0.01, axis=0).tolist(),
        "q99": np.quantile(values, 0.99, axis=0).tolist(),
    }


def _link_or_copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def _dataset_metadata(source):
    source = Path(source)
    source_meta = source / "meta"
    info = json.loads((source_meta / "info.json").read_text(encoding="utf-8"))
    episodes = {
        row["episode_index"]: row
        for row in (
            json.loads(line)
            for line in (source_meta / "episodes.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }
    tasks = (source_meta / "tasks.jsonl").read_text(encoding="utf-8")
    return info, episodes, tasks


def _task_index_remap(source_tasks, template_tasks, source):
    def parse_tasks(text):
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
        by_index = {int(row["task_index"]): row["task"] for row in rows}
        by_task = {row["task"]: int(row["task_index"]) for row in rows}
        if len(by_index) != len(rows) or len(by_task) != len(rows):
            raise RuntimeError(f"Invalid LeRobot task definitions: {source}")
        return by_index, by_task

    source_by_index, source_by_task = parse_tasks(source_tasks)
    _, template_by_task = parse_tasks(template_tasks)
    if set(source_by_task) != set(template_by_task):
        raise RuntimeError(f"Incompatible LeRobot task definitions: {source}")
    return {source_index: template_by_task[task] for source_index, task in source_by_index.items()}


def _remap_table_task_indices(table, remap, source):
    import pyarrow as pa

    columns = [
        name
        for name in ("task_index", "annotation.human.task_description")
        if name in table.column_names
    ]
    for name in columns:
        try:
            values = [remap[int(value)] for value in table[name].to_pylist()]
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError(f"Unknown LeRobot task index in {source}") from exc
        field_index = table.schema.get_field_index(name)
        table = table.set_column(
            field_index,
            name,
            pa.array(values, type=table.schema.field(field_index).type),
        )
    return table


def _write_dataset_selection(template_source, destination, selections):
    import pyarrow as pa
    import pyarrow.parquet as pq

    template_source = Path(template_source)
    destination = Path(destination)
    template_info, _, template_tasks = _dataset_metadata(template_source)
    compatibility_keys = (
        "codebase_version",
        "robot_type",
        "total_tasks",
        "chunks_size",
        "fps",
        "data_path",
        "video_path",
        "features",
    )
    metadata = {}
    task_remaps = {}
    for source, _ in selections:
        source = Path(source)
        if source not in metadata:
            metadata[source] = _dataset_metadata(source)
            info, _, tasks = metadata[source]
            if any(info.get(key) != template_info.get(key) for key in compatibility_keys):
                raise RuntimeError(f"Incompatible LeRobot recording metadata: {source}")
            task_remaps[source] = _task_index_remap(tasks, template_tasks, source)

    chunk_size = int(template_info["chunks_size"])
    video_keys = [
        key for key, feature in template_info["features"].items() if feature.get("dtype") == "video"
    ]
    all_stats = {"observation.state": [], "action": [], "timestamp": []}
    output_episodes = []
    output_episode_stats = []
    total_frames = 0

    for new_index, (source, source_index) in enumerate(selections):
        source = Path(source)
        info, episode_rows, _ = metadata[source]
        if source_index not in episode_rows:
            raise RuntimeError(f"Missing episode {source_index} metadata in {source}")
        source_chunk = source_index // int(info["chunks_size"])
        target_chunk = new_index // chunk_size
        source_data = source / info["data_path"].format(
            episode_chunk=source_chunk,
            episode_index=source_index,
        )
        if not source_data.is_file():
            raise FileNotFoundError(f"Missing recorded episode: {source_data}")
        table = pq.read_table(source_data)
        table = _remap_table_task_indices(table, task_remaps[source], source)
        frame_count = table.num_rows
        table = table.set_column(
            table.schema.get_field_index("episode_index"),
            "episode_index",
            pa.array([new_index] * frame_count, type=pa.int64()),
        )
        table = table.set_column(
            table.schema.get_field_index("index"),
            "index",
            pa.array(range(total_frames, total_frames + frame_count), type=pa.int64()),
        )
        target_data = destination / template_info["data_path"].format(
            episode_chunk=target_chunk,
            episode_index=new_index,
        )
        target_data.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(table, target_data)

        episode_stats = {}
        for column in all_stats:
            values = np.asarray(table[column].to_pylist(), dtype=np.float64)
            if values.size:
                all_stats[column].append(values)
                episode_stats[column] = _array_stats(values)
        output_episode_stats.append(
            {
                "episode_index": new_index,
                "stats": episode_stats,
            }
        )
        output_episodes.append(
            {
                **episode_rows[source_index],
                "episode_index": new_index,
                "length": frame_count,
            }
        )

        for video_key in video_keys:
            source_video = source / info["video_path"].format(
                episode_chunk=source_chunk,
                video_key=video_key,
                episode_index=source_index,
            )
            target_video = destination / template_info["video_path"].format(
                episode_chunk=target_chunk,
                video_key=video_key,
                episode_index=new_index,
            )
            if not source_video.is_file():
                raise FileNotFoundError(f"Missing recorded video: {source_video}")
            _link_or_copy(source_video, target_video)
        total_frames += frame_count

    destination_meta = destination / "meta"
    destination_meta.mkdir(parents=True, exist_ok=True)
    info = dict(template_info)
    info.update(
        {
            "total_episodes": len(selections),
            "total_frames": total_frames,
            "total_videos": len(selections) * len(video_keys),
            "total_chunks": (len(selections) + chunk_size - 1) // chunk_size,
            "splits": {"train": f"0:{len(selections)}"},
        }
    )
    (destination_meta / "info.json").write_text(
        json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    for filename, rows in (
        ("episodes.jsonl", output_episodes),
        ("episodes_stats.jsonl", output_episode_stats),
    ):
        (destination_meta / filename).write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )
    (destination_meta / "tasks.jsonl").write_text(template_tasks, encoding="utf-8")
    stats = {
        column: _array_stats(np.concatenate(chunks, axis=0))
        for column, chunks in all_stats.items()
        if chunks
    }
    (destination_meta / "stats.json").write_text(
        json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _write_dataset_partition(source, destination, source_indices):
    selections = [(Path(source), source_index) for source_index in source_indices]
    _write_dataset_selection(source, destination, selections)


def _recording_result_pairs(source, episodes):
    episode_rows = [
        json.loads(line)
        for line in (source / "meta/episodes.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if all("recording_episode_index" in result for result in episodes):
        return [
            (int(result["recording_episode_index"]), evaluation_index)
            for evaluation_index, result in enumerate(episodes)
        ]
    if len(episode_rows) == len(episodes):
        return [
            (int(row["episode_index"]), evaluation_index)
            for evaluation_index, row in enumerate(episode_rows)
        ]
    raise RuntimeError(
        "Cannot recover recording/result mapping: "
        f"{len(episode_rows)} episode rows, {len(episodes)} evaluation results"
    )


def _resolve_recording_results(source, episodes):
    pairs = _recording_result_pairs(source, episodes)
    resolved = {}
    dropped = []
    for source_index, evaluation_index in pairs:
        if source_index in resolved:
            dropped.append(resolved[source_index])
        resolved[source_index] = {
            "evaluation_episode": evaluation_index,
            "success": bool(episodes[evaluation_index]["success"]),
        }
    available = {
        int(path.stem.rsplit("_", 1)[-1]) for path in (source / "data").rglob("episode_*.parquet")
    }
    if set(resolved) != available:
        raise RuntimeError(
            "Cannot partition recording: resolved episode indices do not match files; "
            f"mapping={sorted(resolved)}, files={sorted(available)}"
        )
    return resolved, dropped


def _partition_recording_by_success(recording_path, episodes):
    source = Path(recording_path)
    resolved, dropped = _resolve_recording_results(source, episodes)
    partitions = {
        outcome: [
            source_index
            for source_index, result in sorted(
                resolved.items(), key=lambda item: item[1]["evaluation_episode"]
            )
            if result["success"] is success
        ]
        for outcome, success in (("success", True), ("failure", False))
    }
    temporary_paths = {name: source / f".{name}.tmp" for name in partitions}
    final_paths = {name: source / name for name in partitions}
    if any(path.exists() for path in (*temporary_paths.values(), *final_paths.values())):
        raise FileExistsError(f"Recording partitions already exist under {source}")
    try:
        for name, indices in partitions.items():
            _write_dataset_partition(source, temporary_paths[name], indices)
        for name in partitions:
            temporary_paths[name].rename(final_paths[name])
    except Exception:
        for path in (*temporary_paths.values(), *final_paths.values()):
            if path.exists():
                shutil.rmtree(path)
        raise

    for directory in ("data", "videos", "meta"):
        path = source / directory
        if path.exists():
            shutil.rmtree(path)
    report = {
        "evaluation_episodes": len(episodes),
        "exported_episodes": len(resolved),
        "success_episodes": len(partitions["success"]),
        "failure_episodes": len(partitions["failure"]),
        "dropped_overwritten_evaluation_episodes": [item["evaluation_episode"] for item in dropped],
    }
    (source / "partition_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    if dropped:
        logging.warning(
            "Exported %d/%d recorded episodes; overwritten evaluation episodes: %s",
            len(resolved),
            len(episodes),
            report["dropped_overwritten_evaluation_episodes"],
        )
    return {name: str(path) for name, path in final_paths.items()}


def _merge_parallel_recordings(results):
    ordered_results = sorted(results, key=lambda stats: stats["worker_index"])
    first = ordered_results[0]
    first_source = Path(first["lerobot_dataset_path"])
    marker = f"_env{first['worker_index']:02d}_"
    prefix, separator, suffix = first_source.name.rpartition(marker)
    if not separator:
        raise RuntimeError(f"Unexpected parallel recording path: {first_source}")
    destination = first_source.parent / f"{prefix}_{suffix}"
    final_paths = {outcome: destination / outcome for outcome in ("success", "failure")}
    if all((path / "meta/info.json").is_file() for path in final_paths.values()):
        return {outcome: str(path) for outcome, path in final_paths.items()}

    selections = []
    result_pairs = []
    sources = []
    for stats in ordered_results:
        source = Path(stats["lerobot_dataset_path"])
        sources.append(source)
        pairs = _recording_result_pairs(source, stats["episodes"])
        resolved, _ = _resolve_recording_results(source, stats["episodes"])
        for source_index, resolved_result in resolved.items():
            evaluation_index = resolved_result["evaluation_episode"]
            global_episode = int(stats["episodes"][evaluation_index]["episode"])
            selections.append((global_episode, source, source_index))
        for source_index, evaluation_index in pairs:
            global_episode = int(stats["episodes"][evaluation_index]["episode"])
            result_pairs.append((global_episode, source, source_index))

    selections.sort(key=lambda item: item[0])
    selected_sources = [(source, source_index) for _, source, source_index in selections]
    source_to_merged = {
        (source, source_index): merged_index
        for merged_index, (_, source, source_index) in enumerate(selections)
    }
    combined_episodes = {
        int(episode["episode"]): dict(episode)
        for stats in ordered_results
        for episode in stats["episodes"]
    }
    for global_episode, source, source_index in result_pairs:
        combined_episodes[global_episode]["recording_episode_index"] = source_to_merged[
            (source, source_index)
        ]
    ordered_episodes = [combined_episodes[index] for index in sorted(combined_episodes)]

    temporary = destination.parent / f".{destination.name}.tmp"
    if temporary.exists():
        shutil.rmtree(temporary)
    if not destination.exists():
        try:
            _write_dataset_selection(first_source, temporary, selected_sources)
            temporary.rename(destination)
        except Exception:
            if temporary.exists():
                shutil.rmtree(temporary)
            raise
    elif not (destination / "meta/info.json").is_file():
        raise FileExistsError(f"Incomplete merged recording exists: {destination}")

    paths = _partition_recording_by_success(destination, ordered_episodes)
    for source in sources:
        if source.exists():
            shutil.rmtree(source)
    return paths
