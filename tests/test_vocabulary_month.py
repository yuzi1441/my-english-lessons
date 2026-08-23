import json
from pathlib import Path

import jsonschema

from scripts.make_vocabulary_month import build_course, normalize_key, validate_course


ROOT = Path(__file__).resolve().parents[1]


def test_month_contract_and_schema():
    course = build_course()
    validate_course(course)
    schema = json.loads((ROOT / "src" / "vocabulary-month.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(course, schema)


def test_exact_counts_and_domains():
    course = build_course()
    assert len(course["days"]) == 30
    assert [day["day"] for day in course["days"]] == list(range(1, 31))
    assert all([group["domain"] for group in day["groups"]] == ["computer", "daily", "github"] for day in course["days"])
    assert all(len(group["items"]) == 6 for day in course["days"] for group in day["groups"])
    assert sum(len(group["items"]) for day in course["days"] for group in day["groups"]) == 540


def test_vocabulary_is_unique_after_normalization():
    course = build_course()
    keys = [normalize_key(item["term"]) for day in course["days"] for group in day["groups"] for item in group["items"]]
    assert len(keys) == len(set(keys)) == 540


def test_each_group_has_recognition_and_recall():
    course = build_course()
    for day in course["days"]:
        for group in day["groups"]:
            assert [exercise["type"] for exercise in group["exercises"]] == ["choice", "fill"]
            assert all(exercise["answer"] for exercise in group["exercises"])


def test_audio_contract_and_technical_pronunciation():
    course = build_course()
    items = [item for day in course["days"] for group in day["groups"] for item in group["items"]]
    assert len({item["audio_term"] for item in items}) == 540
    assert len({item["audio_example"] for item in items}) == 540
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
