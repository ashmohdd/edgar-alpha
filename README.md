# Edgar Alpha — Earnings-Call & 10‑K Language Signal Engine

**Tier:** ELITE · **Functions:** Hedge Fund, CFO Analytics, Strategic Finance

A portfolio-grade system that turns **unstructured financial text** (SEC 10‑K / 10‑Q / 8‑K + optional earnings-call transcripts) into a **quantified, backtested signal**.

> Most NLP repos do toy sentiment on movie reviews. This project does **risk‑factor drift**, **uncertainty language**, and **guidance language change** on real filings—then tests whether it predicts **forward returns**.

## What this answers (business problem)
A PM / CFO wants early warning signals **before** numbers show it:
- Management tone and hedging language ("uncertain", "headwind", "we expect")
- Year-over-year change in Risk Factors language (10‑K vs prior 10‑K)
- MD&A language changes

## Demo (MVP)
- Select a ticker
- Pull filings from EDGAR
- Extract Risk Factors + MD&A sections
- Compute features (uncertainty counts, drift distance)
- Build a z-scored signal
- Evaluate vs **+5D forward returns**

## Architecture
Ingestion (EDGAR; cached/idempotent) → Parsing/normalization (section split) → Feature layer (tone, uncertainty, risk drift) → Signal layer (z-score) → Evaluation (IC/deciles) → Streamlit front end.

## Repo structure
```
edgar-alpha/
├── README.md
├── data/                     # .gitkeep only (do not commit raw filings)
├── src/
│   ├── ingest/               # EDGAR client
│   ├── parse/                # section splitter
│   ├── features/             # tone/uncertainty + risk drift
│   ├── signal/               # build signal table
│   └── eval/                 # IC + decile spread backtest
├── notebooks/
├── app/streamlit_app.py
├── tests/
├── requirements.txt
└── Makefile
```

---

## Quickstart

### 1) Install
```bash
python -m venv .venv
source .venv/bin/activate  # mac/linux
# .venv\Scripts\activate   # windows

pip install -r requirements.txt
```

### 2) Ingest + build signal
```bash
make ingest TICKER=AAPL
make signal TICKER=AAPL
make eval   TICKER=AAPL
```

### 3) Run the dashboard
```bash
make app
```

---

## MVP features implemented
- EDGAR ingestion for 10‑K filings
- Section extraction: **Risk Factors** and **MD&A** (best-effort heuristic)
- Feature set:
  - Uncertainty lexicon count per 1k words
  - Risk-factor drift: cosine distance between current vs prior 10‑K Risk Factors
- Signal: z-score of (uncertainty + drift)
- Evaluation: forward 5 trading-day return + Information Coefficient (IC)

## Limitations (honest)
- Filings vary in structure; section parsing is heuristic.
- MVP uses a simple lexicon + TF-IDF cosine drift. A production system would add:
  - robust HTML/text extraction, better section labeling
  - point-in-time transcript ingestion
  - leakage-safe event-time alignment (call timestamps)
  - transaction cost model and turnover constraints

## What I’d productionize next
- Add 10‑Q and 8‑K events; build an event calendar
- Add guidance extraction (ranges, verbs) with confidence scoring
- Add anomaly flags (tone vs reported KPI divergence)
- Move corpus + features into DuckDB with incremental updates

