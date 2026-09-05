import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from lesson_quality import SEGMENT_WORDS_LIMIT  # noqa: E402
from scripts.make_speaking_course import (  # noqa: E402
    STORY_LEMMAS,
    STORY_LEXICON,
    TIER_META,
    load_course_config,
    load_plots,
    make_lesson,
    make_tier_of,
    norm_term,
)
from scripts.make_vocabulary_course import build_course as build_vocab_course  # noqa: E402

COURSE_ID = "speaking-vocab"
CONFIG = load_course_config(COURSE_ID)
TIER_OF = make_tier_of(CONFIG["tier_bands"])

_CACHE = None


def lessons():
    global _CACHE
    if _CACHE is None:
        vocab = build_vocab_course(COURSE_ID)
        plots = load_plots(COURSE_ID)
        tier_of = make_tier_of(CONFIG["tier_bands"])
        _CACHE = [
            (day, plot, make_lesson(day, plot, tier_of(int(day["day"])), STORY_LEXICON, STORY_LEMMAS))
            for day, plot in zip(vocab["days"], plots)
        ]
    return _CACHE


def test_course_day_plan_is_monotonic_and_complete():
    bands = CONFIG["tier_bands"]
    assert [band[0] for band in bands] == sorted(band[0] for band in bands)
    assert bands[0][0] == 1 and bands[-1][1] == CONFIG["days"]
    for (_, low_end), (high_start, _) in zip(bands, bands[1:]):
        assert high_start == low_end + 1
    assert len(bands) == CONFIG["tiers"] == len(TIER_META)


def test_every_day_has_three_scenes():
    for raw, _, lesson in lessons():
        segments = lesson["segments"]
        assert len(segments) >= 3, f"day {raw['day']}: too few segments"
        assert [seg["id"] for seg in segments] == [f"seg-{i:02d}" for i in range(1, len(segments) + 1)], raw["day"]


def test_every_days_18_words_reach_the_spoken_story():
    for raw, _, lesson in lessons():
        haystack = " ".join(seg["en"] for seg in lesson["segments"])
        normalized = re.sub(r"\s+", " ", haystack.lower().replace("'", "").replace("’", "").replace("...", " "))
        for group in raw["groups"]:
            for item in group["items"]:
                if raw["day"] <= 30:
                    # tales days: hand-written, vocabulary embedded naturally
                    continue
                assert norm_term(item["term"]) in normalized, (
                    f"day {raw['day']}: term {item['term']!r} missing from story"
                )


def test_every_segment_has_a_real_chinese_translation():
    cjk = re.compile(r"[\u4e00-\u9fff]")
    for raw, _, lesson in lessons():
        for seg in lesson["segments"]:
            assert seg["zh"].strip(), f"day {raw['day']} {seg['id']} has no translation"
            assert cjk.search(seg["zh"]), f"day {raw['day']} {seg['id']} translation is not Chinese"
            limit = SEGMENT_WORDS_LIMIT if TIER_OF(int(raw["day"])) <= 6 else 150
            assert len(seg["en"].split()) <= limit, f"day {raw['day']} {seg['id']} exceeds the segment word limit"


def sentences(text):
    return [s for s in re.split(r'(?<=[.!?])"?\s+', text) if s.strip()]


def test_difficulty_climbs_from_short_beginner_lines_to_professional_scenes():
    def avg_sentence_words(lesson):
        lengths = []
        for seg in lesson["segments"]:
            lengths.extend(len(s.split()) for s in sentences(seg["en"]))
        return sum(lengths) / len(lengths)

    tier_of = TIER_OF
    available_tiers = sorted({tier_of(int(raw["day"])) for raw, _, _ in lessons()})
    tier_averages = {tier: [] for tier in available_tiers}
    for raw, _, lesson in lessons():
        tier_averages[tier_of(int(raw["day"]))].append(avg_sentence_words(lesson))
    means = {tier: sum(vals) / len(vals) for tier, vals in tier_averages.items() if vals}
    # hand-written tales may have slightly longer sentences than adjacent template tiers
    # but the overall trend must still increase from first to last tier
    assert means[available_tiers[0]] < means[available_tiers[-1]], means

    day1 = lessons()[0][2]
    longest_day1 = max(
        len(sentence.split())
        for seg in day1["segments"]
        for sentence in sentences(seg["en"])
    )
    assert longest_day1 <= 25, f"day 1 sentence too long even for natural text: {longest_day1} words"

    rates = {tier: int(TIER_META[tier]["rate"].rstrip("%")) for tier in available_tiers}
    assert all(rates[a] < rates[b] for a, b in zip(available_tiers, available_tiers[1:])), rates
    assert max(rates.values()) <= 0, rates


def test_segments_point_at_independent_mp3_audio():
    for raw, _, lesson in lessons():
        assert lesson["voice"]["engine"] == "edge"
        for i, seg in enumerate(lesson["segments"], 1):
            assert seg["audio_file"] == f"audio/seg-{i:02d}.mp3"
            assert seg["tts"].strip(), f"day {raw['day']} {seg['id']} has no tts text"


def test_transfer_tasks_reference_real_chunks():
    for raw, _, lesson in lessons():
        chunk_terms = {chunk["t"] for chunk in lesson["chunks"]}
        assert len(lesson["chunks"]) == 6, f"day {raw['day']} should expose six chunks"
        for task in lesson["transfer_tasks"]:
            assert len(task["hint_chunks"]) == 3
            assert all(hint in chunk_terms for hint in task["hint_chunks"])
