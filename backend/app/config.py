"""
Central configuration.

All provider keys default to the OFFICIAL, PUBLICLY DOCUMENTED sandbox/test
keys published by each provider for development and testing purposes. These
always-pass (or always-controllable) in their respective sandboxes and are
safe to ship in a repo -- they are published by Google/hCaptcha/Cloudflare
themselves, not secrets.

Override any of them via a real .env to point at your own site + real keys
if you want to test against a live (but still candidate-owned) property.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'captcha_tool.db'}")

# ---------------------------------------------------------------------------
# Google reCAPTCHA v2 ("I'm not a robot") official test keys.
# Docs: https://developers.google.com/recaptcha/docs/faq
# "always passes" the checkbox, siteverify always returns success for them.
RECAPTCHA_SITE_KEY = os.getenv(
    "RECAPTCHA_SITE_KEY", "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
)
RECAPTCHA_SECRET_KEY = os.getenv(
    "RECAPTCHA_SECRET_KEY", "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
)
RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"

# ---------------------------------------------------------------------------
# hCaptcha official test keys.
# Docs: https://docs.hcaptcha.com/#integration-testing-test-keys
HCAPTCHA_SITE_KEY = os.getenv(
    "HCAPTCHA_SITE_KEY", "10000000-ffff-ffff-ffff-000000000001"
)
HCAPTCHA_SECRET_KEY = os.getenv(
    "HCAPTCHA_SECRET_KEY", "0x0000000000000000000000000000000000000000"
)
HCAPTCHA_VERIFY_URL = "https://hcaptcha.com/siteverify"

# ---------------------------------------------------------------------------
# Cloudflare Turnstile official test keys.
# Docs: https://developers.cloudflare.com/turnstile/troubleshooting/testing/
TURNSTILE_SITE_KEY = os.getenv("TURNSTILE_SITE_KEY", "1x00000000000000000000AA")
TURNSTILE_SECRET_KEY = os.getenv(
    "TURNSTILE_SECRET_KEY", "1x0000000000000000000000000000000AA"
)
TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

# ---------------------------------------------------------------------------
# Custom OCR solver tuning
OCR_CONFIDENCE_THRESHOLD = float(os.getenv("OCR_CONFIDENCE_THRESHOLD", "55"))
TESSERACT_CMD = os.getenv("TESSERACT_CMD")  # only needed on Windows typically

# Hypothetical third-party per-solve cost used purely for the cost-reporting
# column in the dashboard (e.g. what a 2Captcha/Anti-Captcha style service
# would charge). No third-party API is actually called for this.
THIRDPARTY_COST_PER_SOLVE_USD = float(os.getenv("THIRDPARTY_COST_PER_SOLVE_USD", "0.0010"))

APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
