"""
STEP 4: Career Guidance Recommendation Engine
---------------------------------------------
This is the intelligence layer of the tool:

1. SKILL GAP ANALYZER: Compares current candidate competencies with top
   market demand for a target role to surface missing competencies.

2. SALARY PREDICTOR: Estimates monthly compensation in PKR based on
   role, geographical market, experience level, industry, and skill volume.

Run: python 04_recommendation_engine.py
"""

import os
import sys
import pandas as pd

from core.recommender import (
    get_top_skills_for_role,
    analyze_skill_gap,
    train_salary_model,
    predict_salary,
    save_model_bundle,
    load_model_bundle,
)

__all__ = [
    "get_top_skills_for_role",
    "analyze_skill_gap",
    "train_salary_model",
    "predict_salary",
    "save_model_bundle",
    "load_model_bundle",
]


if __name__ == "__main__":
    if not os.path.exists("job_postings.csv") or not os.path.exists("job_skills_exploded.csv"):
        print("Error: Input CSVs not found. Please run Step 1 and Step 3 first.")
        sys.exit(1)

    df_jobs = pd.read_csv("job_postings.csv")
    df_skills = pd.read_csv("job_skills_exploded.csv")

    # Real data mein roles/cities fixed nahi hote, isliye examples data se hi uthao
    example_role = df_jobs["title"].value_counts().index[0]
    example_city = df_jobs["city"].value_counts().index[0]
    example_industry = df_jobs["industry"].value_counts().index[0]
    example_exp = df_jobs["experience_level"].value_counts().index[0]
    role_skills = (
        df_skills[df_skills["title"] == example_role]["skill"].value_counts().index.tolist()
    )
    example_current = role_skills[:2]

    print("=" * 60)
    print("EXAMPLE 1: Skill Gap Analysis")
    print("=" * 60)
    example = analyze_skill_gap(
        df_skills,
        target_role=example_role,
        current_skills=example_current
    )
    print(f"Target Role: {example['target_role']}")
    print(f"Market Match: {example['market_match_pct']}%")
    print(f"Skills you already have: {example['skills_you_have']}")
    print(f"Skills to learn next: {example['skills_to_learn']}")

    print("\n" + "=" * 60)
    print("EXAMPLE 2: Salary Prediction Model Training & Inference")
    print("=" * 60)
    model, encoders, features, metadata = train_salary_model(df_jobs)

    print(f"Salary Model Performance:")
    print(f"  Mean Absolute Error: PKR {metadata['mae']:,.0f}")
    print(f"  R² Score: {metadata['r2']:.3f}")

    # REAL data par R² kam (ya negative) aa sakta hai — synthetic data mein
    # salary ek formula se banai gayi thi, is liye wahan R² 0.98 tha. Yahan
    # sirf 640 postings, 12 roles aur 29 industries hain, is liye chota
    # train/test split noisy hai. Isliye hum crash NAHI karte, sirf batate hain.
    if metadata["r2"] < 0.30:
        print(
            "  [Note] Low/negative R² is expected here: small sample size (640 rows) "
            "split across many role/city/industry categories. Report this honestly as "
            "a limitation, not a bug — don't claim a high R² in your presentation."
        )

    predicted = predict_salary(
        model, encoders, features,
        title=example_role, city=example_city,
        experience=example_exp, industry=example_industry,
        skill_count=6,
        metadata=metadata
    )
    print(f"\nPredicted salary for {example_exp} {example_role} in {example_city} ({example_industry}, 6 skills):")
    print(f"PKR {predicted:,.0f} per month")

    # Save model and encoders for the dashboard
    save_model_bundle(model, encoders, features, metadata, directory=".")
    print("\nSaved: salary_model.pkl, salary_encoders.pkl, salary_features.pkl, salary_metadata.pkl")