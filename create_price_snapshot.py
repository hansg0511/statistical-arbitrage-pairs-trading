"""Download one reproducible price snapshot without running a backtest.

Usage:
    python create_price_snapshot.py --universe core --start 2023-01-01 --end 2026-01-01 --output research/archive/snapshots/core_recent.pkl
"""

import argparse
import os

from src.constants import TICKERS_CORE, TICKERS_SP500
from src.data_loader import DataLoader, load_or_fetch_prices


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--universe', choices=('core', 'sp500'), required=True)
    parser.add_argument('--start', required=True)
    parser.add_argument('--end', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--no-warmup', action='store_true')
    args = parser.parse_args()

    parent = os.path.dirname(os.path.abspath(args.output))
    if not os.path.isdir(parent):
        parser.error(f'output parent directory does not exist: {parent}')

    tickers = TICKERS_CORE if args.universe == 'core' else TICKERS_SP500
    loader = DataLoader(
        tickers, start=args.start, end=args.end, use_warmup=not args.no_warmup
    )
    _, snapshot = load_or_fetch_prices(loader, write_snapshot_path=args.output)
    if snapshot is None:
        raise RuntimeError('no snapshot was written because the price fetch was empty')
    print(f"Wrote {snapshot['path']} ({snapshot['sha256']})")


if __name__ == '__main__':
    main()
