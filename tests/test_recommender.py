"""
Unit tests for recommender logic: skill gap analysis and salary estimation.
"""

import pytest
import pandas as pd
from core.recommender import (
    analyze_skill_gap,
    get_top_skills_for_role,
    train_salary_model,
    predict_salary,
)


@pytest.fixture
def sample_skills_df():
    data = []
    # 20 Data Analyst rows with Python, SQL, Tableau
    for _ in range(20):
        data.append({"title": "Data Analyst", "skill": "SQL"})
        data.append({"title": "Data Analyst", "skill": "Python"})
        data.append({"title": "Data Analyst", "skill": "Tableau"})
    return pd.DataFrame(data)


@pytest.fixture
def sample_jobs_df():
    roles = ["Data Analyst", "Software Engineer"] * 50
    cities = ["Lahore", "Karachi"] * 50
    exps = ["Entry Level (0-1 yrs)", "Mid Level (2-4 yrs)"] * 50
    industries = ["IT/Software", "Banking/Finance"] * 50

    rows = []
    for i in range(100):
        rows.append({
            "job_id": f"J{i}",
            "title": roles[i],
            "city": cities[i],
            "experience_level": exps[i],
            "industry": industries[i],
            "skills": "Python, SQL, Tableau",
            "salary_min_pkr": 60000 + i * 200,
            "salary_max_pkr": 90000 + i * 300,
            "date_posted": "2025-01-01"
        })
    return pd.DataFrame(rows)


def test_get_top_skills_for_role(sample_skills_df):
    top = get_top_skills_for_role(sample_skills_df, "Data Analyst", top_n=2)
    assert len(top) == 2
    assert "SQL" in top.index


def test_analyze_skill_gap_full_match(sample_skills_df):
    result = analyze_skill_gap(
        sample_skills_df,
        target_role="Data Analyst",
        current_skills=["sql", "python", "tableau"]
    )
    assert result["market_match_pct"] == 100.0
    assert len(result["skills_to_learn"]) == 0
    assert len(result["skills_you_have"]) == 3


def test_analyze_skill_gap_zero_match(sample_skills_df):
    result = analyze_skill_gap(
        sample_skills_df,
        target_role="Data Analyst",
        current_skills=["Rust", "Go"]
    )
    assert result["market_match_pct"] == 0.0
    assert len(result["skills_to_learn"]) == 3
    assert len(result["skills_you_have"]) == 0


def test_analyze_skill_gap_case_insensitive(sample_skills_df):
    result = analyze_skill_gap(
        sample_skills_df,
        target_role="Data Analyst",
        current_skills=["SqL", "pYtHoN"]
    )
    assert "SQL" in result["skills_you_have"]
    assert "Python" in result["skills_you_have"]
    assert "Tableau" in result["skills_to_learn"]


def test_train_and_predict_salary(sample_jobs_df):
    model, encoders, features, metadata = train_salary_model(sample_jobs_df)
    assert metadata["r2"] is not None

    # Normal known prediction
    pred = predict_salary(
        model, encoders, features,
        title="Data Analyst", city="Lahore",
        experience="Entry Level (0-1 yrs)", industry="IT/Software",
        skill_count=3,
        metadata=metadata
    )
    assert pred > 50000

    # Unseen category prediction (should fallback gracefully without throwing exception)
    pred_unseen = predict_salary(
        model, encoders, features,
        title="Nonexistent Role", city="Atlantis",
        experience="Senior Level (5+ yrs)", industry="Unknown Industry",
        skill_count=5,
        metadata=metadata
    )
    assert pred_unseen > 0
