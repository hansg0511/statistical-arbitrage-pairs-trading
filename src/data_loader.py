import concurrent.futures
import hashlib
import os
import time
import pandas as pd
import yfinance as yf
from datetime import timedelta
from typing import Dict, List, Tuple, Optional


def _close_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        if 'Close' not in df.columns.get_level_values(0):
            raise ValueError('price snapshot has no Close columns')
        return df['Close']
    return df


def price_snapshot_fingerprint(path):
    """Return a content hash so a run records the exact market-data input."""
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def load_price_snapshot(path, tickers, start, end, use_warmup=True):
    """Load a strict, validated market-data snapshot without calling yfinance."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f'price snapshot does not exist: {path}')

    df = pd.read_pickle(path)
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise ValueError(f'price snapshot is empty or not a DataFrame: {path}')
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError(f'price snapshot index is not DatetimeIndex: {path}')

    close = _close_columns(df)
    present = [ticker for ticker in tickers if ticker in close.columns and close[ticker].notna().any()]
    required = max(1, int(len(tickers) * 0.95))
    if len(present) < required:
        raise ValueError(
            f'price snapshot has data for only {len(present)}/{len(tickers)} requested tickers '
            f'(need at least {required}): {path}'
        )

    required_start = pd.to_datetime(start)
    if use_warmup:
        required_start -= timedelta(days=250)
    required_end = pd.to_datetime(end)
    if df.index.min() > required_start or df.index.max() < required_end - timedelta(days=7):
        raise ValueError(
            f'price snapshot coverage {df.index.min().date()}..{df.index.max().date()} does not cover '
            f'the required {required_start.date()}..{required_end.date()} interval: {path}'
        )
    return df


def load_or_fetch_prices(loader, snapshot_path=None, write_snapshot_path=None):
    """Return market data and optional provenance for reproducible backtests."""
    if snapshot_path and write_snapshot_path:
        raise ValueError('use either price_snapshot or write_price_snapshot, not both')

    if snapshot_path:
        df = load_price_snapshot(
            snapshot_path, loader.tickers, loader.start, loader.end, loader.use_warmup
        )
        return df, {
            'mode': 'loaded',
            'path': os.path.abspath(snapshot_path),
            'sha256': price_snapshot_fingerprint(snapshot_path),
        }

    df = loader.fetch_prices()
    if write_snapshot_path and not df.empty:
        parent = os.path.dirname(os.path.abspath(write_snapshot_path))
        if not os.path.isdir(parent):
            raise FileNotFoundError(f'price snapshot parent directory does not exist: {parent}')
        df.to_pickle(write_snapshot_path)
        return df, {
            'mode': 'written',
            'path': os.path.abspath(write_snapshot_path),
            'sha256': price_snapshot_fingerprint(write_snapshot_path),
        }
    return df, None

class DataLoader:
    """
    Handles fetching historical price data from external sources 
    and managing local data consistency.
    """
    def __init__(self, tickers: List[str], start: str, end: str, lookback: int = 200, use_warmup: bool = True, timeout: int = 120,
                 max_retries: int = 3, min_fraction: float = 0.95):
        self.tickers = tickers
        self.start = start
        self.end = end
        self.lookback = lookback
        self.use_warmup = use_warmup
        self.timeout = timeout
        self.max_retries = max_retries
        self.min_fraction = min_fraction

    def _do_download(self, prestart):
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(yf.download, self.tickers, start=prestart, end=self.end, progress=False)
            try:
                return fut.result(timeout=self.timeout)
            except concurrent.futures.TimeoutError:
                print(f"ERROR: yfinance download timed out after {self.timeout}s for {len(self.tickers)} tickers")
                return pd.DataFrame()
            except Exception as e:
                print(f"ERROR: yfinance download failed: {e}")
                return pd.DataFrame()

    def _present_tickers(self, df):
        close = df['Close'] if isinstance(df.columns, pd.MultiIndex) else df
        if close is None or close.empty:
            return 0
        return int((close.notna().sum() > 0).sum())

    def fetch_prices(self) -> pd.DataFrame:
        """Fetch daily OHLC data with retry on rate-limit/empty and a completeness guard.

        A partial / rate-limited yfinance fetch silently corrupts downstream pair
        selection (tickers missing from master_df cause the runtime divergence
        filter to drop otherwise-valid pairs). We therefore:
          1. retry up to max_retries with backoff when too few tickers come back,
          2. raise a hard error if the fetched universe is materially short of the
             requested ticker list, so the caller never runs on a gutted universe.
        """
        if self.use_warmup:
            prestart = pd.to_datetime(self.start) - timedelta(days=self.lookback + 50)
        else:
            prestart = self.start

        df = None
        for attempt in range(self.max_retries + 1):
            df = self._do_download(prestart)
            if isinstance(df, pd.Series):
                df = df.to_frame()
            df = df.dropna(how='all') if df is not None and not df.empty else pd.DataFrame()
            present = self._present_tickers(df)
            target = len(self.tickers)
            if present >= self.min_fraction * target:
                return df
            if attempt < self.max_retries:
                wait = 15 * (2 ** attempt)
                print(f"WARN: only {present}/{target} tickers present after attempt {attempt + 1}; "
                      f"retrying in {wait}s (rate-limit likely)...")
                time.sleep(wait)

        present = self._present_tickers(df)
        target = len(self.tickers)
        raise RuntimeError(
            f"yfinance fetch incomplete: {present}/{target} tickers have data after "
            f"{self.max_retries + 1} attempts (need >= {self.min_fraction * target:.0f}). "
            f"This would silently corrupt pair selection - aborting. "
            f"Rate-limited/empty tickers are likely; reduce concurrency and retry."
        )

class DataManager:
    """
    Manages data slicing and caching to optimize signal generation 
    during walk-forward and optimization runs.
    """
    def __init__(self, master_df: pd.DataFrame):
        self.master_df = master_df
        self.z_cache = {}
        self.resid_cache = {}

    def get_OHLC(self, ticker: str, start: Optional[str] = None, end: Optional[str] = None) -> pd.DataFrame:
        """Retrieve price data for a single ticker, handling MultiIndex structures."""
        idx = pd.IndexSlice
        if isinstance(self.master_df.columns, pd.MultiIndex):
            df = self.master_df.loc[:, idx[:, ticker]]
            df.columns = df.columns.droplevel(1)
        else:
            df = self.master_df[[ticker]]
            
        if start or end:
            df = df.loc[start:end]
            
        return df.copy()

    def get_zscores(self, pair: Tuple[str, str], resid_lb: int, z_lb: int, start: str, end: str) -> pd.Series:
        """Calculate or retrieve cached Z-scores for a specific pair and lookback period."""
        from src.signal import compute_residuals, compute_zscore
        key = (pair, resid_lb, z_lb, start, end)
        
        if key not in self.z_cache:
            # Need extra history for the rolling metrics
            full_prices = self.get_OHLC(pair[0], end=end)['Close']
            warmup = resid_lb + z_lb + 10
            
            try:
                start_loc = full_prices.index.get_loc(start)
            except KeyError:
                start_loc = full_prices.index.get_indexer([start], method="bfill")[0]
            
            ext_start = full_prices.index[max(0, start_loc - warmup)]
            
            s1 = self.get_OHLC(pair[0], ext_start, end)['Close']
            s2 = self.get_OHLC(pair[1], ext_start, end)['Close']
            
            # Strategy default is log space
            res_df = compute_residuals(s1, s2, lookback=resid_lb, log_space=True)
            zscore = compute_zscore(res_df['residual'], lookback=z_lb)
            self.z_cache[key] = zscore.loc[start:end]
            
        return self.z_cache[key]
