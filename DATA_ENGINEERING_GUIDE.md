# End-to-End Data Engineering Pipeline: Local Storage ➔ Object Storage ➔ DB

Yeh guide Sir ki di hui requirements ko complete A-Z cover karti hai:
> *"Take your data from local storage to object storage and then from object storage to a SQL or NoSQL database using python. For taking your data from object to any other database, you would also have to do data processing (de-duplication, normalisation, or anything other processing your use case may require). For processing in python, you can use any cloud service or you can do your own RND."*

---

## 1. System Architecture Overview

```
                      [ Local Storage ]
               (RozeePK-Jobs-2024.csv / ZIP)
                             │
                             ▼
               [ Stage 1: Ingestion to Object Storage ]
              ObjectStorageManager.upload_file()
                             │
                             ▼
                    [ Object Storage ]
             MinIO (Local S3) / AWS S3 / Emulated
             Bucket: 'career-guidance-raw'
             Key:    'raw/jobs/RozeePK-Jobs-2024.csv'
                             │
                             ▼
               [ Stage 2: Stream from Object Storage ]
              ObjectStorageManager.get_object_bytes()
                             │
                             ▼
               [ Stage 3: Python Data Processing ]
                        DataProcessor
        ┌────────────────────┴────────────────────┐
        ▼                                         ▼
   DE-DUPLICATION                           NORMALIZATION
• Exact Row Duplicates                 • Text & Whitespace Cleanup
• Semantic Composite Duplicates        • 700+ Titles ➔ 12 Standard Roles
• In-record Skill Duplicates           • Location ➔ Standard Pakistani Cities
                                       • Salary String ➔ Min/Max/Avg PKR Numeric
                                       • Experience ➔ Entry/Mid/Senior Tiers
                                       • Skill Synonym Canonicalization
                                       • ISO 8601 Date Parsing (YYYY-MM-DD)
                                       • 3NF Relational & Document Schemas
        └────────────────────┬────────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        ▼                                         ▼
  [ Stage 4: SQL Database ]             [ Stage 5: NoSQL Database ]
 PostgreSQL / SQLite (3NF Schema)          MongoDB / Document Store
• dim_roles                             • Collection: 'job_postings'
• dim_cities                            • Rich embedded subdocuments:
• dim_companies                            - skills: [array]
• dim_skills                               - salary: {min, max, avg, pkr}
• fact_jobs                                - location: {city, country}
• bridge_job_skills (M:N)               • Compound Indexes
• View: vw_job_market_analytics
                             │
                             ▼
               [ Stage 6 & 7: Downstream Analytics ]
• Apache PySpark (explode skills, trending analysis, salary benchmarks)
• Scikit-Learn (Random Forest Salary Predictor)
• Streamlit Dashboard (Interactive Analytics & Database Explorer)
```

---

## 2. Infrastructure & Docker Compose

Project ke `docker-compose.yml` mein industry-standard services configured hain:

| Service | Technology | Port | Purpose |
|---|---|---|---|
| **Object Storage** | MinIO (S3 Compatible) | `9000` (API), `9001` (Web Console) | Raw data storage (Bucket: `career-guidance-raw`) |
| **SQL Database** | PostgreSQL 15 | `5432` | Relational 3NF data warehouse |
| **NoSQL Database** | MongoDB 6 | `27017` | Document-oriented store with embedded schemas |

### Starting Docker Services (Optional):
```bash
docker compose up -d
```
> **Resilient Fallback Feature:** Agar Docker start nahi bhi ho (ya professor ke computer par Docker na ho), Python pipeline **zero errors** ke saath auto-fallback use karti hai:
> - Object Storage fallback: Emulated Local S3 (`storage_emulated/`)
> - SQL Database fallback: SQLite (`career_guidance.db`)
> - NoSQL fallback: JSON Document Store (`nosql_database.json`)

---

## 3. How to Run the Pipeline

### Step 1: Run the Data Engineering Pipeline
```bash
python 01_pipeline_storage_to_db.py
# Ya purana command: python 01_prepare_real_data.py (dono same pipeline run karte hain)
```

**Output will show:**
1. **Local to Object Storage:** File uploaded to MinIO/S3 bucket `career-guidance-raw`.
2. **Object Storage to Python:** In-memory stream download.
3. **Data Processing:**
   - 4 exact duplicates removed.
   - 12 semantic composite key duplicates removed.
   - Text normalized, messy titles categorized into 12 standardized career domains.
   - Pakistani cities extracted, salaries parsed into numeric PKR, skills canonicalized.
4. **Load to SQL Database:** 3NF schema tables created (`dim_roles`, `dim_cities`, `dim_companies`, `dim_skills`, `fact_jobs`, `bridge_job_skills`).
5. **Load to NoSQL Database:** MongoDB `job_postings` collection loaded with embedded subdocuments.
6. **Live Query Verification:** SQL joins and NoSQL queries run automatically.
7. **Downstream Artifact Sync:** `job_postings.csv` and `job_skills_exploded.csv` updated.

### Step 2: Run Spark Big Data Processing
```bash
python 03_spark_skills_analysis.py
```

### Step 3: Train Recommendation & Salary ML Model
```bash
python 04_recommendation_engine.py
```

### Step 4: Launch Modern Dashboard (with Pipeline Explorer)
```bash
streamlit run 05_dashboard_app.py
```
> Dashboard khol kar **Tab 4: "🗄️ Data Engineering & Storage Pipeline"** mein ja kar professor ko live Object Storage status, SQL query runner aur MongoDB documents dikhao!

---

## 4. Run Automated Test Suite
```bash
pytest -v
```
All 14 tests validate:
- Object Storage upload/download/listing.
- Deduplication logic & metrics.
- Normalization (roles, cities, salaries, skills).
- Relational 3NF tables & joins.
- NoSQL document insertion & query.
- Machine learning & Spark analytics.

---

## 5. Viva / Presentation Points (Sir Ko Kya Bolna Hai)

1. **Local Storage to Object Storage:**
   - *"Sir, humne raw Rozee.pk dataset ko local storage se MinIO Object Storage (jo ke industry-standard AWS S3 API follow karta hai) ke bucket `career-guidance-raw` mein ingest kiya."*
2. **Object Storage to Python Streaming:**
   - *"Humne S3 standard `get_object` API use karke raw stream ko direct Python memory buffer mein load kiya, bina disk I/O bottleneck ke."*
3. **Data Processing (De-duplication & Normalization):**
   - **De-duplication:** *"Humne do levels par de-duplication ki — Exact row deduplication aur Semantic composite key deduplication `(Title, Location, Apply Before)` taake reposted jobs filter hon, aur in-record skill list deduplication."*
   - **Normalization:** *"Raw dataset mein 700+ unstructured titles the jinhe regex rule-engine se 12 canonical roles mein normalize kiya, string salaries (`PKR 30,000 - 60,000/Month`) ko min/max/avg numeric fields mein convert kiya, aur skills ko canonical synonyms (`communication skills` -> `Communication`, `ms excel` -> `MS Excel`) par map kiya."*
4. **SQL vs NoSQL Multi-Paradigm Persistence:**
   - **SQL (PostgreSQL / SQLite):** *"Third Normal Form (3NF) relational star schema create kiya: `dim_roles`, `dim_cities`, `dim_skills`, `fact_jobs`, aur many-to-many relationship ke liye `bridge_job_skills`."*
   - **NoSQL (MongoDB):** *"Document store mein embedded hierarchical structure use kiya jahan har job document ke andar uski skills ka array aur location/salary ke subdocuments embedded hain."*
5. **Interactive UI Demonstration:**
   - *"Humne Streamlit dashboard mein Tab 4 integrate kiya hai jahan aap live SQL queries execute karke dekh sakte hain aur live MongoDB documents inspect kar sakte hain."*
