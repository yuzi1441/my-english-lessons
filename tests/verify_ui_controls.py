"""Mobile layout verification at a 390px viewport (iPhone-class width).

Prerequisites: scripts/build_course.py (or at least the lesson build step) has run.
Run: python -m pytest tests/verify_ui_controls.py -q
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

VIEWPORT = {"width": 390, "height": 844}


@pytest.fixture(scope="module")
def server():
    if not (SITE / "index.html").exists():
        pytest.skip("lessons/week is not built yet; run scripts/build_course.py first")
    handler = lambda *args, **kwargs: http.server.SimpleHTTPRequestHandler(*args, directory=str(SITE), **kwargs)
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        yield f"http://127.0.0.1:{httpd.server_address[1]}"
        httpd.shutdown()


@pytest.fixture(scope="module")
def mobile_page(server):
    with playwright.sync_playwright() as engine:
        try:
            browser = engine.chromium.launch(channel=os.environ.get("PW_CHANNEL") or None)
        except Exception as exc:
            pytest.skip(f"no browser available (set PW_CHANNEL=chrome or run python -m playwright install chromium): {exc}")
        page = browser.new_page(viewport=VIEWPORT, device_scale_factor=2, is_mobile=True)
        page.base_url = server
        yield page
        browser.close()


def overflow_report(page):
    return page.evaluate(
        """() => {
            const width = document.documentElement.clientWidth;
            const offenders = [];
            for (const el of document.querySelectorAll('body *')) {
                const rect = el.getBoundingClientRect();
                if (rect.width > width + 2) {
                    offenders.push(`${el.tagName}.${String(el.className).slice(0, 40)} w=${Math.round(rect.width)}`);
                }
            }
            return { width, offenders: offenders.slice(0, 8) };
        }"""
    )


def test_day_page_has_no_horizontal_overflow_at_390(mobile_page):
    page = mobile_page
    page.goto(f"{page.base_url}/courses/speaking-vocab/day-001/index.html")
    page.wait_for_selector(".seg")
    report = overflow_report(page)
    assert report["offenders"] == [], f"elements overflow 390px: {report['offenders']}"


def test_vocabulary_page_has_no_horizontal_overflow_at_390(mobile_page):
    page = mobile_page
    page.goto(f"{page.base_url}/courses/speaking-vocab/vocabulary-month/index.html?day=1")
    page.wait_for_selector(".word-card")
    report = overflow_report(page)
    assert report["offenders"] == [], f"elements overflow 390px: {report['offenders']}"


def test_index_page_has_no_horizontal_overflow_at_390(mobile_page):
    page = mobile_page
    page.goto(f"{page.base_url}/index.html")
    page.wait_for_selector("a")
    report = overflow_report(page)
    assert report["offenders"] == [], f"elements overflow 390px: {report['offenders']}"


def test_player_controls_are_reachable_on_mobile(mobile_page):
    page = mobile_page
    page.goto(f"{page.base_url}/courses/speaking-vocab/day-001/index.html")
    page.wait_for_selector(".seg")
    assert page.locator("#playBtn").is_visible()
    assert page.locator('[data-play="0"]').is_visible()
    # the fixed player bar must sit inside the viewport
    box = page.locator(".player").bounding_box()
    assert box is not None and box["x"] >= 0 and box["x"] + box["width"] <= VIEWPORT["width"] + 2


def test_translation_and_audio_note_present_on_mobile(mobile_page):
    page = mobile_page
    page.goto(f"{page.base_url}/courses/speaking-vocab/day-001/index.html")
    page.wait_for_selector(".seg")
    translations = page.locator(".seg .zh").all_inner_texts()
    assert len(translations) == 3 and all(text.strip() for text in translations)
