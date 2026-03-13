import hashlib
import re
from typing import Optional


def generate_hash(body_text: str) -> str:
    normalized = re.sub(r"\s+", " ", body_text).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def detect_status(current_hash: str, existing_hash: Optional[str]) -> str:
    if existing_hash is None:
        return "new"
    return "unchanged" if current_hash == existing_hash else "updated"
