import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import requests


URL = "https://api.hyperliquid.xyz/info"
HEADERS = {"Content-Type": "application/json"}
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = BASE_DIR / "agent_outputs"


# --------------------
# Helpers
# --------------------

def _to_num(x: Any) -> float:
    try:
        return float(x)
    except Exception:
        return float("nan")


def _to_iso_utc(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")

def fetch_hl_raw(
    coin: str,
    interval: str,
    hours: int,
    limit: int,
    url: str = URL,
    out: Optional[str] = None,
    convert: bool = False,
    significant_swings: bool = False,
    fvg: bool = False,
) -> Tuple[int, Dict[str, Any]]:
    """Fetch raw candle data from Hyperliquid API.
    
    Args:
        coin: The coin symbol (e.g., "BTC").
        interval: The candle interval (e.g., "1m", "5m", "15m", "1h", "4h", "1d").
        hours: Lookback period in hours.
        limit: Maximum number of candles to fetch.
        url: The Hyperliquid API endpoint URL. This defaults to "https://api.hyperliquid.xyz/info".
        out: Optional file path to write output.
        convert: Whether to convert raw to human-usable candles.
        significant_swings: Whether to annotate output with significant swing highs/lows.
        fvg: Whether to annotate output with Fair Value Gaps and size.
    Returns:
        A tuple of (HTTP status code, metadata dict containing raw/final payload and optional output info).
    """
    now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    interval_mins = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440}.get(interval.lower(), 60)
    start_ms_from_hours = now_ms - int(hours) * 3_600_000
    start_ms_from_limit = now_ms - int(limit) * interval_mins * 60_000
    start_ms = min(start_ms_from_hours, start_ms_from_limit)

    payload = {
        "type": "candleSnapshot",
        "req": {
            "coin": coin,
            "interval": interval,
            "startTime": start_ms,
            "endTime": now_ms,
            "numCandles": int(limit),
        },
    }

    r = requests.post(url, json=payload, headers=HEADERS, timeout=15)
    status = r.status_code
    try:
        body = r.json()
    except Exception:
        body = r.text

    parsed_candles = parse_raw_keep_ohlc(body)
    converted: Optional[List[Dict[str, Any]]] = None
    annotated: Optional[List[Dict[str, Any]]] = None

    if convert and parsed_candles:
        converted = convert_to_human(parsed_candles)

    if (significant_swings or fvg) and parsed_candles:
        annotated = annotate_candles(parsed_candles, include_swings=significant_swings, include_fvg=fvg)

    final_payload: Union[str, Dict[str, Any], List[Any]] = annotated or converted or body

    saved_path: Optional[str] = None
    if out:
        output_path = Path(out)
        if not output_path.is_absolute():
            output_path = DEFAULT_OUTPUT_DIR / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(final_payload, (dict, list)):
            text_to_write = json.dumps(final_payload, indent=2)
        else:
            text_to_write = str(final_payload)
        output_path.write_text(text_to_write, encoding="utf-8")
        try:
            saved_path = str(output_path.relative_to(BASE_DIR))
        except ValueError:
            saved_path = str(output_path)

    return status, {
        "raw": body,
        "converted": converted,
        "annotated": annotated,
        "final": final_payload,
        "saved_to": saved_path,
    }


def _extract_iterable_from_raw(root: Union[Dict[str, Any], List[Any], str]) -> Optional[List[Any]]:
    body = root
    # Attempt to parse string into JSON if needed
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except Exception:
            return None

    if isinstance(body, dict):
        return body.get("candles") or body.get("data") or body.get("result") or body.get("rows")
    return body if isinstance(body, list) else None


def parse_raw_keep_ohlc(raw_root: Union[Dict[str, Any], List[Any], str]) -> List[Dict[str, Any]]:
    arr = _extract_iterable_from_raw(raw_root)
    if not isinstance(arr, list):
        return []
    out: List[Dict[str, Any]] = []
    for c in arr:
        try:
            if isinstance(c, dict) and "t" in c and all(k in c for k in ("o", "h", "l", "c")):
                out.append({"t": int(c["t"]), "o": c["o"], "h": c["h"], "l": c["l"], "c": c["c"], "v": c.get("v")})
            elif isinstance(c, (list, tuple)) and len(c) >= 6:
                out.append({"t": int(c[0]), "o": c[1], "h": c[2], "l": c[3], "c": c[4], "v": c[5]})
        except Exception:
            continue
    out.sort(key=lambda x: x["t"])  # oldest -> newest
    return out[-250:]


def convert_to_human(candles_raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for c in candles_raw:
        out.append({
            "timestamp": _to_iso_utc(c["t"]),
            "open": _to_num(c["o"]),
            "high": _to_num(c["h"]),
            "low": _to_num(c["l"]),
            "close": _to_num(c["c"]),
            "volume": _to_num(c.get("v", 0.0)),
        })
    return out


def compute_three_candle_swings_raw(candles: List[Dict[str, Any]]):
    sh: List[Dict[str, Any]] = []
    sl: List[Dict[str, Any]] = []
    for i in range(1, len(candles) - 1):
        h_prev, h, h_next = _to_num(candles[i - 1]["h"]), _to_num(candles[i]["h"]), _to_num(candles[i + 1]["h"])
        l_prev, l, l_next = _to_num(candles[i - 1]["l"]), _to_num(candles[i]["l"]), _to_num(candles[i + 1]["l"])
        if h > h_prev and h > h_next:
            sh.append({"i": i, "t": candles[i]["t"], "price": candles[i]["h"]})
        if l < l_prev and l < l_next:
            sl.append({"i": i, "t": candles[i]["t"], "price": candles[i]["l"]})
    return sh, sl


def compute_significant_swings_raw(swings: List[Dict[str, Any]], swing_type: str) -> List[Dict[str, Any]]:
    sig: List[Dict[str, Any]] = []
    for i in range(1, len(swings) - 1):
        left, mid, right = swings[i - 1], swings[i], swings[i + 1]
        lp = _to_num(left["price"]) ; mp = _to_num(mid["price"]) ; rp = _to_num(right["price"]) 
        if swing_type == "high":
            if mp > lp and mp > rp:
                sig.append(mid)
        else:
            if mp < lp and mp < rp:
                sig.append(mid)
    return sig


def detect_fvgs_raw(candles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    fvgs: List[Dict[str, Any]] = []
    for i in range(1, len(candles) - 1):
        prev_c, cur_c, next_c = candles[i - 1], candles[i], candles[i + 1]
        prev_high = _to_num(prev_c["h"]) ; next_low = _to_num(next_c["l"]) 
        prev_low  = _to_num(prev_c["l"]) ; next_high = _to_num(next_c["h"]) 
        # Bullish FVG
        if prev_high < next_low:
            fvgs.append({
                "i": i,
                "t": cur_c["t"],
                "type": "bullish",
                "top": next_c["l"],
                "bottom": prev_c["h"],
                "size": next_low - prev_high,
            })
        # Bearish FVG
        if prev_low > next_high:
            fvgs.append({
                "i": i,
                "t": cur_c["t"],
                "type": "bearish",
                "top": prev_c["l"],
                "bottom": next_c["h"],
                "size": prev_low - next_high,
            })
    return fvgs


def annotate_candles(candles_raw: List[Dict[str, Any]], include_swings: bool, include_fvg: bool) -> List[Dict[str, Any]]:
    annotations: Dict[int, Dict[str, Any]] = {i: {} for i in range(len(candles_raw))}

    if include_swings:
        swing_highs, swing_lows = compute_three_candle_swings_raw(candles_raw)
        sig_highs = set((s["i"] for s in compute_significant_swings_raw(swing_highs, "high")))
        sig_lows = set((s["i"] for s in compute_significant_swings_raw(swing_lows, "low")))
        for i in sig_highs:
            annotations[i]["significantSwingHigh"] = True
        for i in sig_lows:
            annotations[i]["significantSwingLow"] = True

    if include_fvg:
        for f in detect_fvgs_raw(candles_raw):
            i = f["i"]
            annotations[i]["fvg"] = {
                "type": f["type"],
                "top": f["top"],
                "bottom": f["bottom"],
                "size": f["size"],
            }

    out: List[Dict[str, Any]] = []
    for i, c in enumerate(candles_raw):
        entry = {
            "t": c["t"],
            "ts": _to_iso_utc(c["t"]),
            "o": c["o"],
            "h": c["h"],
            "l": c["l"],
            "c": c["c"],
        }
        if c.get("v") is not None:
            entry["v"] = c["v"]
        entry.update(annotations.get(i, {}))
        out.append(entry)
    return out


def main():
    p = argparse.ArgumentParser(description="Standalone HL fetcher with optional convert and per-candle annotations (significant swings, FVGs)")
    p.add_argument("--coin", default="BTC")
    p.add_argument("--interval", default="1h")
    p.add_argument("--hours", type=int, default=72)
    p.add_argument("--limit", type=int, default=250)
    p.add_argument("--url", default=URL)
    p.add_argument("--out", default=None, help="Optional file path to write output (annotated/converted/raw)")
    p.add_argument("--convert", action="store_true", help="Convert raw to human-usable candles and print")
    p.add_argument("--significant-swings", action="store_true", help="Annotate output with significant swing highs/lows")
    p.add_argument("--fvg", action="store_true", help="Annotate output with Fair Value Gaps and size")
    args = p.parse_args()

    status, result = fetch_hl_raw(
        coin=args.coin,
        interval=args.interval,
        hours=args.hours,
        limit=args.limit,
        url=args.url,
        out=args.out,
        convert=args.convert,
        significant_swings=args.significant_swings,
        fvg=args.fvg,
    )
    print(f"Status: {status}")

    raw_body = result.get("raw")
    final_body = result.get("final")
    converted = result.get("converted")
    annotated = result.get("annotated")
    saved_to = result.get("saved_to")

    def _pretty(val: Union[str, Dict[str, Any], List[Any]]) -> str:
        if isinstance(val, (dict, list)):
            return json.dumps(val, indent=2)
        return str(val)

    print("Raw response body:")
    print(_pretty(raw_body))

    if converted is not None:
        print("\nConverted candles (human-usable):")
        print(_pretty(converted))

    if annotated is not None:
        print("\nAnnotated candles:")
        print(_pretty(annotated))

    if saved_to:
        print(f"\nSaved output to {saved_to}")
    elif args.out:
        # If save failed, communicate path attempted
        print(f"\nWarning: Failed to persist output to {args.out}")


if __name__ == "__main__":
    main()
