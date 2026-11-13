from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import init_db
from app.routes import captcha, verify, stats, dataset
from app.config import (
    RECAPTCHA_SITE_KEY,
    HCAPTCHA_SITE_KEY,
    TURNSTILE_SITE_KEY,
)

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


@app.get("/health")
def health():
    return {"status": "ok"}
