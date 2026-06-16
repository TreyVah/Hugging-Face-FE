"""
Batch CSV Upload page.
Upload a CSV of applicants → score all → view + download results.
"""
import io
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from frontend.components import api_client as api
from frontend.components.cards import section_header, metric_card

# ── Colour map for decisions
DECISION_COLOURS = {
    "APPROVE": "#00E5A0",
    "REVIEW":  "#FFB800",
    "REJECT":  "#FF4D6A",
}


def render():
    st.title(" Batch CSV Scoring")
    st.caption("Upload a CSV file to score multiple applicants at once. Max 1,000 rows.")

    # ─────────────────────────────────────────
    # Download template
    # ─────────────────────────────────────────
    section_header("Step 1 — Download the template")
    st.info(
        "Your CSV must have exactly these column headers. "
        "Download the template, fill it in, then upload it below."
    )

    if st.button("⬇ Download CSV Template", type="secondary"):
        try:
            import requests, os
            api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
            token    = st.session_state.get("token", "")
            r = requests.get(
                f"{api_base}/batch/template",
                headers={"Authorization": f"Bearer {token}"},
                timeout=15,
            )
            st.download_button(
                "Save template",
                data=r.content,
                file_name="credit_risk_template.csv",
                mime="text/csv",
            )
        except Exception as e:
            st.error(f"Could not fetch template: {e}")

    # ─────────────────────────────────────────
    # File upload
    # ─────────────────────────────────────────
    st.markdown("---")
    section_header("Step 2 — Upload your filled CSV")

    uploaded = st.file_uploader(
        "Choose CSV file",
        type=["csv"],
        help="Max 5MB, max 1,000 rows",
    )

    if uploaded is None:
        st.info(" Upload a CSV file to get started.")
        return

    try:
        df_preview = pd.read_csv(uploaded)
        uploaded.seek(0)
    except Exception:
        st.error("Could not read the file. Make sure it is a valid CSV.")
        return

    st.success(
        f" File loaded: **{uploaded.name}** — "
        f"{len(df_preview):,} rows, {len(df_preview.columns)} columns"
    )

    with st.expander("Preview first 5 rows"):
        st.dataframe(df_preview.head(5), use_container_width=True)

    # ─────────────────────────────────────────
    # Score button
    # ─────────────────────────────────────────
    st.markdown("---")
    section_header("Step 3 — Score all applicants")

    if st.button(" Score Batch", type="primary", use_container_width=True):
        with st.spinner(f"Scoring {len(df_preview):,} applicants... this may take a moment."):
            try:
                import requests, os
                api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
                token    = st.session_state.get("token", "")
                r = requests.post(
                    f"{api_base}/batch/upload",
                    files={"file": (uploaded.name, uploaded.getvalue(), "text/csv")},
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=120,
                )
                if not r.ok:
                    st.error(
                        f"API error {r.status_code}: "
                        f"{r.json().get('detail', 'Unknown error')}"
                    )
                    return
                data = r.json()
                st.session_state["batch_result"] = data
            except Exception as e:
                st.error(f"Request failed: {e}")
                return

    # ─────────────────────────────────────────
    # Results
    # ─────────────────────────────────────────
    data = st.session_state.get("batch_result")
    if not data:
        return

    summary = data["summary"]
    results = data["results"]

    if not results:
        st.warning("No results returned. Check your CSV format.")
        return

    st.markdown("---")
    section_header("Results", f"Batch ID: {summary['batch_id'][:8]}...")

    # KPI row
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1: metric_card("Total Rows", str(summary["total_rows"]),  colour="#6E56FF")
    with k2: metric_card("Scored",     str(summary["scored"]),      colour="#6E56FF")
    with k3: metric_card("Approved",   str(summary["approved"]),    colour="#00E5A0")
    with k4: metric_card("Review",     str(summary["review"]),      colour="#FFB800")
    with k5: metric_card("Rejected",   str(summary["rejected"]),    colour="#FF4D6A")

    m1, m2, m3 = st.columns(3)
    m1.metric("Approval Rate", f"{summary['approval_rate']:.1%}")
    m2.metric("Avg. PD",       f"{summary['avg_pd']:.1%}")
    m3.metric("Avg. Score",    str(summary["avg_score"]))

    # ── Decision donut chart + results table
    st.markdown("---")
    col_chart, col_table = st.columns([1, 2])

    with col_chart:
        labels  = ["Approved", "Review", "Rejected"]
        values  = [summary["approved"], summary["review"], summary["rejected"]]
        colours = ["#00E5A0", "#FFB800", "#FF4D6A"]
        fig = go.Figure(go.Pie(
            labels=labels, values=values, hole=0.55,
            marker_colors=colours,
            textinfo="label+percent",
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=30, b=10),
            height=280,
            title="Decision split",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        df_results = pd.DataFrame(results)

        # ── Safely format columns that may or may not exist
        def safe_pct(col):
            if col in df_results.columns:
                return df_results[col].apply(
                    lambda x: f"{float(x):.1%}" if x is not None else "N/A"
                )
            return "N/A"

        def safe_col(col, default="N/A"):
            return df_results[col] if col in df_results.columns else default

        display_df = pd.DataFrame({
            "Row":        safe_col("row"),
            "Score":      safe_col("credit_score"),
            "Risk Band":  safe_col("risk_band"),
            "Decision":   safe_col("decision"),
            "PD":         safe_pct("probability_of_default"),
            "Confidence": safe_pct("confidence"),
        })

        def colour_decision(val):
            c = DECISION_COLOURS.get(str(val), "#888")
            return f"color: {c}; font-weight: bold"

        styled = display_df.style.applymap(
            colour_decision, subset=["Decision"]
        )
        st.dataframe(styled, use_container_width=True, hide_index=True)

    # ── Validation errors
    if summary.get("validation_errors"):
        st.markdown("---")
        with st.expander(
            f" {len(summary['validation_errors'])} validation errors (rows skipped)"
        ):
            for err in summary["validation_errors"]:
                st.warning(err)

    # ── Download results
    st.markdown("---")
    df_download = pd.DataFrame(results)
    csv_out = df_download.to_csv(index=False)
    st.download_button(
        "⬇ Download scored results CSV",
        data=csv_out,
        file_name=f"scored_{summary['filename']}",
        mime="text/csv",
        use_container_width=True,
    )