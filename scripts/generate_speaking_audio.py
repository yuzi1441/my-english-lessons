#!/usr/bin/env python3
"""Generate local high-quality AAC/M4A narration for speaking lessons.

macOS's built-in Eddy en-US voice is used here because it is consistent and
does not fall back to a low-quality browser voice. Chrome and Safari both play
the resulting M4A files directly.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "examples" / "custom" / "week"
OUT = ROOT / "lessons" / "week"
VOICE = "Eddy"
RATE = "165"


def jobs() -> list[tuple[str, Path]]:
    result = []
    for day in range(1, 31):
        source = DATA / f"day-{day:02d}" / "segments.json"
        data = json.loads(source.read_text(encoding="utf-8"))
        for segment in data["segments"]:
            result.append((segment["tts"], OUT / f"day-{day:02d}" / "audio" / f"{segment['id']}.m4a"))
    return result


def generate(job: tuple[str, Path]) -> tuple[bool, str]:
    text, output = job
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="speaking-tts-") as tmp:
        aiff = Path(tmp) / "speech.aiff"
        try:
            subprocess.run(["say", "-v", VOICE, "-r", RATE, "-o", str(aiff), text], check=True, timeout=45)
            subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", "-o", str(output), str(aiff)], check=True, timeout=45)
            if output.stat().st_size < 500:
                raise RuntimeError("audio file is empty")
            return True, str(output)
        except Exception as exc:
            return False, f"{output}: {exc}"


def main() -> int:
    all_jobs = jobs()
    failures = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(generate, job) for job in all_jobs]
        for future in as_completed(futures):
            ok, detail = future.result()
            if not ok:
                failures.append(detail)
    print(f"speaking audio generated={len(all_jobs) - len(failures)} failed={len(failures)} total={len(all_jobs)}")
    for failure in failures:
        print(f"failed {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
