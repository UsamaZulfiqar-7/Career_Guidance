"""
Database Manager Module (SQL & NoSQL)
--------------------------------------
Provides enterprise-grade persistence across:
1. SQL Relational Database:
   - PostgreSQL (Production / Docker container)
   - SQLite (Local zero-config embedded SQL database fallback)
   - 3NF Relational Star Schema (dim_roles, dim_cities, dim_companies, dim_skills, fact_jobs, bridge_job_skills)
   - Analytical View (vw_job_market_analytics)
2. NoSQL Document Database:
   - MongoDB (Docker container on port 27017)
   - JSON Document Store (Zero-config local NoSQL persistence fallback)
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from sqlalchemy import (
    create_engine, text, MetaData, Table, Column, Integer, String, Date, ForeignKey, Index
)
from sqlalchemy.orm import declarative_base

try:
    import pymongo
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False


Base = declarative_base()


class DatabaseManager:
    """
    Manages both SQL and NoSQL persistence with resilient fallback adapters.
    """

    def __init__(
        self,
        postgres_url: Optional[str] = None,
        sqlite_path: str = "career_guidance.db",
        mongo_url: Optional[str] = None,
        mongo_db_name: str = "career_guidance",
        force_sqlite: bool = False
    ):
        self.postgres_url = postgres_url or os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgrespassword@localhost:5432/career_guidance"
        )
        self.sqlite_path = sqlite_path
        self.mongo_url = mongo_url or os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.mongo_db_name = mongo_db_name
        self.force_sqlite = force_sqlite

        self.sql_engine = None
        self.sql_dialect = "sqlite"
        self.sql_description = ""

        self.mongo_client = None
        self.mongo_db = None
        self.is_mongo_live = False
        self.nosql_description = ""

        self._init_sql_connection()
        self._init_nosql_connection()

    # ------------------------------------------------------------------
    # SQL CONNECTION
    # ------------------------------------------------------------------
    def _is_host_reachable(self, host: str, port: int, timeout: float = 0.5) -> bool:
        import socket
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except Exception:
            return False

    def _init_sql_connection(self):
        if not self.force_sqlite:
            # Quick socket test for Postgres host & port
            host = "localhost"
            port = 5432
            if "@" in self.postgres_url:
                try:
                    after_at = self.postgres_url.split("@")[-1].split("/")[0]
                    if ":" in after_at:
                        host, port_str = after_at.split(":")
                        port = int(port_str)
                    else:
                        host = after_at
                except Exception:
                    pass

            if self._is_host_reachable(host, port, timeout=0.5):
                try:
                    engine = create_engine(self.postgres_url, pool_pre_ping=True, connect_args={"connect_timeout": 2})
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    self.sql_engine = engine
                    self.sql_dialect = "postgresql"
                    self.sql_description = f"PostgreSQL Live ({host}:{port})"
                    return
                except Exception:
                    pass

        # Fallback to SQLite
        db_file = Path(self.sqlite_path).resolve()
        self.sql_engine = create_engine(f"sqlite:///{db_file}")
        self.sql_dialect = "sqlite"
        self.sql_description = f"SQLite Embedded Database ({db_file.name})"

    # ------------------------------------------------------------------
    # NoSQL CONNECTION
    # ------------------------------------------------------------------
    def _init_nosql_connection(self):
        if PYMONGO_AVAILABLE:
            host = "localhost"
            port = 27017
            try:
                clean_url = self.mongo_url.replace("mongodb://", "")
                if "@" in clean_url:
                    clean_url = clean_url.split("@")[-1]
                clean_url = clean_url.split("/")[0]
                if ":" in clean_url:
                    host, port_str = clean_url.split(":")
                    port = int(port_str)
                else:
                    host = clean_url
            except Exception:
                pass

            if self._is_host_reachable(host, port, timeout=0.5):
                try:
                    client = pymongo.MongoClient(self.mongo_url, serverSelectionTimeoutMS=1000)
                    client.admin.command("ping")
                    self.mongo_client = client
                    self.mongo_db = client[self.mongo_db_name]
                    self.is_mongo_live = True
                    self.nosql_description = f"MongoDB Live ({host}:{port})"
                    return
                except Exception:
                    self.mongo_client = None
                    self.mongo_db = None
                    self.is_mongo_live = False

        self.nosql_description = "JSON Document Store (NoSQL Local Emulation)"

    # ------------------------------------------------------------------
    # SQL SCHEMA INITIALIZATION & LOADING
    # ------------------------------------------------------------------
    def create_sql_schema(self):
        """
        Creates normalized relational schema (3NF) with primary keys,
        foreign keys, indices, and analytical views.
        """
        metadata = MetaData()

        # dim_roles
        Table(
            "dim_roles", metadata,
            Column("role_id", Integer, primary_key=True),
            Column("role_name", String(100), nullable=False, unique=True),
        )

        # dim_cities
        Table(
            "dim_cities", metadata,
            Column("city_id", Integer, primary_key=True),
            Column("city_name", String(100), nullable=False, unique=True),
        )

        # dim_companies
        Table(
            "dim_companies", metadata,
            Column("company_id", Integer, primary_key=True),
            Column("company_name", String(150), nullable=False),
        )

        # dim_skills
        Table(
            "dim_skills", metadata,
            Column("skill_id", Integer, primary_key=True),
            Column("skill_name", String(100), nullable=False, unique=True),
        )

        # fact_jobs
        Table(
            "fact_jobs", metadata,
            Column("job_id", String(30), primary_key=True),
            Column("original_title", String(250)),
            Column("role_id", Integer, ForeignKey("dim_roles.role_id")),
            Column("city_id", Integer, ForeignKey("dim_cities.city_id")),
            Column("company_id", Integer, ForeignKey("dim_companies.company_id")),
            Column("experience_level", String(50)),
            Column("salary_min_pkr", Integer),
            Column("salary_max_pkr", Integer),
            Column("salary_avg_pkr", Integer),
            Column("date_posted", String(20)),
            Column("job_type", String(50)),
            Column("min_education", String(100)),
            Column("industry", String(100)),
        )

        # bridge_job_skills
        Table(
            "bridge_job_skills", metadata,
            Column("job_id", String(30), ForeignKey("fact_jobs.job_id"), primary_key=True),
            Column("skill_id", Integer, ForeignKey("dim_skills.skill_id"), primary_key=True),
        )

        # Drop and create tables
        metadata.drop_all(self.sql_engine)
        metadata.create_all(self.sql_engine)

        # Create Analytical View
        view_sql = """
        CREATE VIEW IF NOT EXISTS vw_job_market_analytics AS
        SELECT
            j.job_id,
            j.original_title,
            r.role_name AS role,
            c.city_name AS city,
            co.company_name AS company,
            j.industry,
            j.experience_level,
            j.salary_min_pkr,
            j.salary_max_pkr,
            j.salary_avg_pkr,
            j.date_posted,
            s.skill_name AS skill
        FROM fact_jobs j
        LEFT JOIN dim_roles r ON j.role_id = r.role_id
        LEFT JOIN dim_cities c ON j.city_id = c.city_id
        LEFT JOIN dim_companies co ON j.company_id = co.company_id
        LEFT JOIN bridge_job_skills js ON j.job_id = js.job_id
        LEFT JOIN dim_skills s ON js.skill_id = s.skill_id;
        """
        if self.sql_dialect == "sqlite":
            with self.sql_engine.connect() as conn:
                conn.execute(text(view_sql))
                conn.commit()
        elif self.sql_dialect == "postgresql":
            with self.sql_engine.connect() as conn:
                conn.execute(text("DROP VIEW IF EXISTS vw_job_market_analytics CASCADE;"))
                conn.execute(text(view_sql.replace("IF NOT EXISTS ", "")))
                conn.commit()

    def load_relational_data(self, relational_tables: Dict[str, pd.DataFrame]) -> Dict[str, int]:
        """
        Loads normalized DataFrames into SQL tables.
        """
        self.create_sql_schema()
        counts = {}

        # Insert order matters for foreign keys:
        # 1. Dimensions
        for tname in ["dim_roles", "dim_cities", "dim_companies", "dim_skills"]:
            df = relational_tables[tname]
            df.to_sql(tname, self.sql_engine, if_exists="append", index=False)
            counts[tname] = len(df)

        # 2. Fact
        fact_df = relational_tables["fact_jobs"]
        fact_df.to_sql("fact_jobs", self.sql_engine, if_exists="append", index=False)
        counts["fact_jobs"] = len(fact_df)

        # 3. Bridge
        bridge_df = relational_tables["bridge_job_skills"]
        bridge_df.to_sql("bridge_job_skills", self.sql_engine, if_exists="append", index=False)
        counts["bridge_job_skills"] = len(bridge_df)

        return counts

    # ------------------------------------------------------------------
    # NoSQL LOADING
    # ------------------------------------------------------------------
    def load_nosql_data(self, nosql_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Loads documents into MongoDB collection or JSON Document Store fallback.
        """
        doc_count = len(nosql_documents)

        if self.is_mongo_live and self.mongo_db is not None:
            coll = self.mongo_db["job_postings"]
            coll.drop()
            # Insert documents
            coll.insert_many(nosql_documents)
            # Create indexes
            coll.create_index([("role", pymongo.ASCENDING), ("location.city", pymongo.ASCENDING)])
            coll.create_index([("skills", pymongo.ASCENDING)])
            coll.create_index([("date_posted", pymongo.DESCENDING)])
            return {
                "backend": self.nosql_description,
                "collection": "job_postings",
                "document_count": doc_count,
                "status": "INSERTED_LIVE_MONGODB"
            }

        # Fallback to local JSON document store
        json_path = Path("nosql_database.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({"collection": "job_postings", "count": doc_count, "documents": nosql_documents}, f, indent=2)

        return {
            "backend": self.nosql_description,
            "path": str(json_path),
            "document_count": doc_count,
            "status": "SAVED_LOCAL_DOCUMENT_STORE"
        }

    # ------------------------------------------------------------------
    # ANALYTICAL QUERY INTERFACE
    # ------------------------------------------------------------------
    def execute_sql_query(self, query: str) -> pd.DataFrame:
        with self.sql_engine.connect() as conn:
            return pd.read_sql_query(text(query), conn)

    def get_role_distribution(self) -> pd.DataFrame:
        query = """
        SELECT r.role_name AS role, COUNT(j.job_id) AS total_jobs,
               ROUND(AVG(j.salary_avg_pkr), 0) AS avg_salary_pkr
        FROM fact_jobs j
        JOIN dim_roles r ON j.role_id = r.role_id
        GROUP BY r.role_name
        ORDER BY total_jobs DESC;
        """
        return self.execute_sql_query(query)

    def get_top_skills_by_role(self, role_name: Optional[str] = None, limit: int = 10) -> pd.DataFrame:
        if role_name:
            query = f"""
            SELECT s.skill_name AS skill, COUNT(*) AS posting_count
            FROM bridge_job_skills js
            JOIN fact_jobs j ON js.job_id = j.job_id
            JOIN dim_roles r ON j.role_id = r.role_id
            JOIN dim_skills s ON js.skill_id = s.skill_id
            WHERE r.role_name = '{role_name}'
            GROUP BY s.skill_name
            ORDER BY posting_count DESC
            LIMIT {limit};
            """
        else:
            query = f"""
            SELECT s.skill_name AS skill, COUNT(*) AS posting_count
            FROM bridge_job_skills js
            JOIN dim_skills s ON js.skill_id = s.skill_id
            GROUP BY s.skill_name
            ORDER BY posting_count DESC
            LIMIT {limit};
            """
        return self.execute_sql_query(query)

    def query_nosql(self, filter_dict: Optional[Dict[str, Any]] = None, limit: int = 10) -> List[Dict[str, Any]]:
        filter_dict = filter_dict or {}
        if self.is_mongo_live and self.mongo_db is not None:
            coll = self.mongo_db["job_postings"]
            return list(coll.find(filter_dict, {"_id": 0}).limit(limit))

        # Read from local JSON document store
        json_path = Path("nosql_database.json")
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                docs = data.get("documents", [])
                # Simple filtering
                filtered = []
                for doc in docs:
                    match = True
                    for k, v in filter_dict.items():
                        if doc.get(k) != v:
                            match = False
                            break
                    if match:
                        filtered.append(doc)
                    if len(filtered) >= limit:
                        break
                return filtered
        return []

    def get_status(self) -> Dict[str, Any]:
        return {
            "sql_dialect": self.sql_dialect,
            "sql_description": self.sql_description,
            "is_mongo_live": self.is_mongo_live,
            "nosql_description": self.nosql_description,
        }
