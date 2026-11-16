import os
from dotenv import load_dotenv

load_dotenv()  # local development only; production uses real environment variables

DATABASE_URL = os.environ["DATABASE_URL"]
API_KEY = os.environ["API_KEY"]
JWT_SECRET = os.environ["JWT_SECRET"]
ALLOWED_ORIGINS = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()]