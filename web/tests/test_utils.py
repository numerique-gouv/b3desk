from b3desk.utils import _build_recording_links
from flask_babel import get_locale


def test_build_recording_links_falls_back_to_url_without_direct_link(app):
    """Video format without direct_link should still produce a link using its url."""
    with app.app_context():
        links = _build_recording_links({"video": {"url": "https://bbb.test/v/"}})
    assert links == [{"label": links[0]["label"], "url": "https://bbb.test/v/"}]


def test_locale_selector_outside_request_context(app):
    """Without a request context, the locale selector falls back to the configured variant."""
    with app.app_context():
        locale = get_locale()

    assert str(locale).endswith("seminaire")


def test_locale_selector_outside_request_context_without_variant(app):
    """Without a request context and without MEETING_LOCALE_VARIANT, the fallback is plain french."""
    app.config["MEETING_LOCALE_VARIANT"] = None
    with app.app_context():
        locale = get_locale()

    assert str(locale) == "fr"
