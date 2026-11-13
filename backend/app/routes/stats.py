from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import SolveAttempt, VerificationAttempt
from app.schemas import StatsResponse

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    attempts = db.query(SolveAttempt).all()
    total = len(attempts)
    successful = sum(1 for a in attempts if a.success)
    failed = total - successful
    avg_time = sum(a.processing_time_ms for a in attempts) / total if total else 0.0
    confidences = [a.confidence for a in attempts if a.confidence is not None]
    avg_conf = sum(confidences) / len(confidences) if confidences else None
    total_cost = sum(a.estimated_cost_usd or 0.0 for a in attempts)

    by_type = defaultdict(lambda: {"total": 0, "success": 0})
    for a in attempts:
        by_type[a.challenge_type]["total"] += 1
        if a.success:
            by_type[a.challenge_type]["success"] += 1

    verifications = db.query(VerificationAttempt).all()
    v_total = len(verifications)
    v_success = sum(1 for v in verifications if v.success)

    return StatsResponse(
        total_attempts=total,
        successful=successful,
        failed=failed,
        success_rate=round(successful / total, 4) if total else 0.0,
        avg_processing_time_ms=round(avg_time, 2),
        avg_confidence=round(avg_conf, 2) if avg_conf is not None else None,
        total_estimated_cost_usd=round(total_cost, 4),
        by_challenge_type=dict(by_type),
        verification_attempts=v_total,
        verification_success_rate=round(v_success / v_total, 4) if v_total else 0.0,
    )


@router.post("/stats/reset")
def reset_stats(db: Session = Depends(get_db)):
    db.query(SolveAttempt).delete()
    db.query(VerificationAttempt).delete()
    db.commit()
    return {"status": "cleared"}
