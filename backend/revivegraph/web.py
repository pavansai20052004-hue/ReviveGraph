"""Optional same-origin web host; the existing local API factory is unchanged."""
from pathlib import Path

from fastapi.staticfiles import StaticFiles

from .main import ROOT, create_app


def create_web_app(db_path=None, static_dir=None):
    directory = Path(static_dir) if static_dir is not None else ROOT / "frontend" / "dist"
    if not (directory / "index.html").is_file():
        raise RuntimeError("Build the frontend first: npm --prefix frontend run build")
    app = create_app(db_path)
    # API routes are registered first. Hash-based navigation needs no API fallback.
    app.mount("/", StaticFiles(directory=str(directory), html=True), name="frontend")
    return app
