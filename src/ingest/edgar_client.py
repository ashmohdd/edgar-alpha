from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import requests


SEC_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_ARCHIVES = "https://www.sec.gov/Archives/edgar/data"


def _sec_headers() -> Dict[str, str]:
    # SEC requests a descriptive User-Agent. Set SEC_USER_AGENT in your env.
    ua = os.getenv("SEC_USER_AGENT", "edgar-alpha (email: you@example.com)")
    return {"User-Agent": ua, "Accept-Encoding": "gzip, deflate"}


def load_ticker_map() -> Dict[str, str]:
    """Loads SEC ticker->CIK map from official JSON."""
    url = "https://www.sec.gov/files/company_tickers.json"
    r = requests.get(url, headers=_sec_headers(), timeout=30)
    r.raise_for_status()
    data = r.json()

    # data is dict keyed by integer-like strings
    out = {}
    for _, row in data.items():
        out[row["ticker"].upper()] = str(row["cik_str"]).zfill(10)
    return out


def get_company_submissions(cik10: str) -> dict:
    r = requests.get(SEC_SUBMISSIONS.format(cik=cik10), headers=_sec_headers(), timeout=30)
    r.raise_for_status()
    return r.json()


def list_recent_filings(submissions: dict, forms: List[str]) -> List[dict]:
    rec = submissions.get("filings", {}).get("recent", {})
    if not rec:
        return []

    n = len(rec.get("form", []))
    out = []
    for i in range(n):
        form = rec["form"][i]
        if form not in forms:
            continue
        out.append(
            {
                "form": form,
                "filing_date": rec["filingDate"][i],
                "accession": rec["accessionNumber"][i].replace("-", ""),
                "accession_raw": rec["accessionNumber"][i],
                "primary_doc": rec["primaryDocument"][i],
                "report_date": rec["reportDate"][i],
            }
        )
    return out


def download_filing_text(cik10: str, accession_nodash: str, primary_doc: str) -> str:
    # Example:
    # https://www.sec.gov/Archives/edgar/data/<CIK>/<ACCESSION>/<PRIMARYDOC>
    url = f"{SEC_ARCHIVES}/{int(cik10)}/{accession_nodash}/{primary_doc}"
    r = requests.get(url, headers=_sec_headers(), timeout=60)
    r.raise_for_status()
    return r.text


def save_raw(ticker: str, filing: dict, text: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{ticker}_{filing['form']}_{filing['filing_date']}_{filing['accession']}.html"
    path = out_dir / fname
    path.write_text(text, encoding="utf-8")

    meta_path = out_dir / (fname + ".meta.json")
    meta_path.write_text(json.dumps(filing, indent=2), encoding="utf-8")
    return path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ticker", required=True)
    p.add_argument("--forms", default="10-K")
    p.add_argument("--out", default=".cache/edgar")
    args = p.parse_args()

    ticker = args.ticker.upper()
    forms = [f.strip() for f in args.forms.split(",") if f.strip()]

    cik_map = load_ticker_map()
    if ticker not in cik_map:
        raise SystemExit(f"Ticker not found in SEC map: {ticker}")

    cik10 = cik_map[ticker]
    submissions = get_company_submissions(cik10)
    filings = list_recent_filings(submissions, forms=forms)
    if not filings:
        raise SystemExit(f"No filings found for {ticker} forms={forms}")

    out_dir = Path(args.out) / ticker

    # idempotent: skip if file exists
    for f in filings[:6]:
        fname = f"{ticker}_{f['form']}_{f['filing_date']}_{f['accession']}.html"
        path = out_dir / fname
        if path.exists():
            continue
        text = download_filing_text(cik10, f["accession"], f["primary_doc"])
        save_raw(ticker, f, text, out_dir)

    print(f"Downloaded {ticker} filings to {out_dir}")


if __name__ == "__main__":
    main()
