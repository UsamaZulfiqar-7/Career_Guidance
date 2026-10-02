"""
Pipeline Orchestrator Module
----------------------------
Encapsulates the complete end-to-end data pipeline:
Stage 0: Locate Local Dataset
Stage 1: Local Storage -> Object Storage (MinIO / S3)
Stage 2: Object Storage -> Python Stream
Stage 3: Data Processing (Deduplication + Normalization)
Stage 4: Load to SQL (PostgreSQL / SQLite)
Stage 5: Load to NoSQL (MongoDB / JSON Document Store)
Stage 6: Analytical Verification Queries
Stage 7: Synchronize Artifacts for Spark & Streamlit
"""

import sys
import os
import time
import zipfile
from pathlib import Path
from typing import Dict, Any
import pandas as pd

from core.object_storage import ObjectStorageManager
from core.data_processor import DataProcessor
from core.db_manager import DatabaseManager


ZIP_CANDIDATES = [Path("data/archive.zip"), Path("archive.zip")]
CSV_CANDIDATES = [Path("data/RozeePK-Jobs-2024.csv"), Path("RozeePK-Jobs-2024.csv")]
DEFAULT_BUCKET = "career-guidance-raw"
OBJECT_KEY = "raw/jobs/RozeePK-Jobs-2024.csv"


def locate_local_dataset() -> Path:
    """Locates raw dataset on local filesystem."""
    for p in CSV_CANDIDATES:
        if p.exists():
            return p
    for p in ZIP_CANDIDATES:
        if p.exists():
            with zipfile.ZipFile(p) as z:
                csv_names = [n for n in z.namelist() if n.lower().endswith(".csv")]
                if csv_names:
                    extracted_path = Path("RozeePK-Jobs-2024.csv")
                    with z.open(csv_names[0]) as source, open(extracted_path, "wb") as target:
                        target.write(source.read())
                    print(f"[*] Extracted '{csv_names[0]}' from {p} -> {extracted_path}")
                    return extracted_path
    sys.exit(
        "\n[ERROR] Raw dataset not found. Please ensure 'RozeePK-Jobs-2024.csv' "
        "is present in the project directory or 'data/archive.zip' exists."
    )


def print_banner(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def run_pipeline() -> Dict[str, Any]:
    start_time = time.time()
    print_banner("DATA ENGINEERING ETL PIPELINE EXECUTION")

    # ------------------------------------------------------------------
    # STAGE 0: LOCATE LOCAL FILE
    # ------------------------------------------------------------------
    print("\n[Stage 0] Locating Local Storage Dataset...")
    local_file = locate_local_dataset()
    file_size_mb = local_file.stat().st_size / (1024 * 1024)
    print(f"   -> Found local file: {local_file.resolve()}")
    print(f"   -> File size: {file_size_mb:.2f} MB")

    # ------------------------------------------------------------------
    # STAGE 1: LOCAL STORAGE -> OBJECT STORAGE (MinIO / S3)
    # ------------------------------------------------------------------
    print_banner("STAGE 1: LOCAL STORAGE -> OBJECT STORAGE (MinIO / S3)")
    obj_manager = ObjectStorageManager()
    status = obj_manager.get_status()
    print(f"[*] Object Storage Target: {status['backend']}")
    print(f"[*] Endpoint: {status['endpoint']}")
    print(f"[*] Uploading '{local_file.name}' to bucket '{DEFAULT_BUCKET}' as '{OBJECT_KEY}'...")

    upload_meta = obj_manager.upload_file(
        local_path=str(local_file),
        bucket_name=DEFAULT_BUCKET,
        object_name=OBJECT_KEY
    )
    print("   [+] Upload Successful!")
    print(f"   -> Bucket:   {upload_meta['bucket']}")
    print(f"   -> Key:      {upload_meta['key']}")
    print(f"   -> Size:     {upload_meta['size_bytes']:,} bytes")
    print(f"   -> Backend:  {upload_meta['backend']}")
    print(f"   -> ETag:     {upload_meta.get('etag', 'N/A')}")

    # ------------------------------------------------------------------
    # STAGE 2: OBJECT STORAGE -> PYTHON MEMORY STREAM
    # ------------------------------------------------------------------
    print_banner("STAGE 2: OBJECT STORAGE -> PYTHON STREAM")
    print(f"[*] Streaming object '{OBJECT_KEY}' from bucket '{DEFAULT_BUCKET}' into Python...")
    raw_bytes = obj_manager.get_object_bytes(DEFAULT_BUCKET, OBJECT_KEY)
    print(f"   [+] Successfully received stream: {len(raw_bytes):,} bytes loaded into memory.")

    # ------------------------------------------------------------------
    # STAGE 3: DATA PROCESSING (DE-DUPLICATION & NORMALIZATION)
    # ------------------------------------------------------------------
    print_banner("STAGE 3: PYTHON DATA PROCESSING (DEDUPLICATION & NORMALIZATION)")
    processor = DataProcessor(
        min_salary=10_000,
        max_salary=1_000_000,
        require_salary=True,
        min_postings_per_role=15,
        min_postings_per_city=10
    )
    print("[*] Processing raw dataset stream...")
    results = processor.process_raw_dataset(raw_bytes)
    metrics = results["metrics"]

    print("   [+] Data Processing Complete! Metrics summary:")
    print(f"   -> Initial Raw Postings:           {metrics['initial_raw_rows']:,}")
    print(f"   -> Exact Duplicates Removed:       {metrics['exact_duplicates_dropped']:,}")
    print(f"   -> Semantic Duplicates Removed:    {metrics['semantic_duplicates_dropped']:,}")
    print(f"   -> Final Valid Postings:           {metrics['final_processed_rows']:,}")
    print(f"   -> Standardized Career Roles:      {metrics['unique_roles']}")
    print(f"   -> Standardized Cities:            {metrics['unique_cities']}")
    print(f"   -> Canonical Skills Identified:    {metrics['unique_skills']:,}")
    print(f"   -> Total Job-Skill Associations:   {metrics['total_job_skill_links']:,}")

    # ------------------------------------------------------------------
    # STAGE 4: LOAD TO SQL DATABASE (PostgreSQL / SQLite)
    # ------------------------------------------------------------------
    print_banner("STAGE 4: LOAD INTO SQL DATABASE (Relational 3NF Schema)")
    db_manager = DatabaseManager()
    db_status = db_manager.get_status()
    print(f"[*] SQL Engine: {db_status['sql_description']}")
    print("[*] Creating 3NF Tables: dim_roles, dim_cities, dim_companies, dim_skills, fact_jobs, bridge_job_skills...")

    sql_counts = db_manager.load_relational_data(results["relational_tables"])
    print("   [+] SQL Tables Loaded Successfully:")
    for tbl, cnt in sql_counts.items():
        print(f"       * {tbl:<20}: {cnt:>6,} rows")

    # ------------------------------------------------------------------
    # STAGE 5: LOAD TO NoSQL DATABASE (MongoDB / Document Store)
    # ------------------------------------------------------------------
    print_banner("STAGE 5: LOAD INTO NoSQL DATABASE (Document Collections)")
    nosql_result = db_manager.load_nosql_data(results["nosql_documents"])
    print(f"[*] NoSQL Target: {nosql_result['backend']}")
    print(f"[*] Status:       {nosql_result['status']}")
    print(f"[*] Documents:    {nosql_result['document_count']:,} postings with embedded skills & salary documents")

    # ------------------------------------------------------------------
    # STAGE 6: VERIFY WITH LIVE ANALYTICAL QUERIES
    # ------------------------------------------------------------------
    print_banner("STAGE 6: DATABASE QUERY VERIFICATION")
    print("[*] Query 1: Top 5 Career Roles by Market Demand (SQL Join query)")
    role_dist = db_manager.get_role_distribution().head(5)
    print(role_dist.to_string(index=False))

    print("\n[*] Query 2: Top In-Demand Skills for 'Software / Web Developer' (Bridge Table Join)")
    top_dev_skills = db_manager.get_top_skills_by_role("Software / Web Developer", limit=5)
    print(top_dev_skills.to_string(index=False))

    print("\n[*] Query 3: NoSQL Document Sample Query (MongoDB / Document format)")
    nosql_sample = db_manager.query_nosql({"role": "Software / Web Developer"}, limit=1)
    if nosql_sample:
        s = nosql_sample[0]
        print(f"   -> Job ID:        {s.get('job_id')}")
        print(f"   -> Role:          {s.get('role')} | City: {s.get('location', {}).get('city')}")
        print(f"   -> Salary (Avg):  PKR {s.get('salary', {}).get('avg_pkr', 0):,}/month")
        print(f"   -> Skills:        {', '.join(s.get('skills', [])[:5])}...")

    # ------------------------------------------------------------------
    # STAGE 7: SYNCHRONIZE ARTIFACTS FOR DOWNSTREAM SPARK & DASHBOARD
    # ------------------------------------------------------------------
    print_banner("STAGE 7: SYNCHRONIZE ARTIFACTS FOR SPARK & STREAMLIT")
    clean_jobs_path = Path("job_postings.csv")
    results["clean_jobs"].to_csv(clean_jobs_path, index=False)
    print(f"[+] Synchronized '{clean_jobs_path}' ({len(results['clean_jobs'])} records)")

    skills_exploded_path = Path("job_skills_exploded.csv")
    results["exploded_skills"].to_csv(skills_exploded_path, index=False)
    print(f"[+] Synchronized '{skills_exploded_path}' ({len(results['exploded_skills'])} records)")

    elapsed = time.time() - start_time
    print_banner(f"PIPELINE COMPLETED SUCCESSFULLY IN {elapsed:.2f} SECONDS")
    return results
