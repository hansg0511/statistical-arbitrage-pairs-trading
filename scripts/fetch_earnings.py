#!/usr/bin/env python3
"""
Fetch earnings dates for the full S&P 500 universe (503 tickers) back to ~2013.

Merges previously fetched data from the stat-arb project to avoid re-downloading.
Output: Output/earnings_dates.json
  {ticker: [{period_text, pub_trading_day_str, pub_type, fiscal_year, financial_type}]}
"""
import json
import os
import sys
import time
import socket

from moomoo import OpenQuoteContext, RET_OK

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "src")))
from constants import TICKERS

PUB_TYPE_MAP = {0: "Unknown", 1: "Pre-Market", 2: "After-Market", 3: "During-Market"}
BATCH_SIZE = 29
RATE_LIMIT_SLEEP = 31

OUTPUT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "Output"))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "earnings_dates.json")

CACHE_FILE = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..", "MooMoo", "src", "Output", "earnings_dates.json"
))

OPEND_HOST = os.getenv("FUTU_OPEND_HOST", "127.0.0.1")
OPEND_PORT = int(os.getenv("FUTU_OPEND_PORT", "11111"))


def check_opend():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    try:
        sock.connect((OPEND_HOST, OPEND_PORT))
    except Exception as e:
        print(f"ERROR: Cannot reach OpenD at {OPEND_HOST}:{OPEND_PORT} — {e}")
        sys.exit(1)
    finally:
        sock.close()


def to_jsonable(val):
    if val is None:
        return None
    import math
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    if hasattr(val, "item"):
        val = val.item()
    if hasattr(val, "name"):
        return val.name
    if isinstance(val, (str, int, float, bool)):
        return val
    return str(val)


def df_to_records(df):
    if df is None or (hasattr(df, "shape") and df.shape[0] == 0):
        return []
    records = []
    for i in range(len(df)):
        row = df.iloc[i]
        records.append({k: to_jsonable(row[k]) for k in row.index})
    return records


def fetch_earnings(ctx, code):
    ret, data = ctx.get_financials_earnings_price_move(code, period_count=50)
    if ret != RET_OK:
        raise RuntimeError(f"API error (ret={ret}): {data}")
    records = df_to_records(data)
    if not records:
        return []
    seen = set()
    out = []
    for r in records:
        period_text = r.get("period_text", "")
        pub_day = r.get("pub_trading_day_str", "")
        if not period_text or not pub_day:
            continue
        key = (period_text, pub_day)
        if key in seen:
            continue
        seen.add(key)
        pub_type_raw = r.get("pub_type")
        if pub_type_raw is not None:
            pub_type = PUB_TYPE_MAP.get(int(float(pub_type_raw)), str(pub_type_raw))
        else:
            pub_type = "Unknown"
        out.append({
            "period_text": period_text,
            "pub_trading_day_str": pub_day,
            "pub_type": pub_type,
            "fiscal_year": to_jsonable(r.get("fiscal_year")),
            "financial_type": to_jsonable(r.get("financial_type")),
        })
    return out


def load_cache():
    """Load previously fetched tickers from stat-arb output to avoid re-fetching."""
    if not os.path.isfile(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"  [warn] cache load failed: {e}")
        return {}


def main():
    check_opend()

    codes_needed = set(f"US.{t}" for t in TICKERS)
    cache = load_cache()

    codes_cached = set(cache.keys()) & codes_needed
    codes_to_fetch = sorted(codes_needed - codes_cached)

    print(f"Total universe: {len(codes_needed)} tickers")
    print(f"  cached (from MooMoo/): {len(codes_cached)}")
    print(f"  to fetch: {len(codes_to_fetch)}")
    print()

    result = dict(cache)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not codes_to_fetch:
        print("Nothing to fetch — all tickers are cached.")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        total_earnings = sum(len(v) for v in result.values())
        print(f"Saved {len(result)} tickers, {total_earnings} periods to {OUTPUT_FILE}")
        return

    ctx = None
    try:
        ctx = OpenQuoteContext(host=OPEND_HOST, port=OPEND_PORT)
        total = len(codes_to_fetch)
        for i, code in enumerate(codes_to_fetch, 1):
            sys.stdout.write(f"[{i}/{total}] {code} ... ")
            sys.stdout.flush()
            try:
                earnings = fetch_earnings(ctx, code)
                if earnings:
                    result[code] = earnings
                    sys.stdout.write(f"{len(earnings)} periods\n")
                else:
                    sys.stdout.write("no data\n")
            except Exception as e:
                sys.stdout.write(f"SKIPPED ({e})\n")
            sys.stdout.flush()
            if i % BATCH_SIZE == 0 and i < total:
                print(f"  rate-limit pause {RATE_LIMIT_SLEEP}s ...")
                time.sleep(RATE_LIMIT_SLEEP)
    finally:
        if ctx:
            ctx.close()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    total_earnings = sum(len(v) for v in result.values())
    print(f"\nDone. {len(result)} tickers, {total_earnings} periods saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
