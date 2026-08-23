#!/usr/bin/env python3
"""Generate consistent Edge TTS audio for all vocabulary terms and examples."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / "examples" / "vocabulary-month" / "month.json"
DEFAULT_OUT = ROOT / "lessons" / "week" / "vocabulary-month"
VOICE = "en-US-AndrewNeural"
RATE = "-8%"
PROXY_KEYS = ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy")


@dataclass(frozen=True)
class AudioJob:
    job_id: str
    text: str
    output: Path


def load_jobs(data_path: Path, output_root: Path) -> list[AudioJob]:
    data = json.loads(data_path.read_text(encoding="utf-8"))
    jobs = []
    for day in data["days"]:
        for group in day["groups"]:
            for item in group["items"]:
                jobs.append(AudioJob(f"{item['id']}:term", item["speech"], output_root / item["audio_term"]))
                jobs.append(AudioJob(f"{item['id']}:example", item["example_speech"], output_root / item["audio_example"]))
    return jobs


def valid_audio(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 500


async def synthesize_job(job: AudioJob, semaphore: asyncio.Semaphore, force: bool) -> tuple[str, str]:
    if not force and valid_audio(job.output):
        return "skipped", job.job_id
    import edge_tts

    job.output.parent.mkdir(parents=True, exist_ok=True)
    partial = job.output.with_suffix(".mp3.part")
    async with semaphore:
        last_error = None
        for attempt in range(1, 4):
            try:
                communicate = edge_tts.Communicate(job.text, VOICE, rate=RATE)
                await communicate.save(str(partial))
                if not valid_audio(partial):
                    raise RuntimeError("generated audio is empty")
                partial.replace(job.output)
                return "written", job.job_id
            except Exception as exc:
                last_error = exc
                if partial.exists():
                    partial.unlink()
                await asyncio.sleep(attempt * 0.8)
        return "failed", f"{job.job_id}: {last_error}"


async def generate(jobs: list[AudioJob], concurrency: int, force: bool) -> int:
    for key in PROXY_KEYS:
        os.environ.pop(key, None)
    semaphore = asyncio.Semaphore(concurrency)
    tasks = [asyncio.create_task(synthesize_job(job, semaphore, force)) for job in jobs]
    counts = {"written": 0, "skipped": 0, "failed": 0}
    failures = []
    completed = 0
    for task in asyncio.as_completed(tasks):
        status, detail = await task
        counts[status] += 1
        completed += 1
        if status == "failed":
            failures.append(detail)
        if completed % 25 == 0 or completed == len(tasks):
            print(f"audio {completed}/{len(tasks)} written={counts['written']} skipped={counts['skipped']} failed={counts['failed']}", flush=True)
    for failure in failures:
        print(f"failed {failure}")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--concurrency", type=int, default=6)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    jobs = load_jobs(args.data, args.out)
    if len(jobs) != 1080:
        raise SystemExit(f"expected 1080 audio jobs, got {len(jobs)}")
    return asyncio.run(generate(jobs, max(1, min(args.concurrency, 10)), args.force))


if __name__ == "__main__":
    raise SystemExit(main())
