from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


def plot_equity_and_drawdown(bt: pd.DataFrame, outdir: str = "outputs", title_suffix: str = "") -> None:
    Path(outdir).mkdir(parents=True, exist_ok=True)

    # Equity curve
    plt.figure(figsize=(14, 6))
    plt.plot(bt.index, bt["PortfolioValue"], label="Strategy")
    plt.plot(bt.index, bt["BH_Portfolio"], label="Buy & Hold")
    plt.title(f"Equity Curve {title_suffix}".strip())
    plt.legend()
    plt.tight_layout()
    plt.savefig(Path(outdir) / "equity_curve.png", dpi=200)
    plt.close()

    # Drawdown
    strat_dd = bt["PortfolioValue"] / bt["PortfolioValue"].cummax() - 1
    bh_dd = bt["BH_Portfolio"] / bt["BH_Portfolio"].cummax() - 1

    plt.figure(figsize=(14, 4))
    plt.plot(bt.index, strat_dd, label="Strategy Drawdown")
    plt.plot(bt.index, bh_dd, label="Buy & Hold Drawdown")
    plt.title(f"Drawdown {title_suffix}".strip())
    plt.legend()
    plt.tight_layout()
    plt.savefig(Path(outdir) / "drawdown.png", dpi=200)
    plt.close()


def plot_trades_with_indicators(bt: pd.DataFrame, outdir: str = "outputs", lookback_bars: int = 300) -> None:
    Path(outdir).mkdir(parents=True, exist_ok=True)

    view = bt.tail(lookback_bars).copy()

    plt.figure(figsize=(16, 7))
    plt.plot(view.index, view["Close"], label="Close")
    plt.plot(view.index, view["Supertrend"], label="Supertrend")
    plt.plot(view.index, view["EMA20"], label="EMA20")
    plt.plot(view.index, view["SatStop"], label="Satellite ATR Stop")

    entries = view.dropna(subset=["ExecEntryOpen"])
    exits = view.dropna(subset=["ExecExitOpen"])

    if len(entries) > 0:
        plt.scatter(entries.index, entries["ExecEntryOpen"], marker="^", label="Entry (Exec @ Open)")
    if len(exits) > 0:
        plt.scatter(exits.index, exits["ExecExitOpen"], marker="v", label="Exit (Exec @ Open)")

    plt.title(f"Trades + Indicators (last {lookback_bars} bars)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(Path(outdir) / "trades_indicators.png", dpi=200)
    plt.close()