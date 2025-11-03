# Guide to `tools/tool_fetch_hl_raw.py`

- Line 12: `HEADERS = {"Content-Type": "application/json"}` - Sets default HTTP headers; here only `Content-Type` is specified so the API knows the payload is JSON.
- Line 13: `BASE_DIR = Path(__file__).resolve().parent.parent` - Uses `__file__` (current file path) and `Path` helpers to locate the repository root two folders up from this script.
- Line 14: `DEFAULT_OUTPUT_DIR = BASE_DIR / "agent_outputs"` - Uses the `/` operator overloaded by `Path` to join `BASE_DIR` with the subdirectory `agent_outputs`.

- Line 21: `def _to_num(x: Any) -> float:` - Defines helper function `_to_num`; the annotation `-> float` states it returns a float.
- Line 22: `    try:` - Begins a `try` block to attempt risky operations; the indent (4 spaces) marks block scope.
- Line 23: `        return float(x)` - Converts input `x` to a float and returns it if successful.
- Line 24: `    except Exception:` - Catches any `Exception` from the `try` block.
- Line 25: `        return float("nan")` - Returns `nan` (not-a-number) if conversion fails, signalling missing data.

- Line 27: `def _to_iso_utc(ms: int) -> str:` - Defines `_to_iso_utc` function that expects an integer milliseconds value and returns a string.
- Line 28: `    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")` - Converts milliseconds to seconds, creates a timezone-aware datetime in UTC, formats it as ISO-8601 text, then replaces the `+00:00` suffix with `Z`.

- Line 30: `@tool` - Decorator syntax (`@name`) registers the next function as a LangChain tool, wrapping it in a LangChain `StructuredTool` so the agent can invoke it.
- Line 31: `def fetch_hl_raw(` - Begins definition of `fetch_hl_raw`, the agent-facing implementation that the decorator will wrap; the CLI-friendly twin lives in `tools/fetch_hl_raw.py`.
- Line 32: `    coin: str,` - First parameter annotated as `str`, representing the coin symbol.
- Line 33: `    interval: str,` - Parameter annotation indicates the candle interval must be a string.
- Line 34: `    hours: int,` - `hours` argument annotated as integer; describes lookback duration.
- Line 35: `    limit: int,` - `limit` argument annotated as integer; controls maximum candle count.
- Line 36: `    url: str = URL,` - Optional parameter defaulting to the module-level `URL` constant.
- Line 37: `    out: Optional[str] = None,` - Optional string target path (`Optional[str]` means either str or None) defaulting to None.
- Line 38: `    convert: bool = False,` - Boolean flag that defaults to `False`; toggles conversion to human-friendly format.
- Line 39: `    significant_swings: bool = False,` - Boolean flag controlling swing annotations.
- Line 40: `    fvg: bool = False,` - Boolean flag controlling Fair Value Gap annotations.
- Line 41: `) -> Tuple[int, Dict[str, Any]]:` - Closes parameter list and annotates return type as a tuple containing an integer status code and a dictionary of metadata.
- Line 42: `    """Fetch raw candle data from Hyperliquid API.` - Starts the function docstring; triple quotes define a multi-line string literal used for documentation.

- Line 44: `    Args:` - Docstring heading that introduces argument descriptions.
- Line 45: `        coin: The coin symbol (e.g., "BTC").` - Docstring line describing `coin`; indentation follows docstring convention.
- Line 46: `        interval: The candle interval (e.g., "1m", "5m", "15m", "1h", "4h", "1d").` - Docstring explaining valid interval examples.
- Line 47: `        hours: Lookback period in hours.` - Docstring explaining `hours`.
- Line 48: `        limit: Maximum number of candles to fetch.` - Docstring describing `limit`.
- Line 49: `        url: The Hyperliquid API endpoint URL. This defaults to "https://api.hyperliquid.xyz/info".` - Docstring mentioning `url` default and meaning.
- Line 50: `        out: Optional file path to write output.` - Docstring line detailing `out`.
- Line 51: `        convert: Whether to convert raw to human-usable candles.` - Docstring descriptive text for `convert`.
- Line 52: `        significant_swings: Whether to annotate output with significant swing highs/lows.` - Docstring describing `significant_swings`.
- Line 53: `        fvg: Whether to annotate output with Fair Value Gaps and size.` - Docstring line for `fvg`.
- Line 54: `    Returns:` - Docstring heading introducing return value description.
- Line 55: `        A tuple of (HTTP status code, metadata dict containing raw/final payload and optional output info).` - Docstring describing the tuple structure returned by the function.
- Line 56: `    """` - Closes the docstring triple-quoted string.
- Line 57: `    now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)` - Gets the current UTC time, converts to UNIX seconds, multiplies by 1000, and casts to int to yield milliseconds.
- Line 58: `    interval_mins = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440}.get(interval.lower(), 60)` - Defines a dict mapping interval strings to minutes and looks up the minutes for the requested interval (case-insensitive), defaulting to 60.
- Line 59: `    start_ms_from_hours = now_ms - int(hours) * 3_600_000` - Computes earliest timestamp allowed by the hours lookback; 3,600,000 is milliseconds per hour.
- Line 60: `    start_ms_from_limit = now_ms - int(limit) * interval_mins * 60_000` - Computes earliest timestamp that respects the maximum number of candles.
- Line 61: `    start_ms = min(start_ms_from_hours, start_ms_from_limit)` - Chooses the earlier timestamp of the two constraints so both limits are satisfied.

- Line 63: `    payload = {` - Starts definition of the JSON payload dictionary to send to the API.
- Line 64: `        "type": "candleSnapshot",` - Sets the API request type as `candleSnapshot`.
- Line 65: `        "req": {` - Opens nested `req` dictionary containing request parameters.
- Line 66: `            "coin": coin,` - Passes the `coin` argument through to the payload.
- Line 67: `            "interval": interval,` - Adds `interval` to the payload.
- Line 68: `            "startTime": start_ms,` - Adds calculated starting millisecond timestamp.
- Line 69: `            "endTime": now_ms,` - Specifies the current time as the end timestamp.
- Line 70: `            "numCandles": int(limit),` - Requests up to `limit` candles, converting to `int` to guard against strings.
- Line 71: `        },` - Closes the `req` dictionary entry.
- Line 72: `    }` - Closes the payload dictionary.

- Line 74: `    r = requests.post(url, json=payload, headers=HEADERS, timeout=15)` - Uses `requests.post` to send JSON to the API with headers and a 15-second timeout; result stored in `r`.
- Line 75: `    status = r.status_code` - Extracts the HTTP status code from the response object.
- Line 76: `    try:` - Begins a `try` block to parse response JSON safely.
- Line 77: `        body = r.json()` - Attempts to parse the response body as JSON.
- Line 78: `    except Exception:` - Catches any parsing exception.
- Line 79: `        body = r.text` - Falls back to the raw text of the response if JSON decoding fails.

- Line 81: `    parsed_candles = parse_raw_keep_ohlc(body)` - Calls helper to standardize raw candle data from the API response.
- Line 82: `    converted: Optional[List[Dict[str, Any]]] = None` - Declares `converted` variable with type hint and initializes it to `None`.
- Line 83: `    annotated: Optional[List[Dict[str, Any]]] = None` - Declares `annotated` variable similarly for potential annotations.

- Line 85: `    if convert and parsed_candles:` - Checks both that conversion was requested and that candle data exists.
- Line 86: `        converted = convert_to_human(parsed_candles)` - Converts raw candles to human-friendly format when the above condition is true.

- Line 88: `    if (significant_swings or fvg) and parsed_candles:` - Checks whether any annotation flags are set and data is present.
- Line 89: `        annotated = annotate_candles(parsed_candles, include_swings=significant_swings, include_fvg=fvg)` - Calls helper that returns annotated candles according to requested features.

- Line 91: `    final_payload: Union[str, Dict[str, Any], List[Any]] = annotated or converted or body` - Chooses annotated data if available, otherwise converted data, otherwise the raw body; type hint covers all possible shapes.

- Line 93: `    saved_path: Optional[str] = None` - Initializes `saved_path` to remember where output was written (or None).
- Line 94: `    if out:` - Checks whether a path argument was supplied.
- Line 95: `        output_path = Path(out)` - Wraps the supplied path in a `Path` object for filesystem operations.
- Line 96: `        if not output_path.is_absolute():` - Tests if the provided path is relative.
- Line 97: `            output_path = DEFAULT_OUTPUT_DIR / output_path` - If relative, resolve it under the default output directory.
- Line 98: `        output_path.parent.mkdir(parents=True, exist_ok=True)` - Ensures the parent directory exists by creating missing folders (`parents=True`) without error if already present.
- Line 99: `        if isinstance(final_payload, (dict, list)):` - Checks whether the final payload is JSON-like.
- Line 100: `            text_to_write = json.dumps(final_payload, indent=2)` - Converts dict/list into pretty-printed JSON text if true.
- Line 101: `        else:` - Handles non-dict/list payloads.
- Line 102: `            text_to_write = str(final_payload)` - Converts other payload types to a plain string.
- Line 103: `        output_path.write_text(text_to_write, encoding="utf-8")` - Writes the text out to the target file using UTF-8 encoding.
- Line 104: `        try:` - Begins block to compute a relative path.
- Line 105: `            saved_path = str(output_path.relative_to(BASE_DIR))` - Attempts to record the save location relative to repository base.
- Line 106: `        except ValueError:` - Catches `ValueError` if the output is outside `BASE_DIR`.
- Line 107: `            saved_path = str(output_path)` - Falls back to storing the absolute path string.

- Line 109: `    return status, {` - Starts the return statement that outputs the status code and a result dictionary.
- Line 110: `        "raw": body,` - Adds raw response to the dictionary.
- Line 111: `        "converted": converted,` - Includes converted candles or None.
- Line 112: `        "annotated": annotated,` - Includes annotations or None.
- Line 113: `        "final": final_payload,` - Adds the final payload selected earlier.
- Line 114: `        "saved_to": saved_path,` - Reports where output was saved (or None).
- Line 115: `    }` - Closes the dictionary.

- Line 118: `def _extract_iterable_from_raw(root: Union[Dict[str, Any], List[Any], str]) -> Optional[List[Any]]:` - Defines helper that normalizes possible response structures into a list.
- Line 119: `    body = root` - Assigns the input to a local variable `body` for manipulation.
- Line 120: `    # Attempt to parse string into JSON if needed` - Comment (starting with `#`) explaining the next block.
- Line 121: `    if isinstance(body, str):` - Checks whether `body` is a string.
- Line 122: `        try:` - Starts attempt to parse the string as JSON.
- Line 123: `            body = json.loads(body)` - Parses JSON text into Python objects.
- Line 124: `        except Exception:` - Catches failures (invalid JSON).
- Line 125: `            return None` - Signals inability to extract candle list by returning `None`.

- Line 127: `    if isinstance(body, dict):` - Checks if the body is a dictionary.
- Line 128: `        return body.get("candles") or body.get("data") or body.get("result") or body.get("rows")` - Tries multiple common keys that might hold the candle array and returns the first truthy value found.
- Line 129: `    return body if isinstance(body, list) else None` - If the body itself is already a list, return it; otherwise return `None`.

- Line 132: `def parse_raw_keep_ohlc(raw_root: Union[Dict[str, Any], List[Any], str]) -> List[Dict[str, Any]]:` - Defines helper that extracts candles while keeping OHLC fields.
- Line 133: `    arr = _extract_iterable_from_raw(raw_root)` - Calls the previous helper to obtain a list-like structure.
- Line 134: `    if not isinstance(arr, list):` - Guards against missing or malformed data.
- Line 135: `        return []` - Returns an empty list if no valid data.
- Line 136: `    out: List[Dict[str, Any]] = []` - Initializes an empty list to collect normalized candle dictionaries.
- Line 137: `    for c in arr:` - Begins loop over each element `c` in the array.
- Line 138: `        try:` - Starts block that can handle errors per element.
- Line 139: `            if isinstance(c, dict) and "t" in c and all(k in c for k in ("o", "h", "l", "c")):` - Checks dictionary-style candles with required keys.
- Line 140: `                out.append({"t": int(c["t"]), "o": c["o"], "h": c["h"], "l": c["l"], "c": c["c"], "v": c.get("v")})` - Normalizes dict candle to standard keys, ensuring timestamp is an int and volume may be missing.
- Line 141: `            elif isinstance(c, (list, tuple)) and len(c) >= 6:` - Handles list/tuple formatted candles with at least six items.
- Line 142: `                out.append({"t": int(c[0]), "o": c[1], "h": c[2], "l": c[3], "c": c[4], "v": c[5]})` - Builds normalized dict from list positions (assumes indices [0-5] map to t, o, h, l, c, v).
- Line 143: `        except Exception:` - Catches any conversion issues per candle entry.
- Line 144: `            continue` - Skips malformed entries and continues the loop.
- Line 145: `    out.sort(key=lambda x: x["t"])  # oldest -> newest` - Sorts the collected candles by timestamp ascending; inline comment explains order.
- Line 146: `    return out[-250:]` - Returns only the most recent 250 candles to cap output size.

- Line 149: `def convert_to_human(candles_raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:` - Defines helper that converts raw candles into user-friendly structure.
- Line 150: `    out: List[Dict[str, Any]] = []` - Initializes list for converted candles with type hint.
- Line 151: `    for c in candles_raw:` - Iterates through each standardized candle.
- Line 152: `        out.append({` - Starts construction of the output dictionary for each candle.
- Line 153: `            "timestamp": _to_iso_utc(c["t"]),` - Converts millisecond timestamp to ISO-8601 string using helper.
- Line 154: `            "open": _to_num(c["o"]),` - Converts the open price to float (or NaN).
- Line 155: `            "high": _to_num(c["h"]),` - Converts the high price to float.
- Line 156: `            "low": _to_num(c["l"]),` - Converts the low price to float.
- Line 157: `            "close": _to_num(c["c"]),` - Converts the close price to float.
- Line 158: `            "volume": _to_num(c.get("v", 0.0)),` - Converts volume to float, defaulting missing volume to 0.0.
- Line 159: `        })` - Closes the dictionary literal appended to the list.
- Line 160: `    return out` - Returns the list of converted candle dictionaries.

- Line 163: `def compute_three_candle_swings_raw(candles: List[Dict[str, Any]]):` - Declares helper to find local swing highs and lows; no return type specified but returns two lists.
- Line 164: `    sh: List[Dict[str, Any]] = []` - Initializes list to store swing highs with type hint.
- Line 165: `    sl: List[Dict[str, Any]] = []` - Initializes list to store swing lows.
- Line 166: `    for i in range(1, len(candles) - 1):` - Loops through index positions excluding the first and last to compare neighbors.
- Line 167: `        h_prev, h, h_next = _to_num(candles[i - 1]["h"]), _to_num(candles[i]["h"]), _to_num(candles[i + 1]["h"])` - Grabs and normalizes the surrounding high prices.
- Line 168: `        l_prev, l, l_next = _to_num(candles[i - 1]["l"]), _to_num(candles[i]["l"]), _to_num(candles[i + 1]["l"])` - Grabs and normalizes the surrounding low prices.
- Line 169: `        if h > h_prev and h > h_next:` - Checks if the middle candle high is higher than both neighbors.
- Line 170: `            sh.append({"i": i, "t": candles[i]["t"], "price": candles[i]["h"]})` - Records a swing high with index, timestamp, and original high price.
- Line 171: `        if l < l_prev and l < l_next:` - Checks if the middle candle low is lower than neighbors.
- Line 172: `            sl.append({"i": i, "t": candles[i]["t"], "price": candles[i]["l"]})` - Records swing low similarly.
- Line 173: `    return sh, sl` - Returns both lists as a tuple.

- Line 176: `def compute_significant_swings_raw(swings: List[Dict[str, Any]], swing_type: str) -> List[Dict[str, Any]]:` - Defines helper to filter swing highs or lows down to significant ones.
- Line 177: `    sig: List[Dict[str, Any]] = []` - Initializes list to hold significant swings.
- Line 178: `    for i in range(1, len(swings) - 1):` - Iterates through swings (skipping endpoints) to compare each with its neighbors.
- Line 179: `        left, mid, right = swings[i - 1], swings[i], swings[i + 1]` - Extracts the neighbor swing entries.
- Line 180: `        lp = _to_num(left["price"]) ; mp = _to_num(mid["price"]) ; rp = _to_num(right["price"]) ` - Uses semicolon `;` to place multiple statements on one line, converting each price to float.
- Line 181: `        if swing_type == "high":` - Checks whether we are processing highs.
- Line 182: `            if mp > lp and mp > rp:` - For highs, ensures the middle swing surpasses neighbors.
- Line 183: `                sig.append(mid)` - Records the middle swing as significant.
- Line 184: `        else:` - Handles the case when `swing_type` is anything other than `"high"` (intended for lows).
- Line 185: `            if mp < lp and mp < rp:` - For lows, requires the middle swing be lower than neighbors.
- Line 186: `                sig.append(mid)` - Adds the significant low.
- Line 187: `    return sig` - Returns the significant swings list.

- Line 190: `def detect_fvgs_raw(candles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:` - Declares helper detecting Fair Value Gaps (FVGs) from candle data.
- Line 191: `    fvgs: List[Dict[str, Any]] = []` - Initializes list to collect detected gaps.
- Line 192: `    for i in range(1, len(candles) - 1):` - Iterates over candles excluding first/last to compare neighbors.
- Line 193: `        prev_c, cur_c, next_c = candles[i - 1], candles[i], candles[i + 1]` - Captures previous, current, and next candles.
- Line 194: `        prev_high = _to_num(prev_c["h"]) ; next_low = _to_num(next_c["l"]) ` - Converts previous high and next low; semicolon separates statements.
- Line 195: `        prev_low  = _to_num(prev_c["l"]) ; next_high = _to_num(next_c["h"]) ` - Converts previous low and next high, again using semicolon for separate statements.
- Line 196: `        # Bullish FVG` - Comment labelling logic for bullish gaps.
- Line 197: `        if prev_high < next_low:` - Detects a gap where previous high is below next low.
- Line 198: `            fvgs.append({` - Starts dictionary describing the bullish gap.
- Line 199: `                "i": i,` - Saves the index of the current candle.
- Line 200: `                "t": cur_c["t"],` - Records timestamp of the current candle.
- Line 201: `                "type": "bullish",` - Labels this gap as bullish.
- Line 202: `                "top": next_c["l"],` - Uses next candle's low as the top boundary of the gap.
- Line 203: `                "bottom": prev_c["h"],` - Uses previous candle's high as the bottom boundary.
- Line 204: `                "size": next_low - prev_high,` - Stores the numeric size of the gap as difference between boundaries.
- Line 205: `            })` - Closes the dictionary entry appended to `fvgs`.
- Line 206: `        # Bearish FVG` - Comment introducing bearish gap logic.
- Line 207: `        if prev_low > next_high:` - Detects a bearish gap where previous low is above next high.
- Line 208: `            fvgs.append({` - Begins dictionary for bearish gap.
- Line 209: `                "i": i,` - Saves index.
- Line 210: `                "t": cur_c["t"],` - Saves timestamp.
- Line 211: `                "type": "bearish",` - Marks gap as bearish.
- Line 212: `                "top": prev_c["l"],` - For bearish, top boundary comes from previous low.
- Line 213: `                "bottom": next_c["h"],` - Bottom boundary from next high.
- Line 214: `                "size": prev_low - next_high,` - Calculates gap size for bearish case.
- Line 215: `            })` - Finishes dictionary appended to list.
- Line 216: `    return fvgs` - Returns the list of detected FVG dictionaries.

- Line 219: `def annotate_candles(candles_raw: List[Dict[str, Any]], include_swings: bool, include_fvg: bool) -> List[Dict[str, Any]]:` - Defines helper that adds optional annotations to candles.
- Line 220: `    annotations: Dict[int, Dict[str, Any]] = {i: {} for i in range(len(candles_raw))}` - Creates a dictionary comprehension mapping each candle index to an empty dict for annotations.
- Line 222: `    if include_swings:` - Checks whether swing annotations are requested.
- Line 223: `        swing_highs, swing_lows = compute_three_candle_swings_raw(candles_raw)` - Calls helper to compute raw swing highs and lows.
- Line 224: `        sig_highs = set((s["i"] for s in compute_significant_swings_raw(swing_highs, "high")))` - Uses generator expression to gather indices of significant swing highs into a set.
- Line 225: `        sig_lows = set((s["i"] for s in compute_significant_swings_raw(swing_lows, "low")))` - Similarly collects indices for significant swing lows.
- Line 226: `        for i in sig_highs:` - Loops over significant high indices.
- Line 227: `            annotations[i]["significantSwingHigh"] = True` - Marks each relevant candle with a boolean flag.
- Line 228: `        for i in sig_lows:` - Loops over significant low indices.
- Line 229: `            annotations[i]["significantSwingLow"] = True` - Marks each relevant candle with swing low flag.
- Line 231: `    if include_fvg:` - Checks whether FVG annotations are requested.
- Line 232: `        for f in detect_fvgs_raw(candles_raw):` - Iterates through detected gaps.
- Line 233: `            i = f["i"]` - Extracts the candle index for this gap.
- Line 234: `            annotations[i]["fvg"] = {` - Creates/updates annotation entry for that candle with FVG details.
- Line 235: `                "type": f["type"],` - Stores FVG type (bullish/bearish).
- Line 236: `                "top": f["top"],` - Stores top boundary.
- Line 237: `                "bottom": f["bottom"],` - Stores bottom boundary.
- Line 238: `                "size": f["size"],` - Stores gap size.
- Line 239: `            }` - Closes FVG annotation dictionary.
- Line 241: `    out: List[Dict[str, Any]] = []` - Initializes list to hold merged candle plus annotations.
- Line 242: `    for i, c in enumerate(candles_raw):` - Loops with index and candle data.
- Line 243: `        entry = {` - Starts dictionary for the combined result.
- Line 244: `            "t": c["t"],` - Copies raw timestamp.
- Line 245: `            "ts": _to_iso_utc(c["t"]),` - Adds human-readable timestamp string.
- Line 246: `            "o": c["o"],` - Copies open price as-is.
- Line 247: `            "h": c["h"],` - Copies high price.
- Line 248: `            "l": c["l"],` - Copies low price.
- Line 249: `            "c": c["c"],` - Copies close price.
- Line 250: `        }` - Closes base entry dictionary.
- Line 251: `        if c.get("v") is not None:` - Checks whether volume data exists (allowing zero).
- Line 252: `            entry["v"] = c["v"]` - If present, copies volume into entry.
- Line 253: `        entry.update(annotations.get(i, {}))` - Merges any computed annotations onto the entry.
- Line 254: `        out.append(entry)` - Adds the completed entry to the output list.
- Line 255: `    return out` - Returns the list of annotated candle dictionaries.

- Line 258: `def main():` - Defines `main`, enabling the script to run standalone.
- Line 259: `    p = argparse.ArgumentParser(description="Standalone HL fetcher with optional convert and per-candle annotations (significant swings, FVGs)")` - Creates an `ArgumentParser` for command-line usage, but this module’s decorated `fetch_hl_raw` should be reserved for the agent; the runnable CLI lives in `tools/fetch_hl_raw.py`.
- Line 260: `    p.add_argument("--coin", default="BTC")` - Adds `--coin` CLI option with default "BTC".
- Line 261: `    p.add_argument("--interval", default="1h")` - Adds `--interval` option defaulting to "1h".
- Line 262: `    p.add_argument("--hours", type=int, default=72)` - Adds `--hours` argument, casting input to `int`, default 72.
- Line 263: `    p.add_argument("--limit", type=int, default=250)` - Adds `--limit` argument with integer type and default 250.
- Line 264: `    p.add_argument("--url", default=URL)` - Adds `--url` argument defaulting to the module constant.
- Line 265: `    p.add_argument("--out", default=None, help="Optional file path to write output (annotated/converted/raw)")` - Adds `--out` option with help text; default `None`.
- Line 266: `    p.add_argument("--convert", action="store_true", help="Convert raw to human-usable candles and print")` - Adds boolean flag `--convert`; `action="store_true"` turns it into a simple on/off switch.
- Line 267: `    p.add_argument("--significant-swings", action="store_true", help="Annotate output with significant swing highs/lows")` - Adds flag for swing annotations.
- Line 268: `    p.add_argument("--fvg", action="store_true", help="Annotate output with Fair Value Gaps and size")` - Adds flag for FVG annotations.
- Line 269: `    args = p.parse_args()` - Parses the command-line arguments into the `args` namespace.

- Line 271: `    status, result = fetch_hl_raw(` - Calls `fetch_hl_raw`, unpacking the tuple into `status` and `result`.
- Line 272: `        coin=args.coin,` - Passes parsed `coin` argument using keyword syntax.
- Line 273: `        interval=args.interval,` - Passes interval.
- Line 274: `        hours=args.hours,` - Passes hours.
- Line 275: `        limit=args.limit,` - Passes limit.
- Line 276: `        url=args.url,` - Passes URL.
- Line 277: `        out=args.out,` - Passes output path.
- Line 278: `        convert=args.convert,` - Passes convert flag.
- Line 279: `        significant_swings=args.significant_swings,` - Passes swing flag.
- Line 280: `        fvg=args.fvg,` - Passes FVG flag.
- Line 281: `    )` - Closes argument list and call.
- Line 282: `    print(f"Status: {status}")` - Prints HTTP status using an f-string (formatted string literal).

- Line 284: `    raw_body = result.get("raw")` - Retrieves raw response from result dictionary using `dict.get`.
- Line 285: `    final_body = result.get("final")` - Retrieves final payload (even though not printed later).
- Line 286: `    converted = result.get("converted")` - Retrieves converted data if present.
- Line 287: `    annotated = result.get("annotated")` - Retrieves annotated data if present.
- Line 288: `    saved_to = result.get("saved_to")` - Retrieves save path string if output written.

- Line 290: `    def _pretty(val: Union[str, Dict[str, Any], List[Any]]) -> str:` - Nested helper to format dictionaries/lists nicely; type hints describe accepted types and return.
- Line 291: `        if isinstance(val, (dict, list)):` - Checks if value is dict or list.
- Line 292: `            return json.dumps(val, indent=2)` - Converts dict/list to pretty JSON string.
- Line 293: `        return str(val)` - Otherwise casts value to string.

- Line 295: `    print("Raw response body:")` - Prints header text.
- Line 296: `    print(_pretty(raw_body))` - Prints formatted raw response via `_pretty`.

- Line 298: `    if converted is not None:` - Checks whether converted data exists.
- Line 299: `        print("\nConverted candles (human-usable):")` - Prints section header with leading newline for spacing.
- Line 300: `        print(_pretty(converted))` - Prints formatted converted data.

- Line 302: `    if annotated is not None:` - Checks for annotation data.
- Line 303: `        print("\nAnnotated candles:")` - Prints header with newline.
- Line 304: `        print(_pretty(annotated))` - Prints formatted annotated data.

- Line 306: `    if saved_to:` - Checks if data was successfully saved.
- Line 307: `        print(f"\nSaved output to {saved_to}")` - Prints message including relative path.
- Line 308: `    elif args.out:` - Secondary branch for when save failed but output was requested.
- Line 309: `        # If save failed, communicate path attempted` - Comment explaining the warning case.
- Line 310: `        print(f"\nWarning: Failed to persist output to {args.out}")` - Warns user of failed file write.

- Line 313: `if __name__ == "__main__":` - Standard module guard; runs following block only when executed directly. In practice, prefer `tools/fetch_hl_raw.py` for CLI runs because the `@tool` decorator replaces `fetch_hl_raw` with a `StructuredTool`.
- Line 314: `    main()` - Calls `main()` when the module guard condition is true; with the decorator in place this path is effectively vestigial and should not be used for manual data pulls.
