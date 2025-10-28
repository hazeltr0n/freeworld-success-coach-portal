# Supabase Functions Analysis
**Date:** October 14, 2025
**Status:** Comprehensive audit of all database functions

---

## 📊 Summary

| Function | Status | Used in Code | Recommendation |
|----------|--------|--------------|----------------|
| `batch_insert_jobs_with_dedup` | ✅ ACTIVE | 5 times | **FIX NEEDED** - Not applying delete+insert |
| `refresh_companies_analytics` | ✅ ACTIVE | 4 times | Keep |
| `refresh_free_agents_analytics` | ✅ ACTIVE | 4 times | Keep |
| `scheduled_agents_refresh` | ✅ ACTIVE | 8 times | Keep |
| `get_agent_coaches` | ⚠️ UNUSED | 0 times | Consider removing |
| `coach_has_agent_access` | ⚠️ UNUSED | 0 times | Consider removing |
| `update_agent_coaches_timestamp` | ⚠️ TRIGGER | 0 times | Keep (trigger function) |
| `get_canonical_company_name` | ⚠️ UNUSED | 0 times | Consider removing |
| `get_markets_for_location` | ⚠️ UNUSED | 0 times | Consider removing |
| `trigger_auto_learn_markets` | ⚠️ TRIGGER | 0 times | Keep (trigger function) |

---

## 🔍 Detailed Analysis

### 1. `batch_insert_jobs_with_dedup` ⚠️ **CRITICAL - NEEDS FIX**

**Purpose:** Core job insertion with R3/R1/job_id deduplication

**Files:**
- `20251005200000_fix_batch_insert_function.sql`
- `20251006160926_add_r3_deduplication.sql`
- `20251014040000_fix_dedup_upsert_with_refresh.sql` ← **Latest version**

**Used in:**
- `job_memory_db.py` (line 173)

**Current Problem:**
The latest migration (`20251014040000`) with DELETE+INSERT logic was created but NOT YET APPLIED to the database. The function is currently using the old INSERT+SKIP logic from `20251006160926`.

**Recommendation:** ✅ **APPLY IMMEDIATELY**
1. Go to Supabase Dashboard → SQL Editor
2. Run the contents of `supabase/migrations/20251014040000_fix_dedup_upsert_with_refresh.sql`
3. This will fix the issue where jobs aren't getting fresh timestamps on re-scrape

---

### 2. `refresh_companies_analytics` ✅ **KEEP - ACTIVE**

**Purpose:** Refreshes company analytics aggregations (job counts, markets, coaches)

**File:** `20250922174448_fix_companies_function.sql`

**Used in:**
- `companies_dashboard.py` (manual refresh button)
- `analytics_dashboard.py`

**What it does:**
- Aggregates job postings per company
- Counts unique markets served
- Tracks coach associations
- Calculates job quality distribution

**Recommendation:** ✅ **KEEP** - Core analytics feature

---

### 3. `refresh_free_agents_analytics` ✅ **KEEP - ACTIVE**

**Purpose:** Refreshes Free Agent analytics (clicks, applications, placements)

**Files:**
- `20251009221315_update_analytics_refresh_for_multi_coach.sql`
- `20251009221812_fix_analytics_refresh_field_names.sql` ← **Latest version**

**Used in:**
- `analytics_dashboard.py`
- Scheduled via cron job

**What it does:**
- Aggregates click events per agent
- Calculates application rates
- Tracks placement status
- Multi-coach support

**Recommendation:** ✅ **KEEP** - Core analytics feature

---

### 4. `scheduled_agents_refresh` ✅ **KEEP - ACTIVE**

**Purpose:** Automated scheduled refresh of agent analytics

**Files:**
- `20251009221315_update_analytics_refresh_for_multi_coach.sql`
- `20251009221812_fix_analytics_refresh_field_names.sql` ← **Latest version**

**Used in:**
- Cron job configuration
- `analytics_dashboard.py`
- Background processing

**What it does:**
- Wrapper around `refresh_free_agents_analytics()`
- Scheduled execution
- Error handling and logging

**Recommendation:** ✅ **KEEP** - Critical for automated analytics updates

---

### 5. `get_agent_coaches` ⚠️ **UNUSED - CONSIDER REMOVING**

**Purpose:** Returns array of coaches associated with an agent

**File:** `20251002182336_multi_coach_and_placement_status.sql`

**Used in:** None (0 occurrences in Python code)

**What it does:**
```sql
-- Returns ARRAY of coach usernames for given agent UUID
SELECT coach_username FROM agent_coach_assignments
WHERE agent_uuid = p_agent_uuid
```

**Analysis:**
- Part of multi-coach system
- Created October 2, 2025
- Never used in application code
- May have been replaced by direct table queries

**Recommendation:** ⚠️ **CONSIDER REMOVING**
- Check if this was planning to be used but never implemented
- If not needed, remove to reduce database clutter
- **Before removing:** Verify no Supabase Edge Functions or external integrations use it

---

### 6. `coach_has_agent_access` ⚠️ **UNUSED - CONSIDER REMOVING**

**Purpose:** Permission check - does coach have access to agent?

**File:** `20251002182336_multi_coach_and_placement_status.sql`

**Used in:** None (0 occurrences in Python code)

**What it does:**
```sql
-- Returns BOOLEAN
SELECT EXISTS(
    SELECT 1 FROM agent_coach_assignments
    WHERE agent_uuid = p_agent_uuid
    AND coach_username = p_coach_username
)
```

**Analysis:**
- Part of multi-coach permission system
- Never integrated into Python application
- Permission checks done in Python instead

**Recommendation:** ⚠️ **CONSIDER REMOVING**
- Not being used for permission validation
- Python code handles this logic instead
- **Before removing:** Check if this is part of Row Level Security (RLS) policies

---

### 7. `update_agent_coaches_timestamp` ⚠️ **TRIGGER FUNCTION - KEEP**

**Purpose:** Automatically updates `coaches_updated_at` when coaches change

**File:** `20251002182336_multi_coach_and_placement_status.sql`

**Used in:** Trigger on `agent_coach_assignments` table (not directly in Python)

**What it does:**
```sql
-- Trigger function that fires on INSERT/UPDATE/DELETE
UPDATE free_agents
SET coaches_updated_at = NOW()
WHERE agent_uuid = NEW.agent_uuid
```

**Analysis:**
- **This is a TRIGGER function** - won't show up in Python code
- Automatically maintains timestamp when coach assignments change
- Critical for cache invalidation

**Recommendation:** ✅ **KEEP** - Essential trigger function

---

### 8. `get_canonical_company_name` ⚠️ **UNUSED - CONSIDER REMOVING**

**Purpose:** Resolves company name through parent company hierarchy

**File:** `20251004192625_add_parent_company_hierarchy.sql`

**Used in:** None (0 occurrences in Python code)

**What it does:**
```sql
-- Recursively resolves parent company relationships
-- Returns the "canonical" (top-level) company name
```

**Analysis:**
- Part of company hierarchy feature
- Never integrated into application
- Company merging uses different approach

**Recommendation:** ⚠️ **CONSIDER REMOVING**
- Feature appears abandoned
- Company dashboard uses manual merge instead
- Taking up database resources

---

### 9. `get_markets_for_location` ⚠️ **UNUSED - CONSIDER REMOVING**

**Purpose:** Returns all markets that match a location string

**File:** `20251004221717_create_location_markets_library.sql`

**Used in:** None (0 occurrences in Python code)

**What it does:**
```sql
-- Searches location_markets table
-- Returns matching markets for city/state/ZIP
```

**Analysis:**
- Part of location markets library
- Python code does direct table queries instead
- Function not providing value

**Recommendation:** ⚠️ **CONSIDER REMOVING**
- Direct table access is simpler and more flexible
- Function adds unnecessary abstraction
- Not being used anywhere

---

### 10. `trigger_auto_learn_markets` ⚠️ **TRIGGER FUNCTION - KEEP**

**Purpose:** Automatically learns new markets from job data

**Files:**
- `20251005020000_auto_learn_markets_trigger.sql`
- `20251006142406_fix_auto_learn_trigger_config.sql` ← **Latest version**

**Used in:** Trigger on `jobs` table (not directly in Python)

**What it does:**
```sql
-- Fires on INSERT/UPDATE to jobs table
-- Extracts location data and adds to location_markets
-- Auto-discovers new markets from incoming jobs
```

**Analysis:**
- **This is a TRIGGER function** - won't show up in Python code
- Automatic market discovery system
- Reduces manual market configuration

**Recommendation:** ✅ **KEEP** - Useful automation, but monitor performance
- Could slow down job insertions if not optimized
- Consider disabling if batch inserts become slow

---

## 🎯 Action Items

### Immediate (Priority 1)

1. **Apply `batch_insert_jobs_with_dedup` fix**
   - Go to Supabase Dashboard → SQL Editor
   - Run `supabase/migrations/20251014040000_fix_dedup_upsert_with_refresh.sql`
   - Test with `test_delete_insert_dedup.py`

### Short-term (Priority 2)

2. **Remove unused functions** (reduces clutter, improves maintainability)
   - `get_agent_coaches` - unused since creation
   - `coach_has_agent_access` - unused since creation
   - `get_canonical_company_name` - abandoned feature
   - `get_markets_for_location` - replaced by direct queries

   **Before removing:** Verify no RLS policies, Edge Functions, or external tools depend on these.

### Monitor (Priority 3)

3. **Monitor trigger performance**
   - `trigger_auto_learn_markets` - Could slow down large batch inserts
   - `update_agent_coaches_timestamp` - Generally lightweight

---

## 📝 Function Removal SQL

If you decide to remove the unused functions:

```sql
-- Remove unused functions (run after verification)
DROP FUNCTION IF EXISTS get_agent_coaches(TEXT);
DROP FUNCTION IF EXISTS coach_has_agent_access(TEXT, TEXT);
DROP FUNCTION IF EXISTS get_canonical_company_name(INTEGER);
DROP FUNCTION IF EXISTS get_markets_for_location(TEXT, TEXT);
```

---

## ✅ Healthy Functions (No Action Needed)

- `batch_insert_jobs_with_dedup` - Once fixed, this is critical
- `refresh_companies_analytics` - Active and working
- `refresh_free_agents_analytics` - Active and working
- `scheduled_agents_refresh` - Active and working
- `update_agent_coaches_timestamp` - Trigger, working as intended
- `trigger_auto_learn_markets` - Trigger, useful automation

---

**Next Steps:**
1. Apply the deduplication fix immediately
2. Test thoroughly with next DriverPulse scrape
3. Monitor for 24 hours, then consider removing unused functions
