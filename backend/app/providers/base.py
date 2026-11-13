import hashlib
import time
from dataclasses import dataclass, field

import httpx


@dataclass
class VerifyResult:
    success: bool
    error_codes: list[str] = field(default_factory=list)
    hostname: str | None = None
    challenge_ts: str | None = None
    raw: dict | None = None


def hash_token(token: str | None) -> str | None:
    """Never store/log raw tokens -- keep only a short, irreversible hash
    for reuse detection and debugging."""
    if not token:
        return None
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]


def post_siteverify(url: str, data: dict, timeout: float = 8.0) -> dict:
    """Shared HTTP call wrapper with a sane timeout.

    Secrets are passed only in the POST body over HTTPS to the provider;
    callers must take care never to log `data` directly (it contains the
    secret key).
    """
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, data=data)
        resp.raise_for_status()
        return resp.json()
