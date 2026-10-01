import pandas as pd
import numpy as np

from research.run_transaction_cost_analysis import (
    _break_even_bps,
    _net_path,
    _returns_from_equity,
)


def test_zero_cost_reconstructs_gross_equity_and_returns():
    daily = pd.DataFrame(
        {
            "pnl": [0.0, 100.0, -50.0],
            "total_capital": [1_000_000.0, 1_000_100.0, 1_000_050.0],
            "daily_return": [0.0, 0.0001, -0.00004999500049995],
        },
        index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
    )
    cost_basis = pd.Series(0.0, index=daily.index)
    gross_pnl, net_pnl, net_equity = _net_path(daily, cost_basis, 0)

    assert gross_pnl.tolist() == [0.0, 100.0, -50.0]
    assert net_pnl.equals(gross_pnl)
    assert net_equity.tolist() == [1_000_000.0, 1_000_100.0, 1_000_050.0]
    assert np.allclose(
        _returns_from_equity(net_equity).to_numpy(),
        daily["daily_return"].to_numpy(),
        atol=1e-15,
    )


def test_break_even_bps_uses_entry_and_exit_turnover():
    assert _break_even_bps(10_000.0, 2_000_000.0) == 50.0
