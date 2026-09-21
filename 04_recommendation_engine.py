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
    print("EXAMPLE 2: Salary Prediction Model Training & Inference")
    print("=" * 60)
    model, encoders, features, metadata = train_salary_model(df_jobs)

    print(f"Salary Model Performance:")
    print(f"  Mean Absolute Error: PKR {metadata['mae']:,.0f}")
    print(f"  R² Score: {metadata['r2']:.3f}")

    assert metadata["r2"] > 0.70, f"Model quality below threshold! R2: {metadata['r2']}"

    predicted = predict_salary(
        model, encoders, features,
        title="Data Analyst", city="Lahore",
        experience="Mid Level (2-4 yrs)", industry="IT/Software",
        skill_count=6,
        metadata=metadata
    )
    print(f"\nPredicted salary for a Mid-Level Data Analyst in Lahore (IT/Software, 6 skills):")
    print(f"PKR {predicted:,.0f} per month")

    # Save model and encoders for the dashboard
    save_model_bundle(model, encoders, features, metadata, directory=".")
    print("\nSaved: salary_model.pkl, salary_encoders.pkl, salary_features.pkl, salary_metadata.pkl")
