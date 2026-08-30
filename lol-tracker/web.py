from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

STATIC_DIR = Path(__file__).resolve().parent / "static"

router = APIRouter()


@router.get("/widget", include_in_schema=False)
def widget() -> FileResponse:
    return FileResponse(STATIC_DIR / "widget.html", media_type="text/html")
