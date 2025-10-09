# Loom Training Video Scripts

**5 Video Scripts for Comprehensive Coach Training**

---

## 🎬 Video Production Guidelines

**Recording Setup:**
- Use Loom screen recording (loom.com)
- Record full screen + webcam (build trust)
- Target length: 5-8 minutes per video
- Use clear, conversational tone
- Pause briefly after each major action (allows viewers to process)

**Editing:**
- Add chapter markers for easy navigation
- Include captions for accessibility
- Add arrows/highlights for key buttons

**Delivery:**
- Upload to Loom
- Share links in coach onboarding materials
- Add to internal documentation wiki

---

## 📹 Video 1: "Welcome to Opptek - Platform Overview"
**Length: 6-7 minutes**

### Script

**[INTRO - 30 seconds]**
- Show Opptek dashboard

"Hey everyone, welcome to Opptek! I'm [Your Name], and I'm excited to show you around the platform."

"The job market is noisy - our Free Agents don't have time to sift through thousands of irrelevant job postings. That's what Opptek is for. We use AI to cut through the noise and connect our folks with quality opportunities."

---

**[NAVIGATION - 1 minute]**
- Hover over each tab

"Let me give you a quick tour of the main tabs:"

"**Job Search** - This is your command center. You'll spend most of your time here finding jobs for your agents."

"**Batches & Scheduling** - Automate weekly searches. Set it and forget it." *(hover)*

"**Free Agents** - Your roster. Manage agent preferences and track applications." *(click tab)*

"**Coach Analytics** - Your performance dashboard. See clicks, applications, and success rates." *(click tab)*

"**Market Analytics** - Analyze hiring trends across cities." *(click tab)*

"**Companies** - Track which employers are hiring the most." *(click tab)*

---

**[KEY CONCEPT: MEMORY VS FRESH - 2 minutes]**
- Show Job Search tab

"The first thing to understand: Opptek has two search modes."

**Memory-Only** *(click button)*:
"Memory-Only searches our cache. It's instant - 3 to 10 seconds - and costs zero dollars. This is what you'll use daily to update your agents."

**Indeed Fresh** *(click button)*:
"Fresh Search calls the Indeed API. It takes 60 to 90 seconds and costs about 10 cents per 100 jobs. But it populates the cache with the latest postings."

"Here's the magic: Run a Fresh Search on Monday to populate the cache. Then use Memory-Only Tuesday through Friday - zero cost, fresh jobs."

---

**[THE 8-STAGE PIPELINE - 1.5 minutes]**
- Show diagram or pipeline in action

"When you run a search, jobs go through 8 stages:"

1. "**Ingestion** - We fetch jobs from Indeed, Google Jobs, or Outscraper."
2. "**Normalization** - Map to our 100+ field schema."
3. "**Business Rules** - Quality filtering."
4. "**Deduplication** - Remove duplicates across all sources."
5. "**AI Classification** - OpenAI GPT-4o-mini rates jobs as good, so-so, or bad."
6. "**Routing** - Final job selection."
7. "**Link Tracking** - Generate Short.io tracked links for analytics."
8. "**Data Storage** - Save to Supabase cache."

"This all happens automatically. You just click a button and wait 60 seconds."

---

**[PORTAL LINKS - 1.5 minutes]**
- Show HTML preview example

"The end result: a personalized portal link for your Free Agent."

*(show portal preview)*

"This is what they see - clean, mobile-optimized, jobs ranked by quality. Each job has an AI summary explaining why it's a good match."

"The link is tracked through Short.io, so you'll know when they click and when they apply."

*(show portal link)*

"You text or email this link to your agent. They click it, browse jobs, and apply - all tracked in your analytics."

---

**[NEXT STEPS - 30 seconds]**
"Alright, that's the overview! In the next videos, I'll walk you through:"

- "**Video 2**: Running your first Memory-Only search"
- "**Video 3**: Fresh Search walkthrough"
- "**Video 4**: Free Agent management"
- "**Video 5**: Tracking applications and success"

"Let's dive into Video 2 - Memory-Only searches. See you there!"

**[END]**

---

## 📹 Video 2: "Memory-Only Search Walkthrough"
**Length: 7-8 minutes**

### Script

**[INTRO - 20 seconds]**
- Show Job Search tab

"Welcome back! In this video, I'm going to walk you through a complete Memory-Only search from start to finish."

"Memory-Only is your daily workhorse - instant results, zero cost. Let's do one together."

---

**[STEP 1: CONFIGURE LOCATION - 1 minute]**
- Click Job Search tab

"First, select your location."

*(click Location dropdown)*

"For standard markets, use the dropdown - Dallas-Fort Worth, Houston, Austin, etc."

*(select Dallas-Fort Worth)*

"I'm choosing Dallas-Fort Worth for this example."

---

**[STEP 2: SEARCH PARAMETERS - 1.5 minutes]**
- Show search configuration section

"**Search Mode**: I'll use Sample - 100 jobs. That's the sweet spot for daily searches."

*(select Sample)*

"**Search Terms**: Leave it as 'CDL driver' - nice and broad. The AI will filter quality."

*(show search terms field)*

"**Search Radius**: 50 miles is the default. Works well for most markets."

*(show radius dropdown)*

"**Classifier Type**: I'm using 'CDL Traditional' for truck drivers. If you have warehouse workers looking to transition, use 'Career Pathways' instead."

*(select CDL Traditional)*

---

**[STEP 3: PORTAL SETTINGS - 2 minutes]**
- Scroll to Portal Settings section

"Now let's configure what the Free Agent will see in their portal."

**Max Jobs**: "I want 20 jobs in the portal - quality over quantity."

*(set to 20)*

**Route Type Filter**: "I'll include both local AND regional routes."

*(check both boxes)*

**Match Quality Filter**: "Only 'good' and 'so-so' - we'll filter out the 'bad' jobs."

*(check good and so-so)*

**Fair Chance**: "I'll leave this unchecked for now - unless your agent has a background."

*(show unchecked)*

"These three are critical:"

**Show HTML Preview**: *(check box)* "Always check this so you can review before sharing."

**Generate Portal Link**: *(check box)* "This creates the Short.io tracked link."

**Show Prepared For**: *(check box)* "Adds a personal touch - 'Prepared for John Smith'."

---

**[STEP 4: FREE AGENT LOOKUP - 1 minute]**
- Show Airtable Search section

"Now specify which agent this is for."

**Option 1 - Airtable Search**:
*(type name)* "Type their name, click Search, select from dropdown, Use Selected. Fast and easy."

**Option 2 - Manual Entry**:
*(type name)* "Or just type their name manually and click Use Manual Entry."

*(use manual entry for demo)*

"I'll use John Smith for this example."

---

**[STEP 5: RUN SEARCH - 1 minute]**
- Click Memory Only button

"Alright, everything's configured. Let's run the search."

*(click 💾 Memory Only button)*

"Watch this - it's instant."

*(wait 5 seconds)*

"And... done! 3 seconds. That's the power of the cache."

---

**[STEP 6: REVIEW RESULTS - 1.5 minutes]**
- Scroll through results

"Here's what we got:"

**Search Summary**:
"87 total jobs from memory, 62 are quality (good or so-so). That's a 71% quality rate - excellent."

**Quality Metrics**:
"Quality Rate: 71%. Top Route: Local - 45 jobs."

"This tells me Dallas has plenty of local routes - great for agents who need to be home nightly."

**HTML Preview**:
*(scroll to preview)*

"Here's what John will see - clean job cards, AI summaries, Apply Now buttons."

*(point out job cards)*

**Portal Link**:
*(scroll to link)*

"And here's the magic link: opptek.link/xyz789"

*(click copy button)*

"Copied! Now I'll text this to John."

---

**[STEP 7: SHARE LINK - 30 seconds]**
- Show example text message

"Here's what I send:"

*(show text template)*

```
Hey John! I found 20 quality CDL jobs in Dallas for you.
Check them out: https://opptek.link/xyz789

Let me know if you have questions!
```

"Simple, clear, trackable."

---

**[WRAP-UP - 20 seconds]**
"That's it - a complete Memory-Only search in under 60 seconds."

"Remember: Use Memory-Only daily. Zero cost, instant results, keeps your agents engaged."

"Next video: Fresh Search - when and how to use it. See you there!"

**[END]**

---

## 📹 Video 3: "Fresh Search Walkthrough (Indeed API)"
**Length: 7-8 minutes**

### Script

**[INTRO - 30 seconds]**
- Show Job Search tab

"Welcome to Video 3! Now we're going to run a Fresh Search using the Indeed API."

"Fresh Searches cost about 10 to 15 cents per 100 jobs, but they populate the cache with the latest postings. Use these weekly to keep your job pool fresh."

---

**[WHEN TO USE FRESH VS MEMORY - 1 minute]**
- Show comparison visual

"Quick recap:"

**Memory-Only:**
- "Daily agent updates"
- "Zero cost"
- "Instant (3-10 seconds)"
- "Limited to cached jobs"

**Fresh Search:**
- "Weekly market refreshes"
- "$0.10-0.15 per 100 jobs"
- "60-90 seconds"
- "Latest job postings"

"Here's the workflow I recommend: Fresh Search every Monday at 9am to populate cache. Then Memory-Only Tuesday through Friday. Repeat."

---

**[STEP 1-3: SAME AS MEMORY - 1 minute]**
- Quick configuration

"Configuration is identical to Memory-Only:"

*(click through quickly)*
- "Location: Dallas-Fort Worth"
- "Search Mode: Sample (100 jobs)"
- "Search Terms: CDL driver"
- "Radius: 50 miles"
- "Classifier: CDL Traditional"
- "Portal settings: same as before"
- "Free Agent: Sarah Johnson"

"Everything's the same except which button we click at the end."

---

**[STEP 4: RUN FRESH SEARCH - 3 minutes]**
- Click Indeed Fresh Only button

"Alright, here we go."

*(click 🔍 Indeed Fresh Only button)*

"Watch the pipeline process..."

**Stage 1 - Ingestion**:
*(wait and narrate)*

"Stage 1: Searching Indeed API... requesting 100 jobs for Dallas-Fort Worth."

*(20 second wait)*

"Got 97 jobs back from Indeed."

**Stage 2-3 - Normalization & Rules**:
"Stage 2: Normalizing to our 100+ field schema..."

"Stage 3: Applying business rules... 89 jobs pass quality filters."

**Stage 4 - Deduplication**:
"Stage 4: Checking for duplicates... removed 12 duplicates. 77 unique jobs remain."

**Stage 5 - AI Classification**:
*(this takes longest)*

"Stage 5: AI Classification - this is the slowest stage. GPT-4o-mini is rating each job as good, so-so, or bad."

*(wait 30-45 seconds)*

"Watch the progress bar... 80%... 90%... done!"

"77 jobs classified."

**Stage 6-7 - Routing & Tracking**:
"Stage 6: Applying routing logic - selecting 62 quality jobs for the portal."

"Stage 7: Generating Short.io tracked links..."

**Stage 8 - Storage**:
"Stage 8: Uploading to Supabase cache... and we're done!"

---

**[STEP 5: REVIEW FRESH RESULTS - 1.5 minutes]**
- Scroll through results

"Here's what's different from Memory-Only:"

**Search Summary**:
"Total Jobs: 77"
"Quality Jobs: 62"

*(point to key metric)*

"**Memory Jobs: 25, Fresh Jobs: 52**"

"See that? 52 brand new jobs added to the cache. Those 25 memory jobs were already in cache from earlier searches."

"This is the magic: For the next 7 days, when I run Memory-Only searches for Dallas, I'll get these 52 fresh jobs - zero cost."

**Quality Metrics**:
"Quality Rate: 80.5% - excellent filtering."

**HTML Preview**:
"Same portal preview as Memory-Only."

**Portal Link**:
"New tracked link generated."

---

**[COST BREAKDOWN - 1 minute]**
- Show cost calculation

"Let's talk cost:"

"This search:"
- "100 jobs requested"
- "Cost: ~$0.10-0.15"
- "Result: 52 new jobs in cache"

"Cost per job: Less than 1 cent per job."

"But here's the kicker: These 52 jobs are now available for Memory-Only searches (zero cost) for the next 7 days."

"If I update 10 agents this week using Memory-Only, that's 10 portal links generated from one $0.10 Fresh Search."

"Cost per portal link: 1 cent. That's efficient."

---

**[WEEKLY WORKFLOW - 1 minute]**
- Show calendar visual

"Here's my weekly workflow:"

**Monday 9am**:
"Fresh Search - Dallas (100 jobs) = $0.10"
"Fresh Search - Houston (100 jobs) = $0.10"
"Fresh Search - Austin (100 jobs) = $0.10"

"Total: $0.30 for 300 fresh jobs across 3 markets."

**Tuesday-Friday**:
"Memory-Only searches for all 3 markets - update 20 agents total."

"Cost: $0.00 for 20 portal links."

**Weekly budget: $0.30 for 20 agent updates. Incredibly efficient."**

---

**[WRAP-UP - 30 seconds]**
"That's Fresh Search - your weekly cache refresh."

"Remember: Fresh Search Monday, Memory-Only Tuesday-Friday. Balance freshness with budget."

"Next video: Free Agent Management - adding agents to your roster and tracking engagement. See you there!"

**[END]**

---

## 📹 Video 4: "Free Agent Management - Add, Configure, Track"
**Length: 8-9 minutes**

### Script

**[INTRO - 30 seconds]**
- Show Free Agents tab

"Welcome to Video 4! This is where we manage your Free Agent roster - adding agents, configuring their preferences, and tracking engagement."

"The goal: Each agent gets a personalized portal link that updates automatically with jobs they actually care about."

---

**[PART 1: ADDING AGENTS - 2 minutes]**
- Click Free Agents tab → Manage Agents

"Let's add a new agent."

**Method 1 - Airtable Import**:
*(show Airtable Search section)*

"If your agent is already in Airtable:"
1. "Type their name" *(type)*
2. "Select 'Search by: name'" *(select)*
3. "Click Search" *(click)*
4. "Select from dropdown" *(select)*
5. "Configure preferences" *(scroll down)*

**Method 2 - Manual Entry**:
*(show Manual Entry section)*

"Or add them manually:"
1. "Free Agent Name: Michael Torres" *(type)*
2. "Email: michael.t@example.com" *(type)*
3. "City: Dallas" *(type)*
4. "Configure preferences" *(scroll down)*

"I'll use manual entry for this demo."

---

**[PART 2: CONFIGURING PREFERENCES - 2.5 minutes]**
- Show preference configuration section

"These settings determine what jobs appear in their portal."

**Location/Market**:
*(select Dallas-Fort Worth)*
"Where to search. Dallas-Fort Worth for Michael."

**Route Type**:
*(select dropdown)*
- "**both** - local AND regional/OTR"
- "**local** - home daily only"
- "**regional** - multi-day trips"

"I'll ask Michael: 'Do you need to be home every night?' He says yes, so I select **local**."

**Fair Chance Only**:
*(show checkbox)*
"Check this if your agent has a criminal background. Only shows 'fair chance' jobs."

"Michael doesn't need this, so I'll leave it unchecked."

**Maximum Jobs**:
*(select 20)*
"How many jobs in their portal. 15-20 is the sweet spot - quality over quantity."

**Experience Level**:
*(select dropdown)*
- "**both** - all levels"
- "**no_experience** - entry-level"
- "**experienced** - 2+ years"

"Michael has 3 years CDL experience, so I choose **experienced**."

**Classifier Type**:
*(select CDL Traditional)*
"CDL Traditional for truck drivers, Career Pathways for warehouse workers transitioning."

**Pathway Preferences** *(if Career Pathways selected)*:
*(show 8 checkboxes)*
"Select 2-3 most relevant. For a dock worker: Dock→Driver, CDL Training, Warehouse."

---

**[PART 3: SAVING & AUTO-GENERATION - 1 minute]**
- Click Add Manual Agent button

"Alright, preferences configured. Let's save."

*(click ➕ Add Manual Agent)*

"Watch this..."

*(wait 2 seconds)*

"Done! Michael is now in our roster."

*(scroll to table)*

"See him in the table? All his settings are here, and look -"

*(point to Portal Link column)*

"**Portal link auto-generated!** I didn't have to do anything - Opptek created the Short.io link automatically."

*(click to copy link)*

"Copy and send to Michael. That's it."

---

**[PART 4: THE AGENT TABLE - 2 minutes]**
- Show full table

"This table is your command center."

**Editable columns**:
*(hover over each)*
- "**Radius** - search radius"
- "**Market** - target market"
- "**Route** - route preference"
- "**Fair Chance** - fair chance filter"
- "**Max Jobs** - portal size"
- "**Pathway checkboxes** - 8 pathway types"

"You can edit any of these directly in the table."

**Analytics columns**:
*(point to right side)*
- "**Clicks (All)** - lifetime clicks"
- "**Clicks (14d)** - recent engagement"
- "**Apps (All)** - total applications"
- "**Apps (14d)** - recent applications"
- "**Score** - engagement score 1-10"

"Use these to identify your most engaged agents."

**Portal Link column**:
*(point to link)*
"This is the magic - always up-to-date, always tracked."

---

**[PART 5: EDITING AGENTS - 1 minute]**
- Edit an agent in table

"Let's say Michael's preferences changed - he's now open to regional routes."

*(click Route dropdown for Michael)*
*(change from 'local' to 'both')*

"Changed to 'both'. Now I need to save."

*(scroll to Save Changes button)*
*(click 💾 Save Changes)*

"Watch..."

*(wait 2 seconds)*

"Done! And look - his portal link regenerated automatically."

"The new link includes regional jobs now. Send him the updated link."

---

**[WRAP-UP - 30 seconds]**
"That's Free Agent management:"
1. "Add agents (Airtable or manual)"
2. "Configure preferences"
3. "Save (portal link auto-generates)"
4. "Edit anytime (link auto-updates)"

"Next video: Tracking applications and marking successes. This is where we prove ROI. See you there!"

**[END]**

---

## 📹 Video 5: "Tracking Applications & Proving Success"
**Length: 7-8 minutes**

### Script

**[INTRO - 30 seconds]**
- Show Track Applications sub-tab

"Welcome to the final video! This is where we track agent engagement, monitor applications, and prove ROI."

"Every click, every application, every hire - it's all tracked. Let's dive in."

---

**[PART 1: SELECTING AN AGENT - 45 seconds]**
- Click Free Agents → Track Applications

"First, select your agent."

*(click dropdown)*

"Here's my roster alphabetically. I'll choose Michael Torres."

*(select Michael)*

*(click Refresh Data button)*

"Click Refresh to get the latest data."

---

**[PART 2: AGENT ACTIVITY SUMMARY - 1 minute]**
- Show activity summary section

"Here's Michael's engagement at a glance:"

**Total Applications**: "Michael has applied to 8 jobs all-time."

**Date Range**: "First application: September 15. Most recent: October 5."

**Click Metrics**: "He's clicked his portal link 12 times."

"This tells me: Michael is engaged. 12 clicks, 8 applications - that's a 67% application rate. Excellent."

---

**[PART 3: QUICK EDIT SETTINGS - 1 minute]**
- Show Edit Agent Settings panel

"If I need to update Michael's preferences while reviewing applications, there's a quick-edit panel here."

**Market**: *(show dropdown)* "Change his search market."

**Route Type**: *(show dropdown)* "Update route preference."

**Fair Chance**: *(show checkbox)* "Toggle fair chance filter."

**Max Jobs**: *(show dropdown)* "Adjust portal size."

*(make a change)*

"Let's increase his Max Jobs from 20 to 25."

*(click Save Changes & Regenerate Portal Link)*

"Saved and portal link regenerated - all in one button."

---

**[PART 4: APPLICATION HISTORY TABLE - 2 minutes]**
- Show application table

"Here's every job Michael has applied to."

**Time Period Filter**:
*(select 60 days)*

"I'm viewing the last 60 days. Adjust this as needed."

**Table Columns**:
*(point to each)*
- "**ID** - unique application ID"
- "**Applied Date** - when he applied"
- "**Status** - current status (editable!)"
- "**Company** - employer name"
- "**Job Title** - position"

"The Status column is key - this is where we track progress."

**Status Options**:
*(click dropdown)*
- "**Applied** - initial application (default)"
- "**Interviewing** - he's interviewing"
- "**Offer** - he received an offer"
- "**Hired** - HE GOT THE JOB! ✅"
- "**Rejected** - application rejected"
- "**Ghosted** - no response"
- "**Withdrawn** - he withdrew"

"Let's update one."

*(click Status dropdown for a row)*
"Michael told me he has an interview tomorrow with Swift Transportation."

*(select 'Interviewing')*

"Changed to Interviewing. Now save."

*(click 💾 Save Status Changes)*

"Done! Status updated in the database."

---

**[PART 5: MARKING SUCCESS (THE BIG ONE) - 1.5 minutes]**
- Scroll to Success Tracking section

"Alright, the moment we've been waiting for."

"Michael just called - he got hired by Swift Transportation! Let's record this success."

**Company dropdown**:
*(click dropdown)*

"The dropdown shows companies from his application history. I select Swift Transportation."

*(select Swift)*

**Mark as Success button**:
*(click ✅ Mark as Success)*

*(wait for confirmation)*

"**🎉 Success recorded for Michael Torres at Swift Transportation!**"

"This is how we prove ROI. Every hire gets recorded. Leadership can see exactly how many placements Opptek enabled."

---

**[PART 6: COACH ANALYTICS - 1.5 minutes]**
- Click Coach Analytics tab

"Let's see how this impacts your performance metrics."

**Your Performance (4 columns)**:
*(point to each)*

**Total Clicks**: "143 clicks across all your portal links."

**Unique Agents Engaged**: "22 different agents have clicked."

**Avg Clicks/Agent**: "6.5 clicks per agent - excellent engagement."

**Quality Job Breakdown**: "You've found 387 'good' rated jobs."

"These metrics show your impact."

---

**[PART 7: COACH COMPARISON - 1 minute]**
- Show coach comparison section

"Want to see how you stack up?"

*(select coaches to compare)*

"Select other coaches to compare."

*(show comparison table)*

**Comparison Metrics**:
- "Total agents managed"
- "Total clicks"
- "Click-through rate"
- "Quality job percentage"

"Learn from top performers - what are they doing differently?"

---

**[WRAP-UP - 1 minute]**
"That's application tracking and success measurement:"

1. "**Track engagement** - clicks and applications tell you who's active"
2. "**Update statuses** - keep pipeline current (Applied → Interviewing → Hired)"
3. "**Mark successes** - record every hire to prove ROI"
4. "**Review analytics** - monitor your performance and improve"

"Alright, that's all 5 videos! You now have everything you need to:"
- "✅ Run Memory-Only and Fresh Searches"
- "✅ Add and manage Free Agents"
- "✅ Track applications and prove success"

"The job market is noisy - but with Opptek, you cut through the noise and connect your Free Agents with opportunities that matter."

"Go make an impact. Thanks for watching!"

**[END]**

---

## 📋 Post-Production Checklist

For each video:
- [ ] Add chapter markers (0:00 Intro, 0:30 Step 1, etc.)
- [ ] Include captions/subtitles
- [ ] Add arrows/highlights for key buttons
- [ ] Create thumbnail with clear title
- [ ] Upload to Loom
- [ ] Test video playback
- [ ] Share link in training materials

---

*Opptek: Cutting through the noise to connect Free Agents with opportunities that matter.*
