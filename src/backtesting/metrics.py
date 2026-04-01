from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class BacktestResult:
    cagr: float
    sharpe: float
    max_drawdown: float
    equity_curve: pd.DataFrame


def run_signal_backtest(history_path: Path) -> BacktestResult | None:
    """Run a simple daily signal strategy on snapshot history.

    Signal: fundamental_score >= 4 and sentiment_score > 0.2
    Daily return proxy: average day_change_pct/100 of selected names.
    """
    csv_fallback = history_path.with_suffix(".csv")
    if not history_path.exists() and not csv_fallback.exists():
        return None

    if history_path.exists():
        df = pd.read_parquet(history_path)
    else:
        df = pd.read_csv(csv_fallback)
    if df.empty:
        return None

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["daily_ret"] = pd.to_numeric(df["day_change_pct"], errors="coerce") / 100.0

    signal = (df["fundamental_score"] >= 4) & (df["sentiment_score"] > 0.2)
    signal_df = df[signal].copy()
    if signal_df.empty:
        return None

    port = (
        signal_df.groupby("date", as_index=False)["daily_ret"]
        .mean()
        .sort_values("date")
        .dropna(subset=["daily_ret"])
    )
    if port.empty:
        return None

    port["equity"] = (1.0 + port["daily_ret"]).cumprod()
    curve = port[["date", "daily_ret", "equity"]].copy()

    n_days = len(curve)
    years = max(n_days / 252.0, 1e-9)
    cagr = float(curve["equity"].iloc[-1] ** (1 / years) - 1)

    daily_mean = float(curve["daily_ret"].mean())
    daily_std = float(curve["daily_ret"].std(ddof=1))
    sharpe = float((daily_mean / daily_std) * np.sqrt(252)) if daily_std > 0 else 0.0

    running_max = curve["equity"].cummax()
    drawdown = curve["equity"] / running_max - 1.0
    max_drawdown = float(drawdown.min())

    return BacktestResult(cagr=cagr, sharpe=sharpe, max_drawdown=max_drawdown, equity_curve=curve)
