# CaptchaLens

### CAPTCHA Recognition, OCR Solving & Provider Verification Platform

CaptchaLens is a local, test-focused platform for generating synthetic
CAPTCHAs, recognizing challenge types, evaluating OCR/CV solving, and
verifying tokens through official provider sandbox integrations.

Built by **Uzair Moazzam**.

> **Scope and safety:** CaptchaLens is designed for authorized development,
> testing, and benchmarking. It does not scrape third-party websites, bypass
> live anti-bot protections, harvest tokens, or automate unsolicited
> submissions.

---

## Highlights

- Synthetic CAPTCHA generation with known ground truth
- OpenCV + Tesseract OCR solving with confidence reporting
- Automatic fallback preprocessing for low-confidence OCR results
- Challenge recognition for reCAPTCHA, hCaptcha, Turnstile, and unsupported
  providers
- Official sandbox/test-key integrations for:
  - Google reCAPTCHA v2
  - hCaptcha
  - Cloudflare Turnstile
- Server-side token verification with safe error handling
- Missing, invalid, expired, and reused-token handling
- Batch processing and accuracy reporting
- SQLite-backed attempt and verification statistics
- Read-only dataset insights
- REST API with interactive Swagger documentation
- Playwright end-to-end automation for the local application
- Responsive frontend with animated transitions and a professional UI

## Technology Stack

| Area | Technology |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| Validation | Pydantic |
| Database | SQLite, SQLAlchemy |
| OCR/CV | OpenCV, Pillow, Tesseract |
| Frontend | HTML, CSS, vanilla JavaScript |
| Browser automation | Playwright |
| Testing | pytest |

## Project Structure

```text
captcha-solver-project/
├── automation/
│   └── playwright_demo.py       Local end-to-end browser demo
├── backend/
│   ├── app/
│   │   ├── assets/fonts/        Bundled CAPTCHA font
│   │   ├── providers/           Provider verification clients
│   │   ├── routes/              API route modules
│   │   ├── solver/              OCR and challenge recognition
│   │   ├── static/              Frontend files
│   │   ├── captcha_generator.py Synthetic CAPTCHA generation
│   │   ├── config.py            Environment configuration
│   │   ├── database.py          Database setup
│   │   ├── models.py            SQLAlchemy models
│   │   └── schemas.py           API schemas
│   ├── tests/                   Backend test suite
│   └── run.py                   Development server entry point
├── data/                        Reference data and runtime database
├── .env.example                 Configuration template
├── requirements.txt             Python dependencies
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.10 or newer
- Tesseract OCR
- Chromium browser binaries for the Playwright demo

Install Tesseract:

- **Windows:** Install Tesseract and set `TESSERACT_CMD` in `.env`.
- **Ubuntu/Debian:** `sudo apt-get install tesseract-ocr`
- **macOS:** `brew install tesseract`

### Installation

```bash
git clone <repository-url>
cd captcha-solver-project

python -m venv venv

# Windows PowerShell
venv\Scripts\Activate.ps1

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

On Windows, if Tesseract is not available on PATH, set this in `.env`:

```env
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

### Start the Application

From the `backend` directory:

```bash
python run.py
```

Open the application at:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

## Application Modules

### Custom Solver

Generates a controlled distorted-text CAPTCHA and sends it through the local
OpenCV/Tesseract pipeline. The UI displays the predicted text, confidence,
processing time, fallback usage, and success status.

### Provider Verification

Loads official provider test widgets and sends completed tokens to the local
backend for server-side verification. Provider scripts may be unavailable in
restricted networks; those failures are reported without blocking the rest of
the application.

### Batch & Accuracy

Generates and solves multiple synthetic CAPTCHAs, then reports total runs,
correct results, accuracy, average processing time, and individual outcomes.

### Reporting Dashboard

Displays solve attempts, verification attempts, success rates, processing
times, OCR confidence, estimated cost, and challenge-type distributions.

### Dataset Insights

Reads the supplied reference CSV locally and reports existing CAPTCHA labels.
It does not contact or submit data to any listed website.

## Browser Automation Demo

Install Playwright and its Chromium browser:

```bash
pip install playwright
playwright install chromium
```

With the backend already running, execute from the project root:

```bash
python automation/playwright_demo.py
```

To watch the browser:

```bash
python automation/playwright_demo.py --headed
```

The demo:

1. Opens the local application.
2. Generates and solves a synthetic CAPTCHA.
3. Attempts provider sandbox verification.
4. Reports unavailable third-party widgets without crashing.
5. Tests graceful missing-token handling.

## API Overview

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/generate` | Generate a synthetic CAPTCHA |
| `POST` | `/api/solve/{captcha_id}` | Solve a generated CAPTCHA |
| `POST` | `/api/recognize` | Recognize a challenge type |
| `POST` | `/api/verify` | Verify a provider token |
| `POST` | `/api/batch-run` | Run a synthetic batch |
| `GET` | `/api/site-keys` | Return public provider site keys |
| `GET` | `/api/stats` | Read reporting statistics |
| `POST` | `/api/stats/reset` | Reset reporting statistics |
| `GET` | `/api/dataset/captcha-distribution` | Read dataset insights |
| `GET` | `/health` | Check service health |

## Configuration

All settings are documented in `.env.example`. The application includes
public provider sandbox keys by default so the local demonstration can run
without secret credentials.

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLite or SQLAlchemy-compatible database URL |
| `RECAPTCHA_SITE_KEY` / `RECAPTCHA_SECRET_KEY` | reCAPTCHA test credentials |
| `HCAPTCHA_SITE_KEY` / `HCAPTCHA_SECRET_KEY` | hCaptcha test credentials |
| `TURNSTILE_SITE_KEY` / `TURNSTILE_SECRET_KEY` | Turnstile test credentials |
| `OCR_CONFIDENCE_THRESHOLD` | Threshold for fallback OCR processing |
| `TESSERACT_CMD` | Explicit Tesseract executable path |
| `APP_HOST` / `APP_PORT` | Server bind address and port |

Never commit real provider secret keys to source control.

## Testing

From the `backend` directory:

```bash
pytest tests/ -v
```

The test suite covers CAPTCHA generation, OCR solver behavior, provider
recognition, and graceful handling of invalid image input.

## Reliability and Security Notes

- Raw provider tokens are not returned in API responses or written to logs.
- Token hashes are used for local reuse detection.
- Missing tokens are rejected before contacting a provider.
- Provider timeouts and HTTP failures return structured responses.
- Invalid images produce structured solver errors.
- CAPTCHA and provider failures do not block unrelated application workflows.
- The custom OCR solver runs locally and does not call a third-party solving
  service.

## Cost Model

- Local synthetic OCR: no per-solve API charge.
- Provider sandbox verification: intended for development/testing.
- The dashboard's third-party cost value is a configurable reference estimate
  only; no third-party solving API is called.

## Limitations

The synthetic CAPTCHA generator intentionally provides a measurable OCR
challenge without attempting to defeat commercial anti-bot systems. Accuracy
varies with generated noise and distortion. Use the batch endpoint and
dashboard metrics for the current measured results rather than assuming a
fixed accuracy percentage.

## License

Add the license that matches your intended distribution and usage before
publishing this repository publicly.

## Author

**Uzair Moazzam**
