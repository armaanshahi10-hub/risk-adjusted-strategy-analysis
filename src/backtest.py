import numpy as np
import pandas as pd


def run_backtest(signals: pd.DataFrame, params: dict) -> pd.DataFrame:
    bt = signals.copy()

    initial = params["initial_capital"]
    core_w = params["core_weight"]
    sat_w = params["sat_weight"]

    # Next-day execution
    bt["SatEnterNext"] = bt["SatEntry"].shift(1).fillna(False)
    bt["SatExitNext"] = bt["SatExit"].shift(1).fillna(False)

    # Core allocation at first open
    core_cash = initial * core_w
    sat_cash = initial * sat_w

    core_shares = core_cash / float(bt["Open"].iloc[0])
    core_cash = 0.0

    sat_shares = 0.0
    sat_in = False

    equity_curve = []
    sat_pos_curve = []

    exec_entry_px = [np.nan] * len(bt)
    exec_exit_px = [np.nan] * len(bt)

    for i in range(len(bt)):
        o = float(bt["Open"].iloc[i])
        c = float(bt["Close"].iloc[i])

        # Exit at open
        if sat_in and bool(bt["SatExitNext"].iloc[i]):
            sat_cash = sat_shares * o
            sat_shares = 0.0
            sat_in = False
            exec_exit_px[i] = o

        # Entry at open
        if (not sat_in) and bool(bt["SatEnterNext"].iloc[i]):
            sat_shares = sat_cash / o
            sat_cash = 0.0
            sat_in = True
            exec_entry_px[i] = o

        core_value = core_shares * c
        sat_value = sat_cash + sat_shares * c
        total_equity = core_value + sat_value

        equity_curve.append(total_equity)
        sat_pos_curve.append(1 if sat_in else 0)

    bt["PortfolioValue"] = equity_curve
    bt["SatIn_BT"] = sat_pos_curve
    bt["Ret"] = bt["PortfolioValue"].pct_change().fillna(0.0)

    # Benchmark (100% buy & hold)
    bt["BH_Portfolio"] = initial * (bt["Close"] / bt["Close"].iloc[0])
    bt["BH_Ret"] = bt["Close"].pct_change().fillna(0.0)

    # Store executed prices (for plotting)
    bt["ExecEntryOpen"] = exec_entry_px
    bt["ExecExitOpen"] = exec_exit_px

    return bt