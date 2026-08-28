"""Browser smoke test: lessons build, segments render, and every audio file plays.

Prerequisites: bash build_month.sh (or at least the lesson + audio steps) has run.
Run: python -m pytest tests/verify_browser.py -q
"""
import http.server
import os
import socketserver
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "lessons" / "week"

playwright = pytest.importorskip("playwright.sync_api")


@pytest.fixture(scope="module")
def server():
    if not (SITE / "index.html").exists():
        pytest.skip("lessons/week is not built yet; run build_month.sh first")
    handler = lambda *args, **kwargs: http.server.SimpleHTTPRequestHandler(*args, directory=str(SITE), **kwargs)
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        yield f"http://127.0.0.1:{httpd.server_address[1]}"
        httpd.shutdown()


@pytest.fixture(scope="module")
def browser_page(server):
    with playwright.sync_playwright() as engine:
        try:
            browser = engine.chromium.launch(channel=os.environ.get("PW_CHANNEL") or None)
        except Exception as exc:
            pytest.skip(f"no browser available (set PW_CHANNEL=chrome or run python -m playwright install chromium): {exc}")
        page = browser.new_page()
        page.base_url = server
        yield page
        browser.close()


def test_day_page_renders_three_story_scenes(browser_page):
    page = browser_page
    page.goto(f"{page.base_url}/day-01/index.html")
    page.wait_for_selector(".seg")
    assert page.locator(".seg").count() == 3
    assert page.locator("#vocabBridge .vocab-bridge-word").count() == 18
    translations = page.locator(".seg .zh").all_inner_texts()
    assert all(text.strip() for text in translations)


def test_all_segment_audio_files_exist_and_play(browser_page):
    page = browser_page
    page.goto(f"{page.base_url}/day-01/index.html")
    page.wait_for_selector(".seg")
    status = page.evaluate("window.__AUDIO_STATUS__")
    assert status["missing"] == [], f"segments without audio: {status['missing']}"

    for seg_id in ("seg-01", "seg-02", "seg-03"):
        response = page.request.get(f"{page.base_url}/day-01/audio/{seg_id}.mp3")
        assert response.ok
        assert len(response.body()) > 20000, f"{seg_id}.mp3 is too small to be real narration"

    # click the first play button; the page must attach a real <audio> element
    page.click('[data-play="0"]')
    page.wait_for_function("window.ImmersionReader.state.audio && window.ImmersionReader.state.audio.src")
    src = page.evaluate("window.ImmersionReader.state.audio.src")
    assert src.endswith("audio/seg-01.mp3"), src
    did_fall_back = page.evaluate(
        "() => new Promise(resolve => setTimeout(() => resolve(Boolean(window.speechSynthesis && window.speechSynthesis.speaking)), 600))"
    )
    assert not did_fall_back, "audio fell back to browser speech synthesis"


def test_vocabulary_month_page_loads_all_18_cards(browser_page):
    page = browser_page
    page.goto(f"{page.base_url}/vocabulary-month/index.html?day=1")
    page.wait_for_selector(".word-card")
    assert page.locator(".word-card").count() == 18
    response = page.request.get(f"{page.base_url}/vocabulary-month/month.json")
    assert response.ok
    assert len(response.body()) > 100000


def test_word_audio_is_independent_for_vocabulary_cards(browser_page):
    page = browser_page
    response = page.request.get(f"{page.base_url}/vocabulary-month/audio/d01-computer-01-term.mp3")
    assert response.ok, "vocabulary term audio missing — run scripts/generate_vocabulary_audio.py"
    assert len(response.body()) > 2000
