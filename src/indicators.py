import pandas as pd
import pandas_ta as ta


def add_indicators(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    out = df.copy()

    ta_df = pd.DataFrame(index=out.index)
    ta_df["high"] = out["High"]
    ta_df["low"] = out["Low"]
    ta_df["close"] = out["Close"]

    ta_df.ta.supertrend(length=params["supertrend_len"], multiplier=params["supertrend_mult"], append=True)
    ta_df.ta.atr(length=params["atr_len"], append=True)

    out = out.join(ta_df.drop(columns=["high", "low", "close"]), how="left")

    # Robust rename (pandas_ta column names can vary)
    def pick(prefix: str):
        matches = [c for c in out.columns if c.startswith(prefix)]
        return matches[0] if matches else None

    st_line = pick("SUPERT_")
    st_dir = pick("SUPERTd_")
    atr_col = pick("ATR_") or pick("ATRr_")

    rename_map = {}
    if st_line:
        rename_map[st_line] = "Supertrend"
    if st_dir:
        rename_map[st_dir] = "SupertrendDir"
    if atr_col:
        rename_map[atr_col] = "ATR"

    out.rename(columns=rename_map, inplace=True)

    # EMA momentum filter
    out["EMA20"] = out["Close"].ewm(span=params["ema_span"], adjust=False).mean()

    must_have = ["Open", "High", "Low", "Close", "Volume", "Supertrend", "SupertrendDir", "ATR", "EMA20"]
    out = out.dropna(subset=must_have)

    # Normalize direction to +1/-1
    out["SupertrendDir"] = out["SupertrendDir"].apply(lambda x: 1 if x > 0 else -1)

    return out