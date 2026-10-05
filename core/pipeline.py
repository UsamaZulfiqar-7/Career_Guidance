"""
Pipeline Orchestrator Module
----------------------------
Complete ETL flow:
Local CSV -> MinIO/S3 -> Python processing -> SQL + MongoDB.

The raw object is write-once by default: if the same object key already
exists, the pipeline does not overwrite it.
"""

import os
import sys
import time
import zipfile
from pathlib import Path
from typing import Dict, Any

from core.object_storage import ObjectStorageManager
from core.data_processor import DataProcessor
from core.db_manager import DatabaseManager


ZIP_CANDIDATES = [Path("data/archive.zip"), Path("archive.zip")]
CSV_CANDIDATES = [Path("data/RozeePK-Jobs-2024.csv"), Path("RozeePK-Jobs-2024.csv")]
DEFAULT_BUCKET = os.getenv("RAW_BUCKET", "career-guidance-raw")
OBJECT_KEY = os.getenv("RAW_OBJECT_KEY", "raw/jobs/RozeePK-Jobs-2024.csv")
REQUIRE_LIVE_OBJECT_STORAGE = os.getenv("REQUIRE_LIVE_OBJECT_STORAGE", "1").lower() not in {
    "0", "false", "no", "off"
}


def locate_local_dataset() -> Path:
    """Locate the raw dataset without modifying it."""
    for path in CSV_CANDIDATES:
        if path.exists():
            return path

    for path in ZIP_CANDIDATES:
        if path.exists():
            with zipfile.ZipFile(path) as archive:
                csv_names = [n for n in archive.namelist() if n.lower().endswith(".csv")]
                if csv_names:
                    extracted_path = Path("RozeePK-Jobs-2024.csv")
                    with archive.open(csv_names[0]) as source, extracted_path.open("wb") as target:
                        target.write(source.read())
                    print(f"[+] Extracted '{csv_names[0]}' from {path} -> {extracted_path}")
                    return extracted_path

    sys.exit(
        "\n[ERROR] Raw dataset not found. Put 'RozeePK-Jobs-2024.csv' in the project "
        "directory or place an archive at 'data/archive.zip'."
    )


def print_banner(title: str) -> None:
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def run_pipeline() -> Dict[str, Any]:
    start_time = time.time()
    print_banner("DATA ENGINEERING ETL PIPELINE EXECUTION")

    # ------------------------------------------------------------------
    # STAGE 0: LOCAL DATASET
    # ------------------------------------------------------------------
    print("\n[Stage 0] Locating Local Storage Dataset...")
    local_file = locate_local_dataset()
    file_size_mb = local_file.stat().st_size / (1024 * 1024)
    print(f" -> Found local file: {local_file.resolve()}")
    print(f" -> File size: {file_size_mb:.2f} MB")

    # ------------------------------------------------------------------
    # STAGE 1: LOCAL -> OBJECT STORAGE
    # ------------------------------------------------------------------
    print_banner("STAGE 1: LOCAL STORAGE -> OBJECT STORAGE (MINIO / S3)")
    obj_manager = ObjectStorageManager()
    status = obj_manager.get_status()

    print(f"[+] Object Storage Backend: {status['backend']}")
    print(f"[+] Endpoint: {status['endpoint']}")

    if REQUIRE_LIVE_OBJECT_STORAGE and not status.get("live_s3", False):
        raise RuntimeError(
            "Live MinIO/S3 is required for this assignment, but it is not reachable. "
            "Start MinIO first, then run the pipeline again. "
            "Set REQUIRE_LIVE_OBJECT_STORAGE=0 only for offline development."
        )

    existing_objects = obj_manager.list_objects(DEFAULT_BUCKET, prefix=OBJECT_KEY)
    exact_existing = [obj for obj in existing_objects if obj.get("key") == OBJECT_KEY]

    if exact_existing:
        existing_size = exact_existing[0].get("size_bytes")
        print(f"[+] Raw object already exists: s3://{DEFAULT_BUCKET}/{OBJECT_KEY}")
        print(f" -> Existing object size: {existing_size:,} bytes")
        print(" -> Write-once protection: SKIPPING overwrite of the raw object.")
        upload_meta = {
            "bucket": DEFAULT_BUCKET,
            "key": OBJECT_KEY,
            "size_bytes": existing_size,
            "backend": status["backend"],
            "status": "EXISTING_RAW_OBJECT_PRESERVED",
        }
    else:
        print(f"[+] Uploading '{local_file.name}' to '{DEFAULT_BUCKET}/{OBJECT_KEY}'...")
        upload_meta = obj_manager.upload_file(
            local_path=str(local_file),
            bucket_name=DEFAULT_BUCKET,
            object_name=OBJECT_KEY,
        )
        print("[+] Upload successful.")
        print(f" -> Bucket: {upload_meta['bucket']}")
        print(f" -> Key: {upload_meta['key']}")
        print(f" -> Size: {upload_meta['size_bytes']:,} bytes")
        print(f" -> ETag: {upload_meta.get('etag', 'N/A')}")

    # ------------------------------------------------------------------
    # STAGE 2: OBJECT STORAGE -> PYTHON STREAM
    # ------------------------------------------------------------------
    print_banner("STAGE 2: OBJECT STORAGE -> PYTHON MEMORY STREAM")
    print(f"[+] Reading '{OBJECT_KEY}' from bucket '{DEFAULT_BUCKET}'...")
    raw_bytes = obj_manager.get_object_bytes(DEFAULT_BUCKET, OBJECT_KEY)
    print(f"[+] Received {len(raw_bytes):,} bytes from object storage.")

    # ------------------------------------------------------------------
    # STAGE 3: PROCESSING
    # ------------------------------------------------------------------
    print_banner("STAGE 3: PYTHON DATA PROCESSING")
    processor = DataProcessor(
        min_salary=10_000,
        max_salary=1_000_000,
        require_salary=True,
        min_postings_per_role=15,
        min_postings_per_city=10,
    )

    results = processor.process_raw_dataset(raw_bytes)
    metrics = results["metrics"]

    print("[+] Data Processing Complete")
    print(f" -> Initial Raw Postings:        {metrics['initial_raw_rows']:,}")
    print(f" -> Exact Duplicates Removed:    {metrics['exact_duplicates_dropped']:,}")
    print(f" -> Semantic Duplicates Removed: {metrics['semantic_duplicates_dropped']:,}")
    print(f" -> Final Valid Postings:        {metrics['final_processed_rows']:,}")
    print(f" -> Standardized Roles:          {metrics['unique_roles']:,}")
    print(f" -> Standardized Cities:         {metrics['unique_cities']:,}")
    print(f" -> Canonical Skills:            {metrics['unique_skills']:,}")
    print(f" -> Job-Skill Associations:      {metrics['total_job_skill_links']:,}")

    # ------------------------------------------------------------------
    # STAGE 4: SQL
    # ------------------------------------------------------------------
    print_banner("STAGE 4: LOAD INTO SQL DATABASE")
    db_manager = DatabaseManager()
    db_status = db_manager.get_status()
    print(f"[+] SQL Engine: {db_status['sql_description']}")
    sql_counts = db_manager.load_relational_data(results["relational_tables"])
    for table_name, count in sql_counts.items():
        print(f" -> {table_name:<20}: {count:>7,} rows")

    # ------------------------------------------------------------------
    # STAGE 5: MONGODB
    # ------------------------------------------------------------------
    print_banner("STAGE 5: LOAD INTO NoSQL DATABASE")
    nosql_result = db_manager.load_nosql_data(results["nosql_documents"])
    print(f"[+] NoSQL Target: {nosql_result['backend']}")
    print(f"[+] Status: {nosql_result['status']}")
    print(f"[+] Documents: {nosql_result['document_count']:,}")

    # ------------------------------------------------------------------
    # STAGE 6: VERIFY
    # ------------------------------------------------------------------
    print_banner("STAGE 6: DATABASE QUERY VERIFICATION")
    role_dist = db_manager.get_role_distribution().head(5)
    print("[+] Top 5 roles:")
    print(role_dist.to_string(index=False))

    top_dev_skills = db_manager.get_top_skills_by_role(
        "Software / Web Developer", limit=5
    )
    print("\n[+] Top developer skills:")
    print(top_dev_skills.to_string(index=False))

    nosql_sample = db_manager.query_nosql({"role": "Software / Web Developer"}, limit=1)
    if nosql_sample:
        sample = nosql_sample[0]
        print("\n[+] MongoDB sample:")
        print(f" -> Job ID: {sample.get('job_id')}")
        print(f" -> Role: {sample.get('role')}")
        print(f" -> City: {sample.get('location', {}).get('city')}")

    # ------------------------------------------------------------------
    # STAGE 7: ANALYTICAL ARTIFACTS FOR SPARK/OPTIONAL EXPORTS
    # ------------------------------------------------------------------
    print_banner("STAGE 7: SYNCHRONIZE ANALYTICAL ARTIFACTS")
    results["clean_jobs"].to_csv("job_postings.csv", index=False)
    results["exploded_skills"].to_csv("job_skills_exploded.csv", index=False)
    print(f"[+] job_postings.csv: {len(results['clean_jobs']):,} records")
    print(f"[+] job_skills_exploded.csv: {len(results['exploded_skills']):,} records")
    print("[!] These CSVs are downstream analytical artifacts only; Streamlit reads the database.")

    elapsed = time.time() - start_time
    print_banner(f"PIPELINE COMPLETED SUCCESSFULLY IN {elapsed:.2f} SECONDS")

    results["pipeline_meta"] = {
        "local_file": str(local_file),
        "bucket": DEFAULT_BUCKET,
        "object_key": OBJECT_KEY,
        "object_storage_backend": status["backend"],
        "raw_object_write_status": upload_meta["status"],
        "elapsed_seconds": round(elapsed, 2),
    }
    return results
