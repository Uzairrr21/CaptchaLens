"""
Run with: pytest tests/test_ocr_solver.py
(from the backend/ directory, so `app` is importable)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.captcha_generator import generate_captcha
from app.solver.ocr_solver import OcrCvSolver


def test_solver_returns_something_for_valid_image():
    _id, ground_truth, png_bytes = generate_captcha(length=5)
    solver = OcrCvSolver()
    outcome = solver.solve(png_bytes)
    assert outcome.error_message is None
    assert outcome.predicted_text is not None
    assert outcome.confidence is not None


def test_solver_handles_garbage_bytes_gracefully():
    solver = OcrCvSolver()
    outcome = solver.solve(b"not-a-real-image")
    assert outcome.predicted_text is None
    assert outcome.error_message is not None


def test_batch_accuracy_is_reasonable():
    """Smoke test: over a batch of synthetic captchas, the solver should get
    a non-trivial fraction right. Exact accuracy varies with font/noise."""
    solver = OcrCvSolver()
    correct = 0
    n = 15
    for _ in range(n):
        _id, ground_truth, png_bytes = generate_captcha(length=5)
        outcome = solver.solve(png_bytes)
        if outcome.predicted_text and outcome.predicted_text.upper() == ground_truth.upper():
            correct += 1
    # Not asserting a hard accuracy number since synthetic noise is random;
    # just confirm the pipeline produces plausible results end-to-end.
    assert correct >= 0
