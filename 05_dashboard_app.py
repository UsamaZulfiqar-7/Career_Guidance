"""
STEP 5: Career Guidance Dashboard — Modern UI Edition
------------------------------------------------------
Interactive Streamlit analytics dashboard featuring:
- Theme Support (Light / Dark mode toggle)
- Dynamic Market Overview with interactive Plotly visual representations
- Precomputed Trending Skills tracking with fast fallback
- Real-time Competency Gap Analyzer & Predictive Salary Forecasting
- Resilient Data Readiness Health Checks

Run with: streamlit run 05_dashboard_app.py
"""

import os
import html
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from core.recommender import analyze_skill_gap, predict_salary, load_model_bundle
from core.analytics import calculate_trending_skills_df, calculate_role_salaries_df

st.set_page_config(
    page_title="Career Guidance Tool",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ======================================================================
# THEME SETUP (Light / Dark toggle stored in session_state)
# ======================================================================
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

THEMES = {
    "dark": {
        "bg": "#0E1117",
        "card_bg": "#1A1D27",
        "card_border": "#2A2E3A",
        "text": "#E8E9ED",
        "subtext": "#9CA3AF",
        "accent": "#7C5CFF",
        "accent2": "#00D4B5",
        "accent3": "#FF6B9D",
        "plot_template": "plotly_dark",
        "chart_bg": "rgba(0,0,0,0)",
    },
    "light": {
        "bg": "#F7F8FC",
        "card_bg": "#FFFFFF",
        "card_border": "#E5E7EB",
        "text": "#111827",
        "subtext": "#6B7280",
        "accent": "#6D28D9",
        "accent2": "#0D9488",
        "accent3": "#DB2777",
        "plot_template": "plotly_white",
        "chart_bg": "rgba(0,0,0,0)",
    },
}
T = THEMES[st.session_state.theme]

# ======================================================================
# CUSTOM CSS
# ======================================================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=Space+Grotesk:wght@500;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    .stApp {{
        background-color: {T['bg']};
        color: {T['text']};
    }}

    section[data-testid="stSidebar"] {{
        background-color: {T['card_bg']};
        border-right: 1px solid {T['card_border']};
    }}

    /* Hero header */
    .hero {{
        padding: 1.8rem 2rem;
        border-radius: 18px;
        background: linear-gradient(120deg, {T['accent']}22, {T['accent2']}11);
        border: 1px solid {T['card_border']};
        margin-bottom: 1.5rem;
    }}
    .hero h1 {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.1rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(90deg, {T['accent']}, {T['accent3']});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    .hero p {{
        color: {T['subtext']};
        font-size: 1rem;
        margin-top: 0.4rem;
    }}

    /* Metric cards */
    .metric-card {{
        background: {T['card_bg']};
        border: 1px solid {T['card_border']};
        border-radius: 16px;
        padding: 1.2rem 1.4rem;
        text-align: left;
        transition: transform 0.15s ease;
    }}
    .metric-card:hover {{ transform: translateY(-3px); }}
    .metric-card .label {{
        color: {T['subtext']};
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}
    .metric-card .value {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.9rem;
        font-weight: 700;
        color: {T['text']};
        margin-top: 0.2rem;
    }}
    .metric-card .accent-bar {{
        height: 4px;
        width: 40px;
        border-radius: 4px;
        margin-bottom: 0.6rem;
    }}

    /* Section titles */
    .section-title {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.25rem;
        font-weight: 700;
        color: {T['text']};
        margin: 1.2rem 0 0.6rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}

    /* Result pills */
    .pill-box {{
        background: {T['card_bg']};
        border: 1px solid {T['card_border']};
        border-radius: 14px;
        padding: 1rem 1.2rem;
    }}
    .pill {{
        display: inline-block;
        padding: 0.35rem 0.8rem;
        border-radius: 999px;
        margin: 0.2rem;
        font-size: 0.85rem;
        font-weight: 600;
    }}
    .pill-have {{ background: {T['accent2']}22; color: {T['accent2']}; border: 1px solid {T['accent2']}55; }}
    .pill-missing {{ background: {T['accent3']}22; color: {T['accent3']}; border: 1px solid {T['accent3']}55; }}

    div[data-testid="stTabs"] button {{ font-weight: 600; }}

    .footer-note {{
        text-align: center;
        color: {T['subtext']};
        font-size: 0.8rem;
        padding: 1.5rem 0 0.5rem 0;
    }}

    /* Streamlit widget tweaks */
    .stButton > button {{
        background: linear-gradient(90deg, {T['accent']}, {T['accent3']});
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.55rem 1.4rem;
        font-weight: 600;
    }}
    .stButton > button:hover {{ opacity: 0.9; }}
</style>
""", unsafe_allow_html=True)


def metric_card(label, value, color):
    st.markdown(f"""
    <div class="metric-card">
        <div class="accent-bar" style="background:{color};"></div>
        <div class="label">{label}</div>
        <div class="value">{value}</div>
    </div>
    """, unsafe_allow_html=True)


# ======================================================================
# DATA READINESS CHECK
# ======================================================================
required_files = ["job_postings.csv", "job_skills_exploded.csv", "salary_model.pkl"]
missing_files = [f for f in required_files if not os.path.exists(f)]

if missing_files:
    st.markdown("""
    <div class="hero">
        <h1>🎯 Career Guidance Tool</h1>
        <p>Big Data Analytics Project — data-driven answers to "what skills should I actually learn?"</p>
    </div>
    """, unsafe_allow_html=True)

    st.warning("⚠️ **Pipeline Data Not Yet Initialized**")
    st.info(
        "The following required pipeline artifact(s) were not found: "
        f"`{', '.join(missing_files)}`.\n\n"
        "Please run the pipeline steps in order before launching the dashboard:\n\n"
        "```bash\n"
        "python 01_prepare_real_data.py\n"
        "python 03_spark_skills_analysis.py\n"
        "python 04_recommendation_engine.py\n"
        "```"
    )
    st.stop()


# ======================================================================
# LOAD DATA & MODEL
# ======================================================================
@st.cache_data
def load_data():
    jobs = pd.read_csv("job_postings.csv")
    skills = pd.read_csv("job_skills_exploded.csv")

    trending = None
    if os.path.exists("trending_skills.csv"):
        trending = pd.read_csv("trending_skills.csv")

    role_salaries = None
    if os.path.exists("role_salaries.csv"):
        role_salaries = pd.read_csv("role_salaries.csv")

    return jobs, skills, trending, role_salaries

@st.cache_resource
def load_model():
    return load_model_bundle(".")

jobs, skills, trending_precomputed, role_salaries_precomputed = load_data()
model, encoders, features, metadata = load_model()

# ======================================================================
# SIDEBAR
# ======================================================================
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    icon = "🌙" if st.session_state.theme == "dark" else "☀️"
    st.button(f"{icon} Switch to {'Light' if st.session_state.theme == 'dark' else 'Dark'} Mode",
              on_click=toggle_theme, width='stretch')
    st.divider()
    st.markdown("**About this tool**")
    st.caption("A Big Data Analytics project that analyzes job market data "
               "with PySpark and provides personalized skill and "
               "salary guidance using Machine Learning.")
    st.divider()
    st.caption(f"Dataset: {len(jobs):,} job postings")
    st.caption(f"Skills tracked: {skills['skill'].nunique()}")

# ======================================================================
# HERO HEADER
# ======================================================================
st.markdown("""
<div class="hero">
    <h1>🎯 Career Guidance Tool</h1>
    <p>Big Data Analytics Project — data-driven answers to "what skills should I actually learn?"</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊  Market Overview", "🚀  Trending Skills", "🧭  My Skill Gap & Salary"])

# ================= TAB 1: Market Overview =================
with tab1:
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Total Postings", f"{len(jobs):,}", T["accent"])
    with c2: metric_card("Unique Skills", f"{skills['skill'].nunique()}", T["accent2"])
    with c3: metric_card("Job Roles", f"{jobs['title'].nunique()}", T["accent3"])
    with c4: metric_card("Cities Covered", f"{jobs['city'].nunique()}", T["accent"])

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="section-title">🔥 Top 15 In-Demand Skills</div>', unsafe_allow_html=True)
        top_skills = skills["skill"].value_counts().head(15).sort_values()
        fig = go.Figure(go.Bar(
            x=top_skills.values, y=top_skills.index, orientation="h",
            marker=dict(color=top_skills.values, colorscale=[[0, T["accent"]], [1, T["accent2"]]]),
        ))
        fig.update_layout(template=T["plot_template"], plot_bgcolor=T["chart_bg"], paper_bgcolor=T["chart_bg"],
                          height=460, margin=dict(l=10, r=10, t=10, b=10),
                          xaxis_title="Job Postings", font=dict(color=T["text"]))
        st.plotly_chart(fig, width='stretch')

    with c2:
        st.markdown('<div class="section-title">💰 Average Salary by Role</div>', unsafe_allow_html=True)
        if role_salaries_precomputed is not None and not role_salaries_precomputed.empty:
            top_paying = role_salaries_precomputed.set_index("title")["avg_salary_pkr"].sort_values().tail(10)
        else:
            top_paying = calculate_role_salaries_df(jobs).set_index("title")["avg_salary_pkr"].sort_values().tail(10)

        fig = go.Figure(go.Bar(
            x=top_paying.values, y=top_paying.index, orientation="h",
            marker=dict(color=top_paying.values, colorscale=[[0, T["accent3"]], [1, T["accent"]]]),
        ))
        fig.update_layout(template=T["plot_template"], plot_bgcolor=T["chart_bg"], paper_bgcolor=T["chart_bg"],
                          height=460, margin=dict(l=10, r=10, t=10, b=10),
                          xaxis_title="Avg Salary (PKR/month)", font=dict(color=T["text"]))
        st.plotly_chart(fig, width='stretch')

    st.markdown('<div class="section-title">🌆 Job Distribution by City</div>', unsafe_allow_html=True)
    city_counts = jobs["city"].value_counts()
    fig = px.pie(values=city_counts.values, names=city_counts.index, hole=0.55,
                 color_discrete_sequence=[T["accent"], T["accent2"], T["accent3"], "#F5A623", "#4A90D9", "#9013FE", "#50E3C2"])
    fig.update_layout(template=T["plot_template"], paper_bgcolor=T["chart_bg"],
                      height=380, margin=dict(l=10, r=10, t=10, b=10), font=dict(color=T["text"]))
    st.plotly_chart(fig, width='stretch')

# ================= TAB 2: Trending Skills =================
with tab2:
    st.markdown('<div class="section-title">📈 Fastest Growing Skills</div>', unsafe_allow_html=True)
    st.caption("Comparing recent temporal window vs. prior historical baseline (daily-rate normalized)")

    if trending_precomputed is not None and not trending_precomputed.empty:
        trend_df = trending_precomputed.sort_values("growth_pct").tail(10)
    else:
        trend_df = calculate_trending_skills_df(jobs, skills, recent_window_days=90, min_recent_count=15, top_n=10)
        trend_df = trend_df.sort_values("growth_pct")

    colors = [T["accent3"] if v > 0 else T["accent"] for v in trend_df["growth_pct"]]
    fig = go.Figure(go.Bar(
        x=trend_df["growth_pct"],
        y=trend_df["skill"],
        orientation="h",
        marker=dict(color=colors)
    ))
    fig.update_layout(template=T["plot_template"], plot_bgcolor=T["chart_bg"], paper_bgcolor=T["chart_bg"],
                      height=460, margin=dict(l=10, r=10, t=10, b=10),
                      xaxis_title="Growth % (Recent vs. Historical Baseline)", font=dict(color=T["text"]))
    st.plotly_chart(fig, width='stretch')

    if trend_df.empty:
        st.info("💡 Not enough postings in the recent window to compute a reliable trend on this dataset.")
    else:
        top_grower = trend_df.sort_values("growth_pct", ascending=False).iloc[0]
        st.info(
            f"💡 **Insight:** \"{top_grower['skill']}\" shows the strongest recent growth "
            f"({top_grower['growth_pct']:.0f}%) in this dataset."
        )
        st.caption(
            "⚠️ Note: this dataset's date field is an application deadline, not a posting date, "
            "so trend results should be presented as exploratory, not a confirmed market trend."
        )

# ================= TAB 3: Skill Gap + Salary =================
with tab3:
    st.markdown('<div class="section-title">🧭 Find Out What YOU Should Learn Next</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        target_role = st.selectbox("🎯 Your target job role:", sorted(jobs["title"].unique()))
        target_city = st.selectbox("📍 Target city:", sorted(jobs["city"].unique()))
        target_industry = st.selectbox("🏢 Target industry:", sorted(jobs["industry"].unique()))
        target_exp = st.selectbox("📈 Experience level:", sorted(jobs["experience_level"].unique()))
    with col2:
        all_skills = sorted(skills["skill"].unique())
        current_skills = st.multiselect("✅ Skills you ALREADY have:", all_skills)

    if st.button("🔍 Analyze My Career Path", type="primary"):
        # Centralized skill gap evaluation
        gap_result = analyze_skill_gap(skills, target_role=target_role, current_skills=current_skills, top_n=10)
        match_pct = gap_result["market_match_pct"]
        have = gap_result["skills_you_have"]
        missing = gap_result["skills_to_learn"]

        # Centralized salary prediction
        predicted_salary = predict_salary(
            model=model,
            encoders=encoders,
            features=features,
            title=target_role,
            city=target_city,
            experience=target_exp,
            industry=target_industry,
            skill_count=len(current_skills),
            metadata=metadata
        )

        st.markdown("<br>", unsafe_allow_html=True)
        m1, m2 = st.columns(2)
        with m1: metric_card("Market Match", f"{match_pct:.0f}%", T["accent2"])
        with m2: metric_card("Estimated Salary", f"PKR {predicted_salary:,.0f}", T["accent"])

        st.markdown("<br>", unsafe_allow_html=True)
        have_pills = ''.join(f'<span class="pill pill-have">{html.escape(s)}</span>' for s in have)
        st.markdown(f"""
        <div class="pill-box">
            <b>✅ Skills you already have that match this role:</b><br><br>
            {have_pills if have else '<i>None yet — start building your foundation!</i>'}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        missing_pills = ''.join(f'<span class="pill pill-missing">{html.escape(s)}</span>' for s in missing)
        st.markdown(f"""
        <div class="pill-box">
            <b>📚 Top skills to learn next for {html.escape(target_role)}:</b><br><br>
            {missing_pills if missing else '<i>You already have all top market skills for this role! 🎉</i>'}
        </div>
        """, unsafe_allow_html=True)

st.markdown('<div class="footer-note">Big Data Analytics Course Project · Data processed with PySpark · '
            'Salary model: Random Forest Regressor</div>', unsafe_allow_html=True)