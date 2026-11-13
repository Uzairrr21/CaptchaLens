"""
Challenge-type recognizer.

Given either a direct hint (provider name / "image") or a raw HTML snippet
from a contact page (as you might get from `page.content()` in Playwright),
identifies which kind of CAPTCHA challenge is present and whether this tool
supports solving/verifying it.
"""
import re
from dataclasses import dataclass

SUPPORTED_TYPES = {"synthetic_text", "recaptcha", "hcaptcha", "turnstile"}

# Markers that show up in the real DOM/script tags for each provider.
_MARKERS = {
    "recaptcha": [
        r"g-recaptcha",
        r"grecaptcha\.render",
        r"www\.google\.com/recaptcha",
        r"recaptcha/api\.js",
    ],
    "hcaptcha": [
        r"h-captcha",
        r"hcaptcha\.com/1/api\.js",
        r"hcaptcha\.render",
    ],
    "turnstile": [
        r"cf-turnstile",
        r"challenges\.cloudflare\.com/turnstile",
        r"turnstile\.render",
    ],
    # Known-but-unsupported providers, so we can explicitly say "unsupported"
    # instead of silently misclassifying them.
    "funcaptcha": [r"funcaptcha", r"arkoselabs"],
    "geetest": [r"geetest"],
}


@dataclass
class Recognition:
    challenge_type: str
    supported: bool
    detail: str


def recognize_from_hint(provider_hint: str | None) -> Recognition:
    if not provider_hint:
        return Recognition("unknown", False, "No hint or HTML provided")
    hint = provider_hint.strip().lower()
    if hint in ("image", "synthetic", "synthetic_text", "text"):
        return Recognition("synthetic_text", True, "Synthetic/candidate-controlled text image CAPTCHA")
    if hint in SUPPORTED_TYPES:
        return Recognition(hint, True, f"{hint} explicitly specified and supported")
    if hint in _MARKERS:
        return Recognition(hint, False, f"{hint} recognized but not a supported solving target")
    return Recognition("unsupported", False, f"'{provider_hint}' did not match any known challenge signature")


def recognize_from_html(html_snippet: str) -> Recognition:
    haystack = html_snippet or ""
    for challenge_type, patterns in _MARKERS.items():
        for pattern in patterns:
            if re.search(pattern, haystack, flags=re.IGNORECASE):
                supported = challenge_type in SUPPORTED_TYPES
                detail = (
                    f"Matched marker '{pattern}' -> {challenge_type}"
                    if supported
                    else f"Matched marker '{pattern}' -> {challenge_type} (not a supported solving target)"
                )
                return Recognition(challenge_type, supported, detail)
    # Fall back: a plain <img> whose src/alt mentions captcha => synthetic image captcha
    if re.search(r"(src|alt)=[\"'][^\"']*captcha[^\"']*[\"']", haystack, flags=re.IGNORECASE):
        return Recognition("synthetic_text", True, "Plain <img> captcha element detected")
    return Recognition("unsupported", False, "No known CAPTCHA signature found in the supplied HTML")
