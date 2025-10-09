# Free Agent Management Tutorial

**Complete Lifecycle Guide: Add, Configure, Track, and Succeed**

---

## 🎯 What Is Free Agent Management?

Free Agent Management in Opptek is the process of:
1. **Adding** Free Agents to your roster
2. **Configuring** their job search preferences
3. **Generating** personalized portal links (automatic!)
4. **Tracking** engagement and applications
5. **Monitoring** success metrics and placements

**The goal**: Each Free Agent gets a personalized, continuously-updated job portal that shows only relevant opportunities.

---

## 📋 Free Agent Lifecycle

```
Add Agent → Configure Preferences → Auto-Generate Portal Link
    ↓
Share Link → Agent Clicks → Agent Applies
    ↓
Track Applications → Update Status → Mark as Hired
    ↓
Success! (ROI proven)
```

---

## 🚀 Part 1: Adding Free Agents

### Method 1: Airtable Import (Recommended)

**Use case**: Agent already exists in your Airtable CRM.

#### Step-by-Step:

1. Click **👥 Free Agents** tab
2. Click **📋 Manage Agents** sub-tab
3. Locate **Airtable Lookup** section

4. **Search Airtable** field: Type agent's name
   - Example: "Michael Torres"

5. **Search by** dropdown: Select "name"

6. Click **🔎 Search** button

7. Review search results (shows matching records)

8. **Select Agent** dropdown: Choose the correct agent

9. **Configure search preferences** (we'll cover this in Part 2)

10. Click **Add Selected Agent** button (primary, green)

✅ **Result**: Agent added to your roster with Airtable UUID linked!

💡 **Portal link generates automatically** when you save preferences.

---

### Method 2: Manual Entry (Quick Add)

**Use case**: Agent not in Airtable yet, or you want to add quickly.

#### Step-by-Step:

1. Click **👥 Free Agents** tab
2. Click **📋 Manage Agents** sub-tab
3. Locate **Manual Entry** section

4. **Required fields:**
   - **Free Agent Name**: "Jessica Martinez"
   - **Email**: "jessica.m@example.com"
   - **City**: "Houston"

5. **Optional fields:**
   - **Agent UUID**: (leave blank unless you have it)
   - **State**: "TX" (auto-filled)

6. **Configure search preferences** (covered in Part 2)

7. Click **➕ Add Manual Agent** button (primary, green)

✅ **Result**: Agent added to your roster!

💡 **Portal link generates automatically** on save.

---

### Method 3: Bulk Import (CSV)

**Use case**: Onboarding 10+ agents at once.

#### Step-by-Step:

1. Click **👥 Free Agents** tab
2. Click **📋 Manage Agents** sub-tab
3. Locate **Bulk Import** section

4. **Prepare CSV file** with these columns:
   ```csv
   name,email,city,state,market,route_type,fair_chance_only,max_jobs
   John Smith,john@example.com,Dallas,TX,Dallas-Fort Worth,both,false,25
   Sarah Johnson,sarah@example.com,Houston,TX,Houston,local,true,20
   Mike Williams,mike@example.com,Austin,TX,Austin,regional,false,30
   ```

5. Click **Choose File** and select your CSV

6. Click **🚀 Import Free Agents** button

✅ **Result**: All agents imported with portal links auto-generated!

💡 **Great for team onboarding** - add 50+ agents in seconds.

---

## ⚙️ Part 2: Configuring Search Preferences

**Critical step**: These settings determine what jobs appear in each agent's portal.

---

### Location & Market Settings

#### **Location/Market** dropdown
- Select from standard markets (Dallas-Fort Worth, Houston, etc.)
- Or use custom location if permitted

💡 **Choose the market closest to agent's city** for best results.

**Example**:
- Agent lives in Plano, TX → Select "Dallas-Fort Worth"
- Agent lives in Katy, TX → Select "Houston"

---

### Route Type Preferences

#### **Route Type** dropdown
- **both** - Show local AND regional/OTR jobs
- **local** - Home daily only (local routes)
- **regional** - Multi-day trips (regional/OTR)

💡 **Ask your agent**: "Do you need to be home every night?"
- Yes → **local**
- No/flexible → **both**
- Long haul only → **regional**

**Example**:
- Agent has kids, needs to be home nightly → **local**
- Agent is single, willing to travel → **both**

---

### Fair Chance Filter

#### **Fair Chance Only** checkbox
- ✅ **Checked**: Only show jobs marked "fair chance" (open to people with records)
- ⬜ **Unchecked**: Show all jobs

💡 **Check this** if agent has criminal background.

**Impact**: May reduce job pool by 30-50%, but ensures relevant opportunities only.

---

### Maximum Jobs Per Portal

#### **Maximum Jobs** dropdown
- Options: 5, 10, 15, 20, 25, 30, 50, 75, 100
- Default: **25**
- Recommended: **15-20**

💡 **Quality over quantity**: Agents engage more with 15 great jobs than 100 mediocre ones.

**Guidelines**:
- **VIP agents**: 10-15 jobs (highly curated)
- **Standard agents**: 20-25 jobs (balanced)
- **High-volume markets**: 30-50 jobs (comprehensive)

---

### Experience Level Filter

#### **Experience Level** dropdown
- **both** - All experience levels
- **no_experience** - Entry-level only
- **experienced** - Experienced positions only

💡 **Match to agent's background**:
- No CDL yet → **no_experience**
- CDL with 2+ years → **experienced**
- Open to any → **both**

---

### Classifier Type

#### **Classifier Type** dropdown
- **CDL Traditional** - For drivers (good/so-so/bad ratings)
- **Career Pathways** - For warehouse-to-driver progression

💡 **Choose based on agent's current role**:
- Has CDL, wants driving job → **CDL Traditional**
- Warehouse worker, wants to get CDL → **Career Pathways**

---

### Pathway Preferences (Career Pathways only)

**If you selected Career Pathways classifier**, you'll see 8 checkboxes:

**Select 2-3 most relevant pathways for your agent:**

#### **CDL Jobs** (cdl_pathway)
- ✅ Check for: Traditional CDL driving positions
- Direct CDL opportunities

#### **Dock→Driver** (dock_to_driver)
- ✅ Check for: Dock workers who want to transition to driving
- Dock-to-driver progression programs

#### **CDL Training** (internal_cdl_training)
- ✅ Check for: Anyone wanting company-sponsored CDL training
- Company pays for CDL school

#### **Warehouse→Driver** (warehouse_to_driver)
- ✅ Check for: Warehouse workers wanting to drive
- General warehouse-to-driving transition

#### **Logistics** (logistics_pathway)
- ✅ Check for: Supply chain, dispatch, logistics roles
- Non-driving logistics positions

#### **Non-CDL** (non_cdl_driver)
- ✅ Check for: Delivery, courier, box truck (no CDL)
- Driving jobs that don't require CDL

#### **Warehouse** (warehouse)
- ✅ Check for: Pure warehouse positions
- Forklift, picking, packing roles

#### **Stepping Stone** (stepping_stone)
- ✅ Check for: Entry-level roles that lead somewhere
- First step in career progression

💡 **Most common combinations**:
- **Dock worker**: ✅ Dock→Driver, ✅ CDL Training, ✅ Warehouse
- **Warehouse worker**: ✅ Warehouse→Driver, ✅ CDL Training, ✅ Logistics
- **No experience**: ✅ CDL Training, ✅ Non-CDL, ✅ Stepping Stone

---

### Additional Portal Settings

#### **Quality Filter** (set during search)
- Controlled when you run searches (good/so-so/bad filter)
- Not editable in agent table

#### **Lookback Period**
- How far back to search for jobs
- Options: 3d, 7d, 14d, 30d, 60d, 90d
- Default: **7d** (recommended)

#### **Show Prepared For** checkbox
- ✅ Checked: Portal shows "Prepared for [Agent Name]"
- ⬜ Unchecked: Generic header

💡 **Personal touch**: Check this for 1-on-1 coaching relationships.

---

## 💾 Part 3: Saving and Portal Link Generation

### The Revolutionary Auto-Generation System

**When you click 💾 Save Changes**:
1. Agent preferences saved to Supabase
2. **Portal link automatically generates** (or updates if it exists)
3. Short.io tracked link created
4. Link appears in **Portal Link** column
5. **No manual steps required!**

---

### Step-by-Step: Saving an Agent

1. **Configure all preferences** (location, route, fair chance, max jobs, etc.)

2. Click **➕ Add Manual Agent** or **Add Selected Agent** button

3. ✅ **Agent appears in table below** with:
   - All configured settings
   - **Portal Link** column populated
   - Created timestamp

4. **Copy portal link** from table:
   - Click link text to select
   - Ctrl+C / Cmd+C to copy
   - Example: `https://opptek.link/xyz789`

---

## 📋 Part 4: Managing Your Agent Roster

### The Agent Management Table

**Location**: 👥 Free Agents tab → 📋 Manage Agents sub-tab

**Purpose**: Central dashboard for all your Free Agents.

---

### Table Controls (Above Table)

#### **👻 Show Deleted** checkbox
- ✅ Checked: Include soft-deleted agents
- ⬜ Unchecked: Active agents only

💡 **Use this** to restore accidentally deleted agents.

---

#### **🔄 Also refresh analytics** checkbox
- ✅ Checked: Update click/application counts when refreshing
- ⬜ Unchecked: Just refresh agent data

💡 **Check this** when reviewing engagement metrics.

---

#### **🔄 Refresh** button
- Reloads agents from Supabase
- Updates table with latest data

💡 **Click this** if another coach added agents.

---

#### **🔄 Sync Airtable** button
- Syncs placement/employment status from Airtable
- Updates **Placement** and **Employment** columns

💡 **Run this weekly** to keep status current.

---

### Table Columns Explained

**Read-only Info:**
- **Name** - Free Agent's full name
- **Placement** - Current placement status (from Airtable)
- **Employment** - Current employment status (from Airtable)
- **Coaches** - Assigned coaches
- **City**, **State**, **ZIP** - Location info

**Editable Settings:**
- **Radius** - Search radius (0-200 miles)
- **Market** - Target market dropdown
- **Route** - Route type (both/local/regional)
- **Fair Chance** - Fair chance filter checkbox
- **Max Jobs** - Jobs per portal (5-100)
- **Quality** - Quality filter (all/good_only/good_and_soso)
- **Lookback** - Time period (3d-90d)
- **Show Prepared For** - Personalization checkbox

**Pathway Checkboxes** (8 individual boxes):
- CDL, Dock→CDL, Training, Warehouse→CDL, Logistics, Non-CDL, Warehouse, Stepping Stone

**Analytics** (read-only):
- **Clicks (All)** - Total clicks all-time
- **Clicks (14d)** - Clicks in last 14 days
- **Apps (All)** - Total applications
- **Apps (14d)** - Applications in last 14 days
- **Score** - Engagement score (1-10 scale)
- **Activity** - Last activity summary
- **Last Applied** - Date of most recent application

**Links & Admin:**
- **Portal Link** - Short.io tracked link
- **Admin Portal** - Clickable link to view portal
- **Created** - Date agent was added
- **Delete** - Checkbox for deletion

---

### Editing Agents in the Table

**To edit an agent:**

1. Locate the agent row in table

2. Click into any **editable field** (dropdowns, checkboxes, etc.)

3. Make your changes:
   - Change route type from "both" to "local"
   - Increase max jobs from 20 to 30
   - Check additional pathway preferences

4. **Changes highlight in yellow** (unsaved state)

5. Click **💾 Save Changes** button (below table)

6. ✅ **Portal link auto-regenerates!** (if settings changed)

💡 **No auto-save**: Changes only persist when you click Save Changes.

---

### Updating Multiple Agents

**Batch editing workflow:**

1. Edit Agent #1 settings (route, max jobs, etc.)
2. Edit Agent #2 settings
3. Edit Agent #3 settings
4. ... (edit as many as needed)
5. Click **💾 Save Changes** ONCE
6. ✅ **All agents saved** and portal links regenerated!

💡 **Efficient**: Update 10 agents in 2 minutes.

---

### Deleting Agents (Soft Delete)

**To delete an agent:**

1. Check the **Delete** checkbox for the agent
2. Scroll to bottom of table
3. Click **🗑️ Confirm Delete Selected** button
4. Agent moved to "deleted" status (soft delete)

💡 **Soft delete**: Agent still in database, just hidden.

---

**To restore a deleted agent:**

1. Check **👻 Show Deleted** checkbox (above table)
2. Deleted agents appear with strikethrough
3. Check agents to restore
4. Click **🔄 Confirm Restore Selected** button

---

## 📊 Part 5: Tracking Applications

**Purpose**: Monitor individual Free Agent engagement, applications, and hiring outcomes.

---

### Accessing Application Tracking

1. Click **👥 Free Agents** tab
2. Click **🎯 Track Applications** sub-tab

---

### Selecting an Agent

1. **Select Free Agent** dropdown: Choose agent by name
   - Alphabetical sorting

2. Click **🔄 Refresh Data** button (optional)

---

### Agent Activity Summary

**Displays for selected agent:**
- Total applications count (all-time)
- Date range of applications (first to last)
- Click-through metrics (clicks vs applications)

💡 **High clicks, low applications?** Agent may need coaching on how to apply.

---

### Edit Agent Settings (Quick Edit)

**Quick-edit panel** for agent preferences:
- **Market/Location** - Change search market
- **Route Type** - Update route preference
- **Fair Chance Only** - Toggle filter
- **Maximum Jobs** - Adjust portal size
- **Experience Level** - Change experience filter

**💾 Save Changes & Regenerate Portal Link** button:
- Saves edits
- Auto-regenerates portal link
- Faster than editing in main table

💡 **Use this** when reviewing applications with agent on the phone.

---

### Application History Table

**Displays all applications** for selected agent.

#### **Time Period Filter** dropdown
- Select days: 7, 14, 30, 60, 90, 180, 365
- Default: 60 days

💡 **Adjust based on activity**: Active agents (30 days), slower markets (90 days).

---

#### **📥 Export CSV** button
- Downloads full application history
- Use for reporting, analysis, or sharing with leadership

---

#### **Application Table Columns**

**Read-only:**
- **ID** - Application ID (unique)
- **Applied Date** - When agent applied
- **Company** - Employer name
- **Job Title** - Position title

**Editable:**
- **Status** - Dropdown (see below)

#### **Status Options:**
- **Applied** - Initial application submitted (default)
- **Interviewing** - Agent is interviewing
- **Offer** - Agent received offer
- **Hired** - Agent was hired! ✅
- **Rejected** - Application rejected
- **Ghosted** - No response from employer
- **Withdrawn** - Agent withdrew application

---

#### **Updating Application Status**

**Workflow:**

1. Select agent from dropdown
2. Review applications in table
3. Click **Status** dropdown for an application
4. Select new status (e.g., "Interviewing")
5. Repeat for other applications as needed
6. Click **💾 Save Status Changes** button

✅ **Statuses updated** in Supabase!

💡 **Update regularly** (weekly check-ins with agents).

---

### Success Tracking (Hiring)

**When an agent gets hired:**

1. Scroll to **Success Tracking** section
2. **Company** dropdown: Select the company that hired them
   - Dropdown shows companies from their application history
3. Click **✅ Mark as Success** button
4. Confirmation: "🎉 Success recorded for [Agent Name] at [Company]!"

✅ **Hiring recorded** in database!

💡 **This is how we prove ROI** - always mark successes!

---

## 📈 Part 6: Monitoring Engagement Metrics

### Coach Analytics View

1. Click **📊 Coach Analytics** tab

**Your Performance metrics:**
- **Total Clicks** - All-time clicks on your portal links
- **Unique Agents Engaged** - How many agents clicked
- **Avg Clicks/Agent** - Engagement per agent
- **Quality Job Breakdown** - Good jobs percentage

💡 **Track Avg Clicks/Agent** - Target: 3-5 clicks per agent (good engagement).

---

### Individual Agent Analytics (in Table)

**Analytics columns** (Free Agents → Manage Agents table):
- **Clicks (All)** - Lifetime clicks
- **Clicks (14d)** - Recent engagement (last 14 days)
- **Apps (All)** - Total applications
- **Apps (14d)** - Recent applications
- **Score** - Engagement score (1-10)
- **Activity** - Last activity timestamp
- **Last Applied** - Most recent application date

---

### Engagement Patterns to Watch

**🟢 High Engagement**:
- Clicks (14d): 3-5+
- Apps (14d): 1-3+
- Score: 7-10
- **Action**: Keep sending fresh portals!

**🟡 Medium Engagement**:
- Clicks (14d): 1-2
- Apps (14d): 0-1
- Score: 4-6
- **Action**: Check in with agent, adjust preferences

**🔴 Low Engagement**:
- Clicks (14d): 0
- Apps (14d): 0
- Score: 1-3
- **Action**: Re-engage conversation, verify contact info

---

## ✅ Part 7: Best Practices

### Weekly Agent Management Routine

**Monday Morning (30 minutes):**
1. **🔄 Sync Airtable** - Update placement/employment status
2. **Run Fresh Search** - Populate cache for the week (Dallas, Houston, etc.)
3. **Review engagement** - Check Clicks (14d) column, identify low-engagement agents

**Tuesday-Friday (15 minutes/day):**
1. **Run Memory-Only searches** - Zero-cost portal updates
2. **Update high-engagement agents** - Send fresh portals to active agents
3. **Follow up on applications** - Text agents who clicked but didn't apply

**Friday Afternoon (20 minutes):**
1. **Track Applications** - Update application statuses for all agents
2. **Mark successes** - Record any hires from the week
3. **Coach Analytics review** - Check your weekly performance metrics

---

### Agent Preference Optimization

**Start conservative, then adjust:**

**Week 1:**
- Max Jobs: 20
- Route Type: both
- Fair Chance: (as needed)
- Quality: good_and_soso

**Week 2-3: Monitor engagement:**
- High clicks, high apps → Keep settings
- High clicks, low apps → Reduce max jobs to 15 (higher quality)
- Low clicks → Expand to 30 jobs (more variety)

**Week 4+: Fine-tune:**
- Narrow route type if agent only applies to local jobs
- Adjust pathway preferences based on application patterns

---

### Portal Link Management

**Best practices:**

1. **Always generate portal links** (check "Generate Portal Link")
2. **Include in every agent interaction** (text, email, phone follow-up)
3. **Regenerate weekly** (fresh jobs keep agents engaged)
4. **Track clicks** (analytics show who's engaged)

**Portal link message templates:**

**Initial contact:**
```
Hi [Name]! I created a personalized job portal for you with 20
quality CDL jobs in Dallas. Check it out: https://opptek.link/abc123

Let me know what you think!
```

**Weekly update:**
```
Hey [Name], just updated your job portal with fresh positions from
this week. Still 20 great jobs, but 8 are brand new!

https://opptek.link/abc123
```

**Follow-up after click:**
```
Saw you checked out the portal - awesome! Did you see anything
interesting? Let me know if you have questions about any of the jobs.
```

---

## 🆘 Troubleshooting

### Issue: "Portal link not generating"

**Cause**: "Generate Portal Link" not checked during search, or permissions issue.

**Solution**:
1. Go to Free Agents → Manage Agents table
2. Edit agent settings (any small change)
3. Click **💾 Save Changes**
4. Portal link auto-generates

---

### Issue: "Agent says portal shows wrong jobs"

**Cause**: Preferences not configured correctly.

**Solution**:
1. Review agent preferences in table
2. Verify: market, route type, fair chance, pathway preferences
3. Edit settings to match agent's actual needs
4. Click **💾 Save Changes** (portal regenerates)
5. Share new link with agent

---

### Issue: "Can't find agent in Airtable search"

**Cause**: Agent not in Airtable, or search term doesn't match.

**Solution**:
1. Try searching by UUID instead of name
2. Or use **Manual Entry** to add agent
3. Enter Airtable UUID later when you get it

---

### Issue: "Clicks not tracking"

**Cause**: Short.io integration issue, or portal link not shared correctly.

**Solution**:
1. Verify portal link starts with `https://opptek.link/`
2. Test link yourself (click it) - should redirect to portal
3. Check Coach Analytics after 5 minutes - clicks should appear
4. If still not tracking, regenerate portal link

---

### Issue: "Engagement is low across all agents"

**Causes & Solutions**:

**Cause 1**: Portal links not shared consistently
- **Solution**: Text every agent weekly with fresh link

**Cause 2**: Jobs not relevant
- **Solution**: Review agent preferences, adjust filters

**Cause 3**: Agents already employed
- **Solution**: Sync Airtable, verify employment status

**Cause 4**: Too many jobs (overwhelming)
- **Solution**: Reduce max jobs from 30 to 15

---

## 🎓 Practice Exercise

**Complete Free Agent lifecycle:**

1. **Add an agent** (Manual Entry):
   - Name: "Carlos Rodriguez"
   - Email: "carlos.r@example.com"
   - City: "San Antonio"

2. **Configure preferences**:
   - Market: "San Antonio"
   - Route Type: "both"
   - Fair Chance: checked
   - Max Jobs: 20
   - Classifier: "CDL Traditional"

3. **Save agent** (portal link auto-generates)

4. **Copy portal link** from table

5. **Run Memory-Only search**:
   - San Antonio market
   - CDL driver
   - Generate portal link
   - HTML preview enabled

6. **Share link** (simulate via notes)

7. **Track application** (Track Applications sub-tab):
   - Select Carlos Rodriguez
   - Manually add test application (if system allows)
   - Update status to "Interviewing"

8. **Mark success** (if hired):
   - Select company
   - Click Mark as Success

**Expected outcome**: Complete agent lifecycle in 10 minutes.

---

**Congratulations! You're now a Free Agent management expert.**

💡 **Remember**: The table is your command center. Update preferences → Save Changes → Portal links auto-regenerate → Share with agents → Track engagement → Repeat weekly.

---

*Opptek: Cutting through the noise to connect Free Agents with opportunities that matter.*
