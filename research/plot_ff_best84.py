"""Plots + multi-start Fama-French + comparison for the tuned momentum config.

Config: from argv (best84: lb84/s0.20/b20-80; final84: lb84/s0.30/b15-85; clean40: lb84/s0.40/b10-90). Replaces the default
lb63/step0.10/bounds 0.25-0.75). Pair is the clean-data consensus winner:
  sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_bd7.

Outputs (`fixed_diagnosis/best84 (old)/` or `final84 (old)/`; `clean40/` remains live):
  pair_equity_recent.png      3 panels (control + lucky starts 3,4)
  pair_equity_historical.png  1 chart
  weightA_recent.png          5 panels, w_A path
  weightA_equity_recent.png   5 rows x [equity | weight]
  _FF_PAIR_MULTISTART_best84.md / .csv
  _FF_COMPARE_<tag>_vs_default.md

Usage: python research/plot_ff_best84.py [best84|final84|clean40] [--reports-only|--plots-only]
"""
import os
import sys
import statistics

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402
import matplotlib  # noqa: E402
matplotlib.use('Agg')
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

from research.momentum_ff_pairs import FamaFrenchFetcher  # noqa: E402
from research.pair_sweep_consolidated import get_leg, STARTS_12M, STARTS_2M  # noqa: E402
from research.run_combined_backtest import (  # noqa: E402
    weight_path_momentum_causal, simulate, metrics,
)

BASE = 'fixed_diagnosis'
CONFIG = sys.argv[1] if len(sys.argv) > 1 else 'best84'
REPORTS_ONLY = '--reports-only' in sys.argv[2:]
PLOTS_ONLY = '--plots-only' in sys.argv[2:]
if REPORTS_ONLY and PLOTS_ONLY:
    raise SystemExit('--reports-only and --plots-only cannot be combined')
if CONFIG == 'best84':
    OUT = os.path.join(BASE, 'best84 (old)')
    TAG = 'best84'
    PARAMS = dict(lookback=84, step=0.20, wmin=0.20, wmax=0.80)
    CONFIG_LABEL = 'lb84/s0.20/b20-80'
elif CONFIG == 'final84':
    OUT = os.path.join(BASE, 'final84 (old)')
    TAG = 'final84'
    PARAMS = dict(lookback=84, step=0.30, wmin=0.15, wmax=0.85)
    CONFIG_LABEL = 'lb84/s0.30/b15-85'
elif CONFIG == 'clean40':
    OUT = os.path.join(BASE, 'clean40')
    TAG = 'clean40'
    PARAMS = dict(lookback=84, step=0.40, wmin=0.10, wmax=0.90)
    CONFIG_LABEL = 'lb84/s0.40/b10-90'
else:
    raise SystemExit('usage: python research/plot_ff_best84.py [best84|final84|clean40]')
PCT = 0.25
N_STARTS = 5

PAIR = ('sp500-12m', 'cross_sector_slide1m_noscreen',
        'sp500-2m', 'cross_sector_slide3m_bd7')
DEFAULT_PARAMS = dict(lookback=63, step=0.10, wmin=0.25, wmax=0.75)

LEG_A = ('sp500-12m', 'cross_sector_slide1m_noscreen')
LEG_B = ('sp500-2m', 'cross_sector_slide3m_bd7')
LABEL_A = 'A %s/%s' % LEG_A
LABEL_B = 'B %s/%s' % LEG_B
COLORS = {'A': '#1f77b4', 'B': '#6a0dad', 'mechA': '#2e8b57',
          'mechB': '#e67e22', 'sp500': '#8b0000'}


def sp500_buy_hold():
    ff = pd.read_pickle('research/ff_factors/ff_daily.pkl')
    return (ff['Mkt-RF'] + ff['RF']).dropna()


def eq(r):
    return (1 + r.fillna(0.0)).cumprod()


def leg_a_ret(window, start_idx=0):
    return get_leg(LEG_A[0], LEG_A[1], window, start_idx)['ret']


def leg_b_ret(window, start_idx=0):
    return get_leg(LEG_B[0], LEG_B[1], window, start_idx)['ret']


def pair_ret(window, mech, params, start_idx=0):
    sa, ca, sb, cb = PAIR
    return _combined_series_params(sa, ca, sb, cb, window, mech, params, start_idx)


def weight_path(i, params):
    a, b = leg_a_ret('recent', i), leg_b_ret('recent', i)
    return weight_path_momentum_causal(a, b, **params)


def weight_ylim(params):
    return max(0.0, params['wmin'] - 0.05), min(1.0, params['wmax'] + 0.05)


def start_label(i):
    return '12m %s / 2m %s' % (STARTS_12M[i], STARTS_2M[i])


def plot_window(ax, window, params, start_idx=None):
    i = start_idx or 0
    series = {}
    series['A'] = eq(leg_a_ret(window, i))
    series['B'] = eq(leg_b_ret(window, i))
    for mech in ['A', 'B']:
        series['mech' + mech] = eq(pair_ret(window, mech, params, i))
    x0 = min(s.index.min() for s in series.values())
    x1 = max(s.index.max() for s in series.values())
    mkt = sp500_buy_hold().loc[x0:x1]
    series['sp500'] = eq(mkt)
    style = {'A': dict(lw=1.4), 'B': dict(lw=1.4, ls=':'),
             'mechA': dict(lw=1.5), 'mechB': dict(lw=1.3, ls='--'),
             'sp500': dict(lw=1.6, ls='--')}
    for k, s in series.items():
        ax.plot(s.index, s.values, color=COLORS[k], label='%s  (final %.2f)' % (k, s.iloc[-1]),
                **style[k])
    ax.axhline(1.0, color='gray', lw=0.8, ls='--')
    ax.set_ylabel('Growth of $1')
    ax.grid(alpha=0.3)


def fig_recent(params):
    picks = [0, 3, 4]
    fig, axes = plt.subplots(1, len(picks), figsize=(18, 5.5))
    for ax, i in zip(axes, picks):
        plot_window(ax, 'recent', params, i)
        sh_a = metrics(leg_a_ret('recent', i))['sharpe']
        sh_b = metrics(leg_b_ret('recent', i))['sharpe']
        sh_ma = metrics(pair_ret('recent', 'A', params, i))['sharpe']
        sh_mb = metrics(pair_ret('recent', 'B', params, i))['sharpe']
        ax.set_title('start %s\nA %.2f | B %.2f | mechA %.2f | mechB %.2f' % (
            start_label(i), sh_a, sh_b, sh_ma, sh_mb), fontsize=9)
        ax.legend(loc='best', fontsize=7)
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b\n%Y'))
    fig.suptitle('Recent (2024-2025) — tuned config %s' % CONFIG_LABEL,
                 y=1.0, fontsize=12)
    plt.tight_layout()
    out = os.path.join(OUT, 'pair_equity_recent.png')
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('saved', out)


def fig_historical(params):
    fig, ax = plt.subplots(figsize=(11, 5.5))
    plot_window(ax, 'historical', params)
    sh_a = metrics(leg_a_ret('historical'))['sharpe']
    sh_b = metrics(leg_b_ret('historical'))['sharpe']
    sh_ma = metrics(pair_ret('historical', 'A', params))['sharpe']
    sh_mb = metrics(pair_ret('historical', 'B', params))['sharpe']
    ax.set_title('Historical (2015-2019) — tuned config %s\n'
                 'A %.2f | B %.2f | mechA %.2f | mechB %.2f' % (CONFIG_LABEL, sh_a, sh_b, sh_ma, sh_mb),
                 fontsize=10)
    ax.legend(loc='best', fontsize=8)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.tight_layout()
    out = os.path.join(OUT, 'pair_equity_historical.png')
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('saved', out)


def fig_weights(params):
    fig, axes = plt.subplots(1, 5, figsize=(19, 4), sharex=True, sharey=True)
    for ax, i in zip(axes, range(5)):
        wp = weight_path(i, params)
        ax.plot(wp.index, wp.values, color='#444', drawstyle='steps-post', lw=1.8, label='w_A')
        ax.axhline(0.5, color='gray', lw=0.8, ls='--')
        ax.axhline(params['wmax'], color='gray', lw=0.6, ls=':')
        ax.axhline(params['wmin'], color='gray', lw=0.6, ls=':')
        ax.set_ylim(*weight_ylim(params))
        ax.set_title('start %s' % start_label(i), fontsize=8)
        ax.grid(alpha=0.3)
        if i == 0:
            ax.set_ylabel('w_A (weight on leg A)')
            ax.legend(loc='best', fontsize=8)
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%y'))
    fig.suptitle('Weight on leg A (%s) — tuned config %s (w_B = 1 - w_A)'
                 % (LABEL_A, CONFIG_LABEL), y=1.0, fontsize=11)
    plt.tight_layout()
    out = os.path.join(OUT, 'weightA_recent.png')
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('saved', out)


def fig_equity_weight(params):
    fig, axes = plt.subplots(5, 2, figsize=(16, 15), gridspec_kw={'width_ratios': [2, 1]})
    for i in range(5):
        ax_eq, ax_w = axes[i]
        ax_eq.plot(eq(leg_a_ret('recent', i)).index, eq(leg_a_ret('recent', i)).values,
                   color=COLORS['A'], lw=1.3, label=LABEL_A)
        ax_eq.plot(eq(leg_b_ret('recent', i)).index, eq(leg_b_ret('recent', i)).values,
                   color=COLORS['B'], lw=1.3, ls=':', label=LABEL_B)
        ax_eq.plot(eq(pair_ret('recent', 'A', params, i)).index,
                   eq(pair_ret('recent', 'A', params, i)).values,
                   color=COLORS['mechA'], lw=1.5, label='pair mech A')
        ax_eq.plot(eq(pair_ret('recent', 'B', params, i)).index,
                   eq(pair_ret('recent', 'B', params, i)).values,
                   color=COLORS['mechB'], lw=1.3, ls='--', label='pair mech B')
        ax_eq.axhline(1.0, color='gray', lw=0.8, ls='--')
        ax_eq.grid(alpha=0.3)
        sh_a = metrics(leg_a_ret('recent', i))['sharpe']
        sh_b = metrics(leg_b_ret('recent', i))['sharpe']
        sh_ma = metrics(pair_ret('recent', 'A', params, i))['sharpe']
        ax_eq.set_ylabel('Growth of $1' if i == 4 else '')
        ax_eq.set_title('start %s — A %.2f / B %.2f / mechA %.2f' % (
            start_label(i), sh_a, sh_b, sh_ma), fontsize=8)
        wp = weight_path(i, params)
        ax_w.plot(wp.index, wp.values, color='#444', drawstyle='steps-post', lw=1.8)
        ax_w.axhline(0.5, color='gray', lw=0.8, ls='--')
        ax_w.set_ylim(*weight_ylim(params))
        ax_w.set_ylabel('w_A' if i == 4 else '')
        ax_w.set_title('w_A (on leg A)', fontsize=8)
        ax_w.grid(alpha=0.3)
        ax_eq.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
        ax_eq.xaxis.set_major_formatter(mdates.DateFormatter('%b\n%Y'))
        ax_w.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        ax_w.xaxis.set_major_formatter(mdates.DateFormatter('%b-%y'))
        plt.setp(ax_eq.get_xticklabels(), rotation=0, fontsize=7)
        plt.setp(ax_w.get_xticklabels(), rotation=0, fontsize=7)
        if i == 0:
            ax_eq.legend(loc='best', fontsize=7)
    fig.suptitle('Weight on leg A (%s) vs equity — tuned config %s'
                 % (LABEL_A, CONFIG_LABEL), y=1.0, fontsize=12)
    plt.tight_layout()
    out = os.path.join(OUT, 'weightA_equity_recent.png')
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('saved', out)


def _combined_series_params(sa, ca, sb, cb, window, mech, params, start_idx=0):
    """Build a combined series using the explicitly supplied momentum params."""
    a = get_leg(sa, ca, window, start_idx)
    b = get_leg(sb, cb, window, start_idx)
    wp = weight_path_momentum_causal(a['ret'], b['ret'], **params)
    rows, _, _, _ = simulate({'A': a, 'B': b}, wp, mech, capital=1e6, pct=PCT)
    return pd.Series([r['daily_return'] for r in rows],
                     index=[r['date'] for r in rows])


def _run_ff(pair, window, mech, params, start_idx):
    sa, ca, sb, cb = pair
    r = _combined_series_params(sa, ca, sb, cb, window, mech, params, start_idx)
    sharpe = metrics(r)['sharpe']
    r.name = 'combined'
    res = FamaFrenchFetcher(frequency='daily').regress(
        r, include_momentum=True, include_st_rev=True)
    row = {'window': window, 'mech': mech, 'start': start_idx, 'sharpe': sharpe,
           'alpha_ann': res.alpha_ann, 'alpha_tstat': res.alpha_tstat,
           'alpha_pval': res.alpha_pval, 'rsquared': res.rsquared, 'n_obs': res.n_obs}
    for _, l in res.loadings.iterrows():
        row['%s_beta' % l['factor']] = l['beta']
        row['%s_pval' % l['factor']] = l['pval']
    return row


def run_ff_md():
    sa, ca, sb, cb = PAIR
    rows = []
    for mech in ['A', 'B']:
        rows.append(_run_ff(PAIR, 'historical', mech, PARAMS, 0))
        for i in range(N_STARTS):
            rows.append(_run_ff(PAIR, 'recent', mech, PARAMS, i))
    df = pd.DataFrame(rows)

    csv_path = os.path.join(OUT, '_FF_PAIR_MULTISTART_%s.csv' % TAG)
    md_path = os.path.join(OUT, '_FF_PAIR_MULTISTART_%s.md' % TAG)
    df.to_csv(csv_path, index=False)

    lines = ['# Multi-start Fama-French (FF3 + Mom + ST_Rev, daily, HAC) — pair `%s`\n' % label()]
    lines.append('Combined daily-return series via the trade-event replay, **tuned momentum config '
                 '(%s)**. Historical = single window (2015-2019). '
                 % CONFIG_LABEL
                 + 'Recent = each of the %d aligned start-pairs (all trading strictly 2024-2025). '
                 'Alpha annualized x252; HAC standard errors. **Values in brackets are p-values**.\n'
                 % N_STARTS)
    lines.append('| Window | Start | Mech | Alpha% | Mkt-RF | SMB | HML | Mom | ST_Rev | Sharpe | R2 | N |')
    lines.append('|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
    for _, r in df.iterrows():
        lines.append('| %s | %s | %s | %+.2f%% (%.3f) | %.2f (%.3f) | %.2f (%.3f) | '
                     '%.2f (%.3f) | %.2f (%.3f) | %.2f (%.3f) | %.2f | %.3f | %d |'
                     % (r['window'], r['start'], r['mech'],
                        r['alpha_ann'] * 100, r['alpha_pval'],
                        r['Mkt-RF_beta'], r['Mkt-RF_pval'],
                        r['SMB_beta'], r['SMB_pval'],
                        r['HML_beta'], r['HML_pval'],
                        r['Mom_beta'], r['Mom_pval'],
                        r['ST_Rev_beta'], r['ST_Rev_pval'],
                        r['sharpe'], r['rsquared'], r['n_obs']))
    lines.append('')

    lines.append('## Recent alpha across the %d starts (per mechanism)\n' % N_STARTS)
    lines.append('| Mech | hist alpha | recent mean | recent min | recent max | # positive | # p<0.05 |')
    lines.append('|---|---:|---:|---:|---:|---:|---:|')
    for mech in ['A', 'B']:
        rec = df[(df['mech'] == mech) & (df['window'] == 'recent')]
        hist = df[(df['mech'] == mech) & (df['window'] == 'historical')]
        alphas = rec['alpha_ann'].tolist()
        n_pos = sum(1 for a in alphas if a > 0)
        n_sig = sum(1 for a, p in zip(alphas, rec['alpha_pval']) if p < 0.05)
        lines.append('| %s | %+.2f%% | %+.2f%% | %+.2f%% | %+.2f%% | %d | %d |'
                     % (mech, hist['alpha_ann'].iloc[0] * 100,
                        statistics.mean(alphas) * 100, min(alphas) * 100,
                        max(alphas) * 100, n_pos, n_sig))
    lines.append('')
    lines.append('Caveat: alphas are annualized point estimates; with ~400-500 recent obs and HAC '
                 'errors, p<0.05 is a high bar.\n')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('wrote', md_path)
    print('wrote', csv_path)
    return df


def label():
    sa, ca, sb, cb = PAIR
    return '%s/%s + %s/%s' % (sa, ca, sb, cb)


def load_default_ff():
    sa, ca, sb, cb = PAIR
    tag = '%s_%s_%s_%s' % (sa, ca, sb, cb)
    p = os.path.join(BASE, 'compare', '_FF_PAIR_MULTISTART_%s.csv' % tag)
    if not os.path.exists(p):
        print('WARN: default FF csv not found:', p)
        return None
    return pd.read_csv(p)


def write_compare(df_new):
    df_old = load_default_ff()
    lines = ['# Config comparison — tuned (%s) vs default (lb63/step0.10/b25-75)\n' % CONFIG_LABEL]
    lines.append('Pair: `%s`.\n' % label())

    lines.append('## Sharpe by window/mech\n')
    lines.append('| Window | Mech | default Sh | tuned Sh | delta |')
    lines.append('|---|---:|---:|---:|---:|')
    for window in ['historical', 'recent']:
        for mech in ['A', 'B']:
            if window == 'historical':
                d = df_old[(df_old['window'] == window) & (df_old['mech'] == mech)]
                n = df_new[(df_new['window'] == window) & (df_new['mech'] == mech)]
                if len(d) and len(n):
                    dv, nv = d['sharpe'].iloc[0], n['sharpe'].iloc[0]
                    lines.append('| %s | %s | %.3f | %.3f | %+.3f |' % (window, mech, dv, nv, nv - dv))
            else:
                d = df_old[(df_old['window'] == window) & (df_old['mech'] == mech)]
                n = df_new[(df_new['window'] == window) & (df_new['mech'] == mech)]
                if len(d) and len(n):
                    dv, nv = d['sharpe'].mean(), n['sharpe'].mean()
                    lines.append('| %s (mean 5) | %s | %.3f | %.3f | %+.3f |' % (window, mech, dv, nv, nv - dv))
    lines.append('')

    lines.append('## Recent Sharpe per start\n')
    lines.append('| Start | Mech | default | tuned | delta |')
    lines.append('|---|---:|---:|---:|---:|')
    for mech in ['A', 'B']:
        for i in range(N_STARTS):
            d = df_old[(df_old['window'] == 'recent') & (df_old['mech'] == mech) & (df_old['start'] == i)]
            n = df_new[(df_new['window'] == 'recent') & (df_new['mech'] == mech) & (df_new['start'] == i)]
            if len(d) and len(n):
                dv, nv = d['sharpe'].iloc[0], n['sharpe'].iloc[0]
                lines.append('| %s | %s | %.3f | %.3f | %+.3f |'
                             % (start_label(i), mech, dv, nv, nv - dv))
    lines.append('')

    if df_old is not None:
        lines.append('## Recent alpha comparison (per mech)\n')
        lines.append('| Mech | default mean alpha | tuned mean alpha | default #pos/#sig | tuned #pos/#sig |')
        lines.append('|---|---:|---:|---:|---:|')
        for mech in ['A', 'B']:
            d = df_old[(df_old['window'] == 'recent') & (df_old['mech'] == mech)]
            n = df_new[(df_new['window'] == 'recent') & (df_new['mech'] == mech)]
            d_pos = sum(1 for a in d['alpha_ann'] if a > 0)
            n_pos = sum(1 for a in n['alpha_ann'] if a > 0)
            d_sig = sum(1 for a, p in zip(d['alpha_ann'], d['alpha_pval']) if p < 0.05)
            n_sig = sum(1 for a, p in zip(n['alpha_ann'], n['alpha_pval']) if p < 0.05)
            lines.append('| %s | %+.2f%% | %+.2f%% | %d / %d | %d / %d |'
                         % (mech, d['alpha_ann'].mean() * 100, n['alpha_ann'].mean() * 100,
                            d_pos, d_sig, n_pos, n_sig))
        lines.append('')

        lines.append('## Recent alpha per start (default vs tuned)\n')
        lines.append('| Start | Mech | default α | tuned α | Δ α | default Mkt-RF | tuned Mkt-RF | '
                     'default ST_Rev | tuned ST_Rev |')
        lines.append('|---|---:|---:|---:|---:|---:|---:|---:|---:|')
        for mech in ['A', 'B']:
            for i in range(N_STARTS):
                d = df_old[(df_old['window'] == 'recent') & (df_old['mech'] == mech) & (df_old['start'] == i)]
                n = df_new[(df_new['window'] == 'recent') & (df_new['mech'] == mech) & (df_new['start'] == i)]
                if len(d) and len(n):
                    drow, nrow = d.iloc[0], n.iloc[0]
                    lines.append('| %s | %s | %+.2f%% | %+.2f%% | %+.2f%% | %.2f | %.2f | %.2f | %.2f |'
                                 % (start_label(i), mech,
                                    drow['alpha_ann'] * 100, nrow['alpha_ann'] * 100,
                                    (nrow['alpha_ann'] - drow['alpha_ann']) * 100,
                                    drow['Mkt-RF_beta'], nrow['Mkt-RF_beta'],
                                    drow['ST_Rev_beta'], nrow['ST_Rev_beta']))
        lines.append('')

        lines.append('## Historical alpha comparison\n')
        lines.append('| Mech | default alpha | tuned alpha |')
        lines.append('|---|---:|---:|')
        for mech in ['A', 'B']:
            d = df_old[(df_old['window'] == 'historical') & (df_old['mech'] == mech)]
            n = df_new[(df_new['window'] == 'historical') & (df_new['mech'] == mech)]
            if len(d) and len(n):
                lines.append('| %s | %+.2f%% | %+.2f%% |'
                             % (mech, d['alpha_ann'].iloc[0] * 100, n['alpha_ann'].iloc[0] * 100))
        lines.append('')

    lines.append('Note: tuned recent mean uses the same 5 aligned starts; historical is single-window.\n')
    out_path = os.path.join(OUT, '_FF_COMPARE_%s_vs_default.md' % TAG)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('wrote', out_path)


def main():
    os.makedirs(OUT, exist_ok=True)
    if not REPORTS_ONLY:
        fig_recent(PARAMS)
        fig_historical(PARAMS)
        fig_weights(PARAMS)
        fig_equity_weight(PARAMS)
    else:
        print('reports-only: skipping plot generation')

    if not PLOTS_ONLY:
        df_new = run_ff_md()
        write_compare(df_new)
    else:
        print('plots-only: skipping FF report generation')
    print('done')


if __name__ == '__main__':
    main()
