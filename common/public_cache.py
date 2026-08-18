"""Process-level TTL cache for public GET payloads.

Public pages already tolerate 60–300s ISR. A short in-memory TTL keeps Django
from re-running MongoEngine hydrates on every Googlebot / SSR hit without
changing response shape. Admin writes should call cache_delete_prefix().
"""

from __future__ import annotations

import threading
import time

from rest_framework.response import Response

_lock = threading.Lock()
_store = {}

DEFAULT_TTL_SECONDS = 45
MAX_ENTRIES = 2000


def cache_get(key):
    if not key:
        return None
    now = time.monotonic()
    with _lock:
        entry = _store.get(key)
        if not entry:
            return None
        expires_at, value = entry
        if expires_at <= now:
            _store.pop(key, None)
            return None
        return value


def cache_set(key, value, ttl=DEFAULT_TTL_SECONDS):
    if not key:
        return
    expires_at = time.monotonic() + max(1, int(ttl))
    with _lock:
        if len(_store) >= MAX_ENTRIES:
            stale = [
                existing_key
                for existing_key, (existing_expires, _ignored) in _store.items()
                if existing_expires <= time.monotonic()
            ]
            for existing_key in stale:
                _store.pop(existing_key, None)
            if len(_store) >= MAX_ENTRIES:
                oldest_key = min(_store, key=lambda item: _store[item][0])
                _store.pop(oldest_key, None)
        _store[key] = (expires_at, value)


def cache_delete_prefix(prefix):
    if not prefix:
        return
    with _lock:
        for key in [existing for existing in _store if existing.startswith(prefix)]:
            _store.pop(key, None)


def invalidate_public_http_paths(*path_prefixes):
    """Drop middleware-cached public GET bodies for the given URL prefixes."""
    for path_prefix in path_prefixes:
        if path_prefix:
            cache_delete_prefix(f"httpGET:{path_prefix}")


def public_json_response(payload, status=200, ttl=DEFAULT_TTL_SECONDS):
    response = Response(payload, status=status)
    if status == 200:
        response["Cache-Control"] = (
            f"public, max-age={int(ttl)}, stale-while-revalidate=300"
        )
    elif status == 404:
        response["Cache-Control"] = "public, max-age=10, stale-while-revalidate=30"
    return response
