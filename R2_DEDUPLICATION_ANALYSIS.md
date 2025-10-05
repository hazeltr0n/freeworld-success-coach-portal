# R2 Deduplication Problem Analysis & Solutions

## 🔴 The Problem

**R2 Deduplication Rule:**
```python
r2_key = f"{company}|{market}"  # Same company, same market → Keep ONLY 1 job
```

**What It Does:**
- Zimmerman Transfer, Inc. in Wisconsin → 16 different job postings → **KEEPS ONLY 1**
- Xpress Natural Gas in New York → 12 different jobs → **KEEPS ONLY 1**
- Any company with multiple legitimate positions → **ALL COLLAPSED TO 1**

**The Conflict:**
1. ✅ **Good:** Eliminates spam companies posting 50 identical "CDL Driver" ads
2. ❌ **Bad:** Eliminates legitimate companies with diverse positions:
   - "Milk Hauler - Full Time" (Home daily, $1200-1800/week)
   - "Milk Hauler - Part Time" (Weekends, $150/load)
   - "Cream Hauler" (Different product, different schedule)
   - "Tanker Driver - Limited ELOG" (Different endorsements required)

---

## 📊 Real-World Impact: DriverPulse Example

### Zimmerman Transfer, Inc. (Wisconsin)
**16 legitimate jobs, all different:**

1. Home Daily Milk Hauler - $1200-1800/week
2. Dedicated Milk Hauler - $1500-1600/week
3. Part Time Cream Hauler - $150/load
4. Full Time Milk Hauler - Harlan, IA
5. Milk Hauler (Part Time) - Weekends only
6. Dedicated Tanker Driver (Limited ELOG) - Ag Exempt
7. ... 10 more unique positions

**R2 Result:** Keeps job #1, filters out jobs #2-16 as "duplicates"

**User Experience:** "Why does Zimmerman only have 1 job? I saw 16 on their website!"

---

## 🎯 The Core Tradeoff

### Spam Problem (R2 Solves):
```
Company: "ABC Trucking"
Market: Houston

Posted Jobs:
- "CDL Driver" (same description, URL 1)
- "CDL A Driver" (same description, URL 2)
- "Class A Driver" (same description, URL 3)
- "OTR Driver" (same description, URL 4)
... 20 more identical postings
```

**R2 correctly collapses:** 20 spam ads → 1 job ✅

### Legitimate Diversity Problem (R2 breaks):
```
Company: "Zimmerman Transfer"
Market: Wisconsin

Posted Jobs:
- "Milk Hauler Full Time" ($1800/week, 5 days, tanker)
- "Milk Hauler Part Time" ($150/load, weekends, flexible)
- "Cream Hauler" ($200/load, different product)
- "Dedicated Tanker" (Ag exempt, no ELOG, different routes)
```

**R2 incorrectly collapses:** 4 different jobs → 1 job ❌

---

## 💡 Proposed Solutions

### Option 1: **Job Type Clustering** (Recommended)
**Instead of company+market, use company+market+job_type**

```python
# Extract job type from title
job_type = extract_job_type(title)
# "Milk Hauler Full Time" → "milk_hauler"
# "Cream Hauler" → "cream_hauler"
# "Tanker Driver" → "tanker_driver"
# "CDL Driver" → "cdl_driver"
# "OTR Driver" → "otr_driver"

r2_key = f"{company}|{market}|{job_type}"
```

**Result:**
- ✅ Zimmerman's 3 "Milk Hauler" variations → Keeps best 1
- ✅ Zimmerman's "Cream Hauler" → Separate job (different type)
- ✅ Zimmerman's "Tanker Driver" → Separate job (different type)
- ✅ ABC Trucking's 20 "CDL Driver" spam → Collapses to 1

**Implementation:**
```python
def extract_job_type(title: str) -> str:
    """Extract core job type from title, ignoring modifiers"""
    title_lower = title.lower()

    # Specific product types
    if 'milk' in title_lower and 'haul' in title_lower:
        return 'milk_hauler'
    if 'cream' in title_lower:
        return 'cream_hauler'
    if 'food grade' in title_lower or 'tanker' in title_lower:
        return 'tanker_driver'

    # Route types
    if 'local' in title_lower and 'delivery' in title_lower:
        return 'local_delivery'
    if 'regional' in title_lower:
        return 'regional_driver'
    if 'otr' in title_lower or 'over the road' in title_lower:
        return 'otr_driver'

    # Equipment types
    if 'flatbed' in title_lower:
        return 'flatbed_driver'
    if 'reefer' in title_lower:
        return 'reefer_driver'
    if 'dry van' in title_lower:
        return 'dryvan_driver'

    # Default: generic CDL driver
    return 'cdl_driver'
```

**Pros:**
- ✅ Preserves legitimate job diversity
- ✅ Still collapses spam (20 "CDL Driver" ads → 1)
- ✅ Intelligent grouping based on actual job function

**Cons:**
- ⚠️ Requires good job type extraction logic
- ⚠️ Edge cases where titles are too generic

---

### Option 2: **Salary Range Differentiation**
**If salary ranges differ significantly, keep both**

```python
r2_key_base = f"{company}|{market}"

# Within each R2 group, keep jobs if salary differs by >20%
for group in r2_groups:
    unique_salary_ranges = cluster_by_salary(group, threshold=0.20)
    # Keep one job per salary cluster
```

**Example:**
- Job 1: $1200-1800/week → Keep
- Job 2: $1500-1600/week → **Collapse** (within 20% of Job 1)
- Job 3: $150/load (≈$750/week) → **Keep** (>20% different)

**Pros:**
- ✅ Simple to implement
- ✅ Preserves jobs with genuinely different compensation

**Cons:**
- ⚠️ Doesn't help when salary is missing/similar
- ⚠️ May keep spam if spammers vary salary slightly

---

### Option 3: **Smart Collapse with Best-Job Selection**
**Keep R2, but choose the BEST job from each company**

```python
def select_best_job_from_group(group_df):
    """From R2 duplicates, pick the best one to keep"""

    # Scoring criteria:
    scores = []
    for idx, job in group_df.iterrows():
        score = 0

        # Prefer higher salary
        if job['norm.salary_max']:
            score += job['norm.salary_max'] / 100

        # Prefer jobs with benefits mentioned
        if 'benefits' in job['norm.description'].lower():
            score += 10

        # Prefer jobs with clear requirements (shows legitimacy)
        if '<h3>Requirements</h3>' in job['source.description_raw']:
            score += 5

        # Prefer full-time over part-time
        if 'full time' in job['norm.title'].lower():
            score += 3
        elif 'part time' in job['norm.title'].lower():
            score -= 2

        scores.append((idx, score))

    # Keep highest scoring job
    best_idx = max(scores, key=lambda x: x[1])[0]
    return best_idx
```

**Pros:**
- ✅ Keeps R2 simplicity (company+market)
- ✅ Ensures we show the BEST opportunity from each company
- ✅ User sees highest pay, best benefits

**Cons:**
- ❌ Still loses job diversity (user only sees 1 job per company)
- ⚠️ Doesn't solve "16 jobs → 1 job" problem

---

### Option 4: **R2 Cap Instead of R2 Collapse**
**Allow N jobs per company, not just 1**

```python
r2_dedup_limit = filter_settings.get('r2_dedup_limit', 3)  # Default: keep 3 jobs per company

for group_key, group_df in r2_groups:
    if len(group_df) > r2_dedup_limit:
        # Keep top N, filter the rest
        keep_indices = group_df.index[:r2_dedup_limit]
        dupe_indices = group_df.index[r2_dedup_limit:]

        df.loc[dupe_indices, 'route.final_status'] = f'filtered: R2 limit (company has >{r2_dedup_limit} jobs)'
```

**Example:**
- Zimmerman with 16 jobs → Keep top 3, filter 13
- ABC Trucking with 20 spam ads → Keep top 3, filter 17
- Small company with 2 jobs → Keep both

**Pros:**
- ✅ Balances diversity vs spam
- ✅ Simple to implement (1 line change)
- ✅ Configurable per coach

**Cons:**
- ⚠️ Still arbitrary (why 3? why not 5?)
- ⚠️ Doesn't use intelligence to distinguish spam vs. legitimate

---

### Option 5: **Disable R2, Strengthen R1**
**Rely on R1 (company+title+market) to catch spam**

```python
# R1: company+title+market (exact same job posting)
r1_key = f"{company}|{normalize_title(title)}|{market}"

# R2: DISABLED
r2_dedup = False
```

**Title Normalization:**
```python
def normalize_title(title: str) -> str:
    """Remove minor variations to catch spam"""
    title = title.lower().strip()

    # Remove punctuation
    title = re.sub(r'[^\w\s]', '', title)

    # Normalize common synonyms
    title = title.replace('class a', 'cdl a')
    title = title.replace('tractor trailer', 'semi truck')
    title = title.replace('over the road', 'otr')

    # Remove filler words
    for word in ['driver', 'needed', 'wanted', 'hiring', 'now']:
        title = title.replace(word, '')

    return ' '.join(title.split())  # Normalize whitespace
```

**Example:**
- "CDL Driver" vs "CDL-A Driver" → **Same** (R1 catches it)
- "Milk Hauler" vs "Cream Hauler" → **Different** (both kept)

**Pros:**
- ✅ Preserves all legitimate job diversity
- ✅ Still catches spam with similar titles

**Cons:**
- ⚠️ Spam companies can still post 5-10 different titled ads
- ⚠️ Relies on good title normalization

---

## 🏆 Recommendation: **Hybrid Approach**

Combine Option 1 (Job Type) + Option 4 (Cap):

```python
# Step 1: Extract job type
df['job_type'] = df['norm.title'].apply(extract_job_type)

# Step 2: R2 dedup with job type
r2_key = f"{company}|{market}|{job_type}"

# Step 3: Cap at N jobs per (company+market+job_type)
r2_dedup_limit = 2  # Keep max 2 "Milk Hauler" jobs from same company

for group_key, group_df in r2_groups:
    if len(group_df) > r2_dedup_limit:
        # Sort by quality (salary, benefits, etc.)
        sorted_group = group_df.sort_values(...)
        keep_indices = sorted_group.index[:r2_dedup_limit]
        dupe_indices = sorted_group.index[r2_dedup_limit:]
```

**Result:**
- Zimmerman "Milk Hauler" (16 variations) → Keep top 2
- Zimmerman "Cream Hauler" (1 job) → Keep 1
- Zimmerman "Tanker Driver" (3 jobs) → Keep top 2
- ABC Trucking "CDL Driver" (20 spam) → Keep top 2

**Total:** 6 jobs from Zimmerman (down from 16, up from 1)

---

## 🎯 Immediate Action: Add Toggle

**Quick fix for now:**
```python
# In filter_settings
'r2_dedup_enabled': True,  # Can be disabled per search
'r2_dedup_limit': 3,       # Max jobs per company (0 = unlimited)
'r2_use_job_type': False,  # Use job type clustering (future)
```

**UI in Streamlit:**
```python
r2_enabled = st.checkbox("Enable R2 Deduplication (company+market)", value=True)
if r2_enabled:
    r2_limit = st.slider("Max jobs per company", 0, 10, 3)
    st.caption("0 = unlimited, 3 = keep top 3 jobs per company")
```

This gives coaches control while we build the smarter solution.
