from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.parse.section_splitter import html_to_text, extract_risk_factors, extract_mdna
from src.features.tone import uncertainty_per_1k_words
from src.features.risk_drift import cosine_drift
from src.features.guidance import guidance_verbs_per_1k_words
from src.storage.duckdb_store import connect, upsert_filings, upsert_features


def _parse_from_filename(path: Path) -> dict:
    # <TICKER>_<FORM>_<YYYY-MM-DD>_<ACCESSION>.html
    parts = path.name.split("_")
    return {
        "ticker": parts[0],
        "form": parts[1],
        "filing_date": pd.to_datetime(parts[2]).date(),
        "accession": parts[3].replace(".html", ""),
    }


def build_for_ticker(ticker: str, cache_dir: Path = Path(".cache/edgar")) -> pd.DataFrame:
    t = ticker.upper()
    in_dir = cache_dir / t
    if not in_dir.exists():
        raise SystemExit(f"No cache found. Run: make ingest TICKER={t}")

    files = sorted([p for p in in_dir.glob(f"{t}_*.html")])
    if len(files) < 2:
        raise SystemExit("Need multiple filings to build features.")

    filing_rows = []
    feat_rows = []

    # For drift, we compute within each form separately using prior filing of same form
    prev_risk_by_form = {}

    for p in files:
        meta = _parse_from_filename(p)
        html = p.read_text(encoding="utf-8", errors="ignore")
        text_full = html_to_text(html)
        risk = extract_risk_factors(text_full)
        mdna = extract_mdna(text_full)

        form = meta["form"]
        drift = None
        if form in prev_risk_by_form and prev_risk_by_form[form]:
            drift = cosine_drift(prev_risk_by_form[form], risk)
        prev_risk_by_form[form] = risk

        unc_risk = uncertainty_per_1k_words(risk)
        unc_mdna = uncertainty_per_1k_words(mdna)
        guidance = guidance_verbs_per_1k_words(mdna)

        filing_rows.append(
            {
                **meta,
                "primary_doc": "",
                "report_date": None,
                "source_path": str(p),
                "text_risk": risk,
                "text_mdna": mdna,
                "text_full": text_full,
            }
        )

        feat_rows.append(
            {
                **meta,
                "uncertainty_risk_per_1k": float(unc_risk),
                "uncertainty_mdna_per_1k": float(unc_mdna),
                "guidance_verbs_per_1k": float(guidance),
                "risk_drift": float(drift) if drift is not None else None,
            }
        )

    filings_df = pd.DataFrame(filing_rows)
    feats = pd.DataFrame(feat_rows).sort_values(["form", "filing_date"]).reset_index(drop=True)

    # Build signal within each form to avoid mixing 10-K/10-Q distributions
    feats["signal_raw"] = feats[["uncertainty_risk_per_1k", "uncertainty_mdna_per_1k", "guidance_verbs_per_1k", "risk_drift"]].sum(
        axis=1, skipna=True
    )

    feats["signal_z"] = np.nan
    for form, g in feats.groupby("form"):
        mu = g["signal_raw"].mean()
        sd = g["signal_raw"].std(ddof=0) + 1e-9
        feats.loc[g.index, "signal_z"] = (g["signal_raw"] - mu) / sd

    return filings_df, feats


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ticker", required=True)
    p.add_argument("--db", default="data/processed/edgar_alpha.duckdb")
    p.add_argument("--out_signal", default="data/processed/signal.csv")
    args = p.parse_args()

    filings_df, feats = build_for_ticker(args.ticker)

    con = connect(Path(args.db))
    upsert_filings(con, filings_df)
    upsert_features(con, feats)

    Path(args.out_signal).parent.mkdir(parents=True, exist_ok=True)
    feats.sort_values(["form", "filing_date"]).to_csv(args.out_signal, index=False)
    print(f"Wrote {args.out_signal}")
    print(f"Wrote DuckDB: {args.db}")


if __name__ == "__main__":
    main()
