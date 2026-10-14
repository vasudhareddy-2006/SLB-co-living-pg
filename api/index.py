import sys
import traceback
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from backend.main import app
except Exception as e:
    err_trace = traceback.format_exc()
    from fastapi import FastAPI
    from fastapi.responses import PlainTextResponse
    
    app = FastAPI()
    
    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS", "HEAD"])
    async def error_fallback(full_path: str):
        return PlainTextResponse(f"Vercel Python Startup Error:\n{err_trace}", status_code=500)
