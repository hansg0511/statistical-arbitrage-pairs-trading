import subprocess, json, os, sys
from datetime import datetime

START_DATES = ['2023-12-01', '2023-12-15', '2024-01-01', '2024-01-15', '2024-02-01']
END = '2026-01-01'
BASE_DIR = 'diagnosis/02_earnings_screen_baseline'
EARNINGS_CACHE = 'research/earnings_cache/earnings_dates.pkl'
SUMMARY_PATH = os.path.join(BASE_DIR, 'findings.md')
os.makedirs(BASE_DIR, exist_ok=True)

results = []

for sd in START_DATES:
    for screen in [False, True]:
        label = 'screen' if screen else 'noscreen'
        out_dir = os.path.join(BASE_DIR, f'{sd}_{label}')
        os.makedirs(out_dir, exist_ok=True)

        cmd = [
            sys.executable, 'run_backtest_parallel.py',
            '--profile', 'baseline',
            '--start', sd,
            '--end', END,
            '--output', out_dir,
        ]
        if screen:
            cmd.extend(['--earnings_screen', '--earnings_block_days', '7', '--earnings_cache', EARNINGS_CACHE])
        else:
            cmd.extend(['--no-earnings_screen', '--earnings_block_days', '0'])

        print(f"\n{'='*60}")
        print(f"Running: start={sd}, screen={'ON' if screen else 'OFF'}")
        print(f"{'='*60}")

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        print(result.stdout)
        if result.returncode != 0:
            print("STDERR:", result.stderr[-2000:] if result.stderr else "N/A")

        metrics_path = os.path.join(out_dir, 'metrics.json')
        if os.path.exists(metrics_path):
            with open(metrics_path) as f:
                m = json.load(f)
            results.append({
                'start': sd,
                'screen': screen,
                'return_pct': round(m.get('annualized_return', 0) * 100, 2),
                'sharpe': round(m.get('annualized_sharpe', 0), 2),
                'trades': m.get('total_trades', 0),
                'mean_at': round(m.get('mean_active_trades', 0), 2),
            })
            print(f"  -> Return={results[-1]['return_pct']}%, Sharpe={results[-1]['sharpe']}, Trades={results[-1]['trades']}, AT={results[-1]['mean_at']}")
        else:
            print(f"  -> WARNING: no metrics.json at {metrics_path}")

# Write findings
lines = []
lines.append("# Step 3: Earnings Screen Impact on Baseline\n")
lines.append(f"**Profile:** baseline (same_sector, slide=3m, sel=2m, test=3m, pct=0.18, log_space=True)\n")
lines.append(f"**Block days:** 7 | **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
lines.append("## Results\n")
lines.append("| Start Date | Screen | Ann. Return % | Sharpe | Trades | Mean AT |")
lines.append("|------------|--------|--------------|--------|--------|---------|")

for r in results:
    screen_label = 'ON (+7d)' if r['screen'] else 'OFF'
    lines.append(f"| {r['start']} | {screen_label} | {r['return_pct']} | {r['sharpe']} | {r['trades']} | {r['mean_at']} |")

lines.append("")
no_screen = [r for r in results if not r['screen']]
screen_on = [r for r in results if r['screen']]

if no_screen and screen_on:
    lines.append("## Aggregate Comparison\n")
    lines.append("| Metric | No Screen | Screen +7d | Delta |")
    lines.append("|--------|-----------|------------|-------|")
    ns_ret = round(sum(r['return_pct'] for r in no_screen) / len(no_screen), 2)
    sn_ret = round(sum(r['return_pct'] for r in screen_on) / len(screen_on), 2)
    ns_sh = round(sum(r['sharpe'] for r in no_screen) / len(no_screen), 2)
    sn_sh = round(sum(r['sharpe'] for r in screen_on) / len(screen_on), 2)
    ns_tr = round(sum(r['trades'] for r in no_screen) / len(no_screen), 1)
    sn_tr = round(sum(r['trades'] for r in screen_on) / len(screen_on), 1)
    ns_at = round(sum(r['mean_at'] for r in no_screen) / len(no_screen), 2)
    sn_at = round(sum(r['mean_at'] for r in screen_on) / len(screen_on), 2)
    lines.append(f"| Mean Return % | {ns_ret} | {sn_ret} | {round(sn_ret - ns_ret, 2)} |")
    lines.append(f"| Mean Sharpe | {ns_sh} | {sn_sh} | {round(sn_sh - ns_sh, 2)} |")
    lines.append(f"| Mean Trades | {ns_tr} | {sn_tr} | {round(sn_tr - ns_tr, 1)} |")
    lines.append(f"| Mean Active Trades | {ns_at} | {sn_at} | {round(sn_at - ns_at, 2)} |")

    lines.append("")
    std_ns_sh = round(__import__('statistics').stdev(r['sharpe'] for r in no_screen), 2)
    std_sn_sh = round(__import__('statistics').stdev(r['sharpe'] for r in screen_on), 2)
    lines.append("## Stability Comparison\n")
    lines.append(f"| Metric | No Screen | Screen +7d |")
    lines.append(f"|--------|-----------|------------|")
    lines.append(f"| Sharpe Std | {std_ns_sh} | {std_sn_sh} |")
    lines.append(f"| Sharpe Range | [{min(r['sharpe'] for r in no_screen)}, {max(r['sharpe'] for r in no_screen)}] | [{min(r['sharpe'] for r in screen_on)}, {max(r['sharpe'] for r in screen_on)}] |")

os.makedirs(os.path.dirname(SUMMARY_PATH), exist_ok=True)
with open(SUMMARY_PATH, 'w') as f:
    f.write('\n'.join(lines) + '\n')

print(f"\n{'='*60}")
print(f"Findings written to {SUMMARY_PATH}")
print(f"{'='*60}")
