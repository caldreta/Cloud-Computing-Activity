import os
from dotenv import load_dotenv

load_dotenv()  # local development only; production uses real environment variables

DATABASE_URL = os.environ["DATABASE_URL"]
API_KEY = os.environ["API_KEY"]
JWT_SECRET = os.environ["JWT_SECRET"]
ALLOWED_ORIGINS = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()]

# ---------- Image storage (Supabase Storage) ----------
# Optional, so the API still starts before they are set. Uploads answer 503 until then.
# SUPABASE_URL is worked out from DATABASE_URL (postgres.<project ref>:...) when it is not set.
import re as _re

_ref = _re.search(r"postgres\.([a-z0-9]+):", DATABASE_URL)
SUPABASE_URL = (os.environ.get("SUPABASE_URL") or (f"https://{_ref.group(1)}.supabase.co" if _ref else "")).rstrip("/")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")   # secret: only the API may hold it
IMAGE_BUCKET = "champion-images"
