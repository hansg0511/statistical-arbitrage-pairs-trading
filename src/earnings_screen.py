import yfinance as yf
import pandas as pd
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from typing import Set, Optional

class EarningsScreen:
    """
    Pre-fetches historical earnings dates via yfinance and provides
    a fast check: does a ticker have an earnings date within the
    forward-looking window from a proposed entry date?

    Caches results to a pickle for reuse across runs (avoids 60+
    yfinance calls per sweep run).
    """
    def __init__(self, tickers, start, end, cache_path=None):
        self._cache_path = cache_path
        self._earnings: dict[str, Set[pd.Timestamp]] = {}

        if cache_path and Path(cache_path).exists():
            self._load_cache()
            missing = [t for t in tickers if t not in self._earnings]
            if missing:
                self._fetch(missing, start, end)
                self._save_cache()
        else:
            self._fetch(tickers, start, end)
            if cache_path:
                self._save_cache()

    def _fetch(self, tickers, start, end):
        start_dt = pd.to_datetime(start).normalize()
        end_dt = pd.to_datetime(end).normalize()
        for ticker in tickers:
            try:
                t = yf.Ticker(ticker)
                dates = t.earnings_dates
                if dates is None or dates.empty:
                    self._earnings[ticker] = set()
                    continue
                # Filter to Earnings events only and normalize to dates
                if 'Event Type' in dates.columns:
                    dates = dates[dates['Event Type'] == 'Earnings']
                earnings_dates = {d.date() for d in dates.index if start_dt.date() <= d.date() <= end_dt.date()}
                self._earnings[ticker] = earnings_dates
            except Exception:
                self._earnings[ticker] = set()

    def has_earnings_in_window(self, ticker, entry_date, max_holding_days=15, block_days_after=0):
        entry = pd.to_datetime(entry_date).date()
        dates = self._earnings.get(ticker)
        if not dates:
            return False
        # Forward window: earnings within (entry, entry + max_holding_days]
        window_end = entry + timedelta(days=max_holding_days)
        if any(entry < d <= window_end for d in dates):
            return True
        # Backward window uses calendar dates and blocks the post-event period.
        # An event within the configured N-calendar-day window blocks the entry.
        if block_days_after > 0:
            block_start = entry - timedelta(days=block_days_after)
            if any(block_start < d <= entry for d in dates):
                return True
        return False

    def _save_cache(self):
        with open(self._cache_path, 'wb') as f:
            pickle.dump(self._earnings, f)

    def _load_cache(self):
        with open(self._cache_path, 'rb') as f:
            self._earnings = pickle.load(f)

    def summary(self):
        total = sum(len(v) for v in self._earnings.values())
        return f"EarningsScreen: {len(self._earnings)} tickers, {total} earnings dates"
