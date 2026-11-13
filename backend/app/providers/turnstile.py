import httpx

from app.config import TURNSTILE_SECRET_KEY, TURNSTILE_VERIFY_URL
from app.providers.base import VerifyResult, post_siteverify


def verify_turnstile(token: str | None, remote_ip: str | None = None) -> VerifyResult:
    if not token:
        return VerifyResult(success=False, error_codes=["missing-input-response"])

    payload = {"secret": TURNSTILE_SECRET_KEY, "response": token}
    if remote_ip:
        payload["remoteip"] = remote_ip

    try:
        raw = post_siteverify(TURNSTILE_VERIFY_URL, payload)
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
