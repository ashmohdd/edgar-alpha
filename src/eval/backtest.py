from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf
import pandas_market_calendars as mcal

from src.storage.duckdb_store import connect, upsert_eval


def next_trading_day(date: pd.Timestamp, exchange: str = "NYSE") -> pd.Timestamp:
    cal = mcal.get_calendar(exchange)
    schedule = cal.schedule(start_date=date, end_date=date + pd.Timedelta(days=10))
    days = schedule.index
    for d in days:
        if d >= date:
            return pd.Timestamp(d)
    return pd.Timestamp(days[-1])


def load_features(ticker: str, db_path: Path) -> pd.DataFrame:
    con = connect(db_path)
    q = """
    SELECT * FROM features
    WHERE ticker = ?
    ORDER BY form, filing_date
    """
    df = con.execute(q, [ticker.upper()]).df()
    if df.empty:
        raise SystemExit("No features found in DuckDB. Run: make signal")
    df["filing_date"] = pd.to_datetime(df["filing_date"])
    return df


def add_forward_return(df: pd.DataFrame, horizon_days: int = 5) -> pd.DataFrame:
    t = df["ticker"].iloc[0]
    start = df["filing_date"].min() - pd.Timedelta(days=60)
    end = df["filing_date"].max() + pd.Timedelta(days=60)

    px = yf.download(t, start=start.date(), end=end.date(), progress=False)
    if px.empty:
        raise SystemExit(f"No price data from yfinance for {t}")

    px = px.reset_index().rename(columns={"Date": "date"})
    px["date"] = pd.to_datetime(px["date"]).dt.tz_localize(None)
    closes = px[["date", "Close"]].copy().sort_values("date")

    def _close_on(d: pd.Timestamp) -> float:
        d2 = next_trading_day(d)
        row = closes[closes["date"] >= d2].head(1)
        return float(row.iloc[0]["Close"]) if not row.empty else float("nan")

    def _close_plus_n(d: pd.Timestamp) -> float:
        d2 = next_trading_day(d) + pd.Timedelta(days=horizon_days)
        row = closes[closes["date"] >= d2].head(1)
        return float(row.iloc[0]["Close"]) if not row.empty else float("nan")

    out = df.copy()
    out["px0"] = out["filing_date"].apply(_close_on)
    out["pxn"] = out["filing_date"].apply(_close_plus_n)
    out["fwd_ret"] = out["pxn"] / out["px0"] - 1.0
    out["horizon_days"] = horizon_days
    return out


def information_coefficient(df: pd.DataFrame) -> float:
    d = df.dropna(subset=["signal_z", "fwd_ret"]).copy()
    if len(d) < 6:
        return float("nan")
    return float(np.corrcoef(d["signal_z"], d["fwd_ret"])[0, 1])


def assign_deciles(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["decile"] = np.nan
    for form, g in out.groupby("form"):
        d = g.dropna(subset=["signal_z"]).copy()
        if len(d) < 10:
            continue
        # decile 1=lowest, 10=highest
        d["decile"] = pd.qcut(d["signal_z"], 10, labels=False, duplicates="drop") + 1
        out.loc[d.index, "decile"] = d["decile"].astype(int)
    return out


def decile_spread(df: pd.DataFrame) -> pd.DataFrame:
    d = df.dropna(subset=["decile", "fwd_ret"]).copy()
    if d.empty:
        return pd.DataFrame(columns=["form", "decile", "mean_fwd_ret"])
    return d.groupby(["form", "decile"], as_index=False)["fwd_ret"].mean().rename(columns={"fwd_ret": "mean_fwd_ret"})


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ticker", required=True)
    p.add_argument("--db", default="data/processed/edgar_alpha.duckdb")
    p.add_argument("--out_eval", default="data/processed/eval.csv")
    p.add_argument("--horizon", type=int, default=5)
    args = p.parse_args()

    feats = load_features(args.ticker, Path(args.db))
    feats = add_forward_return(feats, horizon_days=args.horizon)
    feats = assign_deciles(feats)

    ic = information_coefficient(feats)
    spread = decile_spread(feats)

    # persist eval table (event-level)
    con = connect(Path(args.db))
    eval_cols = feats[["ticker", "form", "filing_date", "accession", "horizon_days", "fwd_ret", "decile"]].copy()
    eval_cols["filing_date"] = pd.to_datetime(eval_cols["filing_date"]).dt.date
    upsert_eval(con, eval_cols)

    Path(args.out_eval).parent.mkdir(parents=True, exist_ok=True)
    feats.to_csv(args.out_eval, index=False)

    # export decile chart data
    spread_out = Path("data/processed/decile_spread.csv")
    spread_out.parent.mkdir(parents=True, exist_ok=True)
    spread.to_csv(spread_out, index=False)

    print(f"Wrote {args.out_eval}")
    print(f"Wrote {spread_out}")
    print(f"IC (signal vs +{args.horizon}D forward return): {ic:.3f}")


if __name__ == "__main__":
    main()
