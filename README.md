# Career Guidance Tool — Big Data Analytics Project

Complete A-Z guide: problem se lekar final presentation tak.

---

## 1. Problem Statement (Yeh Sabse Pehle Samjho — Sir Yehi Puchein Ge)

**Real Problem:** Pakistan mein har saal lakhon fresh graduates nikalte hain, lekin unhe pata nahi hota ke job market mein **asal mein kya demand hai**. Nateeja: log wo skills seekhte hain jo already saturated hain, ya jo market mein demand hi nahi rakhtin. Career counseling proper tareeqe se available nahi, aur jo hai wo data-driven nahi, sirf generic advice deti hai.

**Why This Matters:** Job postings (Rozee.pk, LinkedIn, Indeed) mein yeh information already maujood hai — kaunsi skills, kaunse roles, kaunsi cities mein demand mein hain — lekin koi is data ko systematically analyze nahi karta.

**Solution:** Bulk job postings ka data collect karo → Spark se process karo (yeh "Big Data" component hai, kyunke real-world mein lakhon postings hoti hain) → market trends nikalo (top skills, trending skills, salary patterns) → phir ek **personalized tool** banao jahan student apna target role aur current skills batae, aur system exact bataye "yeh skills seekh lo, tumhara market match itna %ge hai, expected salary itni hogi".

**Impact:** Yeh generic project nahi hai — yeh directly students/universities/career counselors use kar sakte hain. Real utility hai.

---

## 2. Tech Stack aur Kyun

- **PySpark** — Bulk job postings process karna, skill frequency nikalna, trend analysis (Big Data component)
- **Pandas + Scikit-learn** — Salary prediction model (Random Forest Regressor)
- **Streamlit** — Interactive dashboard jahan student apna data enter kare aur guidance paaye

---

## 3. Folder Structure

```
career_guidance_project/
│
├── 01_generate_sample_data.py       # Testing data (Step A)
├── 02_scraper_template.py           # OPTIONAL: real data scraping template
├── 03_spark_skills_analysis.py      # PySpark analysis (Step B) - CORE Big Data part
├── 04_recommendation_engine.py      # Skill gap + salary model (Step C)
├── 05_dashboard_app.py              # Streamlit dashboard (Step D)
├── requirements.txt
└── README.md
```

---

## 4. Setup

```bash
python3 -m venv career_env
source career_env/bin/activate       # Windows: career_env\Scripts\activate
pip install -r requirements.txt
```

Java bhi chahiye hoga PySpark ke liye (JDK 8/11/17). Check: `java -version`

---

## 5. REAL DATA — Yeh Zaroor Karo (Sample Data Sirf Testing Ke Liye Hai)

Maine `01_generate_sample_data.py` di hai jisse pipeline turant test ho sakta hai. Lekin **final submission ke liye real data use karo**:

### Option A (Easiest): Kaggle Dataset
Search karo Kaggle par:
- "LinkedIn Job Postings" (2023-2024 wala dataset, thousands of real postings)
- "Data Science Job Postings"
- "Naukri.com Job Postings" (South Asian job market ke liye relevant)

Download karke columns ko match karo is structure se: `title, company, city, industry, experience_level, skills, salary_min_pkr, salary_max_pkr, date_posted`

### Option B (Zyada Impressive): Khud Scrape Karo
`02_scraper_template.py` mein starting template diya hai jo Rozee.pk jaisi sites se public job listings nikal sakta hai. **Yeh apne laptop par chalana** (sandbox mein internet nahi hai). Isme aapko:
1. Actual page ko browser mein khol kar "Inspect Element" karna hoga
2. CSS selectors (class names) ko update karna hoga apni actual site ke hisaab se
3. Job description se skills nikalne ke liye keyword matching use karna hoga (script mein example diya hai)

**Yeh option behtar hai kyunke:** Real, live, LOCAL Pakistani job market data — instructor ko bohot impress karega ke aapne khud data collect kiya, sirf Kaggle se download nahi kiya.

---

## 6. Step-by-Step Execution

### Step A — Sample data (ya apna real data isi naam se save karo: `job_postings.csv`)
```bash
python3 01_generate_sample_data.py
```

### Step B — Spark Analysis (CORE Big Data component)
```bash
python3 03_spark_skills_analysis.py
```
**Kya karta hai:**
- Job postings load karta hai, `skills` column ko "explode" karta hai (ek job posting jisme 5 skills hain, wo 5 separate rows ban jati hain — yeh Spark ka `explode()` function hai)
- Spark SQL se: overall top skills, role-wise top skills, city-wise top skills
- **Trending skills** nikalta hai (last 90 din vs baaki saal, daily-rate normalize karke — yeh important hai warna comparison galat hoga)
- Average salary by role

### Step C — Recommendation Engine
```bash
python3 04_recommendation_engine.py
```
**Kya karta hai:**
- Skill gap analyzer: target role batao, current skills batao, system bataega kya missing hai
- Salary prediction model train karta hai (Random Forest) jo role, city, experience, skill count se salary predict karta hai

### Step D — Dashboard (Final Demo)
```bash
streamlit run 05_dashboard_app.py
```
3 tabs honge:
1. **Market Overview** — top skills, top paying roles
2. **Trending Skills** — kya grow kar raha hai (AI tools, cloud, etc.)
3. **My Skill Gap & Salary** — student apna role/skills select kare, personalized guidance paaye

---

## 7. Presentation Mein Kya Bolna Hai (Sir Ko Impress Karne Ke Liye)

1. **Problem se start karo** — generic "I made a data project" mat bolo. Bolo: "Fresh graduates ko pata nahi hota kya seekhein, is wajah se galat skills seekh kar time waste karte hain. Maine is problem ko data se solve karne ki koshish ki."
2. **Data source explain karo** — kahan se aya, kitna bara hai, real-world mein kitna bara ho sakta hai (lakhon postings)
3. **Big Data justification** — "Ek job portal roz hazaron postings receive karta hai. Manually analyze karna impossible hai, isliye Spark ka distributed processing use kiya"
4. **Live demo karo** — dashboard khol kar khud apna role/skills daal kar dikhao
5. **Trending skills ka insight highlight karo** — yeh sabse "wow" wala part hai: "Dekhein, AI tools ki demand 100%+ badhi hai pichle 3 mahinon mein"
6. **Limitations aur future scope bolo** — "Abhi sample/limited data hai, real deployment mein live scraping pipeline chalegi jo daily naye postings add karegi"

---

## 8. Common Errors

| Error | Fix |
|---|---|
| `JAVA_HOME not set` | JDK install karo |
| Scraper 403/blocked | Site bot detection kar rahi hai — headers change karo, delay barhao, ya Kaggle dataset use karo |
| Dashboard mein purani data | Steps A→B→C dobara chalao is order mein jab bhi naya data daalo |
| Salary prediction error "unseen category" | Dashboard mein wahi role/city/industry select karo jo training data mein tha |

---

