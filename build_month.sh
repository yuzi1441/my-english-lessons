#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install -q -e '.[dev]'
npm ci --silent
python3 scripts/make_week.py
python3 scripts/make_month.py
python3 scripts/make_vocabulary_month.py
python3 scripts/generate_vocabulary_audio.py
cp src/template/vocab.html lessons/week/vocab.html
cp src/template/vocab.js lessons/week/vocab.js
cp src/template/adaptive-review.js lessons/week/adaptive-review.js
cp src/template/style.css lessons/week/style.css
cp src/template/_worker.js lessons/week/_worker.js
mkdir -p lessons/week/vendor
cp node_modules/ts-fsrs/dist/index.umd.js lessons/week/vendor/ts-fsrs.umd.js
cp node_modules/ts-fsrs/LICENSE lessons/week/vendor/ts-fsrs.LICENSE.txt

for day_num in $(seq -w 1 28); do
  day="day-${day_num}"
  prev_num=$((10#$day_num - 1))
  next_num=$((10#$day_num + 1))
  prev=""
  next=""
  if [ "$prev_num" -ge 1 ]; then
    prev="../day-$(printf '%02d' "$prev_num")/index.html"
  fi
  if [ "$next_num" -le 28 ]; then
    next="../day-$(printf '%02d' "$next_num")/index.html"
  fi

  python3 src/tts_generate.py "examples/custom/week/$day/segments.json" \
    --out "lessons/week/$day/audio" --word-audio full
  python3 src/build_page.py "examples/custom/week/$day/segments.json" \
    --out "lessons/week/$day" --prev "$prev" --next "$next" --home "../index.html"
done

echo "Month 1 built: lessons/week/index.html"
echo "Vocabulary month built: lessons/week/vocabulary-month/index.html"
