import sys; sys.path.insert(0, '.')
import time
import warnings
warnings.filterwarnings('ignore')

from datetime import date
from dateutil.relativedelta import relativedelta
from src.constants import TICKERS, SECTOR_MAP, UNIVERSE
from src.data_loader import DataLoader
from src.pair_selection import PairSelector
from src.pair_cache import PairSelectionCache

# Fetch full data range with warmup
print("Fetching data (2015-01-01 to 2026-01-01)...")
loader = DataLoader(TICKERS, start='2015-01-01', end='2026-01-01', use_warmup=True)
master_df = loader.fetch_prices()

selector = PairSelector(pvalue_threshold=0.05)
cache = PairSelectionCache('research/cache')

# Generate windows matching FoldBuilder(slide=1, sel_len=2)
# sel_end = sel_start + relativedelta(months=2) - timedelta(days=1)
windows = []
curr = date(2015, 1, 1)
stop = date(2025, 12, 31)
while True:
    sel_end = curr + relativedelta(months=2) - relativedelta(days=1)
    if sel_end > stop:
        break
    windows.append((curr, sel_end))
    curr += relativedelta(months=1)

total = len(windows)
print(f"Seeding {total} selection windows (x2 modes = {total * 2} cache keys)")
print(f"Range: {windows[0][0]} to {windows[-1][1]}")
print()

# Track cross-sector vs same-sector
stats = {'cross': 0, 'same': 0, 'cross_hit': 0, 'same_hit': 0}
start_time = time.time()

for i, (sel_start, sel_end) in enumerate(windows):
    s_str, e_str = str(sel_start), str(sel_end)

    for same_sector, mode in [(True, 'same'), (False, 'cross')]:
        key = (UNIVERSE, s_str, e_str, same_sector)
        cached = cache.get(key)
        if cached is not None:
            stats[f'{mode}_hit'] += 1
            pair_count = len(cached)
        else:
            df = selector.select_pairs(master_df, SECTOR_MAP, s_str, e_str, same_sector_only=same_sector)
            cache.set(key, df)
            pair_count = len(df)
            stats[mode] += 1

    if (i + 1) % 10 == 0:
        elapsed = time.time() - start_time
        print(f"[{i+1}/{total}] {s_str} → {e_str} | "
              f"cross: {stats['cross']} new, {stats['cross_hit']} cached | "
              f"same: {stats['same']} new, {stats['same_hit']} cached | "
              f"{elapsed:.0f}s elapsed")
        cache.save()

# Final save
elapsed = time.time() - start_time
print(f"\nDone. {elapsed:.0f}s total")
print(f"Cross-sector: {stats['cross']} computed, {stats['cross_hit']} cached hits")
print(f"Same-sector:  {stats['same']} computed, {stats['same_hit']} cached hits")
cache.save()
print("Cache saved.")
