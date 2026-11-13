from typing import Optional
from pydantic import BaseModel


class GenerateCaptchaResponse(BaseModel):
    captcha_id: str
    image_base64: str
    challenge_type: str = "synthetic_text"


class SolveResultResponse(BaseModel):
    captcha_id: str
    challenge_type: str
    method: str
    predicted_text: Optional[str]
    confidence: Optional[float]
    success: bool
    fallback_used: bool
    processing_time_ms: float
    estimated_cost_usd: float
    error_message: Optional[str] = None


class RecognizeRequest(BaseModel):
    """Used by /api/recognize to classify a challenge from DOM/page hints."""
    html_snippet: Optional[str] = None
    provider_hint: Optional[str] = None


class RecognizeResponse(BaseModel):
    challenge_type: str
    supported: bool
    detail: str


class VerifyTokenRequest(BaseModel):
    provider: str   # recaptcha | hcaptcha | turnstile
    token: Optional[str] = None
    remote_ip: Optional[str] = None


class VerifyTokenResponse(BaseModel):
    provider: str
    success: bool
    error_codes: list[str] = []
    hostname: Optional[str] = None
    challenge_ts: Optional[str] = None
    processing_time_ms: float


class BatchRunRequest(BaseModel):
    count: int = 20


class StatsResponse(BaseModel):
    total_attempts: int
    successful: int
    failed: int
    success_rate: float
    avg_processing_time_ms: float
    avg_confidence: Optional[float]
    total_estimated_cost_usd: float
    by_challenge_type: dict
    verification_attempts: int
    verification_success_rate: float
