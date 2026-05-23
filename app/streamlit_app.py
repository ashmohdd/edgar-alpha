from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="Edgar Alpha", layout="wide")

st.title("Edgar Alpha — Language Signal Engine")
st.caption("EDGAR 10‑K language → features → signal → forward return evaluation (MVP)")

st.sidebar.header("Controls")
ticker = st.sidebar.text_input("Ticker", value="AAPL")

st.sidebar.markdown("### Run pipeline")
st.sidebar.code(
    "make ingest TICKER=...\nmake signal TICKER=...\nmake eval TICKER=...",
    language="bash",
)

sig_path = "data/processed/signal.csv"
eval_path = "data/processed/eval.csv"

try:
    sig = pd.read_csv(sig_path, parse_dates=["filing_date"])
except FileNotFoundError:
    st.warning("No signal found. Run: make ingest / make signal")
    st.stop()

st.subheader("Signal table")
st.dataframe(sig.sort_values("filing_date", ascending=False), use_container_width=True)

fig = px.line(sig.sort_values("filing_date"), x="filing_date", y="signal_z", markers=True, title="Signal (z-score) by filing")
st.plotly_chart(fig, use_container_width=True)

try:
    ev = pd.read_csv(eval_path, parse_dates=["filing_date"])
    st.subheader("Evaluation")
    st.dataframe(ev.sort_values("filing_date", ascending=False), use_container_width=True)

    fig2 = px.scatter(ev, x="signal_z", y="fwd_ret", trendline="ols", title="Signal vs +5D forward return")
    st.plotly_chart(fig2, use_container_width=True)
except FileNotFoundError:
    st.info("Run: make eval TICKER=... to compute forward returns and IC")
