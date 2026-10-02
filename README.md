# Career Guidance Tool — Big Data Analytics Project

Complete A-Z guide:

## 1. Problem Statement (Yeh Sabse Pehle Samjho — Sir Yehi Puchein Ge)

**Real Problem:** Pakistan mein har saal lakhon fresh graduates nikalte hain, lekin unhe pata nahi hota ke job market mein **asal mein kya demand hai**. Nateeja: log wo skills seekhte hain jo already saturated hain, ya jo market mein demand hi nahi rakhtin. Career counseling proper tareeqe se available nahi, aur jo hai wo data-driven nahi, sirf generic advice deti hai.

**Why This Matters:** Job postings (Rozee.pk, LinkedIn, Indeed) mein yeh information already maujood hai — kaunsi skills, kaunse roles, kaunsi cities mein demand mein hain — lekin koi is data ko systematically analyze nahi karta.

**Solution:** Real job postings ka data collect karo → Spark se process karo (yeh "Big Data" component hai, kyunke real-world mein lakhon postings hoti hain) → market trends nikalo (top skills, salary patterns) → phir ek **personalized tool** banao jahan student apna target role aur current skills batae, aur system bataye "yeh skills seekh lo, tumhara market match itna %ge hai, expected salary itni hogi".

**Impact:** Yeh generic project nahi hai — yeh directly students/universities/career counselors use kar sakte hain. Real utility hai.

---

## 2. Tech Stack aur Kyun

- **MinIO / AWS S3** — Object Storage for raw data ingestion (`career-guidance-raw` bucket)
- **SQL (PostgreSQL / SQLite)** — 3NF Relational Data Warehouse (`fact_jobs`, `dim_roles`, `dim_skills`, `bridge_job_skills`)
- **NoSQL (MongoDB)** — Document store for rich JSON job postings with embedded skills/salary schemas
- **PySpark** — Bulk job postings distributed analytics & skill frequency explosion (Big Data component)
- **Pandas + Scikit-learn** — Predictive salary modeling (Random Forest Regressor)
- **Streamlit** — Interactive modern UI with real-time Career Guidance & Live Data Engineering Explorer

---

## 3. Folder Structure

```
career_guidance_project/
│
├── core/
│   ├── object_storage.py            # MinIO / AWS S3 / Emulated S3 Client
│   ├── data_processor.py            # De-duplication, Normalization & 3NF Schema Generator
│   ├── db_manager.py                # SQL (PostgreSQL/SQLite) & NoSQL (MongoDB) Manager
│   ├── pipeline.py                  # End-to-End ETL Pipeline Orchestrator
│   ├── analytics.py                 # Trending & salary helper functions
│   └── recommender.py               # Skill gap & ML salary model functions
├── 01_pipeline_storage_to_db.py     # Local -> Object Storage -> Processing -> SQL/NoSQL DB
├── 01_prepare_real_data.py          # Legacy runner (delegates to 01_pipeline_storage_to_db)
├── 02_scraper_template.py           # Optional: live scraper template
├── 03_spark_skills_analysis.py      # PySpark analysis (Step B) - CORE Big Data part
├── 04_recommendation_engine.py      # Skill gap + salary model (Step C)
├── 05_dashboard_app.py              # Streamlit dashboard + Data Engineering Explorer (Step D)
├── docker-compose.yml               # MinIO, PostgreSQL, and MongoDB containers
├── DATA_ENGINEERING_GUIDE.md        # Complete Data Pipeline architecture & viva guide
├── requirements.txt
└── README.md
```

---

## 4. Setup

```bash
python -m venv career_env
career_env\Scripts\activate          # Windows
pip install -r requirements.txt
```

*(Optional) Start Docker services (MinIO, PostgreSQL, MongoDB):*
```bash
docker compose up -d
```
> Note: Even if Docker is not started, the pipeline automatically uses intelligent local fallbacks (Emulated S3, SQLite, and JSON Document Store) with zero crashes!

---

## 5. Dataset — Kya Use Ho Raha Hai

Is project mein **synthetic/fake data nahi hai**. Real dataset use ho raha hai:

**Source:** Kaggle — "Pakistan Job Market Dataset (Rozee.pk)", file `RozeePK-Jobs-2024.csv`.

**Raw dataset:** 1059 real job postings, columns: Title, Job Location, Functional Area, Career Level, Minimum Experience, Minimum Education, Job Type, Skills, Salary, Apply Before.

---

## 6. Step-by-Step Execution

### Step A — Data Pipeline (Local ➔ Object Storage ➔ Processing ➔ SQL/NoSQL DB)
```bash
python 01_pipeline_storage_to_db.py
```
**Kya karta hai:**
- **Local Storage ➔ Object Storage:** Raw CSV ko MinIO/S3 bucket `career-guidance-raw` mein upload karta hai
- **Object Storage ➔ Python:** Raw data stream direct memory mein download karta hai
- **Data Processing:**
  - **De-duplication:** Exact duplicate rows aur composite key duplicates remove karta hai
  - **Normalization:** 700+ raw titles ko 12 canonical roles mein group karta hai; Pakistani cities extract karta hai; salaries ko numeric PKR mein parse karta hai; experience level buckets banata hai; skills ke synonyms standardize karta hai
- **Load to SQL Database:** PostgreSQL / SQLite mein 3NF relational schema load karta hai (`fact_jobs`, `dim_roles`, `dim_cities`, `dim_skills`, `bridge_job_skills`, view `vw_job_market_analytics`)
- **Load to NoSQL Database:** MongoDB mein embedded document structure load karta hai
- **Sync:** Spark aur Dashboard ke liye clean `job_postings.csv` aur `job_skills_exploded.csv` generate karta hai

### Step B — Spark Analysis (CORE Big Data component)
```bash
python 03_spark_skills_analysis.py
```
**Kya karta hai:**
- Job postings load karta hai, `skills` column ko "explode" karta hai (ek job posting jisme 5 skills hain, wo 5 separate rows ban jati hain — yeh Spark ka `explode()` function hai)
- Spark SQL se: overall top skills, role-wise top skills
- Trending skills nikalta hai (last 90 din vs baaki period, daily-rate normalize karke) — **is dataset par yeh reliable nahi hai**, Section 7 dekho
- Average salary by role

### Step C — Recommendation Engine
```bash
python 04_recommendation_engine.py
```
**Kya karta hai:**
- Skill gap analyzer: target role batao, current skills batao, system bataega kya missing hai
- Salary prediction model train karta hai (Random Forest) jo role, city, experience, industry, skill count se salary predict karta hai

### Step D — Dashboard (Final Demo)
```bash
streamlit run 05_dashboard_app.py
```
3 tabs honge:
1. **Market Overview** — top skills, top paying roles
2. **Trending Skills** — dataset ki date-limitation ki wajah se caveat ke saath dikhta hai
3. **My Skill Gap & Salary** — student apna role/skills select kare, personalized guidance paaye

---

## 7. Honest Limitations

Real data use karne ka faida yeh hai ke project asli hai, lekin do cheezein sample-size ki wajah se kamzor hain:

1. **Salary Model ka R² kam (ya negative) hai.** 640 postings 12 roles × 6 cities × 29 industries mein bat jate hain, is liye model ke paas seekhne ko kaafi data nahi hota. Yeh ek real limitation hai, bug nahi.
2. **Trending Skills is dataset par meaningful nahi hai.** Dataset mein posting date nahi, sirf deadline hai, jo sirf ~83 din ke range mein simat jata hai. Isse "recent vs older period" comparison ka koi matlab nahi banta (older period mein data hi nahi bachta).

"Maine real Kaggle dataset use kiya, sample-generated data nahi. Real data ka faida yeh hai ke findings genuine hain, lekin sample size chhota hone ki wajah se salary model aur trending analysis ki accuracy limited hai — real deployment mein zyada data (jaise live scraping se roz naye postings) is masle ko solve karega."

---



## 8. Common Errors

| Error | Fix |
|---|---|
| `JAVA_HOME not set` | JDK install karo |
| `ERROR: dataset nahi mili` (Step A) | `archive.zip` ko `data\archive.zip` par rakho, ya `RozeePK-Jobs-2024.csv` project root mein rakho |
| `Error: job_postings.csv not found` (Step B) | Step A pehle chalao aur uska poora output check karo ke "Saved: job_postings.csv" print hua ho |
| Scraper 403/blocked (`02_scraper_template.py`) | Site bot detection kar rahi hai — headers change karo, delay barhao |
| Dashboard mein purani data | Steps A→B→C dobara chalao is order mein jab bhi naya data daalo |
| Salary prediction error "unseen category" | Dashboard mein wahi role/city/industry select karo jo training data mein tha |

---
