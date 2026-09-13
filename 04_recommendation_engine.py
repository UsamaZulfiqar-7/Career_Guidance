"""
STEP 4: Career Guidance Recommendation Engine
--------------------------------------------------
This is the "intelligence" layer of the tool. Two things:

1. SKILL GAP ANALYZER: Given a student's current skills + target job role,
   tell them exactly which top skills they're MISSING for that role.

2. SALARY PREDICTOR: Given a role, city, experience level, and skill count,
   predict the expected salary range using a trained regression model.

Run: python3 04_recommendation_engine.py
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

# ==========================================================
# PART A: Skill Gap Analyzer (rule-based, uses Spark output)
# ==========================================================

def get_top_skills_for_role(df_skills, role, top_n=8):
    """Returns the most in-demand skills for a given job role."""
    role_data = df_skills[df_skills["title"] == role]
    top_skills = role_data["skill"].value_counts().head(top_n)
    return top_skills

def analyze_skill_gap(df_skills, target_role, current_skills):
    """
    Compares a student's current skills against what the market demands
    for their target role, and returns what they're missing.
    """
    top_skills = get_top_skills_for_role(df_skills, target_role, top_n=10)
    current_skills_set = set(s.strip().lower() for s in current_skills)

    have, missing = [], []
    for skill, count in top_skills.items():
        if skill.lower() in current_skills_set:
            have.append(skill)
        else:
            missing.append(skill)

    match_pct = len(have) / len(top_skills) * 100 if len(top_skills) > 0 else 0
    return {
        "target_role": target_role,
        "skills_you_have": have,
        "skills_to_learn": missing,
        "market_match_pct": round(match_pct, 1),
    }


# ==========================================================
# PART B: Salary Prediction Model
# ==========================================================

def train_salary_model(df_jobs):
    df = df_jobs.copy()
    df["avg_salary"] = (df["salary_min_pkr"] + df["salary_max_pkr"]) / 2
    df["skill_count"] = df["skills"].apply(lambda x: len(str(x).split(",")))

    # Encode categorical features
    le_title = LabelEncoder()
    le_city = LabelEncoder()
    le_exp = LabelEncoder()
    le_industry = LabelEncoder()

    df["title_enc"] = le_title.fit_transform(df["title"])
    df["city_enc"] = le_city.fit_transform(df["city"])
    df["exp_enc"] = le_exp.fit_transform(df["experience_level"])
    df["industry_enc"] = le_industry.fit_transform(df["industry"])

    features = ["title_enc", "city_enc", "exp_enc", "industry_enc", "skill_count"]
    X = df[features]
    y = df["avg_salary"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=150, max_depth=12, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    print(f"Salary Model Performance:")
    print(f"  Mean Absolute Error: PKR {mae:,.0f}")
    print(f"  R² Score: {r2:.3f}")

    encoders = {"title": le_title, "city": le_city, "experience": le_exp, "industry": le_industry}
    return model, encoders, features


def predict_salary(model, encoders, features, title, city, experience, industry, skill_count):
    try:
        row = pd.DataFrame([{
            "title_enc": encoders["title"].transform([title])[0],
            "city_enc": encoders["city"].transform([city])[0],
            "exp_enc": encoders["experience"].transform([experience])[0],
            "industry_enc": encoders["industry"].transform([industry])[0],
            "skill_count": skill_count,
        }])[features]
        return model.predict(row)[0]
    except ValueError as e:
        return None  # unseen category


# ==========================================================
# MAIN: Run and save everything
# ==========================================================
if __name__ == "__main__":
    df_jobs = pd.read_csv("job_postings.csv")
    df_skills = pd.read_csv("job_skills_exploded.csv")

    print("=" * 60)
    print("EXAMPLE 1: Skill Gap Analysis")
    print("=" * 60)
    example = analyze_skill_gap(
        df_skills,
        target_role="Data Analyst",
        current_skills=["Excel", "SQL", "Communication"]
    )
    print(f"Target Role: {example['target_role']}")
    print(f"Market Match: {example['market_match_pct']}%")
    print(f"Skills you already have: {example['skills_you_have']}")
    print(f"Skills to learn next: {example['skills_to_learn']}")

    print("\n" + "=" * 60)
    print("EXAMPLE 2: Salary Prediction Model")
    print("=" * 60)
    model, encoders, features = train_salary_model(df_jobs)

    predicted = predict_salary(
        model, encoders, features,
        title="Data Analyst", city="Lahore",
        experience="Mid Level (2-4 yrs)", industry="IT/Software",
        skill_count=6
    )
    print(f"\nPredicted salary for a Mid-Level Data Analyst in Lahore (IT/Software, 6 skills):")
    print(f"PKR {predicted:,.0f} per month")

    # Save model and encoders for the dashboard
    joblib.dump(model, "salary_model.pkl")
    joblib.dump(encoders, "salary_encoders.pkl")
    joblib.dump(features, "salary_features.pkl")
    print("\nSaved: salary_model.pkl, salary_encoders.pkl, salary_features.pkl")
