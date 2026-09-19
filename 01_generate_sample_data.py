"""
STEP 1: Generate Sample Job Postings Dataset (for testing/development)
--------------------------------------------------------------------------
NOTE: ACTUAL project, real data ki 2 option shain:-

OPTION A - Real dataset from Kaggle (EASIEST, recommended):
   - "LinkedIn Job Postings 2023-2024" - https://www.kaggle.com/datasets/arshkon/linkedin-job-postings
   - "Data Analyst / Data Scientist Jobs" datasets - search "job postings" on Kaggle
   - Just rename columns to match this structure: title, company, city, industry,
     experience_level, skills, salary_min, salary_max, date_posted

OPTION B - Scrape real Pakistani job sites yourself (see 02_scraper_template.py)
   - Rozee.pk, Indeed Pakistan, Mustakbil.com have public job listings
   - More impressive to instructor because it's LOCAL, real-time data

This script creates SYNTHETIC data with realistic role-skill-salary relationships
so you can build/test your entire pipeline immediately.
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

np.random.seed(42)
random.seed(42)

# ---- Define realistic job roles and their typical required skills ----
ROLE_SKILLS = {
    "Data Scientist": ["Python", "SQL", "Machine Learning", "Deep Learning", "Statistics",
                        "Pandas", "TensorFlow", "Data Visualization", "R"],
    "Data Analyst": ["SQL", "Excel", "Power BI", "Tableau", "Python", "Data Visualization",
                      "Statistics", "Communication"],
    "Software Engineer": ["Java", "Python", "C++", "Git", "SQL", "Data Structures",
                           "System Design", "REST APIs"],
    "Frontend Developer": ["JavaScript", "React", "HTML", "CSS", "TypeScript", "Git",
                            "Figma", "Responsive Design"],
    "Backend Developer": ["Node.js", "Python", "Java", "SQL", "MongoDB", "REST APIs",
                           "Docker", "Git"],
    "Full Stack Developer": ["JavaScript", "React", "Node.js", "SQL", "MongoDB", "Git",
                              "HTML", "CSS", "REST APIs"],
    "DevOps Engineer": ["Docker", "Kubernetes", "AWS", "CI/CD", "Linux", "Git",
                         "Jenkins", "Terraform"],
    "Machine Learning Engineer": ["Python", "TensorFlow", "PyTorch", "Machine Learning",
                                   "Deep Learning", "AWS", "Docker", "SQL"],
    "Mobile App Developer": ["Flutter", "Android", "Kotlin", "Swift", "Java", "Git",
                              "REST APIs", "Firebase"],
    "QA Engineer": ["Manual Testing", "Automation Testing", "Selenium", "Python",
                     "Java", "SQL", "Agile", "Test Cases"],
    "Digital Marketing Specialist": ["SEO", "Google Ads", "Social Media Marketing",
                                      "Content Writing", "Google Analytics", "Email Marketing"],
    "Graphic Designer": ["Adobe Photoshop", "Illustrator", "Figma", "Canva",
                          "UI/UX", "Branding"],
    "UI/UX Designer": ["Figma", "Adobe XD", "UI/UX", "Wireframing", "User Research",
                        "Prototyping"],
    "Network Engineer": ["Networking", "CCNA", "Linux", "Cisco", "Firewalls",
                          "Network Security"],
    "Cybersecurity Analyst": ["Network Security", "Penetration Testing", "SIEM",
                               "Linux", "Firewalls", "Cybersecurity Frameworks"],
    "Project Manager": ["Agile", "Scrum", "Communication", "JIRA", "Risk Management",
                         "Stakeholder Management"],
    "Business Analyst": ["SQL", "Excel", "Communication", "Requirement Gathering",
                          "Power BI", "Agile"],
    "HR Executive": ["Recruitment", "Communication", "HR Policies", "Payroll",
                      "Employee Relations"],
    "Accountant": ["QuickBooks", "Excel", "Financial Reporting", "Taxation", "SAP"],
    "Sales Executive": ["Communication", "Negotiation", "CRM", "Lead Generation",
                         "Customer Relationship Management"],
}

CITIES = ["Lahore", "Karachi", "Islamabad", "Faisalabad", "Rawalpindi", "Multan", "Peshawar"]
CITY_WEIGHTS = [0.28, 0.30, 0.15, 0.08, 0.07, 0.06, 0.06]  # bigger cities = more jobs

INDUSTRIES = ["IT/Software", "Banking/Finance", "E-commerce", "Telecom",
              "Manufacturing", "Education", "Healthcare", "Marketing/Media"]

EXPERIENCE_LEVELS = ["Entry Level (0-1 yrs)", "Mid Level (2-4 yrs)", "Senior Level (5+ yrs)"]

COMPANIES = ["Netsol Technologies", "Systems Limited", "Techlogix", "Arbisoft",
             "10Pearls", "Folio3", "Devsinc", "Contour Software", "Careem",
             "Daraz", "TRG Pakistan", "Bank Alfalah IT", "Jazz", "Telenor",
             "NayaTel", "Confiz", "Xavor", "VentureDive", "KeepTruckin",
             "Bitrix24 Pakistan"]

def generate_postings(n):
    rows = []
    roles = list(ROLE_SKILLS.keys())
    start_date = datetime(2024, 9, 1)

    for i in range(n):
        role = random.choice(roles)
        possible_skills = ROLE_SKILLS[role]
        # pick a realistic subset of skills for this specific posting (not always all)
        num_skills = random.randint(max(3, len(possible_skills) - 4), len(possible_skills))
        skills = random.sample(possible_skills, min(num_skills, len(possible_skills)))

        experience = random.choices(EXPERIENCE_LEVELS, weights=[0.4, 0.4, 0.2])[0]
        city = random.choices(CITIES, weights=CITY_WEIGHTS)[0]
        industry = random.choice(INDUSTRIES)
        company = random.choice(COMPANIES)

        # pick how far into the year this posting is (0 = start_date, 365 = one year later)
        day_offset = random.randint(0, 365)

        # simulate a REAL trend: AI-related skills become more common as the year goes on
        # (this mimics the real-world rise of AI tool demand in job postings)
        ai_skill_probability = 0.03 + (day_offset / 365) * 0.35  # ~3% early -> ~38% late in year
        if random.random() < ai_skill_probability:
            bonus_skills = ["ChatGPT/LLM Tools", "Generative AI", "Prompt Engineering"]
            skills.append(random.choice(bonus_skills))
        # Cloud Computing grows moderately over the year too
        if random.random() < (0.05 + (day_offset / 365) * 0.15):
            skills.append("Cloud Computing")

        # salary depends on role seniority + number of skills (rough realistic simulation, in PKR)
        base_salary = {
            "Entry Level (0-1 yrs)": 45000,
            "Mid Level (2-4 yrs)": 100000,
            "Senior Level (5+ yrs)": 220000,
        }[experience]
        tech_roles = ["Data Scientist", "Machine Learning Engineer", "DevOps Engineer", "Software Engineer"]
        role_multiplier = 1.3 if role in tech_roles else 1.0
        salary_min = int(base_salary * role_multiplier * random.uniform(0.85, 1.0))
        salary_max = int(salary_min * random.uniform(1.2, 1.6))

        date_posted = start_date + timedelta(days=day_offset)

        rows.append({
            "job_id": f"JOB{i+1:05d}",
            "title": role,
            "company": company,
            "city": city,
            "industry": industry,
            "experience_level": experience,
            "skills": ", ".join(skills),
            "salary_min_pkr": salary_min,
            "salary_max_pkr": salary_max,
            "date_posted": date_posted.strftime("%Y-%m-%d"),
        })

    return pd.DataFrame(rows)

df = generate_postings(8000)
df.to_csv("job_postings.csv", index=False)

print(f"Sample dataset created: job_postings.csv")
print(f"Total postings: {len(df)}")
print(f"Unique roles: {df['title'].nunique()}")
print(f"Unique cities: {df['city'].nunique()}")
print(f"Date range: {df['date_posted'].min()} to {df['date_posted'].max()}")
print("\nSample rows:")
print(df.head())
