import numpy as np
import pandas as pd


def generate_signals(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    out = df.copy()

    WAIT_BARS = params["wait_bars"]
    RECENT_N = params["recent_n"]
    VOL_MA_N = params["vol_ma_n"]
    VOL_MULT = params["vol_mult"]
    ATR_MULT = params["atr_mult"]

    out["VolMA"] = out["Volume"].rolling(VOL_MA_N).mean()

    # Supertrend flips bullish
    out["BullFlip"] = (out["SupertrendDir"] == 1) & (out["SupertrendDir"].shift(1) == -1)

    # Setup tracking
    out["SetupActive"] = False
    out["SetupHigh"] = np.nan
    out["SetupStart"] = -1
    out["Eligible"] = False

    active = False
    setup_high = None
    start_i = None

    for i in range(len(out)):
        if out["BullFlip"].iloc[i]:
            active = True
            setup_high = out["High"].iloc[i]  # reversal candle high
            start_i = i

        # cancel setup if trend flips bearish before entry
        if out["SupertrendDir"].iloc[i] == -1:
            active = False
            setup_high = None
            start_i = None

        out.iloc[i, out.columns.get_loc("SetupActive")] = active
        if active:
            out.iloc[i, out.columns.get_loc("SetupHigh")] = setup_high
            out.iloc[i, out.columns.get_loc("SetupStart")] = start_i
            out.iloc[i, out.columns.get_loc("Eligible")] = (i >= start_i + WAIT_BARS)

    # Base entry (post-wait breakout)
    out["LongEntry"] = (
        out["SetupActive"]
        & out["Eligible"]
        & (out["High"] > out["SetupHigh"])
        & (out["SupertrendDir"] == 1)
    )

    # Re-entry conditions
    out["RecentHigh"] = out["High"].rolling(RECENT_N).max()
    out["VolSpike"] = out["Volume"] > (VOL_MULT * out["VolMA"])
    out["LongReEntryCond"] = (
        (out["High"] > out["RecentHigh"].shift(1)) & out["VolSpike"] & (out["SupertrendDir"] == 1)
    )

    # Satellite state machine (long-only)
    out["SatEntry"] = False
    out["SatExit"] = False
    out["SatInPos"] = False
    out["SatStop"] = np.nan
    out["SatHighestClose"] = np.nan

    sat_in = False
    highest_close = None
    stop = None
    allow_reentry = False

    for i in range(len(out)):
        close = float(out["Close"].iloc[i])
        atr = float(out["ATR"].iloc[i])
        dir_ = int(out["SupertrendDir"].iloc[i])
        ema20 = float(out["EMA20"].iloc[i])

        # Manage existing satellite position
        if sat_in:
            highest_close = max(highest_close, close)
            stop = highest_close - ATR_MULT * atr

            stop_hit = close <= stop
            trend_flip = (dir_ == -1)

            # Momentum filter: only exit on stop if close < EMA20
            momentum_weak = close < ema20

            if trend_flip or (stop_hit and momentum_weak):
                out.iloc[i, out.columns.get_loc("SatExit")] = True
                sat_in = False
                highest_close = None
                stop = None
                allow_reentry = (dir_ == 1)

        # Entry / Re-entry when flat
        if not sat_in:
            if bool(out["LongEntry"].iloc[i]):
                out.iloc[i, out.columns.get_loc("SatEntry")] = True
                sat_in = True
                highest_close = close
                stop = highest_close - ATR_MULT * atr
                allow_reentry = False

            elif allow_reentry and bool(out["LongReEntryCond"].iloc[i]):
                out.iloc[i, out.columns.get_loc("SatEntry")] = True
                sat_in = True
                highest_close = close
                stop = highest_close - ATR_MULT * atr
                allow_reentry = False

        # Record state
        out.iloc[i, out.columns.get_loc("SatInPos")] = sat_in
        out.iloc[i, out.columns.get_loc("SatStop")] = stop if stop is not None else np.nan
        out.iloc[i, out.columns.get_loc("SatHighestClose")] = (
            highest_close if highest_close is not None else np.nan
        )

    return out