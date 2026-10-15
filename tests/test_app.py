"""Smoke test: the dashboard renders on the real dataset without errors."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def test_app_renders_and_filters():
    at = AppTest.from_file(APP, default_timeout=120).run()
    assert not at.exception
    assert [m.label for m in at.metric][:2] == ["Net revenue", "Orders"]
    at.sidebar.multiselect[0].set_value(["Germany"]).run()
    assert not at.exception
