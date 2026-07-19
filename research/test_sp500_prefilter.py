import sys; sys.path.insert(0, '.')
import time
import warnings
import pandas as pd
warnings.filterwarnings('ignore')

from src.constants import TICKERS, SECTOR_MAP
from src.data_loader import DataLoader
from src.pair_selection import PairSelector

SEL_START, SEL_END = '2023-06-01', '2023-07-31'
DIVERGENCE_THRESHOLD = 0.10

print("=== S&P 500 Cross-Sector Cointegration Test ===")
print(f"Selection window: {SEL_START} to {SEL_END}")
print(f"Return divergence threshold: {DIVERGENCE_THRESHOLD}")
print(f"Total tickers in universe: {len(TICKERS)}")
print()

# 1. Fetch data
print("Fetching S&P 500 prices...")
t0 = time.time()
loader = DataLoader(TICKERS, start='2023-01-01', end='2023-08-31', use_warmup=True)
master_df = loader.fetch_prices()
t1 = time.time()
print(f"Fetched in {t1-t0:.1f}s")
print(f"DataFrame shape: {master_df.shape}")

# Extract close prices (handle MultiIndex or flat)
if isinstance(master_df.columns, pd.MultiIndex):
    close_prices = master_df['Close']
else:
    close_prices = master_df

# How many tickers actually have data?
available = [t for t in TICKERS if t in close_prices.columns and close_prices[t].notna().sum() > 20]
print(f"Tickers with sufficient data: {len(available)} / {len(TICKERS)}")
missing = [t for t in TICKERS if t not in available]
if missing:
    print(f"  Missing/delisted: {', '.join(missing)}")
print()

# 2. Run pair selection with divergence pre-filter
print("Running pair selection (cross-sector, return_divergence_threshold=0.10)...")
selector = PairSelector(pvalue_threshold=0.05)
t2 = time.time()
result = selector.select_pairs(
    master_df, SECTOR_MAP, SEL_START, SEL_END,
    same_sector_only=False,
    return_divergence_threshold=DIVERGENCE_THRESHOLD
)
t3 = time.time()
stats = selector._stats

# 3. Compute stats
total = stats['total_combinations']
skipped = stats['divergence_skipped']
coint_tested = stats['coint_tested']
coint_passed = stats['coint_passed']

print()
print("=== RESULTS ===")
print(f"  Total cross-sector combinations:  {total:>8,}")
print(f"  Divergence > 10% (pre-filter):    {skipped:>8,}  ({skipped/total*100:.1f}%)")
print(f"  Tested for cointegration:         {coint_tested:>8,}  ({coint_tested/total*100:.1f}%)")
print(f"  Passed cointegration:             {coint_passed:>8,}  ({coint_passed/total*100:.1f}%)")
print(f"  Time: {t3-t2:.1f}s ({(t3-t2)/60:.1f}m)")
if coint_passed > 0:
    print()
    print("Top pairs selected:")
    for _, row in result.head(10).iterrows():
        print(f"  {row['pair']}  (log-pvalue={row['cointegration_pvalue_log']:.4f})")
