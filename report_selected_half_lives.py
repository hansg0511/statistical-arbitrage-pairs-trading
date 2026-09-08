"""Summarize log half lives of pairs selected by completed baseline runs."""

import argparse
import os

import pandas as pd


THRESHOLDS = (20, 60, 120, 252, 504)


def markdown_table(frame):
    columns = list(frame.columns)
    lines = [
        '| ' + ' | '.join(columns) + ' |',
        '| ' + ' | '.join('---' for _ in columns) + ' |',
    ]
    for row in frame.itertuples(index=False, name=None):
        values = []
        for value in row:
            if isinstance(value, float):
                values.append(f'{value:.2f}')
            else:
                values.append(str(value).replace('|', '\\|'))
        lines.append('| ' + ' | '.join(values) + ' |')
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='fixed_diagnosis')
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()

    paths = []
    for section in ('06', '07', '08a', '08b', '09a', '09b', '10a', '10b'):
        section_dir = os.path.join(args.root, section)
        if not os.path.isdir(section_dir):
            continue
        for run_name in os.listdir(section_dir):
            path = os.path.join(section_dir, run_name, 'selected_pairs.csv')
            if os.path.isfile(path):
                paths.append((section, run_name, path))

    if not paths:
        parser.error(f'no selected_pairs.csv files found under {args.root}')
    if not os.path.isdir(args.output_dir):
        parser.error(f'output directory does not exist: {args.output_dir}')

    frames = []
    for section, run_name, path in paths:
        frame = pd.read_csv(path)
        frame['section'] = section
        frame['run'] = run_name
        frames.append(frame)
    pairs = pd.concat(frames, ignore_index=True)
    pairs['half_life_log'] = pd.to_numeric(pairs['half_life_log'], errors='coerce')
    pairs = pairs[pairs['half_life_log'].notna() & (pairs['half_life_log'] > 0)].copy()

    pair_path = os.path.join(args.output_dir, 'selected_half_lives.csv')
    pairs.sort_values('half_life_log', ascending=False).to_csv(pair_path, index=False)

    fold_stats = pairs.groupby(['section', 'run', 'fold_id'], as_index=False).agg(
        selected_pairs=('pair', 'size'),
        mean_half_life_log=('half_life_log', 'mean'),
        median_half_life_log=('half_life_log', 'median'),
        max_half_life_log=('half_life_log', 'max'),
    )
    for threshold in THRESHOLDS:
        fold_stats[f'pairs_over_{threshold}d'] = pairs.assign(
            over=pairs['half_life_log'] > threshold
        ).groupby(['section', 'run', 'fold_id'])['over'].sum().to_numpy()
    fold_path = os.path.join(args.output_dir, 'selected_half_life_by_fold.csv')
    fold_stats.to_csv(fold_path, index=False)

    sections = pairs.groupby('section')['half_life_log'].agg(
        selected_pair_observations='size', mean='mean', median='median', max='max'
    )
    sections['mean_top20_half_life'] = fold_stats.groupby('section')[
        'mean_half_life_log'
    ].mean()
    sections['median_top20_half_life'] = fold_stats.groupby('section')[
        'median_half_life_log'
    ].mean()

    lines = [
        '# Selected Log Half-Life Report',
        '',
        f'Input root: `{args.root}`',
        f'Selected-pair observations: {len(pairs):,}; completed selection folds: {len(fold_stats):,}.',
        '',
        '## Overall',
        '',
        f"- Mean selected-pair log half life: {pairs['half_life_log'].mean():.2f} trading days.",
        f"- Median selected-pair log half life: {pairs['half_life_log'].median():.2f} trading days.",
        f"- Mean of each fold's selected-pair mean: {fold_stats['mean_half_life_log'].mean():.2f} trading days.",
        f"- Maximum selected log half life: {pairs['half_life_log'].max():.2f} trading days.",
    ]
    for threshold in THRESHOLDS:
        count = (pairs['half_life_log'] > threshold).sum()
        lines.append(f'- Above {threshold} days: {count:,} ({count / len(pairs):.2%}).')
    lines.extend([
        '', '## By Section', '',
        markdown_table(sections.reset_index().round(2)), '',
    ])
    high = pairs.nlargest(25, 'half_life_log')[
        ['section', 'run', 'fold_id', 'rank', 'pair', 'half_life_log',
         'cointegration_pvalue_log']
    ].copy()
    lines.extend(['## 25 Highest Selected Half Lives', '', markdown_table(high), ''])
    report_path = os.path.join(args.output_dir, 'selected_half_life_report.md')
    with open(report_path, 'w', encoding='ascii') as handle:
        handle.write('\n'.join(lines))
    print(f'Wrote {report_path}')


if __name__ == '__main__':
    main()
