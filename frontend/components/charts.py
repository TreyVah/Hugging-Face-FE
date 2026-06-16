"""
All chart-rendering functions.
Each returns a Plotly figure — caller uses st.plotly_chart(fig).
Keeping charts here means pages stay clean and charts are testable.
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List


# ── Colour constants (match risk bands) ──────
COLOURS = {
    "APPROVE": "#00E5A0",
    "REVIEW":  "#FFB800",
    "REJECT":  "#FF4D6A",
    "Low Risk":    "#00E5A0",
    "Medium Risk": "#FFB800",
    "High Risk":   "#FF4D6A",
}

LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(13,11,26,0.6)",
    font=dict(family="sans-serif", size=13, color="#8B83B0"),
    margin=dict(l=20, r=20, t=40, b=20),
    xaxis=dict(
        gridcolor="rgba(110,86,255,0.1)",
        zerolinecolor="rgba(110,86,255,0.15)",
        color="#8B83B0",
    ),
    yaxis=dict(
        gridcolor="rgba(110,86,255,0.1)",
        zerolinecolor="rgba(110,86,255,0.15)",
        color="#8B83B0",
    ),
)


def pd_gauge(probability: float) -> go.Figure:
    """
    Speedometer-style gauge showing probability of default.
    Green (safe) → Red (risky) colour band.
    """
    pct = round(probability * 100, 1)
    if probability < 0.2:
        color = "#00E5A0"
    elif probability < 0.5:
        color = "#FFB800"
    else:
        color = "#FF4D6A"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=pct,
        number={"suffix": "%", "font": {"size": 36}},
        delta={"reference": 20, "suffix": "%", "decreasing": {"color": "#1D9E75"}},
        title={"text": "Probability of Default", "font": {"size": 15}},
        gauge={
            "axis": {"range": [0, 100], "ticksuffix": "%"},
            "bar":  {"color": color, "thickness": 0.3},
            "steps": [
    {"range": [0,  20],  "color": "rgba(0,229,160,0.12)"},
    {"range": [20, 50],  "color": "rgba(255,184,0,0.12)"},
    {"range": [50, 100], "color": "rgba(255,77,106,0.12)"},
],
            "threshold": {
                "line": {"color": "#333", "width": 3},
                "value": pct,
            },
        },
    ))
    fig.update_layout(**LAYOUT, height=260)
    return fig


def credit_score_gauge(score: int) -> go.Figure:
    """FICO-style credit score bar: 300–850."""
    if score >= 700:
        color = "#1D9E75"
    elif score >= 580:
        color = "#EF9F27"
    else:
        color = "#E24B4A"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": "Credit Score", "font": {"size": 15}},
        gauge={
            "axis": {"range": [300, 850]},
            "bar":  {"color": color, "thickness": 0.3},
            "steps": [
                {"range": [300, 580], "color": "#FCEBEB"},
                {"range": [580, 700], "color": "#FAEEDA"},
                {"range": [700, 850], "color": "#E1F5EE"},
            ],
        },
    ))
    fig.update_layout(**LAYOUT, height=240)
    return fig


def shap_bar_chart(feature_impacts: list) -> go.Figure:
    """
    Horizontal bar chart of SHAP feature impacts.
    Red bars = increase default risk.
    Green bars = decrease default risk (protective).
    Sorted by absolute impact, top 12 shown.
    """
    df = pd.DataFrame(feature_impacts).head(12)
    df = df.sort_values("shap_value")

    colours = ["#E24B4A" if v > 0 else "#1D9E75" for v in df["shap_value"]]

    fig = go.Figure(go.Bar(
        x=df["shap_value"],
        y=df["feature"],
        orientation="h",
        marker_color=colours,
        text=[f"{v:+.4f}" for v in df["shap_value"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>SHAP: %{x:.5f}<extra></extra>",
    ))
    fig.add_vline(x=0, line_width=1, line_color="gray", opacity=0.5)
    fig.update_layout(
        **LAYOUT,
        title="Feature Impact (SHAP values)",
        height=420,
        xaxis_title="Impact on default probability",
        yaxis_title=None,
    )
    return fig


def decision_pie(history_items: list) -> go.Figure:
    """Donut chart: Approve / Review / Reject breakdown."""
    counts = {"APPROVE": 0, "REVIEW": 0, "REJECT": 0}
    for item in history_items:
        d = item.get("decision", "")
        if d in counts:
            counts[d] += 1

    labels = list(counts.keys())
    values = list(counts.values())
    colours = [COLOURS[l] for l in labels]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker_colors=colours,
        textinfo="label+percent",
        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
    ))
    fig.update_layout(**LAYOUT, title="Decision breakdown", height=320)
    return fig


def pd_histogram(history_items: list) -> go.Figure:
    """Distribution of probability of default across all predictions."""
    pds = [i.get("probability_of_default", 0) * 100 for i in history_items]
    if not pds:
        return go.Figure()

    fig = go.Figure(go.Histogram(
        x=pds,
        nbinsx=20,
        marker_color="#3B8BD4",
        opacity=0.8,
        hovertemplate="PD: %{x:.1f}%<br>Count: %{y}<extra></extra>",
    ))
    fig.add_vline(x=20, line_dash="dash", line_color="#E24B4A",
                  annotation_text="20% threshold")
    fig.update_layout(
        **LAYOUT,
        title="PD distribution",
        xaxis_title="Probability of Default (%)",
        yaxis_title="Count",
        height=300,
    )
    return fig


def score_over_time(history_items: list) -> go.Figure:
    """Line chart: credit score trend over time."""
    if not history_items:
        return go.Figure()

    df = pd.DataFrame(history_items)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df = df.sort_values("created_at")

    fig = go.Figure(go.Scatter(
        x=df["created_at"],
        y=df["credit_score"],
        mode="lines+markers",
        line=dict(color="#3B8BD4", width=2),
        marker=dict(
            size=7,
            color=[COLOURS.get(d, "#888") for d in df["decision"]],
            line=dict(width=1, color="white"),
        ),
        hovertemplate=(
            "<b>%{x|%Y-%m-%d %H:%M}</b><br>"
            "Score: %{y}<extra></extra>"
        ),
    ))
    fig.add_hline(y=700, line_dash="dash", line_color="#1D9E75",
                  annotation_text="Approve threshold (700)")
    fig.add_hline(y=580, line_dash="dash", line_color="#EF9F27",
                  annotation_text="Review threshold (580)")
    fig.update_layout(
        **LAYOUT,
        title="Credit score over time",
        height=300,
    )
    fig.update_yaxes(range=[250, 900])
    return fig