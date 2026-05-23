from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.parse.section_splitter import html_to_text, extract_risk_factors, extract_mdna
from src.features.tone import uncertainty_per_1k_words
from src.features.risk_drift import cosine_drift


def build_signal_for_ticker(ticker: str, cache_dir: Path = Path(".cache/edgar")) -> pd.DataFrame:
    t = ticker.upper()
    in_dir = cache_dir / t
    if not in_dir.exists():
        raise SystemExit(f"No cache found. Run: make ingest TICKER={t}")

    files = sorted([p for p in in_dir.glob(f"{t}_10-K_*.html")])
    if len(files) < 2:
        raise SystemExit("Need at least 2 10-K filings for drift. Try another ticker.")

    rows = []
    for p in files:
        # parse filing date from name
        parts = p.name.split("_")
        filing_date = parts[2]
        html = p.read_text(encoding="utf-8", errors="ignore")
        text = html_to_text(html)

        risk = extract_risk_factors(text)
        mdna = extract_mdna(text)

        rows.append(
            {
                "ticker": t,
                "filing_date": pd.to_datetime(filing_date),
                "risk_text": risk,
                "mdna_text": mdna,
                "uncertainty_risk_per_1k": uncertainty_per_1k_words(risk),
                "uncertainty_mdna_per_1k": uncertainty_per_1k_words(mdna),
            }
        )

    df = pd.DataFrame(rows).sort_values("filing_date")

    # drift: compare risk factors vs prior 10-K
    drifts = [None]
    for i in range(1, len(df)):
        drifts.append(cosine_drift(df.iloc[i - 1]["risk_text"], df.iloc[i]["risk_text"]))

    df["risk_drift"] = drifts

    # signal: zscore of uncertainty + drift
    x = df[["uncertainty_risk_per_1k", "uncertainty_mdna_per_1k", "risk_drift"]].copy()
    x = x.astype(float)

    df["signal_raw"] = x.sum(axis=1, skipna=True)
    df["signal_z"] = (df["signal_raw"] - df["signal_raw"].mean()) / (df["signal_raw"].std(ddof=0) + 1e-9)

    return df[["ticker", "filing_date", "uncertainty_risk_per_1k", "uncertainty_mdna_per_1k", "risk_drift", "signal_z"]]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ticker", required=True)
    p.add_argument("--out", default="data/processed/signal.csv")
    args = p.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    df = build_signal_for_ticker(args.ticker)
    df.to_csv(out, index=False)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
