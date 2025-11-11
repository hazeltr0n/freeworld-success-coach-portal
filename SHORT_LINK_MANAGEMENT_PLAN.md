# Short.io Link Management System - Comprehensive Plan

## 🔍 Current State Analysis

I've identified **6 different link generation pathways** across your codebase that are creating Short.io links:

### Link Generation Pathways

1. **Pipeline v3.1 Stage 7** (`pipeline_v3.py:1800-1950`)
   - Creates links for quality jobs (good/so-so) from fresh scrapes
   - **BUG**: Line 1821 references undefined `force_link_generation` variable
   - **Impact**: Breaks 80% coverage optimization, creates duplicate links
   - Volume: ~100-500 links per batch run

2. **Agent Portal Link Generation** (`free_agent_system.py:175-275`)
   - Creates tracking links when agents view their personalized job feeds
   - Runs for each portal access
   - Volume: Variable, depends on agent activity

3. **Memory Search with Link Generation** (`supabase_utils.py:1040-1075`)
   - `instant_memory_search()` generates links for jobs pulled from database
   - Rate limited: 1 second delay per 10 jobs
   - Volume: Depends on portal traffic

4. **Portal Link Regeneration** (`app.py:678-750, 1834-1861, 2037-2051`)
   - Creates Short.io links for agent portal URLs themselves
   - Triggered when coaches "Regenerate Portal Links" in Free Agent Management tab
   - Volume: ~1 link per agent (you have ~100-200 agents)

5. **Async Job Queue Link Generation** (`async_job_manager.py:731-742`)
   - GitHub Actions workflows create links during async batch processing
   - DriverPulse, Indeed, Google Jobs async batches
   - Volume: 100-500 links per async job

6. **Legacy/Test Link Generation** (various test files, debug scripts)
   - Test suite, debug tools, development scripts
   - Low volume but accumulates over time

### Root Causes of 100k+ Link Explosion

1. **Undefined Variable Bug** (`pipeline_v3.py:1821`)
   - `force_link_generation` is used but never defined
   - Breaks smart reuse optimization that should skip link generation when 80%+ jobs already have links
   - System creates NEW links every time instead of reusing

2. **Multiple Pathways Creating Duplicate Links**
   - Pipeline creates link for job_id=X
   - Agent portal creates another link for same job_id=X
   - Memory search creates yet another link for job_id=X
   - **Result**: 3-15x duplicate links per job

3. **No Centralized Link Registry**
   - Each pathway independently calls `link_tracker.create_short_link()`
   - No shared cache or registry to check "does this job already have a link?"
   - `allowDuplicates: False` in Short.io payload doesn't prevent this (only prevents same URL being shortened twice, not same job getting multiple links)

4. **Portal Link Regeneration**
   - When coaches bulk regenerate portal links, old links aren't deleted
   - Creates orphaned links in Short.io

## 🎯 Proposed Solution: Centralized Link Management System

### Phase 1: Fix Critical Bugs (Immediate)

1. **Fix `force_link_generation` Bug**
   - Define the variable or remove the broken logic
   - Restore 80% coverage optimization to work properly

2. **Add Supabase Link Registry**
   - Create `short_links` table in Supabase:
     ```sql
     CREATE TABLE short_links (
       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       job_id TEXT NOT NULL,              -- id.job from jobs table
       agent_uuid TEXT,                   -- Optional: agent-specific link
       short_url TEXT NOT NULL,           -- freeworldjobs.short.gy/xyz
       short_id TEXT NOT NULL,            -- xyz (idString from Short.io)
       original_url TEXT NOT NULL,
       link_type TEXT NOT NULL,           -- 'job_application', 'agent_portal'
       created_at TIMESTAMPTZ DEFAULT NOW(),
       last_used_at TIMESTAMPTZ,
       click_count INT DEFAULT 0,
       is_active BOOLEAN DEFAULT TRUE,
       UNIQUE(job_id, agent_uuid)         -- Prevent duplicate links per job+agent
     );

     CREATE INDEX idx_short_links_job_id ON short_links(job_id);
     CREATE INDEX idx_short_links_agent ON short_links(agent_uuid);
     CREATE INDEX idx_short_links_type ON short_links(link_type);
     CREATE INDEX idx_short_links_active ON short_links(is_active);
     ```

3. **Create Centralized Link Manager** (`link_manager.py`)
   ```python
   class CentralizedLinkManager:
       """Single source of truth for all Short.io link operations"""

       def get_or_create_link(self, job_id, original_url, agent_uuid=None, **kwargs):
           """Check registry first, create only if needed"""
           # Check Supabase registry
           existing = self.check_registry(job_id, agent_uuid)
           if existing:
               return existing['short_url']

           # Create new link via Short.io
           short_url = link_tracker.create_short_link(...)

           # Register in Supabase
           self.register_link(job_id, short_url, agent_uuid, ...)

           return short_url

       def cleanup_old_links(self, days_old=90, link_type=None):
           """Identify and delete inactive links"""
           # Query Supabase for old unused links
           # Delete from Short.io
           # Mark as inactive in registry
   ```

### Phase 2: Automatic Link Lifecycle Management

4. **Implement Link TTL System**
   - Job links expire after 90 days (jobs are stale)
   - Portal links expire when agent becomes inactive (>180 days no clicks)
   - Weekly cleanup job via GitHub Actions cron

5. **Link Usage Tracking**
   - Update `last_used_at` and `click_count` via Short.io webhooks
   - Identify unused links for deletion

6. **Automatic Link Limits**
   ```python
   MAX_ACTIVE_LINKS = 95000  # Stay under 100k with buffer

   def enforce_link_limit():
       current_count = get_active_link_count()
       if current_count > MAX_ACTIVE_LINKS:
           # Delete oldest unused links
           cleanup_oldest_links(count=current_count - MAX_ACTIVE_LINKS + 5000)
   ```

### Phase 3: Portal Link Optimization

7. **Update Portal Link Generation**
   - When regenerating portal links, DELETE old Short.io link first
   - Track portal link ID in `agent_profiles.portal_link_id`
   - Reuse existing portal link if still valid

8. **Unified Link Generation Entry Points**
   - All 6 pathways call `CentralizedLinkManager.get_or_create_link()`
   - No direct calls to `link_tracker.create_short_link()`
   - Guaranteed deduplication

### Phase 4: Monitoring & Alerts

9. **Link Health Dashboard**
   - Show total active links / plan limit
   - Alert when approaching 95% capacity
   - Show link creation rate (links/day)
   - Show deletion rate (cleanup effectiveness)

10. **GitHub Actions Cron Jobs**
    ```yaml
    # .github/workflows/link_cleanup.yml
    schedule:
      - cron: '0 0 * * 0'  # Weekly on Sunday

    jobs:
      cleanup-old-links:
        - Run cleanup script
        - Delete links >90 days old with 0 clicks
        - Report deleted count
    ```

## 📊 Expected Impact

### Before Implementation
- **Current State**: 100k+ links for 6,775 quality jobs = 15x duplication
- **Problem**: Over plan limit, can't create new links
- **Manual Work**: Coaches must manually delete links

### After Implementation
- **Link Count**: ~10-15k active links (1.5-2x jobs, with agent-specific tracking)
- **Automatic Cleanup**: Weekly deletion of stale links
- **Zero Duplication**: Centralized registry prevents duplicates
- **Self-Managing**: Stays under limit automatically

## 🛠️ Implementation Order

1. ✅ **Immediate (Today)**: Fix `force_link_generation` bug (1 hour)
2. ✅ **Quick Win (This Week)**: Run manual cleanup script to delete 80k old links (2 hours)
3. 📋 **Phase 1 (Next Week)**: Implement Supabase registry + CentralizedLinkManager (8 hours)
4. 📋 **Phase 2 (Week 2)**: Add TTL system + automated cleanup (4 hours)
5. 📋 **Phase 3 (Week 3)**: Update all 6 pathways to use centralized manager (6 hours)
6. 📋 **Phase 4 (Week 4)**: Monitoring dashboard + cron jobs (4 hours)

**Total Effort**: ~24 hours over 4 weeks
**Payoff**: Never manually manage links again, automatic stay under limit

---

## 📝 Additional Notes

### CSV Analysis Results (from previous investigation)
- **Total links in CSV export**: 17,956
- **Portal links (KEEP)**: 12,724 (contain fwcareercoach or supabase)
- **Safe to delete from CSV**: 3,001 links (test + job board links)
- **Discrepancy**: CSV shows only ~18k links but account is over 100k limit
  - Suggests many links not visible in CSV export
  - Need to use Short.io API for complete inventory

### Immediate Cleanup Strategy
1. Use `bulk_delete_old_shortio_links.py` script (already created)
2. Sort links by creation date (oldest first)
3. Keep ALL portal links (fwcareercoach/supabase URLs)
4. Delete oldest 80k job application links
5. Should bring total from 100k+ down to ~20k active links

### Key Files Modified in This Plan
- `pipeline_v3.py` - Fix undefined variable bug (line 1821)
- `link_manager.py` - NEW centralized manager
- `supabase_utils.py` - Update to use centralized manager
- `free_agent_system.py` - Update to use centralized manager
- `async_job_manager.py` - Update to use centralized manager
- `app.py` - Update portal link regeneration to delete old links first
- `.github/workflows/link_cleanup.yml` - NEW automated cleanup cron

---

*Last Updated: November 4, 2025*
*Analysis by: Claude (Anthropic)*
