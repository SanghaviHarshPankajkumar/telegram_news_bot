from app.telegram import WELCOME_MESSAGE, markdown_to_telegram_html


def test_markdown_bold_converts_to_html():
    assert markdown_to_telegram_html("Line\n**Hello**") == "<b>Line</b>\n<b>Hello</b>"


def test_section_headers_are_bolded():
    rendered = markdown_to_telegram_html("Daily Dose of DS | 06 Jun 2026\nToday's lineup\n- A")
    assert "<b>Daily Dose of DS | 06 Jun 2026</b>" in rendered
    assert "<b>Today&#x27;s lineup</b>" in rendered
    assert "• A" in rendered


def test_welcome_message_uses_release_language_not_polling_interval():
    assert "checked every 30 minutes" not in WELCOME_MESSAGE
    assert "when detected" in WELCOME_MESSAGE
