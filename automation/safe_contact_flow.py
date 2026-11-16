"""Safe local contact-form automation demo.

This script is intentionally restricted to localhost. It may fill a local
test form and optionally wait for a human to complete a CAPTCHA, but it never
attempts to solve or bypass a live CAPTCHA.
"""
import argparse
import os
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright

AUTHORIZED_HOSTS = {
    host.strip().lower()
    for host in os.getenv("AUTHORIZED_CONTACT_HOSTS", "localhost,127.0.0.1,::1").split(",")
    if host.strip()
}
CAPTCHA_MARKERS = {
    "recaptcha": ("g-recaptcha", "recaptcha/api.js", "grecaptcha"),
    "hcaptcha": ("h-captcha", "hcaptcha.com/1/api.js", "hcaptcha"),
    "turnstile": ("cf-turnstile", "challenges.cloudflare.com/turnstile", "turnstile"),
}


@dataclass
class FlowResult:
    status: str
    detail: str
    challenge_type: str | None = None


def _authorized_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and (parsed.hostname or "").lower() in AUTHORIZED_HOSTS


def _challenge_type(html: str) -> str | None:
    lowered = html.lower()
    for challenge, markers in CAPTCHA_MARKERS.items():
        if any(marker in lowered for marker in markers):
            return challenge
    return None


def run_contact_flow(
    url: str,
    name: str,
    email: str,
    message: str,
    manual_captcha: bool = False,
) -> FlowResult:
    if not _authorized_url(url):
        return FlowResult("blocked", "The URL is not in AUTHORIZED_CONTACT_HOSTS.")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not manual_captcha)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=15_000)
            page.get_by_label("Name", exact=False).first.fill(name)
            page.get_by_label("Email", exact=False).first.fill(email)
            page.get_by_label("Message", exact=False).first.fill(message)

            challenge = _challenge_type(page.content())
            if challenge and not manual_captcha:
                return FlowResult(
                    "captcha_detected",
                    "CAPTCHA detected; no automatic bypass was attempted.",
                    challenge,
                )

            if challenge:
                input("Complete the CAPTCHA in the browser, then press Enter here: ")
                if _challenge_type(page.content()):
                    return FlowResult(
                        "captcha_incomplete",
                        "The CAPTCHA is still present; the form was not submitted.",
                        challenge,
                    )

            form = page.locator("form").first
            action = form.get_attribute("action") or page.url
            resolved_action = urljoin(page.url, action)
            if not _authorized_url(resolved_action):
                return FlowResult("blocked", "The form action is not authorized; submission was refused.")

            form.locator("button[type='submit'], input[type='submit']").first.click()
            return FlowResult("submitted", "Local form submitted successfully.")
        finally:
            browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the localhost-only safe contact-form demo.")
    parser.add_argument("--url", default="http://localhost:8000", help="Local test form URL")
    parser.add_argument("--name", default="CaptchaLens Test")
    parser.add_argument("--email", default="test@example.invalid")
    parser.add_argument("--message", default="Authorized local automation test")
    parser.add_argument(
        "--manual-captcha",
        action="store_true",
        help="Show the browser and wait for a human to complete a detected CAPTCHA",
    )
    args = parser.parse_args()
    result = run_contact_flow(
        args.url, args.name, args.email, args.message, args.manual_captcha
    )
    print(result)


if __name__ == "__main__":
    main()
