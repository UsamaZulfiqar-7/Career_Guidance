"""
STEP 1: Prepare REAL Job Postings Data (Rozee.pk 2024, Kaggle)
------------------------------------------------------------------
Yeh script Kaggle ka "Pakistan Job Market Dataset (Rozee.pk)" ko clean karke
project ke standard format mein convert karti hai:

    job_id, title, company, city, industry, experience_level, skills,
    salary_min_pkr, salary_max_pkr, date_posted

Isse 01_generate_sample_data.py (synthetic data) ki zaroorat khatam.

Dataset kahan rakhni hai (koi bhi ek jagah chalegi):
    data/archive.zip                (recommended)
    archive.zip                     (project root mein)
    data/RozeePK-Jobs-2024.csv      (agar zip extract kar li ho)

Run:  python 01_prepare_real_data.py
"""

import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

import pandas as pd

# ------------------------------------------------------------------ SETTINGS
ZIP_CANDIDATES = [Path("data/archive.zip"), Path("archive.zip")]
CSV_CANDIDATES = [Path("data/RozeePK-Jobs-2024.csv"), Path("RozeePK-Jobs-2024.csv")]
OUTPUT_FILE = "job_postings.csv"

# True  = sirf woh jobs jin mein salary di hui hai (salary model ke liye safe)
# False = salary-less jobs bhi rakho (core/ ko NaN handle karna hoga)
REQUIRE_SALARY = True
MIN_POSTINGS_PER_ROLE = 15   # isse kam postings wale roles skill-gap ke liye bekaar hain
MIN_POSTINGS_PER_CITY = 10   # baqi cities "Other" mein chali jati hain
MIN_SALARY, MAX_SALARY = 10_000, 1_000_000   # PKR/month, unrealistic values hatao

# ------------------------------------------------------------------ LOAD
def load_raw() -> pd.DataFrame:
    for p in ZIP_CANDIDATES:
        if p.exists():
            with zipfile.ZipFile(p) as z:
                name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
                print(f"Loading {name} from {p}")
                with z.open(name) as f:
                    return pd.read_csv(f)
    for p in CSV_CANDIDATES:
        if p.exists():
            print(f"Loading {p}")
            return pd.read_csv(p)
    sys.exit(
        "ERROR: dataset nahi mili. archive.zip ko 'data' folder mein rakho:\n"
        "  project_folder/data/archive.zip"
    )

# ------------------------------------------------------------------ CITY
KNOWN_CITIES = [
    "Lahore", "Karachi", "Islamabad", "Rawalpindi", "Faisalabad", "Multan",
    "Peshawar", "Quetta", "Sialkot", "Gujranwala", "Hyderabad", "Bahawalpur",
    "Sargodha", "Jhelum", "Gujrat", "Sahiwal", "Abbottabad", "Sukkur",
]

def extract_city(loc) -> str:
    """'Johar Town, Lahore, Pakistan' -> 'Lahore'"""
    parts = [p.strip() for p in re.sub(r"\s+", " ", str(loc)).split(",") if p.strip()]
    parts = [p for p in parts if p.lower() != "pakistan"]
    for p in parts:
        if p in KNOWN_CITIES:
            return p
    return parts[0] if parts else "Other"

# ------------------------------------------------------------------ ROLE
# Order matters: pehla match jeetta hai.
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

def map_role(title: str, functional_area) -> str:
    t = str(title).lower()
    for role, pattern in ROLE_RULES:
        if re.search(pattern, t):
            return role
    return FUNCTIONAL_AREA_TO_ROLE.get(str(functional_area).strip(), "Other")

# ------------------------------------------------------------------ EXPERIENCE
def experience_label(min_exp, career_level):
    s = str(min_exp).lower().strip()
    years = None
    if s not in ("nan", "none", ""):
        if "fresh" in s or "less than" in s:
            years = 0
        else:
            m = re.search(r"\d+", s)
            years = int(m.group()) if m else None
    if years is None:  # fallback: Career Level
        c = str(career_level).lower()
        if "entry" in c or "intern" in c or "student" in c:
            years = 0
        elif "experienced" in c:
            years = 3
        elif "head" in c or "senior" in c or "manager" in c:
            years = 5
    if years is None:
        return None
    if years <= 1:
        return "Entry Level (0-1 yrs)"
    if years <= 4:
        return "Mid Level (2-4 yrs)"
    return "Senior Level (5+ yrs)"

# ------------------------------------------------------------------ SALARY
SALARY_RE = re.compile(r"PKR\.?\s*([\d,]+)\s*-\s*([\d,]+)")

def parse_salary(s):
    m = SALARY_RE.search(str(s))
    if not m:
        return (None, None)
    lo, hi = int(m.group(1).replace(",", "")), int(m.group(2).replace(",", ""))
    if hi < lo:
        lo, hi = hi, lo
    return (lo, hi)

# ------------------------------------------------------------------ SKILLS
SYNONYMS = {
    "communication skills": "Communication",
    "communication": "Communication",
    "excel": "MS Excel",
    "microsoft excel": "MS Excel",
    "ms excel": "MS Excel",
    "fluent in english": "English Fluency",
    "javascript": "JavaScript",
}

def split_skills(raw) -> list:
    out = []
    for x in str(raw).split(","):
        x = re.sub(r"\s+", " ", x).strip()
        if x and x.lower() != "nan" and len(x) <= 40:
            out.append(x)
    return out

def clean_skills(series: pd.Series) -> pd.Series:
    lists = series.apply(split_skills)
    surface = Counter(s for lst in lists for s in lst)
    canon = {}
    for s, _ in surface.most_common():          # most common spelling wins
        canon.setdefault(s.lower(), s)

    def normalise(lst):
        seen, result = set(), []
        for s in lst:
            key = s.lower()
            name = SYNONYMS.get(key, canon.get(key, s))
            if name.lower() not in seen:
                seen.add(name.lower())
                result.append(name)
        return ", ".join(result)

    return lists.apply(normalise)

# ------------------------------------------------------------------ MAIN
def main():
    raw = load_raw()
    print(f"Raw rows: {len(raw)}")

    df = raw.dropna(how="all").copy()
    df = df.dropna(subset=["Title", "Skills"])
    df = df.drop_duplicates()
    print(f"After removing empty/duplicate rows: {len(df)}")

    out = pd.DataFrame()
    out["original_title"] = df["Title"].astype(str).str.strip()
    out["title"] = [map_role(t, fa) for t, fa in zip(df["Title"], df["Functional Area"])]
    out["company"] = "Not Disclosed"                      # dataset mein company column nahi
    out["city"] = df["Job Location"].apply(extract_city)
    out["industry"] = df["Functional Area"].fillna("Other").astype(str).str.strip()
    out["experience_level"] = [
        experience_label(m, c) for m, c in zip(df["Minimum Experience"], df["Career Level"])
    ]
    out["skills"] = clean_skills(df["Skills"])
    sal = df["Salary"].apply(parse_salary)
    out["salary_min_pkr"] = [s[0] for s in sal]
    out["salary_max_pkr"] = [s[1] for s in sal]
    # NOTE: dataset mein POSTING date nahi hai, sirf "Apply Before" (deadline) hai.
    out["date_posted"] = pd.to_datetime(
        df["Apply Before"], format="%d-%b-%y", errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    out["job_type"] = df["Job Type"].values
    out["min_education"] = df["Minimum Education"].values

    # ---- filters
    n0 = len(out)
    out = out[out["skills"].str.len() > 0]
    out = out[out["experience_level"].notna()]
    out = out[out["date_posted"].notna()]
    out = out[out["title"] != "Other"]
    print(f"Dropped (no skills / experience / date / unmatched role): {n0 - len(out)}")

    if REQUIRE_SALARY:
        n0 = len(out)
        ok = out["salary_min_pkr"].between(MIN_SALARY, MAX_SALARY) & out["salary_max_pkr"].between(MIN_SALARY, MAX_SALARY)
        out = out[ok]
        print(f"Dropped (salary missing/unrealistic): {n0 - len(out)}")

    role_counts = out["title"].value_counts()
    keep_roles = role_counts[role_counts >= MIN_POSTINGS_PER_ROLE].index
    print(f"Dropped (roles with < {MIN_POSTINGS_PER_ROLE} postings): {(~out['title'].isin(keep_roles)).sum()}")
    out = out[out["title"].isin(keep_roles)]

    city_counts = out["city"].value_counts()
    small = city_counts[city_counts < MIN_POSTINGS_PER_CITY].index
    out["city"] = out["city"].where(~out["city"].isin(small), "Other")

    out = out.reset_index(drop=True)
    out.insert(0, "job_id", [f"JOB{i + 1:05d}" for i in range(len(out))])
    out["salary_min_pkr"] = out["salary_min_pkr"].astype("Int64")
    out["salary_max_pkr"] = out["salary_max_pkr"].astype("Int64")

    cols = ["job_id", "title", "company", "city", "industry", "experience_level",
            "skills", "salary_min_pkr", "salary_max_pkr", "date_posted",
            "original_title", "job_type", "min_education"]
    out[cols].to_csv(OUTPUT_FILE, index=False)

    print(f"\nSaved: {OUTPUT_FILE}  ({len(out)} postings)")
    print(f"Roles ({out['title'].nunique()}):")
    print(out["title"].value_counts().to_string())
    print(f"\nCities: {out['city'].nunique()} | Industries: {out['industry'].nunique()}")
    print(f"Date range (deadline proxy): {out['date_posted'].min()} -> {out['date_posted'].max()}")
    print(
        "\n[WARNING] Dataset mein posting date nahi hai (sirf 'Apply Before'). "
        "Saari dates ~1 mahine mein hain, is liye 'Trending Skills' analysis is data par "
        "MEANINGFUL nahi hai."
    )

if __name__ == "__main__":
    main()