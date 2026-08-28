#!/usr/bin/env python3
"""Generate stable, clear narration audio for every speaking-lesson segment.

Cross-platform Edge TTS pipeline (works on macOS, Linux, and Windows):
- one mp3 per segment, named audio/seg-NN.mp3 next to each lesson page
- one WordBoundary sidecar (seg-NN.words.json) per segment for karaoke sync
- one mp3 per hard term / chunk under audio/w/ so card playback never
  falls back to a browser voice

Audio is regenerated only when missing; pass --force to rebuild everything.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from lesson_quality import required_word_audio_terms, word_audio_slug  # noqa: E402

DATA = ROOT / "examples" / "custom" / "week"
OUT = ROOT / "lessons" / "week"
PROXY_KEYS = ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy")
MIN_AUDIO_BYTES = 500


@dataclass(frozen=True)
class AudioJob:
    job_id: str
    text: str
    output: Path
    words_output: Path | None
    voice: str
    rate: str


def valid_audio(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > MIN_AUDIO_BYTES


def collect_jobs(days: list[int], force: bool) -> list[AudioJob]:
    jobs: list[AudioJob] = []
    for day in days:
        source = DATA / f"day-{day:02d}" / "segments.json"
        data = json.loads(source.read_text(encoding="utf-8"))
        voice_cfg = data.get("voice", {})
        voice = str(voice_cfg.get("voice", "en-US-AndrewNeural"))
        rate = str(voice_cfg.get("rate", "-8%"))
        audio_dir = OUT / f"day-{day:02d}" / "audio"
        for segment in data["segments"]:
            output = audio_dir / f"{segment['id']}.mp3"
            words = audio_dir / f"{segment['id']}.words.json"
            if not force and valid_audio(output):
                continue
            jobs.append(AudioJob(segment["id"], str(segment.get("tts") or segment["en"]).strip(),
                                 output, words, voice, rate))
        for term in required_word_audio_terms(data):
            output = audio_dir / "w" / f"{word_audio_slug(term)}.mp3"
            if not force and valid_audio(output):
                continue
            jobs.append(AudioJob(f"w/{word_audio_slug(term)}", term, output, None, voice, rate))
    return jobs


async def synthesize(job: AudioJob, semaphore: asyncio.Semaphore) -> tuple[bool, str]:
    import edge_tts

    async with semaphore:
        last_error: Exception | None = None
        job.output.parent.mkdir(parents=True, exist_ok=True)
        partial = job.output.with_suffix(job.output.suffix + ".part")
        for attempt in range(1, 4):
            try:
                if job.words_output is None:
                    communicate = edge_tts.Communicate(job.text, job.voice, rate=job.rate)
                    await communicate.save(str(partial))
                else:
                    try:
                        communicate = edge_tts.Communicate(job.text, job.voice, rate=job.rate, boundary="WordBoundary")
                    except TypeError:
                        communicate = edge_tts.Communicate(job.text, job.voice, rate=job.rate)
                    await stream_with_word_boundaries(communicate, partial, job.words_output)
                if not valid_audio(partial):
                    raise RuntimeError("generated audio is empty")
                partial.replace(job.output)
                return True, job.job_id
            except Exception as exc:
                last_error = exc
                if partial.exists():
                    partial.unlink(missing_ok=True)
                await asyncio.sleep(attempt * 0.8)
        return False, f"{job.output}: {last_error}"


async def stream_with_word_boundaries(communicate, partial: Path, words_output: Path) -> None:
    words: list[dict] = []
    with partial.open("wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 10_000_000
                words.append({
                    "text": str(chunk.get("text", "")),
                    "t0": round(start, 3),
                    "t1": round(start + chunk["duration"] / 10_000_000, 3),
                })
    # fingerprint binds the sidecar to this exact mp3 (build_page drops stale pairs)
    payload = {"mp3_bytes": partial.stat().st_size, "words": words}
    words_output.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def parse_days(raw: str) -> list[int]:
    days: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            low, high = part.split("-", 1)
            days.extend(range(int(low), int(high) + 1))
        else:
            days.append(int(part))
    return sorted({day for day in days if 1 <= day <= 30}) or list(range(1, 31))


async def run(days: list[int], concurrency: int, force: bool) -> int:
    for key in PROXY_KEYS:
        os.environ.pop(key, None)
    jobs = collect_jobs(days, force)
    if not jobs:
        print("speaking audio already complete; nothing to do")
        return 0
    semaphore = asyncio.Semaphore(concurrency)
    tasks = [asyncio.create_task(synthesize(job, semaphore)) for job in jobs]
    failed: list[str] = []
    done = 0
    for task in asyncio.as_completed(tasks):
        ok, detail = await task
        done += 1
        if not ok:
            failed.append(detail)
        if done % 25 == 0 or done == len(tasks):
            print(f"speaking audio {done}/{len(tasks)} failed={len(failed)}", flush=True)
    for detail in failed:
        print(f"failed {detail}")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", default="1-30", help="Day selection, e.g. 1-30 or 1,5,9")
    parser.add_argument("--concurrency", type=int, default=6)
    parser.add_argument("--force", action="store_true", help="Regenerate even when audio exists")
    args = parser.parse_args()
    days = parse_days(args.days)
    return asyncio.run(run(days, max(1, min(args.concurrency, 10)), args.force))


if __name__ == "__main__":
    raise SystemExit(main())
