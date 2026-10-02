"""
========================================================================================
END-TO-END DATA ENGINEERING PIPELINE: LOCAL STORAGE -> OBJECT STORAGE -> DB
========================================================================================
Requirements Fulfilled:
1. Local Storage -> Object Storage (MinIO / S3 bucket: 'career-guidance-raw')
2. Object Storage -> Python Memory Stream
3. Data Processing (De-duplication, Text/Role/City/Salary/Skill Normalization, 3NF modeling)
4. Processed Data -> SQL Relational Database (PostgreSQL / SQLite)
5. Processed Data -> NoSQL Document Database (MongoDB / Document Store)
6. Analytics Synchronization -> job_postings.csv & job_skills_exploded.csv for Spark & UI

Run with:
    python 01_pipeline_storage_to_db.py
========================================================================================
"""

from core.pipeline import run_pipeline

if __name__ == "__main__":
    run_pipeline()
