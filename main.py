from src.data import get_clean_data
from src.indicators import add_indicators
from src.signals import generate_signals
from src.backtest import run_backtest
from src.metrics import summarize_performance
from src.plots import plot_equity_and_drawdown, plot_trades_with_indicators

PARAMS = {
    "ticker": "SPY",
    "start_date": "2010-01-01", 
    "end_date": "2018-12-31",

    "supertrend_len": 14,
    "supertrend_mult": 3,
    "atr_len": 14,
    "ema_span": 20,

    "wait_bars": 2,
    "atr_mult": 2.5,

    # NEW: 15% trailing stop from highest close since entry
    "trail_stop_pct": 0.15,

    "recent_n": 10,
    "vol_ma_n": 20,
    "vol_mult": 1.10,

    "initial_capital": 10000,
    "core_weight": 0.30,
    "sat_weight": 0.70,
}

def main():
    raw = get_clean_data(PARAMS["ticker"], PARAMS["start_date"], PARAMS["end_date"])
    feat = add_indicators(raw, PARAMS)
    sig = generate_signals(feat, PARAMS)
    bt = run_backtest(sig, PARAMS)

    stats = summarize_performance(bt)

    print("\n===== TRAINING PERFORMANCE (ATR stop vs 15% trailing stop — tighter stop wins) =====")
    for k, v in stats.items():
        if "Value" in k:
            print(f"{k}: ${v:,.2f}")
        elif ("CAGR" in k) or ("MaxDD" in k) or ("Vol" in k) or ("Time" in k):
            print(f"{k}: {v:.2%}")
        else:
            print(f"{k}: {v}")

    plot_equity_and_drawdown(bt, outdir="outputs", title_suffix=f"({PARAMS['start_date']} → {PARAMS['end_date']})")
    plot_trades_with_indicators(bt, outdir="outputs", lookback_bars=300)

if __name__ == "__main__":
    main()