import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from scripts.make_speaking_month import (  # noqa: E402
    TIER_META,
    make_lesson,
    norm_term,
    tier_of,
)

VOCAB_PATH = ROOT / "examples" / "vocabulary-month" / "month.json"

_CACHE = None


def lessons():
    global _CACHE
    if _CACHE is None:
        month = json.loads(VOCAB_PATH.read_text(encoding="utf-8"))
        _CACHE = [(day, make_lesson(day)) for day in month["days"]]
    return _CACHE


def test_thirty_days_with_three_scenes_each():
    pairs = lessons()
    assert len(pairs) == 30
    for raw, lesson in pairs:
        segments = lesson["segments"]
        assert [seg["id"] for seg in segments] == ["seg-01", "seg-02", "seg-03"], raw["day"]


def test_every_days_18_words_reach_the_spoken_story():
    for raw, lesson in lessons():
        haystack = " ".join(seg["en"] for seg in lesson["segments"])
        normalized = re.sub(r"\s+", " ", haystack.lower().replace("'", "").replace("’", "").replace("...", " "))
        for group in raw["groups"]:
            for item in group["items"]:
                assert norm_term(item["term"]) in normalized, (
                    f"day {raw['day']}: term {item['term']!r} missing from story"
                )


def test_every_segment_has_a_real_chinese_translation():
    cjk = re.compile(r"[\u4e00-\u9fff]")
    for raw, lesson in lessons():
        for seg in lesson["segments"]:
            assert seg["zh"].strip(), f"day {raw['day']} {seg['id']} has no translation"
            assert cjk.search(seg["zh"]), f"day {raw['day']} {seg['id']} translation is not Chinese"
            assert len(seg["en"].split()) <= 110, f"day {raw['day']} {seg['id']} exceeds the segment word limit"


def sentences(text):
    return [s for s in re.split(r'(?<=[.!?])"?\s+', text) if s.strip()]


def test_difficulty_climbs_from_short_beginner_lines_to_professional_scenes():
    def avg_sentence_words(day_lesson):
        lengths = []
        for seg in day_lesson["segments"]:
            lengths.extend(len(s.split()) for s in sentences(seg["en"]))
        return sum(lengths) / len(lengths)

    tier_averages = {tier: [] for tier in (1, 2, 3, 4)}
    for raw, lesson in lessons():
        tier_averages[tier_of(int(raw["day"]))].append(avg_sentence_words(lesson))
    means = {tier: sum(vals) / len(vals) for tier, vals in tier_averages.items()}
    assert means[1] < means[2] < means[3] < means[4], means

    day1 = lessons()[0][1]
    longest_day1 = max(
        len(sentence.split())
        for seg in day1["segments"]
        for sentence in sentences(seg["en"])
    )
    assert longest_day1 <= 13, f"day 1 must stay beginner-short, got a {longest_day1}-word sentence"

    rates = {tier: int(TIER_META[tier]["rate"].rstrip("%")) for tier in (1, 2, 3, 4)}
    assert rates[1] < rates[2] < rates[3] < rates[4] < 0, rates


def test_segments_point_at_independent_mp3_audio():
    for raw, lesson in lessons():
        assert lesson["voice"]["engine"] == "edge"
        for i, seg in enumerate(lesson["segments"], 1):
            assert seg["audio_file"] == f"audio/seg-{i:02d}.mp3"
            assert seg["tts"].strip(), f"day {raw['day']} {seg['id']} has no tts text"


def test_transfer_tasks_reference_real_chunks():
    for raw, lesson in lessons():
        chunk_terms = {chunk["t"] for chunk in lesson["chunks"]}
        assert len(lesson["chunks"]) == 6, f"day {raw['day']} should expose six chunks"
        for task in lesson["transfer_tasks"]:
            assert len(task["hint_chunks"]) == 3
            assert all(hint in chunk_terms for hint in task["hint_chunks"])
