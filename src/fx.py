"""
USD/THB exchange rate: one fallback constant and one live fetch shared by every module.
"""
from typing import Optional

FALLBACK_USDTHB = 33.62

_cached_rate: Optional[float] = None


def fetch_usdthb(timeout: int = 10) -> Optional[float]:
    """Live USD/THB from TradingView FX_IDC, cached per process. Returns None when unavailable."""
    global _cached_rate
    if _cached_rate is not None:
        return _cached_rate
    try:
        from src.tradingview import _fetch_from_scanner
        rows = _fetch_from_scanner("forex", ["FX_IDC:USDTHB"], timeout=timeout)
        rate = float(rows[0]["close"]) if rows and rows[0].get("close") else None
    except Exception:
        rate = None
    if rate and 20.0 < rate < 60.0:
        _cached_rate = rate
        return rate
    return None


def resolve_usdthb(stored: Optional[float] = None) -> float:
    """Live rate if reachable, else the stored rate, else the fallback constant."""
    return fetch_usdthb() or (float(stored) if stored else FALLBACK_USDTHB)
