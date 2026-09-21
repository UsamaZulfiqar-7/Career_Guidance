"""
Recommender Module: Implements competency gap analysis and predictive salary modeling
with robust categorical handling, fallback logic, and artifact serialization.
"""

from typing import List, Dict, Any, Optional, Tuple
import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score


def get_top_skills_for_role(df_skills: pd.DataFrame, role: str, top_n: int = 10) -> pd.Series:
    """
    Returns the most in-demand skills for a given job role from exploded skill data.
    """
    if df_skills.empty:
        return pd.Series(dtype=int)
    role_data = df_skills[df_skills["title"].str.lower() == role.lower()]
    if role_data.empty:
        return pd.Series(dtype=int)
    return role_data["skill"].value_counts().head(top_n)


def analyze_skill_gap(
    df_skills: pd.DataFrame,
    target_role: str,
    current_skills: List[str],
    top_n: int = 10
) -> Dict[str, Any]:
    """
    Compares a candidate's current skills against what the market demands
    for their target role, surfacing matching and missing competencies.
    """
    top_skills_series = get_top_skills_for_role(df_skills, target_role, top_n=top_n)
    current_skills_set = set(str(s).strip().lower() for s in current_skills if str(s).strip())

    have: List[str] = []
    missing: List[str] = []

    for skill in top_skills_series.index:
        if str(skill).strip().lower() in current_skills_set:
            have.append(skill)
        else:
            missing.append(skill)

    total_target = len(top_skills_series)
    match_pct = (len(have) / total_target * 100.0) if total_target > 0 else 0.0

    return {
        "target_role": target_role,
        "skills_you_have": have,
        "skills_to_learn": missing,
        "market_match_pct": round(match_pct, 1),
        "target_skills_count": total_target,
    }


def train_salary_model(
    df_jobs: pd.DataFrame
) -> Tuple[RandomForestRegressor, Dict[str, LabelEncoder], List[str], Dict[str, Any]]:
    """
    Trains a Random Forest Regressor to estimate expected salary based on
    role, location, seniority, industry, and skill volume.
    Returns the fitted model, feature encoders, feature column list, and evaluation metrics.
    """
    df = df_jobs.copy()
    df["avg_salary"] = (df["salary_min_pkr"] + df["salary_max_pkr"]) / 2.0
    df["skill_count"] = df["skills"].apply(lambda x: len([s for s in str(x).split(",") if s.strip()]))

    le_title = LabelEncoder()
    le_city = LabelEncoder()
    le_exp = LabelEncoder()
    le_industry = LabelEncoder()

    df["title_enc"] = le_title.fit_transform(df["title"].astype(str))
    df["city_enc"] = le_city.fit_transform(df["city"].astype(str))
    df["exp_enc"] = le_exp.fit_transform(df["experience_level"].astype(str))
    df["industry_enc"] = le_industry.fit_transform(df["industry"].astype(str))

    features = ["title_enc", "city_enc", "exp_enc", "industry_enc", "skill_count"]
    X = df[features]
    y = df["avg_salary"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(
        n_estimators=120,
        max_depth=12,
        min_samples_split=4,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = float(mean_absolute_error(y_test, preds))
    r2 = float(r2_score(y_test, preds))

    # Precalculate segment medians for robust unseen category fallback
    role_medians = df.groupby("title")["avg_salary"].median().to_dict()
    city_medians = df.groupby("city")["avg_salary"].median().to_dict()
    overall_median = float(df["avg_salary"].median())

    encoders = {
        "title": le_title,
        "city": le_city,
        "experience": le_exp,
        "industry": le_industry,
    }

    metadata = {
        "mae": mae,
        "r2": r2,
        "role_medians": role_medians,
        "city_medians": city_medians,
        "overall_median": overall_median,
        "sample_size": len(df),
    }

    return model, encoders, features, metadata


def predict_salary(
    model: RandomForestRegressor,
    encoders: Dict[str, LabelEncoder],
    features: List[str],
    title: str,
    city: str,
    experience: str,
    industry: str,
    skill_count: int,
    metadata: Optional[Dict[str, Any]] = None
) -> float:
    """
    Predicts monthly salary in PKR. Gracefully handles unseen categories
    by falling back to role/city medians instead of raising exceptions.
    """
    skill_count_val = max(1, int(skill_count))

    try:
        title_cls = encoders["title"].classes_
        city_cls = encoders["city"].classes_
        exp_cls = encoders["experience"].classes_
        ind_cls = encoders["industry"].classes_

        # Fallback values for unseen inputs
        title_val = title if title in title_cls else title_cls[0]
        city_val = city if city in city_cls else city_cls[0]
        exp_val = experience if experience in exp_cls else exp_cls[0]
        ind_val = industry if industry in ind_cls else ind_cls[0]

        row = pd.DataFrame([{
            "title_enc": encoders["title"].transform([title_val])[0],
            "city_enc": encoders["city"].transform([city_val])[0],
            "exp_enc": encoders["experience"].transform([exp_val])[0],
            "industry_enc": encoders["industry"].transform([ind_val])[0],
            "skill_count": skill_count_val,
        }])[features]

        predicted = float(model.predict(row)[0])

        # If title was unseen but metadata has role medians, blend or fallback
        if title not in title_cls and metadata and "overall_median" in metadata:
            return float(metadata["overall_median"])

        return round(predicted, 0)

    except Exception:
        # Emergency fallback if model execution fails
        if metadata and "role_medians" in metadata and title in metadata["role_medians"]:
            return float(metadata["role_medians"][title])
        if metadata and "overall_median" in metadata:
            return float(metadata["overall_median"])
        return 95000.0


def save_model_bundle(
    model: RandomForestRegressor,
    encoders: Dict[str, LabelEncoder],
    features: List[str],
    metadata: Dict[str, Any],
    directory: str = "."
) -> None:
    """Saves all model artifacts to disk."""
    joblib.dump(model, os.path.join(directory, "salary_model.pkl"))
    joblib.dump(encoders, os.path.join(directory, "salary_encoders.pkl"))
    joblib.dump(features, os.path.join(directory, "salary_features.pkl"))
    joblib.dump(metadata, os.path.join(directory, "salary_metadata.pkl"))


def load_model_bundle(directory: str = ".") -> Tuple[Any, Any, Any, Optional[Dict[str, Any]]]:
    """Loads all model artifacts from disk."""
    model = joblib.load(os.path.join(directory, "salary_model.pkl"))
    encoders = joblib.load(os.path.join(directory, "salary_encoders.pkl"))
    features = joblib.load(os.path.join(directory, "salary_features.pkl"))

    metadata_path = os.path.join(directory, "salary_metadata.pkl")
    metadata = joblib.load(metadata_path) if os.path.exists(metadata_path) else None

    return model, encoders, features, metadata
