# 🎯 Career Guidance Tool — Big Data & Cloud Data Engineering Pipeline

A comprehensive Big Data Analytics and Data Engineering system that processes real Pakistani job market data (Rozee.pk), moves it from Local Storage to Object Storage (MinIO / S3), cleans and normalizes it in Python, persists it into SQL (PostgreSQL / SQLite 3NF) and NoSQL (MongoDB), executes distributed analytics with Apache PySpark, predicts salaries using Machine Learning, and visualizes everything via an interactive modern Streamlit Dashboard.

---

## 📑 Table of Contents
1. [Problem Statement](#1-problem-statement)
2. [Tech Stack & Architecture](#2-tech-stack--architecture)
3. [Folder Structure](#3-folder-structure)
4. [Environment Setup](#4-environment-setup)
5. [Step-by-Step Execution Guide (Project Kaise Chalana Hai)](#5-step-by-step-execution-guide)
6. [Dashboard Walkthrough (4 Tabs)](#6-dashboard-walkthrough)
7. [Automated Testing Suite](#7-automated-testing-suite)
8. [Viva / Presentation Guide (Sir Ke Sawaalat Aur Jawaabaat)](#8-viva--presentation-guide)
9. [Dataset Limitations & Troubleshooting](#9-dataset-limitations--troubleshooting)

---

## 1. Problem Statement

* **Real Problem:** Pakistan mein har saal hazaron fresh graduates nikalte hain, lekin unhe pata nahi hota ke job market mein **asal mein kis skill ki demand hai**. Nateeja: log saturated ya obsolete skills seekh kar time aur resources waste karte hain. Conventional counseling data-driven nahi hoti.
* **Our Solution:** Real job postings ka data collect karo ➔ Object Storage mein ingest karo ➔ Python mein De-duplication aur Normalization karo ➔ SQL aur NoSQL databases mein persist karo ➔ Apache PySpark se distributed skill demand aur salary patterns nikalo ➔ Scikit-Learn se personalized skill gap aur salary prediction model train karo ➔ Streamlit interactive dashboard se student ko personalized recommendations aur live pipeline explorer provide karo.

---

## 2. Tech Stack & Architecture

### Technologies Used:
* **Object Storage:** MinIO (AWS S3-compatible, bucket: `career-guidance-raw`) + Local S3 Emulator fallback
* **SQL Database:** PostgreSQL 15 (Docker) + SQLite 3NF Data Warehouse (`career_guidance.db`)
* **NoSQL Database:** MongoDB 6 (Docker) + JSON Document Store fallback (`nosql_database.json`)
* **Distributed Big Data Engine:** Apache PySpark 3.5+ / 4.2+ (JVM-accelerated distributed processing)
* **Machine Learning:** Scikit-Learn (Random Forest Regressor, MAE / R² benchmarks)
* **Web UI Dashboard:** Streamlit + Plotly (Modern Dark/Light mode theme + Live Database Console)
* **Testing:** Pytest (14 automated unit and integration tests)

### Data Flow Diagram:
```
                      [ 1. Local Storage ]
                 RozeePK-Jobs-2024.csv (Raw Data)
                               │
                               ▼
               [ 2. Object Storage Ingestion ]
           MinIO / AWS S3 (Bucket: career-guidance-raw)
           Key: raw/jobs/RozeePK-Jobs-2024.csv
                               │
                               ▼
                 [ 3. Python Memory Stream ]
            ObjectStorageManager.get_object_bytes()
                               │
                               ▼
                 [ 4. Python Data Processing ]
                          DataProcessor
        ┌──────────────────────┴──────────────────────┐
        ▼                                             ▼
   DE-DUPLICATION                               NORMALIZATION
• Exact Row Duplicates                       • Whitespace & Text Cleanup
• Semantic Key Duplicates:                   • 700+ Raw Titles ➔ 12 Standard Roles
  (Title, Location, Apply Before)            • Addresses ➔ Pakistani Metros
• In-record Skill Duplicates                 • Unstructured Salary ➔ Min/Max/Avg PKR
                                             • Experience ➔ Entry/Mid/Senior Tiers
                                             • Skill Synonyms ➔ Canonical Names
                                             • ISO 8601 Date Parsing (YYYY-MM-DD)
        └──────────────────────┬──────────────────────┘
                               │
        ┌──────────────────────┴──────────────────────┐
        ▼                                             ▼
 [ 5. SQL Database (3NF) ]                  [ 6. NoSQL Database ]
PostgreSQL / SQLite Database                   MongoDB / Doc Store
• dim_roles (role_id, role_name)            • Collection: 'job_postings'
• dim_cities (city_id, city_name)           • Embedded Documents:
• dim_companies (company_id, name)             - skills: ["Python", "SQL"...]
• dim_skills (skill_id, skill_name)            - salary: {min, max, avg}
• fact_jobs (job_id, salary, dates...)         - location: {city, country}
• bridge_job_skills (Many-to-Many)          • Compound Indexes
• View: vw_job_market_analytics
        └──────────────────────┬──────────────────────┘
                               │
                               ▼
           [ 7. Downstream Big Data & ML Artifacts ]
• job_postings.csv & job_skills_exploded.csv
• PySpark distributed skill frequency analysis (03_spark_skills_analysis.py)
• Scikit-Learn Random Forest Salary Model (04_recommendation_engine.py)
• Modern Streamlit UI Dashboard + Storage Explorer (05_dashboard_app.py)
```

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
│   ├── analytics.py                 # Spark & Trending helper analytics
│   └── recommender.py               # Skill gap & ML salary model functions
├── 01_pipeline_storage_to_db.py     # Local ➔ Object Storage ➔ Processing ➔ SQL/NoSQL DB
├── 01_prepare_real_data.py          # Legacy runner (delegates to 01_pipeline_storage_to_db)
├── 02_scraper_template.py           # Optional live web scraper template
├── 03_spark_skills_analysis.py      # PySpark analysis (Step B) - CORE Big Data part
├── 04_recommendation_engine.py      # Skill gap + salary model training (Step C)
├── 05_dashboard_app.py              # Streamlit dashboard + Data Engineering Explorer (Step D)
├── docker-compose.yml               # MinIO, PostgreSQL, and MongoDB containers
├── tests/
│   ├── test_data_pipeline.py        # Object Storage, ETL, SQL, and NoSQL unit tests
│   ├── test_analytics.py            # Spark analytics unit tests
│   └── test_recommender.py          # Recommendation and ML model unit tests
├── requirements.txt                 # Project dependencies
└── README.md                        # Master Documentation
```

---

## 4. Environment Setup

### Prerequisites:
* Python 3.10+
* Java JDK 8/11/17 (PySpark ke liye): `java -version`
* *(Optional)* Docker Desktop: MinIO, PostgreSQL, MongoDB run karne ke liye.

### Virtual Environment Setup:
```powershell
# 1. Virtual environment create karein (agar pehle se nahi hai)
python -m venv career_env

# 2. Virtual environment activate karein
career_env\Scripts\activate          # Windows PowerShell / CMD

# 3. Dependencies install karein
pip install -r requirements.txt
```

### *(Optional)* Docker Stack Start Karein:
```powershell
docker compose up -d
```
> **Resilient Fallback Guarantee:** Agar aapke computer par Docker start na ho, to bhi code crash nahi hoga! Pipeline automatically **Local Emulated S3**, **SQLite 3NF Database**, aur **JSON Document Store** use karke 100% execute hoti hai.

---

## 5. Step-by-Step Execution Guide

Project ko run karne ke liye niche diye gaye steps ko order mein execute karein:

### Step 1: Run Data Engineering Pipeline (Local ➔ Object Storage ➔ Processing ➔ DB)
```powershell
career_env\Scripts\python.exe 01_pipeline_storage_to_db.py
```
*(Ya `career_env\Scripts\python.exe 01_prepare_real_data.py` chalayein, dono auto-connected hain).*

**Yeh script kya karti hai:**
1. Raw Kaggle dataset (`RozeePK-Jobs-2024.csv`) ko MinIO Object Storage bucket `career-guidance-raw` mein ingest karti hai.
2. Object Storage se direct Python memory mein stream download karti hai.
3. **De-duplication:** 4 exact duplicates + 12 semantic duplicate postings filter karti hai.
4. **Normalization:** 700+ raw titles ko 12 canonical roles mein map karti hai, salary parse karti hai, Pakistani cities nikalati hai, aur skills ke synonyms standardize karti hai.
5. **SQL Loading:** PostgreSQL / SQLite mein 3NF relational schema load karti hai (`dim_roles`, `dim_cities`, `dim_companies`, `dim_skills`, `fact_jobs`, `bridge_job_skills`).
6. **NoSQL Loading:** MongoDB mein rich embedded documents (`job_postings`) insert karti hai.
7. Downstream Spark aur Dashboard ke liye clean `job_postings.csv` aur `job_skills_exploded.csv` generate karti hai.

---

### Step 2: Run PySpark Big Data Analysis
```powershell
career_env\Scripts\python.exe 03_spark_skills_analysis.py
```
**Yeh script kya karti hai:**
* Spark Session start karti hai.
* `skills` column ko distributed level par explode karti hai (one job ➔ multiple skill records).
* Spark SQL se overall top 15 in-demand skills aur role-wise average salary benchmarks calculate karti hai.
* Output tables save karti hai: `top_skills_overall.csv`, `trending_skills.csv`, `role_salaries.csv`.

---

### Step 3: Train Recommendation Engine & Salary Model
```powershell
career_env\Scripts\python.exe 04_recommendation_engine.py
```
**Yeh script kya karti hai:**
* Skill Gap Analyzer verify karti hai (user skills vs market demand).
* Scikit-Learn Random Forest Regressor model train karti hai.
* Serialized bundle save karti hai: `salary_model.pkl`, `salary_encoders.pkl`, `salary_features.pkl`.

---

### Step 4: Launch Interactive Streamlit Dashboard
```powershell
career_env\Scripts\streamlit.exe run 05_dashboard_app.py
```
Browser mein URL open hoga: `http://localhost:8501`.

---

## 6. Dashboard Walkthrough (4 Tabs)

Dashboard mein 4 modern interactive tabs hain:
1. **📊 Market Overview:** Top 15 skills bar chart, average salary by role chart, total job postings, aur cities distribution.
2. **🚀 Trending Skills:** Dynamic temporal window normalization ke sath skills ka growth rate comparison.
3. **🧭 My Skill Gap & Salary:** Student apna Target Role, Target City, Experience Level, aur Current Skills select kare; system realtime Market Match % calculate karega, missing skills bataega, aur expected salary predict karega.
4. **🗄️ Data Engineering & Storage Pipeline (Sir Ke Liye Khas):**
   * Object Storage (MinIO/S3) status badge aur bucket metadata.
   * SQL Relational 3NF table stats (`fact_jobs`, `dim_roles`, `dim_skills`, `bridge_job_skills`).
   * **Live Interactive SQL Query Console:** Jahan Sir dropdown se queries select kar sakte hain ya custom SQL likh kar "Execute Query" button se live database run kar sakte hain!
   * **Live MongoDB Document Explorer:** Jahan MongoDB ke nested JSON documents (with embedded skills array and salary subdocs) inspect kiye ja sakte hain.

---

## 7. Automated Testing Suite

Tamam components ki testing ke liye automated pytest test suite shamil hai:
```powershell
career_env\Scripts\pytest.exe -v
```
**Tests Covered (14/14 Pass):**
* Object Storage upload, download, and listing.
* Exact & semantic deduplication logic.
* Role regex mapping, city extraction, salary parsing, and skill canonicalization.
* Relational 3NF tables creation and joins.
* NoSQL document loading and querying.
* Spark dynamic windowing & trending analytics.
* Machine Learning salary model inference & skill gap matching.

---

## 8. Viva / Presentation Guide (Sir Ke Sawaalat Aur Jawaabaat)

### Q1: "Aapne direct CSV database mein kyun nahi daali? Object Storage kyun use kiya?"
> *"Sir, modern Data Engineering architecture mein raw data direct operational database mein nahi daala jata. Pehle raw files ko ek centralized Object Storage (Data Lake / S3) mein archive kiya jata hai taake raw uncorrupted copy hamesha available rahe. Phir downstream ETL pipelines us raw lake se data stream karke clean karti hain aur target databases mein load karti hain."*

### Q2: "Aapne De-duplication kaise ki?"
> *"Sir, humne two levels par de-duplication ki:*
> 1. **Exact Duplicate Removal:** Agar complete row 100% duplicate ho to drop kiya (4 rows filter huin).
> 2. **Semantic Composite Key Removal:** Job portals par employers aksar wohi job thode din baad repost kar dete hain. Humne `(Title, Job Location, Apply Before, Functional Area)` ki composite key par check lagaya taake duplicate postings filter hon (12 reposted listings filter huin).
> 3. **In-Record Skill Deduplication:** Ek hi job posting ke andar bar bar repeat hone wali skills ko bhi deduplicate kiya."*

### Q3: "SQL aur NoSQL dono kyun use kiye?"
> *"Sir, humne polyglot persistence demonstrate kiya hai:*
> * **SQL (Relational):** 3NF star schema (`fact_jobs`, `dim_roles`, `dim_cities`, `dim_skills`, `bridge_job_skills`) banaya jo complex analytical queries aur joins ke liye optimal hai.
> * **NoSQL (MongoDB):** Document-oriented store use kiya jisme har job posting ek nested JSON document hai jisme skills array aur salary details embedded hain. Yeh fast read aur web API serving ke liye best hai."*

### Q4: "Chhote dataset par PySpark use karne ka kya faida?"
> *"Sir, PySpark distributed engine hai. Humne code modular Spark SQL aur transformations (`explode()`, `groupBy()`) par likha hai. Iska faida yeh hai ke chahe dataset 1,000 rows ka ho ya 10 million rows ka, hamara code bina kisi tabdeeli ke poore Spark cluster par parallel scale ho sakta hai."*

---

## 9. Dataset Limitations & Troubleshooting

### Dataset Limitations (Viva Mein Honestly Batane Ke Liye):
1. **Posting Date Limitation:** Dataset mein posting date nahi thi, sirf 'Apply Before' deadline thi jo ~83 din ke chhotay span mein simat jati hai, is liye trending analysis short window par chalti hai.
2. **Salary Sample Size:** 640 clean postings 12 roles × 6 cities mein divide hoti hain, isliye sample size small hone se salary model ka MAE moderate hai. Production mein live scraper se mazeed data add karke accuracy mazeed barhai ja sakti hai.

### Troubleshooting:
| Issue | Reason | Fix |
|---|---|---|
| `docker compose` error | Docker Desktop app start nahi thi | Windows Start Menu se **Docker Desktop** open karein, ya script ko chalne dein (auto-fallback SQLite/Local S3 use karega). |
| `JAVA_HOME not set` | PySpark ko Java chahiye | JDK 8/11/17 install karein aur system PATH mein set karein. |
| Dashboard data missing | Pipeline steps execute nahi huye | Steps 1, 2, aur 3 run karein phir dashboard open karein. |
