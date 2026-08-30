#!/usr/bin/env python3
"""Build one course end-to-end: data -> pages -> audio -> indexes.

Usage:
  python scripts/build_course.py --course speaking-vocab [--days 1-30] [--no-audio] [--no-pages]

Conventions per course id (e.g. speaking-vocab):
- examples/courses/<id>/course.json            registry: days, titles, tier bands
- examples/courses/<id>/content/month-*.json   authored content (vocab + story)
- examples/courses/<id>/days/day-NNN/segments.json  generated lesson data
- lessons/week/courses/<id>/                   deployed course (day pages, vocabulary SPA, runtime)
- lessons/week/index.html                      site-wide course catalog (rewritten on each build)

Audio generation is incremental (existing mp3s are skipped), so re-running is cheap.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

RUNTIME_FILES = ["vocab.html", "vocab.js", "adaptive-review.js", "style.css"]


def courses() -> list[dict]:
    out = []
    for path in sorted((ROOT / "examples" / "courses").glob("*/course.json")):
        config = json.loads(path.read_text(encoding="utf-8"))
        config["_dir"] = path.parent.name
        out.append(config)
    return out


def run_python(script: str, *args: str) -> None:
    cmd = [sys.executable, str(ROOT / script), *args]
    print(f"$ {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True, cwd=ROOT)


def built_days(course_id: str) -> list[int]:
    days_dir = ROOT / "examples" / "courses" / course_id / "days"
    if not days_dir.exists():
        return []
    return sorted(int(p.name.split("-")[1]) for p in days_dir.glob("day-*") if (p / "segments.json").exists())


def parse_days(raw: str, allowed: list[int]) -> list[int]:
    if not raw.strip():
        return allowed
    allowed_set = set(allowed)
    picked: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            low, high = part.split("-", 1)
            picked.update(range(int(low), int(high) + 1))
        else:
            picked.add(int(part))
    return sorted(picked & allowed_set)


def ensure_vendor() -> Path | None:
    umd = ROOT / "node_modules" / "ts-fsrs" / "dist" / "index.umd.js"
    if not umd.exists():
        print("ts-fsrs vendor bundle missing; running npm ci ...", flush=True)
        subprocess.run(["npm", "ci", "--silent"], check=True, cwd=ROOT)
    return umd


def copy_runtime(course_id: str) -> None:
    course_out = ROOT / "lessons" / "week" / "courses" / course_id
    course_out.mkdir(parents=True, exist_ok=True)
    for name in RUNTIME_FILES:
        shutil.copy2(ROOT / "src" / "template" / name, course_out / name)
    umd = ensure_vendor()
    if umd:
        vendor = course_out / "vendor"
        vendor.mkdir(exist_ok=True)
        shutil.copy2(umd, vendor / "ts-fsrs.umd.js")
        license_path = umd.parent.parent / "LICENSE"
        if license_path.exists():
            shutil.copy2(license_path, vendor / "ts-fsrs.LICENSE.txt")


def build_pages(course_id: str, config: dict, days: list[int]) -> int:
    from build_page import build_nav, closeout, load_json, render_index, validate_lesson  # noqa: E402

    course_out = ROOT / "lessons" / "week" / "courses" / course_id
    days_src = ROOT / "examples" / "courses" / course_id / "days"
    failures = 0
    for day in days:
        segments_path = days_src / f"day-{day:03d}" / "segments.json"
        if not segments_path.exists():
            continue
        out_dir = course_out / f"day-{day:03d}"
        prev_href = f"../day-{day - 1:03d}/index.html" if day > 1 else ""
        next_href = f"../day-{day + 1:03d}/index.html" if day < config["days"] else ""
        try:
            data = load_json(segments_path)
            validate_lesson(data)
            render_index(data, out_dir, build_nav(prev_href, next_href, "../index.html"),
                         {"id": course_id, "day": day})
            print(f"day {day:03d}: {closeout(data, out_dir).splitlines()[0]}", flush=True)
        except Exception as exc:  # keep building the rest of the course
            failures += 1
            print(f"day {day:03d}: FAILED: {exc}", file=sys.stderr, flush=True)
    return failures


def write_catalog() -> Path:
    entries = []
    for config in courses():
        course_id = config["_dir"]
        days = built_days(course_id)
        if not days:
            continue
        entries.append({
            "id": course_id,
            "title": config["title"],
            "subtitle": config["subtitle"],
            "vocab_title": config["vocab_title"],
            "days": config["days"],
            "built_days": len(days),
            "last_day": days[-1],
            "url": f"courses/{course_id}/",
        })
    payload = json.dumps(entries, ensure_ascii=False)
    html = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>英语学习 · 课程目录</title><style>body{{font-family:-apple-system,sans-serif;max-width:760px;margin:0 auto;padding:36px 20px;line-height:1.6;background:#fafafa;color:#222}}h1{{font-size:28px;margin-bottom:4px}}.sub{{color:#666;margin-bottom:28px}}.course-card{{display:block;margin:18px 0;padding:24px;border-radius:16px;background:#fff;border:1px solid #e3e3e3;text-decoration:none;color:#222}}.course-card:hover{{background:#f0f7ff}}.course-card h2{{margin:0 0 4px;font-size:21px;color:#163e33}}.course-card p{{margin:0 0 10px;color:#666;font-size:14px}}.progress-row{{display:flex;gap:8px;align-items:center;font-size:13px;color:#444}}.bar{{flex:1;height:8px;border-radius:4px;background:#e7ece9;overflow:hidden}}.bar i{{display:block;height:100%;background:linear-gradient(90deg,#2d6b55,#3f9c74)}}.continue{{display:inline-block;margin-top:10px;padding:7px 14px;border-radius:999px;background:#163e33;color:#fff;font-size:13px;text-decoration:none}}.continue:hover{{background:#2d6b55}}.vocab-link{{color:#2d6b55;font-size:13px;text-decoration:none}}</style></head><body><h1>英语学习 · 课程目录</h1><p class="sub">Immersion Reader · 多课程学习门户 · 学习进度保存在本机浏览器</p><div id="catalog"></div><script>window.__COURSES__ = {payload};</script><script>
(function() {{
  var esc = function(t) {{ return String(t || "").replace(/[&<>"]/g, function(c) {{ return {{ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }}[c]; }}); }};
  var el = document.getElementById("catalog");
  el.innerHTML = (window.__COURSES__ || []).map(function(c) {{
    var visited = 0, lastDay = 0;
    try {{
      var p = JSON.parse(localStorage.getItem("ir:" + c.id + ":progress") || "null");
      if (p && p.visited) visited = Object.keys(p.visited).length;
      if (p && p.lastDay) lastDay = p.lastDay;
    }} catch (e) {{}}
    var pct = Math.min(100, Math.round(visited / c.days * 100));
    var continueHref = lastDay ? c.url + "day-" + String(lastDay).padStart(3, "0") + "/index.html" : c.url + "day-001/index.html";
    var continueLabel = visited ? "继续学习 · Day " + lastDay : "从 Day 1 开始";
    return '<a class="course-card" href="' + esc(c.url) + 'index.html">'
      + '<h2>' + esc(c.title) + '</h2>'
      + '<p>' + esc(c.subtitle) + '</p>'
      + '<div class="progress-row"><span>' + visited + ' / ' + c.days + ' 天</span>'
      + '<span class="bar"><i style="width:' + pct + '%"></i></span><span>' + pct + '%</span></div>'
      + '<span class="continue">' + continueLabel + ' →</span>'
      + ' <span class="vocab-link" style="margin-left:10px">' + esc(c.vocab_title) + ' →</span>'
      + '</a>';
  }}).join("") || '<p>还没有已构建的课程。</p>';
}})();
</script></body></html>'''
    out = ROOT / "lessons" / "week" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


def write_redirects(course_id: str, config: dict) -> None:
    """Legacy URLs (pre multi-course layout) redirect into the course directory."""
    week = ROOT / "lessons" / "week"

    def stub(path: Path, href: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            '<!doctype html><meta charset="utf-8">'
            f'<title>已迁移</title><meta http-equiv="refresh" content="0; url={href}">'
            f'<p>页面已迁移，<a href="{href}">点此继续</a>。</p>',
            encoding="utf-8",
        )

    legacy_days = int(config.get("legacy_days", 0))
    for day in range(1, legacy_days + 1):
        stub(week / f"day-{day:02d}" / "index.html", f"../courses/{course_id}/day-{day:03d}/index.html")
    stub(week / "vocab.html", f"courses/{course_id}/vocab.html")
    stub(week / "vocabulary-month" / "index.html", f"../courses/{course_id}/vocabulary-month/index.html")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course", default="speaking-vocab")
    parser.add_argument("--days", default="", help="subset like 1-30 or 1,5,9; default every built day")
    parser.add_argument("--no-audio", action="store_true", help="skip TTS generation")
    parser.add_argument("--no-pages", action="store_true", help="skip static page build")
    parser.add_argument("--skip-generators", action="store_true", help="only rebuild pages/audio from existing data")
    args = parser.parse_args()

    config_path = ROOT / "examples" / "courses" / args.course / "course.json"
    if not config_path.exists():
        print(f"unknown course: {args.course}", file=sys.stderr)
        return 2
    config = json.loads(config_path.read_text(encoding="utf-8"))

    if not args.skip_generators:
        run_python("scripts/make_vocabulary_course.py", "--course", args.course)
        run_python("scripts/make_speaking_course.py", "--course", args.course)

    available = built_days(args.course)
    if not available:
        print("no generated day data found; nothing to build", file=sys.stderr)
        return 2
    days = parse_days(args.days, available)
    print(f"building course {args.course}: days {days[0]}-{days[-1]} ({len(days)} of {len(available)} available)")

    copy_runtime(args.course)
    # the Pages worker (cloud notebook sync) lives at the deployment root
    shutil.copy2(ROOT / "src" / "template" / "_worker.js", ROOT / "lessons" / "week" / "_worker.js")
    if not args.no_audio:
        run_python("scripts/generate_speaking_audio.py", "--course", args.course,
                   "--days", f"{days[0]}-{days[-1]}")
        run_python("scripts/generate_vocabulary_audio.py", "--course", args.course)
    if not args.no_pages:
        failures = build_pages(args.course, config, days)
        write_redirects(args.course, config)
        catalog = write_catalog()
        print(f"course home: lessons/week/courses/{args.course}/index.html")
        print(f"catalog: {catalog.relative_to(ROOT)}")
        if failures:
            print(f"{failures} day page(s) failed; see errors above", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
