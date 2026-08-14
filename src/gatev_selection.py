import pandas as pd
import numpy as np


class GatevSelector:
    """
    Gatev (2006) distance-based pair selection.
    Selects pairs whose normalized prices have the smallest
    sum of squared differences (SSD) over the formation period.
    Discards pairs whose cumulative return difference exceeds
    `max_return_divergence` (Gatev original filter).
    """

    def __init__(self, top_k: int = 20, max_return_divergence: float = 0.10):
        self.top_k = top_k
        self.max_return_divergence = max_return_divergence

    def select_pairs(self, close_prices: pd.DataFrame, sel_start: str, sel_end: str) -> pd.DataFrame:
        sel_data = close_prices.loc[sel_start:sel_end]

        norm_prices = sel_data / sel_data.iloc[0]
        arr = norm_prices.values.astype(np.float64)

        T, N = arr.shape
        squared_norms = (arr ** 2).sum(axis=0)
        dot_product = arr.T @ arr
        ssd_matrix = squared_norms[:, None] + squared_norms[None, :] - 2 * dot_product

        triu_idx = np.triu_indices(N, k=1)
        triu_ssd = ssd_matrix[triu_idx]
        top_n = min(self.top_k * 10, len(triu_ssd))

        if top_n <= 0:
            return pd.DataFrame(columns=['pair', 'ssd', 'correlation'])

        top_idx = np.argpartition(triu_ssd, top_n)[:top_n]
        top_ordering = np.argsort(triu_ssd[top_idx])
        top_idx = top_idx[top_ordering]

        pairs_i = triu_idx[0][top_idx]
        pairs_j = triu_idx[1][top_idx]
        tickers = sorted(sel_data.columns)

        last_row = arr[-1, :]
        returns = last_row - 1.0

        rows = []
        for idx_i, idx_j in zip(pairs_i, pairs_j):
            t1, t2 = tickers[idx_i], tickers[idx_j]
            if abs(returns[idx_i] - returns[idx_j]) > self.max_return_divergence:
                continue
            ssd = float(ssd_matrix[idx_i, idx_j])
            corr = float(np.corrcoef(arr[:, idx_i], arr[:, idx_j])[0, 1])
            rows.append({'pair': f'{t1}-{t2}', 'ssd': ssd, 'correlation': corr})

        df = pd.DataFrame(rows)
        return df.sort_values('ssd').head(self.top_k)
