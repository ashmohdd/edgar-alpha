# Edgar Alpha — Earnings-Call & 10‑K Language Signal Engine

**Tier:** ELITE · **Functions:** Hedge Fund, CFO Analytics, Strategic Finance

A portfolio-grade system that turns **unstructured financial text** (SEC 10‑K / 10‑Q / 8‑K + optional earnings-call transcripts) into a **quantified, backtested signal**.

> Most NLP repos do toy sentiment on movie reviews. This project does **risk‑factor drift**, **uncertainty language**, and **guidance verb deltas** on real filings—then tests whether it predicts **forward returns**.

## What this answers (business problem)
A PM / CFO wants early warning signals **before** numbers show it:
- Management tone and hedging language
- YoY change in **Risk Factors** language (10‑K vs prior 10‑K)
- **Guidance language intensity** changes in MD&A

## Architecture
Ingestion (EDGAR; cached/idempotent) → Parsing/normalization (section split) → Feature layer (uncertainty, guidance verbs, risk drift) → Signal layer (z-score) → Evaluation (IC/deciles) → Streamlit front end.

## Quickstart

### 1) Install
```bash
python -m venv .venv
source .venv/bin/activate  # mac/linux
# .venv\Scripts\activate   # windows

pip install -r requirements.txt
```

### 2) Set SEC User-Agent (required)
Use your real email.
```bash
export SEC_USER_AGENT="edgar-alpha (your_email@example.com)"
# Windows PowerShell:
# $env:SEC_USER_AGENT="edgar-alpha (your_email@example.com)"
```

### 3) Ingest + build signal + evaluate
```bash
make ingest TICKER=AAPL
make signal TICKER=AAPL
make eval   TICKER=AAPL
```

### 4) Run the dashboard
```bash
make app
```

---

## What’s implemented (MVP+)
### Filings
- 10‑K and 10‑Q ingestion from EDGAR (cached, idempotent)

### Parsing
- HTML→text cleanup
- Best-effort section extraction:
  - Risk Factors (Item 1A)
  - MD&A (Item 7)

### Features
- Uncertainty lexicon count per 1k words
- Guidance verb intensity per 1k words (expects/anticipates/forecast/project/outlook)
- Risk-factor drift (TF‑IDF cosine distance vs prior filing of same form)

### Storage
- DuckDB database at `data/processed/edgar_alpha.duckdb`
  - `filings` (corpus)
  - `features` (feature table)
  - `eval` (event-level forward returns + deciles)

### Evaluation
- Forward return horizon: +5 trading days (configurable)
- Information Coefficient (IC)
- Decile spread (mean forward return by signal decile)

---

## Results (what to screenshot)
After running `make eval` and `make app`, screenshot:
- The decile spread bar chart
- The signal vs forward return scatter

---

## Limitations / what I’d productionize next
- Better section parsing across issuers and filing formats
- Add 8‑K events and earnings-call transcripts
- Add leakage-safe event timestamp alignment (calls vs next open)
- Add transaction costs and turnover constraints
- Add multi-ticker universe backtesting
