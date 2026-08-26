#!/usr/bin/env python3
"""Generate a 30-day speaking course whose story follows the vocabulary month."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOCAB = ROOT / "examples" / "vocabulary-month" / "month.json"
OUT = ROOT / "examples" / "custom" / "week"


def hard_type(item: dict) -> str:
    return "term" if "术语" in str(item.get("part", "")) else "idiom"


def phase(day: int) -> tuple[str, str, str]:
    if day <= 7:
        return "入门故事", "Alex is new on the team. The sentences are short, clear, and easy to repeat.", "Alex is new, so the team uses short sentences."
    if day <= 14:
        return "基础工作", "Alex can now describe a small task and ask a clear question.", "Alex has practised the basics, so the team gives Alex a small task."
    if day <= 21:
        return "项目协作", "Alex now connects ideas, explains a problem, and reports progress.", "Because the project is growing, Alex needs to explain each step to the team."
    return "专业场景", "Alex now handles an AI, security, or deployment task and gives a careful update.", "As the project becomes more professional, Alex gives a clear update and checks the risks."


def term_text(items: list[dict]) -> str:
    return " and ".join(f'"{item.get("term", "")}"' for item in items)


def segment_for_scene(day: int, groups: list[dict], scene: int, start: int) -> dict:
    computer, daily, github = (group.get("items", []) for group in groups)
    c, d, g = computer[start : start + 2], daily[start : start + 2], github[start : start + 2]
    phase_name, level_note, bridge = phase(day)
    if day == 1:
        if scene == 1:
            en_lines = [
                "My name is Alex. Today is Monday, my first day at a new job.",
                "I am a new engineer. My team makes a chat program.",
                f"In the morning, Maria shows me the {term_text(c)}. I look carefully and repeat the words.",
                f"She smiles and says {term_text(d)}. After lunch, she shows me the {term_text(g)} on GitHub.",
                "I am a little nervous, but Maria smiles and says that I can take my time.",
            ]
        elif scene == 2:
            en_lines = [
                "After the morning meeting, Maria helps me learn the project.",
                f"She points to the {term_text(c)} and shows me where the files are.",
                f"Then she says {term_text(d)}. I answer slowly and try to sound friendly.",
                f"Together, we read the {term_text(g)} and find the next small task.",
                "I do not know every word yet, but I feel better because the team is kind.",
            ]
        else:
            en_lines = [
                "Before I leave, Maria gives me a small task.",
                f"I use the {term_text(c)} to finish it and then save my work.",
                f"She asks me about {term_text(d)}. I listen, smile, and say goodbye.",
                f"Then I open GitHub and look at the {term_text(g)} with her.",
                "It is my first day, and I am ready to learn one small step at a time.",
            ]
    elif day <= 7:
        en_lines = [
            f"It is day {day}. Alex is still new on the team. {bridge}",
            f"In the morning, Maria helps me use the {term_text(c)} for a small task.",
            f"During our chat, she says {term_text(d)}. I answer clearly and ask one short question.",
            f"After lunch, I work with the team on GitHub and practise {term_text(g)}.",
            "The task is small, but I understand a little more than yesterday.",
        ]
    elif day <= 14:
        en_lines = [
            f"On day {day}, Alex has a small task. {bridge}",
            f"First, Alex checks {term_text(c)} and writes one clear note about the work.",
            f"During a short chat, Maria uses {term_text(d)}. Alex answers politely and asks one question.",
            f"Then Alex records the progress with {term_text(g)} so the team can follow the change.",
            "The task is not big, but Alex can now explain it from start to finish.",
        ]
    elif day <= 21:
        en_lines = [
            f"By day {day}, Alex is helping with a growing project. {bridge}",
            f"Before the meeting, Alex reviews {term_text(c)} and explains why each one matters.",
            f"When a teammate asks for an update, Alex uses {term_text(d)} to keep the conversation clear.",
            f"After the meeting, Alex updates the project with {term_text(g)} and records the next action.",
            "The team understands the plan, and Alex has learned to connect vocabulary with real work.",
        ]
    else:
        en_lines = [
            f"Near the end of the month, Alex handles a more professional task. {bridge}",
            f"Alex checks {term_text(c)} before making a decision and explains the possible risk.",
            f"In the discussion, Alex uses {term_text(d)} to clarify the goal, timing, and next step.",
            f"Finally, Alex documents {term_text(g)} so another teammate can review the work later.",
            "The work is not perfect, but the update is clear, careful, and useful.",
        ]
    en = " ".join(en_lines)
    title = groups[0].get("title", "词汇")
    topics = "、".join(str(group.get("topic", "")) for group in groups)
    terms = c + d + g
    zh = (
        f"第 {day} 天 · {phase_name}。今天把“{topics}”放进 Alex 的连续故事。"
        f"{level_note}先听一遍，再遮住中文复述；最后把 Alex 换成自己。"
        f"本段词汇：{', '.join(item.get('term', '') for item in terms)}。"
    )
    hard = [{"w": item.get("term", ""), "type": hard_type(item), "def": item.get("meaning", "")} for item in terms if item.get("term")]
    return {"id": f"seg-{scene:02d}", "en": en, "tts": en, "audio_file": f"audio/seg-{scene:02d}.m4a", "zh": zh, "hard": hard}


def make_lesson(day_data: dict) -> dict:
    day = int(day_data["day"])
    groups = day_data.get("groups", [])
    segments = [segment_for_scene(day, groups, scene, start) for scene, start in enumerate((0, 2, 4), 1)]
    all_items = [item for group in groups for item in group.get("items", [])]
    chunks = [{"t": item.get("term", ""), "cn": item.get("meaning", ""), "eg": item.get("example_speech") or item.get("example", "")} for item in all_items[:6] if item.get("term")]
    phase_name, _, _ = phase(day)
    patterns = ([{"t": "I am new on the team.", "cn": "我是团队里的新人。"}, {"t": "I need to X.", "cn": "我需要做 X。"}, {"t": "I feel ready for the next step.", "cn": "我准备好进行下一步了。"}] if day <= 7 else [{"t": "First, I X.", "cn": "首先，我 X。"}, {"t": "Then I X.", "cn": "然后，我 X。"}, {"t": "I can explain X from start to finish.", "cn": "我能从头到尾解释 X。"}])
    lexicon = {item["term"].lower(): {"def": item.get("meaning", "")} for item in all_items if item.get("term") and " " not in item["term"]}
    word_count = sum(len(segment["en"].split()) for segment in segments)
    topics = " × ".join(str(group.get("topic", "")) for group in groups)
    english_titles = [(1, 1, "My First Standup"), (2, 7, "My First Week"), (8, 14, "Small Tasks"), (15, 21, "Project Collaboration"), (22, 30, "Professional Workflow")]
    english_title = next(title for low, high, title in english_titles if low <= day <= high)
    return {
        "meta": {"title": f"Day {day}: Alex's {english_title}", "title_zh": f"第 {day} 天：Alex 的{phase_name}", "source": f"Vocabulary Month · Day {day}", "url": "", "kind": "article", "lang": "en", "study_card": {"word_count": word_count, "segment_count": len(segments), "difficulty": f"{phase_name} · 词汇主线", "estimated_days": 1, "main_practice": "先听故事 · 再跟读 · 最后替换成自己的经历", "value_points": [f"当天 18 个词汇都进入 Alex 的故事", topics, "30 秒口语输出"], "suggested_pace": "先猜大意 · 听读 2 遍 · 遮住中文复述 · 完成输出任务"}},
        "voice": {"engine": "edge", "voice": "en-US-AndrewNeural", "rate": "-8%", "speed": 0.92}, "segments": segments, "chunks": chunks, "patterns": patterns,
        "transfer_tasks": [{"genre": "standup_update", "task": f"Use any three Day {day} vocabulary items. Retell Alex's situation in your own words, then say what you did, what was difficult, and what you will do next.", "hint_chunks": [item["t"] for item in chunks[:3]]}], "lexicon": lexicon,
    }


def write_index(days: list[dict]) -> None:
    rows = []
    for day in days:
        number = int(day["day"])
        topics = " × ".join(str(group.get("topic", "")) for group in day.get("groups", []))
        rows.append(f'<li><a href="day-{number:02d}/index.html"><h2>Day {number} · Alex 的词汇口语故事</h2><p>{topics} · 约 20 分钟</p></a></li>')
    html = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>英语学习 · 30 天词汇口语课</title><style>body{{font-family:-apple-system,sans-serif;max-width:760px;margin:0 auto;padding:32px 20px;line-height:1.6;background:#fafafa;color:#222}}h1{{font-size:28px}}ul{{list-style:none;padding:0}}li{{background:#fff;border:1px solid #e3e3e3;border-radius:10px;margin:10px 0;overflow:hidden}}a{{display:block;padding:14px 18px;text-decoration:none;color:#222}}h2{{margin:0 0 3px;font-size:17px}}p{{margin:0;color:#666;font-size:13px}}</style></head><body><h1>英语学习 · 30 天词汇口语课</h1><p>词汇是主线；Alex 的故事从新人入职逐步走到专业项目协作。</p><ul>{''.join(rows)}</ul></body></html>'''
    (ROOT / "lessons" / "week" / "index.html").write_text(html, encoding="utf-8")


def main() -> None:
    data = json.loads(VOCAB.read_text(encoding="utf-8"))
    days = data.get("days", [])
    if len(days) != 30:
        raise SystemExit(f"vocabulary month must contain 30 days, found {len(days)}")
    for raw in days:
        out = OUT / f"day-{int(raw['day']):02d}" / "segments.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(make_lesson(raw), ensure_ascii=False, indent=1), encoding="utf-8")
    write_index(days)
    print(f"written 30 progressive story lessons to {OUT}")


if __name__ == "__main__":
    main()
