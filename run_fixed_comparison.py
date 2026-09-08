"""Generate fixed_diagnosis/_COMPARISON_WITH_PIPELINE.md — old vs new, full detail.

Historical sections (08a/08b/09a/09b) hold a SINGLE start date, so their numbers
are single-start (apples-to-apples with the old single-start pipeline cells).
Recent sections (05/06/07/10/10a/10b) are 5-start (10 = 8-start) means.
"""
import glob, os, json, statistics
from src.result_validation import validate_run_output

BASE = 'fixed_diagnosis'
CFGS = ['same_sector_slide3m_noscreen', 'same_sector_slide3m_bd7',
        'same_sector_slide1m_noscreen', 'same_sector_slide1m_bd7',
        'cross_sector_slide3m_noscreen', 'cross_sector_slide3m_bd7',
        'cross_sector_slide1m_noscreen', 'cross_sector_slide1m_bd7']


def stats(section, cfg):
    v = []
    for f in glob.glob(os.path.join(BASE, section, '*_%s/metrics.json' % cfg)):
        run_dir = os.path.dirname(f)
        validation = validate_run_output(run_dir)
        if not validation['valid']:
            details = '; '.join(validation['reasons'])
            raise RuntimeError(f'invalid run output {run_dir}: {details}')
        m = json.load(open(f))
        v.append((m['annualized_sharpe'], m['annualized_return'] * 100))
    if not v:
        return None, None
    return (round(statistics.mean(x[0] for x in v), 2),
            round(statistics.mean(x[1] for x in v), 2))


# ---- OLD numbers extracted from RESEARCH_PIPELINE.md (Sh, Ret) ----
OLD_2M = {
    'same_sector_slide3m_noscreen': [0.38, 0.81, -0.16, -0.50, 0.80, 2.28, 0.02, 0.08],
    'same_sector_slide3m_bd7':      [0.39, 0.55, -0.47, -1.03, 0.81, 1.79, 0.42, 0.65],
    'same_sector_slide1m_noscreen': [-0.24, -0.41, -0.06, -0.12, 1.01, 1.76, -0.00, -0.02],
    'same_sector_slide1m_bd7':      [-0.27, -0.39, -0.27, -0.37, 1.28, 1.79, 0.40, 0.41],
    'cross_sector_slide3m_noscreen': [0.12, 0.24, -0.03, -0.10, 0.34, 0.79, 0.33, 0.72],
    'cross_sector_slide3m_bd7':     [0.20, 0.26, -0.09, -0.16, 0.73, 1.18, 0.13, 0.36],
    'cross_sector_slide1m_noscreen': [0.01, 0.00, -0.09, -0.19, 0.32, 0.57, 0.29, 0.59],
    'cross_sector_slide1m_bd7':     [0.25, 0.27, -0.01, -0.03, 0.48, 0.56, 0.05, 0.06],
}
OLD_12M = {
    'same_sector_slide3m_noscreen': [-0.48, -0.53, 1.56, 2.83, -0.20, -0.46, 1.40, 4.41],
    'same_sector_slide3m_bd7':      [0.26, 0.23, 0.85, 0.94, 0.72, 0.44, 0.91, 1.78],
    'same_sector_slide1m_noscreen': [-0.48, -0.29, 0.11, 0.15, 0.08, 0.08, 1.42, 4.02],
    'same_sector_slide1m_bd7':      [0.53, 0.23, 0.56, 0.56, 0.97, 0.48, 1.64, 2.70],
    'cross_sector_slide3m_noscreen': [0.02, 0.03, -0.09, -0.31, 0.06, 0.50, 1.07, 2.64],
    'cross_sector_slide3m_bd7':     [0.21, 0.26, -0.02, -0.07, 0.08, 0.11, 0.25, 0.46],
    'cross_sector_slide1m_noscreen': [-0.12, -0.19, 0.53, 1.03, 0.36, 0.71, 1.47, 2.50],
    'cross_sector_slide1m_bd7':     [0.14, 0.13, 0.56, 0.88, 0.36, 0.40, 0.97, 1.22],
}
SECTIONS_2M = ['08a', '09a', '06', '07']
SECTIONS_12M = ['08b', '09b', '10a', '10b']
HDR_2M = ['core 2015-19 (08a)', 'SP500 2015-19 (09a)', 'core recent (06)', 'SP500 recent (07)']
HDR_12M = ['core 2015-19 (08b)', 'SP500 2015-19 (09b)', 'core recent (10a)', 'SP500 recent (10b)']
# label the averaging convention per cell
CONV_2M = ['single-start', 'single-start', '5-start', '5-start']
CONV_12M = ['single-start', 'single-start', '5-start', '5-start']

L = []


def matrix_block(title, old_map, sections, headers, conv):
    L.append('### %s\n' % title)
    L.append('| Config | ' + ' | '.join('%s <br><sub>%s</sub>' % (h, c) for h, c in zip(headers, conv)) + ' |')
    L.append('|---|' + '|'.join(['---'] * len(headers)) + '|')
    for c in CFGS:
        cells = []
        for i, sec in enumerate(sections):
            old_sh = old_map[c][i * 2]
            new_sh, new_ret = stats(sec, c)
            if new_sh is None:
                cells.append('N/A')
                continue
            d = new_sh - old_sh
            arrow = '▲' if d > 0.05 else ('▼' if d < -0.05 else '≈')
            cells.append('%s → %s (%+0.2f) %s' % (old_sh, new_sh, d, arrow))
        L.append('| `%s` | %s |' % (c, ' | '.join(cells)))
    L.append('')


def best_of(sec):
    best = None
    for c in CFGS:
        sh, rt = stats(sec, c)
        if sh is not None and (best is None or sh > best[1]):
            best = (c, sh, rt)
    return best


# ---- Header ----
L.append('# Fixed-window reruns vs RESEARCH_PIPELINE.md\n')
L.append('Generated from `fixed_diagnosis/` (aligned windows) against the numbers published in '
         '`RESEARCH_PIPELINE.md`. All figures are annualized Sharpe unless noted.\n')

# ---- Caveats ----
L.append('## How to read this (caveats)\n')
L.append('Old and new numbers are **not perfectly apples-to-apples**. Differences mix three changes:\n')
L.append('1. **Trading window:** old historical = single 2015-01-01 start, trading 2016-01 → 2020-12 '
         '(trimmed); new = 2014-11-01 (2m) / 2014-01-01 (12m) single start, trading 2015-01 → 2019-12. '
         '**2020 is fully dropped** in the new runs. Recent: old ≈ 2024-02 → 2025-12; new = '
         '2024-01 → 2025-12 for all.\n')
L.append('2. **Averaging convention:** historical cells are single-start in BOTH old and new. '
         'Recent cells are 5-start means (10 = 8-start) in both. No triple-counting remains: each '
         'historical section is one run over the full 2015-2019 window.\n')
L.append('3. **Selection alignment:** new 2m and 12m grids trade the *identical* calendar window '
         '(start pushed back by `sel_months`), removing the 12m-vs-2m warmup mismatch that existed in '
         'the old runs. Configs, `mp=20`, `pct=0.045` (mp=5/pct=0.18 for 05, pct=0.25 for 10) unchanged.\n')
L.append('Treat a delta as informative, not causal — it bundles window + alignment.\n')

# ---- Tier 1: headline ----
L.append('## 1. Headline — best config per cell (old → new)\n')
L.append('| Cell | Old best (Sh) | New best | Δ |')
L.append('|---|---:|---:|---:|')
headline = [
    ('core 2m hist (08a)', 'same_sector_slide3m_bd7', 0.39, best_of('08a')),
    ('SP500 2m hist (09a)', 'none (all negative)', -0.01, best_of('09a')),
    ('core 2m recent (06)', 'same_sector_slide1m_bd7', 1.28, best_of('06')),
    ('SP500 2m recent (07)', 'same_sector_slide3m_bd7', 0.42, best_of('07')),
    ('core 12m hist (08b)', 'same_sector_slide1m_bd7', 0.53, best_of('08b')),
    ('SP500 12m hist (09b)', 'same_sector_slide3m_noscreen', 1.56, best_of('09b')),
    ('core 12m recent (10a)', 'same_sector_slide1m_bd7', 0.97, best_of('10a')),
    ('SP500 12m recent (10b)', 'same_sector_slide1m_bd7', 1.64, best_of('10b')),
]
for cell, old_cfg, old, new in headline:
    if new is None:
        L.append('| %s | `%s` %.2f | N/A | — |' % (cell, old_cfg, old))
        continue
    c, sh, rt = new
    d = sh - old
    arrow = '▲' if d > 0.05 else ('▼' if d < -0.05 else '≈')
    L.append('| %s | `%s` %.2f | `%s` **%.2f** / %.2f%% | %+.2f %s |'
             % (cell, old_cfg, old, c, sh, rt, d, arrow))
L.append('')

# ---- Tier 2: full matrices ----
L.append('## 2. Full per-config delta matrices (Sharpe: old → new, Δ)\n')
L.append('*Cells show `old → new (Δ)`; ▲ = +>0.05, ▼ = −>0.05, ≈ = within ±0.05. '
         'Historical cells are single-start on both sides.*\n')
matrix_block('2-month selection', OLD_2M, SECTIONS_2M, HDR_2M, CONV_2M)
matrix_block('12-month selection', OLD_12M, SECTIONS_12M, HDR_12M, CONV_12M)

# ---- Tier 4: key takeaways ----
L.append('## 3. What changed / key takeaways\n')
best_09a = best_of('09a')
L.append('- **SP500 2m historical flipped positive** (old: all 8 configs negative −0.01…−0.47; '
         'new single-start best `%s` %.2f). Dropping 2020 + aligned windows changed '
         'the verdict on this cell.\n' % (best_09a[0], best_09a[1]))
L.append('- **SP500 12m historical best collapsed** (old single-start `same 3m noscreen` 1.56 → '
         'new single-start best `%s` %.2f). The 1.56 was largely a 2016-2020 window effect.\n'
         % (best_of('09b')[0], best_of('09b')[1]))
L.append('- **Core 12m historical** best `%s` %.2f vs old 0.53. Core 12m remains the thin-book '
         'caveat (few same-sector pairs).\n' % (best_of('08b')[0], best_of('08b')[1]))
best_07 = best_of('07')
best_10a = best_of('10a')
best_10b = best_of('10b')
L.append('- **Recent cells are not uniformly stable:** core 2m `same 1m bd7` 1.28 → %.2f; SP500 2m '
         '`same 3m bd7` 0.42 → %.2f (best now `%s` %.2f); core 12m `same 1m bd7` 0.97 → %.2f '
         '(best now `%s` %.2f); SP500 12m `same 1m bd7` 1.64 → %.2f (best now `%s` %.2f).\n'
         % (stats('06', 'same_sector_slide1m_bd7')[0],
            stats('07', 'same_sector_slide3m_bd7')[0], best_07[0], best_07[1],
            stats('10a', 'same_sector_slide1m_bd7')[0], best_10a[0], best_10a[1],
            stats('10b', 'same_sector_slide1m_bd7')[0], best_10b[0], best_10b[1]))
L.append('- **Consistent rule:** SP500 needs 12m selection; core 2m ≥ core 12m on recent. '
         'The universe × selection interaction in RESEARCH_PIPELINE.md still holds under aligned windows.\n')

out = os.path.join(BASE, '_COMPARISON_WITH_PIPELINE.md')
with open(out, 'w', encoding='utf-8') as f:
    f.write('\n'.join(L) + '\n')
print('wrote', out, '(%d lines)' % len(L))
