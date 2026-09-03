#!/usr/bin/env bash
# Commit all built-site chunks locally, then push with endless-ish retries.
# Idempotent: re-running skips already-committed chunks.
set -u
cd "C:/Users/whatn/Documents/Qoder/2026-08-28/5e48103a" || exit 1

# 1) stop ignoring lessons/
sed -i '/^lessons\/$/d' .gitignore
git add .gitignore
git diff --cached --quiet || git commit -q -m "track built site in repo for VPS pull deployment"

# 2) runtime files (small)
R="lessons/week/courses/speaking-vocab"
git add lessons/week/index.html lessons/week/style.css lessons/week/_worker.js \
  "$R/index.html" "$R/vocab.html" "$R/vocab.js" "$R/adaptive-review.js" \
  "$R/vendor" "$R/_worker.js" "$R/vocabulary-month/index.html" \
  "$R/vocabulary-month/app.js" "$R/vocabulary-month/style.css" "$R/vocabulary-month/month.json" 2>/dev/null
git diff --cached --quiet || git commit -q -m "site: runtime files"

# 3) day pages, slices of 20 days
start=1
while [ "$start" -le 365 ]; do
  end=$((start + 19)); [ "$end" -gt 365 ] && end=365
  d="$start"
  while [ "$d" -le "$end" ]; do
    git add "lessons/week/courses/speaking-vocab/day-$(printf '%03d' "$d")" 2>/dev/null
    d=$((d + 1))
  done
  git diff --cached --quiet || git commit -q -m "site: days $start-$end"
  start=$((start + 20))
done

# 4) vocabulary audio, chunks of 2000 files
find "$R/vocabulary-month/audio" -name '*.mp3' | sort > /tmp/vlist.txt
split -l 2000 /tmp/vlist.txt /tmp/vchunk- 2>/dev/null
for f in /tmp/vchunk-*; do
  [ -f "$f" ] || continue
  xargs -a "$f" -d '\n' git add -- 2>/dev/null
  git diff --cached --quiet || git commit -q -m "site: vocab audio chunk"
  rm -f "$f"
done

echo "COMMIT-PHASE-DONE ahead=$(git rev-list --count origin/main..main 2>/dev/null || echo '?')"

# 5) push everything, oldest first, retrying for up to ~45 min
attempt=1
while [ "$attempt" -le 90 ]; do
  ahead=$(git rev-list --count origin/main..main 2>/dev/null || echo 0)
  if [ "$ahead" -eq 0 ]; then
    echo "ALL-PUSHED attempt $attempt"
    exit 0
  fi
  # push only the oldest unpushed commit so each transfer stays small
  oldest=$(git rev-list --max-parents=0 origin/main..main 2>/dev/null | tail -1)
  [ -z "$oldest" ] && oldest=$(git rev-list origin/main..main | tail -1)
  if git push origin "+$oldest:refs/heads/main" > /tmp/push_out 2>&1; then
    echo "PUSHED $oldest ($ahead remaining)"
    attempt=$((attempt + 1))
    continue
  fi
  echo "push attempt $attempt failed: $(tail -1 /tmp/push_out)"
  sleep 30
  attempt=$((attempt + 1))
done
echo "PUSH-RETRIES-EXHAUSTED ahead=$(git rev-list --count origin/main..main)"
