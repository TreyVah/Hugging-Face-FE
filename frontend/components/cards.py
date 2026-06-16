"""
RiskNova UI components — Dark Purple + Cyan fintech theme.
"""
import streamlit as st

# ── Theme colours
PURPLE      = "#6E56FF"
PURPLE_LIGHT= "#9B85FF"
CYAN        = "#00D4FF"
SURFACE     = "#13102A"
SURFACE2    = "#1A1535"
BORDER      = "rgba(110,86,255,0.18)"
TEXT        = "#E8E4FF"
MUTED       = "#8B83B0"
APPROVE     = "#00E5A0"
REVIEW      = "#FFB800"
REJECT      = "#FF4D6A"


def inject_global_css():
    """Call once at the top of every page render."""
    st.markdown("""
    <style>
    /* ── Page background */
    .stApp { background: #0D0B1A !important; }
    section[data-testid="stSidebar"] {
        background: #13102A !important;
        border-right: 1px solid rgba(110,86,255,0.18) !important;
    }

    /* ── Sidebar nav buttons */
    section[data-testid="stSidebar"] .stButton button {
        background: transparent !important;
        border: none !important;
        color: #8B83B0 !important;
        text-align: left !important;
        font-size: 14px !important;
        padding: 8px 12px !important;
        border-radius: 6px !important;
        transition: all 0.15s ease !important;
    }
    section[data-testid="stSidebar"] .stButton button:hover {
        background: rgba(110,86,255,0.1) !important;
        color: #E8E4FF !important;
    }

    /* ── Primary buttons */
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #6E56FF, #00D4FF) !important;
        border: none !important;
        color: #fff !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        letter-spacing: 0.3px !important;
    }
    .stButton button[kind="primary"]:hover {
        opacity: 0.9 !important;
        transform: translateY(-1px) !important;
    }

    /* ── Inputs */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        background: #1A1535 !important;
        border: 1px solid rgba(110,86,255,0.25) !important;
        color: #E8E4FF !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #6E56FF !important;
        box-shadow: 0 0 0 2px rgba(110,86,255,0.15) !important;
    }

    /* ── Metric cards */
    [data-testid="metric-container"] {
        background: #13102A !important;
        border: 1px solid rgba(110,86,255,0.18) !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
    }
    [data-testid="metric-container"] label {
        color: #8B83B0 !important;
        font-size: 11px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #9B85FF !important;
        font-size: 24px !important;
        font-weight: 500 !important;
    }

    /* ── Dataframes */
    .stDataFrame { border: 1px solid rgba(110,86,255,0.18) !important; border-radius: 10px !important; }

    /* ── Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #13102A !important;
        border-radius: 8px !important;
        gap: 4px !important;
        padding: 4px !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #8B83B0 !important;
        border-radius: 6px !important;
    }
    .stTabs [aria-selected="true"] {
        background: #6E56FF !important;
        color: #fff !important;
    }

    /* ── Expander */
    .streamlit-expanderHeader {
        background: #13102A !important;
        border: 1px solid rgba(110,86,255,0.18) !important;
        border-radius: 8px !important;
        color: #E8E4FF !important;
    }

    /* ── Spinner */
    .stSpinner > div { border-top-color: #6E56FF !important; }

    /* ── Scrollbar */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: #0D0B1A; }
    ::-webkit-scrollbar-thumb { background: rgba(110,86,255,0.4); border-radius: 2px; }
    </style>
    """, unsafe_allow_html=True)


def decision_badge(decision: str, risk_band: str, credit_score: int) -> None:
    config = {
        "APPROVE": {
            "bg":     "rgba(0,229,160,0.08)",
            "border": "rgba(0,229,160,0.3)",
            "color":  "#00E5A0",
            "dot":    "#00E5A0",
            "label":  "APPROVED",
        },
        "REVIEW": {
            "bg":     "rgba(255,184,0,0.08)",
            "border": "rgba(255,184,0,0.3)",
            "color":  "#FFB800",
            "dot":    "#FFB800",
            "label":  "MANUAL REVIEW",
        },
        "REJECT": {
            "bg":     "rgba(255,77,106,0.08)",
            "border": "rgba(255,77,106,0.3)",
            "color":  "#FF4D6A",
            "dot":    "#FF4D6A",
            "label":  "REJECTED",
        },
    }
    c = config.get(decision, config["REVIEW"])
    st.markdown(f"""
    <div style="
        background:{c['bg']};
        border:1px solid {c['border']};
        border-radius:14px;
        padding:20px 24px;
        display:flex;
        align-items:center;
        justify-content:space-between;
        margin-bottom:16px;
    ">
        <div style="display:flex;align-items:center;gap:16px;">
            <div style="
                width:48px;height:48px;border-radius:12px;
                background:rgba(255,255,255,0.06);
                display:flex;align-items:center;justify-content:center;
            ">
                <div style="width:16px;height:16px;border-radius:50%;
                    background:{c['dot']};
                    box-shadow:0 0 8px {c['dot']};
                "></div>
            </div>
            <div>
                <div style="
                    font-size:22px;font-weight:500;
                    color:{c['color']};letter-spacing:2px;
                ">{c['label']}</div>
                <div style="font-size:12px;color:#8B83B0;margin-top:3px;">
                    {risk_band} &nbsp;·&nbsp;
                    Credit Score: <span style="color:#E8E4FF;font-weight:500;">{credit_score}</span>
                </div>
            </div>
        </div>
        <div style="
            background:rgba(255,255,255,0.04);
            border:1px solid rgba(255,255,255,0.08);
            border-radius:10px;padding:10px 16px;text-align:center;
        ">
            <div style="font-size:10px;color:#8B83B0;
                text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">
                Decision
            </div>
            <div style="font-size:15px;font-weight:500;color:{c['color']};">
                {decision}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def metric_card(label: str, value: str, delta: str = None,
                colour: str = "#6E56FF") -> None:
    delta_html = ""
    if delta:
        arrow  = "▲" if not delta.startswith("-") else "▼"
        dcol   = "#00E5A0" if not delta.startswith("-") else "#FF4D6A"
        delta_html = (
            f'<div style="font-size:12px;color:{dcol};margin-top:4px;">'
            f'{arrow} {delta}</div>'
        )
    st.markdown(f"""
    <div style="
        background:#13102A;
        border:1px solid rgba(110,86,255,0.18);
        border-top:3px solid {colour};
        border-radius:10px;
        padding:16px 18px;
        text-align:center;
    ">
        <div style="
            font-size:10px;color:#8B83B0;
            text-transform:uppercase;letter-spacing:0.8px;
            font-weight:500;margin-bottom:8px;
        ">{label}</div>
        <div style="font-size:26px;font-weight:500;color:{colour};">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def section_header(title: str, subtitle: str = "") -> None:
    sub = (
        f'<p style="color:#8B83B0;font-size:13px;margin:3px 0 0;">{subtitle}</p>'
        if subtitle else ""
    )
    st.markdown(f"""
    <div style="
        margin:24px 0 14px;
        padding-left:12px;
        border-left:3px solid #6E56FF;
    ">
        <h3 style="
            margin:0;font-size:16px;font-weight:500;
            color:#E8E4FF;letter-spacing:0.2px;
        ">{title}</h3>
        {sub}
    </div>
    """, unsafe_allow_html=True)


def api_error(message: str) -> None:
    st.markdown(f"""
    <div style="
        background:rgba(255,77,106,0.08);
        border:1px solid rgba(255,77,106,0.3);
        border-radius:10px;padding:14px 18px;color:#FF4D6A;
        font-size:14px;
    ">
        <strong>Error:</strong> {message}
    </div>
    """, unsafe_allow_html=True)


def info_row(label: str, value: str) -> None:
    st.markdown(f"""
    <div style="
        display:flex;justify-content:space-between;
        padding:9px 0;
        border-bottom:1px solid rgba(110,86,255,0.12);
    ">
        <span style="color:#8B83B0;font-size:13px;">{label}</span>
        <span style="font-weight:500;font-size:13px;color:#E8E4FF;">{value}</span>
    </div>
    """, unsafe_allow_html=True)


def glow_badge(text: str, colour: str) -> str:
    """Returns HTML for a small glowing pill badge."""
    return (
        f'<span style="'
        f'background:rgba({colour},0.12);'
        f'border:1px solid rgba({colour},0.35);'
        f'color:rgb({colour});'
        f'border-radius:20px;padding:3px 10px;font-size:11px;font-weight:500;">'
        f'{text}</span>'
    )