"""
Analytics Module: Computes dynamic time-window normalized trends,
skill frequencies, and salary benchmarks.
"""

from typing import Tuple, Dict, Any
import pandas as pd
import numpy as np


def calculate_dynamic_window(
    min_date: pd.Timestamp,
    max_date: pd.Timestamp,
    recent_window_days: int = 90
) -> Tuple[int, int]:
    """
    Computes dynamic window sizes for recent vs older historical periods.
    Eliminates hardcoded date divisors (e.g. 275.0) and adapts to any dataset duration.
    """
    total_days = max(1, (pd.to_datetime(max_date) - pd.to_datetime(min_date)).days)
    recent_days = min(recent_window_days, total_days)
    older_days = max(1, total_days - recent_days)
    return recent_days, older_days


def calculate_trending_skills_df(
    df_jobs: pd.DataFrame,
    df_skills: pd.DataFrame,
    recent_window_days: int = 90,
    min_recent_count: int = 15,
    top_n: int = 10
) -> pd.DataFrame:
    """
    Vectorized computation of trending skills by comparing daily occurrence
    rates between the recent window and the older historical baseline.
    """
    if df_skills.empty or df_jobs.empty:
        return pd.DataFrame(columns=["skill", "recent_rate", "older_rate", "recent_count", "older_count", "growth_pct"])

    # Ensure date_posted is attached
    if "date_posted" not in df_skills.columns:
        date_lookup = df_jobs.set_index("job_id")["date_posted"]
        df_skills = df_skills.copy()
        df_skills["date_posted"] = df_skills["job_id"].map(date_lookup)

    df_skills = df_skills.dropna(subset=["date_posted", "skill"])
    df_skills["date_posted"] = pd.to_datetime(df_skills["date_posted"])

    max_date = df_skills["date_posted"].max()
    min_date = df_skills["date_posted"].min()

    recent_days, older_days = calculate_dynamic_window(min_date, max_date, recent_window_days)
    cutoff = max_date - pd.Timedelta(days=recent_days)

    recent_mask = df_skills["date_posted"] >= cutoff
    recent_series = df_skills[recent_mask]["skill"].value_counts()
    older_series = df_skills[~recent_mask]["skill"].value_counts()

    # Align on skills
    all_skills = sorted(set(recent_series.index).union(set(older_series.index)))
    trend_df = pd.DataFrame(index=all_skills)
    trend_df["recent_count"] = trend_df.index.map(recent_series).fillna(0).astype(int)
    trend_df["older_count"] = trend_df.index.map(older_series).fillna(0).astype(int)

    trend_df["recent_rate"] = trend_df["recent_count"] / float(recent_days)
    trend_df["older_rate"] = trend_df["older_count"] / float(older_days)

    # Filter by minimum threshold in recent window
    trend_df = trend_df[trend_df["recent_count"] >= min_recent_count].copy()
    if trend_df.empty:
        return pd.DataFrame(columns=["skill", "recent_rate", "older_rate", "recent_count", "older_count", "growth_pct"])

    # Calculate growth percentage: ((recent_rate - older_rate) / older_rate) * 100
    # Avoid zero-division by using a small floor for older rate
    rate_floor = 1.0 / (older_days * 2.0)
    effective_older_rate = np.where(trend_df["older_rate"] > 0, trend_df["older_rate"], rate_floor)

    trend_df["growth_pct"] = np.round(
        ((trend_df["recent_rate"] - trend_df["older_rate"]) / effective_older_rate) * 100.0,
        1
    )
    trend_df["skill"] = trend_df.index
    trend_df = trend_df.sort_values(by="growth_pct", ascending=False).head(top_n)
    return trend_df.reset_index(drop=True)


def calculate_role_salaries_df(df_jobs: pd.DataFrame) -> pd.DataFrame:
    """
    Computes average monthly salary and posting volume by job title.
    """
    if df_jobs.empty:
        return pd.DataFrame(columns=["title", "avg_salary_pkr", "num_postings"])

    df = df_jobs.copy()
    df["avg_salary"] = (df["salary_min_pkr"] + df["salary_max_pkr"]) / 2.0
    summary = df.groupby("title").agg(
        avg_salary_pkr=("avg_salary", lambda s: int(round(s.mean()))),
        num_postings=("job_id", "count")
    ).reset_index()

    return summary.sort_values(by="avg_salary_pkr", ascending=False)
