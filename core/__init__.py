"""
Core Career Guidance package.
Provides modular business logic for analytics, skill gap analysis, and salary estimation.
"""

from .recommender import (
    get_top_skills_for_role,
    analyze_skill_gap,
    train_salary_model,
    predict_salary,
)
from .analytics import (
    calculate_dynamic_window,
    calculate_trending_skills_df,
    calculate_role_salaries_df,
)

__all__ = [
    "get_top_skills_for_role",
    "analyze_skill_gap",
    "train_salary_model",
    "predict_salary",
    "calculate_dynamic_window",
    "calculate_trending_skills_df",
    "calculate_role_salaries_df",
]
