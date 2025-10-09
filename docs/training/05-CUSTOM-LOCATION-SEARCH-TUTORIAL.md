# Custom Location Search Tutorial

**Advanced Guide for Searching Any City or State**

---

## 🎯 What Is a Custom Location Search?

A Custom Location Search allows you to search for jobs in **any city and state** - not just the pre-configured standard markets.

### Standard Markets vs Custom Locations

**Standard Markets** (dropdown):
- Dallas-Fort Worth
- Houston
- Austin
- Atlanta
- Phoenix
- ... (pre-configured list)

**Custom Locations** (you type it):
- Waco, TX
- Lubbock, TX
- Shreveport, LA
- Little Rock, AR
- ... (anywhere in USA)

---

## ✅ Benefits of Custom Location Searches

- **Reach smaller markets** - Agents in cities without standard markets
- **Expand geographic coverage** - Test new regions
- **Hyper-local targeting** - Specific city instead of metro area
- **Competitive advantage** - Less competition in smaller markets

---

## ⚠️ Prerequisites

### Permission Required
**You must have `can_use_custom_locations` permission** to access this feature.

**To check if you have permission:**
1. Log in to Opptek
2. Navigate to Job Search tab
3. Check Location dropdown - do you see **"Custom Location"** option?
   - ✅ Yes → You have permission
   - ❌ No → Contact admin to request permission

---

### API Cost Considerations

Custom Location searches use the **Indeed API** (same as Fresh Search):
- **Cost**: ~$0.10-0.15 per 100 jobs
- **Processing time**: 45-90 seconds
- **Budget impact**: Same as standard Fresh Search

💡 **Recommendation**: Use Fresh Search (not Memory-Only) for first custom location search to populate cache.

---

## 🚀 Step-by-Step Tutorial

### Step 1: Navigate to Job Search Tab

1. Log in to Opptek
2. Click **🔍 Job Search** tab at top

---

### Step 2: Select Custom Location Mode

1. Locate **Location Type** dropdown
   - Default: "Select Market"

2. Click dropdown and select **"Custom Location"**

✅ **Interface changes**: Market dropdown disappears, replaced with **Custom Location** text field.

---

### Step 3: Enter Custom Location

**Custom Location** text field appears.

**Format**: `City, State`

**Examples**:
- `Waco, TX`
- `Shreveport, LA`
- `Little Rock, AR`
- `Midland, TX`

💡 **Important**:
- Always include **city AND state**
- Use standard state abbreviations (TX, LA, AR, etc.)
- Comma between city and state

---

#### Common Formatting Mistakes

❌ **Wrong**:
- `Waco` (missing state)
- `Waco TX` (missing comma)
- `Waco, Texas` (use abbreviation TX, not full name)
- `waco, tx` (lowercase works, but uppercase is cleaner)

✅ **Correct**:
- `Waco, TX`
- `Shreveport, LA`
- `Little Rock, AR`

---

### Step 4: Configure Search Mode

**Search Mode dropdown:**
- Select **"Sample (100 jobs)"** (recommended for first custom location search)

💡 **Why 100 jobs?**
- Smaller markets may not have 500 jobs
- 100 is usually sufficient to populate cache
- Test the market before committing to larger searches

---

### Step 5: Set Search Parameters

**Same as standard searches:**

- **Search Terms**: `CDL driver` (or customize)
- **Search Radius**: `50 miles` (recommended for smaller markets)
- **Classifier Type**: `CDL Traditional` or `Career Pathways`
- **Exact Location Mode**: ⬜ Leave unchecked (allow radius expansion)
- **Include No-Experience Jobs**: ⬜ Or ✅ as needed

---

### Step 6: Configure Portal Settings

**Same as other tutorials:**

- **Max Jobs for PDF**: `20`
- **Route Type Filter**: ✅ Both (Local and Regional/OTR)
- **Match Quality Filter**: ✅ good, ✅ so-so
- **Fair Chance Only**: ⬜ (or ✅ if needed)
- **Show HTML Preview**: ✅ **Check this**
- **Generate Portal Link**: ✅ **Check this**
- **Show "Prepared For"**: ✅ **Check this**
- **Enable PDF Generation**: ⬜ Leave unchecked

---

### Step 7: Enter Free Agent Info

**Use Airtable Search or Manual Entry:**

For this tutorial:
- **Free Agent Name**: "Tommy Wilson"
- **City**: "Waco" (matches custom location)
- Click **✅ Use Manual Entry**

💡 **Tip**: Agent's city should match (or be near) your custom location.

---

### Step 8: Set Memory Time Period

**Memory Time Period dropdown:**
- Select **"7 days"** (standard)

💡 **Note**: First custom location search will likely have 0 memory hits (no cached jobs yet).

---

### Step 9: Run Fresh Search (Recommended)

**For first custom location search, use Fresh Search:**

### **🔍 Indeed Fresh Only**

**Click the button.**

⏱️ **Wait 60-90 seconds** for processing.

💡 **Why Fresh Search?**
- Custom locations rarely have cached jobs (unless other coaches searched recently)
- Fresh Search populates cache for future Memory-Only searches
- Ensures latest job postings for new market

---

### Step 10: Review Search Results

### Search Summary Section

**Example output** for Waco, TX:
```
Fresh Search Results for Custom Location: Waco, TX
Search Terms: CDL driver | Radius: 50 miles | Classifier: CDL Traditional

Total Jobs: 43
Quality Jobs (good/so-so): 31
Good: 22 | So-So: 9 | Bad: 12

Memory Jobs: 0 | Fresh Jobs: 43
✅ 43 new jobs added to cache!
```

💡 **Key insights**:
- **Total Jobs: 43** - Smaller than Dallas (typical for smaller market)
- **Fresh Jobs: 43** - All new (no cache yet)
- **Quality rate: 72%** - Good filtering even in smaller market

---

### Quality Metrics (4-Column Display)

**Review these metrics:**
- **Total Jobs**: 43
- **Quality Jobs**: 31 (72% quality rate ✅)
- **Quality Rate**: 72.0%
- **Top Route**: Regional (18 jobs)

💡 **Smaller markets often have more regional/OTR jobs** (fewer local routes than big cities).

---

### Route Distribution (Bar Chart)

**Example for Waco:**
- Local: 11 jobs
- Regional: 18 jobs
- OTR: 14 jobs

💡 **Adjust agent preferences** based on what's available in the market.

---

## 🖥️ Step 11: Review HTML Preview

**Same as other tutorials:**

Scroll down to **HTML Preview** section.

**What you should see:**
- Portal header: "Prepared by Coach [Your Name] for Tommy Wilson"
- Job cards (up to 20 jobs):
  - Company, title, location
  - AI classification summary
  - **Apply Now** button

### ✅ Quality Check for Custom Locations:
- [ ] Jobs are actually in/near Waco (check location field)
- [ ] Radius respected (within 50 miles)
- [ ] Quality mix appropriate for smaller market
- [ ] Route types match market characteristics

💡 **Custom location verification**: Some jobs may show nearby cities (Temple, Killeen) within 50-mile radius - this is correct behavior.

---

## 🔗 Step 12: Copy Portal Link

**Same as other tutorials:**

Scroll down to **Portal Link** section.

```
✅ Portal link generated!

https://opptek.link/def789

This link will track when Tommy Wilson clicks and applies to jobs.
```

### **Copy the link:**
1. Click the **📋 Copy Link** button
2. Link copied to clipboard!

---

## 📱 Step 13: Share Link with Free Agent

**Via text message:**
```
Hey Tommy! Just searched the Waco area for you and found 20
quality CDL jobs (some in Temple and Killeen too - all within
50 miles).

Check them out: https://opptek.link/def789

Let me know what you think!
- [Your Name]
```

💡 **Note**: Mention nearby cities to set expectations.

---

## 🔄 Step 14: Leverage Cache for Future Searches

**Now that you've populated the cache:**

### **For the next 7 days, you can:**

1. Run **💾 Memory-Only** searches for "Waco, TX"
2. Get those 43 fresh jobs (plus any others added by other coaches)
3. **Zero API cost** for repeat searches
4. Update agent portals daily without spending

**Example workflow:**
- **Monday 9am**: Fresh Search (Waco, TX) → $0.10 cost
- **Tuesday-Friday**: Memory-Only (Waco, TX) → $0.00 cost each day
- **Next Monday**: Fresh Search again → $0.10 cost

---

## 💡 Advanced Custom Location Strategies

### Strategy 1: Multi-City Coverage

**Use case**: Agent is willing to relocate to multiple smaller cities.

**Approach**:
1. Run separate custom location searches for each city:
   - Waco, TX
   - Temple, TX
   - Killeen, TX

2. Each search generates a portal link

3. Send agent all 3 links:
```
Hey Tommy, I searched 3 cities for you:

Waco area: https://opptek.link/abc123
Temple area: https://opptek.link/def456
Killeen area: https://opptek.link/ghi789

Check them all and see what looks good!
```

💡 **Budget**: 3 searches × $0.10 = ~$0.30 total cost.

---

### Strategy 2: Custom Location + Multiple Markets

**Use case**: Agent is flexible on location, wants comprehensive coverage.

**Approach**:
1. Use **"Select Markets"** (plural) for standard markets:
   - Dallas-Fort Worth
   - Houston
   - Austin

2. Add **Custom Location** searches for nearby smaller cities:
   - Waco, TX
   - College Station, TX
   - Tyler, TX

3. Combine results into a comprehensive portal

💡 **Note**: You'll need to run separate searches - can't mix "Select Markets" and "Custom Location" in one search.

---

### Strategy 3: Radius Optimization for Custom Locations

**Smaller markets may need larger radius for sufficient job volume.**

**Experiment with radius:**

1. **First search**: 50 miles (standard)
   - Result: 30-50 jobs

2. **If too few jobs**: Increase to 75-100 miles
   - Result: 60-80 jobs

3. **If too many irrelevant locations**: Decrease to 25 miles
   - Result: 15-25 jobs (hyper-local)

💡 **Balance**: Enough jobs to be useful, close enough to be relevant.

---

### Strategy 4: Test Markets Before Committing

**Before running Medium (500) or Full (1000) searches in new custom location:**

1. Run **Quick Test (25 jobs)** first
   - Cost: ~$0.02-0.03

2. Review results:
   - Quality rate
   - Route type distribution
   - Job relevance

3. If results are good:
   - Run **Sample (100)** or **Medium (500)**

4. If results are poor:
   - Try different search terms
   - Adjust radius
   - Or skip this market entirely

💡 **Cost savings**: $0.03 test prevents wasting $0.50 on bad market.

---

## 📊 Comparing Standard vs Custom Location Results

### Run This Experiment:

**Step 1: Standard Market Search**
1. Location: "Select Market" → Dallas-Fort Worth
2. Search Mode: Sample (100)
3. Run Fresh Search
4. Note: Total jobs, quality rate, route distribution

**Step 2: Custom Location Search**
1. Location: "Custom Location" → Fort Worth, TX
2. Search Mode: Sample (100)
3. Run Fresh Search
4. Note: Total jobs, quality rate, route distribution

**Step 3: Compare Results**
- **Dallas-Fort Worth** (metro area): 85-100 jobs, 75% quality, 60% local routes
- **Fort Worth, TX** (specific city): 50-70 jobs, 70% quality, 50% local routes

**Insight**: Standard markets cover broader area, custom locations are more targeted.

---

## 🗺️ Geographic Coverage Best Practices

### Building a Custom Location Network

**Goal**: Cover Texas with mix of standard markets and custom locations.

**Standard Markets (pre-configured):**
- Dallas-Fort Worth
- Houston
- Austin
- San Antonio
- El Paso

**Custom Locations (you add):**
- Waco, TX
- Lubbock, TX
- Amarillo, TX
- Corpus Christi, TX
- Tyler, TX
- College Station, TX
- Midland/Odessa, TX

**Result**: Comprehensive Texas coverage, reaching agents in all major and mid-size cities.

---

### Budget-Conscious Custom Location Strategy

**Monthly budget**: $5.00

**Allocation**:
- **Standard markets** (Monday Fresh Searches): $2.00
  - Dallas (500 jobs) = $0.50
  - Houston (500 jobs) = $0.50
  - Austin (500 jobs) = $0.50
  - San Antonio (500 jobs) = $0.50

- **Custom locations** (Weekly Fresh Searches): $2.00
  - Waco (100 jobs) = $0.10
  - Lubbock (100 jobs) = $0.10
  - ... (20 custom location searches total)

- **Reserve**: $1.00 for testing new markets

**Result**: 2000+ standard market jobs, 2000+ custom location jobs, comprehensive coverage.

---

## 🆘 Troubleshooting Custom Location Searches

### Issue: "Location not found" or "No jobs returned"

**Cause**: City name misspelled, or very small town with no job postings.

**Solution**:
1. Verify spelling of city and state
2. Check state abbreviation is correct (TX not Texas)
3. Try nearby larger city
4. Increase radius to 75-100 miles

---

### Issue: "Only 5 jobs found, expected 50+"

**Cause**:
- Very small market with limited job postings
- Exact Location Mode enabled (too restrictive)
- Search terms too specific

**Solution**:
1. Uncheck "Exact Location Mode"
2. Increase radius to 75-100 miles
3. Broaden search terms (just "CDL driver" instead of "CDL driver local")
4. Consider searching nearby larger city instead

---

### Issue: "Jobs are showing cities 100+ miles away"

**Cause**:
- Indeed API expanding search due to insufficient jobs in target area
- Radius set too high

**Solution**:
1. Reduce radius to 25-50 miles
2. Check "Exact Location Mode" to enforce strict boundary
3. Accept that smaller markets may have limited local jobs

---

### Issue: "Custom location results different than standard market"

**Example**:
- "Dallas-Fort Worth" (standard): 100 jobs
- "Dallas, TX" (custom): 60 jobs

**Cause**: Standard markets cover larger metro area, custom locations are city-specific.

**Explanation**:
- "Dallas-Fort Worth" includes: Dallas, Fort Worth, Plano, Irving, Arlington, etc.
- "Dallas, TX" includes: Dallas + 50-mile radius

**Solution**: Choose based on agent's needs:
- Agent in Dallas only → Use "Dallas, TX" custom location
- Agent flexible across metro → Use "Dallas-Fort Worth" standard market

---

## 📈 Tracking Custom Location Performance

### Coach Analytics View

1. Click **📊 Coach Analytics** tab

**Review custom location effectiveness:**
- Compare click rates: Standard markets vs custom locations
- Application rates by geographic area
- Quality job percentage by market type

💡 **Insight**: Some custom locations may outperform standard markets (less competition, more engaged agents).

---

### Market Analytics Dashboard

1. Click **📈 Market Analytics** tab

**Analyze custom location coverage:**
- Total jobs by custom location
- Quality rate by city
- Click-through rates by geographic area

💡 **Use this** to identify high-performing custom locations worth repeating.

---

## ✅ Success Checklist

After completing this tutorial, you should be able to:

- [ ] Verify you have `can_use_custom_locations` permission
- [ ] Select "Custom Location" mode in Job Search tab
- [ ] Format custom locations correctly (City, State)
- [ ] Run Fresh Searches for custom locations
- [ ] Interpret results for smaller markets
- [ ] Adjust radius based on market size
- [ ] Leverage cache for future Memory-Only searches
- [ ] Build a custom location network
- [ ] Compare standard vs custom location results

---

## 🎓 Practice Exercise

**Complete custom location search workflow:**

1. **Select Custom Location mode**

2. **Enter location**: "Lubbock, TX"

3. **Configure search**:
   - Search Mode: Sample (100 jobs)
   - Search Terms: "CDL driver"
   - Search Radius: 75 miles (larger radius for smaller market)
   - Classifier: CDL Traditional

4. **Set portal preferences**:
   - Max Jobs: 20
   - Route Type: both
   - Quality: good and so-so
   - HTML Preview: enabled
   - Generate Portal Link: enabled

5. **Run Fresh Search** (not Memory-Only - populate cache first)

6. **Review results**:
   - How many total jobs?
   - What's the quality rate?
   - What's the route type distribution?
   - Are there enough local routes, or mostly regional/OTR?

7. **Copy portal link** and save for agent

8. **Run Memory-Only** immediately after (verify cache works)
   - Should find same ~jobs
   - Zero cost

**Expected outcome:**
- 30-60 total jobs (smaller market)
- 60-75% quality rate
- Higher proportion of regional/OTR routes (typical for Lubbock)
- Fresh Search cost: ~$0.10
- Memory-Only cost: $0.00
- Total time: 90 seconds

---

**Congratulations! You're now a Custom Location search expert.**

💡 **Remember**: Custom locations unlock access to smaller markets where your agents face less competition. Use them strategically to expand your geographic footprint without breaking the budget.

---

*Opptek: Cutting through the noise to connect Free Agents with opportunities that matter.*
