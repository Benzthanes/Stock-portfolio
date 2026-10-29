"""
USD/THB exchange rate: one fallback constant and one live fetch shared by every module.
"""
from typing import Optional, Tuple
import logging
import time

logger = logging.getLogger(__name__)

FALLBACK_USDTHB = 33.62
FALLBACK_CACHE_TTL_SECONDS = 600  # 10 minutes cache TTL for failed network fetches

_cached_rate: Optional[float] = None
_cached_source: Optional[str] = None
_last_failure_time: float = 0.0


def fetch_usdthb(timeout: int = 10) -> Optional[float]:
    """Live USD/THB from TradingView FX_IDC, cached per process. Returns None when unavailable."""
    global _cached_rate, _cached_source, _last_failure_time
    if _cached_source == "live":
        return _cached_rate
    if _cached_source == "fallback":
        if time.time() - _last_failure_time < FALLBACK_CACHE_TTL_SECONDS:
            return None
        _cached_source = None
        _cached_rate = None

    rate = None
    try:
        from src.tradingview import _fetch_from_scanner
        rows = _fetch_from_scanner("forex", ["FX_IDC:USDTHB"], timeout=timeout)
        rate = float(rows[0]["close"]) if rows and rows[0].get("close") else None
    except Exception as exc:
        logger.warning("Failed to fetch live USD/THB exchange rate (%s). Falling back to %s.", exc, FALLBACK_USDTHB)
        rate = None

    if rate and 20.0 < rate < 60.0:
        _cached_rate = rate
        _cached_source = "live"
        return rate

    logger.warning("Live USD/THB rate unavailable (got %r). Using fallback rate %s.", rate, FALLBACK_USDTHB)
    _cached_rate = FALLBACK_USDTHB
    _cached_source = "fallback"
    _last_failure_time = time.time()
    return None


def resolve_usdthb_with_source(stored: Optional[float] = None) -> Tuple[float, str]:
    """
    Resolve USD/THB rate and source ('live', 'stored', or 'fallback').
    """
    live_rate = fetch_usdthb()
    if live_rate is not None:
        return live_rate, "live"
    if stored:
        return float(stored), "stored"
    return FALLBACK_USDTHB, "fallback"


def resolve_usdthb(stored: Optional[float] = None) -> float:
    """Live rate if reachable, else the stored rate, else the fallback constant."""
    rate, _ = resolve_usdthb_with_source(stored)
    return rate
