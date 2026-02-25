import numpy as np
import pandas as pd


def generate_signals(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    out = df.copy()

    WAIT_BARS = params["wait_bars"]
    RECENT_N = params["recent_n"]
    VOL_MA_N = params["vol_ma_n"]
    VOL_MULT = params["vol_mult"]

    ATR_MULT = params["atr_mult"]
    TRAIL_STOP_PCT = params.get("trail_stop_pct", 0.15)

    # NEW: trades are only allowed on/after this date
    trade_start_date = params.get("trade_start_date", None)
    if trade_start_date is not None:
        trade_start_date = pd.to_datetime(trade_start_date)

    out["VolMA"] = out["Volume"].rolling(VOL_MA_N).mean()
    out["BullFlip"] = (out["SupertrendDir"] == 1) & (out["SupertrendDir"].shift(1) == -1)

    # Setup tracking
    out["SetupActive"] = False
    out["SetupHigh"] = np.nan
    out["SetupStart"] = -1
    out["Eligible"] = False

    # Base + re-entry conditions
    out["RecentHigh"] = out["High"].rolling(RECENT_N).max()
    out["VolSpike"] = out["Volume"] > (VOL_MULT * out["VolMA"])
    out["LongEntry"] = False
    out["LongReEntryCond"] = False

    # Satellite outputs
    out["SatEntry"] = False
    out["SatExit"] = False
    out["SatInPos"] = False
    out["SatStop"] = np.nan
    out["SatHighestClose"] = np.nan

    # --- State variables ---
    active = False
    setup_high = None
    start_i = None

    sat_in = False
    highest_close = None
    stop = None
    allow_reentry = False

    started_trading = False  # flips True once we cross trade_start_date

    for i in range(len(out)):
        dt = out.index[i]

        # Enforce "no trading before start date" AND reset state at the start boundary
        if trade_start_date is not None and (dt < trade_start_date):
            # stay flat; do not build setups; do not carry state
            active = False
            setup_high = None
            start_i = None

            sat_in = False
            highest_close = None
            stop = None
            allow_reentry = False

            # record state (flat)
            out.iloc[i, out.columns.get_loc("SetupActive")] = False
            out.iloc[i, out.columns.get_loc("Eligible")] = False
            out.iloc[i, out.columns.get_loc("SatInPos")] = False
            out.iloc[i, out.columns.get_loc("SatStop")] = np.nan
            out.iloc[i, out.columns.get_loc("SatHighestClose")] = np.nan
            continue

        if trade_start_date is not None and (not started_trading) and (dt >= trade_start_date):
            # Hard reset exactly at the boundary once
            active = False
            setup_high = None
            start_i = None

            sat_in = False
            highest_close = None
            stop = None
            allow_reentry = False

            started_trading = True

        close = float(out["Close"].iloc[i])
        high = float(out["High"].iloc[i])
        atr = float(out["ATR"].iloc[i])
        dir_ = int(out["SupertrendDir"].iloc[i])
        ema20 = float(out["EMA20"].iloc[i])

        # --- Setup logic (bull flip -> wait -> breakout) ---
        if bool(out["BullFlip"].iloc[i]):
            active = True
            setup_high = high
            start_i = i

        # cancel setup if bearish before entry
        if dir_ == -1:
            active = False
            setup_high = None
            start_i = None

        out.iloc[i, out.columns.get_loc("SetupActive")] = active
        if active:
            out.iloc[i, out.columns.get_loc("SetupHigh")] = setup_high
            out.iloc[i, out.columns.get_loc("SetupStart")] = start_i
            out.iloc[i, out.columns.get_loc("Eligible")] = (i >= start_i + WAIT_BARS)
        else:
            out.iloc[i, out.columns.get_loc("Eligible")] = False

        long_entry = (
            active
            and bool(out["Eligible"].iloc[i])
            and (high > float(out["SetupHigh"].iloc[i]))
            and (dir_ == 1)
        )
        out.iloc[i, out.columns.get_loc("LongEntry")] = long_entry

        long_reentry = (
            (high > float(out["RecentHigh"].shift(1).iloc[i]))
            and bool(out["VolSpike"].iloc[i])
            and (dir_ == 1)
        )
        out.iloc[i, out.columns.get_loc("LongReEntryCond")] = long_reentry

        # --- Manage open satellite position ---
        if sat_in:
            highest_close = max(highest_close, close)

            atr_stop = highest_close - ATR_MULT * atr
            pct_trail_stop = highest_close * (1 - TRAIL_STOP_PCT)

            # "whichever hits first" => tighter stop wins (higher stop price)
            stop = max(atr_stop, pct_trail_stop)

            stop_hit = close <= stop
            trend_flip = (dir_ == -1)
            momentum_weak = close < ema20

            if trend_flip or (stop_hit and momentum_weak):
                out.iloc[i, out.columns.get_loc("SatExit")] = True
                sat_in = False
                highest_close = None
                stop = None
                allow_reentry = (dir_ == 1)

        # --- Entry / re-entry when flat ---
        if not sat_in:
            if long_entry:
                out.iloc[i, out.columns.get_loc("SatEntry")] = True
                sat_in = True
                highest_close = close

                atr_stop = highest_close - ATR_MULT * atr
                pct_trail_stop = highest_close * (1 - TRAIL_STOP_PCT)
                stop = max(atr_stop, pct_trail_stop)

                allow_reentry = False

            elif allow_reentry and long_reentry:
                out.iloc[i, out.columns.get_loc("SatEntry")] = True
                sat_in = True
                highest_close = close

                atr_stop = highest_close - ATR_MULT * atr
                pct_trail_stop = highest_close * (1 - TRAIL_STOP_PCT)
                stop = max(atr_stop, pct_trail_stop)

                allow_reentry = False

        # record satellite state
        out.iloc[i, out.columns.get_loc("SatInPos")] = sat_in
        out.iloc[i, out.columns.get_loc("SatStop")] = stop if stop is not None else np.nan
        out.iloc[i, out.columns.get_loc("SatHighestClose")] = highest_close if highest_close is not None else np.nan

    return out