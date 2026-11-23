"""Uploads pictures to Supabase Storage with the standard library, so no extra package is needed.

The bucket is public: the website shows pictures straight from its public URL, and only this
API (holding the secret key) can add or replace files.
"""
import json
import re
import urllib.error
import urllib.request
from typing import Optional

from config import IMAGE_BUCKET, SUPABASE_SERVICE_KEY, SUPABASE_URL

MAX_BYTES = 4 * 1024 * 1024   # Vercel itself refuses request bodies above about 4.5 MB
EXTENSIONS = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


class StorageError(Exception):
    pass


def is_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_SERVICE_KEY)


def sniff_type(data: bytes) -> Optional[str]:
    """The real type of the file from its first bytes, not from what the browser claims."""
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def public_url(path: str) -> str:
    return f"{SUPABASE_URL}/storage/v1/object/public/{IMAGE_BUCKET}/{path}"


def upload(path: str, data: bytes, content_type: str) -> None:
    """Stores the file at `path` inside the bucket, replacing any file already there."""
    if not is_configured():
        raise StorageError("Image storage is not set up on the server.")
    request = urllib.request.Request(
        f"{SUPABASE_URL}/storage/v1/object/{IMAGE_BUCKET}/{path}",
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "apikey": SUPABASE_SERVICE_KEY,
            "Content-Type": content_type,
            "x-upsert": "true",
            "Cache-Control": "max-age=3600",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            response.read()
    except urllib.error.HTTPError as error:
        # Keep the reason, never the key or the request headers
        try:
            reason = json.loads(error.read().decode("utf-8", "replace")).get("message", "")
        except Exception:
            reason = ""
        raise StorageError(f"Storage refused the upload ({error.code}). {reason}".strip())
    except (urllib.error.URLError, TimeoutError):
        raise StorageError("Couldn't reach image storage.")
