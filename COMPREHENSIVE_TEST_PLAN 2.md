# FreeWorld Success Coach Portal - Comprehensive Test Plan
*Pre-Production Deployment Testing*

## 🎯 **Testing Strategy**
- **Goal**: Test EVERY user-facing feature across all 6 tabs before production deployment
- **Approach**: Manual testing + Playwright automation for critical paths
- **Coverage**: Authentication, permissions, all features, error handling, edge cases

---

## 🔐 **1. AUTHENTICATION & ACCESS CONTROL**

### Login/Logout Flow
- [ ] **Login with valid credentials** (admin and regular coach)
- [ ] **Login with invalid credentials** (should show error)
- [ ] **Session persistence** (refresh page, still logged in)
- [ ] **Logout functionality** (hamburger menu → Sign Out)
- [ ] **Password change** (hamburger menu → Change Password)
- [ ] **Cache clearing** (hamburger menu → Clear Cache)

### Permission System
- [ ] **Admin vs Coach access** (Admin sees all tabs, Coach sees restricted)
- [ ] **Batches & Scheduling permission** (only if `can_access_batches` is True)
- [ ] **PDF generation permission** (only if `can_generate_pdf` is True)
- [ ] **Force fresh classification permission** (admin only)
- [ ] **Google Jobs access permission** (if enabled)

---

## 🔍 **2. TAB 1: JOB SEARCH**

### Search Parameters Configuration
- [ ] **Location Type selection** (Select Market vs Custom Location)
- [ ] **Market selection** (Houston, Dallas, Austin, etc.)
- [ ] **Custom location input** (free text entry)
- [ ] **Job quantity slider** (25-1000 jobs)
- [ ] **Search terms input** (CDL, driver, trucking keywords)
- [ ] **Search radius** (5-50+ miles)

### Search Modes
- [ ] **Fresh search** (pulls new data from APIs)
- [ ] **Memory search** (uses cached data)
- [ ] **Memory Only search** (button in main interface)

### Advanced Options
- [ ] **Force fresh classification** (if admin)
- [ ] **No experience required filter**
- [ ] **Exact location mode** (radius=0)

### PDF Configuration Section
- [ ] **PDF route type filter** (Local, OTR, Both)
- [ ] **Job quality filter** (good, so-so, bad combinations)
- [ ] **Fair chance only checkbox**
- [ ] **Include memory jobs checkbox**
- [ ] **Max jobs for PDF** (25-100)
- [ ] **Show 'prepared for' message toggle** ⭐ CRITICAL FIX
- [ ] **HTML preview checkbox**
- [ ] **Generate portal link checkbox**

### Free Agent Lookup
- [ ] **Search by name** (partial matches)
- [ ] **Search by UUID** (exact match)
- [ ] **Search by email** (exact match)
- [ ] **Agent selection from dropdown**
- [ ] **Manual entry option**

### Search Execution & Results
- [ ] **Run fresh search** (APIs called, data returned)
- [ ] **Run memory search** (cached data loaded)
- [ ] **Quality job filtering** (good/so-so displayed)
- [ ] **Results table display** (jobs with proper columns)
- [ ] **Sorting functionality** (Local→OTR→Unknown) ⭐ RECENT FIX
- [ ] **Market-specific results** (multiple markets)

### PDF Generation
- [ ] **PDF download button appears** (after search)
- [ ] **PDF generation works** (file downloads)
- [ ] **PDF shows correct sorting** (Local→OTR→Unknown) ⭐ CRITICAL FIX
- [ ] **Prepared for message toggle works** ⭐ CRITICAL FIX
  - [ ] **When checked**: Shows "Prepared for [Name] by Coach [Coach]"
  - [ ] **When unchecked**: No prepared message
- [ ] **Job quality filtering in PDF** (only selected qualities)
- [ ] **Route filtering in PDF** (only selected routes)
- [ ] **Link tracking in PDF** (Short.io links work) ⭐ RECENT FIX (no expiry)

### HTML Preview
- [ ] **HTML preview checkbox works**
- [ ] **Preview displays correctly** (mobile-optimized view)
- [ ] **Job sorting in preview** (Local→OTR→Unknown) ⭐ RECENT FIX
- [ ] **Prepared for toggle in preview** ⭐ CRITICAL FIX
- [ ] **Short links work in preview** ⭐ RECENT FIX (no expiry)

### Portal Link Generation
- [ ] **Portal link checkbox works**
- [ ] **Portal link generation** (Short.io link created)
- [ ] **Portal link functionality** (opens agent portal)
- [ ] **Portal respects all filters** (route, quality, fair chance)
- [ ] **Portal shows prepared message toggle** ⭐ CRITICAL FIX
- [ ] **Portal links don't expire** ⭐ RECENT FIX

### Error Handling
- [ ] **API failures gracefully handled** (timeout, 500 errors)
- [ ] **Empty results handled** (no jobs found message)
- [ ] **Invalid location handled** (error message shown)
- [ ] **Permission denied handled** (clear error messages)

---

## 🗓️ **3. TAB 2: BATCHES & SCHEDULING**

### Access Control
- [ ] **Permission check** (only visible if `can_access_batches`)
- [ ] **Access denied message** (for coaches without permission)

### Batch Management
- [ ] **View active batches** (if any exist)
- [ ] **Create new batch** (if functionality exists)
- [ ] **Batch status display** (pending, running, completed)
- [ ] **Batch results download** (if completed)

### Scheduling
- [ ] **View scheduled searches** (if any exist)
- [ ] **Create scheduled search** (if functionality exists)
- [ ] **Schedule management** (edit, delete, pause)

---

## 👥 **4. TAB 3: FREE AGENTS**

### Agent Import (Airtable)
- [ ] **Airtable lookup field** (search by name/email)
- [ ] **Dropdown selection** (from Airtable results)
- [ ] **Agent data import** (name, email, location populated)
- [ ] **Use selected agent button** (imports to database)

### Manual Agent Entry ⭐ RECENT FEATURE
- [ ] **Manual entry form** (all fields available)
  - [ ] Agent Name (required)
  - [ ] Email (optional)
  - [ ] UUID (auto-generated if empty)
  - [ ] City/State (optional)
  - [ ] Market selection (required)
- [ ] **Advanced settings** (route filter, fair chance, max jobs, experience)
- [ ] **Add manual agent button** (saves to database)
- [ ] **Portal link generation** (automatic Short.io link)
- [ ] **Success confirmation** (agent saved message)

### Agent Management Table
- [ ] **Agent list display** (all agents for coach)
- [ ] **Status column** (🟢 Active vs 👻 Deleted) ⭐ RECENT FEATURE
- [ ] **Click statistics** (total clicks, recent clicks)
- [ ] **Inline editing** (name, market, route, fair chance, etc.)
- [ ] **Portal link display** (Short.io links)
- [ ] **Admin portal links** (if available)

### Agent Recovery System ⭐ RECENT FEATURE
- [ ] **"Show Deleted" checkbox** (toggles visibility)
- [ ] **Deleted agents display** (with 👻 status)
- [ ] **Restore checkbox** (for deleted agents)
- [ ] **Bulk restore functionality** (select multiple, restore all)
- [ ] **Restore confirmation** (agents become active again)

### Bulk Operations
- [ ] **Refresh button** (reload from database)
- [ ] **Data source indicator** (🟢 Supabase vs 🟡 Session)
- [ ] **Regenerate all portal links** (updates Short.io links)
- [ ] **Export email list** (CSV download)
- [ ] **Delete selected agents** (soft delete to inactive)

### Agent Analytics
- [ ] **Click statistics accuracy** (matches actual clicks)
- [ ] **Lookback period filter** (7d, 14d, 30d)
- [ ] **Portal visit tracking** (total visits per agent)
- [ ] **Performance metrics** (engagement rates)

---

## 📊 **5. TAB 4: COACH ANALYTICS**

### Overview Tab
- [ ] **Total engagements** (click counts)
- [ ] **Date range filter** (last 7 days, 30 days, etc.)
- [ ] **Coach performance summary** (current coach stats)

### Individual Agents Tab
- [ ] **Per-agent breakdown** (individual performance)
- [ ] **Agent click statistics** (detailed by agent)
- [ ] **Engagement trends** (over time if available)

### FreeWorld Dashboard Tab  
- [ ] **Program-wide metrics** (if admin/accessible)
- [ ] **Economic impact estimates** (if calculated)
- [ ] **ROI calculations** (if available)

### Detailed Events Tab
- [ ] **Click event log** (individual click records)
- [ ] **Event filtering** (by agent, date, etc.)
- [ ] **Export functionality** (CSV download)

### Admin Reports Tab
- [ ] **Admin-only access** (permission check)
- [ ] **Cross-coach analytics** (if admin)
- [ ] **System-wide reporting** (comprehensive metrics)

---

## 🏢 **6. TAB 5: COMPANIES**

### Companies Dashboard
- [ ] **Companies table display** (job postings by company)
- [ ] **Company statistics** (job counts, locations)
- [ ] **Data freshness indicator** (last updated time)
- [ ] **Sorting functionality** (by company name, job count)
- [ ] **Search/filter** (find specific companies)

### Company Data Management
- [ ] **Data refresh** (update from latest job data)
- [ ] **Export functionality** (CSV download if available)
- [ ] **Company details** (drill-down view if available)

---

## 👑 **7. TAB 6: ADMIN PANEL**

### Access Control
- [ ] **Admin only access** (role='admin' required)
- [ ] **Restricted message** (for non-admin users)

### Coach Management
- [ ] **Coach list display** (all coaches in system)
- [ ] **Add new coach** (creation functionality)
- [ ] **Edit coach permissions** (role, specific permissions)
- [ ] **Password reset** (for other coaches) ⭐ RECENT FIX
- [ ] **Coach status management** (active/inactive)

### Permission Management
- [ ] **Permission matrix** (view/edit all permissions)
- [ ] **Bulk permission updates** (multiple coaches)
- [ ] **Permission validation** (changes take effect)

### System Administration
- [ ] **System status** (health checks if available)
- [ ] **Cache management** (clear system caches)
- [ ] **Debug information** (system diagnostics)

---

## 🔗 **8. AGENT PORTAL (PUBLIC-FACING)**

### Portal Access
- [ ] **Direct UUID access** (with secure token)
- [ ] **Encoded config access** (from portal links)
- [ ] **Security token validation** (invalid tokens rejected)
- [ ] **Error messages** (clear access denied messages)

### Portal Display
- [ ] **Mobile-optimized layout** (responsive design)
- [ ] **Job listings display** (clean, organized view)
- [ ] **Job sorting** (Local→OTR→Unknown) ⭐ RECENT FIX
- [ ] **Quality filtering** (based on agent preferences)
- [ ] **Fair chance filtering** (if agent has preference)
- [ ] **Route filtering** (local/OTR based on agent settings)

### Portal Personalization
- [ ] **Agent name display** (first name only for security)
- [ ] **Prepared for message** (respects toggle setting) ⭐ CRITICAL FIX
  - [ ] **When enabled**: Shows "Prepared for [Name] by Coach [Coach]"
  - [ ] **When disabled**: No prepared message
- [ ] **Job count limits** (respects agent max_jobs setting)
- [ ] **Location-specific jobs** (based on agent location)

### Portal Links & Tracking
- [ ] **Job application links** (Short.io tracked URLs) ⭐ RECENT FIX (no expiry)
- [ ] **Click tracking** (analytics recorded in Supabase)
- [ ] **Link functionality** (all job links work)
- [ ] **No expired links** (permanent links) ⭐ RECENT FIX

---

## 🧪 **9. CROSS-FEATURE INTEGRATION TESTS**

### End-to-End Workflows
- [ ] **Complete job search → PDF generation → agent portal creation workflow**
- [ ] **Agent creation → portal access → job application workflow**
- [ ] **Analytics tracking → click recording → reporting workflow**
- [ ] **Permission changes → feature access → functionality workflow**

### Data Consistency
- [ ] **Job data consistency** (same jobs across preview, PDF, portal)
- [ ] **Agent data consistency** (settings reflected across all features)
- [ ] **Analytics consistency** (clicks recorded accurately everywhere)
- [ ] **Link consistency** (same Short.io links used throughout)

### Recent Fix Validation ⭐ CRITICAL
- [ ] **Prepared for toggle** (works in ALL channels: HTML, PDF, Portal)
- [ ] **Job sorting** (Local→OTR→Unknown in ALL outputs)
- [ ] **Link expiry removal** (no links expire anywhere)
- [ ] **Agent recovery** (deleted agents can be restored)

---

## 🤖 **10. PLAYWRIGHT AUTOMATION SETUP**

### Critical Path Automation
```typescript
// Priority test scenarios for Playwright
1. Login → Job Search → PDF Generation (with prepared toggle OFF)
2. Login → Free Agent Creation → Portal Access 
3. Login → Agent Recovery (show deleted → restore)
4. Portal Access → Job Sorting Verification
5. Cross-tab Navigation (all 6 tabs accessible)
```

### Test Data Setup
- [ ] **Test coach accounts** (admin + regular coach)
- [ ] **Test agent data** (active + deleted agents)
- [ ] **Mock job data** (different routes: Local, OTR, Unknown)
- [ ] **Permission variations** (different coach permissions)

### Environment Setup
- [ ] **QA environment ready** (current environment)
- [ ] **Test database** (Supabase with test data)
- [ ] **API configurations** (all integrations working)
- [ ] **Short.io testing** (link generation functional)

---

## 📋 **11. TEST EXECUTION CHECKLIST**

### Pre-Test Setup
- [ ] **Environment verified** (QA portal accessible)
- [ ] **Test accounts created** (admin + regular coach)
- [ ] **Test data prepared** (agents, jobs, etc.)
- [ ] **All integrations working** (APIs, Supabase, Short.io)

### Manual Testing Execution
- [ ] **Authentication tests** (complete)
- [ ] **Job Search tab** (all features tested)
- [ ] **Batches & Scheduling tab** (if accessible)
- [ ] **Free Agents tab** (all features tested)
- [ ] **Coach Analytics tab** (all features tested)
- [ ] **Companies tab** (all features tested)
- [ ] **Admin Panel tab** (if admin)
- [ ] **Agent Portal** (public access tested)

### Playwright Automation
- [ ] **Playwright installed** (`npm install playwright`)
- [ ] **Test scripts written** (critical paths)
- [ ] **CI/CD integration** (if desired)
- [ ] **Test reports** (automated results)

### Bug Tracking
- [ ] **Issues documented** (with reproduction steps)
- [ ] **Priority assigned** (critical/high/medium/low)
- [ ] **Fixes implemented** (and re-tested)
- [ ] **Regression testing** (previous fixes still work)

---

## 🚀 **12. PRODUCTION DEPLOYMENT READINESS**

### Final Validation
- [ ] **All tests passing** (100% feature coverage)
- [ ] **No critical bugs** (blocking issues resolved)
- [ ] **Performance acceptable** (reasonable load times)
- [ ] **Security verified** (authentication, authorization)

### Deployment Process
- [ ] **QA→Production sync** (files copied correctly)
- [ ] **Environment variables** (production configs set)
- [ ] **Database migrations** (if any required)
- [ ] **Cache clearing** (production environment fresh)

### Post-Deployment Verification
- [ ] **Smoke tests** (basic functionality works)
- [ ] **Critical path verification** (key workflows functional)
- [ ] **Monitoring active** (error tracking, performance)
- [ ] **Rollback plan ready** (if issues discovered)

---

## ⚠️ **CRITICAL FIXES TO VALIDATE**

These recent fixes MUST be thoroughly tested:

1. **Prepared For Toggle** ⭐ HIGHEST PRIORITY
   - Test in HTML preview, PDFs, and portal links
   - Verify toggle OFF = no message, toggle ON = message shows

2. **Job Sorting** (Local→OTR→Unknown)
   - Verify consistent across all outputs
   - Test with mixed job data

3. **Link Expiry Removal**
   - Verify no links expire (test older links still work)
   - Confirm new links created without expiry

4. **Agent Recovery System**
   - Test soft delete/restore functionality
   - Verify "Show Deleted" checkbox works

---

## 🎯 **PLAYWRIGHT RECOMMENDATION**

**YES, implement Playwright automation for:**
- Critical user journeys (login → search → PDF)
- Cross-browser compatibility testing
- Regression testing of recent fixes
- CI/CD integration for future deployments

This would significantly improve confidence in production deployments and catch regressions early.