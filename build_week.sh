#!/usr/bin/env bash
set -e
python3 -m pip install -q -e '.[dev]'
python3 scripts/make_week.py
for day in day-01 day-02 day-03 day-04 day-05 day-06 day-07; do
  python3 src/tts_generate.py "examples/custom/week/$day/segments.json" --out "lessons/week/$day/audio"
  python3 src/build_page.py "examples/custom/week/$day/segments.json" --out "lessons/week/$day"
done
python3 scripts/make_week_index.py
