import pandas as pd
import yfinance as yf


def get_clean_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    df = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True, progress=False)

    # yfinance can return a MultiIndex in some cases
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.columns = [str(c).strip().title() for c in df.columns]

    need = ["Open", "High", "Low", "Close", "Volume"]
    missing = [c for c in need if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns {missing}. Have: {list(df.columns)}")

    df = df[need].copy()
    df[need] = df[need].apply(pd.to_numeric, errors="coerce")
    df.index = pd.to_datetime(df.index).normalize()
    df = df.dropna()

    return df