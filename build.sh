#!/usr/bin/env bash
set -e
pip install -q -e '.[dev]'
python src/tts_generate.py examples/custom/segments.json --out lessons/custom/audio
python src/build_page.py examples/custom/segments.json --out lessons/custom
