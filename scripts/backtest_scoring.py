#!/usr/bin/env python3
"""
Walk-forward backtest of the technical indicator states used by src/scoring.py.

For every ticker in the US Top 100 universe (plus the portfolio), it samples one
bar every STEP bars, computes each indicator using only candles up to that bar,
and records the forward return. Each indicator state is then compared with the
baseline (every sample) to decide whether it earns points.

Usage:
    python3 scripts/backtest_scoring.py            # uses data/.backtest_candles.json when fresh
    python3 scripts/backtest_scoring.py --refresh  # re-downloads candles
Writes data/backtest_scoring.json.
"""

import argparse
import json
import math
import statistics as st
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import chart_data as cd
from src.http import http_get
from src.universe import get_universe

CANDLES_PATH = ROOT / "data" / ".backtest_candles.json"
RESULT_PATH = ROOT / "data" / "backtest_scoring.json"
CANDLES_TTL_SECONDS = 7 * 86400
WINDOW = 450
STEP = 5
HORIZONS = (20, 60)
LOOKBACK_BARS = 900
MIN_T = 2.0


def fetch_candles(ticker: str) -> List[Dict[str, Any]]:
    symbol = ticker.replace(".", "-").upper()
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=6y&interval=1d"
    res = json.loads(http_get(url, timeout=15).decode("utf-8")).get("chart", {}).get("result") or []
    if not res:
        return []
    quote = res[0].get("indicators", {}).get("quote", [{}])[0]
    out = []
    for i, ts in enumerate(res[0].get("timestamp", [])):
        row = [quote.get(k, [None] * (i + 1))[i] for k in ("open", "high", "low", "close")]
        if None in row:
            continue
        vol = (quote.get("volume") or [0] * (i + 1))[i] or 0
        out.append({"time": time.strftime("%Y-%m-%d", time.gmtime(ts)), "open": row[0], "high": row[1],
                    "low": row[2], "close": row[3], "volume": int(vol)})
    return out


def load_candles(tickers: List[str], refresh: bool) -> Dict[str, List[Dict[str, Any]]]:
    """Cache entries are {"fetched_at", "candles"} per ticker. Failed or empty fetches are never cached."""
    cache: Dict[str, Any] = {}
    if CANDLES_PATH.exists() and not refresh:
        cache = {t: e for t, e in json.loads(CANDLES_PATH.read_text()).items()
                 if isinstance(e, dict) and e.get("candles") and time.time() - e.get("fetched_at", 0) <= CANDLES_TTL_SECONDS}
    missing = [t for t in tickers if t not in cache]
    for i, t in enumerate(missing, 1):
        try:
            candles = fetch_candles(t)
        except Exception as exc:
            print(f"  skip {t}: {exc}", file=sys.stderr)
            continue
        if candles:
            cache[t] = {"fetched_at": time.time(), "candles": candles}
        print(f"  fetched {i}/{len(missing)} {t} ({len(candles)} bars)", file=sys.stderr)
    if missing:
        CANDLES_PATH.write_text(json.dumps(cache))
    return {t: cache[t]["candles"] if t in cache else [] for t in tickers}


def ema_last(values: List[float], period: int) -> float:
    k = 2.0 / (period + 1)
    e = values[0]
    for v in values[1:]:
        e = v * k + e * (1 - k)
    return e


def rsi_series(closes: List[float], period: int = 14) -> List[float]:
    out = [50.0] * len(closes)
    gains = [max(0.0, closes[i] - closes[i - 1]) for i in range(1, len(closes))]
    losses = [max(0.0, closes[i - 1] - closes[i]) for i in range(1, len(closes))]
    if len(gains) < period:
        return out
    ag, al = sum(gains[:period]) / period, sum(losses[:period]) / period
    for i in range(period, len(gains)):
        ag = (ag * (period - 1) + gains[i]) / period
        al = (al * (period - 1) + losses[i]) / period
        out[i + 1] = 100.0 - 100.0 / (1 + ag / al) if al else 100.0
    return out


def band(value: float, edges: List[float], labels: List[str]) -> str:
    for edge, label in zip(edges, labels):
        if value < edge:
            return label
    return labels[-1]


def sample_states(window: List[Dict[str, Any]]) -> Dict[str, str]:
    closes = [c["close"] for c in window]
    close = closes[-1]
    dist = (close - ema_last(closes, 200)) / ema_last(closes, 200) * 100.0
    rsi = rsi_series(closes)
    vfi = cd.compute_volume_flow_indicator(window)
    wae = cd.compute_waddah_attar_explosion(window)
    sq = cd.compute_squeeze_momentum(window)
    ut = cd.compute_ut_bot_alerts(window)
    ce = cd.compute_chandelier_exit(window)
    wt = cd.compute_wavetrend_oscillator(window)
    smc = cd.compute_smart_money_concepts(window)
    lz = cd.compute_lorentzian_classification(window)
    dip = -3.0 <= dist <= 8.0 and min(rsi[-5:]) < 40.0
    knife_vfi = vfi["status"] == "DISTRIBUTION"
    knife_ce = close < (ce.get("long_stop") or 0)
    states = {
        "ema200_dist": band(dist, [-10, -3, 0, 5, 10], ["<-10%", "-10..-3%", "-3..0%", "0..5%", "5..10%", ">10%"]),
        "rsi": band(rsi[-1], [30, 40, 60, 70], ["<30", "30-40", "40-60", "60-70", ">70"]),
        "rsi_hook": str(rsi[-1] > rsi[-2] and min(rsi[-3:]) < 40.0),
        "vfi": vfi["status"],
        "wae": wae["status"],
        "squeeze": f"{sq['status']}:{sq['direction']}",
        "ut_bot": ut["position"],
        "chandelier": ce["direction"],
        "wavetrend": "BULL_CROSS_OVERSOLD" if wt["bullish_cross"] and wt["wt1"] < -50 else wt["direction"],
        "smc_structure": smc["market_structure"].split(" (")[0],
        "lorentzian": lz["direction"],
        "dip": str(dip),
    }
    if dip:
        states["dip_knife_vfi"] = str(knife_vfi)
        states["dip_knife_chandelier"] = str(knife_ce)
        states["dip_knife_any"] = str(knife_vfi or knife_ce)
    return states


def collect(candles: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    rows = []
    horizon = max(HORIZONS)
    for n, (ticker, c) in enumerate(candles.items(), 1):
        if len(c) < WINDOW + horizon + 50:
            continue
        start = max(WINDOW, len(c) - LOOKBACK_BARS - horizon)
        for i in range(start, len(c) - horizon, STEP):
            close = c[i]["close"]
            row = {"ticker": ticker, "time": c[i]["time"], "states": sample_states(c[i - WINDOW:i + 1])}
            for h in HORIZONS:
                row[f"fwd{h}"] = (c[i + h]["close"] / close - 1) * 100.0
            row["mdd60"] = (min(x["low"] for x in c[i + 1:i + 61]) / close - 1) * 100.0
            rows.append(row)
        print(f"  scored {n}/{len(candles)} {ticker}", file=sys.stderr)
    return rows


def compare(rows: List[Dict[str, Any]], key: str, metric: str, horizon: int) -> Dict[str, Any]:
    """Mean of `metric` for one state against the rest of the same population, with an overlap-adjusted t."""
    by_state = defaultdict(list)
    for r in rows:
        if key in r["states"]:
            by_state[r["states"][key]].append(r)
    population = [r[metric] for r in rows if key in r["states"]]
    if len(population) < 30:
        return {}
    base_mean = st.mean(population)
    overlap = max(1.0, horizon / STEP)
    mid = sorted(r["time"] for r in rows)[len(rows) // 2]
    out = {}
    for state, rs in sorted(by_state.items()):
        vals = [r[metric] for r in rs]
        rest = [r[metric] for r in rows if key in r["states"] and r["states"][key] != state]
        if len(vals) < 20 or len(rest) < 20:
            continue
        diff = st.mean(vals) - st.mean(rest)
        se = math.sqrt(st.pvariance(vals) / max(1.0, len(vals) / overlap) + st.pvariance(rest) / max(1.0, len(rest) / overlap))
        halves = []
        for side in (lambda r: r["time"] < mid, lambda r: r["time"] >= mid):
            a = [r[metric] for r in rs if side(r)]
            b = [r[metric] for r in rows if key in r["states"] and r["states"][key] != state and side(r)]
            halves.append(st.mean(a) - st.mean(b) if a and b else 0.0)
        t = diff / se if se else 0.0
        stable = halves[0] * halves[1] > 0
        out[state] = {
            "n": len(vals), "mean": round(st.mean(vals), 2), "median": round(st.median(vals), 2),
            "win_pct": round(sum(v > 0 for v in vals) / len(vals) * 100, 1),
            "diff_vs_rest": round(diff, 2), "t": round(t, 2),
            "half_diffs": [round(h, 2) for h in halves],
            "verdict": ("edge+" if t >= MIN_T else "edge-" if t <= -MIN_T else "none") if stable else "unstable",
        }
    return {"baseline_mean": round(base_mean, 2), "states": out}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--refresh", action="store_true", help="re-download candles")
    parser.add_argument("--limit", type=int, default=0, help="only the first N tickers (debug)")
    args = parser.parse_args()

    tickers = sorted(set(get_universe("all")) | {h["ticker"] for h in json.loads((ROOT / "data" / "portfolio.json").read_text())["holdings"]})
    tickers = [t for t in tickers if t not in ("VOO",)][: args.limit or None]
    t0 = time.time()
    rows = collect(load_candles(tickers, args.refresh))
    keys = sorted({k for r in rows for k in r["states"]})
    result = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M"),
        "config": {"window": WINDOW, "step": STEP, "lookback_bars": LOOKBACK_BARS, "min_t": MIN_T,
                   "tickers": len({r["ticker"] for r in rows}), "samples": len(rows)},
        "fwd60": {k: compare(rows, k, "fwd60", 60) for k in keys},
        "fwd20": {k: compare(rows, k, "fwd20", 20) for k in keys},
        "mdd60": {k: compare(rows, k, "mdd60", 60) for k in keys},
    }
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=1))
    print(f"{len(rows)} samples, {result['config']['tickers']} tickers, {time.time() - t0:.0f}s -> {RESULT_PATH}")
    for metric in ("fwd60", "mdd60"):
        print(f"\n== {metric} (state mean vs rest, t adjusted for overlap)")
        for k in keys:
            for state, s in result[metric][k].get("states", {}).items():
                if s["verdict"].startswith("edge"):
                    print(f"  {k:22} {state:28} n={s['n']:5} mean={s['mean']:6.2f} diff={s['diff_vs_rest']:+6.2f} t={s['t']:+5.2f} {s['verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
