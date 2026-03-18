import pandas as pd

from src.data import get_clean_data
from src.indicators import add_indicators
from src.signals import generate_signals
from src.backtest import run_backtest
from src.metrics import summarize_performance

BASE_PARAMS = {
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

TICKERS = ["SPY", "QQQ", "IWM", "EFA", "TLT", "GLD"]

TRAIN_START = "2010-01-01"
TRAIN_END = "2018-12-31"
TEST_START = "2019-01-01"
TEST_END = "2024-12-31"

WARMUP_DAYS = 550


def run_one_period(
    ticker: str,
    start: str,
    end: str,
    params: dict,
    warmup_days: int = WARMUP_DAYS,
) -> dict:
    start_dt = pd.to_datetime(start)
    warmup_start = (start_dt - pd.Timedelta(days=warmup_days)).strftime("%Y-%m-%d")

    local_params = params.copy()
    local_params["ticker"] = ticker
    local_params["start_date"] = warmup_start
    local_params["end_date"] = end
    local_params["trade_start_date"] = start

    raw = get_clean_data(ticker, local_params["start_date"], local_params["end_date"])
    feat = add_indicators(raw, local_params)
    sig = generate_signals(feat, local_params)

    # Evaluate only the visible period, but after indicators/signals had warmup history
    sig_eval = sig.loc[start:end].copy()

    bt = run_backtest(sig_eval, local_params)
    stats = summarize_performance(bt)

    result = {
        "Ticker": ticker,
        "Start": start,
        "End": end,
        "FinalValue_Strategy": stats.get("FinalValue_Strategy"),
        "FinalValue_BH": stats.get("FinalValue_BH"),
        "CAGR_Strategy": stats.get("CAGR_Strategy"),
        "CAGR_BH": stats.get("CAGR_BH"),
        "MaxDD_Strategy": stats.get("MaxDD_Strategy"),
        "MaxDD_BH": stats.get("MaxDD_BH"),
        "Vol_Strategy": stats.get("Vol_Strategy"),
        "Vol_BH": stats.get("Vol_BH"),
        "Sharpe_Strategy": stats.get("Sharpe_Strategy"),
        "Sharpe_BH": stats.get("Sharpe_BH"),
        "Sat_Entries": stats.get("Sat_Entries"),
        "Sat_Exits": stats.get("Sat_Exits"),
        "Sat_TimeInMarket": stats.get("Sat_TimeInMarket"),
        "TotalTradeCosts_$": float(bt["CumTradeCost_$"].iloc[-1]) if "CumTradeCost_$" in bt.columns else 0.0,
    }
    return result


def run_universe(period_name: str, start: str, end: str, tickers: list[str], params: dict) -> pd.DataFrame:
    results = []

    print(f"\n===== {period_name.upper()} MULTI-ASSET TEST =====")
    print(f"Period: {start} → {end}\n")

    for ticker in tickers:
        try:
            row = run_one_period(ticker, start, end, params)
            results.append(row)

            print(f"{ticker}:")
            print(f"  FinalValue_Strategy: ${row['FinalValue_Strategy']:,.2f}")
            print(f"  FinalValue_BH:       ${row['FinalValue_BH']:,.2f}")
            print(f"  CAGR_Strategy:       {row['CAGR_Strategy']:.2%}")
            print(f"  CAGR_BH:             {row['CAGR_BH']:.2%}")
            print(f"  Sharpe_Strategy:     {row['Sharpe_Strategy']:.3f}")
            print(f"  Sharpe_BH:           {row['Sharpe_BH']:.3f}")
            print(f"  MaxDD_Strategy:      {row['MaxDD_Strategy']:.2%}")
            print(f"  MaxDD_BH:            {row['MaxDD_BH']:.2%}")
            print(f"  TradeCosts:          ${row['TotalTradeCosts_$']:,.2f}")
            print()
        except Exception as e:
            print(f"{ticker}: FAILED -> {e}\n")

    out = pd.DataFrame(results)

    if not out.empty:
        print("===== SUMMARY =====")
        print(
            out[
                [
                    "Ticker",
                    "CAGR_Strategy",
                    "CAGR_BH",
                    "Sharpe_Strategy",
                    "Sharpe_BH",
                    "MaxDD_Strategy",
                    "MaxDD_BH",
                    "TotalTradeCosts_$",
                ]
            ].to_string(index=False)
        )

    return out


def main():
    train_df = run_universe("Train", TRAIN_START, TRAIN_END, TICKERS, BASE_PARAMS)
    test_df = run_universe("Test", TEST_START, TEST_END, TICKERS, BASE_PARAMS)

    if not train_df.empty:
        train_df.to_csv("outputs/multi_asset_train_results.csv", index=False)

    if not test_df.empty:
        test_df.to_csv("outputs/multi_asset_test_results.csv", index=False)

    if not train_df.empty:
        print("\n===== TRAIN AVERAGES =====")
        print(f"Avg CAGR_Strategy:   {train_df['CAGR_Strategy'].mean():.2%}")
        print(f"Avg CAGR_BH:         {train_df['CAGR_BH'].mean():.2%}")
        print(f"Avg Sharpe_Strategy: {train_df['Sharpe_Strategy'].mean():.3f}")
        print(f"Avg Sharpe_BH:       {train_df['Sharpe_BH'].mean():.3f}")
        print(f"Avg MaxDD_Strategy:  {train_df['MaxDD_Strategy'].mean():.2%}")
        print(f"Avg MaxDD_BH:        {train_df['MaxDD_BH'].mean():.2%}")

    if not test_df.empty:
        print("\n===== TEST AVERAGES =====")
        print(f"Avg CAGR_Strategy:   {test_df['CAGR_Strategy'].mean():.2%}")
        print(f"Avg CAGR_BH:         {test_df['CAGR_BH'].mean():.2%}")
        print(f"Avg Sharpe_Strategy: {test_df['Sharpe_Strategy'].mean():.3f}")
        print(f"Avg Sharpe_BH:       {test_df['Sharpe_BH'].mean():.3f}")
        print(f"Avg MaxDD_Strategy:  {test_df['MaxDD_Strategy'].mean():.2%}")
        print(f"Avg MaxDD_BH:        {test_df['MaxDD_BH'].mean():.2%}")


if __name__ == "__main__":
    main()