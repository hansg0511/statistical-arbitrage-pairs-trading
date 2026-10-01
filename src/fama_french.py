import io
import zipfile
import pickle
import pandas as pd
import numpy as np
import statsmodels.api as sm
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from urllib.request import urlopen


MONTHLY_URLS = {
    'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_txt.zip': [
        'Mkt-RF', 'SMB', 'HML', 'RF'],
    'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_txt.zip': [
        'Mom'],
    'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_ST_Reversal_Factor_txt.zip': [
        'ST_Rev'],
}

DAILY_URLS = {
    'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_daily_txt.zip': [
        'Mkt-RF', 'SMB', 'HML', 'RF'],
    'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_daily_txt.zip': [
        'Mom'],
    'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_ST_Reversal_Factor_daily_txt.zip': [
        'ST_Rev'],
}


@dataclass
class FFResult:
    alpha: float
    alpha_ann: float
    alpha_tstat: float
    alpha_pval: float
    loadings: pd.DataFrame
    rsquared: float
    adj_rsquared: float
    n_obs: int
    residuals: pd.Series
    monthly_returns: pd.Series
    factors_used: pd.DataFrame
    frequency: str = 'monthly'

    def summary(self) -> str:
        period_label = 'Daily' if self.frequency == 'daily' else 'Monthly'
        factor_label = '252' if self.frequency == 'daily' else '12'
        obs_label = 'days' if self.frequency == 'daily' else 'months'
        lines = [
            'Fama-French 3-Factor + Momentum + ST_Reversal Regression',
            f'{"=" * 65}',
            f'  {period_label} Alpha:    {self.alpha:+.4%}',
            f'  Annualized (x{factor_label}): {self.alpha_ann:+.2%}',
            f'  Alpha t-stat:     {self.alpha_tstat:.3f}',
            f'  Alpha p-value:    {self.alpha_pval:.4f}',
            f'',
            f'  R-squared:  {self.rsquared:.4f}',
            f'  Adj R-squared: {self.adj_rsquared:.4f}',
            f'  Observations: {self.n_obs} {obs_label}',
            f'',
            f'  Loadings (HAC standard errors):',
            f'  {"Factor":<12} {"Beta":>10} {"t-stat":>8} {"p-value":>8}',
            f'  {"-"*12} {"-"*10} {"-"*8} {"-"*8}',
        ]
        for _, row in self.loadings.iterrows():
            lines.append(
                f'  {row["factor"]:<12} {row["beta"]:>10.4f} '
                f'{row["tstat"]:>8.3f} {row["pval"]:>8.4f}'
            )
        return '\n'.join(lines)


class FamaFrenchFetcher:
    def __init__(
        self,
        cache_dir: str = 'research/ff_factors',
        frequency: str = 'monthly',
        snapshot_path: Optional[str] = None,
    ):
        self.frequency = frequency
        self._snapshot_path = Path(snapshot_path) if snapshot_path else None
        self._cache_dir = Path(cache_dir)
        if self._snapshot_path is None:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
        suffix = 'daily' if frequency == 'daily' else 'monthly'
        self._cache_path = self._cache_dir / f'ff_{suffix}.pkl'
        self._factors: Optional[pd.DataFrame] = None

    def fetch(self, force: bool = False) -> pd.DataFrame:
        if self._factors is not None and not force:
            return self._factors

        if self._snapshot_path is not None:
            if not self._snapshot_path.is_file():
                raise FileNotFoundError(f'Fama-French snapshot not found: {self._snapshot_path}')
            index_name = 'date' if self.frequency == 'daily' else 'month'
            frame = pd.read_csv(self._snapshot_path, parse_dates=[index_name])
            required = {'Mkt-RF', 'SMB', 'HML', 'RF'}
            if self.frequency == 'daily':
                required.update({'Mom', 'ST_Rev'})
            missing = required.difference(frame.columns)
            if missing:
                raise ValueError(f'Fama-French snapshot is missing columns: {sorted(missing)}')
            if frame[index_name].duplicated().any():
                raise ValueError(f'Fama-French snapshot has duplicate {index_name} values')
            frame = frame.set_index(index_name).sort_index()
            if not np.isfinite(frame[list(required)].to_numpy(dtype=float)).all():
                raise ValueError('Fama-French snapshot contains non-finite values')
            self._factors = frame
            return self._factors

        if self._cache_path.exists() and not force:
            with open(self._cache_path, 'rb') as f:
                self._factors = pickle.load(f)
            return self._factors

        url_map = DAILY_URLS if self.frequency == 'daily' else MONTHLY_URLS
        frames = []
        for url, col_names in url_map.items():
            df = self._download_and_parse(url, col_names)
            if df is not None:
                frames.append(df)

        if not frames:
            raise RuntimeError(f'Failed to download Fama-French {self.frequency} data.')

        merged = frames[0]
        for df in frames[1:]:
            merged = merged.join(df, how='outer')

        idx_name = 'date' if self.frequency == 'daily' else 'month'
        merged.index = merged.index.rename(idx_name)
        merged = merged.sort_index()

        with open(self._cache_path, 'wb') as f:
            pickle.dump(merged, f)

        self._factors = merged
        return self._factors

    def _download_and_parse(self, url: str, col_names: list[str]) -> Optional[pd.DataFrame]:
        try:
            resp = urlopen(url, timeout=30)
            raw = resp.read()
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                txt_name = [n for n in z.namelist() if n.endswith('.txt')]
                if not txt_name:
                    return None
                with z.open(txt_name[0]) as f:
                    text = f.read().decode('utf-8')
        except Exception:
            return None

        is_daily = '_daily_' in url
        idx_name = 'date' if is_daily else 'month'
        records = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            parts = stripped.split()
            date_str = parts[0]
            if len(date_str) == 8 and is_daily:
                try:
                    dt = pd.Timestamp(date_str)
                    if dt.month < 1 or dt.month > 12:
                        continue
                    vals = [float(x) for x in parts[1:1 + len(col_names)]]
                    if any(v < -90 for v in vals):
                        continue
                    records.append((dt, *vals))
                except (ValueError, IndexError):
                    continue
            elif len(date_str) == 6 and not is_daily:
                try:
                    yr = int(date_str[:4])
                    mo = int(date_str[4:6])
                    if mo < 1 or mo > 12:
                        continue
                    period = pd.Period(year=yr, month=mo, freq='M')
                    vals = [float(x) for x in parts[1:1 + len(col_names)]]
                    if any(v < -90 for v in vals):
                        continue
                    records.append((period, *vals))
                except (ValueError, IndexError):
                    continue
            else:
                continue

        if not records:
            return None

        df = pd.DataFrame.from_records(
            records, columns=[idx_name] + col_names)
        df = df.set_index(idx_name)
        for c in col_names:
            df[c] = df[c] / 100.0
        return df

    def regress(
        self,
        strategy_returns: pd.Series,
        include_momentum: bool = True,
        include_st_rev: bool = True,
        maxlags: Optional[int] = None,
    ) -> FFResult:
        is_daily = self.frequency == 'daily'
        factors = self.fetch()

        if is_daily:
            strat = strategy_returns[strategy_returns != 0].copy()
            strat.index = pd.to_datetime(strat.index)
        else:
            strat = strategy_returns.resample('M').apply(
                lambda r: (1 + r).prod() - 1)
            strat.index = strat.index.to_period('M')

        strategy_name = strategy_returns.name or 'Strategy'
        strat.name = strategy_name

        factor_cols = ['Mkt-RF', 'SMB', 'HML']
        if include_momentum and 'Mom' in factors.columns:
            factor_cols.append('Mom')
        if include_st_rev and 'ST_Rev' in factors.columns:
            factor_cols.append('ST_Rev')

        common_idx = strat.index.intersection(factors.index)
        if len(common_idx) < 6:
            label = 'days' if is_daily else 'months'
            raise ValueError(
                f'Only {len(common_idx)} overlapping {label}. Need at least 6.'
            )

        y = strat.loc[common_idx] - factors.loc[common_idx, 'RF']
        X = factors.loc[common_idx, factor_cols]
        X = sm.add_constant(X)

        combined = pd.concat([y, X], axis=1).dropna()
        y = combined.iloc[:, 0]
        X = combined.iloc[:, 1:]

        nobs = len(y)
        if nobs < 6:
            label = 'days' if is_daily else 'months'
            raise ValueError(f'Only {nobs} overlapping {label} after dropping NaNs. Need at least 6.')
        if maxlags is None:
            maxlags = int(nobs ** 0.25)

        model = sm.OLS(y.values.astype(float), X.values.astype(float))
        res = model.fit(cov_type='HAC', cov_kwds={'maxlags': maxlags})

        loadings_data = []
        for i, col in enumerate(X.columns):
            loadings_data.append({
                'factor': col,
                'beta': res.params[i],
                'tstat': res.tvalues[i],
                'pval': res.pvalues[i],
            })
        loadings_df = pd.DataFrame(loadings_data)

        alpha = res.params[0]
        annual_factor = 252 if is_daily else 12
        alpha_ann = alpha * annual_factor
        alpha_tstat = res.tvalues[0]
        alpha_pval = res.pvalues[0]

        resid_series = pd.Series(res.resid, index=y.index, name='residual')

        return FFResult(
            alpha=alpha,
            alpha_ann=alpha_ann,
            alpha_tstat=alpha_tstat,
            alpha_pval=alpha_pval,
            loadings=loadings_df,
            rsquared=res.rsquared,
            adj_rsquared=res.rsquared_adj,
            n_obs=nobs,
            residuals=resid_series,
            monthly_returns=strat.loc[y.index],
            factors_used=X,
            frequency=self.frequency,
        )
