import numpy as np
import pandas as pd


def run_backtest(signals: pd.DataFrame, params: dict) -> pd.DataFrame:
    bt = signals.copy()

    initial = params["initial_capital"]
    core_w = params["core_weight"]
    sat_w = params["sat_weight"]

    # Trading frictions
    commission_pct = params.get("commission_pct", 0.0)
    slippage_pct = params.get("slippage_pct", 0.0)
    trade_cost_pct = commission_pct + slippage_pct

    # Next-day execution
    bt["SatEnterNext"] = bt["SatEntry"].shift(1).fillna(False)
    bt["SatExitNext"] = bt["SatExit"].shift(1).fillna(False)

    # Core allocation at first open
    core_cash = initial * core_w
    sat_cash = initial * sat_w

    first_open = float(bt["Open"].iloc[0])
    core_shares = core_cash / first_open
    core_cash = 0.0

    sat_shares = 0.0
    sat_in = False

    equity_curve = []
    sat_pos_curve = []

    exec_entry_px = [np.nan] * len(bt)
    exec_exit_px = [np.nan] * len(bt)

    trade_cost_dollars = [0.0] * len(bt)
    cumulative_trade_cost_dollars = [0.0] * len(bt)
    running_trade_costs = 0.0

    for i in range(len(bt)):
        o = float(bt["Open"].iloc[i])
        c = float(bt["Close"].iloc[i])

        # Exit at open
        if sat_in and bool(bt["SatExitNext"].iloc[i]):
            gross_exit_value = sat_shares * o
            exit_cost = gross_exit_value * trade_cost_pct
            sat_cash = gross_exit_value - exit_cost

            sat_shares = 0.0
            sat_in = False
            exec_exit_px[i] = o

            trade_cost_dollars[i] += exit_cost
            running_trade_costs += exit_cost

        # Entry at open
        if (not sat_in) and bool(bt["SatEnterNext"].iloc[i]):
            # Spend available sat_cash, but lose a % to trading friction
            entry_cost = sat_cash * trade_cost_pct
            dollars_invested = sat_cash - entry_cost

            if dollars_invested > 0:
                sat_shares = dollars_invested / o
                sat_cash = 0.0
                sat_in = True
                exec_entry_px[i] = o

                trade_cost_dollars[i] += entry_cost
                running_trade_costs += entry_cost

        core_value = core_shares * c
        sat_value = sat_cash + sat_shares * c
        total_equity = core_value + sat_value

        equity_curve.append(total_equity)
        sat_pos_curve.append(1 if sat_in else 0)
        cumulative_trade_cost_dollars[i] = running_trade_costs

    bt["PortfolioValue"] = equity_curve
    bt["SatIn_BT"] = sat_pos_curve
    bt["Ret"] = bt["PortfolioValue"].pct_change().fillna(0.0)

    # Benchmark (100% buy-and-hold)
    bt["BH_Portfolio"] = initial * (bt["Close"] / bt["Close"].iloc[0])
    bt["BH_Ret"] = bt["Close"].pct_change().fillna(0.0)

    # Store executed prices (for plotting)
    bt["ExecEntryOpen"] = exec_entry_px
    bt["ExecExitOpen"] = exec_exit_px

    # Cost tracking
    bt["TradeCost_$"] = trade_cost_dollars
    bt["CumTradeCost_$"] = cumulative_trade_cost_dollars

    return bt