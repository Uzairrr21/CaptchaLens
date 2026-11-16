from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from urllib.parse import urlparse

from app.database import init_db
from app.routes import captcha, verify, stats, dataset
from app.config import (
    RECAPTCHA_SITE_KEY,
    HCAPTCHA_SITE_KEY,
    TURNSTILE_SITE_KEY,
    AUTHORIZED_CONTACT_HOSTS,
)
from app.schemas import AutomationUrlRequest, ContactDemoRequest

app = FastAPI(
    title="CAPTCHA Solving & Verification Tool",
    description="Custom OCR solving engine + official provider test-key verification flow.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(captcha.router)
app.include_router(verify.router)
app.include_router(stats.router)
app.include_router(dataset.router)


@app.get("/api/site-keys")
def site_keys():
    """Public site keys only -- never secrets -- so the frontend can render
    the provider widgets without hardcoding them in two places."""
    return {
        "recaptcha_site_key": RECAPTCHA_SITE_KEY,
        "hcaptcha_site_key": HCAPTCHA_SITE_KEY,
        "turnstile_site_key": TURNSTILE_SITE_KEY,
    }


# Serve the simple frontend
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
def index():
    return FileResponse("app/static/index.html")


@app.get("/contact-demo")
def contact_demo():
    return FileResponse("app/static/contact_demo.html")


@app.post("/api/contact-demo")
def submit_contact_demo(req: ContactDemoRequest):
    """Accept the local automation fixture without sending email or storing data."""
    return {
        "status": "accepted",
        "message": f"Local demo message received for {req.name}.",
    }


@app.post("/api/automation/authorize-url")
def authorize_contact_url(req: AutomationUrlRequest):
    """Validate a contact URL against the configured authorization allowlist."""
    parsed = urlparse(req.url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"} or hostname not in AUTHORIZED_CONTACT_HOSTS:
        return {
            "allowed": False,
            "detail": "URL refused. Configure an owned host in AUTHORIZED_CONTACT_HOSTS.",
        }
    return {
        "allowed": True,
        "hostname": hostname,
        "detail": "URL is allowlisted. CAPTCHA completion remains manual.",
        "command": f"python automation\\safe_contact_flow.py --url {req.url} --manual-captcha",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
