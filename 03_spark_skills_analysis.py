"""
STEP 3: Big Data Analysis with PySpark
------------------------------------------
This is the CORE "Big Data" component of your project.

We take raw job postings (which in real life could be millions of rows
scraped over months from multiple job sites) and use Spark to:
1. Explode the "skills" column (one job posting -> multiple skill rows)
2. Find most in-demand skills overall, by role, by city
3. Find TRENDING skills (comparing recent months vs older months)
4. Analyze salary vs skills/experience
5. Save processed results for the dashboard/recommender

Run: python3 03_spark_skills_analysis.py
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = (
    SparkSession.builder.appName("CareerGuidance-SkillsAnalysis")
    .config("spark.driver.memory", "2g")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")

print("Spark session started. Version:", spark.version)

# ---- 1. Load data ----
df = spark.read.csv("job_postings.csv", header=True, inferSchema=True)
df = df.withColumn("date_posted", F.to_date("date_posted"))
print(f"\nTotal job postings loaded: {df.count()}")

df.createOrReplaceTempView("jobs")

# ---- 2. Explode skills: one row per (job, skill) pair ----
# "Python, SQL, Excel" -> 3 separate rows, one per skill
df_skills = df.withColumn("skill", F.explode(F.split(F.trim(F.col("skills")), ",\\s*")))
df_skills.createOrReplaceTempView("job_skills")

print(f"Total (job, skill) pairs after exploding: {df_skills.count()}")

# ---- 3. Overall Top In-Demand Skills ----
print("\n--- TOP 15 MOST IN-DEMAND SKILLS (OVERALL) ---")
top_skills = spark.sql("""
    SELECT skill, COUNT(*) as demand_count,
           ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM jobs), 2) as pct_of_all_jobs
    FROM job_skills
    GROUP BY skill
    ORDER BY demand_count DESC
    LIMIT 15
""")
top_skills.show(truncate=False)

# ---- 4. Top Skills by Role ----
print("\n--- TOP SKILLS FOR 'Data Analyst' ROLE (example) ---")
spark.sql("""
    SELECT skill, COUNT(*) as demand_count
    FROM job_skills
    WHERE title = 'Data Analyst'
    GROUP BY skill
    ORDER BY demand_count DESC
    LIMIT 10
""").show(truncate=False)

# ---- 5. Top Skills by City ----
print("\n--- TOP SKILLS IN 'Faisalabad' (example) ---")
spark.sql("""
    SELECT skill, COUNT(*) as demand_count
    FROM job_skills
    WHERE city = 'Faisalabad'
    GROUP BY skill
    ORDER BY demand_count DESC
    LIMIT 10
""").show(truncate=False)

# ---- 6. Trending Skills: last 3 months vs prior period ----
print("\n--- TRENDING SKILLS (Last 3 Months vs Rest of Year) ---")
max_date = df.agg(F.max("date_posted")).collect()[0][0]
recent_cutoff = max_date - F.expr("INTERVAL 90 DAYS")

# IMPORTANT: recent window (90 days) and older window (rest of year, ~275 days)
# have different lengths, so we normalize to a DAILY RATE before comparing -
# otherwise the longer "older" window would always look bigger, which is misleading.
trending = spark.sql(f"""
    WITH recent AS (
        SELECT skill, COUNT(*) / 90.0 as recent_rate
        FROM job_skills
        WHERE date_posted >= DATE_SUB('{max_date}', 90)
        GROUP BY skill
    ),
    older AS (
        SELECT skill, COUNT(*) / 275.0 as older_rate
        FROM job_skills
        WHERE date_posted < DATE_SUB('{max_date}', 90)
        GROUP BY skill
    )
    SELECT r.skill,
           ROUND(r.recent_rate * 90, 0) as recent_count,
           ROUND(COALESCE(o.older_rate, 0) * 275, 0) as older_count,
           ROUND((r.recent_rate - COALESCE(o.older_rate, 0.01)) * 100.0 / COALESCE(o.older_rate, 0.01), 1) as growth_pct
    FROM recent r
    LEFT JOIN older o ON r.skill = o.skill
    WHERE r.recent_rate * 90 > 15
    ORDER BY growth_pct DESC
    LIMIT 10
""")
trending.show(truncate=False)

# ---- 7. Average Salary by Role ----
print("\n--- AVERAGE SALARY BY ROLE (PKR) ---")
spark.sql("""
    SELECT title,
           ROUND(AVG((salary_min_pkr + salary_max_pkr) / 2), 0) as avg_salary_pkr,
           COUNT(*) as num_postings
    FROM jobs
    GROUP BY title
    ORDER BY avg_salary_pkr DESC
""").show(20, truncate=False)

# ---- 8. Save processed outputs for dashboard/recommender ----
df_skills.toPandas().to_csv("job_skills_exploded.csv", index=False)
top_skills.toPandas().to_csv("top_skills_overall.csv", index=False)

print("\nSaved: job_skills_exploded.csv, top_skills_overall.csv")

spark.stop()
print("Done. Spark session stopped.")
