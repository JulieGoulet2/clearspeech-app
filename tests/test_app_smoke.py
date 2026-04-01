"""
Very small smoke tests for the Streamlit app.

These tests check that:
- the app starts
- important UI elements are present

They do NOT test the full AI behavior.
"""

from streamlit.testing.v1 import AppTest


def test_app_starts():
    """
    The app should run without crashing.
    """
    at = AppTest.from_file("app.py")
    at.run()
    assert not at.exception


def test_app_shows_title():
    """
    The title should be visible on the first screen.
    """
    at = AppTest.from_file("app.py")
    at.run()
    assert any("ClearSpeech" in h.value for h in at.title)


def test_app_has_text_area():
    """
    The first screen should contain at least one text area for user input.
    """
    at = AppTest.from_file("app.py")
    at.run()
    assert len(at.text_area) >= 1