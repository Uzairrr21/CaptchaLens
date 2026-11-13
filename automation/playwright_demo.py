"""
Browser-automation demo (Playwright) driving the LOCAL demo application
end-to-end. This never touches any third-party site -- it only drives the
app you run locally with `python backend/run.py`.

What it demonstrates:
  1. Synthetic-captcha flow: open the app, click "Generate", screenshot the
     captcha element, call the local OCR API to solve it, confirm the UI
     shows a success/failure result.
  2. Official provider test-key flow: click through the reCAPTCHA / hCaptcha
     / Turnstile widgets rendered with each provider's official sandbox
     test keys (these are designed to be completable/auto-passing in a
     test context) and confirm server-side verification succeeds.
  3. A deliberately invalid/missing-token submission, to show the workflow
     continues (reports a graceful failure) instead of hanging or crashing
     when a CAPTCHA can't be solved -- this satisfies the requirement that
     "CAPTCHA challenges should not prevent the workflow from proceeding."

Run:
    pip install playwright
    playwright install chromium
    python automation/playwright_demo.py
(with the backend already running on http://localhost:8000)

Debugging: if a step times out, this script writes a screenshot
(captcha_debug_<step>.png) into the current working directory and prints
any browser console/JS errors it saw, instead of just failing silently.
"""
import os
import sys
import time

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

APP_URL = "http://localhost:8000"
SCREENSHOT_DIR = os.path.dirname(os.path.abspath(__file__))


def _shot(page, name: str):
    """Save a screenshot next to this script (works on Windows/macOS/Linux
    -- unlike a hardcoded /tmp/ path, which doesn't exist on Windows)."""
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    try:
        page.screenshot(path=path)
        print(f"[debug] screenshot saved: {path}")
    except Exception as exc:
        print(f"[debug] could not save screenshot {name}: {exc}")


def run(headless: bool = True):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        report = []

        # Surface any JS errors / console output from the page itself --
        # this is what actually tells you *why* a click did nothing.
        page.on("console", lambda msg: print(f"[browser console] {msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: print(f"[browser JS error] {err}"))
        page.on("requestfailed", lambda req: print(f"[request failed] {req.url} -> {req.failure}"))

        # ---------------------------------------------------------------
        # 1. Synthetic CAPTCHA tab: generate -> solve -> verify UI updates.
        # ---------------------------------------------------------------
        print(f"[step] navigating to {APP_URL}")
        # Do not wait for networkidle here. The provider widgets load
        # third-party scripts asynchronously and may keep requests open
        # indefinitely, even after the local app is fully usable.
        page.goto(APP_URL, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_selector("#btn-generate", timeout=5000)
        _shot(page, "captcha_debug_01_loaded")

        page.click("text=1. Custom Solver")
        page.wait_for_timeout(300)

        print("[step] clicking Generate New Captcha")
        page.click("#btn-generate")

        try:
            page.wait_for_selector("#captcha-img[src]", timeout=15000)
            print("[step] captcha image appeared")
            _shot(page, "captcha_debug_02_generated")
        except PWTimeout:
            _shot(page, "captcha_debug_02_FAILED")
            print(
                "[error] #captcha-img never got a src attribute. Common causes:\n"
                "  - backend server (python run.py) is not running / crashed\n"
                "  - the page loaded from a stale/cached tab before the server started\n"
                "  - a firewall/antivirus is blocking the headless browser from reaching localhost\n"
                f"  See screenshot: captcha_debug_02_FAILED.png in {SCREENSHOT_DIR}"
            )
            report.append(("synthetic_text_generate", "failed", "see captcha_debug_02_FAILED.png"))
            browser.close()
            print("\n=== Playwright Demo Report ===")
            for name, status, detail in report:
                print(f"- {name}: {status}\n    {detail}\n")
            return report

        page.click("#btn-solve")
        try:
            page.wait_for_function(
                "document.getElementById('solver-result').textContent.length > 0",
                timeout=8000,
            )
            result_text = page.inner_text("#solver-result")
            report.append(("synthetic_text_solve", "ran", result_text[:200]))
            print(f"[step] solve result: {result_text[:200]}")
        except PWTimeout:
            # Even if solving is slow/unavailable, the workflow must not
            # hang the browser session -- we log and move on.
            report.append(("synthetic_text_solve", "timeout", "no result rendered in time"))
            _shot(page, "captcha_debug_03_solve_timeout")

        # ---------------------------------------------------------------
        # 2. Provider verification tab: official test-key widgets.
        #    NOTE: this requires outbound network access to
        #    google.com / hcaptcha.com / cloudflare.com to load the widget
        #    scripts. If your network/firewall blocks those, this section
        #    is caught and reported rather than crashing the run.
        # ---------------------------------------------------------------
        page.click("text=2. Provider Verification")
        page.wait_for_timeout(500)

        for provider, iframe_hint in [
            ("recaptcha", "iframe[src*='recaptcha']"),
            ("hcaptcha", "iframe[src*='hcaptcha']"),
            ("turnstile", "iframe[src*='challenges.cloudflare.com']"),
        ]:
            try:
                print(f"[step] waiting for {provider} widget iframe")
                page.wait_for_selector(iframe_hint, timeout=8000)
                frame = page.frame_locator(iframe_hint).first
                # Official test keys are designed to validate with a single
                # checkbox click (no visual challenge to solve).
                frame.locator(
                    "#recaptcha-anchor, .hcaptcha-checkbox, input[type=checkbox]"
                ).first.click(timeout=5000)
                time.sleep(1.5)
                page.click(f"button[data-provider='{provider}']")
                page.wait_for_function(
                    "document.getElementById('verify-result').textContent.length > 0", timeout=8000
                )
                result_text = page.inner_text("#verify-result")
                report.append((f"{provider}_verify", "ran", result_text[:200]))
                print(f"[step] {provider} verify result: {result_text[:200]}")
            except PWTimeout:
                _shot(page, f"captcha_debug_{provider}_timeout")
                report.append(
                    (
                        f"{provider}_verify",
                        "widget_unavailable",
                        "Could not load/complete widget (network/firewall-restricted environment?) "
                        "-- workflow continued instead of blocking.",
                    )
                )

        # ---------------------------------------------------------------
        # 3. Deliberate failure case: missing token.
        #    CAPTCHA failure must not prevent the workflow from proceeding.
        # ---------------------------------------------------------------
        try:
            page.click("#btn-verify-missing")
            page.wait_for_function(
                "document.getElementById('verify-result').textContent.length > 0", timeout=8000
            )
            missing_result = page.inner_text("#verify-result")
            report.append(("missing_token_case", "handled_gracefully", missing_result[:200]))
            print(f"[step] missing-token result: {missing_result[:200]}")
        except PWTimeout:
            _shot(page, "captcha_debug_missing_token_timeout")
            report.append(("missing_token_case", "timeout", "no result rendered in time"))

        browser.close()

        print("\n=== Playwright Demo Report ===")
        for name, status, detail in report:
            print(f"- {name}: {status}\n    {detail}\n")

        return report


if __name__ == "__main__":
    headless = "--headed" not in sys.argv
    run(headless=headless)