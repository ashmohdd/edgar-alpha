"""DuckDB storage for corpus, features, and signals."""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import pandas as pd


DEFAULT_DB = Path("data/processed/edgar_alpha.duckdb")


def connect(db_path: Path = DEFAULT_DB) -> duckdb.DuckDBPyConnection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    con.execute("PRAGMA threads=4")
    return con


def init_schema(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS filings (
            ticker VARCHAR,
            form VARCHAR,
            filing_date DATE,
            accession VARCHAR,
            primary_doc VARCHAR,
            report_date DATE,
            source_path VARCHAR,
            text_risk VARCHAR,
            text_mdna VARCHAR,
            text_full VARCHAR,
            PRIMARY KEY(ticker, form, filing_date, accession)
        );
        """
    )

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS features (
            ticker VARCHAR,
            form VARCHAR,
            filing_date DATE,
            accession VARCHAR,
            uncertainty_risk_per_1k DOUBLE,
            uncertainty_mdna_per_1k DOUBLE,
            guidance_verbs_per_1k DOUBLE,
            risk_drift DOUBLE,
            signal_raw DOUBLE,
            signal_z DOUBLE,
            PRIMARY KEY(ticker, form, filing_date, accession)
        );
        """
    )

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS eval (
            ticker VARCHAR,
            form VARCHAR,
            filing_date DATE,
            accession VARCHAR,
            horizon_days INTEGER,
            fwd_ret DOUBLE,
            decile INTEGER,
            PRIMARY KEY(ticker, form, filing_date, accession, horizon_days)
        );
        """
    )


def upsert_filings(con: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> None:
    init_schema(con)
    con.register("_filings", df)
    con.execute(
        """
        INSERT OR REPLACE INTO filings
        SELECT * FROM _filings
        """
    )
    con.unregister("_filings")


def upsert_features(con: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> None:
    init_schema(con)
    con.register("_features", df)
    con.execute(
        """
        INSERT OR REPLACE INTO features
        SELECT * FROM _features
        """
    )
    con.unregister("_features")


def upsert_eval(con: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> None:
    init_schema(con)
    con.register("_eval", df)
    con.execute(
        """
        INSERT OR REPLACE INTO eval
        SELECT * FROM _eval
        """
    )
    con.unregister("_eval")


def inspect(con: duckdb.DuckDBPyConnection, ticker: str) -> None:
    t = ticker.upper()
    print("filings:")
    print(con.execute("SELECT form, COUNT(*) n, MIN(filing_date) min_dt, MAX(filing_date) max_dt FROM filings WHERE ticker=? GROUP BY 1 ORDER BY 1", [t]).df())
    print("features:")
    print(con.execute("SELECT form, COUNT(*) n FROM features WHERE ticker=? GROUP BY 1 ORDER BY 1", [t]).df())
    print("eval:")
    print(con.execute("SELECT form, COUNT(*) n FROM eval WHERE ticker=? GROUP BY 1 ORDER BY 1", [t]).df())


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ticker", required=True)
    p.add_argument("--db", default=str(DEFAULT_DB))
    p.add_argument("--inspect", action="store_true")
    args = p.parse_args()

    con = connect(Path(args.db))
    init_schema(con)
    if args.inspect:
        inspect(con, args.ticker)


if __name__ == "__main__":
    main()
