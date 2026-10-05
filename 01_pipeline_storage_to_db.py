"""
END-TO-END DATA ENGINEERING PIPELINE

Local Storage -> MinIO Object Storage -> Python Processing -> SQL + MongoDB

Run:
    python 01_pipeline_storage_to_db.py
"""

from core.pipeline import run_pipeline


if __name__ == "__main__":
    run_pipeline()
