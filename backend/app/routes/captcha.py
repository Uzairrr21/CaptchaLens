import base64
import time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.captcha_generator import generate_captcha_base64, pop_ground_truth, generate_captcha
from app.config import THIRDPARTY_COST_PER_SOLVE_USD
from app.database import get_db
from app.models import SolveAttempt
from app.schemas import (
    GenerateCaptchaResponse,
    SolveResultResponse,
    RecognizeRequest,
    RecognizeResponse,
    BatchRunRequest,
)
from app.solver.ocr_solver import OcrCvSolver
from app.solver.recognizer import recognize_from_hint, recognize_from_html

router = APIRouter(prefix="/api", tags=["captcha"])
_solver = OcrCvSolver()


@router.post("/generate", response_model=GenerateCaptchaResponse)
def generate():
    captcha_id, b64 = generate_captcha_base64()
    return GenerateCaptchaResponse(captcha_id=captcha_id, image_base64=b64)


def _solve_and_log(db: Session, captcha_id: str, image_bytes: bytes, ground_truth: str | None) -> SolveResultResponse:
    start = time.perf_counter()
    outcome = _solver.solve(image_bytes)
    elapsed_ms = (time.perf_counter() - start) * 1000

    success = bool(
        outcome.predicted_text and ground_truth and outcome.predicted_text.upper() == ground_truth.upper()
    ) if ground_truth else bool(outcome.predicted_text)

    record = SolveAttempt(
        challenge_type="synthetic_text",
        method=_solver.name,
        ground_truth=ground_truth,
        predicted_text=outcome.predicted_text,
        confidence=outcome.confidence,
        success=success,
        fallback_used=outcome.fallback_used,
        processing_time_ms=elapsed_ms,
        estimated_cost_usd=0.0,  # local OCR engine: no per-call cost
        error_message=outcome.error_message,
    )
    db.add(record)
    db.commit()

    return SolveResultResponse(
        captcha_id=captcha_id,
        challenge_type="synthetic_text",
        method=_solver.name,
        predicted_text=outcome.predicted_text,
        confidence=outcome.confidence,
        success=success,
        fallback_used=outcome.fallback_used,
        processing_time_ms=round(elapsed_ms, 2),
        estimated_cost_usd=0.0,
        error_message=outcome.error_message,
    )


@router.post("/solve/{captcha_id}", response_model=SolveResultResponse)
def solve(captcha_id: str, image_base64: str, db: Session = Depends(get_db)):
    """Solve a previously generated synthetic captcha by id.

    image_base64 is the PNG the client was shown (round-tripped back so this
    endpoint is stateless w.r.t. image storage); ground truth is looked up
    server-side from the id so the client can never see/cheat the answer.
    """
    ground_truth = pop_ground_truth(captcha_id)
    image_bytes = base64.b64decode(image_base64)
    return _solve_and_log(db, captcha_id, image_bytes, ground_truth)


@router.post("/recognize", response_model=RecognizeResponse)
def recognize(req: RecognizeRequest):
    if req.html_snippet:
        result = recognize_from_html(req.html_snippet)
    else:
        result = recognize_from_hint(req.provider_hint)
    return RecognizeResponse(
        challenge_type=result.challenge_type, supported=result.supported, detail=result.detail
    )


@router.post("/batch-run")
def batch_run(req: BatchRunRequest, db: Session = Depends(get_db)):
    """Generates N fresh synthetic captchas and solves them immediately,
    for accuracy-statistics / bonus 'batch processing' requirement."""
    results = []
    for _ in range(max(1, min(req.count, 500))):
        captcha_id, ground_truth, png_bytes = generate_captcha()
        result = _solve_and_log(db, captcha_id, png_bytes, ground_truth)
        results.append(result)

    correct = sum(1 for r in results if r.success)
    return {
        "requested": req.count,
        "ran": len(results),
        "correct": correct,
        "accuracy": round(correct / len(results), 4) if results else 0.0,
        "avg_processing_time_ms": round(sum(r.processing_time_ms for r in results) / len(results), 2) if results else 0,
        "results": results,
    }
