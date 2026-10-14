import sys
from pathlib import Path

# Add project root directory to sys.path for Vercel Serverless environment
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Import FastAPI instance from backend.main
from backend.main import app as fastapi_app

# Vercel's Python runtime requires a top-level un-indented assignment to 'app' or 'handler'
app = fastapi_app
