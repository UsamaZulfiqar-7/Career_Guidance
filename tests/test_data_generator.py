"""
Unit tests for Step 1 data generation logic.
"""

import pytest
import pandas as pd
from importlib import import_module

data_gen_module = import_module("01_generate_sample_data")
generate_postings = data_gen_module.generate_postings


def test_generate_postings_schema():
    df = generate_postings(50)
    expected_cols = [
        "job_id", "title", "company", "city", "industry",
        "experience_level", "skills", "salary_min_pkr",
        "salary_max_pkr", "date_posted"
    ]
    assert list(df.columns) == expected_cols
    assert len(df) == 50


def test_generate_postings_salaries_valid():
    df = generate_postings(50)
    assert (df["salary_min_pkr"] > 0).all()
    assert (df["salary_max_pkr"] >= df["salary_min_pkr"]).all()


def test_generate_postings_dates_valid():
    df = generate_postings(50)
    dates = pd.to_datetime(df["date_posted"], errors="coerce")
    assert dates.notna().all()


def test_generate_postings_skills_non_empty():
    df = generate_postings(50)
    for skills_str in df["skills"]:
        skills_list = [s.strip() for s in skills_str.split(",") if s.strip()]
        assert len(skills_list) >= 3
