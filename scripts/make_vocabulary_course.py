#!/usr/bin/env python3
"""Build the vocabulary course data (month.json) from per-month content files.

Course layout (per course id, e.g. speaking-vocab):
- examples/courses/<id>/course.json                     course registry (days, titles, tiers)
- examples/courses/<id>/content/month-NN.vocab.json     authored vocabulary, 30 days per file
- examples/courses/<id>/vocabulary-month/month.json     built course data (validated)
- lessons/week/courses/<id>/vocabulary-month/           deployed interactive vocabulary site

Each authored day carries three domain groups; terms are "term|中文释义" lines.
The generator derives ids, part-of-speech, TTS speech text, audio paths,
collocations, examples and two exercises per group — exactly as the original
30-day course did — so content files stay small and reviewable.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_VOCAB_APP = ROOT / "src" / "vocabulary_month"

DOMAIN_ORDER = ("computer", "daily", "github")

DOMAIN_META = {
    "computer": {"title": "计算机英语", "icon": "⌘", "kind": "技术术语"},
    "daily": {"title": "日常交流英语", "icon": "◎", "kind": "实用表达"},
    "github": {"title": "GitHub 项目英语", "icon": "⑂", "kind": "协作术语"},
}

SPEECH_REPLACEMENTS = (
    ("CODEOWNERS", "code owners"),
    ("CONTRIBUTING", "contributing"),
    ("Dependabot", "depend a bot"),
    ("GitHub", "Git Hub"),
    ("README", "read me"),
    ("localhost", "local host"),
    ("HTTP", "H T T P"),
    ("JSON", "J son"),
    ("CSV", "C S V"),
    ("DNS", "D N S"),
    ("CPU", "C P U"),
    ("RAM", "ram"),
    ("URL", "U R L"),
    ("API", "A P I"),
    ("IP", "I P"),
    ("PR", "P R"),
    ("CI", "C I"),
    ("AI", "A I"),
    ("RFC", "R F C"),
    ("SPA", "S P A"),
    ("SDK", "S D K"),
    ("CLI", "C L I"),
    ("SQL", "S Q L"),
    ("YAML", "ya mel"),
    ("UI", "U I"),
    ("UX", "U X"),
    ("QA", "Q A"),
    ("SLA", "S L A"),
    ("NLP", "N L P"),
    ("LLM", "L L M"),
    ("GPT", "G P T"),
    ("GPU", "G P U"),
    ("SSD", "S S D"),
    ("VPN", "V P N"),
    ("DNS", "D N S"),
    ("SSH", "S S H"),
    ("TCP", "T C P"),
    ("CDN", "C D N"),
    ("JWT", "J W T"),
    ("CSS", "C S S"),
    ("HTML", "H T M L"),
)


def normalize_key(term: str) -> str:
    return re.sub(r"\s+", " ", term.strip().lower().rstrip(".!?"))


def speech_text(text: str) -> str:
    """Expand technical abbreviations so neural TTS reads them predictably."""
    spoken = text
    for written, replacement in SPEECH_REPLACEMENTS:
        spoken = re.sub(rf"\b{re.escape(written)}\b", replacement, spoken)
    return spoken.replace("...", "").strip()


def parse_terms(raw: list[str]) -> list[tuple[str, str]]:
    result = []
    for line in raw:
        term, meaning = line.split("|", 1)
        result.append((term.strip(), meaning.strip()))
    return result


def load_course_config(course_id: str) -> dict:
    path = ROOT / "examples" / "courses" / course_id / "course.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_content_month_files(course_id: str, kind: str) -> list[dict]:
    """Load content/month-NN.<kind>.json sorted by month number."""
    content_dir = ROOT / "examples" / "courses" / course_id / "content"
    docs = []
    for path in sorted(content_dir.glob(f"month-*.{kind}.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        doc["_file"] = path.name
        docs.append(doc)
    return docs


def load_vocab_days(course_id: str) -> list[dict]:
    """Concatenate authored days across months, verifying 30-day month blocks."""
    per_day = 30
    days: list[dict] = []
    for doc in load_content_month_files(course_id, "vocab"):
        month = doc["month"]
        month_days = doc["days"]
        if len(month_days) > per_day + 5:
            raise SystemExit(
                f"{doc['_file']}: at most {per_day + 5} days per month file, found {len(month_days)}"
            )
        expected_start = (month - 1) * per_day + 1
        for offset, raw_day in enumerate(month_days):
            missing = [dom for dom in DOMAIN_ORDER if dom not in raw_day]
            if missing:
                raise SystemExit(f"{doc['_file']} day {expected_start + offset}: missing domains {missing}")
            for dom in DOMAIN_ORDER:
                terms = raw_day[dom].get("terms", [])
                if len(terms) != 6:
                    raise SystemExit(
                        f"{doc['_file']} day {expected_start + offset}/{dom}: expected 6 terms, found {len(terms)}"
                    )
            days.append(raw_day)
    return days


VERB_STARTS = {
    "accept", "add", "amend", "approve", "assign", "cancel", "catch", "check", "cite", "clean",
    "clone", "close", "complete", "confirm", "convert", "create", "debug", "discard", "download",
    "execute", "fetch", "finish", "fix", "fork", "free", "go", "handle", "install", "leave", "link",
    "make", "mark", "merge", "mention", "open", "parse", "pick", "process", "publish", "pull", "push",
    "rebase", "receive", "remove", "request", "reset", "resolve", "restore", "restrict", "retry", "revert",
    "revoke", "run", "save", "send", "sign", "squash", "start", "stop", "subscribe", "switch", "sync",
    "take", "turn", "uninstall", "unsubscribe", "update", "verify", "wash", "watch",
    "answer", "apply", "back", "block", "branch", "break", "build", "bundle", "cache", "call",
    "carry", "collect", "come", "configure", "connect", "cut", "deal", "deploy", "design", "dig",
    "double", "draw", "drop", "ease", "end", "escort", "evaluate", "extend", "fall", "feel",
    "fill", "follow", "gather", "get", "give", "grow", "hang", "hold", "hop", "hunt", "iron",
    "join", "jump", "keep", "kick", "land", "launch", "lay", "lean", "log", "look", "loosen",
    "measure", "monitor", "move", "note", "own", "pair", "park", "pass", "patch", "pay", "pick",
    "plan", "play", "point", "post", "practice", "profile", "queue", "rank", "reach", "read",
    "record", "rehearse", "release", "roll", "scale", "schedule", "scope", "screen", "set",
    "settle", "ship", "shut", "sit", "sketch", "sleep", "sort", "speak", "spell", "split",
    "stand", "stay", "step", "stick", "stretch", "study", "sum", "tag", "team", "test",
    "think", "throw", "time", "tone", "touch", "trace", "track", "train", "tune", "type",
    "walk", "warm", "weigh", "wire", "wrap", "write",
}


def item_for(day: int, domain: str, topic_title: str, index: int, term: str, meaning: str) -> dict:
    meta = DOMAIN_META[domain]
    first_word = re.sub(r"[^a-z]", "", term.lower().split()[0]) if term.split() else ""
    if domain == "daily":
        pos = "完整句型" if term.endswith((".", "?", "!")) else "固定表达"
    elif first_word in VERB_STARTS:
        pos = "动词短语"
    elif term.isupper() or term in {"GitHub Actions", "GitHub Discussion"}:
        pos = "名词（缩写或专名）"
    elif " " in term:
        pos = "名词短语"
    elif term in {"branch", "commit", "fork", "issue", "label", "query", "release", "retry", "rollback"}:
        pos = "名词，也可作动词"
    else:
        pos = "名词"
    if domain == "daily":
        example = f'在这个场景中，可以直接说：“{term}”'
        english_example = term if term.endswith((".", "?", "!")) else f"{term}."
        collocation = term
        note = f"这是“{topic_title}”场景中的高频表达。先听发音，再整句记忆，不要逐字硬译。"
        part = "日常表达"
    elif domain == "github":
        example = f'团队在“{topic_title}”流程中会使用 {term}。'
        english_example = f'Our team uses "{term}" to keep the project clear.'
        collocation = term if " " in term else f"use {term} in a project"
        note = f"这是 GitHub 的{meta['kind']}。记住它在“{topic_title}”中的具体作用。"
        part = "GitHub 术语" if " " not in term else "GitHub 词块"
    else:
        example = f'处理“{topic_title}”时会遇到 {term}。'
        english_example = f'I learned how to use "{term}" in a computer task.'
        collocation = term if " " in term else f"work with {term}"
        note = f"这是“{topic_title}”中的基础概念。把英文、中文含义和实际场景一起记。"
        part = "技术术语" if " " not in term else "技术词块"
    return {
        "id": f"d{day:02d}-{domain}-{index:02d}",
        "term": term,
        "key": normalize_key(term),
        "meaning": meaning,
        "part": part,
        "pos": pos,
        "speech": speech_text(term),
        "example_speech": speech_text(english_example),
        "audio_term": f"audio/d{day:02d}-{domain}-{index:02d}-term.mp3",
        "audio_example": f"audio/d{day:02d}-{domain}-{index:02d}-example.mp3",
        "collocation": collocation,
        "example": english_example,
        "explanation": example,
        "note": note,
    }


def build_course(course_id: str) -> dict:
    config = load_course_config(course_id)
    groups_per_day = config["groups"]
    terms_per_group = config["terms_per_group"]
    raw_days = load_vocab_days(course_id)
    if not raw_days:
        raise SystemExit(f"no content month files found for course {course_id}")

    days = []
    for day_number, raw_day in enumerate(raw_days, 1):
        groups = []
        for domain in groups_per_day:
            topic_title, terms = raw_day[domain]["topic"], parse_terms(raw_day[domain]["terms"])
            items = [item_for(day_number, domain, topic_title, idx, term, meaning)
                     for idx, (term, meaning) in enumerate(terms, 1)]
            quiz_choices = [item["meaning"] for item in items[:3]]
            groups.append({
                "domain": domain,
                **DOMAIN_META[domain],
                "topic": topic_title,
                "intro": f"今天只围绕“{topic_title}”学习 {terms_per_group} 个高频词或表达。先猜，再揭晓，最后用一次。",
                "items": items,
                "exercises": [
                    {
                        "type": "choice",
                        "question": f'“{items[0]["term"]}”最符合下面哪个意思？',
                        "choices": quiz_choices,
                        "answer": items[0]["meaning"],
                    },
                    {
                        "type": "fill",
                        "question": f'看中文写英文：{items[-1]["meaning"]}',
                        "answer": items[-1]["term"],
                    },
                ],
            })
        days.append({
            "day": day_number,
            "title": f"Day {day_number} · {groups[0]['topic']} × {groups[2]['topic']}",
            "duration": "约 30 分钟",
            "new_count": config["new_terms_per_day"],
            "groups": groups,
        })

    total_days = len(days)
    return {
        "meta": {
            "course": course_id,
            "title": config["vocab_title"],
            "subtitle": config["vocab_subtitle"],
            "days": total_days,
            "target_days": config["days"],
            "new_terms": total_days * config["new_terms_per_day"],
            "review_steps": config["review_steps"],
            "version": 2,
        },
        "days": days,
    }


def validate_course(course: dict, config: dict) -> None:
    days = course["days"]
    if not days:
        raise ValueError("course contains no days")
    expected_terms = len(days) * config["new_terms_per_day"]
    keys = []
    for expected_day, day in enumerate(days, 1):
        if day["day"] != expected_day or len(day["groups"]) != len(config["groups"]):
            raise ValueError(f"invalid structure on day {expected_day}")
        for group in day["groups"]:
            if len(group["items"]) != config["terms_per_group"] or len(group["exercises"]) != 2:
                raise ValueError(
                    f"day {expected_day} / {group['domain']} must have {config['terms_per_group']} items and 2 exercises"
                )
            keys.extend(item["key"] for item in group["items"])
    if len(keys) != expected_terms:
        raise ValueError(f"expected {expected_terms} terms, got {len(keys)}")
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    if duplicates:
        raise ValueError(f"duplicate vocabulary keys: {', '.join(duplicates)}")


def write_course(course_id: str) -> Path:
    config = load_course_config(course_id)
    course = build_course(course_id)
    validate_course(course, config)
    data_dir = ROOT / "examples" / "courses" / course_id / "vocabulary-month"
    data_dir.mkdir(parents=True, exist_ok=True)
    data_path = data_dir / "month.json"
    data_path.write_text(json.dumps(course, ensure_ascii=False, indent=2), encoding="utf-8")
    out_dir = ROOT / "lessons" / "week" / "courses" / course_id / "vocabulary-month"
    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(data_path, out_dir / "month.json")
    for name in ("index.html", "app.js", "style.css"):
        shutil.copy2(SRC_VOCAB_APP / name, out_dir / name)
    print(
        f"Vocabulary course built: {out_dir} "
        f"({course['meta']['days']} days / target {course['meta']['target_days']}, "
        f"{course['meta']['new_terms']} terms)"
    )
    return data_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course", default="speaking-vocab")
    args = parser.parse_args()
    write_course(args.course)


if __name__ == "__main__":
    main()
