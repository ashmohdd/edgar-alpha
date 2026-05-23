from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="Edgar Alpha", layout="wide")

st.title("Edgar Alpha — Language Signal Engine")
st.caption("EDGAR 10‑K/10‑Q language → features → signal → forward return evaluation")

st.sidebar.header("Controls")
st.sidebar.markdown("Run locally:")
st.sidebar.code(
    "export SEC_USER_AGENT=\"edgar-alpha (your_email@example.com)\"\n"
    "make ingest TICKER=AAPL\nmake signal TICKER=AAPL\nmake eval TICKER=AAPL\nmake app\n",
    language="bash",
)

sig_path = "data/processed/signal.csv"
ev_path = "data/processed/eval.csv"
dec_path = "data/processed/decile_spread.csv"

try:
    sig = pd.read_csv(sig_path, parse_dates=["filing_date"])
except FileNotFoundError:
    st.warning("No signal found. Run: make ingest / make signal")
    st.stop()

st.subheader("Signal table (features)")
st.dataframe(sig.sort_values(["form", "filing_date"], ascending=[True, False]), use_container_width=True)

fig = px.line(
    sig.sort_values("filing_date"),
    x="filing_date",
    y="signal_z",
    color="form",
    markers=True,
    title="Signal (z-score) by filing",
)
st.plotly_chart(fig, use_container_width=True)

# Evaluation
try:
    ev = pd.read_csv(ev_path, parse_dates=["filing_date"])
    st.subheader("Event-level evaluation")
    st.dataframe(ev.sort_values(["form", "filing_date"], ascending=[True, False]), use_container_width=True)

    fig2 = px.scatter(
        ev.dropna(subset=["signal_z", "fwd_ret"]),
        x="signal_z",
        y="fwd_ret",
        color="form",
        trendline="ols",
        title="Signal vs +N-day forward return",
    )
    st.plotly_chart(fig2, use_container_width=True)
except FileNotFoundError:
    st.info("Run: make eval TICKER=... to compute forward returns and IC")

# Decile chart
try:
    dec = pd.read_csv(dec_path)
    st.subheader("Headline result: mean forward return by decile")
    fig3 = px.bar(dec, x="decile", y="mean_fwd_ret", color="form", barmode="group", title="Decile spread")
    st.plotly_chart(fig3, use_container_width=True)
except FileNotFoundError:
    st.info("Run: make eval to produce decile spread chart data")

