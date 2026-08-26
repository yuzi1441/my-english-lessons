#!/usr/bin/env python3
"""Generate a 30-day speaking course that follows the vocabulary course.

The vocabulary course is the spine: each speaking lesson reuses the same 18
items in three short, read-aloud sections (computer, daily, GitHub).
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VOCAB = ROOT / "examples" / "vocabulary-month" / "month.json"
OUT = ROOT / "examples" / "custom" / "week"


def hard_type(item: dict) -> str:
    part = str(item.get("part", ""))
    return "term" if "术语" in part else "idiom"


def segment_for_group(day: int, group: dict, index: int, items: list[dict] | None = None) -> dict:
    items = items if items is not None else group.get("items", [])
    domain = group.get("domain", "")
    title = group.get("title", "Vocabulary")
    topic = group.get("topic", title)
    english_title = {"computer": "computer English", "daily": "daily English", "github": "GitHub English"}.get(domain, "today's English")
    lines = [
        f"Today I practise {english_title} in a real conversation.",
        "I need to explain a small task clearly to another person.",
    ]
    for item in items:
        term = item.get("term", "")
        if domain == "daily":
            lines.append(f'I say "{term}" in a daily conversation.')
        elif domain == "github":
            lines.append(f'I use "{term}" when I work with my team.')
        else:
            lines.append(f'I say "{term}" when I talk about my computer project.')
    terms = [item.get("term", "this word") for item in items]
    if len(terms) >= 3:
        lines.append(f"I tell my teammate: Today I use {terms[0]}, {terms[1]}, and {terms[2]}.")
    lines.append(f"At the end, I say: I can use {terms[0] if terms else 'this word'} clearly today.")
    en = " ".join(lines)
    zh_lines = [
        f"今天口语练习围绕“{title}”，场景是“{topic}”。",
        "先听英文，再尝试不看中文复述。",
    ]
    for item in items:
        zh_lines.append(f"{item.get('term', '')}：{item.get('meaning', '')}。示例：{item.get('example_speech') or item.get('example', '')}")
    zh_lines.append("最后用自己的经历替换示例中的内容，再说一遍。")
    return {
        "id": f"seg-{index:02d}",
        "en": en,
        "tts": en,
        "zh": "".join(zh_lines),
        "hard": [
            {"w": item.get("term", ""), "type": hard_type(item), "def": item.get("meaning", "")}
            for item in items
            if item.get("term")
        ],
    }


def make_lesson(day: dict) -> dict:
    number = int(day["day"])
    groups = day.get("groups", [])
    segments = []
    for group in groups:
        items = group.get("items", [])
        for offset in range(0, len(items), 3):
            segments.append(segment_for_group(number, group, len(segments) + 1, items[offset : offset + 3]))
    all_items = [item for group in groups for item in group.get("items", [])]
    chunks = [
        {"t": item.get("term", ""), "cn": item.get("meaning", ""), "eg": item.get("example_speech") or item.get("example", "")}
        for item in all_items[:6]
        if item.get("term")
    ]
    patterns = [
        {"t": "The key expression is X.", "cn": "关键表达是 X。"},
        {"t": "In Chinese, it means X.", "cn": "它的中文意思是 X。"},
        {"t": "I can use X clearly today.", "cn": "我今天能清楚地使用 X。"},
    ]
    lexicon = {item["term"].lower(): {"def": item.get("meaning", "")} for item in all_items if item.get("term") and " " not in item["term"]}
    word_count = sum(len(seg["en"].split()) for seg in segments)
    topics = " × ".join(str(group.get("topic", "")) for group in groups)
    return {
        "meta": {
            "title": f"Day {number}: Vocabulary Speaking Lab",
            "title_zh": f"第 {number} 天：当天词汇口语实验室",
            "source": f"Vocabulary Month · Day {number}",
            "url": "",
            "kind": "article",
            "lang": "en",
            "study_card": {
                "word_count": word_count,
                "segment_count": len(segments),
                "difficulty": "词汇主线 · 口语应用",
                "estimated_days": 1,
                "main_practice": "先学词汇 · 再听读 · 最后主动输出",
                "value_points": [f"当天 18 个词汇全部进入口语正文", topics, "30 秒个人化输出"],
                "suggested_pace": "先猜意思 · 听读正文 · 遮住中文复述 · 用自己的经历替换",
            },
        },
        "voice": {"engine": "edge", "voice": "en-US-AndrewNeural", "rate": "-20%", "speed": 0.8},
        "segments": segments,
        "chunks": chunks,
        "patterns": patterns,
        "transfer_tasks": [{
            "genre": "standup_update",
            "task": f"Use any three Day {number} vocabulary items. Say what you did, what problem you had, and what you will do next.",
            "hint_chunks": [item["t"] for item in chunks[:3]],
        }],
        "lexicon": lexicon,
    }


def write_index(days: list[dict]) -> None:
    rows = []
    for day in days:
        number = int(day["day"])
        groups = day.get("groups", [])
        topics = " × ".join(str(group.get("topic", "")) for group in groups)
        rows.append(f'<li><a href="day-{number:02d}/index.html"><h2>Day {number} · 词汇口语实验室</h2><p>{topics} · 约 20 分钟</p></a></li>')
    html = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>英语学习 · 30 天词汇口语课</title><style>body{{font-family:-apple-system,sans-serif;max-width:760px;margin:0 auto;padding:32px 20px;line-height:1.6;background:#fafafa;color:#222}}h1{{font-size:28px}}ul{{list-style:none;padding:0}}li{{background:#fff;border:1px solid #e3e3e3;border-radius:10px;margin:10px 0;overflow:hidden}}a{{display:block;padding:14px 18px;text-decoration:none;color:#222}}h2{{margin:0 0 3px;font-size:17px}}p{{margin:0;color:#666;font-size:13px}}</style></head><body><h1>英语学习 · 30 天词汇口语课</h1><p>词汇是主线；每一天的 18 个词都会进入对应口语正文。</p><ul>{''.join(rows)}</ul></body></html>'''
    (ROOT / "lessons" / "week" / "index.html").write_text(html, encoding="utf-8")


def main() -> None:
    data = json.loads(VOCAB.read_text(encoding="utf-8"))
    days = data.get("days", [])
    if len(days) != 30:
        raise SystemExit(f"vocabulary month must contain 30 days, found {len(days)}")
    for raw in days:
        lesson = make_lesson(raw)
        out = OUT / f"day-{int(raw['day']):02d}" / "segments.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(lesson, ensure_ascii=False, indent=1), encoding="utf-8")
    write_index(days)
    print(f"written 30 vocabulary-linked speaking lessons to {OUT}")


if __name__ == "__main__":
    main()
