"""
STEP 2 (OPTIONAL BUT IMPRESSIVE): Real Data Collection Template
--------------------------------------------------------------------
Agar aap REAL Pakistani job market data use karna chahte ho (instructor ko
zyada impress karega kyunke yeh LOCAL, LIVE data hai), yeh template use karo.

NOTE: Yeh script is sandbox mein NAHI chalega (network restricted hai).
Ise apne LAPTOP par chalana, jahan internet available hai.

IMPORTANT ETHICS/LEGAL NOTE:
- Sirf PUBLIC job listing pages scrape karo (jo bina login dikhti hain)
- robots.txt respect karo (site ka /robots.txt check karo pehle)
- Requests ke beech delay rakho (server par load na dalo)
- Yeh sirf EDUCATIONAL/RESEARCH purpose ke liye hai

Install: pip install requests beautifulsoup4
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def scrape_rozee_jobs(search_term="data analyst", max_pages=3):
    """
    Template for scraping Rozee.pk public job search results.
    You WILL need to inspect the actual page HTML structure yourself
    (right-click -> Inspect on the job listing page) because site
    layouts change over time - this is a STARTING STRUCTURE.
    """
    all_jobs = []

    for page in range(1, max_pages + 1):
        url = f"https://www.rozee.pk/job/jsearch/q/{search_term}/fpn/{page}"
        print(f"Fetching page {page}: {url}")

        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching page {page}: {e}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        # NOTE: These CSS selectors are EXAMPLES - inspect the real page
        # and update them to match actual class names / tags
        job_cards = soup.find_all("div", class_="job")  # <-- update selector

        for card in job_cards:
            try:
                title = card.find("h3").get_text(strip=True) if card.find("h3") else None
                company = card.find("div", class_="cname").get_text(strip=True) if card.find("div", class_="cname") else None
                city = card.find("div", class_="city").get_text(strip=True) if card.find("div", class_="city") else None

                all_jobs.append({
                    "title": title,
                    "company": company,
                    "city": city,
                })
            except AttributeError:
                continue

        time.sleep(random.uniform(2, 4))  # be polite, don't hammer the server

    return pd.DataFrame(all_jobs)


if __name__ == "__main__":
    # Example usage - adjust search terms to roles you're interested in
    search_terms = ["data-analyst", "software-engineer", "digital-marketing"]
    all_results = []

    for term in search_terms:
        df = scrape_rozee_jobs(search_term=term, max_pages=2)
        all_results.append(df)

    final_df = pd.concat(all_results, ignore_index=True)
    final_df.to_csv("scraped_job_postings_raw.csv", index=False)
    print(f"\nScraped {len(final_df)} job postings")
    print("IMPORTANT: You'll need to manually add a 'skills' column by parsing")
    print("job descriptions with keyword matching (see skills extraction note below)")

"""
SKILLS EXTRACTION FROM JOB DESCRIPTIONS (if you scrape full descriptions):
------------------------------------------------------------------------------
If your scraper captures the FULL job description text, extract skills like this:

SKILL_KEYWORDS = ["Python", "SQL", "Excel", "Power BI", "Java", "React", ...]

def extract_skills(description_text):
    found = []
    for skill in SKILL_KEYWORDS:
        if skill.lower() in description_text.lower():
            found.append(skill)
    return ", ".join(found)

df["skills"] = df["description"].apply(extract_skills)

This turns unstructured text into the structured "skills" column that the
rest of this project's pipeline (Steps 3-5) expects.
"""
