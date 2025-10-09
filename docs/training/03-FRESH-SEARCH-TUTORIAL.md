# Fresh Search Tutorial (Indeed/Outscraper)

**Complete Step-by-Step Guide for API-Powered Job Searches**

---

## 🎯 What Is a Fresh Search?

A Fresh Search pulls jobs directly from job board APIs (Indeed, Google Jobs, Outscraper) and runs them through the full 8-stage Opptek pipeline:

1. **Ingestion** - Fetch jobs from API
2. **Normalization** - Map to 100+ field schema
3. **Business Rules** - Quality filtering
4. **Deduplication** - Remove duplicates
5. **AI Classification** - Good/so-so/bad ratings
6. **Routing** - Final selection
7. **Link Tracking** - Generate Short.io links
8. **Data Storage** - Save to Supabase cache

---

## ✅ Benefits of Fresh Searches

- **Latest job postings** - Jobs posted in last 24-48 hours
- **Comprehensive coverage** - Not limited to cache
- **Populates memory** - Future Memory-Only searches benefit
- **AI classification** - Fresh jobs get rated by AI
- **Full tracking** - Short.io portal links generated
- **Market expansion** - Discover jobs in new markets

---

## ⚠️ Important Considerations

### API Costs
- **Indeed**: ~$0.10-0.15 per 100 jobs
- **Outscraper**: Varies by plan
- **Google Jobs**: 99% cheaper than Indeed (if you have access)

### Processing Time
- **Indeed Fresh**: 45-90 seconds for 100 jobs
- **Memory-Only**: 3-10 seconds

### Budget Management
- Check your **Monthly Budget** in Admin Panel
- Track spending in Coach Analytics
- Balance Fresh searches (weekly) with Memory-Only (daily)

---

## 💡 When to Use Fresh Searches

### ✅ Perfect For:
- **Weekly market updates** - Refresh cache every Monday
- **New markets** - First search in a new city/state
- **VIP agents** - Important clients deserve latest postings
- **Comprehensive searches** - Need 500-1000 jobs
- **Market research** - Analyzing hiring trends

### ❌ Not Ideal For:
- **Daily agent updates** - Use Memory-Only (zero cost)
- **High-frequency testing** - Use Memory-Only
- **End of month** - Preserve budget with Memory-Only
- **Quick link regeneration** - Use Memory-Only

---

## 📋 Prerequisites

Before running a Fresh Search, ensure:

1. **You have `can_pull_fresh_jobs` permission**
   - Check with admin if you see "Permission denied"

2. **Budget remaining** for the month
   - Check Coach Analytics or Admin Panel

3. **Free Agent info ready** (name, preferences)

4. **Good understanding** of Memory-Only searches
   - Complete that tutorial first

---

## 🚀 Step-by-Step Tutorial

### Step 1: Navigate to Job Search Tab

1. Log in to Opptek
2. Click **🔍 Job Search** tab at top

---

### Step 2: Configure Location

**Same as Memory-Only tutorial:**

1. Location dropdown: Select **"Select Market"**
2. Choose **Dallas-Fort Worth** from market dropdown

💡 **Tip**: Start with a high-volume market (Dallas, Houston, Atlanta) to see robust results.

---

### Step 3: Set Search Mode

**Important: Search mode affects API costs!**

**Search Mode dropdown:**
- **Quick Test (25 jobs)** - $0.02-0.03 cost, testing only
- **Sample (100 jobs)** - $0.10-0.15 cost, **recommended for this tutorial**
- **Medium (500 jobs)** - $0.50-0.75 cost, comprehensive weekly search
- **Full (1000 jobs)** - $1.00-1.50 cost, requires admin permission

💡 **For this tutorial**: Select **"Sample (100 jobs)"**.

---

### Step 4: Configure Search Parameters

**Same as Memory-Only:**

- **Search Terms**: `CDL driver` (or customize)
- **Search Radius**: `50 miles`
- **Classifier Type**: `CDL Traditional`

**Additional Fresh Search Consideration:**

**Exact Location Mode** (checkbox):
- ⬜ **Unchecked** (default): Indeed will expand radius if needed for 100 jobs
- ✅ **Checked**: Strict location boundary (may return fewer jobs)

💡 **Leave unchecked** for first Fresh search - you want full coverage.

---

### Step 5: Configure Portal Settings

**Same as Memory-Only tutorial:**

- **Max Jobs for PDF**: `20`
- **Route Type Filter**: Both ✅ Local and ✅ Regional/OTR
- **Match Quality Filter**: ✅ good, ✅ so-so (leave bad unchecked)
- **Fair Chance Only**: ⬜ (or ✅ if needed)
- **Show HTML Preview**: ✅ **Check this**
- **Generate Portal Link**: ✅ **Check this**
- **Show "Prepared For"**: ✅ **Check this**
- **Enable PDF Generation**: ⬜ (leave unchecked)

---

### Step 6: Enter Free Agent Info

**Same as Memory-Only:**

Use **Airtable Search** or **Manual Entry** to specify agent.

For this tutorial:
- **Free Agent Name**: "Sarah Johnson"
- **Agent UUID**: (leave blank or fill from Airtable)
- Click **✅ Use Manual Entry**

---

### Step 7: Set Memory Time Period

**Memory Time Period dropdown:**
- Select **"7 days"** (standard)

💡 **Note**: Fresh Search will ALSO check memory first to avoid re-scraping recent jobs. The "7 days" setting tells it: "Don't re-scrape jobs I already have from the last 7 days."

---

### Step 8: Review Fresh Search Button

**Locate the button:**

### **🔍 Indeed Fresh Only**

💡 **What will happen when you click**:
1. Indeed API scrape (45-90 seconds)
2. AI classification (GPT-4o-mini)
3. Deduplication (remove duplicates)
4. Portal link generation (Short.io)
5. Supabase storage (cache for future Memory searches)

**Cost estimate for 100 jobs**: $0.10-0.15

---

### Step 9: Run Fresh Search ⚠️

**Click the button:**

### **🔍 Indeed Fresh Only**

✅ You should see:

**Stage 1: Ingestion**
```
🔍 Searching Indeed API...
Requesting 100 jobs for Dallas-Fort Worth...
```

⏱️ **Wait 20-30 seconds** (Indeed API call)

---

**Stage 2-3: Normalization & Rules**
```
📋 Normalizing 97 jobs to canonical schema...
✅ Normalized 97 jobs

⚖️ Applying business rules...
✅ 89 jobs pass quality filters
```

---

**Stage 4: Deduplication**
```
🔍 Checking for duplicates...
✅ Removed 12 duplicates (77 unique jobs remain)
```

---

**Stage 5: AI Classification**
```
🤖 Classifying jobs with OpenAI GPT-4o-mini...
Progress: [████████░░] 80% (62/77 jobs classified)
```

⏱️ **Wait 30-45 seconds** (AI classification is the slowest stage)

---

**Stage 6-7: Routing & Tracking**
```
✅ AI Classification complete: 77 jobs classified

🎯 Applying routing logic...
✅ 62 quality jobs selected for portal

🔗 Generating Short.io tracked links...
✅ 62 tracked links generated
```

---

**Stage 8: Storage**
```
💾 Uploading to Supabase...
✅ 62 jobs uploaded to database
✅ Cache populated for future Memory-Only searches
```

---

### Total processing time: 60-90 seconds

---

## 📊 Step 10: Review Fresh Search Results

### Search Summary Section

You'll see:
```
Fresh Search Results for Dallas-Fort Worth
Search Terms: CDL driver | Radius: 50 miles | Classifier: CDL Traditional

Total Jobs: 77
Quality Jobs (good/so-so): 62
Good: 43 | So-So: 19 | Bad: 15

Memory Jobs: 25 | Fresh Jobs: 52
✅ 52 new jobs added to cache!
```

💡 **Key insights**:
- **Fresh Jobs: 52** - Brand new jobs found by Indeed API
- **Memory Jobs: 25** - Jobs already in cache (within 7 days), not re-scraped
- **Total: 77** - Combined pool
- **Quality rate: 80.5%** - Excellent filtering

---

### Quality Metrics (4-Column Display)

**Review these metrics:**
- **Total Jobs**: 77
- **Quality Jobs**: 62 (80.5% quality rate ✅)
- **Quality Rate**: 80.5%
- **Top Route**: Local (38 jobs)

💡 **Good quality rate** for Fresh Search: 60-85%

💡 **Lower than expected?** - Try adjusting search terms or expanding radius.

---

### Route Distribution (Bar Chart)

**Check the mix:**
- Local: 38 jobs
- Regional: 14 jobs
- OTR: 25 jobs

💡 **Local jobs dominate in Dallas** - typical for urban markets.

---

## 🖥️ Step 11: Review HTML Preview

**Same as Memory-Only tutorial:**

Scroll down to **HTML Preview** section.

**What you should see:**
- Clean phone-screen mockup
- Portal header: "Prepared by Coach [Your Name] for Sarah Johnson"
- Job cards (up to 20 jobs):
  - Company, title, location
  - AI classification summary
  - **Apply Now** button

### ✅ Quality Check:
- [ ] Agent name spelled correctly
- [ ] Jobs look fresh (posted in last 1-3 days)
- [ ] Good/so-so mix is appropriate
- [ ] Route types match preferences
- [ ] Locations within commute range

💡 **Fresh Search advantage**: You should see "Posted 1 day ago" or "Posted 2 days ago" in job descriptions.

---

## 🔗 Step 12: Copy Portal Link

Scroll down to **Portal Link** section.

**You'll see:**
```
✅ Portal link generated!

https://opptek.link/abc456

This link will track when Sarah Johnson clicks and applies to jobs.
```

### **Copy the link:**
1. Click the **📋 Copy Link** button
2. Link copied to clipboard!

---

## 📱 Step 13: Share Link with Free Agent

**Via text message:**
```
Hey Sarah! I just searched Indeed for you and found 20
fresh CDL jobs in Dallas (most posted in the last 2 days).

Check them out: https://opptek.link/abc456

Let me know if you see anything interesting!
- [Your Name]
```

**Via email:**
```
Subject: FRESH Job Alerts - 20 New CDL Positions in Dallas

Hi Sarah,

I've just completed a fresh search of the Dallas job market
and found 20 quality CDL driving positions posted in the last
1-3 days. These jobs have been pre-screened by our AI to match
your preferences.

Your Portal Link: https://opptek.link/abc456

Highlights:
- 43 "good" rated positions (AI-verified quality)
- Mix of local and regional routes
- Fresh postings (most within 48 hours)
- Jobs within 50 miles of Dallas

Click the link to see all 20 jobs and apply directly. These are
hot off the press - apply soon!

Let me know if you need anything!

Best,
[Your Name]
```

---

## 💰 Step 14: Review API Cost

**Check your spending:**

1. Click **📊 Coach Analytics** tab
2. Review **API Spending** section (if visible)
3. Note: ~$0.10-0.15 spent on this search

💡 **Budget management**: If you ran 10 Fresh searches today (1000 jobs total), you've spent ~$1.00-1.50.

---

## 🔄 Step 15: Leverage the Cache

**Here's the magic**: The 52 new jobs you just found are now cached!

### **For the next 7 days, you can:**

1. Run **💾 Memory-Only** searches for Dallas
2. Get those 52 fresh jobs (plus any others in cache)
3. **Zero API cost** for repeat searches
4. Update agent portals daily without spending

**Example workflow:**
- **Monday 9am**: Fresh Search (Dallas, 100 jobs) → $0.10 cost
- **Tuesday-Friday**: Memory-Only (Dallas) → $0.00 cost each day
- **Next Monday**: Fresh Search again → $0.10 cost

💡 **Weekly Fresh + Daily Memory = Optimal cost efficiency**

---

## 📊 Step 16: Track Performance

### Check immediate engagement:

1. Click **📊 Coach Analytics** tab
2. Review metrics:
   - Total clicks (will increase when agent clicks)
   - Quality job percentage (should be 60-85%)
   - Fresh vs Memory ratio

### Check individual agent tracking:

1. Click **👥 Free Agents** tab
2. **🎯 Track Applications** sub-tab
3. **Select Free Agent**: Choose "Sarah Johnson"
4. Monitor:
   - Clicks
   - Applications
   - Status updates (Applied, Interviewing, etc.)

💡 **Follow up** if agent clicks but doesn't apply - they may have questions!

---

## ✅ Success Checklist

After completing this tutorial, you should be able to:

- [ ] Understand Fresh Search vs Memory-Only differences
- [ ] Run a Fresh Search using Indeed API
- [ ] Monitor 8-stage pipeline processing
- [ ] Interpret "Memory Jobs" vs "Fresh Jobs" metrics
- [ ] Understand API cost implications ($0.10-0.15 per 100 jobs)
- [ ] Leverage cache for future Memory-Only searches
- [ ] Share fresh portal links with agents
- [ ] Track spending and engagement

---

## 💡 Pro Tips

### Tip 1: Weekly Fresh Search Workflow

**Monday Morning Routine (15 minutes):**
1. Run Fresh Search for your top 3 markets (Dallas, Houston, Austin)
2. 100 jobs each = 300 total jobs = ~$0.30-0.45 cost
3. Cache populated for entire week
4. Tuesday-Friday: Use Memory-Only (zero cost) to update all agents

**Result**: Full coverage, minimal cost.

---

### Tip 2: Cost-Effective Search Modes

**Budget-Conscious Approach:**
- **Monday**: Medium (500 jobs) for primary market → $0.50
- **Wednesday**: Sample (100 jobs) for secondary market → $0.10
- **Daily**: Memory-Only for all agents → $0.00

**Total weekly cost**: ~$0.60 for 600+ jobs across 2 markets.

---

### Tip 3: When to Use Each API

**Indeed Fresh** (default):
- Standard CDL and warehouse searches
- Broad coverage
- Reliable classification

**Google Jobs** (if you have access):
- 99% cost savings vs Indeed
- Exact location mode recommended
- Requires `can_access_google_jobs` permission

**Outscraper** (via Batches & Scheduling):
- Batch processing (async)
- CSV export workflows
- Custom scraping needs

---

### Tip 4: Quality Control

**After Fresh Search, always check:**
1. **Quality Rate**: Should be 60-85%
   - <50%: Search terms too broad, or market is weak
   - >90%: Search terms too narrow, missing opportunities

2. **Fresh vs Memory Ratio**:
   - First search in market: Should be 100% Fresh
   - Subsequent searches: 30-70% Fresh (cache working)

3. **Job Posting Dates**:
   - Most jobs should be posted within 3-5 days
   - >10 days old: Market may be slow, or API issue

---

## 🆘 Troubleshooting

### Issue: "Indeed API timeout - no jobs returned"

**Cause**: Indeed API is slow or unresponsive (rare).

**Solution**:
1. Wait 2-3 minutes and try again
2. Reduce search mode to Quick Test (25 jobs)
3. Try a different market
4. Contact admin if persistent

---

### Issue: "Only 12 jobs found, expected 100"

**Cause**:
- Very specific search terms ("CDL driver class A hazmat tanker")
- Small market with limited postings
- Exact Location Mode enabled with tight radius

**Solution**:
1. Broaden search terms to just "CDL driver"
2. Uncheck "Exact Location Mode"
3. Increase radius to 75-100 miles
4. Try a larger nearby market

---

### Issue: "Quality rate is only 30% (expected 60-85%)"

**Cause**:
- Search terms too broad ("driver")
- Classifier mismatch (used Pathway for CDL jobs)
- Weak job market

**Solution**:
1. Refine search terms: "CDL driver" instead of just "driver"
2. Verify classifier type (CDL Traditional for driving jobs)
3. Check business rules (Admin → System Settings)

---

### Issue: "AI classification is slow (>2 minutes)"

**Cause**:
- OpenAI API rate limits
- High volume (500-1000 jobs)
- Network latency

**Solution**:
1. Wait patiently - it will complete
2. Reduce search mode (500 → 100 jobs)
3. Check OpenAI API status (Admin → Test All APIs)

---

### Issue: "Permission denied when clicking Indeed Fresh Only"

**Cause**: You don't have `can_pull_fresh_jobs` permission.

**Solution**:
1. Contact your admin
2. Request `can_pull_fresh_jobs` permission
3. Use Memory-Only in the meantime

---

## 🔍 Advanced: Comparing Fresh vs Memory

### Run This Experiment:

**Step 1: Fresh Search**
1. Run Fresh Search for Dallas, 100 jobs
2. Note: **Fresh Jobs: 52**, **Memory Jobs: 25**
3. Copy portal link and save for comparison

**Step 2: Immediate Memory Search**
1. Without changing any settings, click **💾 Memory Only**
2. Note: Should find ~77 jobs (all from memory now)
3. Compare portal link - jobs should be nearly identical

**Step 3: Wait 24 Hours**
1. Next day, run **💾 Memory Only** again
2. Note: May find 80-90 jobs (other coaches added to cache)
3. Portal link updated with new jobs

**Insight**: Fresh Search populates cache → Memory searches leverage cache → Multiple coaches benefit.

---

## 📚 Next Steps

**Now that you've mastered Fresh Searches, learn:**
- **Free Agent Management Tutorial** - Complete agent lifecycle guide
- **Batches & Scheduling Tutorial** - Automate weekly Fresh searches
- **Custom Location Search Tutorial** - Advanced targeting

---

## 🎓 Practice Exercise

**Try this now:**

1. Run a **Fresh Search** for **Austin** market
2. Search for **"warehouse"** instead of CDL driver
3. Use **Career Pathways** classifier
4. Select **Medium (500 jobs)** mode (if permitted)
5. Select pathway preferences: **warehouse**, **logistics_pathway**, **stepping_stone**
6. Set max jobs to **25**
7. Generate portal with HTML preview
8. Review quality rate and fresh vs memory ratio

**Expected outcome:**
- 300-500 total jobs
- 40-60% quality rate (pathways are more specific)
- 70-90% fresh jobs (first search in Austin with these pathways)
- Portal link with 25 warehouse progression opportunities
- Cost: ~$0.50-0.75
- Total time: 90-120 seconds

---

**Congratulations! You're now a Fresh Search expert.**

💡 **Remember**: Fresh searches are your weekly workhorse. Use them strategically to populate the cache, then leverage Memory-Only for zero-cost daily agent updates.

---

*Opptek: Cutting through the noise to connect Free Agents with opportunities that matter.*
