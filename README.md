# Immersion Reader

Turn a long-form English article or transcript into a local static deep-reading page.

[English](README.md) | [简体中文](README.zh.md)

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Demo: GitHub Pages ready](https://img.shields.io/badge/demo-GitHub%20Pages%20ready-3b5bdb.svg)](docs/demo/index.html)

![Immersion Reader demo](docs/assets/demo.gif)

## What this is

- A static lesson package compiler.
- Built for English learners who already live in a local coding agent (Claude Code, Codex, or OpenCode): your agent compiles the lesson, you study it.
- Output opens as local HTML.
- Edge TTS is the default audio path.
- Karaoke-style word highlight follows the audio; click any word to play from it.

## What this is not

- No account.
- No backend.
- No database.
- No cloud sync.
- No public local-agent CLI bridge.
- No in-page agent server.

Use the page's copy prompts with your local agent when you need help with a word, segment, summary, or transfer task.

## Selection Card Policy

- Single-word selections can show an offline dictionary card.
- 2-5 word phrases stay agent cards by default; the whole phrase meaning is often not the sum of word definitions.
- Longer passage selections copy a deep-reading prompt for your local agent.
- Clicking prepared chunks is different: authored chunks can still show their Chinese meaning and example sentence.

## Try it first

A compiled demo lesson lives at [`docs/demo/index.html`](docs/demo/index.html) — clone, then open it directly in a browser. No install needed.

The same page is served via GitHub Pages: <https://rayw-lab.github.io/english-immersion-reader/demo/>.

## Quickstart

```bash
python3.13 -m venv .venv  # or any Python >= 3.10
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python src/build_page.py examples/demo/segments.json --out lessons/demo
python src/tts_generate.py examples/demo/segments.json --out lessons/demo/audio --dry-run
python3 -m http.server 8770 --directory lessons/demo
```

Then open `http://localhost:8770/index.html`.

Generated lessons belong in `lessons/`, which is ignored by git. Do not commit user-captured transcripts, private articles, or generated lesson audio unless you own the rights.

## 365-day vocabulary & speaking course

A full year of lessons: every day introduces 18 hand-authored vocabulary items (computer, daily conversation, GitHub) and weaves all of them into one continuous story about Alex — a developer who joins a team on day 1 and grows into a tech lead by day 365. Sentence length and speech rate climb through 8 difficulty tiers; every English segment ships with an exact Chinese translation, per-segment Edge TTS audio, karaoke word timings, and per-term audio.

Build everything (data, pages, audio — audio is incremental, so re-runs are cheap):

```bash
python3 scripts/build_course.py --course speaking-vocab            # full build
python3 scripts/build_course.py --course speaking-vocab --days 1-30  # a range only
python3 scripts/build_course.py --course speaking-vocab --skip-generators --no-audio  # pages only
```

### Multi-course layout

- `examples/courses/<id>/course.json` — course registry (days, titles, tier bands)
- `examples/courses/<id>/content/month-NN.vocab.json` + `month-NN.story.json` — hand-authored content, 30 days per file
- `examples/courses/<id>/days/day-NNN/segments.json` — generated lesson data
- `lessons/week/index.html` — course catalog (lists every course under `examples/courses/`)
- `lessons/week/courses/<id>/` — the deployed course: day pages, interactive vocabulary site, runtime
- Legacy URLs (`/day-01/`, `/vocabulary-month/`) redirect into the main course

Learning state is namespaced per course (`ir:<course>:...`) with per-day practice keys; the vocabulary notebook (`ir_vocab_v1`) stays shared across courses and stamps each entry with an explicit `course` id. Adding a new course later (e.g. CET-4/6) only needs a new `examples/courses/<id>/` directory — the catalog picks it up automatically.

### Deploying

The built `lessons/week/` folder is fully static — any static file server works (nginx, Caddy, `python3 -m http.server`). The bundled `_worker.js` adds optional cloud sync of the vocabulary notebook on Cloudflare Pages; without it the site silently runs in local-only mode.

The vocabulary notebook uses the official `ts-fsrs` scheduler with 90% target retention, four review ratings, short-term relearning steps, and per-card difficulty/stability state. `npm ci` installs the pinned browser scheduler before the static build copies its UMD bundle into `lessons/week/vendor/`.

## Skill Install

Copy `skills/immersion-reader/` into `~/.claude/skills/` or your project `.claude/skills/` directory. OpenCode and Codex users should keep this repository's `AGENTS.md` with the lesson project so the agent follows the data contract.

## Verification

```bash
python -m pytest -q
python -m playwright install chromium
python -m pytest tests/verify_browser.py tests/verify_ui_controls.py -q
```

## Recording Privacy

The shadowing recorder is session-only. Your voice never leaves memory. Close the tab and the recording is gone.

## License

MIT. See [`LICENSE`](LICENSE).
