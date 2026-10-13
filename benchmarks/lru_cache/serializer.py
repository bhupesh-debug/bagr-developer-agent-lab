"""Key serialization and normalization for LRU Cache."""
import hashlib
import json
from typing import Any


def serialize_key(key: Any) -> str:
    """Normalizes arbitrary keys into unique string keys."""
    if isinstance(key, str):
        return key
    if isinstance(key, (int, float, bool)):
        return str(key)
    try:
        encoded = json.dumps(key, sort_keys=True)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]
    except Exception:
        return str(hash(key))
