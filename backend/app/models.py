import datetime as dt

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text

from app.database import Base


class SolveAttempt(Base):
    """One attempt at recognizing + solving a CAPTCHA challenge."""

    __tablename__ = "solve_attempts"

    id = Column(Integer, primary_key=True, index=True)
    challenge_type = Column(String, index=True)       # synthetic_text | recaptcha | hcaptcha | turnstile | unsupported
    method = Column(String)                            # ocr_cv | provider_widget | n/a
    ground_truth = Column(String, nullable=True)
    predicted_text = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    success = Column(Boolean, default=False)
    fallback_used = Column(Boolean, default=False)
    processing_time_ms = Column(Float)
    estimated_cost_usd = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)


class VerificationAttempt(Base):
    """One server-side provider token verification call."""

    __tablename__ = "verification_attempts"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, index=True)   # recaptcha | hcaptcha | turnstile
    success = Column(Boolean, default=False)
    error_codes = Column(String, nullable=True)
    hostname = Column(String, nullable=True)
    token_hash = Column(String, index=True, nullable=True)
    processing_time_ms = Column(Float)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
