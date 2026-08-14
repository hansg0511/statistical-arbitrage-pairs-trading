import subprocess, json, os, sys
from datetime import datetime

START_DATES = ['2023-12-01', '2023-12-15', '2024-01-01', '2024-01-15', '2024-02-01']
END = '2026-01-01'
BASE_DIR = 'diagnosis/sweep_earnings'
EARNINGS_CACHE = 'research/earnings_cache/earnings_dates.pkl'
SUMMARY_PATH = os.path.join(BASE_DIR, 'summary.md')

results = []

for sd in START_DATES:
    for screen in [True, False]:
        label = 'screen' if screen else 'noscreen'
        out_dir = os.path.join(BASE_DIR, f'{sd}_{label}')
        os.makedirs(out_dir, exist_ok=True)

        cmd = [
            sys.executable, 'run_backtest_parallel.py',
            '--profile', 'golden',
            '--start', sd,
            '--end', END,
            '--output', out_dir,
            '--earnings_cache', EARNINGS_CACHE,
        ]
        if not screen:
            cmd.extend(['--no-earnings_screen', '--earnings_block_days', '0'])

        print(f"\n{'='*60}")
        print(f"Running: start={sd}, screen={'ON' if screen else 'OFF'}")
        print(f"{'='*60}")

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr[:500])

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
            })
            print(f"  → Return={results[-1]['return_pct']}%, Sharpe={results[-1]['sharpe']}, Trades={results[-1]['trades']}")
        else:
            print(f"  → WARNING: no metrics.json at {metrics_path}")

# Write summary
lines = []
lines.append("# Earnings Screen Sweep — Golden Profile\n")
lines.append(f"**Universe:** core | **Fold settings:** sel=2m, test=3m, slide=1m | **Block days:** 7\n")
lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
lines.append("| Start Date | Screen | Ann. Return % | Sharpe | Trades |")
lines.append("|------------|--------|--------------|--------|--------|")

for r in results:
    screen_label = 'ON (+7d)' if r['screen'] else 'OFF'
    lines.append(f"| {r['start']} | {screen_label} | {r['return_pct']} | {r['sharpe']} | {r['trades']} |")

lines.append("")
no_screen = [r for r in results if not r['screen']]
screen_on = [r for r in results if r['screen']]

if no_screen and screen_on:
    lines.append("## Summary\n")
    lines.append("| Metric | No Screen | Screen +7d |")
    lines.append("|--------|-----------|------------|")
    ns_ret = round(sum(r['return_pct'] for r in no_screen) / len(no_screen), 2)
    sn_ret = round(sum(r['return_pct'] for r in screen_on) / len(screen_on), 2)
    ns_sh = round(sum(r['sharpe'] for r in no_screen) / len(no_screen), 2)
    sn_sh = round(sum(r['sharpe'] for r in screen_on) / len(screen_on), 2)
    ns_tr = round(sum(r['trades'] for r in no_screen) / len(no_screen), 1)
    sn_tr = round(sum(r['trades'] for r in screen_on) / len(screen_on), 1)
    lines.append(f"| Mean Return % | {ns_ret} | {sn_ret} |")
    lines.append(f"| Mean Sharpe | {ns_sh} | {sn_sh} |")
    lines.append(f"| Mean Trades | {ns_tr} | {sn_tr} |")

os.makedirs(os.path.dirname(SUMMARY_PATH), exist_ok=True)
with open(SUMMARY_PATH, 'w') as f:
    f.write('\n'.join(lines) + '\n')

print(f"\n{'='*60}")
print(f"Summary written to {SUMMARY_PATH}")
print(f"{'='*60}")
