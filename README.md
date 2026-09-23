# Career Guidance Tool — Big Data Analytics Project

Complete A-Z guide:

---

## 1. Problem Statement (Yeh Sabse Pehle Samjho — Sir Yehi Puchein Ge)

**Real Problem:** Pakistan mein har saal lakhon fresh graduates nikalte hain, lekin unhe pata nahi hota ke job market mein **asal mein kya demand hai**. Nateeja: log wo skills seekhte hain jo already saturated hain, ya jo market mein demand hi nahi rakhtin. Career counseling proper tareeqe se available nahi, aur jo hai wo data-driven nahi, sirf generic advice deti hai.

**Why This Matters:** Job postings (Rozee.pk, LinkedIn, Indeed) mein yeh information already maujood hai — kaunsi skills, kaunse roles, kaunsi cities mein demand mein hain — lekin koi is data ko systematically analyze nahi karta.

**Solution:** Real job postings ka data collect karo → Spark se process karo (yeh "Big Data" component hai, kyunke real-world mein lakhon postings hoti hain) → market trends nikalo (top skills, salary patterns) → phir ek **personalized tool** banao jahan student apna target role aur current skills batae, aur system bataye "yeh skills seekh lo, tumhara market match itna %ge hai, expected salary itni hogi".

**Impact:** Yeh generic project nahi hai — yeh directly students/universities/career counselors use kar sakte hain. Real utility hai.

---

## 2. Tech Stack aur Kyun

- **PySpark** — Bulk job postings process karna, skill frequency nikalna (Big Data component)
- **Pandas + Scikit-learn** — Salary prediction model (Random Forest Regressor)
- **Streamlit** — Interactive dashboard jahan student apna data enter kare aur guidance paaye

---

## 3. Folder Structure

```
career_guidance_project/
│
├── data/
│   └── archive.zip                  # Kaggle dataset (RozeePK-Jobs-2024.csv ke andar)
├── core/
│   ├── analytics.py                 # trending/salary helper functions
│   └── recommender.py               # skill gap + salary model functions
├── 01_prepare_real_data.py          # REAL data cleaning (Step A)
├── 02_scraper_template.py           # OPTIONAL: apna live scraper likhne ka template
├── 03_spark_skills_analysis.py      # PySpark analysis (Step B) - CORE Big Data part
├── 04_recommendation_engine.py      # Skill gap + salary model (Step C)
├── 05_dashboard_app.py              # Streamlit dashboard (Step D)
├── requirements.txt
└── README.md
```

---

## 4. Setup

```bash
python -m venv career_env
career_env\Scripts\activate          # Windows
pip install -r requirements.txt
```

Java bhi chahiye hoga PySpark ke liye (JDK 8/11/17). Check: `java -version`

---

## 5. Dataset — Kya Use Ho Raha Hai

Is project mein **synthetic/fake data nahi hai**. Real dataset use ho raha hai:

**Source:** Kaggle — "Pakistan Job Market Dataset (Rozee.pk)", file `RozeePK-Jobs-2024.csv`.

**Raw dataset:** 1059 real job postings, columns: Title, Job Location, Functional Area, Career Level, Minimum Experience, Minimum Education, Job Type, Skills, Salary, Apply Before.

**Important limitation:** Dataset mein **posting date nahi hai**, sirf "Apply Before" (application deadline) hai — is liye Trending Skills analysis is dataset par meaningful result nahi deta (Section 7 mein detail hai).

`data/archive.zip` ko project root ke `data` folder mein rakho — `01_prepare_real_data.py` seedha zip se parh leti hai, extract karne ki zaroorat nahi.

---

## 6. Step-by-Step Execution

### Step A — Real Data Cleaning
```bash
python 01_prepare_real_data.py
```
**Kya karta hai:**
- Raw 1059 postings ko clean karta hai: missing salary/skills/experience wali rows hataata hai
- 700+ messy raw titles (jaise "Sales Executive (Male)") ko keyword-matching se **12 clean roles** mein group karta hai
- Location se city nikalta hai, salary text ("PKR 50,000 - 70,000") ko numbers mein todta hai
- Experience ko Entry/Mid/Senior buckets mein daalta hai

**Output:** `job_postings.csv` — **640 clean postings**, 12 roles, 6 cities, 29 industries.

### Step B — Spark Analysis (CORE Big Data component)
```bash
python 03_spark_skills_analysis.py
```
**Kya karta hai:**
- Job postings load karta hai, `skills` column ko "explode" karta hai (ek job posting jisme 5 skills hain, wo 5 separate rows ban jati hain — yeh Spark ka `explode()` function hai)
- Spark SQL se: overall top skills, role-wise top skills
- Trending skills nikalta hai (last 90 din vs baaki period, daily-rate normalize karke) — **is dataset par yeh reliable nahi hai**, Section 7 dekho
- Average salary by role

### Step C — Recommendation Engine
```bash
python 04_recommendation_engine.py
```
**Kya karta hai:**
- Skill gap analyzer: target role batao, current skills batao, system bataega kya missing hai
- Salary prediction model train karta hai (Random Forest) jo role, city, experience, industry, skill count se salary predict karta hai

### Step D — Dashboard (Final Demo)
```bash
streamlit run 05_dashboard_app.py
```
3 tabs honge:
1. **Market Overview** — top skills, top paying roles
2. **Trending Skills** — dataset ki date-limitation ki wajah se caveat ke saath dikhta hai
3. **My Skill Gap & Salary** — student apna role/skills select kare, personalized guidance paaye

---

## 7. Honest Limitations

Real data use karne ka faida yeh hai ke project asli hai, lekin do cheezein sample-size ki wajah se kamzor hain:

1. **Salary Model ka R² kam (ya negative) hai.** 640 postings 12 roles × 6 cities × 29 industries mein bat jate hain, is liye model ke paas seekhne ko kaafi data nahi hota. Yeh ek real limitation hai, bug nahi.
2. **Trending Skills is dataset par meaningful nahi hai.** Dataset mein posting date nahi, sirf deadline hai, jo sirf ~83 din ke range mein simat jata hai. Isse "recent vs older period" comparison ka koi matlab nahi banta (older period mein data hi nahi bachta).

"Maine real Kaggle dataset use kiya, sample-generated data nahi. Real data ka faida yeh hai ke findings genuine hain, lekin sample size chhota hone ki wajah se salary model aur trending analysis ki accuracy limited hai — real deployment mein zyada data (jaise live scraping se roz naye postings) is masle ko solve karega."

---



## 8. Common Errors

| Error | Fix |
|---|---|
| `JAVA_HOME not set` | JDK install karo |
| `ERROR: dataset nahi mili` (Step A) | `archive.zip` ko `data\archive.zip` par rakho, ya `RozeePK-Jobs-2024.csv` project root mein rakho |
| `Error: job_postings.csv not found` (Step B) | Step A pehle chalao aur uska poora output check karo ke "Saved: job_postings.csv" print hua ho |
| Scraper 403/blocked (`02_scraper_template.py`) | Site bot detection kar rahi hai — headers change karo, delay barhao |
| Dashboard mein purani data | Steps A→B→C dobara chalao is order mein jab bhi naya data daalo |
| Salary prediction error "unseen category" | Dashboard mein wahi role/city/industry select karo jo training data mein tha |

---
