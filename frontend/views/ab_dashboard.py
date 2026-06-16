"""
A/B Testing Dashboard.
Shows live performance comparison between XGBoost (A) and LightGBM (B).
Allows admins to change traffic split and declare winners.
"""
import streamlit as st
import plotly.graph_objects as go
import requests
import os

from frontend.components.cards import section_header, metric_card

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")


def _headers():
    return {"Authorization": f"Bearer {st.session_state.get('token', '')}"}


def _get(endpoint: str) -> dict:
    r = requests.get(f"{API_BASE}{endpoint}", headers=_headers(), timeout=15)
    if not r.ok:
        raise RuntimeError(f"API error {r.status_code}: {r.json().get('detail')}")
    return r.json()


def _post(endpoint: str, params: dict = None) -> dict:
    r = requests.post(
        f"{API_BASE}{endpoint}",
        headers=_headers(),
        params=params,
        timeout=15,
    )
    if not r.ok:
        raise RuntimeError(f"API error {r.status_code}: {r.json().get('detail')}")
    return r.json()

def render():
    st.title(" A/B Model Testing")
    st.caption("Compare XGBoost (A) vs LightGBM (B) on live traffic.")

    # ─────────────────────────────────────────
    # Current config
    # ─────────────────────────────────────────
    section_header("Current Configuration")
    try:
        config = _get("/ab/config")
    except RuntimeError as e:
        st.error(str(e))
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Mode",        config["mode"].upper(),        colour="#7F77DD")
    with c2:
        metric_card("Traffic Split",
                    f"{int(config['traffic_split_pct']*100)}% A / "
                    f"{int((1-config['traffic_split_pct'])*100)}% B",
                    colour="#3B8BD4")
    with c3:
        status_colour = "#1D9E75" if config["enabled"] else "#E24B4A"
        metric_card("Status",
                    " Active" if config["enabled"] else "⏸ Paused",
                    colour=status_colour)

    st.info(f" **Experiment:** `{config.get('active_test_id', 'N/A')}` "
            f"— {config['description']}")

    # ─────────────────────────────────────────
    # Controls
    # ─────────────────────────────────────────
    st.markdown("---")
    section_header("Controls", "Adjust traffic split or force a model")

    ctrl1, ctrl2 = st.columns(2)

    with ctrl1:
        st.markdown("**Traffic Mode**")
        new_mode = st.selectbox(
            "Mode", ["auto", "xgb", "lgbm"],
            index=["auto", "xgb", "lgbm"].index(config["mode"]),
            label_visibility="collapsed",
        )
        split_pct = st.slider(
            "% traffic to XGBoost (A)",
            0, 100,
            int(config["traffic_split_pct"] * 100),
            disabled=(new_mode != "auto"),
        )
        if st.button(" Save config", type="primary"):
            try:
                _post("/ab/config", params={
                    "mode": new_mode,
                    "traffic_split_pct": split_pct / 100,
                })
                st.success(" Config updated.")
                st.rerun()
            except RuntimeError as e:
                st.error(str(e))

    with ctrl2:
        st.markdown("**New Experiment**")
        new_test_id = st.text_input(
            "Experiment ID",
            placeholder="e.g. experiment-002",
        )
        if st.button(" Start new experiment"):
            if not new_test_id:
                st.warning("Enter an experiment ID first.")
            else:
                try:
                    _post("/ab/reset", params={"new_test_id": new_test_id})
                    st.success(f" New experiment started: {new_test_id}")
                    st.rerun()
                except RuntimeError as e:
                    st.error(str(e))

    # ─────────────────────────────────────────
    # Live stats
    # ─────────────────────────────────────────
    st.markdown("---")
    section_header("Live Performance Stats")

    try:
        stats_data = _get("/ab/stats")
    except RuntimeError as e:
        st.error(str(e))
        return

    if "message" in stats_data and not stats_data.get("group_a", {}).get("count"):
        st.info(stats_data["message"])
        st.caption("Score some applicants first — the A/B router will automatically "
                   "tag each prediction to group A or B.")
        return

    exp   = stats_data.get("experiment", {})
    a     = stats_data.get("group_a", {})
    b     = stats_data.get("group_b", {})

    st.caption(
        f"Experiment: `{exp.get('test_id', 'N/A')}` · "
        f"Total predictions: **{exp.get('total_predictions', 0)}** · "
        f"Split: {int(exp.get('traffic_split_pct', 0.5)*100)}% A / "
        f"{int((1-exp.get('traffic_split_pct', 0.5))*100)}% B"
    )

    # ── KPI comparison table
    metrics = [
        ("Predictions",    str(a.get("count", 0)),
                           str(b.get("count", 0))),
        ("Avg. PD",        f"{a.get('avg_pd', 0):.1%}",
                           f"{b.get('avg_pd', 0):.1%}"),
        ("Avg. Score",     str(int(a.get("avg_score", 0))),
                           str(int(b.get("avg_score", 0)))),
        ("Approval Rate",  f"{a.get('approval_rate', 0):.1%}",
                           f"{b.get('approval_rate', 0):.1%}"),
        ("Avg. Confidence",f"{a.get('avg_confidence', 0):.1%}",
                           f"{b.get('avg_confidence', 0):.1%}"),
    ]

    col_label, col_a, col_b = st.columns([2, 1, 1])
    col_label.markdown("**Metric**")
    col_a.markdown("** A — XGBoost**")
    col_b.markdown("** B — LightGBM**")

    for label, val_a, val_b in metrics:
        col_label.write(label)
        col_a.write(val_a)
        col_b.write(val_b)

    # ── Side-by-side bar chart
    st.markdown("---")
    section_header("Decision Distribution by Model")

    categories = ["Approve", "Review", "Reject"]
    vals_a = [
        a.get("approve_count", 0),
        a.get("review_count",  0),
        a.get("reject_count",  0),
    ]
    vals_b = [
        b.get("approve_count", 0),
        b.get("review_count",  0),
        b.get("reject_count",  0),
    ]

    fig = go.Figure(data=[
        go.Bar(name="A — XGBoost",  x=categories, y=vals_a,
               marker_color="#1D9E75", opacity=0.85),
        go.Bar(name="B — LightGBM", x=categories, y=vals_b,
               marker_color="#3B8BD4", opacity=0.85),
    ])
    fig.update_layout(
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=40, b=20),
        height=320,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ─────────────────────────────────────────
    # Declare winner
    # ─────────────────────────────────────────
    st.markdown("---")
    section_header("Declare Winner")

    if st.button(" Analyse and declare winner", type="primary"):
        try:
            winner_data = _get("/ab/winner")
            winner      = winner_data.get("winner")
            confidence  = winner_data.get("confidence", "Low")
            rec         = winner_data.get("recommendation", "")
            scores      = winner_data.get("scores", {})
            margin      = winner_data.get("margin", 0)

            if not winner:
                st.warning(winner_data.get("message", "Not enough data."))
            else:
                if "XGBoost" in winner:
                    st.success(f" **Winner: {winner}**")
                else:
                    st.info(f" **Winner: {winner}**")

                s1, s2, s3 = st.columns(3)
                s1.metric("XGBoost score",  f"{scores.get('A_XGBoost', 0):.4f}")
                s2.metric("LightGBM score", f"{scores.get('B_LightGBM', 0):.4f}")
                s3.metric("Margin",         f"{margin:.4f}", help="Higher = more decisive win")

                conf_colour = {"High": "", "Medium": "", "Low": ""}.get(confidence, "")
                st.info(f"{conf_colour} **Confidence: {confidence}** — {rec}")

                # Quick-promote button
                winner_key = winner_data.get("winner_key")
                if st.button(f" Promote {winner} — route all traffic to winner"):
                    _post("/ab/config", params={"mode": winner_key})
                    st.success(f" All traffic now routed to {winner}.")
                    st.rerun()

        except RuntimeError as e:
            st.error(str(e))