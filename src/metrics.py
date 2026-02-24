import numpy as np
import pandas as pd


def max_drawdown(series: pd.Series) -> float:
    peak = series.cummax()
    dd = series / peak - 1.0
    return float(dd.min())


def cagr(series: pd.Series, trading_days: int = 252) -> float:
    years = len(series) / trading_days
    if years <= 0:
        return 0.0
    return float((series.iloc[-1] / series.iloc[0]) ** (1 / years) - 1)


def ann_vol(ret: pd.Series, trading_days: int = 252) -> float:
    return float(ret.std(ddof=0) * np.sqrt(trading_days))


def sharpe(ret: pd.Series, trading_days: int = 252) -> float:
    vol = ret.std(ddof=0)
    if vol == 0:
        return 0.0
    return float(ret.mean() / vol * np.sqrt(trading_days))


def summarize_performance(bt: pd.DataFrame) -> dict:
    bt2 = bt.copy()
    bt2["SatChange"] = bt2["SatIn_BT"].diff().fillna(0)
    entries = int((bt2["SatChange"] == 1).sum())
    exits = int((bt2["SatChange"] == -1).sum())
    time_in = float(bt2["SatIn_BT"].mean())

    return {
        "FinalValue_Strategy": float(bt2["PortfolioValue"].iloc[-1]),
        "FinalValue_BH": float(bt2["BH_Portfolio"].iloc[-1]),
        "CAGR_Strategy": cagr(bt2["PortfolioValue"]),
        "CAGR_BH": cagr(bt2["BH_Portfolio"]),
        "MaxDD_Strategy": max_drawdown(bt2["PortfolioValue"]),
        "MaxDD_BH": max_drawdown(bt2["BH_Portfolio"]),
        "Vol_Strategy": ann_vol(bt2["Ret"]),
        "Vol_BH": ann_vol(bt2["BH_Ret"]),
        "Sharpe_Strategy": sharpe(bt2["Ret"]),
        "Sharpe_BH": sharpe(bt2["BH_Ret"]),
        "Sat_Entries": entries,
        "Sat_Exits": exits,
        "Sat_TimeInMarket": time_in,
    }