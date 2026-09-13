"""
STEP 5: Career Guidance Dashboard (Streamlit)
--------------------------------------------------
This is the final tool students would actually use. It has:
1. Market overview (top skills, salary trends)
2. Trending skills (what's rising in demand)
3. Personal skill-gap tool: pick a target role + your current skills ->
   get a personalized "what to learn next" list
4. Salary estimator

Run with:  streamlit run 05_dashboard_app.py
"""

import streamlit as st
import pandas as pd
import joblib
import matplotlib.pyplot as plt

st.set_page_config(page_title="Career Guidance Tool", layout="wide")

@st.cache_data
def load_data():
    jobs = pd.read_csv("job_postings.csv")
    skills = pd.read_csv("job_skills_exploded.csv")
    return jobs, skills

@st.cache_resource
def load_model():
    model = joblib.load("salary_model.pkl")
    encoders = joblib.load("salary_encoders.pkl")
    features = joblib.load("salary_features.pkl")
    return model, encoders, features

jobs, skills = load_data()
model, encoders, features = load_model()

st.title("🎯 Career Guidance Tool")
st.markdown("**Big Data Analytics Project** — Data-driven answer to: *'What skills should I actually learn?'*")

tab1, tab2, tab3 = st.tabs(["📊 Market Overview", "🚀 Trending Skills", "🧭 My Skill Gap & Salary"])

# ================= TAB 1: Market Overview =================
with tab1:
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Job Postings Analyzed", f"{len(jobs):,}")
    col2.metric("Unique Skills Tracked", f"{skills['skill'].nunique()}")
    col3.metric("Job Roles Covered", f"{jobs['title'].nunique()}")

    st.divider()
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Top 15 Most In-Demand Skills")
        top_skills = skills["skill"].value_counts().head(15)
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.barh(top_skills.index[::-1], top_skills.values[::-1], color="teal")
        ax.set_xlabel("Number of Job Postings Requiring This Skill")
        st.pyplot(fig)

    with c2:
        st.subheader("Average Salary by Role (PKR/month)")
        avg_sal = jobs.copy()
        avg_sal["avg_salary"] = (avg_sal["salary_min_pkr"] + avg_sal["salary_max_pkr"]) / 2
        top_paying = avg_sal.groupby("title")["avg_salary"].mean().sort_values(ascending=False).head(10)
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.barh(top_paying.index[::-1], top_paying.values[::-1], color="darkorange")
        ax.set_xlabel("Average Salary (PKR)")
        st.pyplot(fig)

# ================= TAB 2: Trending Skills =================
with tab2:
    st.subheader("📈 Skills Growing Fastest in Demand")
    st.caption("Comparing last 90 days of postings vs. the rest of the year (normalized by daily rate)")

    skills["date_posted"] = pd.to_datetime(jobs.set_index("job_id").loc[skills["job_id"]]["date_posted"].values)
    max_date = skills["date_posted"].max()
    cutoff = max_date - pd.Timedelta(days=90)

    recent = skills[skills["date_posted"] >= cutoff]["skill"].value_counts() / 90
    older = skills[skills["date_posted"] < cutoff]["skill"].value_counts() / (skills["date_posted"].nunique() - 90 if skills["date_posted"].nunique() > 90 else 275)

    trend_df = pd.DataFrame({"recent_rate": recent, "older_rate": older}).fillna(0)
    trend_df = trend_df[trend_df["recent_rate"] * 90 > 15]
    trend_df["growth_pct"] = ((trend_df["recent_rate"] - trend_df["older_rate"]) / trend_df["older_rate"].replace(0, 0.001)) * 100
    trend_df = trend_df.sort_values("growth_pct", ascending=False).head(10)

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["crimson" if v > 0 else "steelblue" for v in trend_df["growth_pct"]]
    ax.barh(trend_df.index[::-1], trend_df["growth_pct"][::-1], color=colors)
    ax.set_xlabel("Growth % (recent vs. earlier in the year)")
    ax.set_title("Fastest Growing Skills")
    st.pyplot(fig)

    st.info("💡 **Insight:** AI-related skills (ChatGPT/LLM Tools, Prompt Engineering, Generative AI) "
            "and Cloud Computing show the sharpest growth — these are worth prioritizing.")

# ================= TAB 3: Skill Gap + Salary =================
with tab3:
    st.subheader("Find Out What YOU Should Learn Next")

    col1, col2 = st.columns(2)
    with col1:
        target_role = st.selectbox("🎯 Your target job role:", sorted(jobs["title"].unique()))
        target_city = st.selectbox("📍 Target city:", sorted(jobs["city"].unique()))
        target_industry = st.selectbox("🏢 Target industry:", sorted(jobs["industry"].unique()))
        target_exp = st.selectbox("📈 Experience level:", sorted(jobs["experience_level"].unique()))

    with col2:
        all_skills = sorted(skills["skill"].unique())
        current_skills = st.multiselect("✅ Skills you ALREADY have:", all_skills)

    if st.button("Analyze My Career Path", type="primary"):
        # Skill gap analysis
        role_skills = skills[skills["title"] == target_role]["skill"].value_counts().head(10)
        current_set = set(s.lower() for s in current_skills)

        have = [s for s in role_skills.index if s.lower() in current_set]
        missing = [s for s in role_skills.index if s.lower() not in current_set]
        match_pct = len(have) / len(role_skills) * 100 if len(role_skills) > 0 else 0

        st.divider()
        m1, m2 = st.columns(2)
        m1.metric("Market Match", f"{match_pct:.0f}%")

        # Salary prediction
        try:
            row = pd.DataFrame([{
                "title_enc": encoders["title"].transform([target_role])[0],
                "city_enc": encoders["city"].transform([target_city])[0],
                "exp_enc": encoders["experience"].transform([target_exp])[0],
                "industry_enc": encoders["industry"].transform([target_industry])[0],
                "skill_count": max(len(current_skills), 1),
            }])[features]
            predicted_salary = model.predict(row)[0]
            m2.metric("Estimated Salary", f"PKR {predicted_salary:,.0f}/month")
        except Exception:
            m2.metric("Estimated Salary", "N/A")

        st.success(f"✅ Skills you already have that match this role: {', '.join(have) if have else 'None yet'}")
        st.warning(f"📚 Top skills to learn next for **{target_role}**: {', '.join(missing) if missing else 'You have them all!'}")

st.divider()
st.caption("Big Data Analytics Course Project | Data processed with PySpark | Salary model: Random Forest Regressor")
