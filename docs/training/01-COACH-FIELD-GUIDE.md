# Opptek Coach Field Guide

**Complete Reference for All Features, Fields, and Buttons**

---

## 🎯 What Is Opptek?

**The Problem**: The job market is overwhelming. Free Agents (CDL drivers and warehouse workers) don't have time to read through thousands of irrelevant job postings to find the ones that actually matter to them.

**That's what Opptek is for.**

Opptek is an AI-powered job discovery platform that cuts through the noise. It finds quality employment opportunities, classifies them using AI, and delivers personalized job portals to each Free Agent based on their preferences.

---

## 📑 Navigation Overview

When you log in, you'll see these main tabs:

- **🔍 Job Search** - Search for jobs and create personalized portals
- **🗓️ Batches & Scheduling** - Schedule automated searches (if enabled)
- **👥 Free Agents** - Manage your Free Agent roster
- **📊 Coach Analytics** - Track your performance metrics
- **📈 Market Analytics** - Analyze market-level data
- **🏢 Companies** - Company performance insights
- **👑 Admin Panel** - System administration (admin only)

---

## 1️⃣ JOB SEARCH TAB

### 🎯 Purpose
Find quality jobs for Free Agents using either cached results (Memory Only) or fresh API searches (Indeed Fresh).

---

### 📍 Location Settings

#### **Location Type**
Choose how to specify where to search:
- **Select Market** - Use one of our pre-configured markets (Dallas-Fort Worth, Houston, etc.)
- **Select Markets** - Search multiple markets at once
- **Custom Location** - Enter any city/state (requires permission)

💡 **Tip**: Use standard markets for consistent results. Use custom locations for agents in smaller cities.

---

#### **Search Mode**
Controls how many jobs to search:
- **Quick Test (25 jobs)** - Fast testing, low cost
- **Sample (100 jobs)** - Standard search, balanced
- **Medium (500 jobs)** - Comprehensive coverage
- **Full (1000 jobs)** - Maximum coverage (admin permission required)

💡 **Cost Impact**: Larger searches cost more in API credits. Start with Sample mode.

---

### 🔍 Search Configuration

#### **Search Terms**
What job titles to search for. Examples:
- `CDL driver` (default)
- `warehouse worker`
- `forklift operator`
- `dock worker`

💡 **Tip**: Keep it simple. The AI will filter quality later.

---

#### **Search Radius**
How far from the location to search:
- Options: 0, 5, 10, 15, 25, 50, 75, 100 miles
- Default: 50 miles

💡 **Tip**: 50 miles works for most markets. Use 75-100 for rural areas.

---

#### **Classifier Type**
Which AI classifier to use:
- **CDL Traditional** - For truck driving jobs (good/so-so/bad ratings)
- **Career Pathways** - For warehouse-to-driver progression opportunities

💡 **When to use each**:
- CDL Traditional: Experienced CDL drivers looking for driving jobs
- Career Pathways: Warehouse workers wanting to transition into driving

---

#### **Exact Location Mode** (checkbox)
- ✅ Checked: Search ONLY in the exact city specified
- ⬜ Unchecked: Allow radius expansion for more results

💡 **Use exact location** when Free Agent can't commute far.

---

#### **Include No-Experience Jobs** (checkbox)
- ✅ Checked: Include entry-level positions
- ⬜ Unchecked: Only experienced positions

💡 **Check this** for Free Agents without CDL experience or who are just starting out.

---

### 📄 Free Agent Portal/PDF Settings

This section controls what jobs appear in the personalized portal you create.

#### **Max Jobs for PDF**
How many jobs to include in the agent's portal:
- Options: 5, 10, 15, 20, 25, 30, 50, 75, 100
- Recommendation: 15-25 jobs

💡 **Quality over quantity**: Agents are more likely to engage with 20 great jobs than 100 mediocre ones.

---

#### **Route Type Filter**
Filter by route type (CDL classifier only):
- **Local routes** - Home daily
- **Regional/OTR routes** - Multi-day trips

💡 **Tip**: Ask your Free Agent about home time preferences before filtering.

---

#### **Match Quality Filter**
Filter by AI quality rating:
- **good** - High-quality jobs (recommended to include)
- **so-so** - Medium-quality jobs (may include)
- **bad** - Low-quality jobs (usually exclude)

💡 **Standard practice**: Include only "good" and "so-so" jobs.

---

#### **Pathway Preferences** (Career Pathways classifier only)
Select which career pathways to include:
- **cdl_pathway** - Direct CDL opportunities
- **dock_to_driver** - Dock worker to driver progression
- **internal_cdl_training** - Company-sponsored CDL training
- **warehouse_to_driver** - Warehouse to driver transition
- **logistics_pathway** - Logistics and supply chain
- **non_cdl_driver** - Delivery, courier (no CDL)
- **warehouse** - Warehouse positions
- **stepping_stone** - Entry-level progression roles

💡 **Tip**: Select 2-3 relevant pathways based on agent's current role and goals.

---

#### **Fair Chance Only** (checkbox)
- ✅ Checked: Only show "fair chance" jobs (open to people with records)
- ⬜ Unchecked: Show all jobs

💡 **Check this** if your Free Agent has a criminal background.

---

#### **Show HTML Preview** (checkbox)
- ✅ Checked: See a preview of what the Free Agent will see
- ⬜ Unchecked: No preview

💡 **Always check this** to verify the portal looks good before sharing.

---

#### **Generate Portal Link** (checkbox)
- ✅ Checked: Create a Short.io tracked link for analytics
- ⬜ Unchecked: No tracking link

💡 **Always check this** to track agent engagement.

---

#### **Show "Prepared For"** (checkbox)
- ✅ Checked: Portal shows "Prepared by Coach [Your Name] for [Agent Name]"
- ⬜ Unchecked: Generic portal header

💡 **Personal touch**: Check this for 1-on-1 agent relationships.

---

#### **Enable PDF Generation** (checkbox)
- ✅ Checked: Generate downloadable PDF report
- ⬜ Unchecked: No PDF (just portal link)

💡 **Most coaches don't need PDFs** - portal links are more trackable.

---

### 👤 Free Agent Lookup

Two ways to specify which Free Agent you're creating the portal for:

#### **Airtable Search**
Search your Airtable database:
1. Type agent's name, UUID, or email in search box
2. Choose search type (name/uuid/email)
3. Click **🔎 Search**
4. Select agent from dropdown
5. Click **✅ Use Selected**

💡 **Fastest method** if agent is already in your Airtable.

---

#### **Manual Entry**
Enter agent info manually:
1. Type **Free Agent Name**
2. Enter **Agent UUID** (if you have it for Airtable linking)
3. Click **✅ Use Manual Entry**

💡 **Use this** for quick one-off searches or when agent isn't in Airtable yet.

---

### 💾 Smart Memory Section

#### **Memory Time Period**
How far back to check cached jobs:
- Options: 24 hours, 3 days, 7 days, 14 days, 30 days
- Default: 7 days

💡 **Tip**: Use 3-7 days for freshest results while maximizing cache hits.

---

### 🔘 Search Buttons

#### **💾 Memory Only** (Primary button)
- Searches ONLY cached jobs (no API calls)
- ✅ Instant results (3-10 seconds)
- ✅ Zero API cost
- ✅ Still generates tracked links
- ⚠️ Limited to jobs scraped in last [memory period]

**When to use**:
- Daily agent updates
- Testing configurations
- Quick portal regeneration

---

#### **🔍 Indeed Fresh Only** (Primary button)
- Searches Indeed API for fresh jobs
- ⚠️ Costs API credits ($0.10-0.15 per 100 jobs)
- ⏱️ Takes 45-90 seconds
- ✅ Latest job postings
- ✅ Runs through full 8-stage pipeline (AI classification, deduplication, tracking)

**When to use**:
- New markets with no cached jobs
- Weekly comprehensive searches
- Important client searches

💡 **Best practice**: Use Memory Only daily, Fresh Search weekly.

---

#### **⚡ Force Fresh Classification** (Advanced option in expander)
- Re-runs AI classification on cached jobs
- Useful when testing new AI prompts
- Requires admin permission

**When to use**: Almost never (admin testing only)

---

### 📊 Search Results

After running a search, you'll see:

#### **Search Summary**
- Total jobs found
- Quality jobs (good/so-so)
- Memory vs fresh jobs breakdown
- Search metadata (market, terms, radius)

---

#### **Quality Metrics** (4-column display)
- **Total Jobs** - All jobs found
- **Quality Jobs** - Good + So-So rated jobs
- **Quality Rate** - Percentage of quality jobs
- **Top Route** - Most common route type

---

#### **Route Distribution** (if CDL classifier)
Bar chart showing:
- Local routes count
- Regional routes count
- OTR routes count

💡 **Use this** to verify the mix matches your agent's preferences.

---

#### **HTML Preview** (if enabled)
Shows exactly what the Free Agent will see in their portal:
- Job cards with company, title, location
- AI classification summary
- Apply links

💡 **Always review this** before sharing the portal link.

---

#### **Portal Link** (if generated)
Short.io tracked link like: `https://opptek.link/abc123`

**How to use**:
1. Copy the link
2. Text/email to your Free Agent
3. Track clicks in Coach Analytics tab

💡 **The link is also saved** in the Free Agents table for future reference.

---

#### **Download Options**
- **📥 Download CSV** - Spreadsheet of all jobs
- **📄 Download PDF** - PDF report (if enabled)

---

## 2️⃣ BATCHES & SCHEDULING TAB

### 🎯 Purpose
Schedule automated job searches to run on a recurring basis (daily, weekly, monthly).

**Use case**: Set up a daily 9am search for Dallas CDL jobs, so fresh results are always ready.

---

### 📦 Async Batches Section

#### **Indeed Batch Scheduler**

**Location Settings:**
- Same options as Job Search tab
- Can schedule multiple markets at once

**Search Parameters:**
- Same as Job Search tab (terms, radius, classifier, etc.)

**Schedule Settings:**

**Frequency** - How often to run:
- **Once** - Run one time only
- **Daily** - Every day
- **Weekly** - Specific days of week
- **Monthly** - Same day each month

**Time (HH:MM)** - When to run (24-hour format):
- Example: `09:00` for 9am, `14:30` for 2:30pm

**Days of Week** (if Weekly/Daily selected):
- Check boxes: Mon, Tue, Wed, Thu, Fri, Sat, Sun

💡 **Typical schedule**: Daily at 9am, Monday-Friday

**📅 Create Batch Schedule** - Saves the schedule

---

#### **Google Jobs Batch Scheduler**
- Requires `can_access_google_jobs` permission
- 99% cost savings vs Indeed
- Single market only
- Same scheduling options as Indeed

💡 **Use Google Jobs** when you have permission - much cheaper.

---

#### **DriverPulse Batch Scheduler**
CDL-specific job board integration:

**Search Term/Title** - Job title to search (default: "CDL driver")

**Filter Mode**:
- **Nationwide** - Search entire DriverPulse database
- **ZIP-based (Free Agent profiles)** - Only search ZIPs from your Free Agents

**AI Classifier**:
- CDL Job Classifier
- Pathway Classifier
- Both (CDL + Pathway)
- None (No AI classification)

💡 **DriverPulse runs in background** via GitHub Actions - no waiting.

**📅 Create DriverPulse Schedule** - Saves the schedule

---

#### **Scheduled Batches Table**
Shows all active batch schedules:
- Job type (Indeed, Google, DriverPulse)
- Frequency
- Next run time
- Status
- Edit/Delete buttons

💡 **Check this regularly** to ensure batches are running as expected.

---

### 📄 CSV Classification Section

**Purpose**: Upload a CSV file of jobs and run AI classification on them.

**Use case**: You exported jobs from another source and want Opptek to classify quality.

**Steps**:
1. Select **Target Market** (for metadata)
2. Choose **Route Filter**: both, local, or otr
3. Select **Classifier Type**: cdl or pathway
4. Upload CSV file
5. Map **Market Column** from your CSV
6. Click **🚀 Classify CSV**

💡 **CSV Requirements**: Must have columns for title, company, location, description.

---

## 3️⃣ FREE AGENTS TAB

### 📋 Manage Agents Sub-tab

### 🎯 Purpose
Build and manage your roster of Free Agents, configure their search preferences, and track their portal links.

---

### 🔍 Airtable Lookup Section

**Purpose**: Import agents from your Airtable database.

**Steps**:
1. Type agent's name, UUID, or email in **Search Airtable** box
2. Select **Search by**: name, uuid, or email
3. Click **🔎 Search**
4. Review results
5. Select agent from **Select Agent** dropdown
6. Click **Add Selected Agent** to import

💡 **Pro tip**: You can also **📋 Copy Portal Link** directly from search results if agent is already in Opptek.

---

### ➕ Manual Entry Section

**Purpose**: Add a new Free Agent manually (without Airtable).

#### **Required Fields**:
- **Free Agent Name** - Full name (e.g., "John Smith")
- **Email** - Contact email
- **City** - Current city (e.g., "Dallas")

#### **Optional Fields**:
- **Agent UUID** - Links to Airtable record if you have it
- **State** - Default is "TX"

#### **Search Configuration** (sets their portal preferences):

**Location/Market** - Where to search for jobs (dropdown of all markets)

**Route Type**:
- **both** - Show local AND regional/OTR jobs
- **local** - Home daily only
- **regional** - Multi-day trips only

**Fair Chance Only** (checkbox):
- ✅ Only show jobs open to people with records
- ⬜ Show all jobs

**Maximum Jobs** - How many jobs in their portal (1-100, default 25)

**Experience Level**:
- **both** - All experience levels
- **no_experience** - Entry-level only
- **experienced** - Experienced positions only

**Classifier Type**:
- **CDL Traditional** - For drivers
- **Career Pathways** - For warehouse-to-driver progression

**Pathway Preferences** (if Career Pathways selected):
- Check boxes for 8 pathway types
- Select 2-3 most relevant for the agent

**➕ Add Manual Agent** - Creates the agent and auto-generates their portal link

💡 **Portal link is created automatically** - no extra steps needed.

---

### 📊 Bulk Import Section

Upload a CSV to import multiple Free Agents at once.

**CSV Columns Required**:
- name, email, city, state, market, route_type, fair_chance_only, max_jobs

**🚀 Import Free Agents** - Processes the CSV

💡 **Great for onboarding** 10+ agents quickly.

---

### 📋 Agent Management Table

**Purpose**: The main control panel for all your Free Agents.

#### **Table Controls** (above table):

**👻 Show Deleted** (checkbox):
- ✅ Include soft-deleted agents in table
- ⬜ Show only active agents

**🔄 Also refresh analytics** (checkbox):
- ✅ Update engagement metrics (clicks, applications) when refreshing
- ⬜ Just refresh agent data

**🔄 Refresh** button - Reloads agents from database

**🔄 Sync Airtable** button - Syncs placement/employment status from Airtable

💡 **Use Sync Airtable** weekly to keep employment status current.

---

#### **Table Columns Explained**:

**Basic Info** (read-only):
- **Name** - Free Agent's full name
- **Placement** - Current placement status (from Airtable)
- **Employment** - Current employment status (from Airtable)
- **Coaches** - Assigned coaches (comma-separated)
- **City** - Current city
- **State** - Current state
- **ZIP** - ZIP code

---

**Search Settings** (editable):

**Radius (mi)** - Search radius dropdown:
- Options: 0, 10, 25, 50, 75, 100, 150, 200 miles

**Market** - Market dropdown (all standard markets)

**Route** - Route type preference:
- **both** - Local and regional/OTR
- **local** - Home daily
- **regional** - Multi-day trips

**Fair Chance** (checkbox):
- ✅ Fair chance jobs only
- ⬜ All jobs

**Max Jobs** - Jobs per portal:
- Options: 5, 10, 15, 20, 25, 30, 50, 75, 100

**Quality** - Quality filter:
- **all** - All quality ratings
- **good_only** - Only "good" rated jobs
- **good_and_soso** - Good and so-so rated

**Lookback** - How far back to search:
- Options: 3d, 7d, 14d, 30d, 60d, 90d
- Default: 7d (7 days)

**Show Prepared For** (checkbox):
- ✅ Show "Prepared for [Agent Name]" on portal
- ⬜ Generic header

---

**Pathway Preferences** (individual checkboxes):

These 8 checkboxes control which pathway types appear in the agent's portal:

- **CDL** (CDL Jobs) - Traditional CDL driving positions
- **Dock→CDL** (Dock→Driver) - Dock worker to driver progression
- **Training** (CDL Training) - Company-sponsored CDL training programs
- **Warehouse→CDL** (Warehouse→Driver) - Warehouse to driving transition
- **Logistics** - Logistics and supply chain roles
- **Non-CDL** - Delivery/courier (no CDL required)
- **Warehouse** - Warehouse positions
- **Stepping Stone** - Entry-level stepping stone roles

💡 **For most agents**: Check CDL, Dock→CDL, and Training.

---

**Analytics** (read-only):

- **Clicks (All)** - Total clicks all-time on their portal link
- **Clicks (14d)** - Clicks in last 14 days
- **Apps (All)** - Total applications all-time
- **Apps (14d)** - Applications in last 14 days
- **Score** - Engagement score (calculated metric)
- **Activity** - Last activity summary
- **Last Applied** - Date of most recent application

💡 **Track Clicks (14d)** to identify engaged agents.

---

**Links & Admin**:

- **Portal Link** - Short.io tracked link (e.g., `https://opptek.link/xyz789`)
- **Admin Portal** - Clickable link to view their portal
- **Created** - Date agent was added to Opptek
- **Delete** (checkbox) - Mark for deletion

---

#### **Action Buttons** (below table):

**💾 Save Changes** (Primary button):
- Saves all edits to Supabase
- **Automatically regenerates portal links** for any agents with changed settings
- Updates Short.io tracking

💡 **This is the most important button** - always click after editing.

**↩️ Discard Changes** - Reverts all unsaved edits

**🗑️ Confirm Delete Selected** - Soft-deletes agents with Delete checkbox checked

**🔄 Confirm Restore Selected** - Restores soft-deleted agents

---

### 🎯 Track Applications Sub-tab

### 🎯 Purpose
Monitor individual Free Agent job applications and track hiring outcomes.

---

#### **Free Agent Selection**:
1. **Select Free Agent** - Dropdown (alphabetical by name)
2. **🔄 Refresh Data** - Updates application history

---

#### **Agent Activity Summary**:
Shows for selected agent:
- Total applications count
- Date range of applications (first to last)
- Click-through metrics

💡 **Use this** to identify highly engaged agents.

---

#### **Edit Agent Settings**:
Quick-edit panel for agent preferences:
- Market/Location
- Route Type
- Fair Chance Only
- Maximum Jobs
- Experience Level

**💾 Save Changes & Regenerate Portal Link** - Updates settings and portal

💡 **Faster than editing in table** when you just need to tweak one agent.

---

#### **Application History Table**:

**Time Period Filter**:
- Select days: 7, 14, 30, 60, 90, 180, 365
- Default: 60 days

**📥 Export CSV** - Downloads application history

**Table Columns**:
- **ID** - Application ID (read-only)
- **Applied Date** - When agent applied (read-only)
- **Status** (editable dropdown):
  - Applied
  - Interviewing
  - Offer
  - Hired
  - Rejected
  - Ghosted
  - Withdrawn
- **Company** - Employer name (read-only)
- **Job Title** - Position title (read-only)

**💾 Save Status Changes** - Updates application statuses

💡 **Update statuses regularly** to track pipeline progress.

---

#### **Success Tracking**:

When an agent gets hired:
1. Select **Company** from dropdown (companies they applied to)
2. Click **✅ Mark as Success**
3. Confirms hiring in database

💡 **Always mark successes** - this is how we prove ROI!

---

## 4️⃣ COACH ANALYTICS TAB

### 🎯 Purpose
Track your personal performance and compare with other coaches.

---

### 📊 Your Performance Metrics (4-column display):

- **Total Clicks** - All-time clicks on your portal links
- **Unique Agents Engaged** - How many different agents clicked
- **Avg Clicks/Agent** - Engagement per agent
- **Job Quality Breakdown** - Count of "good" rated jobs you've found

💡 **Track Avg Clicks/Agent** - higher is better engagement.

---

### 👥 Coach Comparison:

**Select Coaches to Compare** - Multiselect (all non-admin coaches)

Shows comparison table:
- Coach name
- Total agents managed
- Total clicks
- Click-through rate
- Quality job percentage

💡 **Learn from top performers** - what are they doing differently?

---

## 5️⃣ MARKET ANALYTICS TAB

**Purpose**: Analyze job market trends, geographic coverage, and market penetration.

💡 **Use this** to identify underserved markets or hot hiring areas.

---

## 6️⃣ COMPANIES TAB

**Purpose**: Track company hiring patterns, job quality, and agent placements.

**Columns**:
- Company name
- Total jobs posted
- Quality job percentage
- Agent applications
- Successful placements

💡 **Use this** to build relationships with high-quality employers.

---

## 7️⃣ ADMIN PANEL TAB

**Admin role required**

### 🔧 Manage Coaches Section

#### **Add New Coach**:

**Form Fields**:
- **Username** - Login username (e.g., "john.smith")
- **Full Name** - Display name (e.g., "John Smith")
- **Email** - Contact email
- **Password** - Initial password (min 6 chars)
- **Test Account** (checkbox) - Memory-only, no API calls
- **🔑 Create as Admin** (checkbox) - Full system access

**Add Coach** - Creates the coach account

💡 **Test Account** is useful for training new coaches.

---

#### **Existing Coaches**:

**Per-Coach Permission Checkboxes**:
- **PDF Generation** - Can generate PDF reports
- **CSV Export** - Can export CSV files
- **Airtable Sync** - Can sync with Airtable
- **Supabase Sync** - Can sync with Supabase
- **Custom Locations** - Can use custom location searches
- **Google Jobs Access** - Can use Google Jobs API (99% savings)
- **Full Mode Access** - Can search 1000 jobs
- **Edit Filters** - Can modify business rules
- **Pull Fresh Jobs** - Can run fresh API searches
- **Force Fresh Classification** - Can re-run AI classification
- **Batches & Scheduling Access** - Can schedule batch jobs
- **🔑 Admin Role** - Full system access

**Monthly Budget ($)** - API spending limit

**💾 Save Permissions** - Updates coach permissions

---

**Password Reset**:
- **New Password** - New password (min 6 chars)
- **Confirm Password** - Confirmation
- **🔄 Reset Password** - Changes coach password

**🗑️ Delete [Coach Name]** - Removes coach account

---

### ⚙️ System Settings Section

**🧪 Test All APIs** - Validates all API connections:
- Supabase
- OpenAI
- Indeed
- Google Jobs
- Outscraper
- Short.io

💡 **Run this** if searches are failing to diagnose issues.

---

## 🔑 Understanding Permissions

**Permission Levels**:

**All Coaches**:
- View Job Search tab
- View Free Agents tab
- View Coach Analytics tab
- Memory-only searches

**With `can_pull_fresh_jobs`**:
- Indeed Fresh searches
- API credit usage

**With `can_access_batches`**:
- Batches & Scheduling tab
- Automated search scheduling

**With `can_access_google_jobs`**:
- Google Jobs searches (99% cheaper)

**Admin Role**:
- All permissions
- Admin Panel access
- User management
- System settings

💡 **Contact your admin** to request additional permissions.

---

## 💡 Best Practices

### Daily Workflow:
1. **Check Coach Analytics** - Review yesterday's engagement
2. **Run Memory Only searches** - Update active agent portals (zero cost)
3. **Review Track Applications** - Update application statuses
4. **Respond to agents** - Follow up on clicks but no applications

### Weekly Workflow:
1. **Run Fresh Indeed searches** - Refresh job database for your markets
2. **Sync Airtable** - Update employment statuses
3. **Review Market Analytics** - Identify trends
4. **Compare coach performance** - Learn from top performers

### Monthly Workflow:
1. **Review API budget** - Check spending vs allocation
2. **Audit Free Agents table** - Remove inactive agents
3. **Update pathway preferences** - Adjust based on hiring trends
4. **Export success metrics** - Track ROI for leadership

---

## 🆘 Common Issues & Solutions

### "No jobs found in memory"
**Solution**: Run a Fresh Indeed search first to populate the cache.

### "Permission denied"
**Solution**: Contact admin to request the required permission.

### "Agent portal link not working"
**Solution**: Check that "Generate Portal Link" was enabled. Re-save agent in table to regenerate.

### "Classifications seem wrong"
**Solution**: Check classifier type (CDL vs Pathway). Try Force Fresh Classification (if permitted).

### "Batch job not running"
**Solution**: Check Scheduled Batches table for errors. Verify schedule time is in 24-hour format.

---

## 📚 Related Documentation

- **Memory-Only Search Tutorial** - Step-by-step guide for zero-cost searches
- **Fresh Search Tutorial** - How to run Indeed/Outscraper searches
- **Free Agent Management Tutorial** - Complete agent lifecycle guide
- **Custom Location Search Tutorial** - Advanced location targeting
- **Loom Training Videos** - Video walkthroughs of key features

---

**Questions?** Contact your admin or refer to the full technical documentation in `CLAUDE.md`.

---

*Opptek: Cutting through the noise to connect Free Agents with opportunities that matter.*
