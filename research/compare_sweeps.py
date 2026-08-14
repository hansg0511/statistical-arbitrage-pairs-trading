"""Compare the legacy CSV momentum sweep vs the consolidated (A/B) sweep rankings.

Usage: python research/compare_sweeps.py [--mechanism A|B|both]
"""
import os
import sys
import itertools
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from research import pair_sweep as legacy  # noqa: E402
from research.pair_sweep_consolidated import STRATEGIES, CFGS, pair_results  # noqa: E402

BASE = 'fixed_diagnosis'

_ret_cache = {}
_orig_load = legacy.load


def _cached_load(sec, start, cfg):
    key = (sec, start, cfg)
    if key not in _ret_cache:
        _ret_cache[key] = _orig_load(sec, start, cfg)
    return _ret_cache[key]


legacy.load = _cached_load


def legacy_ranking():
    legs = [(s, c) for s in STRATEGIES for c in CFGS]
    out = []
    for (sa, ca), (sb, cb) in itertools.combinations(legs, 2):
        rm, rng, hs, hr = legacy.pair_metrics(sa, ca, sb, cb, use_momentum=True)
        if pd.isna(hs):
            continue
        out.append({'pair': f'{sa}/{ca} + {sb}/{cb}', 'recent': rm, 'hist': hs,
                    'score': min(rm, hs)})
    out.sort(key=lambda x: x['score'], reverse=True)
    return out


def consolidated_ranking(mech):
    legs = [(s, c) for s in STRATEGIES for c in CFGS]
    out = []
    for (sa, ca), (sb, cb) in itertools.combinations(legs, 2):
        rm, rng, hs = pair_results(sa, ca, sb, cb, mech, 0.25)
        if pd.isna(hs):
            continue
        out.append({'pair': f'{sa}/{ca} + {sb}/{cb}', 'recent': rm, 'hist': hs,
                    'score': min(rm, hs)})
    out.sort(key=lambda x: x['score'], reverse=True)
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--mechanism', default='both', choices=['A', 'B', 'both'])
    args = ap.parse_args()

    print('Computing legacy CSV momentum sweep...')
    leg_rank = legacy_ranking()
    leg_top = {r['pair'] for r in leg_rank[:20]}

    lines = []
    lines.append('# Sweep comparison: legacy CSV momentum vs consolidated\n')
    lines.append('Legacy = return-arithmetic combined book with through-month momentum weights '
                 '(pair_sweep.py). Consolidated = trade-event shared-account replay at pct=0.25.\n')

    for mech in (['A', 'B'] if args.mechanism == 'both' else [args.mechanism]):
        print(f'Computing consolidated mech {mech} sweep...')
        con_rank = consolidated_ranking(mech)
        con_top = {r['pair'] for r in con_rank[:20]}
        overlap = leg_top & con_top

        by_pair = {r['pair']: r for r in leg_rank}
        lines.append(f'## Mechanism {mech}\n')
        lines.append(f'- Legacy momentum top-20: {len(leg_top)} pairs; consolidated top-20: {len(con_top)}; '
                     f'overlap: {len(overlap)} ({len(overlap)}/20)\n')
        lines.append('| Rank (cons) | Pair | Legacy score | Cons score | Legacy recent | Cons recent | Legacy hist | Cons hist |')
        lines.append('|---:|---|--:|--:|--:|--:|--:|--:|')
        for i, r in enumerate(con_rank[:20], 1):
            lp = by_pair.get(r['pair'])
            l = (lp or {}).get('score', float('nan'))
            lr = (lp or {}).get('recent', float('nan'))
            lh = (lp or {}).get('hist', float('nan'))
            lines.append(f'| {i} | {r["pair"]} | {l:.2f} | {r["score"]:.2f} | {lr:.2f} | {r["recent"]:.2f} | {lh:.2f} | {r["hist"]:.2f} |')
        lines.append('')

        # top-20 not shared
        only_cons = con_top - leg_top
        only_leg = leg_top - con_top
        lines.append(f'### In consolidated top-20 but not legacy: {sorted(only_cons)}\n')
        lines.append(f'### In legacy top-20 but not consolidated: {sorted(only_leg)}\n')

    out = os.path.join(BASE, '_SWEEP_COMPARISON.md')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('wrote', out)


if __name__ == '__main__':
    main()
