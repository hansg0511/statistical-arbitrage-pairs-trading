"""Pure transaction-cost calculations used by the TCA overlay and tests."""

from __future__ import annotations

import pandas as pd


INITIAL_CAPITAL = 1_000_000.0


def _net_path(
    daily: pd.DataFrame,
    cost_basis: pd.Series,
    cost_bps: float,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Return gross PnL, net PnL, and net equity for one cost scenario."""
    gross_pnl = daily["pnl"].astype(float)
    daily_cost = cost_basis.reindex(gross_pnl.index).fillna(0.0) * (cost_bps / 10_000.0)
    net_pnl = gross_pnl - daily_cost
    net_equity = INITIAL_CAPITAL + net_pnl.cumsum()
    if (net_equity <= 0).any():
        raise ValueError(f"non-positive net equity at {cost_bps} bps")
    return gross_pnl, net_pnl, net_equity


def _returns_from_equity(equity: pd.Series) -> pd.Series:
    previous = equity.shift(1).fillna(INITIAL_CAPITAL)
    return equity.div(previous).sub(1.0)


def _break_even_bps(gross_pnl: float, total_traded_notional: float) -> float:
    """Interpolate the one-way rate where final net PnL reaches zero."""
    if gross_pnl <= 0 or total_traded_notional <= 0:
        return float("nan")
    return float(gross_pnl / total_traded_notional * 10_000.0)
