"""
Unit tests for analytics and dynamic windowing functions.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from core.analytics import (
    calculate_dynamic_window,
    calculate_trending_skills_df,
    calculate_role_salaries_df,
)


def test_calculate_dynamic_window_standard():
    min_d = pd.Timestamp("2024-01-01")
    max_d = pd.Timestamp("2025-01-01")  # 366 days
    recent, older = calculate_dynamic_window(min_d, max_d, recent_window_days=90)
    assert recent == 90
    assert older == 366 - 90


def test_calculate_dynamic_window_short_dataset():
    min_d = pd.Timestamp("2025-01-01")
    max_d = pd.Timestamp("2025-02-01")  # 31 days
    recent, older = calculate_dynamic_window(min_d, max_d, recent_window_days=90)
    assert recent == 31
    assert older >= 1


def test_calculate_role_salaries_df():
    sample_jobs = pd.DataFrame([
        {"job_id": "J1", "title": "Data Analyst", "salary_min_pkr": 80000, "salary_max_pkr": 120000},
        {"job_id": "J2", "title": "Data Analyst", "salary_min_pkr": 100000, "salary_max_pkr": 140000},
        {"job_id": "J3", "title": "DevOps", "salary_min_pkr": 150000, "salary_max_pkr": 200000},
    ])
    res = calculate_role_salaries_df(sample_jobs)
    assert len(res) == 2
    da_row = res[res["title"] == "Data Analyst"].iloc[0]
    assert da_row["num_postings"] == 2
    assert da_row["avg_salary_pkr"] == 110000  # (100k + 120k) / 2


def test_calculate_trending_skills_df():
    base_date = datetime(2025, 1, 1)
    jobs_rows = []
    skills_rows = []

    for i in range(100):
        jid = f"J{i}"
        # 30 postings in last 30 days (recent), 70 in earlier period
        is_recent = i < 30
        date = base_date + timedelta(days=320 if is_recent else 50)
        jobs_rows.append({"job_id": jid, "date_posted": date.strftime("%Y-%m-%d")})

        # LLM skill appears primarily in recent postings
        if is_recent:
            skills_rows.append({"job_id": jid, "skill": "LLM Tools"})
        else:
            skills_rows.append({"job_id": jid, "skill": "Legacy Tool"})

    df_jobs = pd.DataFrame(jobs_rows)
    df_skills = pd.DataFrame(skills_rows)

    trend = calculate_trending_skills_df(df_jobs, df_skills, recent_window_days=90, min_recent_count=5)
    assert not trend.empty
    assert "LLM Tools" in trend["skill"].values
    llm_row = trend[trend["skill"] == "LLM Tools"].iloc[0]
    assert llm_row["growth_pct"] > 0
