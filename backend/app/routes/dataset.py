"""
Read-only analytics over the supplied reference CSV
(USA_Ecommerce_Platforms_200_Contact_Pages.csv).

IMPORTANT: this module only reads the labels already present in the CSV
(which Platform / which Captcha type each listed site reportedly uses). It
never visits, scrapes, or submits to any of the listed websites -- the
assignment's own scope section explicitly excludes contact-form automation
and bulk submissions against unrelated third-party sites, so this tool does
not do that. This endpoint exists purely to turn the CSV into a small
reference report (e.g. "how common is each CAPTCHA type across this
dataset"), which is useful context for the recognizer module above.
"""
import csv
from collections import Counter
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.config import DATA_DIR

router = APIRouter(prefix="/api", tags=["dataset"])

CSV_PATH = DATA_DIR / "USA_Ecommerce_Platforms_200_Contact_Pages.csv"


@router.get("/dataset/captcha-distribution")
def captcha_distribution():
    if not CSV_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Reference CSV not found at {CSV_PATH}. Copy it there to enable this report.",
        )

    captcha_counts = Counter()
    platform_counts = Counter()
    platform_by_captcha = Counter()
    total = 0

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            captcha = (row.get("Captcha") or "unknown").strip()
            platform = (row.get("Platform") or "unknown").strip()
            captcha_counts[captcha] += 1
            platform_counts[platform] += 1
            platform_by_captcha[(platform, captcha)] += 1

    return {
        "total_sites": total,
        "captcha_type_distribution": dict(captcha_counts),
        "platform_distribution": dict(platform_counts),
        "platform_by_captcha": {f"{p} / {c}": n for (p, c), n in platform_by_captcha.items()},
        "note": (
            "Derived purely from the labels already present in the reference CSV. "
            "No automated requests were made to any listed website."
        ),
    }
