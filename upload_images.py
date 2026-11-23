"""One-time: copies the website's existing pictures into Supabase Storage.

Usage (from this folder, with SUPABASE_SERVICE_KEY set in .env):
    python upload_images.py "../Cloud-Computing-Activity-3/images"

It uploads <images>/league/* and <images>/ranks/* with the same relative paths the database
already stores (league/zed.jpg, ranks/iron.png), so no database values change. Safe to run
again: existing files are replaced. At the end it checks that every image path stored in the
characters and ranks tables can be opened from its public URL.
"""
import mimetypes
import sys
import urllib.error
import urllib.request
from pathlib import Path

from sqlalchemy import text

import storage
from database import engine

FOLDERS = ["league", "ranks"]
TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}


def main(images_dir: Path) -> int:
    if not storage.is_configured():
        print("SUPABASE_SERVICE_KEY is not set. Add it to .env first.")
        return 1
    sent = failed = 0
    for folder in FOLDERS:
        for file in sorted((images_dir / folder).glob("*")):
            content_type = TYPES.get(file.suffix.lower())
            if not content_type:
                continue
            path = f"{folder}/{file.name}"
            try:
                storage.upload(path, file.read_bytes(), content_type)
                sent += 1
            except storage.StorageError as error:
                failed += 1
                print(f"FAILED {path}: {error}")
    print(f"Uploaded {sent} files, {failed} failed.")

    # Check every path the database refers to
    with engine.connect() as conn:
        paths = [r[0] for r in conn.execute(text(
            "select image from characters where image is not null "
            "union select image from ranks where image is not null"))]
    missing = []
    for path in paths:
        try:
            with urllib.request.urlopen(urllib.request.Request(storage.public_url(path), method="HEAD"), timeout=15):
                pass
        except urllib.error.URLError:
            missing.append(path)
    print(f"Checked {len(paths)} image paths in the database: {len(paths) - len(missing)} open from storage, {len(missing)} missing.")
    for path in missing:
        print("  missing:", path)
    return 1 if failed or missing else 0


if __name__ == "__main__":
    if len(sys.argv) != 2 or not Path(sys.argv[1]).is_dir():
        raise SystemExit(__doc__)
    raise SystemExit(main(Path(sys.argv[1])))
