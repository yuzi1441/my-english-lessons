import json
from pathlib import Path

import jsonschema

from scripts.make_vocabulary_course import (
    build_course,
    load_course_config,
    normalize_key,
    validate_course,
)


ROOT = Path(__file__).resolve().parents[1]
COURSE_ID = "speaking-vocab"
CONFIG = load_course_config(COURSE_ID)


def course():
    return build_course(COURSE_ID)


def test_course_contract_and_schema():
    built = course()
    validate_course(built, CONFIG)
    schema = json.loads((ROOT / "src" / "vocabulary-month.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(built, schema)
    assert built["meta"]["course"] == COURSE_ID
    assert built["meta"]["days"] == len(built["days"])
    assert built["meta"]["days"] <= CONFIG["days"]
    # months are authored in 30-day blocks; the final month may add the last 5 days to 365
    assert built["meta"]["days"] % 30 in (0, 5)


def test_days_are_contiguous_and_structured():
    built = course()
    assert [day["day"] for day in built["days"]] == list(range(1, len(built["days"]) + 1))
    assert all([group["domain"] for group in day["groups"]] == CONFIG["groups"] for day in built["days"])
    assert all(len(group["items"]) == CONFIG["terms_per_group"] for day in built["days"] for group in day["groups"])
    total = sum(len(group["items"]) for day in built["days"] for group in day["groups"])
    assert total == built["meta"]["new_terms"]


def test_vocabulary_is_unique_after_normalization():
    built = course()
    keys = [normalize_key(item["term"]) for day in built["days"] for group in day["groups"] for item in group["items"]]
    assert len(keys) == len(set(keys)) == built["meta"]["new_terms"]


def test_each_group_has_recognition_and_recall():
    built = course()
    for day in built["days"]:
        for group in day["groups"]:
            assert [exercise["type"] for exercise in group["exercises"]] == ["choice", "fill"]
            assert all(exercise["answer"] for exercise in group["exercises"])


def test_audio_contract_and_technical_pronunciation():
    built = course()
    items = [item for day in built["days"] for group in day["groups"] for item in group["items"]]
    assert len({item["audio_term"] for item in items}) == built["meta"]["new_terms"]
    assert len({item["audio_example"] for item in items}) == built["meta"]["new_terms"]
    by_term = {item["term"]: item for item in items}
    assert by_term["API"]["speech"] == "A P I"
    assert by_term["README file"]["speech"] == "read me file"
    assert by_term["HTTP request"]["speech"] == "H T T P request"


def test_word_cards_have_individual_learning_actions():
    source = (ROOT / "src" / "vocabulary_month" / "app.js").read_text(encoding="utf-8")
    assert 'data-add-word="${esc(item.id)}"' in source
    assert "播放单词" in source
    assert "查看这个词的中文释义" in source
    assert "function addWord(item, day)" in source
