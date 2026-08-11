#!/usr/bin/env bash
set -e
python3 -m pip install -q -e '.[dev]'
python3 scripts/make_week.py

build_day() {
  local day=$1 prev=$2 next=$3
  python3 src/tts_generate.py "examples/custom/week/$day/segments.json" --out "lessons/week/$day/audio"
  python3 src/build_page.py "examples/custom/week/$day/segments.json" --out "lessons/week/$day" --prev "$prev" --next "$next" --home "index.html"
}

build_day day-01 "" "day-02/index.html"
build_day day-02 "day-01/index.html" "day-03/index.html"
build_day day-03 "day-02/index.html" "day-04/index.html"
build_day day-04 "day-03/index.html" "day-05/index.html"
build_day day-05 "day-04/index.html" "day-06/index.html"
build_day day-06 "day-05/index.html" "day-07/index.html"
build_day day-07 "day-06/index.html" ""

python3 scripts/make_week_index.py
