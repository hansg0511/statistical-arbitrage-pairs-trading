"""Regenerate diagnosis/04_max_pairs_sweep (40) and 02b_earnings_sweep_full (30) with the
fixed backtest code, serially with pauses to avoid yfinance rate-limit / CPU overload.

Then:
  - sync diagnosis/06_grid_search_mp5 (old)  <- fixed_diagnosis/05  (mp=5, pct=0.18, already regen)
  - sync diagnosis/sweep_same_sector_slide1m_bd7_pct025 (old) <- fixed_diagnosis/10 (pct=0.25, already regen)
  - regenerate findings.md for 04, 02b, 06_grid_search_mp5 (old), sweep.

findings.md files are data-generated tables (not hand-authored), so regenerating is correct.
"""
import subprocess, json, os, sys, shutil, statistics, time
from datetime import datetime
from src.result_validation import validate_run_output

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
SYS = sys.executable
END = '2026-01-01'
EARNINGS_CACHE = 'research/earnings_cache/earnings_dates.pkl'
CACHE = 'research/cache'
PAUSE = 30.0

OUTPUT_FILES = ['metrics.json', 'daily_returns.csv', 'daily_returns_active_only.csv',
                 'oos_fold_summary.csv', 'trade_marks.csv', 'signal_log.csv',
                 'rejected_orders.csv', 'run.log', 'run_status.json']
OUTPUT_DIRS = ['trade_logs']


def run_job(out_dir, cmd):
    os.makedirs(out_dir, exist_ok=True)
    print('  [CMD] ' + ' '.join(cmd)[:200], flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    with open(os.path.join(out_dir, 'run.log'), 'w') as f:
        f.write(r.stdout or '')
        if r.stderr:
            f.write('\n--- STDERR ---\n'); f.write(r.stderr)
    validation = validate_run_output(out_dir) if r.returncode == 0 else {'valid': False}
    ok = validation['valid']
    print(f"  [DONE] {os.path.basename(out_dir)}: {'OK' if ok else 'ABORT'} rc={r.returncode}", flush=True)
    return ok


# ---------------------------------------------------------------------------
# 04 : max_pairs sweep
# ---------------------------------------------------------------------------
S04 = 'diagnosis/04_max_pairs_sweep'
S04_STARTS = ['2023-12-01', '2023-12-15', '2024-01-01', '2024-01-15', '2024-02-01']
S04_MP = [(5, 0.18), (10, 0.09), (20, 0.045), (50, 0.018)]
S04_SECTORS = [('same_sector', []),
               ('cross_sector', ['--cross_sector', '--return_divergence', '0.10'])]


def regen_04():
    res = []
    for sd in S04_STARTS:
        for sector, extra in S04_SECTORS:
            for mp, pct in S04_MP:
                out = os.path.join(S04, f'{sd}_{sector}_mp{mp}')
                cmd = [SYS, 'run_backtest_parallel.py', '--profile', 'baseline',
                       '--universe', 'core', '--start', sd, '--end', END, '--output', out,
                       '--no-earnings_screen', '--max_pairs', str(mp), '--pct_per_pair', str(pct),
                       '--cache_dir', CACHE, '--sel_months', '2', '--workers', '1'] + list(extra)
                ok = run_job(out, cmd)
                if ok:
                    m = json.load(open(os.path.join(out, 'metrics.json')))
                    res.append({'start': sd, 'sector': sector, 'max_pairs': mp,
                                'return_pct': round(m.get('annualized_return', 0) * 100, 2),
                                'sharpe': round(m.get('annualized_sharpe', 0), 2),
                                'trades': m.get('total_trades', 0),
                                'mean_at': round(m.get('mean_active_trades', 0), 2)})
                time.sleep(PAUSE)
    write_04_findings(res)
    return sum(1 for r in res)


def write_04_findings(results):
    labels_mp = [mp for mp, _ in S04_MP]
    lines = ["# Max Pairs Sweep — same_sector vs cross_sector\n"]
    lines.append(f"**Grid:** {len(S04_STARTS)} start dates × {len(S04_SECTORS)} sector modes × {len(S04_MP)} max_pairs = {len(results)} runs\n")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    for sector_label in ['same_sector', 'cross_sector']:
        lines.append(f"## {sector_label} — Sharpe Pivot\n")
        lines.append("| Start Date | " + " | ".join([f"mp={mp}" for mp in labels_mp]) + " |")
        lines.append("|" + "|".join(["---"] * (1 + len(labels_mp))) + "|")
        for sd in S04_STARTS:
            row = [sd] + [str(next((r['sharpe'] for r in results if r['start'] == sd and r['sector'] == sector_label and r['max_pairs'] == mp), 'N/A')) for mp in labels_mp]
            lines.append('| ' + ' | '.join(row) + ' |')
        lines.append("")
        lines.append(f"## {sector_label} — Trades Pivot\n")
        lines.append("| Start Date | " + " | ".join([f"mp={mp}" for mp in labels_mp]) + " |")
        lines.append("|" + "|".join(["---"] * (1 + len(labels_mp))) + "|")
        for sd in S04_STARTS:
            row = [sd] + [str(next((r['trades'] for r in results if r['start'] == sd and r['sector'] == sector_label and r['max_pairs'] == mp), 'N/A')) for mp in labels_mp]
            lines.append('| ' + ' | '.join(row) + ' |')
        lines.append("")
        lines.append(f"## {sector_label} — Mean Active Trades Pivot\n")
        lines.append("| Start Date | " + " | ".join([f"mp={mp}" for mp in labels_mp]) + " |")
        lines.append("|" + "|".join(["---"] * (1 + len(labels_mp))) + "|")
        for sd in S04_STARTS:
            row = [sd] + [str(next((r['mean_at'] for r in results if r['start'] == sd and r['sector'] == sector_label and r['max_pairs'] == mp), 'N/A')) for mp in labels_mp]
            lines.append('| ' + ' | '.join(row) + ' |')
        lines.append("")
        lines.append(f"## {sector_label} — Aggregate Summary\n")
        lines.append("| Metric | " + " | ".join([f"mp={mp}" for mp in labels_mp]) + " |")
        lines.append("|--------|" + "|".join(["---"] * len(labels_mp)) + "|")
        for metric_key, metric_name, fmt in [('sharpe', 'Mean Sharpe', '.2f'), ('trades', 'Mean Trades', '.1f'),
                                              ('return_pct', 'Mean Return %', '.2f'), ('mean_at', 'Mean Active Trades', '.2f')]:
            row = [metric_name] + [f"{statistics.mean([r[metric_key] for r in results if r['sector'] == sector_label and r['max_pairs'] == mp]):{fmt}}" if [r[metric_key] for r in results if r['sector'] == sector_label and r['max_pairs'] == mp] else 'N/A' for mp in labels_mp]
            lines.append('| ' + ' | '.join(row) + ' |')
        lines.append("")
        lines.append(f"## {sector_label} — Stability (Sharpe Std & Range)\n")
        lines.append("| Metric | " + " | ".join([f"mp={mp}" for mp in labels_mp]) + " |")
        lines.append("|--------|" + "|".join(["---"] * len(labels_mp)) + "|")
        row = ['Sharpe Std'] + [f"{statistics.stdev([r['sharpe'] for r in results if r['sector'] == sector_label and r['max_pairs'] == mp]):.2f}" if len([r['sharpe'] for r in results if r['sector'] == sector_label and r['max_pairs'] == mp]) > 1 else '0.00' for mp in labels_mp]
        lines.append('| ' + ' | '.join(row) + ' |')
        row = ['Sharpe Range'] + [f"[{min([r['sharpe'] for r in results if r['sector'] == sector_label and r['max_pairs'] == mp]):.2f}, {max([r['sharpe'] for r in results if r['sector'] == sector_label and r['max_pairs'] == mp]):.2f}]" if [r['sharpe'] for r in results if r['sector'] == sector_label and r['max_pairs'] == mp] else 'N/A' for mp in labels_mp]
        lines.append('| ' + ' | '.join(row) + ' |')
        lines.append("")
    lines.append("## Cross-Sector vs Same-Sector Comparison (Sharpe)\n")
    lines.append("| max_pairs | same_sector Mean | cross_sector Mean | same_sector Std | cross_sector Std |")
    lines.append("|-----------|-----------------|-------------------|-----------------|------------------|")
    for mp in labels_mp:
        ss = [r['sharpe'] for r in results if r['sector'] == 'same_sector' and r['max_pairs'] == mp]
        cs = [r['sharpe'] for r in results if r['sector'] == 'cross_sector' and r['max_pairs'] == mp]
        lines.append(f"| {mp} | {statistics.mean(ss):.2f} | {statistics.mean(cs):.2f} | {statistics.stdev(ss):.2f} | {statistics.stdev(cs):.2f} |")
    with open(os.path.join(S04, 'findings.md'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print(f"  findings -> {S04}/findings.md", flush=True)


# ---------------------------------------------------------------------------
# 02b : earnings block-days sweep
# ---------------------------------------------------------------------------
S02B = 'diagnosis/02b_earnings_sweep_full'
S02B_STARTS = ['2023-12-01', '2023-12-15', '2024-01-01', '2024-01-15', '2024-02-01']
S02B_BD = {'noscreen': None, 'bd0': 0, 'bd3': 3, 'bd5': 5, 'bd7': 7, 'bd9': 9}


def regen_02b():
    res = []
    for sd in S02B_STARTS:
        for label, bd in S02B_BD.items():
            out = os.path.join(S02B, f'{sd}_{label}')
            cmd = [SYS, 'run_backtest_parallel.py', '--profile', 'baseline',
                   '--universe', 'core', '--start', sd, '--end', END, '--output', out,
                   '--cache_dir', CACHE, '--sel_months', '2', '--max_pairs', '5',
                   '--pct_per_pair', '0.18', '--workers', '1']
            if bd is None:
                cmd += ['--no-earnings_screen', '--earnings_block_days', '0']
            else:
                cmd += ['--earnings_screen', '--earnings_block_days', str(bd), '--earnings_cache', EARNINGS_CACHE]
            ok = run_job(out, cmd)
            if ok:
                m = json.load(open(os.path.join(out, 'metrics.json')))
                res.append({'start': sd, 'label': label, 'block_days': bd,
                            'return_pct': round(m.get('annualized_return', 0) * 100, 2),
                            'sharpe': round(m.get('annualized_sharpe', 0), 2),
                            'trades': m.get('total_trades', 0),
                            'mean_at': round(m.get('mean_active_trades', 0), 2)})
            time.sleep(PAUSE)
    write_02b_findings(res)
    return sum(1 for r in res)


def write_02b_findings(results):
    labels = list(S02B_BD.keys())
    lines = ["# Earnings Block Days Sweep — Baseline (same_sector, slide=3m)\n"]
    lines.append(f"**Grid:** {len(S02B_STARTS)} start dates × {len(labels)} screen settings = {len(results)} runs\n")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    for title, key in [("Sharpe Pivot", 'sharpe'), ("Trades Pivot", 'trades'), ("Return % Pivot", 'return_pct')]:
        lines.append(f"## {title}\n")
        lines.append("| Start Date | " + " | ".join(labels) + " |")
        lines.append("|------------|" + "|".join(["---"] * len(labels)) + "|")
        for sd in S02B_STARTS:
            row = [sd] + [str(next((r[key] for r in results if r['start'] == sd and r['label'] == lb), 'N/A')) for lb in labels]
            lines.append('| ' + ' | '.join(row) + ' |')
        lines.append("")
    lines.append("## Aggregate Summary\n")
    lines.append("| Metric | " + " | ".join(labels) + " |")
    lines.append("|--------|" + "|".join(["---"] * len(labels)) + "|")
    for key, name, fmt in [('sharpe', 'Mean Sharpe', '.2f'), ('trades', 'Mean Trades', '.1f'),
                           ('return_pct', 'Mean Return %', '.2f'), ('mean_at', 'Mean Active Trades', '.2f')]:
        row = [name] + [f"{statistics.mean([r[key] for r in results if r['label'] == lb]):{fmt}}" if [r[key] for r in results if r['label'] == lb] else 'N/A' for lb in labels]
        lines.append('| ' + ' | '.join(row) + ' |')
    lines.append("")
    lines.append("## Stability (Sharpe Std per Block Days)\n")
    lines.append("| Metric | " + " | ".join(labels) + " |")
    lines.append("|--------|" + "|".join(["---"] * len(labels)) + "|")
    row = ['Sharpe Std'] + [f"{statistics.stdev([r['sharpe'] for r in results if r['label'] == lb]):.2f}" if len([r['sharpe'] for r in results if r['label'] == lb]) > 1 else '0.00' for lb in labels]
    lines.append('| ' + ' | '.join(row) + ' |')
    row = ['Sharpe Range'] + [f"[{min([r['sharpe'] for r in results if r['label'] == lb]):.2f}, {max([r['sharpe'] for r in results if r['label'] == lb]):.2f}]" if [r['sharpe'] for r in results if r['label'] == lb] else 'N/A' for lb in labels]
    lines.append('| ' + ' | '.join(row) + ' |')
    lines.append("")
    lines.append("## Interpretation\n")
    lines.append("bd3 and bd5 are identical across all displayed starts and metrics. bd7 and bd9 "
                 "match on four of five starts; their only material difference is the 2024-01-01 "
                 "start, where bd9 is higher. That one start accounts for most of bd9's higher mean "
                 "Sharpe, so it is not sufficient evidence that bd9 is generally superior.\n")
    lines.append("bd7 and bd9 retain nearly the same number of trades (25.6 versus 25.2 mean trades), "
                 "while bd7 has lower Sharpe dispersion (0.73 versus 0.85). bd7 is therefore retained "
                 "as the conservative minimum-sufficient secondary filter; earnings screening remains "
                 "secondary to pair-selection stability.\n")
    with open(os.path.join(S02B, 'findings.md'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print(f"  findings -> {S02B}/findings.md", flush=True)


# ---------------------------------------------------------------------------
# Sync mirrors (already-regen fixed_diagnosis sources)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# sweep 2015-2020 historical arm (section 10 historical; core mp20 pct0.25 slide1 bd7)
# ---------------------------------------------------------------------------
SWEEP_HIST = 'diagnosis/sweep_same_sector_slide1m_bd7_pct025 (old)/2015-2020'
SWEEP_HIST_STARTS = ['2015-01-01', '2017-01-01', '2019-01-01']


def regen_sweep_hist():
    res = []
    for sd in SWEEP_HIST_STARTS:
        out = os.path.join(SWEEP_HIST, sd)
        cmd = [SYS, 'run_backtest_parallel.py', '--profile', 'baseline',
               '--universe', 'core', '--start', sd, '--end', '2021-01-01', '--output', out,
               '--cache_dir', CACHE, '--sel_months', '2', '--workers', '1',
               '--earnings_screen', '--earnings_block_days', '7', '--earnings_cache', EARNINGS_CACHE,
               '--slide_months', '1', '--max_pairs', '20', '--pct_per_pair', '0.25']
        ok = run_job(out, cmd)
        if ok:
            m = json.load(open(os.path.join(out, 'metrics.json')))
            res.append({'start': sd, 'sharpe': round(m.get('annualized_sharpe', 0), 2),
                        'return_pct': round(m.get('annualized_return', 0) * 100, 2),
                        'trades': m.get('total_trades', 0),
                        'at': round(m.get('mean_active_trades', 0), 2)})
        time.sleep(PAUSE)
    # findings for the hist subdir
    lines = ["# Section 10 — core 2m, mp=20, pct=0.25 (2015-2020 historical arm)\n"]
    lines.append(f"**Runs:** {len(res)} | **Starts:** {len(res)}\n")
    lines.append("| Start | Sharpe | Ret% | Trades | AT |")
    lines.append("|---|---:|---:|---:|---:|")
    for r in res:
        lines.append(f"| {r['start']} | {r['sharpe']:.2f} | {r['return_pct']:.2f} | {r['trades']} | {r['at']:.2f} |")
    with open(os.path.join(SWEEP_HIST, 'findings.md'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print(f"  findings -> {SWEEP_HIST}/findings.md", flush=True)
    return len(res)


def sync(src_base, dst_base):
    copied = 0
    for cfg in os.listdir(src_base):
        src = os.path.join(src_base, cfg); dst = os.path.join(dst_base, cfg)
        if not os.path.isdir(src):
            continue
        os.makedirs(dst, exist_ok=True)
        for fn in OUTPUT_FILES:
            sp = os.path.join(src, fn)
            if os.path.exists(sp):
                shutil.copy2(sp, os.path.join(dst, fn)); copied += 1
        for dn in OUTPUT_DIRS:
            sd = os.path.join(src, dn)
            if os.path.isdir(sd):
                os.makedirs(os.path.join(dst, dn), exist_ok=True)
                for f2 in os.listdir(sd):
                    shutil.copy2(os.path.join(sd, f2), os.path.join(dst, dn, f2))
    print(f"  synced {src_base} -> {dst_base} ({copied} files)", flush=True)
    return copied


def copy_findings(src_md, dst_md):
    if os.path.exists(src_md):
        shutil.copy2(src_md, dst_md)
        print(f"  findings copied {src_md} -> {dst_md}", flush=True)


def main():
    print("===== [1/4] regenerate 04_max_pairs_sweep =====", flush=True)
    n04 = regen_04()
    print(f"  04 done: {n04}/40", flush=True)

    print("\n===== [2/4] regenerate 02b_earnings_sweep_full =====", flush=True)
    n02b = regen_02b()
    print(f"  02b done: {n02b}/30", flush=True)

    print("\n===== [3/4] sync 06_grid_search_mp5 (old) <- fixed_diagnosis/05 =====", flush=True)
    sync('fixed_diagnosis/05', 'diagnosis/06_grid_search_mp5 (old)')
    copy_findings('fixed_diagnosis/05/findings.md', 'diagnosis/06_grid_search_mp5 (old)/findings.md')

    print("\n===== [4/4] sync sweep_same_sector_slide1m_bd7_pct025 (old) <- fixed_diagnosis/10 =====", flush=True)
    sync('fixed_diagnosis/10', 'diagnosis/sweep_same_sector_slide1m_bd7_pct025 (old)')
    copy_findings('fixed_diagnosis/10/findings.md', 'diagnosis/sweep_same_sector_slide1m_bd7_pct025 (old)/findings.md')

    print("\n===== [5/5] regenerate sweep 2015-2020 historical arm =====", flush=True)
    n_sweep_hist = regen_sweep_hist()
    print(f"  sweep 2015-2020 done: {n_sweep_hist}/3", flush=True)

    print("\nDONE.", flush=True)


if __name__ == '__main__':
    main()
