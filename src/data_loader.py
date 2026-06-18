import pandas as pd
import yfinance as yf
from datetime import timedelta
from typing import Dict, List, Tuple, Optional

class DataLoader:
    """
    Handles fetching historical price data from external sources 
    and managing local data consistency.
    """
    def __init__(self, tickers: List[str], start: str, end: str, lookback: int = 200, use_warmup: bool = True):
        self.tickers = tickers
        self.start = start
        self.end = end
        self.lookback = lookback
        self.use_warmup = use_warmup

    def fetch_prices(self) -> pd.DataFrame:
        """Fetch daily OHLC data for the given tickers with an optional warmup buffer."""
        # Add buffer for rolling lookbacks if requested
        if self.use_warmup:
            prestart = pd.to_datetime(self.start) - timedelta(days=self.lookback + 50) 
        else:
            prestart = self.start
            
        df = yf.download(self.tickers, start=prestart, end=self.end, progress=False)
        
        if isinstance(df, pd.Series):
            df = df.to_frame()
            
        return df.dropna(how='all')

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
