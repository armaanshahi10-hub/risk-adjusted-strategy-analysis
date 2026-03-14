import pandas as pd

from src.data import get_clean_data
from src.indicators import add_indicators
from src.signals import generate_signals
from src.backtest import run_backtest
from src.metrics import summarize_performance
from src.plots import plot_equity_and_drawdown, plot_trades_with_indicators


BASE_PARAMS = {
    "ticker": "SPY",
    "supertrend_len": 14,
    "supertrend_mult": 3,
    "atr_len": 14,
    "ema_span": 20,
    "wait_bars": 2,
    "atr_mult": 2.5,
    "trail_stop_pct": 0.15,
    "recent_n": 10,
    "vol_ma_n": 20,
    "vol_mult": 1.10,
    "initial_capital": 10000,
    "core_weight": 0.30,
    "sat_weight": 0.70,
    "commission_pct": 0.0005,
    "slippage_pct": 0.0005,
}


def run_period(name: str, start: str, end: str, warmup_days: int = 550):
    start_dt = pd.to_datetime(start)
    warmup_start = (start_dt - pd.Timedelta(days=warmup_days)).strftime("%Y-%m-%d")

    params = dict(BASE_PARAMS)
    params["start_date"] = warmup_start
    params["end_date"] = end
    params["trade_start_date"] = start  # <-- trades only allowed from 'start'

    raw = get_clean_data(params["ticker"], params["start_date"], params["end_date"])
    feat = add_indicators(raw, params)

    sig = generate_signals(feat, params)

    # Slice to the actual evaluation window for backtest + plots
    sig_eval = sig.loc[start:end].copy()

    bt = run_backtest(sig_eval, params)
    stats = summarize_performance(bt)

    print(f"\n===== {name.upper()} PERFORMANCE ({start} → {end}) =====")
    for k, v in stats.items():
        if "Value" in k:
            print(f"{k}: ${v:,.2f}")
        elif ("CAGR" in k) or ("MaxDD" in k) or ("Vol" in k) or ("Time" in k):
            print(f"{k}: {v:.2%}")
        else:
            print(f"{k}: {v}")

    outdir = f"outputs/{name}"
    plot_equity_and_drawdown(bt, outdir=outdir, title_suffix=f"({start} → {end})")
    plot_trades_with_indicators(bt, outdir=outdir, lookback_bars=300)

    return stats


def main():
    # Train / Test split
    train_stats = run_period("train", "2010-01-01", "2018-12-31")
    test_stats = run_period("test", "2019-01-01", "2024-12-31")

    # Optional: print a quick side-by-side headline comparison
    print("\n===== HEADLINE COMPARISON =====")
    print(f"Train MaxDD: {train_stats['MaxDD_Strategy']:.2%} | Test MaxDD: {test_stats['MaxDD_Strategy']:.2%}")
    print(f"Train Sharpe: {train_stats['Sharpe_Strategy']:.2f} | Test Sharpe: {test_stats['Sharpe_Strategy']:.2f}")


if __name__ == "__main__":
    main()