# Memory-Only Search Tutorial

**Complete Step-by-Step Guide for Zero-Cost Job Searches**

---

## 🎯 What Is a Memory-Only Search?

A Memory-Only search pulls jobs ONLY from Opptek's cached database - no fresh API calls to Indeed, Google Jobs, or Outscraper.

### ✅ Benefits:
- **Instant results** (3-10 seconds vs 45-90 seconds)
- **Zero API cost** (no budget impact)
- **Full tracking** (still generates Short.io portal links)
- **AI classification** (jobs already classified as good/so-so/bad)
- **Fresh enough** (cache updated by weekly Fresh searches)

### ⚠️ Limitations:
- Limited to jobs scraped in last [memory period] (default: 7 days)
- May miss brand-new job postings (posted in last 24 hours)
- Dependent on previous Fresh searches populating the cache

---

## 💡 When to Use Memory-Only

### ✅ Perfect For:
- **Daily agent updates** - Refreshing portal links without API costs
- **High-frequency searches** - Checking multiple times per day
- **Testing configurations** - Experimenting with filters/settings
- **Quick portal regeneration** - Agent lost their link, need to resend
- **Budget conservation** - Near end of month, preserving API credits

### ❌ Not Ideal For:
- **Brand new markets** - No cached jobs yet (use Fresh first)
- **Weekly comprehensive searches** - Want latest postings (use Fresh)
- **VIP client searches** - Important agents deserve fresh results

---

## 📋 Prerequisites

Before running a Memory-Only search, ensure:

1. **Fresh searches have run** in the last 7 days for your target market
   - Either you ran them, or another coach did
   - Or a scheduled batch job populated the cache

2. **You have `can_generate_pdf` permission** (for HTML preview and portal links)

3. **Free Agent info ready** (name, preferences, contact info)

---

## 🚀 Step-by-Step Tutorial

### Step 1: Navigate to Job Search Tab

1. Log in to Opptek
2. Click **🔍 Job Search** tab at top

---

### Step 2: Configure Location

**Choose location type:**

#### Option A: Single Market (Most Common)
1. Location dropdown stays on **"Select Market"**
2. Select market from dropdown (e.g., "Dallas-Fort Worth")

💡 **Tip**: Use standard markets for consistent results.

#### Option B: Multiple Markets
1. Change location dropdown to **"Select Markets"**
2. Check multiple markets (e.g., Dallas, Houston, Austin)

#### Option C: Custom Location (Requires Permission)
1. Change location dropdown to **"Custom Location"**
2. Enter city and state (e.g., "Waco, TX")

💡 **For this tutorial**: Select **Dallas-Fort Worth** as single market.

---

### Step 3: Configure Search Mode

**Search Mode dropdown:**
- Select **"Sample (100 jobs)"** for this tutorial

💡 **Why 100?** Balances comprehensiveness with speed. Memory searches are fast enough to handle 100 jobs easily.

---

### Step 4: Set Search Terms

**Search Terms** field:
- Leave as default: **"CDL driver"**
- Or customize for your agent (e.g., "warehouse worker", "forklift operator")

💡 **Tip**: Keep it broad. AI will filter quality later.

---

### Step 5: Set Search Radius

**Search Radius dropdown:**
- Select **50 miles** (default)
- Adjust if agent has limited commute range

💡 **For agents who can't travel far**: Use 25 miles or less.

---

### Step 6: Choose Classifier Type

**Classifier Type dropdown:**

#### Option A: CDL Traditional (Most Common)
- Select **"CDL Traditional"**
- For experienced CDL drivers
- AI rates jobs as: good, so-so, or bad
- Shows route types: local, regional, OTR

#### Option B: Career Pathways
- Select **"Career Pathways"**
- For warehouse workers wanting to transition to driving
- AI identifies progression opportunities
- Shows pathway types: dock_to_driver, internal_cdl_training, etc.

💡 **For this tutorial**: Select **CDL Traditional**.

---

### Step 7: Configure Portal Settings

**This section controls what the Free Agent sees in their personalized portal.**

#### Max Jobs for PDF:
- Select **20** (sweet spot for engagement)

#### Route Type Filter:
- Select **both** options:
  - ✅ **Local routes**
  - ✅ **Regional/OTR routes**
- Or filter based on agent's home time preference

#### Match Quality Filter:
- Select these two:
  - ✅ **good**
  - ✅ **so-so**
- Leave **bad** unchecked (filter out low-quality jobs)

#### Fair Chance Only:
- ⬜ Leave unchecked (unless agent has criminal background)
- ✅ Check if agent needs fair chance jobs

#### Show HTML Preview:
- ✅ **Check this box** (so you can review before sharing)

#### Generate Portal Link:
- ✅ **Check this box** (creates tracked Short.io link)

#### Show "Prepared For":
- ✅ **Check this box** (personalizes portal header)

#### Enable PDF Generation:
- ⬜ Leave unchecked (portal link is better than PDF)

---

### Step 8: Enter Free Agent Info

**Two options:**

#### Option A: Airtable Search (Recommended)

1. **Search Airtable** field: Type agent's name (e.g., "John Smith")
2. **Search by** dropdown: Select **"name"**
3. Click **🔎 Search** button
4. Review search results
5. **Select Free Agent** dropdown: Choose the correct agent
6. Click **✅ Use Selected** button

✅ **Agent info auto-fills!**

---

#### Option B: Manual Entry (Quick Option)

1. **Free Agent Name** field: Type "John Smith"
2. **Agent UUID** field: Leave blank (optional)
3. Click **✅ Use Manual Entry** button

✅ **Manual info populated!**

---

### Step 9: Set Memory Time Period

**Memory Time Period dropdown:**
- Select **"7 days"** (default, recommended)

💡 **What this means**: Search jobs cached in last 7 days.

**Other options:**
- **3 days** - Freshest results, smaller pool
- **14 days** - Broader coverage, may include older postings
- **30 days** - Maximum coverage, but some jobs may be filled

---

### Step 10: Run Memory-Only Search

**Click the big button:**

### **💾 Memory Only**

✅ You should see:
- "Searching memory cache..."
- Progress indicator
- Results appear in 3-10 seconds

---

## 📊 Step 11: Review Search Results

### Search Summary Section

You'll see:
```
Memory Search Results for Dallas-Fort Worth
Search Terms: CDL driver | Radius: 50 miles | Classifier: CDL Traditional

Total Jobs: 87
Quality Jobs (good/so-so): 62
Good: 41 | So-So: 21 | Bad: 25

Memory Jobs: 87 | Fresh Jobs: 0
```

💡 **Verify**:
- Total jobs found (should be 50-100 for Dallas)
- Quality percentage (aim for 50%+)
- All jobs from memory (Fresh Jobs: 0)

---

### Quality Metrics (4-Column Display)

**Review these metrics:**
- **Total Jobs**: 87
- **Quality Jobs**: 62 (71% quality rate ✅)
- **Quality Rate**: 71.3%
- **Top Route**: Local (45 jobs)

💡 **Good quality rate**: 50-80% means AI is filtering well.

---

### Route Distribution (Bar Chart)

**Check the mix:**
- Local: 45 jobs
- Regional: 18 jobs
- OTR: 24 jobs

💡 **Use this** to verify the mix matches agent preferences.

---

## 🖥️ Step 12: Review HTML Preview

Scroll down to **HTML Preview** section.

**What you should see:**
- Clean phone-screen mockup
- Portal header: "Prepared by Coach [Your Name] for John Smith"
- Job cards (up to 20 jobs, as configured):
  - Company logo placeholder
  - Job title
  - Company name
  - Location
  - AI classification summary
  - **Apply Now** button

### ✅ Quality Check:
- [ ] Agent name spelled correctly
- [ ] Jobs look relevant
- [ ] Good/so-so mix is appropriate
- [ ] Locations are within commute range
- [ ] Route types match preferences

💡 **If something looks wrong**: Scroll back up and adjust portal settings, then click Memory Only again.

---

## 🔗 Step 13: Copy Portal Link

Scroll down to **Portal Link** section.

**You'll see:**
```
✅ Portal link generated!

https://opptek.link/xyz789

This link will track when John Smith clicks and applies to jobs.
```

### **Copy the link:**
1. Click the **📋 Copy Link** button
2. Link copied to clipboard!

---

## 📱 Step 14: Share Link with Free Agent

**Via text message:**
```
Hey John! I found 20 quality CDL driver jobs in Dallas
for you. Check them out: https://opptek.link/xyz789

Let me know if you have questions!
- [Your Name]
```

**Via email:**
```
Subject: Your Personalized Job Portal - 20 CDL Jobs in Dallas

Hi John,

I've created a personalized job portal with 20 quality CDL
driving positions in the Dallas area. These jobs have been
pre-screened by our AI to match your preferences.

Your Portal Link: https://opptek.link/xyz789

The portal includes:
- Local and regional routes
- Good and so-so rated positions
- Jobs within 50 miles of Dallas

Click the link to see all 20 jobs and apply directly.

Let me know if you need anything!

Best,
[Your Name]
```

---

## 📈 Step 15: Track Engagement (Optional)

### Check clicks in Coach Analytics:

1. Click **📊 Coach Analytics** tab
2. Review **Total Clicks** metric (should increase when agent clicks)
3. Check **Unique Agents Engaged** (includes this agent now)

### Check individual agent tracking:

1. Click **👥 Free Agents** tab
2. Click **🎯 Track Applications** sub-tab
3. **Select Free Agent**: Choose "John Smith"
4. **Agent Activity Summary** shows:
   - Total clicks
   - Recent applications
   - Last activity timestamp

💡 **Follow up** if agent clicked but didn't apply - they may have questions!

---

## 🔄 Step 16: Update Agent Portal (Future)

**When to regenerate:**
- Weekly updates with fresh jobs
- Agent's preferences changed
- Agent lost their original link

**How to regenerate (Two methods):**

### Method A: Run Memory-Only Again
1. Repeat Steps 1-10
2. New portal link generated
3. Share updated link with agent

### Method B: Update in Free Agents Table
1. Click **👥 Free Agents** tab
2. **📋 Manage Agents** sub-tab
3. Find agent in table
4. Edit preferences (route type, max jobs, etc.)
5. Click **💾 Save Changes** button
6. **Portal link auto-regenerates!**
7. Copy new link from **Portal Link** column

💡 **Method B is faster** for simple updates.

---

## ✅ Success Checklist

After completing this tutorial, you should be able to:

- [ ] Run a Memory-Only search in under 60 seconds
- [ ] Configure location, search mode, and classifier
- [ ] Set portal preferences (filters, max jobs, quality)
- [ ] Use Airtable lookup to find Free Agents
- [ ] Review HTML preview before sharing
- [ ] Generate and copy portal links
- [ ] Share links via text/email
- [ ] Track engagement in analytics

---

## 💡 Pro Tips

### Tip 1: Batch Updates
**Update 10 agents in 10 minutes:**
1. Run Memory-Only for Dallas market once
2. Save HTML preview
3. Go to Free Agents table
4. Edit 10 agents' settings
5. Click **💾 Save Changes** (auto-regenerates all 10 portal links)
6. Copy links and text each agent

### Tip 2: Memory Period Strategy
- **3 days**: For agents checking daily (most engaged)
- **7 days**: Standard (good balance)
- **14 days**: For agents in smaller markets (broader coverage)

### Tip 3: Quality Filter Adjustment
- **Good only**: VIP agents, high standards
- **Good + So-So**: Standard (most agents)
- **All quality levels**: Testing, or very limited market

### Tip 4: Zero-Cost Daily Workflow
1. Monday: Run Fresh Search to populate cache
2. Tuesday-Friday: Run Memory-Only for all agents (zero cost)
3. Track engagement in Coach Analytics
4. Follow up on clicks without applications

---

## 🆘 Troubleshooting

### Issue: "No jobs found in memory"

**Cause**: No cached jobs for this market/search term combination.

**Solution**:
1. Run a **🔍 Indeed Fresh Only** search first (will cost API credits)
2. Wait 60-90 seconds for results
3. Then switch to Memory-Only for future searches

---

### Issue: "Only 5 jobs found, expected 50+"

**Cause**: Very specific filters reducing pool (fair chance + local + no experience).

**Solution**:
1. Broaden filters (remove fair chance filter temporarily)
2. Or increase memory period to 14 days
3. Or run Fresh Search to populate cache with more jobs

---

### Issue: "Jobs are old (posted 10+ days ago)"

**Cause**: No recent Fresh searches have run for this market.

**Solution**:
1. Run a Fresh Search to update the cache
2. Or schedule a weekly batch job (Batches & Scheduling tab)

---

### Issue: "Portal link doesn't track clicks"

**Cause**: "Generate Portal Link" was not checked.

**Solution**:
1. Check **Generate Portal Link** box
2. Run Memory-Only search again
3. New tracked link will generate

---

## 📚 Next Steps

**Now that you've mastered Memory-Only searches, learn:**
- **Fresh Search Tutorial** - How to run Indeed/Outscraper API searches
- **Free Agent Management Tutorial** - Complete agent lifecycle guide
- **Custom Location Search Tutorial** - Advanced location targeting

---

## 🎓 Practice Exercise

**Try this now:**

1. Run a Memory-Only search for **Houston** market
2. Search for **"warehouse worker"** instead of CDL driver
3. Use **Career Pathways** classifier
4. Select pathway preferences: **dock_to_driver** and **internal_cdl_training**
5. Set max jobs to **15**
6. Generate portal with HTML preview
7. Review results and copy portal link

**Expected outcome:**
- 15-30 warehouse-to-driver pathway jobs
- Quality rate 40-60%
- Portal link ready to share
- Total time: 60 seconds

---

**Congratulations! You're now a Memory-Only search expert.**

💡 **Remember**: Memory-Only is your daily workhorse. Use it liberally - it costs nothing and keeps your agents engaged with fresh portal links.

---

*Opptek: Cutting through the noise to connect Free Agents with opportunities that matter.*
