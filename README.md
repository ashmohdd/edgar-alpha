# Edgar Alpha — EDGAR Language Signal Engine (10‑K / 10‑Q)

**Audience:** PMs, Strategic Finance, CFO Analytics, Systematic Research

A portfolio-grade system that turns **unstructured financial text** (SEC 10‑K / 10‑Q filings) into a **quantified signal** and evaluates it with a **leakage-aware event-study** (+5 trading days).

> Most “NLP projects” do sentiment on movie reviews. This project measures **risk‑factor drift**, **uncertainty/hedging intensity**, and **guidance language intensity** on real filings—then tests whether it relates to **forward returns**.

---

## Executive summary (non-technical)
Executives often want an early-warning indicator that management’s tone is shifting **before** that shows up cleanly in the numbers.

This project:
1. Pulls a company’s latest **10‑K / 10‑Q** from SEC EDGAR
2. Extracts the sections finance teams care about (**Risk Factors** and **MD&A**)
3. Converts the language into a small set of measurable “tone” features
4. Combines them into a single **z‑scored signal**
5. Tests whether that signal has any relationship to **+5 trading‑day forward returns** after filings

**What a finance reviewer should look at:**
- The **decile spread chart** (does higher signal decile have meaningfully different forward returns?)
- The **signal vs forward return scatter** (is there any monotonic relationship?)
- The **feature table** (do the drivers make intuitive sense: uncertainty up, drift up, guidance language up?)

---

## Diagram (how this replaces manual work)
This is the “big picture” of what Edgar Alpha automates end-to-end:

![Edgar Alpha architecture](docs/architecture.svg)

---

## Demo (example run: AAPL)
This repo is designed so a finance viewer can reproduce the full workflow in minutes.

### Run the pipeline
```bash
export SEC_USER_AGENT="edgar-alpha (your_email@example.com)"
make ingest TICKER=AAPL
make signal TICKER=AAPL
make eval   TICKER=AAPL
make app
```

### What gets generated (artifacts)
After the run you will have:
- Cached filings (local): `.cache/edgar/AAPL/*.html`
- Signal table: `data/processed/signal.csv`
- Event study output: `data/processed/eval.csv`
- Decile chart data: `data/processed/decile_spread.csv`
- DuckDB database: `data/processed/edgar_alpha.duckdb`

### What you’ll see in the dashboard
- **Signal table** (per filing): uncertainty, guidance intensity, risk drift, and `signal_z`
- **Signal over time** split by form (10‑K vs 10‑Q)
- **Signal vs +5D forward return** scatter (sanity check)
- **Decile spread chart** (headline): mean +5D return by signal decile

### Example interpretation (finance language)
If the top signal deciles show meaningfully different forward returns vs the bottom deciles, that suggests the language features
(uncertainty, guidance verbs, risk drift) capture information that markets may price with a lag after filings.
If the decile spread is flat, that result is still useful: it indicates this specific feature mix may not be predictive for that ticker/horizon,
and should be improved (more filings, better section parsing, add transcripts/8‑Ks, multi-ticker testing).

---

## Business problem (why this exists)
A PM/CFO wants early warning. Changes in:
- risk language (what management chooses to emphasize),
- uncertainty/hedging tone,
- guidance verbs (expects/anticipates/forecast/project/outlook)

can precede:
- earnings surprises,
- post-filing drift,
- and re‑rating events.

This repo demonstrates the **full loop**: ingestion → feature engineering → signal building → evaluation.

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
- **Uncertainty** lexicon count per 1k words
- **Guidance verb intensity** per 1k words (expects/anticipates/forecast/project/outlook)
- **Risk-factor drift**: TF‑IDF cosine distance vs prior filing of the same form

### Signal
- `signal_raw` = sum of feature values (with missing handling)
- `signal_z` = z-score computed **within form** (10‑K and 10‑Q distributions differ)

### Evaluation
- Event alignment: filing date → next trading day close
- Forward return horizon: **+5 trading days** (configurable)
- Metrics:
  - Information Coefficient (IC)
  - **Decile spread** (mean forward return by signal decile)

### Storage
- DuckDB database at `data/processed/edgar_alpha.duckdb`
  - `filings` (corpus / extracted sections)
  - `features` (feature table + signal)
  - `eval` (event-level forward returns + decile assignment)

---

## Architecture
Ingestion (EDGAR; cached/idempotent) → Parsing/normalization (section split) → Feature layer (uncertainty, guidance verbs, risk drift) → Signal layer (z-score) → Evaluation (IC/deciles) → Streamlit front end.

---

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

## What to screenshot for your portfolio (recruiter-friendly)
After running `make eval` and `make app`, screenshot:
1. **Decile spread** bar chart (headline)
2. **Signal vs forward return** scatter (sanity check)
3. Feature table (shows explainability)

---

## Limitations / what I’d productionize next
- Filing structure varies; section parsing is heuristic
- Add 8‑K events and earnings-call transcripts
- Add leakage-safe event timestamp alignment (calls vs next open)
- Add transaction costs + turnover constraints
- Add multi-ticker universe backtesting + pooled IC/decile results
