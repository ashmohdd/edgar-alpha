from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf
import pandas_market_calendars as mcal


def next_trading_day(date: pd.Timestamp, exchange: str = "NYSE") -> pd.Timestamp:
    cal = mcal.get_calendar(exchange)
    schedule = cal.schedule(start_date=date, end_date=date + pd.Timedelta(days=10))
    days = schedule.index
    for d in days:
        if d >= date:
            return pd.Timestamp(d)
    return pd.Timestamp(days[-1])


def load_signal(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["filing_date"])
    return df.sort_values("filing_date")


def add_forward_return(df: pd.DataFrame, horizon_days: int = 5) -> pd.DataFrame:
    t = df["ticker"].iloc[0]
    start = df["filing_date"].min() - pd.Timedelta(days=30)
    end = df["filing_date"].max() + pd.Timedelta(days=30)

    px = yf.download(t, start=start.date(), end=end.date(), progress=False)
    if px.empty:
        raise SystemExit(f"No price data from yfinance for {t}")

    px = px.reset_index().rename(columns={"Date": "date"})
    px["date"] = pd.to_datetime(px["date"]).dt.tz_localize(None)

    # map each filing to next trading day close, then compute +N day forward return
    closes = px[["date", "Close"]].copy().sort_values("date")

    def _close_on(d: pd.Timestamp) -> float:
        # choose next available trading day
        d2 = next_trading_day(d)
        row = closes[closes["date"] >= d2].head(1)
        if row.empty:
            return float("nan")
        return float(row.iloc[0]["Close"])

    df = df.copy()
    df["px0"] = df["filing_date"].apply(_close_on)

    def _close_plus_n(d: pd.Timestamp) -> float:
        d2 = next_trading_day(d) + pd.Timedelta(days=horizon_days)
        row = closes[closes["date"] >= d2].head(1)
        if row.empty:
            return float("nan")
        return float(row.iloc[0]["Close"])

    df["pxn"] = df["filing_date"].apply(_close_plus_n)
    df["fwd_ret"] = df["pxn"] / df["px0"] - 1.0
    return df


def information_coefficient(df: pd.DataFrame) -> float:
    d = df.dropna(subset=["signal_z", "fwd_ret"]).copy()
    if len(d) < 3:
        return float("nan")
    return float(np.corrcoef(d["signal_z"], d["fwd_ret"])[0, 1])


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ticker", required=True)
    p.add_argument("--signal", default="data/processed/signal.csv")
    p.add_argument("--out", default="data/processed/eval.csv")
    args = p.parse_args()

    sig = load_signal(Path(args.signal))
    sig = add_forward_return(sig, horizon_days=5)

    ic = information_coefficient(sig)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sig.to_csv(out, index=False)

    print(f"Wrote {out}")
    print(f"IC (signal vs +5D forward return): {ic:.3f}")


if __name__ == "__main__":
    main()
