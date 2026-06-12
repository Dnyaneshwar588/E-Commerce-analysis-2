import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Premium CSS Stylesheet for SaaS E-Commerce Customer Analytics Dashboard
CSS_STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

/* Global Font Override */
html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
}

/* Sidebar Custom Styling */
[data-testid="stSidebar"] {
    background-color: #0f172a;
    color: #f8fafc;
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}

[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3, 
[data-testid="stSidebar"] h4, 
[data-testid="stSidebar"] span, 
[data-testid="stSidebar"] label {
    color: #f8fafc !important;
}

/* Custom styled sidebar radio buttons */
[data-testid="stSidebar"] .stRadio > div {
    gap: 6px;
}

[data-testid="stSidebar"] .stRadio label {
    background: rgba(255, 255, 255, 0.03);
    padding: 10px 14px;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    cursor: pointer;
    display: block;
    width: 100%;
}

[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(99, 102, 241, 0.15);
    border-color: rgba(99, 102, 241, 0.4);
    transform: translateX(4px);
}

[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"] {
    background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%) !important;
    border-color: #6366f1 !important;
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
}

/* Main Dashboard Canvas Background */
.stApp {
    background: 
        radial-gradient(circle at 0% 0%, rgba(99, 102, 241, 0.06) 0%, transparent 40%),
        radial-gradient(circle at 100% 100%, rgba(14, 165, 233, 0.05) 0%, transparent 40%),
        linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}

/* Glassmorphic Header Hero Banner */
.hero {
    padding: 2.5rem;
    border-radius: 28px;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.06);
    box-shadow: 0 20px 40px rgba(15, 23, 42, 0.15);
    margin-bottom: 2.2rem;
    position: relative;
    overflow: hidden;
}

.hero::after {
    content: '';
    position: absolute;
    top: -40%;
    right: -40%;
    width: 300px;
    height: 300px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(99, 102, 241, 0.25) 0%, transparent 70%);
    pointer-events: none;
}

.hero h1 {
    margin: 0;
    font-size: 2.8rem;
    line-height: 1.15;
    font-weight: 800;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #ffffff 30%, #cbd5e1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero p {
    margin: 0.8rem 0 0;
    color: #94a3b8;
    font-size: 1.15rem;
    font-weight: 400;
    line-height: 1.5;
    max-width: 800px;
}

/* Metric Section Titles */
.section-title {
    font-size: 1.45rem;
    font-weight: 700;
    color: #0f172a;
    margin: 2rem 0 1.2rem;
    letter-spacing: -0.02em;
    border-bottom: 2px solid rgba(226, 232, 240, 0.8);
    padding-bottom: 0.5rem;
}

/* Glassmorphic Metric Cards */
.glass-metric {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255, 255, 255, 0.5);
    border-radius: 24px;
    padding: 1.6rem;
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.03);
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    margin-bottom: 1.2rem;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 100%;
    min-height: 140px;
}

.glass-metric:hover {
    transform: translateY(-6px);
    box-shadow: 0 20px 40px rgba(15, 23, 42, 0.08);
    border-color: rgba(99, 102, 241, 0.35);
    background: rgba(255, 255, 255, 0.9);
}

.metric-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.6rem;
}

.metric-title {
    font-size: 0.85rem;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.07em;
}

.metric-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 38px;
    height: 38px;
    border-radius: 12px;
    font-size: 1.15rem;
}

.metric-value {
    font-size: 2.1rem;
    font-weight: 800;
    color: #0f172a;
    line-height: 1.1;
    letter-spacing: -0.03em;
    margin-top: 0.2rem;
}

.metric-subtext {
    font-size: 0.82rem;
    color: #475569;
    font-weight: 600;
    margin-top: 0.6rem;
    display: flex;
    align-items: center;
    gap: 0.3rem;
}

/* Glassmorphic Cards for Tables & Info */
.glass-card {
    background: rgba(255, 255, 255, 0.65);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.5);
    border-radius: 22px;
    padding: 1.5rem;
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.03);
    margin-bottom: 1.8rem;
}

/* Styled Business Insights Container */
.insight-box {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.8) 0%, rgba(255, 255, 255, 0.6) 100%);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 24px;
    padding: 1.8rem;
    box-shadow: 0 15px 35px rgba(15, 23, 42, 0.04);
    margin-bottom: 2rem;
}

.insight-item {
    padding: 0.75rem 0;
    border-bottom: 1px solid rgba(226, 232, 240, 0.6);
    display: flex;
    align-items: start;
    gap: 0.65rem;
    font-size: 0.98rem;
    color: #334155;
    font-weight: 500;
    line-height: 1.45;
}

.insight-item:last-child {
    border-bottom: none;
}

.small-note {
    color: #64748b;
    font-size: 0.82rem;
    line-height: 1.5;
}

/* Primary buttons styling */
.stButton>button {
    background: linear-gradient(135deg, #4f46e5 0%, #2563eb 100%);
    color: white;
    border: none;
    padding: 0.6rem 1.8rem;
    border-radius: 12px;
    font-weight: 600;
    box-shadow: 0 4px 14px rgba(79, 70, 229, 0.25);
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(79, 70, 229, 0.4);
    background: linear-gradient(135deg, #6366f1 0%, #3b82f6 100%);
    border: none;
    color: white;
}

/* Custom styled tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    background-color: rgba(241, 245, 249, 0.9);
    padding: 8px;
    border-radius: 16px;
    border: 1px solid rgba(226, 232, 240, 0.8);
}

.stTabs [data-baseweb="tab"] {
    height: 44px;
    white-space: nowrap;
    background-color: transparent;
    border-radius: 12px;
    color: #475569;
    font-size: 0.9rem;
    font-weight: 600;
    border: none;
    padding: 0 16px;
    transition: all 0.25s ease;
}

.stTabs [data-baseweb="tab"]:hover {
    background-color: rgba(255, 255, 255, 0.6);
    color: #0f172a;
}

.stTabs [aria-selected="true"] {
    background-color: #ffffff !important;
    color: #4f46e5 !important;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
}
</style>
"""

# Categorical Color Palette - SaaS Slate/Indigo Theme
PLOTLY_THEME_COLORS = [
    "#6366f1",  # Indigo
    "#10b981",  # Emerald Green
    "#f59e0b",  # Amber/Gold
    "#ec4899",  # Pink
    "#06b6d4",  # Cyan
    "#8b5cf6",  # Violet
    "#f97316",  # Orange
    "#ef4444",  # Red
]


def apply_plotly_style(fig):
    """Apply premium SaaS/Modern styling to Plotly figures."""
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_family="'Outfit', sans-serif",
        font_color="#475569",
        title_font_size=16,
        title_font_color="#0f172a",
        title_font_family="'Outfit', sans-serif",
        legend_title_font_color="#64748b",
        legend=dict(
            font=dict(
                color="#334155",
                size=11
            )
        ),
        margin=dict(t=60, b=40, l=45, r=20),
        colorway=PLOTLY_THEME_COLORS,
        hoverlabel=dict(
            bgcolor="#0f172a",
            font_size=13,
            font_color="#ffffff",
            font_family="'Outfit', sans-serif"
        )
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(226, 232, 240, 0.5)",
        linecolor="rgba(226, 232, 240, 0.9)",
        tickfont=dict(color="#64748b", size=11),
        title_font=dict(color="#475569", size=12, family="'Outfit', sans-serif")
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(226, 232, 240, 0.5)",
        linecolor="rgba(226, 232, 240, 0.9)",
        tickfont=dict(color="#64748b", size=11),
        title_font=dict(color="#475569", size=12, family="'Outfit', sans-serif")
    )
    if hasattr(fig.layout, "yaxis2") and fig.layout.yaxis2 is not None:
        fig.update_layout(
            yaxis2=dict(
                showgrid=False,
                linecolor="rgba(226, 232, 240, 0.9)",
                tickfont=dict(color="#64748b", size=11),
                title_font=dict(color="#475569", size=12, family="'Outfit', sans-serif")
            )
        )
    return fig


def render_metric_card(title, value, subtext, icon_emoji, border_color="#4f46e5"):
    """Render a premium glassmorphic metric card using HTML/CSS."""
    card_html = f"""
    <div class="glass-metric" style="border-top: 4px solid {border_color};">
        <div class="metric-header">
            <span class="metric-title">{title}</span>
            <span class="metric-icon" style="background-color: {border_color}15; color: {border_color};">{icon_emoji}</span>
        </div>
        <div>
            <div class="metric-value">{value}</div>
            <div class="metric-subtext">{subtext}</div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_header(title="E-commerce Customer Analytics Dashboard", subtitle="Business-focused sales, customer, regional, product, and fulfillment analysis powered by Python, SQL, and Streamlit."):
    """Render the glassmorphic hero header."""
    header_html = f"""
    <div class="hero">
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)


def render_footer():
    """Render the dashboard placement/portfolio-ready footer."""
    pass


def render_insights_box(insights):
    """Render business insights callouts inside a frosted-glass container."""
    items = "".join([f"<div class='insight-item'><span style='margin-right: 0.5rem; flex-shrink: 0;'>💡</span><span>{item}</span></div>" for item in insights])
    st.markdown(
        f"<div class='insight-box'><h4 style='margin-top:0; margin-bottom:0.8rem; color:#0f172a; font-weight:700;'>📊 Business Analytics Insights</h4>{items}</div>",
        unsafe_allow_html=True,
    )


def render_info_card(title, text, emoji="💡", color="#4f46e5"):
    """Render a nice styled descriptive card for context."""
    card_html = f"""
    <div class="glass-card" style="border-left: 4px solid {color}; margin-bottom: 1.5rem;">
        <h5 style="margin-top:0; margin-bottom:0.4rem; color:#0f172a; font-weight:700;">{emoji} {title}</h5>
        <div style="font-size:0.94rem; color:#475569; line-height:1.5;">{text}</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_styled_dataframe(df, numeric_cols=None, currency_cols=None, pct_cols=None):
    """Render a clean, stylized Streamlit dataframe with formatted columns."""
    column_config = {}
    
    if numeric_cols:
        for col in numeric_cols:
            column_config[col] = st.column_config.NumberColumn(format="%d")
            
    if currency_cols:
        for col in currency_cols:
            column_config[col] = st.column_config.NumberColumn(format="₹%,.2f")
            
    if pct_cols:
        for col in pct_cols:
            column_config[col] = st.column_config.NumberColumn(format="%.1f%%")
            
    st.dataframe(df, use_container_width=True, column_config=column_config)
