"""
History page — paginated table of all past predictions.
Supports filtering, row expansion, and CSV export.
"""
import streamlit as st
import pandas as pd
from frontend.components import api_client as api
from frontend.components.cards  import section_header
from frontend.components.charts import shap_bar_chart

def render():
    st.title(" Prediction History")
    st.caption("Browse, filter, and inspect all past credit decisions.")

    # ─────────────────────────────────────────
    # Filter bar
    # ─────────────────────────────────────────
    col1, col2, col3 = st.columns([2, 2, 1])
    decision_filter = col1.selectbox(
        "Filter by decision", ["All", "APPROVE", "REVIEW", "REJECT"]
    )
    per_page = col2.selectbox("Rows per page", [10, 20, 50], index=1)
    page     = col3.number_input("Page", min_value=1, value=1)

    # Fetch
    with st.spinner("Loading history..."):
        try:
            data = api.get_history(
                page=page,
                per_page=per_page,
                decision=None if decision_filter == "All" else decision_filter,
            )
        except RuntimeError as e:
            st.error(str(e))
            return

    items = data.get("items", [])
    total = data.get("total", 0)

    if not items:
        st.info("No predictions match your filter.")
        return

    st.caption(f"Showing {len(items)} of {total} predictions · Page {page}")

    # ─────────────────────────────────────────
    # Table
    # ─────────────────────────────────────────
    df = pd.DataFrame(items)
    df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
    df["probability_of_default"] = df["probability_of_default"].map("{:.1%}".format)
    df["confidence"]             = df["confidence"].map("{:.1%}".format)

    display_cols = {
        "created_at":             "Date",
        "credit_score":           "Score",
        "risk_band":              "Risk Band",
        "decision":               "Decision",
        "probability_of_default": "PD",
        "confidence":             "Confidence",
        "prediction_id":          "ID",
    }
    df_display = df[list(display_cols.keys())].rename(columns=display_cols)
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # ─────────────────────────────────────────
    # CSV export
    # ─────────────────────────────────────────
    csv = df_display.to_csv(index=False)
    st.download_button(
        "⬇ Export to CSV",
        data=csv,
        file_name="credit_risk_history.csv",
        mime="text/csv",
    )

    # ─────────────────────────────────────────
    # Row detail expander
    # ─────────────────────────────────────────
    st.markdown("---")
    section_header("Inspect a prediction")
    pred_ids = [i["prediction_id"] for i in items]
    selected_id = st.selectbox("Select prediction ID", pred_ids)

    if selected_id and st.button("Load details", type="primary"):
        with st.spinner("Fetching detail..."):
            try:
                detail = api.get_prediction_detail(selected_id)
            except RuntimeError as e:
                st.error(str(e))
                return

        col_a, col_b = st.columns(2)
        with col_a:
            section_header("Input data")
            inp = detail.get("input_data", {})
            for k, v in inp.items():
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;"
                    f"padding:5px 0;border-bottom:1px solid #eee'>"
                    f"<span style='color:#888;font-size:13px'>{k.replace('_',' ').title()}</span>"
                    f"<span style='font-weight:500;font-size:13px'>{v}</span></div>",
                    unsafe_allow_html=True,
                )

        with col_b:
            section_header("Result")
            st.metric("Decision",     detail["decision"])
            st.metric("Credit Score", detail["credit_score"])
            st.metric("PD",           f"{detail['probability_of_default']:.1%}")
            st.metric("Risk Band",    detail["risk_band"])
            st.metric("Confidence",   f"{detail['confidence']:.1%}")

        # Load SHAP explanation for this historical prediction
        if st.button(" Load SHAP explanation"):
            with st.spinner("Computing explanation..."):
                try:
                    exp = api.explain(selected_id)
                    st.plotly_chart(
                        shap_bar_chart(exp["feature_impacts"]),
                        use_container_width=True,
                    )
                except RuntimeError as e:
                    st.warning(f"Explanation unavailable: {e}")