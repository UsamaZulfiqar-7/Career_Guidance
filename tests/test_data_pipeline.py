"""
Unit and Integration Tests for Data Engineering Pipeline
-------------------------------------------------------
Validates:
1. Object Storage Operations (Upload, Download, Emulated S3 semantics)
2. Data Processing (De-duplication, Text, Role, City, Salary, Skill Normalization)
3. SQL Database Schema & Analytical Queries (PostgreSQL / SQLite)
4. NoSQL Document Loading & Querying (MongoDB / JSON document store)
"""

import os
import shutil
import pytest
import pandas as pd
from pathlib import Path

from core.object_storage import ObjectStorageManager, LocalObjectStorageEmulator
from core.data_processor import DataProcessor
from core.db_manager import DatabaseManager


@pytest.fixture
def sample_raw_df():
    """Returns sample messy job postings data."""
    return pd.DataFrame([
        {
            "Title": "Senior Python Developer",
            "Salary": "PKR. 80,000 - 120,000/Month",
            "Job Type": "Full Time/Permanent",
            "Job Location": "DHA, Lahore, Pakistan",
            "Functional Area": "Software & Web Development",
            "Career Level": "Experienced Professional",
            "Apply Before": "15-Jan-25",
            "Minimum Experience": "3 Years",
            "Minimum Education": "Bachelor",
            "Gender": "No Preference",
            "Age": "NA",
            "Skills": "Python, Django, PostgreSQL, excel, MS Excel, Python"
        },
        {
            # Exact duplicate of the first row
            "Title": "Senior Python Developer",
            "Salary": "PKR. 80,000 - 120,000/Month",
            "Job Type": "Full Time/Permanent",
            "Job Location": "DHA, Lahore, Pakistan",
            "Functional Area": "Software & Web Development",
            "Career Level": "Experienced Professional",
            "Apply Before": "15-Jan-25",
            "Minimum Experience": "3 Years",
            "Minimum Education": "Bachelor",
            "Gender": "No Preference",
            "Age": "NA",
            "Skills": "Python, Django, PostgreSQL, excel, MS Excel, Python"
        },
        {
            "Title": "Sales Executive (Female)",
            "Salary": "PKR. 35,000 - 50,000/Month",
            "Job Type": "Full Time/Permanent",
            "Job Location": "Karachi, Pakistan",
            "Functional Area": "Sales & Business Development",
            "Career Level": "Entry Level",
            "Apply Before": "20-Jan-25",
            "Minimum Experience": "Fresh",
            "Minimum Education": "Intermediate",
            "Gender": "Female",
            "Age": "20-28",
            "Skills": "Communication Skills, Cold Calling, Negotiation Skills, communication"
        }
    ])


class TestObjectStorage:
    def test_local_emulator_upload_and_download(self, tmp_path):
        emulator_dir = tmp_path / "emulated_s3"
        emulator = LocalObjectStorageEmulator(str(emulator_dir))

        test_file = tmp_path / "test_data.csv"
        test_file.write_text("col1,col2\nval1,val2")

        # Upload
        res = emulator.upload_file(str(test_file), "test-bucket", "raw/test.csv")
        assert res["status"] == "SUCCESS"
        assert res["bucket"] == "test-bucket"
        assert res["key"] == "raw/test.csv"

        # Read back
        data = emulator.get_object_bytes("test-bucket", "raw/test.csv")
        assert b"col1,col2" in data

        # List objects
        items = emulator.list_objects("test-bucket")
        assert len(items) == 1
        assert items[0]["key"] == "raw/test.csv"


class TestDataProcessor:
    def test_deduplication(self, sample_raw_df):
        processor = DataProcessor(min_postings_per_role=1, min_postings_per_city=1)
        res = processor.process_raw_dataset(sample_raw_df)
        metrics = res["metrics"]

        # Exact duplicate was dropped
        assert metrics["exact_duplicates_dropped"] == 1
        # Final rows should be 2 unique postings
        assert metrics["final_processed_rows"] == 2

    def test_normalizations(self, sample_raw_df):
        processor = DataProcessor(min_postings_per_role=1, min_postings_per_city=1)
        res = processor.process_raw_dataset(sample_raw_df)
        clean = res["clean_jobs"]

        # 1. Role normalization
        roles = clean["title"].tolist()
        assert "Software / Web Developer" in roles
        assert "Sales & Business Development" in roles

        # 2. City extraction
        cities = clean["city"].tolist()
        assert "Lahore" in cities
        assert "Karachi" in cities

        # 3. Salary parsing
        python_job = clean[clean["title"] == "Software / Web Developer"].iloc[0]
        assert python_job["salary_min_pkr"] == 80000
        assert python_job["salary_max_pkr"] == 120000

        # 4. In-record skill deduplication and canonicalization
        # Input had: "Python, Django, PostgreSQL, excel, MS Excel, Python"
        # Should be deduplicated: Python only once, and excel -> MS Excel
        skills_str = python_job["skills"]
        skills_list = [s.strip() for s in skills_str.split(",")]
        assert skills_list.count("Python") == 1
        assert "MS Excel" in skills_list
        assert "excel" not in skills_list

    def test_dimensional_relational_tables(self, sample_raw_df):
        processor = DataProcessor(min_postings_per_role=1, min_postings_per_city=1)
        res = processor.process_raw_dataset(sample_raw_df)
        tables = res["relational_tables"]

        assert "dim_roles" in tables
        assert "dim_cities" in tables
        assert "dim_skills" in tables
        assert "fact_jobs" in tables
        assert "bridge_job_skills" in tables

        assert len(tables["dim_roles"]) == 2
        assert len(tables["dim_cities"]) == 2
        assert len(tables["fact_jobs"]) == 2
        assert len(tables["bridge_job_skills"]) > 0


class TestDatabaseManager:
    def test_sql_and_nosql_pipeline(self, sample_raw_df, tmp_path):
        processor = DataProcessor(min_postings_per_role=1, min_postings_per_city=1)
        res = processor.process_raw_dataset(sample_raw_df)

        db_path = tmp_path / "test_career.db"
        db = DatabaseManager(sqlite_path=str(db_path), force_sqlite=True)

        # Load SQL
        counts = db.load_relational_data(res["relational_tables"])
        assert counts["fact_jobs"] == 2
        assert counts["dim_roles"] == 2

        # Verify SQL query
        df_roles = db.get_role_distribution()
        assert len(df_roles) == 2
        assert "Software / Web Developer" in df_roles["role"].values

        # Load NoSQL
        nosql_res = db.load_nosql_data(res["nosql_documents"])
        assert nosql_res["document_count"] == 2

        # Query NoSQL
        queried = db.query_nosql({"role": "Software / Web Developer"}, limit=1)
        assert len(queried) == 1
        assert queried[0]["role"] == "Software / Web Developer"
        assert queried[0]["salary"]["avg_pkr"] == 100000
