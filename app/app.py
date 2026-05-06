"""
Domain Intelligence Dashboard — Streamlit App
Premium dark-themed dashboard for expiring domain discovery and scoring.
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timezone

from utils.config import DATA_FILE, HIGH_VALUE_THRESHOLD, MEDIUM_VALUE_THRESHOLD

# ─────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Domain Intelligence — Expiring Domain Scanner",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Domain Intelligence App — AI-powered expiring domain discovery and scoring.",
    },
)

# ─────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    * { font-family: 'Inter', sans-serif !important; }
    
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* Header gradient */
    .header-gradient {
        background: linear-gradient(135deg, #7C3AED 0%, #06B6D4 50%, #10B981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.8rem;
        font-weight: 800;
        letter-spacing: -1px;
        margin-bottom: 0;
        line-height: 1.1;
    }
    
    .header-subtitle {
        color: #94A3B8;
        font-size: 1.05rem;
        font-weight: 400;
        margin-top: 4px;
        margin-bottom: 1.5rem;
    }
    
    /* KPI Cards */
    .kpi-card {
        background: linear-gradient(145deg, #1E1E32 0%, #16162A 100%);
        border: 1px solid rgba(124, 58, 237, 0.2);
        border-radius: 16px;
        padding: 1.4rem 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    .kpi-card:hover {
        border-color: rgba(124, 58, 237, 0.5);
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(124, 58, 237, 0.15);
    }
    .kpi-value {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #7C3AED, #06B6D4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 2px;
    }
    .kpi-label {
        color: #94A3B8;
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Top domains section */
    .top-domain-card {
        background: linear-gradient(145deg, #1A1A2E 0%, #16162A 100%);
        border: 1px solid rgba(16, 185, 129, 0.25);
        border-radius: 12px;
        padding: 0.9rem 1.2rem;
        margin-bottom: 0.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.2s ease;
    }
    .top-domain-card:hover {
        border-color: rgba(16, 185, 129, 0.6);
        background: linear-gradient(145deg, #1E1E35 0%, #1A1A30 100%);
    }
    
    /* Value tags */
    .tag-high {
        background: linear-gradient(135deg, #10B981, #059669);
        color: white;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .tag-medium {
        background: linear-gradient(135deg, #F59E0B, #D97706);
        color: white;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .tag-low {
        background: linear-gradient(135deg, #6B7280, #4B5563);
        color: white;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.3rem;
        font-weight: 700;
        color: #E2E8F0;
        margin-top: 2rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F0F1A 0%, #1A1A2E 100%);
    }
    [data-testid="stSidebar"] .stMarkdown h1 {
        font-size: 1.2rem;
        color: #7C3AED;
    }
    
    /* Table styling */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* Plotly chart container */
    .stPlotlyChart {
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #7C3AED, #06B6D4);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        padding: 0.6rem 1.5rem;
        transition: all 0.3s ease;
    }
    .stDownloadButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.4);
    }
    
    /* Updated timestamp */
    .updated-badge {
        background: rgba(124, 58, 237, 0.15);
        border: 1px solid rgba(124, 58, 237, 0.3);
        border-radius: 8px;
        padding: 4px 12px;
        font-size: 0.78rem;
        color: #A78BFA;
        display: inline-block;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Data Loading
# ─────────────────────────────────────────────
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data() -> pd.DataFrame:
    """Load the scored domains dataset."""
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE)
    else:
        # Run pipeline inline if no data exists
        try:
            from pipeline.run_pipeline import run_pipeline
            run_pipeline()
            df = pd.read_csv(DATA_FILE)
        except Exception:
            st.error("⚠️ No data available. Please run the pipeline first.")
            return pd.DataFrame()
    
    # Ensure numeric columns
    numeric_cols = ["score", "estimated_price", "days_until_expiry",
                    "keyword_score", "trend_score", "tld_score",
                    "brandability_score", "length_score"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    
    return df


# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
st.markdown('<h1 class="header-gradient">🔍 Domain Intelligence</h1>', unsafe_allow_html=True)
st.markdown('<p class="header-subtitle">AI-powered expiring domain discovery • Real-time scoring • Global coverage</p>', unsafe_allow_html=True)

# Load data
df = load_data()

if df.empty:
    st.warning("No domain data available. Please run the pipeline first: `python -m pipeline.run_pipeline`")
    st.stop()

# Last updated badge
if "scored_at" in df.columns:
    latest = df["scored_at"].max()
    st.markdown(f'<div class="updated-badge">📡 Last updated: {latest}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Sidebar Filters
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎛️ Filters")
    st.markdown("---")
    
    # Expiry window
    st.markdown("**⏰ Expiry Window**")
    expiry_options = ["All"] + sorted(df["expiry_window"].dropna().unique().tolist()) if "expiry_window" in df.columns else ["All"]
    selected_expiry = st.selectbox("Select window", expiry_options, label_visibility="collapsed")
    
    # Score range
    st.markdown("**📊 Score Range**")
    score_min, score_max = st.slider(
        "Score", 0, 100, (0, 100), label_visibility="collapsed"
    )
    
    # TLD filter
    st.markdown("**🌐 TLD Filter**")
    if "tld" in df.columns:
        all_tlds = sorted(df["tld"].dropna().unique().tolist())
        selected_tlds = st.multiselect("TLDs", all_tlds, default=[], placeholder="All TLDs")
    else:
        selected_tlds = []
        
    # Country filter
    st.markdown("**🌍 Country Filter**")
    if "country" in df.columns:
        all_countries = sorted(df["country"].dropna().unique().tolist())
        selected_countries = st.multiselect("Countries", all_countries, default=[], placeholder="All Countries")
    else:
        selected_countries = []
    
    # Keyword search
    st.markdown("**🔎 Keyword Search**")
    keyword = st.text_input("Search domains", placeholder="e.g., cloud, ai, pay", label_visibility="collapsed")
    
    # Value tag filter
    st.markdown("**🏷️ Value Tag**")
    tag_options = ["All", "High Value", "Medium Value", "Low Value"]
    selected_tag = st.selectbox("Tag", tag_options, label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("### 📥 Export")

# ─────────────────────────────────────────────
# Apply Filters
# ─────────────────────────────────────────────
filtered = df.copy()

if selected_expiry != "All" and "expiry_window" in filtered.columns:
    filtered = filtered[filtered["expiry_window"] == selected_expiry]

filtered = filtered[(filtered["score"] >= score_min) & (filtered["score"] <= score_max)]

if selected_tlds:
    filtered = filtered[filtered["tld"].isin(selected_tlds)]

if selected_countries:
    filtered = filtered[filtered["country"].isin(selected_countries)]

if keyword:
    filtered = filtered[filtered["domain"].str.contains(keyword.lower(), case=False, na=False)]

if selected_tag != "All":
    filtered = filtered[filtered["tag"] == selected_tag]

# ─────────────────────────────────────────────
# KPI Metrics
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">📈 Summary Metrics</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{len(filtered):,}</div>
        <div class="kpi-label">Total Domains</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    high_count = len(filtered[filtered["tag"] == "High Value"])
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{high_count}</div>
        <div class="kpi-label">High Value</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    expiring_soon = len(filtered[filtered["expiry_window"] == "1 Day"]) if "expiry_window" in filtered.columns else 0
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{expiring_soon}</div>
        <div class="kpi-label">Expiring 24h</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    avg_score = filtered["score"].mean() if len(filtered) > 0 else 0
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{avg_score:.1f}</div>
        <div class="kpi-label">Avg Score</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Top 10 Domains of the Day
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">🏆 Top 10 Domains of the Day</div>', unsafe_allow_html=True)

top10 = filtered.nlargest(10, "score")

if len(top10) > 0:
    for _, row in top10.iterrows():
        tag_class = "tag-high" if row["tag"] == "High Value" else ("tag-medium" if row["tag"] == "Medium Value" else "tag-low")
        price_display = f"${row['estimated_price']:.0f}" if row['estimated_price'] >= 100 else f"${row['estimated_price']:.2f}"
        
        st.markdown(f"""
        <div class="top-domain-card">
            <div>
                <span style="font-weight:700; font-size:1.05rem; color:#E2E8F0;">{row['domain']}</span>
                <span class="{tag_class}">{row['tag']}</span>
            </div>
            <div style="display:flex; gap:24px; align-items:center;">
                <div style="text-align:center;">
                    <div style="font-weight:700; color:#7C3AED; font-size:1.1rem;">{row['score']:.0f}</div>
                    <div style="font-size:0.7rem; color:#64748B;">SCORE</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-weight:700; color:#06B6D4; font-size:1.1rem;">{price_display}</div>
                    <div style="font-size:0.7rem; color:#64748B;">EST. PRICE</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-weight:700; color:#10B981; font-size:1.1rem;">{row.get('expiry_window', 'N/A')}</div>
                    <div style="font-size:0.7rem; color:#64748B;">EXPIRES IN</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No domains match the current filters.")

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Main Data Table
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">📋 Domain Explorer</div>', unsafe_allow_html=True)

display_cols = ["domain", "score", "tag", "estimated_price", "tld", "country", "expiry_window", "days_until_expiry",
                "keyword_score", "trend_score", "brandability_score", "length_score"]
available_cols = [c for c in display_cols if c in filtered.columns]

if len(filtered) > 0:
    display_df = filtered[available_cols].copy()
    display_df = display_df.rename(columns={
        "domain": "Domain",
        "score": "Score",
        "tag": "Tag",
        "estimated_price": "Est. Price ($)",
        "tld": "TLD",
        "country": "Country",
        "expiry_window": "Expiry Window",
        "days_until_expiry": "Days Left",
        "keyword_score": "Keyword",
        "trend_score": "Trend",
        "brandability_score": "Brand",
        "length_score": "Length",
    })
    
    st.dataframe(
        display_df,
        use_container_width=True,
        height=500,
        column_config={
            "Score": st.column_config.ProgressColumn(
                "Score",
                min_value=0,
                max_value=100,
                format="%.0f",
            ),
            "Est. Price ($)": st.column_config.NumberColumn(
                "Est. Price ($)",
                format="$%.2f",
            ),
        },
    )
    
    # Download button in sidebar
    with st.sidebar:
        csv_data = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=f"domain_intelligence_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
else:
    st.info("No domains match the current filters. Try adjusting the sidebar filters.")

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Visualizations
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">📊 Analytics</div>', unsafe_allow_html=True)

viz_col1, viz_col2 = st.columns(2)

with viz_col1:
    st.markdown("#### Score Distribution")
    if len(filtered) > 0:
        fig_hist = px.histogram(
            filtered, x="score", nbins=25,
            color_discrete_sequence=["#7C3AED"],
            labels={"score": "Domain Score", "count": "Count"},
        )
        fig_hist.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#94A3B8",
            xaxis=dict(gridcolor="rgba(148,163,184,0.1)"),
            yaxis=dict(gridcolor="rgba(148,163,184,0.1)"),
            margin=dict(l=20, r=20, t=30, b=20),
            height=350,
        )
        st.plotly_chart(fig_hist, use_container_width=True)

with viz_col2:
    st.markdown("#### TLD Distribution")
    if len(filtered) > 0 and "tld" in filtered.columns:
        tld_counts = filtered["tld"].value_counts().head(10)
        fig_tld = px.pie(
            values=tld_counts.values,
            names=tld_counts.index,
            color_discrete_sequence=px.colors.sequential.Plasma_r,
            hole=0.4,
        )
        fig_tld.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#94A3B8",
            margin=dict(l=20, r=20, t=30, b=20),
            height=350,
            showlegend=True,
            legend=dict(font=dict(size=10)),
        )
        st.plotly_chart(fig_tld, use_container_width=True)

# Row 2: More charts
viz_col3, viz_col4 = st.columns(2)

with viz_col3:
    st.markdown("#### Value Tag Breakdown")
    if len(filtered) > 0:
        tag_counts = filtered["tag"].value_counts()
        colors_map = {"High Value": "#10B981", "Medium Value": "#F59E0B", "Low Value": "#6B7280"}
        fig_tag = go.Figure(data=[
            go.Bar(
                x=tag_counts.index,
                y=tag_counts.values,
                marker_color=[colors_map.get(t, "#6B7280") for t in tag_counts.index],
                text=tag_counts.values,
                textposition="auto",
            )
        ])
        fig_tag.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#94A3B8",
            xaxis=dict(gridcolor="rgba(148,163,184,0.1)"),
            yaxis=dict(gridcolor="rgba(148,163,184,0.1)"),
            margin=dict(l=20, r=20, t=30, b=20),
            height=350,
        )
        st.plotly_chart(fig_tag, use_container_width=True)

with viz_col4:
    st.markdown("#### Score vs Estimated Price")
    if len(filtered) > 0:
        fig_scatter = px.scatter(
            filtered.head(200),
            x="score",
            y="estimated_price",
            color="tag",
            size="score",
            hover_data=["domain", "tld"],
            color_discrete_map={
                "High Value": "#10B981",
                "Medium Value": "#F59E0B",
                "Low Value": "#6B7280",
            },
            labels={"score": "Score", "estimated_price": "Est. Price ($)"},
        )
        fig_scatter.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#94A3B8",
            xaxis=dict(gridcolor="rgba(148,163,184,0.1)"),
            yaxis=dict(gridcolor="rgba(148,163,184,0.1)"),
            margin=dict(l=20, r=20, t=30, b=20),
            height=350,
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

# ─────────────────────────────────────────────
# Expiry Timeline
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">⏳ Expiry Timeline</div>', unsafe_allow_html=True)

if "expiry_window" in filtered.columns and len(filtered) > 0:
    expiry_dist = filtered["expiry_window"].value_counts().reindex(["1 Day", "7 Days", "30 Days", "30+ Days"]).fillna(0)
    fig_timeline = go.Figure(data=[
        go.Bar(
            x=expiry_dist.index,
            y=expiry_dist.values,
            marker=dict(
                color=["#EF4444", "#F59E0B", "#06B6D4", "#6B7280"],
            ),
            text=expiry_dist.values.astype(int),
            textposition="auto",
            textfont=dict(color="white", size=14, family="Inter"),
        )
    ])
    fig_timeline.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#94A3B8",
        xaxis=dict(gridcolor="rgba(148,163,184,0.1)", title="Expiry Window"),
        yaxis=dict(gridcolor="rgba(148,163,184,0.1)", title="Number of Domains"),
        margin=dict(l=20, r=20, t=30, b=20),
        height=300,
    )
    st.plotly_chart(fig_timeline, use_container_width=True)

# ─────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#64748B; font-size:0.8rem; padding: 1rem 0;">
    <strong>Domain Intelligence</strong> • AI-Powered Domain Discovery Engine<br>
    Data sources: RDAP Protocol, Public Domain Lists, Seed Generation<br>
    Scoring: Keyword Analysis • Trend Relevance • Brandability • TLD Value<br>
    <span style="color:#7C3AED;">Built with Streamlit • Automated via GitHub Actions</span>
</div>
""", unsafe_allow_html=True)
