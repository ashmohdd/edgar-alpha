.PHONY: ingest signal eval app

TICKER ?= AAPL

ingest:
	python -m src.ingest.edgar_client --ticker $(TICKER)

signal:
	python -m src.signal.build_signal --ticker $(TICKER)

eval:
	python -m src.eval.backtest --ticker $(TICKER)

app:
	streamlit run app/streamlit_app.py
