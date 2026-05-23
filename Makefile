.PHONY: ingest signal eval app db

TICKER ?= AAPL

# Ingest filings (10-K + 10-Q)
ingest:
	python -m src.ingest.edgar_client --ticker $(TICKER) --forms 10-K,10-Q

# Build features + signal into DuckDB and export CSV artifacts
signal:
	python -m src.signal.build_signal --ticker $(TICKER)

# Evaluate: IC + deciles + event-study outputs
# (reads from DuckDB if available)
eval:
	python -m src.eval.backtest --ticker $(TICKER)

# Launch app
app:
	streamlit run app/streamlit_app.py

# Inspect DB (optional)
db:
	python -m src.storage.duckdb_store --ticker $(TICKER) --inspect
