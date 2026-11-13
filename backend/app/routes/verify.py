import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import VerificationAttempt
from app.providers.base import hash_token
from app.providers.recaptcha import verify_recaptcha
from app.providers.hcaptcha import verify_hcaptcha
from app.providers.turnstile import verify_turnstile
from app.schemas import VerifyTokenRequest, VerifyTokenResponse

router = APIRouter(prefix="/api", tags=["verify"])

_VERIFIERS = {
    "recaptcha": verify_recaptcha,
    "hcaptcha": verify_hcaptcha,
    "turnstile": verify_turnstile,
}

# Tracks token hashes we've already accepted, so a resubmitted (reused)
# token is caught locally even before round-tripping to the provider.
_SEEN_TOKEN_HASHES: set[str] = set()


@router.post("/verify", response_model=VerifyTokenResponse)
def verify_token(req: VerifyTokenRequest, db: Session = Depends(get_db)):
    provider = req.provider.lower().strip()
    if provider not in _VERIFIERS:
        raise HTTPException(status_code=400, detail=f"Unsupported provider '{req.provider}'")

    start = time.perf_counter()
    token_hash = hash_token(req.token)

    if not req.token:
        result_success, error_codes, hostname, challenge_ts = False, ["missing-input-response"], None, None
    elif token_hash in _SEEN_TOKEN_HASHES:
        # Caught locally -- avoids leaking the (already-used) token further
        # and mirrors what the provider itself would report.
        result_success, error_codes, hostname, challenge_ts = False, ["token-already-used"], None, None
    else:
        outcome = _VERIFIERS[provider](req.token, req.remote_ip)
        result_success = outcome.success
        error_codes = outcome.error_codes
        hostname = outcome.hostname
        challenge_ts = outcome.challenge_ts
        if result_success:
            _SEEN_TOKEN_HASHES.add(token_hash)

    elapsed_ms = (time.perf_counter() - start) * 1000

    db.add(
        VerificationAttempt(
            provider=provider,
            success=result_success,
            error_codes=",".join(error_codes) if error_codes else None,
            hostname=hostname,
            token_hash=token_hash,
            processing_time_ms=elapsed_ms,
        )
    )
    db.commit()

    # NOTE: req.token / the secret key are never written to logs or returned
    # in this response -- only hostname/timestamp/error codes are exposed.
    return VerifyTokenResponse(
        provider=provider,
        success=result_success,
        error_codes=error_codes,
        hostname=hostname,
        challenge_ts=challenge_ts,
        processing_time_ms=round(elapsed_ms, 2),
    )
