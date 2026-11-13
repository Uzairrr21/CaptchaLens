"""
Custom CAPTCHA solving engine: OpenCV preprocessing + Tesseract OCR.

Two preprocessing pipelines are provided. The primary pipeline is fast and
works well on clean-ish synthetic captchas; if its confidence comes back
below OCR_CONFIDENCE_THRESHOLD, a heavier fallback pipeline (stronger
denoising + adaptive thresholding + morphological cleanup) is tried
automatically. This fallback-on-low-confidence behaviour satisfies the
"fallback handling if a primary method fails" bonus requirement.
"""
import re
import time

import cv2
import numpy as np
import pytesseract

from app.config import OCR_CONFIDENCE_THRESHOLD, TESSERACT_CMD
from app.solver.base import BaseSolver, SolveOutcome

if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

_TESS_CONFIG = (
    "--psm 7 -c tessedit_char_whitelist=ABCDEFGHJKMNPQRSTUVWXYZ23456789"
)


def _bytes_to_cv2(image_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def _preprocess_primary(img: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


def _preprocess_fallback(img: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    denoised = cv2.fastNlMeansDenoising(gray, h=15)
    blurred = cv2.medianBlur(denoised, 3)
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 35, 11
    )
    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    return cleaned


def _ocr_with_confidence(processed_img: np.ndarray) -> tuple[str, float]:
    data = pytesseract.image_to_data(
        processed_img, config=_TESS_CONFIG, output_type=pytesseract.Output.DICT
    )
    words, confs = [], []
    for text, conf in zip(data["text"], data["conf"]):
        text = text.strip()
        conf = float(conf)
        if text and conf >= 0:
            words.append(text)
            confs.append(conf)
    joined = re.sub(r"[^A-Za-z0-9]", "", "".join(words)).upper()
    avg_conf = sum(confs) / len(confs) if confs else 0.0
    return joined, avg_conf


class OcrCvSolver(BaseSolver):
    name = "ocr_cv"

    def solve(self, image_bytes: bytes) -> SolveOutcome:
        try:
            img = _bytes_to_cv2(image_bytes)
            if img is None:
                return SolveOutcome(None, None, False, "Could not decode image bytes")

            processed = _preprocess_primary(img)
            text, conf = _ocr_with_confidence(processed)
            fallback_used = False

            if not text or conf < OCR_CONFIDENCE_THRESHOLD:
                fallback_processed = _preprocess_fallback(img)
                fb_text, fb_conf = _ocr_with_confidence(fallback_processed)
                # Keep whichever result is stronger.
                if fb_text and fb_conf > conf:
                    text, conf = fb_text, fb_conf
                fallback_used = True

            if not text:
                return SolveOutcome(None, conf, fallback_used, "OCR produced no text")

            return SolveOutcome(text, round(conf, 2), fallback_used, None)
        except Exception as exc:  # defensive: never let a bad image crash the API
            return SolveOutcome(None, None, False, f"Solver error: {exc}")
