"""
Entry point. Run from the backend/ directory:

    python run.py

or directly with uvicorn:

    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""
import uvicorn

from app.config import APP_HOST, APP_PORT

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=APP_HOST, port=APP_PORT, reload=True)
