"""
Dashboard page — portfolio-level analytics across all predictions.
Fetches up to 500 most recent predictions and visualises them.
"""
import streamlit as st
import pandas as pd
from frontend.components import api_client as api
from frontend.components.cards  import section_header, metric_card
from frontend.components.charts import (
    decision_pie, pd_histogram, score_over_time
)

def render():
    st.title(" Dashboard")
    st.caption("Portfolio-level analytics across all scored applicants.")

    # Fetch data
    with st.spinner("Loading analytics..."):
        try:
            data = api.get_history(page=1, per_page=100)
        except RuntimeError as e:
            st.error(str(e))
            return

    items = data.get("items", [])
    if not items:
        st.info("No predictions yet. Score some applicants first.")
        return

    df = pd.DataFrame(items)
    df["created_at"] = pd.to_datetime(df["created_at"])

    # ─────────────────────────────────────────
    # KPI Cards
    # ─────────────────────────────────────────
    section_header("Portfolio KPIs")
    k1, k2, k3, k4 = st.columns(4)

    total      = len(df)
    avg_pd     = df["probability_of_default"].mean()
    avg_score  = int(df["credit_score"].mean())
    approve_rt = (df["decision"] == "APPROVE").mean()

    with k1:
        metric_card("Total Scored", str(total), colour="#3B8BD4")
    with k2:
        metric_card("Avg. PD", f"{avg_pd:.1%}", colour="#E24B4A")
    with k3:
        metric_card("Avg. Credit Score", str(avg_score), colour="#1D9E75")
    with k4:
        metric_card("Approval Rate", f"{approve_rt:.1%}", colour="#EF9F27")

    # ─────────────────────────────────────────
    # Decision breakdown + PD distribution
    # ─────────────────────────────────────────
    st.markdown("---")
    section_header("Distribution")
    ch1, ch2 = st.columns(2)
    with ch1:
        st.plotly_chart(decision_pie(items), use_container_width=True)
    with ch2:
        st.plotly_chart(pd_histogram(items), use_container_width=True)

    # ─────────────────────────────────────────
    # Score over time
    # ─────────────────────────────────────────
    st.markdown("---")
    section_header("Score trend")
    st.plotly_chart(score_over_time(items), use_container_width=True)

    # ─────────────────────────────────────────
    # Risk band breakdown table
    # ─────────────────────────────────────────
    st.markdown("---")
    section_header("Risk band summary")
    summary = (
        df.groupby("risk_band")
        .agg(
            count=("prediction_id", "count"),
            avg_pd=("probability_of_default", "mean"),
            avg_score=("credit_score", "mean"),
        )
        .reset_index()
        .rename(columns={
            "risk_band": "Risk Band",
            "count":     "Count",
            "avg_pd":    "Avg. PD",
            "avg_score": "Avg. Score",
        })
    )
    summary["Avg. PD"]    = summary["Avg. PD"].map("{:.1%}".format)
    summary["Avg. Score"] = summary["Avg. Score"].map("{:.0f}".format)
    st.dataframe(summary, use_container_width=True, hide_index=True)