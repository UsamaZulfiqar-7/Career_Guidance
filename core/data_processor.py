"""
Data Processing, De-duplication & Normalization Module
------------------------------------------------------
Implements comprehensive ETL data engineering logic:
1. De-duplication (Exact record, semantic composite key, in-record skills)
2. Normalization (Text, Regex Role mapping, City extraction, Salary parsing,
   Experience bucketing, Skill canonicalization, ISO Date conversion)
3. Dimensional Schema Transformation (Relational 3NF & Document NoSQL)
"""

import re
import io
from collections import Counter
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np


KNOWN_CITIES = [
    "Lahore", "Karachi", "Islamabad", "Rawalpindi", "Faisalabad", "Multan",
    "Peshawar", "Quetta", "Sialkot", "Gujranwala", "Hyderabad", "Bahawalpur",
    "Sargodha", "Jhelum", "Gujrat", "Sahiwal", "Abbottabad", "Sukkur",
]

ROLE_RULES = [
    ("Operations & Logistics", r"procurement|purchas"),
    ("Admin & Office Support", r"data entry|receptionist|office assistant|office boy|secretary|clerk|front desk|admin"),
    ("Data & Analytics", r"data analy|data scien|business intelligence|\bbi\b|machine learning|\bai\b|\bml\b|analytics"),
    ("Software / Web Developer", r"developer|software|programmer|full ?stack|front ?end|back ?end|\bweb\b|react|php|laravel|wordpress|flutter|android|\bios\b|mern|python|\.net|java\b"),
    ("IT & Networking", r"\bit\b|network|system admin|devops|helpdesk it|technical support|\bqa\b|tester"),
    ("Design & Creative", r"graphic|designer|video|animator|animation|photograph|illustrat|ui/?ux|creative|editor"),
    ("Customer Support", r"telemarket|call cent|customer (service|support|care|relation)|\bcsr\b|help ?desk|customer experience"),
    ("Sales & Business Development", r"sales|business development|\bbde\b|account manager|relationship manager"),
    ("Marketing", r"\bseo\b|social media|digital market|marketing|brand|content market"),
    ("Accounts & Finance", r"account|finance|financial|audit|tax|bookkeep|cashier|payroll"),
    ("Human Resources", r"\bhr\b|human resource|recruit|talent"),
    ("Teaching & Training", r"teacher|tutor|instructor|lecturer|trainer|faculty|academic"),
    ("Management (Project/Product)", r"project manager|product manager|product owner|scrum|program manager"),
    ("Writing & Content", r"writer|content|copywrit|journalist|translator"),
    ("Healthcare", r"doctor|nurse|pharmac|medical|clinic|dentist|physician|paramedic|lab tech"),
    ("Engineering (Non-IT)", r"civil|mechanical|electrical|engineer|architect|surveyor|site supervisor"),
    ("Operations & Logistics", r"warehouse|logistic|supply chain|operations|store keeper|driver|dispatch|procurement"),
]

FUNCTIONAL_AREA_TO_ROLE = {
    "Sales & Business Development": "Sales & Business Development",
    "Accounts, Finance & Financial Services": "Accounts & Finance",
    "Client Services & Customer Support": "Customer Support",
    "Marketing": "Marketing",
    "Telemarketing": "Customer Support",
    "Software & Web Development": "Software / Web Developer",
    "Creative Design": "Design & Creative",
    "Human Resources": "Human Resources",
    "Secretarial, Clerical & Front Office": "Admin & Office Support",
    "Operations": "Operations & Logistics",
    "Teachers/Education, Training & Development": "Teaching & Training",
    "Health & Medicine": "Healthcare",
    "Engineering": "Engineering (Non-IT)",
    "Administration": "Admin & Office Support",
    "Computer Networking": "IT & Networking",
    "Warehousing": "Operations & Logistics",
    "Data Entry": "Admin & Office Support",
    "Architects & Construction": "Engineering (Non-IT)",
    "Writer": "Writing & Content",
}

SKILL_SYNONYMS = {
    "communication skills": "Communication",
    "communication": "Communication",
    "excel": "MS Excel",
    "microsoft excel": "MS Excel",
    "ms excel": "MS Excel",
    "fluent in english": "English Fluency",
    "english communication": "English Fluency",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "reactjs": "React",
    "react.js": "React",
    "react": "React",
    "python programming": "Python",
    "py": "Python",
    "sql server": "SQL Server",
    "ms sql": "SQL Server",
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "customer service": "Customer Support",
    "customer care": "Customer Support",
    "problem solving": "Problem Solving",
    "analytical skills": "Analytical Skills",
    "time management": "Time Management",
    "team player": "Teamwork",
    "team building": "Teamwork",
    "negotiation skills": "Negotiation",
}

SALARY_PATTERN = re.compile(r"PKR\.?\s*([\d,]+)\s*-\s*([\d,]+)", re.IGNORECASE)


class DataProcessor:
    """
    Production-grade ETL processor providing:
    - Multi-stage de-duplication
    - Field-level & domain normalizations
    - Dimensional relational modeling (3NF)
    - Document-oriented NoSQL structuring
    """

    def __init__(
        self,
        min_salary: int = 10_000,
        max_salary: int = 1_000_000,
        require_salary: bool = True,
        min_postings_per_role: int = 15,
        min_postings_per_city: int = 10
    ):
        self.min_salary = min_salary
        self.max_salary = max_salary
        self.require_salary = require_salary
        self.min_postings_per_role = min_postings_per_role
        self.min_postings_per_city = min_postings_per_city
        self.metrics: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # NORMALIZATION HELPERS
    # ------------------------------------------------------------------
    @staticmethod
    def normalize_text(text: Any) -> str:
        if pd.isna(text) or text is None:
            return ""
        s = str(text)
        s = re.sub(r"[\r\n\t]+", " ", s)
        s = re.sub(r"\s+", " ", s)
        return s.strip()

    @staticmethod
    def extract_city(loc: Any) -> str:
        cleaned = DataProcessor.normalize_text(loc)
        parts = [p.strip() for p in cleaned.split(",") if p.strip()]
        parts = [p for p in parts if p.lower() != "pakistan"]
        for p in parts:
            for city in KNOWN_CITIES:
                if city.lower() == p.lower():
                    return city
        return parts[0] if parts else "Other"

    @staticmethod
    def map_role(title: str, functional_area: Any) -> str:
        t = str(title).lower()
        for role, pattern in ROLE_RULES:
            if re.search(pattern, t):
                return role
        return FUNCTIONAL_AREA_TO_ROLE.get(str(functional_area).strip(), "Other")

    @staticmethod
    def parse_salary(salary_raw: Any) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        if pd.isna(salary_raw) or not salary_raw:
            return None, None, None
        m = SALARY_PATTERN.search(str(salary_raw))
        if not m:
            return None, None, None
        try:
            lo = int(m.group(1).replace(",", ""))
            hi = int(m.group(2).replace(",", ""))
            if hi < lo:
                lo, hi = hi, lo
            avg = (lo + hi) // 2
            return lo, hi, avg
        except (ValueError, TypeError):
            return None, None, None

    @staticmethod
    def parse_experience(min_exp: Any, career_level: Any) -> Optional[str]:
        s = str(min_exp).lower().strip()
        years = None
        if s not in ("nan", "none", "", "na"):
            if "fresh" in s or "less than" in s:
                years = 0
            else:
                m = re.search(r"\d+", s)
                years = int(m.group()) if m else None

        if years is None:
            c = str(career_level).lower()
            if any(k in c for k in ("entry", "intern", "student", "fresh")):
                years = 0
            elif "experienced" in c:
                years = 3
            elif any(k in c for k in ("head", "senior", "manager", "lead")):
                years = 5

        if years is None:
            return None
        if years <= 1:
            return "Entry Level (0-1 yrs)"
        if years <= 4:
            return "Mid Level (2-4 yrs)"
        return "Senior Level (5+ yrs)"

    @staticmethod
    def clean_and_deduplicate_skills(raw_skills: Any) -> List[str]:
        """
        Splits, canonicalizes, and eliminates duplicates inside a single record's skill list.
        """
        if pd.isna(raw_skills) or not raw_skills:
            return []
        items = [s.strip() for s in str(raw_skills).split(",") if s.strip()]
        seen_lower = set()
        cleaned_skills = []
        for item in items:
            item_clean = re.sub(r"\s+", " ", item).strip()
            if not item_clean or item_clean.lower() in ("nan", "none", "na") or len(item_clean) > 40:
                continue
            key = item_clean.lower()
            canonical = SKILL_SYNONYMS.get(key, item_clean.title() if len(item_clean) > 3 else item_clean)
            if canonical.lower() not in seen_lower:
                seen_lower.add(canonical.lower())
                cleaned_skills.append(canonical)
        return cleaned_skills

    # ------------------------------------------------------------------
    # MAIN PROCESSING PIPELINE
    # ------------------------------------------------------------------
    def process_raw_dataset(self, raw_input: Any) -> Dict[str, Any]:
        """
        Takes raw dataset (bytes, filepath, or DataFrame), performs:
        1. De-duplication (Exact & Semantic)
        2. Field Normalization
        3. Business Rule Validation
        4. Relational Schema Decomposition (SQL)
        5. Document Generation (NoSQL)
        """
        if isinstance(raw_input, (bytes, bytearray)):
            df_raw = pd.read_csv(io.BytesIO(raw_input))
        elif isinstance(raw_input, str):
            df_raw = pd.read_csv(raw_input)
        elif isinstance(raw_input, pd.DataFrame):
            df_raw = raw_input.copy()
        else:
            raise TypeError("Unsupported raw_input type. Expected bytes, str path, or DataFrame.")

        initial_rows = len(df_raw)

        # --------------------------------------------------------------
        # 1. DE-DUPLICATION
        # --------------------------------------------------------------
        # A. Remove all-null rows
        df = df_raw.dropna(how="all").copy()

        # B. Exact row deduplication
        rows_before_exact = len(df)
        df = df.drop_duplicates()
        exact_duplicates_dropped = rows_before_exact - len(df)

        # C. Mandatory fields check
        title_col = "Title" if "Title" in df.columns else df.columns[0]
        skills_col = "Skills" if "Skills" in df.columns else None

        df = df.dropna(subset=[title_col])
        if skills_col:
            df = df.dropna(subset=[skills_col])

        # D. Semantic composite key de-duplication
        # Postings with identical Title, Location, and Apply Before are duplicated listings
        dedup_keys = [col for col in [title_col, "Job Location", "Apply Before", "Functional Area"] if col in df.columns]
        rows_before_semantic = len(df)
        df = df.drop_duplicates(subset=dedup_keys, keep="first")
        semantic_duplicates_dropped = rows_before_semantic - len(df)

        # --------------------------------------------------------------
        # 2. FIELD NORMALIZATION
        # --------------------------------------------------------------
        out = pd.DataFrame()
        out["original_title"] = df[title_col].apply(self.normalize_text)

        functional_area = df["Functional Area"] if "Functional Area" in df.columns else pd.Series("Other", index=df.index)
        out["title"] = [
            self.map_role(t, fa) for t, fa in zip(df[title_col], functional_area)
        ]

        out["company"] = "Not Disclosed"
        loc_col = df["Job Location"] if "Job Location" in df.columns else pd.Series("Other", index=df.index)
        out["city"] = loc_col.apply(self.extract_city)

        out["industry"] = functional_area.fillna("Other").astype(str).str.strip()

        min_exp = df["Minimum Experience"] if "Minimum Experience" in df.columns else pd.Series(np.nan, index=df.index)
        career_lvl = df["Career Level"] if "Career Level" in df.columns else pd.Series(np.nan, index=df.index)
        out["experience_level"] = [
            self.parse_experience(m, c) for m, c in zip(min_exp, career_lvl)
        ]

        # Skill list parsing and in-record deduplication
        raw_skills_series = df[skills_col] if skills_col else pd.Series("", index=df.index)
        parsed_skills_list = raw_skills_series.apply(self.clean_and_deduplicate_skills)
        out["skills_list"] = parsed_skills_list
        out["skills"] = parsed_skills_list.apply(lambda lst: ", ".join(lst))
        out["skills_count"] = parsed_skills_list.apply(len)

        # Salary parsing
        sal_series = df["Salary"] if "Salary" in df.columns else pd.Series(np.nan, index=df.index)
        parsed_salaries = sal_series.apply(self.parse_salary)
        out["salary_min_pkr"] = [s[0] for s in parsed_salaries]
        out["salary_max_pkr"] = [s[1] for s in parsed_salaries]
        out["salary_avg_pkr"] = [s[2] for s in parsed_salaries]

        # Date normalization
        date_raw = df["Apply Before"] if "Apply Before" in df.columns else pd.Series(np.nan, index=df.index)
        out["date_posted"] = pd.to_datetime(
            date_raw, format="%d-%b-%y", errors="coerce"
        ).dt.strftime("%Y-%m-%d")

        out["job_type"] = df["Job Type"].fillna("Full Time/Permanent").apply(self.normalize_text) if "Job Type" in df.columns else "Full Time/Permanent"
        out["min_education"] = df["Minimum Education"].fillna("Bachelor").apply(self.normalize_text) if "Minimum Education" in df.columns else "Bachelor"

        # --------------------------------------------------------------
        # 3. QUALITY FILTERS
        # --------------------------------------------------------------
        rows_before_filter = len(out)
        out = out[out["skills_count"] > 0]
        out = out[out["experience_level"].notna()]
        out = out[out["date_posted"].notna()]
        out = out[out["title"] != "Other"]

        if self.require_salary:
            salary_mask = (
                out["salary_min_pkr"].between(self.min_salary, self.max_salary) &
                out["salary_max_pkr"].between(self.min_salary, self.max_salary)
            )
            out = out[salary_mask]

        # Role frequency threshold
        role_counts = out["title"].value_counts()
        keep_roles = role_counts[role_counts >= self.min_postings_per_role].index
        out = out[out["title"].isin(keep_roles)]

        # City frequency normalization
        city_counts = out["city"].value_counts()
        small_cities = city_counts[city_counts < self.min_postings_per_city].index
        out["city"] = out["city"].where(~out["city"].isin(small_cities), "Other")

        out = out.reset_index(drop=True)
        out.insert(0, "job_id", [f"JOB{i + 1:05d}" for i in range(len(out))])
        out["salary_min_pkr"] = out["salary_min_pkr"].astype("Int64")
        out["salary_max_pkr"] = out["salary_max_pkr"].astype("Int64")
        out["salary_avg_pkr"] = out["salary_avg_pkr"].astype("Int64")

        # --------------------------------------------------------------
        # 4. DIMENSIONAL SCHEMA (RELATIONAL 3NF FOR SQL)
        # --------------------------------------------------------------
        # dim_roles
        unique_roles = sorted(out["title"].unique())
        dim_roles = pd.DataFrame({
            "role_id": range(1, len(unique_roles) + 1),
            "role_name": unique_roles
        })
        role_map = dict(zip(dim_roles["role_name"], dim_roles["role_id"]))

        # dim_cities
        unique_cities = sorted(out["city"].unique())
        dim_cities = pd.DataFrame({
            "city_id": range(1, len(unique_cities) + 1),
            "city_name": unique_cities
        })
        city_map = dict(zip(dim_cities["city_name"], dim_cities["city_id"]))

        # dim_companies
        unique_companies = sorted(out["company"].unique())
        dim_companies = pd.DataFrame({
            "company_id": range(1, len(unique_companies) + 1),
            "company_name": unique_companies
        })
        company_map = dict(zip(dim_companies["company_name"], dim_companies["company_id"]))

        # dim_skills
        all_unique_skills = sorted({s for sl in out["skills_list"] for s in sl})
        dim_skills = pd.DataFrame({
            "skill_id": range(1, len(all_unique_skills) + 1),
            "skill_name": all_unique_skills
        })
        skill_map = dict(zip(dim_skills["skill_name"], dim_skills["skill_id"]))

        # fact_jobs
        fact_jobs = pd.DataFrame({
            "job_id": out["job_id"],
            "original_title": out["original_title"],
            "role_id": out["title"].map(role_map),
            "city_id": out["city"].map(city_map),
            "company_id": out["company"].map(company_map),
            "experience_level": out["experience_level"],
            "salary_min_pkr": out["salary_min_pkr"],
            "salary_max_pkr": out["salary_max_pkr"],
            "salary_avg_pkr": out["salary_avg_pkr"],
            "date_posted": out["date_posted"],
            "job_type": out["job_type"],
            "min_education": out["min_education"],
            "industry": out["industry"]
        })

        # bridge_job_skills (many-to-many relationship)
        bridge_records = []
        for idx, row in out.iterrows():
            jid = row["job_id"]
            for sname in row["skills_list"]:
                bridge_records.append({
                    "job_id": jid,
                    "skill_id": skill_map[sname]
                })
        bridge_job_skills = pd.DataFrame(bridge_records)

        # --------------------------------------------------------------
        # 5. EXPLODED SKILLS (FOR SPARK & DASHBOARD COMPATIBILITY)
        # --------------------------------------------------------------
        exploded_records = []
        for idx, row in out.iterrows():
            for sname in row["skills_list"]:
                exploded_records.append({
                    "job_id": row["job_id"],
                    "skill": sname,
                    "title": row["title"],
                    "city": row["city"],
                    "salary_avg_pkr": row["salary_avg_pkr"],
                    "date_posted": row["date_posted"]
                })
        df_exploded_skills = pd.DataFrame(exploded_records)

        # --------------------------------------------------------------
        # 6. DOCUMENT GENERATION (FOR NoSQL / MONGODB)
        # --------------------------------------------------------------
        nosql_documents = []
        for idx, row in out.iterrows():
            nosql_documents.append({
                "_id": row["job_id"],
                "job_id": row["job_id"],
                "role": row["title"],
                "original_title": row["original_title"],
                "company": row["company"],
                "industry": row["industry"],
                "location": {
                    "city": row["city"],
                    "country": "Pakistan"
                },
                "experience_level": row["experience_level"],
                "salary": {
                    "min_pkr": int(row["salary_min_pkr"]) if pd.notna(row["salary_min_pkr"]) else None,
                    "max_pkr": int(row["salary_max_pkr"]) if pd.notna(row["salary_max_pkr"]) else None,
                    "avg_pkr": int(row["salary_avg_pkr"]) if pd.notna(row["salary_avg_pkr"]) else None,
                    "currency": "PKR",
                    "period": "monthly"
                },
                "skills": row["skills_list"],
                "skills_count": len(row["skills_list"]),
                "date_posted": row["date_posted"],
                "job_type": row["job_type"],
                "min_education": row["min_education"]
            })

        # Save metrics
        self.metrics = {
            "initial_raw_rows": initial_rows,
            "exact_duplicates_dropped": exact_duplicates_dropped,
            "semantic_duplicates_dropped": semantic_duplicates_dropped,
            "final_processed_rows": len(out),
            "unique_roles": len(dim_roles),
            "unique_cities": len(dim_cities),
            "unique_skills": len(dim_skills),
            "total_job_skill_links": len(bridge_job_skills),
            "salary_range_pkr": f"{self.min_salary:,} - {self.max_salary:,}"
        }

        # Flattened canonical export for backward compatibility
        export_cols = [
            "job_id", "title", "company", "city", "industry", "experience_level",
            "skills", "salary_min_pkr", "salary_max_pkr", "date_posted",
            "original_title", "job_type", "min_education"
        ]
        df_clean_jobs = out[export_cols].copy()

        return {
            "metrics": self.metrics,
            "clean_jobs": df_clean_jobs,
            "exploded_skills": df_exploded_skills,
            "relational_tables": {
                "dim_roles": dim_roles,
                "dim_cities": dim_cities,
                "dim_companies": dim_companies,
                "dim_skills": dim_skills,
                "fact_jobs": fact_jobs,
                "bridge_job_skills": bridge_job_skills
            },
            "nosql_documents": nosql_documents
        }
