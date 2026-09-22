# TESTING GUIDE — Career Guidance Tool
Complete guide on how to run, test, and verify each part of the project.
Yeh guide **real Rozee.pk dataset** ke outputs dikhati hai — sample/fake data
ke numbers nahi, jo tumne apne terminal par khud produce kiye.

---

## Before You Start: Requirements Check

```bash
python --version
```
Expected: `Python 3.9` or higher

```bash
java -version
```
Expected: something like `openjdk version "17..."` — PySpark needs this.
If missing: install JDK from https://adoptium.net/ (choose JDK 11 or 17)

```bash
pip --version
```
Expected: pip version info.

---

## Setup (Do This Once)

```bash
cd career_guidance_project
python -m venv career_env
career_env\Scripts\activate          # Windows
pip install -r requirements.txt
```

**How to know it worked:** Run `pip list` — you should see `pyspark`,
`pandas`, `scikit-learn`, `streamlit` in the list.

---

## Dataset Placement (Do This Before Step A)

Kaggle se `archive.zip` download karo aur project mein rakho:

```
career_guidance_project/
└── data/
    └── archive.zip        (isme RozeePK-Jobs-2024.csv hai)
```

Agar zip extract kar li ho, to `RozeePK-Jobs-2024.csv` project root mein bhi
rakh sakte ho — script dono jagah check karti hai.

---

## STEP A: Clean the Real Dataset

```bash
python 01_prepare_real_data.py
```

### ✅ Expected Output (yeh real output hai, tumne khud produce kiya):
```
Loading RozeePK-Jobs-2024.csv
Raw rows: 1059
After removing empty/duplicate rows: 1029
Dropped (no skills / experience / date / unmatched role): 116
Dropped (salary missing/unrealistic): 241
Dropped (roles with < 15 postings): 32

Saved: job_postings.csv  (640 postings)
Roles (12):
title
Sales & Business Development    161
Accounts & Finance               76
Customer Support                 75
Marketing                        60
Admin & Office Support           55
Operations & Logistics           48
Software / Web Developer         41
Design & Creative                33
Engineering (Non-IT)             30
Human Resources                  22
Teaching & Training              22
IT & Networking                  17

Cities: 6 | Industries: 29
Date range (deadline proxy): 2024-12-21 -> 2025-03-14

[WARNING] Dataset mein posting date nahi hai (sirf 'Apply Before'). Saari
dates ~1 mahine mein hain, is liye 'Trending Skills' analysis is data par
MEANINGFUL nahi hai.
```

### How to verify it worked:
1. Check `job_postings.csv` appeared in your folder.
2. Row count should be **640**, columns: `job_id, title, company, city,
   industry, experience_level, skills, salary_min_pkr, salary_max_pkr,
   date_posted, original_title, job_type, min_education`.

**If this step fails:**
| Problem | Fix |
|---|---|
| `ERROR: dataset nahi mili` | `archive.zip` ko `data\archive.zip` par rakho |
| `ModuleNotFoundError: pandas` | `pip install -r requirements.txt` dobara chalao, venv active hai check karo |

---

## STEP B: Run the Spark Big Data Analysis

```bash
python 03_spark_skills_analysis.py
```

### ✅ Expected Output (real output, tumne khud produce kiya):
```
Spark session started. Version: 4.2.0
Total job postings loaded: 640
Total (job, skill) pairs after exploding: 2578

--- TOP 15 MOST IN-DEMAND SKILLS (OVERALL) ---
+--------------------------------+------------+---------------+
|skill                           |demand_count|pct_of_all_jobs|
+--------------------------------+------------+---------------+
|Communication                   |234         |36.56          |
|English Fluency                 |90          |14.06          |
|Sales Management                |55          |8.59           |
|Coordination Skills             |48          |7.50           |
|Admin Operations Management     |40          |6.25           |
|End to End Sales                |32          |5.00           |
|Telemarketing Skills            |24          |3.75           |
|Customer Satisfaction Management|23          |3.59           |
|JavaScript                      |21          |3.28           |
|Travels Knowledge               |20          |3.13           |
|MS Excel                        |20          |3.13           |
...

--- AVERAGE SALARY BY ROLE (PKR) ---
+----------------------------+--------------+------------+
|title                       |avg_salary_pkr|num_postings|
+----------------------------+--------------+------------+
|Software / Web Developer    |116122.0      |41          |
|IT & Networking             |102647.0      |17          |
|Human Resources             |100659.0      |22          |
|Engineering (Non-IT)        |90083.0       |30          |
|Accounts & Finance          |86829.0       |76          |
|Design & Creative           |80985.0       |33          |
|Marketing                   |79417.0       |60          |
|Operations & Logistics      |75000.0       |48          |
|Admin & Office Support      |74991.0       |55          |
|Sales & Business Development|62811.0       |161         |
|Customer Support            |58813.0       |75          |
|Teaching & Training         |56136.0       |22          |
+----------------------------+--------------+------------+

Saved: job_skills_exploded.csv, top_skills_overall.csv, trending_skills.csv, role_salaries.csv
Done. Spark session stopped.
```

### ⚠️ Ek cheez expected hai (bug nahi):
"TRENDING SKILLS" table mein har skill ka `older_count = 0` aayega aur
`growth_pct` bohot bara (jaise 28092%) dikhega. Yeh dataset ki date-range
limitation ki wajah se hai (Section 7 of README.md), koi coding error
nahi. **Is table ko presentation mein highlight mat karna.**

### How to verify it worked:
1. Spark tables printed honi chahiye (boxes with `|` characters).
2. 4 new files appear: `job_skills_exploded.csv`, `top_skills_overall.csv`,
   `trending_skills.csv`, `role_salaries.csv`
3. `job_skills_exploded.csv` mein **2578 rows** honi chahiye (640 se zyada) —
   yeh proves "explode" step kaam kar raha hai.

### What this means (for your viva):
- **"Total (job, skill) pairs after exploding: 2578"** → real data transformation ho rahi hai
- **Communication (36.56%)** sabse demanded skill hai — is dataset mein zyada tar postings non-tech roles (Sales, Admin, Customer Support) ki hain, is liye soft skills top par hain

**If this step fails:**
| Problem | Fix |
|---|---|
| `JAVA_HOME` error / `Java gateway process exited` | Java not installed or wrong version. Install JDK 11 or 17. |
| `Error: job_postings.csv not found!` | Step A ka poora output check karo — "Saved: job_postings.csv" print hona chahiye tha |

---

## STEP C: Train the Recommendation Engine

```bash
python 04_recommendation_engine.py
```

### ✅ Expected Output (real output, tumne khud produce kiya):
```
============================================================
EXAMPLE 1: Skill Gap Analysis
============================================================
Target Role: Sales & Business Development
Market Match: 20.0%
Skills you already have: ['Communication', 'Sales Management']
Skills to learn next: ['English Fluency', 'End to End Sales', 'Coordination Skills', 'Telemarketing Skills', 'Sales Automation', 'Business Development Process', 'B2B Business Development', 'Student Counseling']

============================================================
EXAMPLE 2: Salary Prediction Model Training & Inference
============================================================
Salary Model Performance:
  Mean Absolute Error: PKR 40,066
  R² Score: -0.167
  [Note] Low/negative R² is expected here: small sample size (640 rows)
  split across many role/city/industry categories. Report this honestly as
  a limitation, not a bug — don't claim a high R² in your presentation.

Predicted salary for Mid Level (2-4 yrs) Sales & Business Development in Lahore (Sales & Business Development, 6 skills):
PKR 97,981 per month

Saved: salary_model.pkl, salary_encoders.pkl, salary_features.pkl, salary_metadata.pkl
```

### How to verify it worked:
1. Three (actually four) `.pkl` files appear.
2. R² negative aana **normal hai is dataset par** — yeh kam data ki wajah
   se hai, koi bug nahi. **0.98 jaisa number expect mat karo**, wo purane
   synthetic (fake) data se tha.
3. "Skills to learn next" list logically make sense karni chahiye.

### What R² and MAE mean (for your viva):
- **R² Score (-0.167)**: model role/city/industry/experience/skill-count se
  salary ko explain karne mein average guess se bhi kharab hai. Wajah: 640
  rows, 12 roles, 29 industries — itne categories ke liye data kam hai.
- **MAE (PKR 40,066)**: average prediction error, salary range ke hisaab se
  bara hai — yeh bhi chhote data ki nishani hai.
- **Honest framing:** "Model ka architecture sahi hai (Random Forest,
  proper encoding, fallback logic) — accuracy sample size se limited hai.
  Zyada real data milne par yehi pipeline behtar model dega."

**If this step fails:**
| Problem | Fix |
|---|---|
| `Error: Input CSVs not found` | Step A aur B pehle chalao |

---

## STEP D: Run the Dashboard (Final Demo)

```bash
streamlit run 05_dashboard_app.py
```

### ✅ Expected Output:
```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

### How to test the dashboard:

**Test 1 — Market Overview tab:**
- Top numbers should show **640** total postings
- Charts: top 15 skills (Communication should be #1), top paying roles
  (Software / Web Developer should be #1)

**Test 2 — Trending Skills tab:**
- Will show the caveat note about deadline-vs-posting-date limitation
- Growth % numbers will look unrealistically large — this is expected,
  don't present this tab as a real market insight

**Test 3 — My Skill Gap & Salary tab (your live demo):**
1. Select target role: any of the 12 real roles (e.g. `Software / Web Developer`)
2. Select city, industry, experience — all populated from real data, no
   fixed dropdown values
3. Select a couple of skills you already have
4. Click **"Analyze My Career Path"**

✅ Expected result: match % and salary estimate will vary depending on your
selections — there's no single fixed "expected" number anymore since the
dropdowns are built from real, varied data.

**If the dashboard doesn't load or shows errors:**
| Problem | Fix |
|---|---|
| Blank page / "File not found" errors | You skipped Steps A, B, or C. Run them in order first. |
| "Address already in use" | `streamlit run 05_dashboard_app.py --server.port 8502` |
| Charts don't show | Refresh the browser page (Ctrl+R) |

To stop the dashboard: go back to your terminal and press `Ctrl+C`.

---

## Full Run Order (Copy-Paste Checklist)

```bash
python 01_prepare_real_data.py       # Step A — real data cleaning
python 03_spark_skills_analysis.py   # Step B
python 04_recommendation_engine.py   # Step C
streamlit run 05_dashboard_app.py    # Step D (opens dashboard)
```

Run every time you start fresh, or if you get a newer/updated `archive.zip`.

---

## How to "Prove" Your Project Works (for submission/viva)

Take screenshots of:
1. Terminal output of Step A — proves real Kaggle data was cleaned (1059 → 640)
2. Terminal output of Step B (the Spark tables) — proves you used PySpark
3. A completed "Skill Gap" result from Tab 3 with your own test inputs
4. The R² score from Step C terminal output — and be ready to explain it
   honestly as a small-sample limitation, not hide it

Put these 4 screenshots in your report/presentation slides as evidence,
along with one slide on limitations (see README.md Section 7).

---