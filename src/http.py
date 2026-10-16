"""Shared HTTP client with timeout, retry, exponential backoff and jitter."""

import json
import random
import socket
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

RETRY_STATUS = {429, 500, 502, 503, 504}
DEFAULT_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

_sleep = time.sleep


class HttpError(Exception):
    def __init__(self, url: str, reason: str, status: Optional[int] = None):
        super().__init__(f"{url}: {reason}")
        self.url = url
        self.reason = reason
        self.status = status


def _retryable(exc: BaseException) -> bool:
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code in RETRY_STATUS
    return isinstance(exc, (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError))


def _request(req: urllib.request.Request, timeout: float, retries: int, backoff: float) -> bytes:
    attempt = 0
    while True:
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as exc:
            status = exc.code if isinstance(exc, urllib.error.HTTPError) else None
            if attempt >= retries or not _retryable(exc):
                raise HttpError(req.full_url, f"{type(exc).__name__}: {exc}", status) from exc
            _sleep(backoff * (2 ** attempt) + random.uniform(0, backoff))
            attempt += 1


def http_get(url: str, headers: Optional[Dict[str, str]] = None, timeout: float = 10,
             retries: int = 2, backoff: float = 0.5) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_UA, **(headers or {})})
    return _request(req, timeout, retries, backoff)


def http_post_json(url: str, payload: Any, headers: Optional[Dict[str, str]] = None, timeout: float = 10,
                   retries: int = 2, backoff: float = 0.5) -> Any:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"User-Agent": DEFAULT_UA, "Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    return json.loads(_request(req, timeout, retries, backoff).decode("utf-8"))
