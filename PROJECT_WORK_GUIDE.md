# 📘 Career Guidance Project — Complete Project & Work Manual

> **Yeh file project ki mukammal tafseel (A to Z) bayan karti hai:**
> 1. Is project mein kya kya implement hua hai.
> 2. Data local storage se Object Storage, aur Object Storage se SQL/NoSQL Database tak kaise flow hota hai.
> 3. De-duplication aur Normalization kaise kaam karti hai.
> 4. Spark, Machine Learning aur Streamlit Dashboard ka kya role hai.
> 5. Har file ka maqsad kya hai.
> 6. Step-by-step kaise run karna hai.
> 7. Sir ke saamne viva/presentation mein kya bolna hai.

---

## 📑 Table of Contents
1. [Project Ka Asal Maqsad (Problem & Solution)](#1-project-ka-asal-maqsad)
2. [A to Z Architecture & Data Flow](#2-a-to-z-architecture--data-flow)
3. [Sir Ki Requirements Kaise Poori Huin](#3-sir-ki-requirements-kaise-poori-huin)
4. [File-by-File Explanation (Har File Ka Kaam)](#4-file-by-file-explanation)
5. [Step-by-Step Run Karne Ka Tareeqa](#5-step-by-step-run-karne-ka-tareeqa)
6. [Sir Ke Saamne Viva / Presentation Q&A](#6-sir-ke-saamne-viva--presentation-qa)

---

## 1. Project Ka Asal Maqsad

### Asal Masla (Problem Statement):
Pakistan mein har saal hazaron fresh graduates nikalte hain, lekin unhein pata nahi hota ke job market mein asal demand kis skill ki hai. Nateeja yeh nikalta hai ke students aisi skills seekhte hain jo ya to saturate ho chuki hain ya market mein unka scope kam hai. Generic career counseling data-driven nahi hoti.

### Hamara Solution:
Humne Pakistan ke real job portal (**Rozee.pk 2024 Kaggle dataset**) ka real data lia aur ek **Complete Data Engineering & Analytics Pipeline** banai:
1. **Raw Ingestion:** Local storage se raw data ko **MinIO Object Storage (S3)** mein daala.
2. **Python Stream Processing:** Object storage se data stream karke **De-duplication** aur **Normalization** ki.
3. **Multi-Paradigm Database Storage:** Data ko **SQL (PostgreSQL / SQLite 3NF Schema)** aur **NoSQL (MongoDB)** dono mein persist kiya.
4. **Big Data Processing:** **Apache PySpark** se distributed level par skills explode kar ke top skills aur role salaries calculate keen.
5. **Machine Learning:** **Scikit-Learn (Random Forest)** se expected salary prediction aur Skill Gap Analysis model train kiya.
6. **Interactive Dashboard:** **Streamlit** modern UI banaya jahan student apni target role aur skills select karke guidance le sakta hai, aur Sir live **Data Engineering & Storage Pipeline** inspect kar sakte hain.

---

## 2. A to Z Architecture & Data Flow

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

## 3. Sir Ki Requirements Kaise Poori Huin

### Requirement 1: "Take your data from local storage to object storage"
- **Code:** `core/object_storage.py` & `01_pipeline_storage_to_db.py`
- **Kaise kiya:** Python ka `boto3` client use karke raw CSV file ko local storage se MinIO (S3-compatible Object Storage) ke bucket `career-guidance-raw` mein upload kiya.
- **Smart Fallback:** Agar Docker/MinIO start na ho, to code crash nahi hota balki `storage_emulated/` mein S3 semantics ke sath local emulation karta hai.

### Requirement 2: "And then from object storage to a SQL or NoSQL database using python"
- **Code:** `core/db_manager.py` & `01_pipeline_storage_to_db.py`
- **Kaise kiya:** Object storage se bytes buffer stream karke data process hua, phir:
  - **SQL:** Relational Data Warehouse mein 3NF normalized tables (`dim_roles`, `dim_cities`, `dim_skills`, `fact_jobs`, `bridge_job_skills`) create karke load kiya. (PostgreSQL container aur SQLite zero-config fallback).
  - **NoSQL:** MongoDB collection `job_postings` mein rich document format (nested arrays aur embedded objects) ke sath insert kiya.

### Requirement 3: "You would also have to do data processing (de-duplication, normalisation, or anything other processing)"
- **Code:** `core/data_processor.py`
- **De-duplication (Do levels par):**
  1. *Exact Row Deduplication:* Pori row identical hone par drop kiya.
  2. *Semantic Composite Deduplication:* `(Title, Job Location, Apply Before, Functional Area)` ke combination par reposted duplicate jobs ko drop kiya.
  3. *In-Record Skill Deduplication:* Ek hi job posting ke andar agar multiple times skill repeat ho rahi thi (e.g. `['Excel', 'MS Excel', 'Excel']`), usko deduplicate kiya.
- **Normalization:**
  1. *Title ➔ Standard Role Mapping:* 700+ raw noisy titles (jaise "Senior Python Full Stack Engineer") ko regex rules se 12 core career domains mein map kiya.
  2. *City Extraction:* Messy Pakistani addresses (e.g. "Johar Town, Lahore, Pakistan") se clean city name "Lahore" extract kiya.
  3. *Salary Parsing:* Unstructured text `"PKR. 30,000 - 60,000/Month"` ko numeric columns `salary_min_pkr`, `salary_max_pkr`, aur `salary_avg_pkr` mein convert kiya aur outliers filter kiye.
  4. *Experience Bucketing:* Minimum experience ko standard tiers (`Entry Level (0-1 yrs)`, `Mid Level (2-4 yrs)`, `Senior Level (5+ yrs)`) mein categorize kiya.
  5. *Skill Synonym Canonicalization:* Har skill ke different spellings ko ek canonical name dia (e.g., `communication skills` ➔ `Communication`, `ms excel` ➔ `MS Excel`).
  6. *Date Normalization:* Deadlines ko standard ISO 8601 (`YYYY-MM-DD`) format mein convert kiya.

---

## 4. File-by-File Explanation

| File Path | Description |
|---|---|
| `docker-compose.yml` | Multi-container setup: **MinIO** (port 9000/9001), **PostgreSQL** (port 5432), aur **MongoDB** (port 27017). |
| `core/object_storage.py` | Object Storage Manager class jo MinIO, AWS S3, aur Local Emulated S3 ko transparently handle karti hai. |
| `core/data_processor.py` | Data Engineering core class jo de-duplication, field normalizations, 3NF schema tables aur NoSQL documents banati hai. |
| `core/db_manager.py` | SQL (PostgreSQL & SQLite) aur NoSQL (MongoDB & JSON store) connection, schema creation, bulk insertion aur analytical query methods. |
| `core/pipeline.py` | Master ETL pipeline orchestrator jo saare 7 stages ko step-by-step run karta hai. |
| `01_pipeline_storage_to_db.py` | Main script jo Local ➔ Object Storage ➔ Processing ➔ SQL/NoSQL pipeline execute karta hai. |
| `01_prepare_real_data.py` | Backward-compatible script (jo internally `core.pipeline` ko call karti hai). |
| `03_spark_skills_analysis.py` | Apache PySpark script jo Big Data distributed processing use karke skills explode karti hai aur role salaries compute karti hai. |
| `04_recommendation_engine.py` | Scikit-Learn Random Forest Regressor train karti hai aur personalized skill gap analyzer execute karti hai. |
| `05_dashboard_app.py` | Streamlit interactive web application jisme **Tab 4 (Data Engineering & Storage Explorer)** shamil hai. |
| `tests/test_data_pipeline.py` | Pytest automated test suite jo Object Storage, Deduplication, Normalization, SQL aur NoSQL ko verify karti hai. |

---

## 5. Step-by-Step Run Karne Ka Tareeqa

Windows terminal (PowerShell / Command Prompt) mein project folder ke andar:

### Step 0: Virtual Environment Activate Karein
```powershell
career_env\Scripts\activate
```

### Step 1: (Optional) Docker Services Start Karein
Agar aapke paas Docker Desktop chal raha hai:
```powershell
docker compose up -d
```
*(Agar Docker na ho to koi masla nahi, code auto-fallback mode mein baghair kisi error ke chalega).*

### Step 2: Data Engineering Pipeline Run Karein
```powershell
career_env\Scripts\python.exe 01_pipeline_storage_to_db.py
```
Yeh script:
- Raw file ko Object Storage mein ingest karegi.
- Object Storage se stream download karegi.
- De-duplication aur Normalization karegi.
- SQL aur NoSQL databases load karegi.
- Live verification queries execute karegi.
- Spark aur Dashboard ke liye clean artifacts sync karegi.

### Step 3: Spark Big Data Analysis Run Karein
```powershell
career_env\Scripts\python.exe 03_spark_skills_analysis.py
```
Yeh script PySpark ke through skills explode karegi aur top in-demand skills aur role salary benchmarks generate karegi.

### Step 4: Machine Learning Recommendation Engine Run Karein
```powershell
career_env\Scripts\python.exe 04_recommendation_engine.py
```
Yeh script Random Forest model train karegi aur `salary_model.pkl` save karegi.

### Step 5: Interactive Web Dashboard Kholein
```powershell
career_env\Scripts\streamlit.exe run 05_dashboard_app.py
```
Browser mein `http://localhost:8501` khulega:
- **Tab 1: Market Overview** (Top skills, salaries by role).
- **Tab 2: Trending Skills** (Growth rates).
- **Tab 3: My Skill Gap & Salary** (Personalized guidance).
- **Tab 4: 🗄️ Data Engineering & Storage Pipeline** (Live Object Storage status, Live SQL Query Console, Live MongoDB Document Explorer).

### Step 6: Automated Tests Run Karein
```powershell
career_env\Scripts\pytest.exe -v
```
Tamam **14 ke 14 unit tests pass** hotay hain!

---

## 6. Sir Ke Saamne Viva / Presentation Q&A

### Q1: "Aapne direct CSV database mein kyun nahi daali? Object Storage kyun use kiya?"
**Answer:**
> *"Sir, modern big data architecture mein raw data ko direct database mein daalna anti-pattern samjha jata hai. Industry standard yeh hai ke pehle raw files ko ek centralized Object Storage (Data Lake / S3) mein rakha jata hai taake raw copy hamesha intact rahe. Phir downstream ETL pipelines us raw lake se data stream karke clean karti hain aur target databases mein load karti hain."*

### Q2: "Aapne De-duplication kaise ki?"
**Answer:**
> *"Sir, humne do distinct levels par de-duplication ki:*
> 1. **Exact Duplicate Removal:** Agar pori row 100% duplicate ho to usko drop kiya.
> 2. **Semantic Composite Key Removal:** Job portals par log aksar wohi job thode din baad dobara post kar dete hain. Humne `(Title, Job Location, Apply Before, Functional Area)` ki composite key par check lagaya taake duplicate postings filter ho sakein.
> 3. **In-Record Skill Deduplication:** Ek hi posting ke andar repeat hone wali skills ko bhi deduplicate kiya."*

### Q3: "SQL aur NoSQL dono kyun use kiye? Dono mein kya farq hai?"
**Answer:**
> *"Sir, humne polyglot persistence (multi-paradigm) demonstrate kiya:*
> - **SQL (Relational):** Third Normal Form (3NF) relational star schema banaya (`fact_jobs`, `dim_roles`, `dim_cities`, `dim_skills`, aur many-to-many ke liye `bridge_job_skills`). Yeh analytical queries aur joins ke liye best hai.
> - **NoSQL (MongoDB):** Document-oriented store use kiya jisme har job posting ek JSON document hai jisme skills ka array aur location/salary ke subdocuments embedded hain. Yeh fast read aur API serving ke liye ideal hai."*

### Q4: "Chhote dataset par PySpark use karne ka kya faida?"
**Answer:**
> *"Sir, PySpark distributed computing engine hai. Hamara code modular Spark transformations (jaise `explode()`, `groupBy()`, Spark SQL) par likha gaya hai. Iska matlab hai ke chahe dataset mein 1,000 rows hon ya 10 million rows hon, hamara Spark code bina kisi modification ke poore cluster par parallel run ho sakta hai."*

### Q5: "Aapke project ki limitations kya hain?"
**Answer:**
> *"Sir, real Kaggle dataset use karne ki wajah se do limitations aati hain:*
> 1. Dataset mein posting date nahi thi, sirf 'Apply Before' deadline thi jo ~83 din ke chhotay span mein simat jati hai, is liye trending analysis short window par chalti hai.
> 2. 640 clean postings 12 roles × 6 cities mein divide hoti hain, isliye sample size small hone se salary model ka MAE moderate hai. Future scope mein live scraper se mazeed data add karke accuracy barhai ja sakti hai."*
