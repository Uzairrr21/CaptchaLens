import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.solver.recognizer import recognize_from_html, recognize_from_hint
from app.providers.base import hash_token


def test_recognize_recaptcha_from_html():
    html = '<div class="g-recaptcha" data-sitekey="abc"></div>'
    result = recognize_from_html(html)
    assert result.challenge_type == "recaptcha"
    assert result.supported is True


def test_recognize_hcaptcha_from_html():
    html = '<div class="h-captcha" data-sitekey="abc"></div>'
    result = recognize_from_html(html)
    assert result.challenge_type == "hcaptcha"


def test_recognize_turnstile_from_html():
    html = '<div class="cf-turnstile" data-sitekey="abc"></div>'
    result = recognize_from_html(html)
    assert result.challenge_type == "turnstile"


def test_recognize_unsupported_provider():
    html = '<div class="funcaptcha" data-pkey="abc"></div>'
    result = recognize_from_html(html)
    assert result.supported is False


def test_recognize_unknown_html():
    result = recognize_from_html("<p>just a normal page</p>")
    assert result.challenge_type == "unsupported"
    assert result.supported is False


def test_recognize_from_hint_synthetic():
    result = recognize_from_hint("image")
    assert result.challenge_type == "synthetic_text"
    assert result.supported is True


def test_hash_token_never_returns_raw_token():
    token = "super-secret-token-value"
    hashed = hash_token(token)
    assert hashed != token
    assert len(hashed) == 16


def test_hash_token_none_input():
    assert hash_token(None) is None
    assert hash_token("") is None
