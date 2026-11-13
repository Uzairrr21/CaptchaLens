import httpx

from app.config import HCAPTCHA_SECRET_KEY, HCAPTCHA_SITE_KEY, HCAPTCHA_VERIFY_URL
from app.providers.base import VerifyResult, post_siteverify


def verify_hcaptcha(token: str | None, remote_ip: str | None = None) -> VerifyResult:
    if not token:
        return VerifyResult(success=False, error_codes=["missing-input-response"])

    payload = {
        "secret": HCAPTCHA_SECRET_KEY,
        "response": token,
        "sitekey": HCAPTCHA_SITE_KEY,
    }
    if remote_ip:
        payload["remoteip"] = remote_ip

    try:
        raw = post_siteverify(HCAPTCHA_VERIFY_URL, payload)
    except httpx.TimeoutException:
        return VerifyResult(success=False, error_codes=["timeout-contacting-provider"])
    except httpx.HTTPError as exc:
        return VerifyResult(success=False, error_codes=[f"http-error:{exc.__class__.__name__}"])

    return VerifyResult(
        success=bool(raw.get("success")),
        error_codes=raw.get("error-codes", []),
        hostname=raw.get("hostname"),
        challenge_ts=raw.get("challenge_ts"),
        raw=raw,
    )
