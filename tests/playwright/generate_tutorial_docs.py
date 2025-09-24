#!/usr/bin/env python3
"""
Tutorial Documentation Generator
Generate comprehensive coach tutorial documentation without heavy screenshot capture
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directories for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class QuickTutorialGenerator:
    """Generate tutorial documentation based on system analysis"""

    def __init__(self, output_dir: str = "docs/coach-tutorial"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_complete_guide(self):
        """Generate complete tutorial guide"""
        print("📚 Generating FreeWorld Success Coach Portal Tutorial...")

        # Create directory structure
        dirs = [
            "getting-started", "daily-workflows", "features-guide",
            "reference", "troubleshooting", "screenshots"
        ]
        for dir_name in dirs:
            (self.output_dir / dir_name).mkdir(exist_ok=True)

        # Generate all documentation
        self._generate_main_readme()
        self._generate_getting_started()
        self._generate_field_definitions()
        self._generate_daily_workflows()
        self._generate_features_guide()
        self._generate_troubleshooting()

        print(f"✅ Tutorial documentation generated at: {self.output_dir}")

    def _generate_main_readme(self):
        """Generate main README file"""
        content = f"""# FreeWorld Success Coach Portal - User Guide

*Last Updated: {datetime.now().strftime('%B %d, %Y')}*

The FreeWorld Success Coach Portal is your comprehensive tool for connecting Free Agents (CDL drivers and warehouse workers) with quality employment opportunities through AI-powered job matching and analytics.

## 🚀 Quick Start

1. **[Login & Setup](getting-started/login-and-setup.md)** - Get started with the portal
2. **[Basic Job Search](daily-workflows/basic-job-search.md)** - Your first search
3. **[Understanding Results](daily-workflows/interpreting-results.md)** - Reading job classifications

## 📋 Table of Contents

### Getting Started
- [Login & Setup](getting-started/login-and-setup.md)
- [Understanding the Interface](getting-started/understanding-interface.md)
- [Your First Search](getting-started/first-search.md)

### Daily Workflows
- [Basic Job Search](daily-workflows/basic-job-search.md)
- [Advanced Search Options](daily-workflows/advanced-search-options.md)
- [Interpreting Results](daily-workflows/interpreting-results.md)
- [Generating Reports](daily-workflows/generating-reports.md)
- [Managing Free Agents](daily-workflows/managing-agents.md)

### Features Guide
- [Search Modes & Types](features-guide/search-modes.md)
- [AI Classification System](features-guide/classification-types.md)
- [Analytics Dashboard](features-guide/analytics-dashboard.md)
- [Batch Scheduling](features-guide/batch-scheduling.md)

### Reference
- [Complete Field Definitions](reference/field-definitions.md)
- [Search Parameters Guide](reference/search-parameters.md)
- [Permissions & Access Levels](reference/permissions.md)

### Troubleshooting
- [Common Issues](troubleshooting/common-issues.md)
- [Performance Tips](troubleshooting/performance-tips.md)
- [Error Messages](troubleshooting/error-messages.md)

## 🎯 Key Features

- **AI-Powered Classification**: Automatically rates job quality and identifies career pathways
- **Multi-Source Search**: Indeed, Google Jobs, and Outscraper integration
- **Memory System**: Intelligent caching for cost-effective repeated searches
- **Analytics Dashboard**: Track Free Agent engagement and coach performance
- **Batch Scheduling**: Automate recurring job searches
- **Link Tracking**: Monitor Free Agent job application activity

## 💡 Best Practices

1. **Start with Memory Only** searches for speed and cost efficiency
2. **Use test mode (25 jobs)** when trying new locations or parameters
3. **Check analytics daily** to monitor Free Agent engagement
4. **Set up batch schedules** for recurring searches in key markets

## 🆘 Need Help?

- Check [Common Issues](troubleshooting/common-issues.md) for quick solutions
- Review [Field Definitions](reference/field-definitions.md) for parameter explanations
- Contact your administrator for permission or access issues

---
*This guide covers all current features and is updated regularly to match system changes.*
"""

        with open(self.output_dir / "README.md", 'w') as f:
            f.write(content)

    def _generate_getting_started(self):
        """Generate getting started guides"""

        # Login and Setup
        login_content = """# Login & Setup

## Accessing the Portal

1. **Navigate to Portal**: Go to your assigned portal URL (e.g., `https://fwcareertest.streamlit.app`)
2. **Login Form**: You'll see a simple login form with username and password fields
3. **Enter Credentials**: Use the username and password provided by your administrator
4. **Sign In**: Click the "🔓 Sign In" button

## After Login

Once logged in successfully, you'll see the main interface with navigation tabs:

- **🔍 Job Search** - Main search interface
- **🗓️ Batches & Scheduling** - Automated job searches (if you have permission)
- **👥 Free Agents** - Manage Free Agent profiles
- **📊 Coach Analytics** - Performance and engagement metrics
- **🏢 Companies** - Company overview and statistics
- **⚙️ Admin Panel** - System administration (admin only)

## Initial Setup Tips

1. **Test Your Permissions**: Try accessing different tabs to see what features you have
2. **Start Small**: Begin with a test search (25 jobs) to familiarize yourself
3. **Check Analytics**: Visit the analytics dashboard to understand the interface
4. **Contact Admin**: If you can't access expected features, check with your administrator

## Troubleshooting Login

**Login not working?**
- Verify username and password are correct
- Try refreshing the page
- Contact your administrator if credentials don't work

**Interface not loading after login?**
- Wait 10-15 seconds for the interface to fully load
- Check your internet connection
- Try logging out and back in

---
*Next: [Understanding the Interface](understanding-interface.md)*
"""

        with open(self.output_dir / "getting-started" / "login-and-setup.md", 'w') as f:
            f.write(login_content)

        # Understanding Interface
        interface_content = """# Understanding the Interface

The FreeWorld Success Coach Portal uses a clean, tab-based interface designed for efficiency.

## Main Navigation

The interface uses horizontal radio button navigation at the top:

### 🔍 Job Search
Your primary workspace for finding jobs for Free Agents.

**Key Elements:**
- **Search Parameters**: Location, search terms, job quantity
- **Search Mode Buttons**: Memory Only vs Fresh searches
- **Classifier Selection**: CDL Traditional vs Career Pathways
- **Results Display**: Job listings with quality ratings

### 👥 Free Agents
Manage Free Agent profiles and generate personalized job lists.

**Key Elements:**
- **Agent Search**: Find agents by name, location, or preferences
- **Profile Management**: View and edit agent details
- **Portal Generation**: Create personalized job portals

### 📊 Coach Analytics
Monitor performance and Free Agent engagement.

**Key Tabs:**
- **Overview**: System-wide metrics
- **Individual Agents**: Per-agent engagement data
- **Admin Reports**: Coach performance (admin only)
- **Detailed Events**: Granular click tracking

### 🏢 Companies
View company performance and market presence.

**Features:**
- **Company Listings**: Top companies by job volume
- **Market Analysis**: Geographic distribution
- **Quality Metrics**: Average job ratings by company

### 🗓️ Batches & Scheduling *(Permission Required)*
Automate recurring job searches.

**Features:**
- **Indeed Batch Scheduling**: Set up automated Indeed searches
- **Google Batch Scheduling**: Configure Google Jobs automation
- **Schedule Management**: View and edit existing schedules

### ⚙️ Admin Panel *(Admin Only)*
System administration and user management.

**Features:**
- **User Management**: Add/edit coaches and permissions
- **System Settings**: Configure AI prompts and business rules
- **Performance Monitoring**: System-wide analytics

## Interface Tips

1. **Tab Memory**: The system remembers your last used settings in each tab
2. **Form Persistence**: Search parameters stay filled until you change them
3. **Real-time Updates**: Analytics and results update automatically
4. **Responsive Design**: Interface works on desktop and tablet devices

## Visual Indicators

- **Green Metrics**: Good performance indicators
- **Loading Spinners**: Appear during searches and data loading
- **Progress Bars**: Show search completion status
- **Color-coded Results**: Green (good), Yellow (so-so), Red (bad) job ratings

---
*Next: [Your First Search](first-search.md)*
"""

        with open(self.output_dir / "getting-started" / "understanding-interface.md", 'w') as f:
            f.write(interface_content)

    def _generate_field_definitions(self):
        """Generate comprehensive field definitions"""
        content = """# Complete Field Definitions

## Search Parameters

### Location
**Type**: Text Input
**Description**: Target geographic area for job search
**Examples**:
- "Houston, TX"
- "Dallas, TX"
- "Austin, TX"

**Tips**:
- Use "City, State" format for best results
- Stick to major metro areas for higher job volume
- Test with nearby cities if no results found

### Search Terms
**Type**: Text Input
**Description**: Keywords to find relevant jobs
**Examples**:
- "CDL driver" - For commercial driving positions
- "truck driver" - Broader driving jobs
- "warehouse, forklift" - Warehouse positions
- "dock worker" - Loading dock jobs

**Tips**:
- Use specific job titles for targeted results
- Combine related terms with commas
- Avoid overly specific requirements in search terms

### Job Quantity
**Type**: Select Dropdown
**Options**:
- **25 jobs (test)** - Quick test searches, lowest cost
- **100 jobs (sample)** - Standard search size for most use cases
- **500 jobs (medium)** - Comprehensive search for larger markets
- **1000+ jobs (full)** - Maximum search (admin permission required)

**Cost Impact**: Larger quantities use more API credits

## Search Modes

### 💾 Memory Only
**Description**: Search cached jobs from recent searches (last 72 hours)
**Speed**: Very fast (2-5 seconds)
**Cost**: Free
**When to Use**:
- Repeat searches in same location
- Quick results needed
- Testing search parameters
- Cost-conscious searching

### 🔍 Indeed Fresh Only
**Description**: Search fresh jobs directly from Indeed API
**Speed**: Moderate (30-90 seconds)
**Cost**: API charges apply
**When to Use**:
- New locations not recently searched
- Need latest job postings
- Memory search returns insufficient results

## AI Classification Types

### CDL Traditional
**Purpose**: Classify commercial driving jobs
**Best For**:
- CDL Class A/B driver positions
- Truck driving jobs
- Transportation roles
- OTR and local route jobs

**Output Classifications**:
- **Good**: High-quality CDL positions with good pay/benefits
- **So-So**: Acceptable but may prefer experience
- **Bad**: Poor conditions, misleading, or very low pay

### Career Pathways
**Purpose**: Identify career progression opportunities
**Best For**:
- Warehouse positions
- Entry-level jobs leading to CDL
- Skills-based progression paths
- Non-driving transportation jobs

**Pathway Categories**:
- `cdl_pathway` - Direct CDL driving opportunities
- `dock_to_driver` - Warehouse dock to CDL progression
- `warehouse_to_driver` - General warehouse to driving
- `internal_cdl_training` - Company-sponsored CDL programs
- `general_warehouse` - Standard warehouse positions

## Quality Ratings

### 🟢 Good Jobs
**Criteria**:
- Competitive pay ($60,000+ annually for CDL)
- Good benefits package
- Clear job requirements
- Stable companies
- Fair chance friendly

### 🟡 So-So Jobs
**Criteria**:
- Acceptable pay range
- Some benefits
- May prefer experience but not require it
- Decent working conditions
- Worth considering for right candidate

### 🟥 Bad Jobs
**Criteria**:
- Below-market pay
- Poor working conditions
- Misleading job descriptions
- Excessive requirements for entry-level
- Red flags in company reviews

## Route Types

### Local Routes
**Description**: Home daily, local/regional delivery
**Typical**:
- Within 150-mile radius
- Home every night
- Local delivery routes
- City/regional work

### OTR (Over-The-Road)
**Description**: Long-haul, multi-day trips
**Typical**:
- Multi-state routes
- Days/weeks away from home
- Higher pay potential
- Cross-country hauling

## Experience Levels

### Entry Level
**Description**: Jobs accepting new CDL holders or career changers
**Requirements**:
- Recent CDL graduates welcome
- Minimal experience required
- Training provided
- Career starter positions

### Experienced
**Description**: Jobs requiring prior driving or related experience
**Requirements**:
- 1+ years driving experience
- Proven safety record
- Specific endorsements
- Advanced skill sets

## Special Designations

### Fair Chance
**Description**: Employers open to candidates with criminal records
**Indicator**: ✅ Fair Chance designation in results
**Importance**: Critical for Free Agents with justice involvement

### Training Provided
**Description**: Companies offering CDL training or skills development
**Types**:
- Company-sponsored CDL school
- On-the-job training programs
- Skills advancement opportunities
- Apprenticeship programs

---
*For specific questions about field usage, see [Search Parameters Guide](search-parameters.md)*
"""

        with open(self.output_dir / "reference" / "field-definitions.md", 'w') as f:
            f.write(content)

    def _generate_daily_workflows(self):
        """Generate daily workflow guides"""

        # Basic Job Search
        basic_search_content = """# Basic Job Search

This is the most common workflow for finding jobs for Free Agents.

## Step 1: Navigate to Job Search

1. Click the **🔍 Job Search** tab in the main navigation
2. The search interface will load with parameter forms

## Step 2: Set Search Parameters

### Essential Parameters:
1. **Location**: Enter target city and state (e.g., "Houston, TX")
2. **Search Terms**: Enter relevant job keywords (e.g., "CDL driver")
3. **Job Quantity**: Select appropriate search size:
   - Start with "25 jobs (test)" for new locations
   - Use "100 jobs (sample)" for standard searches
   - Only use larger sizes for comprehensive market analysis

### Optional Parameters:
- **Classifier Type**: Choose based on job type:
  - "CDL Traditional" for driving jobs
  - "Career Pathways" for warehouse/progression jobs

## Step 3: Choose Search Mode

### Start with Memory Only (Recommended)
1. Click **💾 Memory Only** button first
2. Results appear in 2-5 seconds if location was recently searched
3. No API cost, very fast results
4. Shows jobs from last 72 hours of searches

### Use Fresh Search if Needed
1. If Memory Only returns few/no results, use **🔍 Indeed Fresh Only**
2. Takes 30-90 seconds but gets latest job postings
3. Uses API credits but provides fresh data
4. Best for new locations or when memory is stale

## Step 4: Review Results

### Results Display Includes:
- **Total Jobs Found**: Number at top of results
- **Quality Distribution**: Good/So-So/Bad breakdown
- **Route Distribution**: Local vs OTR breakdown
- **Job Listings**: Individual job details with ratings

### Quality Indicators:
- 🟢 **Good**: High-quality matches (target these)
- 🟡 **So-So**: Acceptable options (review carefully)
- 🟥 **Bad**: Avoid recommending these

## Step 5: Export Results (Optional)

1. Scroll to bottom of results
2. Configure PDF export options:
   - Maximum jobs to include
   - Quality levels to include
   - Route types to include
3. Click **Generate PDF Report**
4. PDF downloads with professional formatting

## Best Practices

### For Efficient Searches:
1. **Always try Memory Only first** - saves time and money
2. **Start small** - use 25 jobs to test new locations
3. **Use specific search terms** - "CDL driver" vs generic "driver"
4. **Check multiple nearby cities** if one returns few results

### For Quality Results:
1. **Focus on Good ratings** - these meet Free Agent needs best
2. **Review So-So jobs carefully** - may work for right candidate
3. **Avoid Bad jobs** - waste of time and hurt coach credibility
4. **Note Fair Chance indicators** - critical for many Free Agents

### Time-Saving Tips:
1. **Reuse successful parameters** - system remembers your settings
2. **Set up batch searches** for regular markets (if you have permission)
3. **Use analytics** to see which searches perform best
4. **Keep notes** on what works in each market

## Common Issues

**No results found?**
- Try broader search terms ("driver" instead of "CDL Class A driver")
- Test nearby cities ("Austin, TX" if "San Antonio, TX" fails)
- Switch to Indeed Fresh if Memory Only is empty

**Results taking too long?**
- Use smaller job quantity (25 instead of 100+)
- Check internet connection
- Try during off-peak hours

**Too many Bad jobs?**
- Adjust search terms to be more specific
- Try different classifier type
- Consider different location with better job market

---
*Next: [Advanced Search Options](advanced-search-options.md)*
"""

        with open(self.output_dir / "daily-workflows" / "basic-job-search.md", 'w') as f:
            f.write(basic_search_content)

    def _generate_features_guide(self):
        """Generate features guide"""

        # Search Modes
        search_modes_content = """# Search Modes & Types

Understanding when and how to use different search modes is key to efficient job searching.

## Search Modes

### 💾 Memory Only Search

**What it does**: Searches jobs cached from recent API calls (last 72 hours)

**Advantages**:
- ⚡ **Very Fast**: Results in 2-5 seconds
- 💰 **No Cost**: Uses cached data, no API charges
- 🔄 **Consistent**: Same results for repeated searches
- 🧠 **Smart Caching**: Automatically stores searches from all coaches

**When to Use**:
- Repeat searches in same location
- Quick results needed for client meetings
- Testing search parameters
- Cost-conscious searching
- Follow-up searches after initial fresh search

**Limitations**:
- Only returns results if location searched recently (72 hours)
- May miss newest job postings
- Limited to previously searched terms and locations

### 🔍 Indeed Fresh Only

**What it does**: Searches fresh jobs directly from Indeed API

**Advantages**:
- 🆕 **Latest Jobs**: Gets newest postings from Indeed
- 🌍 **Any Location**: Works for any US location
- 📈 **Complete Results**: Full job market coverage
- 🎯 **Custom Terms**: Search any keywords you specify

**When to Use**:
- New locations not recently searched
- Need absolutely latest job postings
- Memory search returns insufficient results (< 20 jobs)
- Exploring new markets
- Client needs comprehensive market analysis

**Considerations**:
- ⏱️ **Slower**: Takes 30-90 seconds to complete
- 💵 **API Cost**: Uses Indeed API credits
- 📊 **Rate Limited**: Limited searches per day
- 🔄 **Variable**: Results may vary between searches

## Search Strategy Recommendations

### Optimal Search Flow:
1. **Start with Memory Only** for any location
2. **Evaluate results** - if 20+ good jobs, you're done
3. **Use Indeed Fresh** if Memory returns < 20 jobs
4. **Memory will cache** Fresh results for future use

### Cost-Effective Approach:
- Use Memory Only 80% of the time
- Reserve Fresh searches for new markets or when memory is insufficient
- Set up batch schedules for regular markets to keep memory fresh

### Time-Efficient Approach:
- Always try Memory Only first (5 seconds vs 90 seconds)
- Use Fresh only when necessary
- Remember that Fresh results get cached for future Memory searches

## Classifier Types

### CDL Traditional

**Purpose**: Optimized for commercial driving job classification

**Best Results For**:
- CDL Class A/B driver positions
- Truck driving jobs (local, regional, OTR)
- Transportation and logistics roles
- Delivery driver positions

**Classification Focus**:
- Pay rates appropriate for driving work
- CDL requirements and endorsements
- Route types (local vs OTR)
- Experience requirements for drivers
- Benefits important to drivers (health, per-mile pay, home time)

**Output Quality**:
- 🟢 **Good**: $60,000+ annually, good benefits, fair requirements
- 🟡 **So-So**: Acceptable pay, may prefer experience
- 🟥 **Bad**: Below-market pay, poor conditions, misleading ads

### Career Pathways

**Purpose**: Identifies career progression opportunities and entry-level positions

**Best Results For**:
- Warehouse and logistics positions
- Entry-level jobs that can lead to CDL careers
- Skills-based progression opportunities
- Non-driving transportation roles

**Pathway Categories**:
- **CDL Pathway**: Direct commercial driving opportunities
- **Dock to Driver**: Warehouse loading dock positions that promote to driving
- **Warehouse to Driver**: General warehouse work with driving advancement
- **Internal CDL Training**: Companies offering CDL sponsorship/training
- **General Warehouse**: Standard warehouse and fulfillment center jobs

**Classification Focus**:
- Career advancement potential
- Training and skill development opportunities
- Entry requirements for career changers
- Progression timelines and pathways

## Job Quantity Selection

### 25 Jobs (Test)
**When to Use**:
- Testing new locations
- Quick parameter verification
- Cost-conscious exploration
- Client demo or preview

**Pros**: Fast, low cost, good for validation
**Cons**: May miss some opportunities in large markets

### 100 Jobs (Sample)
**When to Use**:
- Standard searches for most clients
- Balanced cost vs coverage
- Regular market assessment
- General Free Agent job searches

**Pros**: Good market coverage, reasonable cost, comprehensive results
**Cons**: May be overkill for small markets

### 500 Jobs (Medium)
**When to Use**:
- Large market comprehensive analysis
- Major client with high job needs
- Market research and reporting
- Building extensive job inventory

**Pros**: Extensive coverage, thorough market view
**Cons**: Higher cost, slower processing, may include lower-quality jobs

### 1000+ Jobs (Full) - *Admin Permission Required*
**When to Use**:
- Complete market saturation analysis
- Research and reporting projects
- Building maximum job databases
- Special projects requiring comprehensive data

**Pros**: Complete market coverage
**Cons**: High cost, long processing time, requires special permission

---
*Next: [AI Classification System](classification-types.md)*
"""

        with open(self.output_dir / "features-guide" / "search-modes.md", 'w') as f:
            f.write(search_modes_content)

    def _generate_troubleshooting(self):
        """Generate troubleshooting guide"""

        common_issues_content = """# Common Issues & Solutions

## Search Issues

### "No results found" or Very Few Results

**Possible Causes & Solutions**:

1. **Location not recently searched**
   - Try **Indeed Fresh Only** instead of Memory Only
   - Check spelling of city and state
   - Try nearby major cities (Houston instead of smaller suburbs)

2. **Search terms too specific**
   - Use broader terms: "driver" instead of "CDL Class A experienced driver"
   - Try "CDL driver" instead of specific job titles
   - Remove extra qualifiers and requirements

3. **Small job market**
   - Increase job quantity from 25 to 100
   - Expand to nearby metro areas
   - Try different search terms relevant to the area

4. **Memory cache is stale**
   - Use Indeed Fresh to populate memory with current jobs
   - Wait a few hours and try Memory Only again
   - Check if other coaches have searched this location recently

### Search Takes Too Long or Times Out

**Solutions**:

1. **Reduce job quantity**
   - Use 25 jobs for testing, 100 for normal searches
   - Avoid 500+ unless necessary for comprehensive analysis

2. **Check search mode**
   - Memory Only should complete in 5 seconds
   - Indeed Fresh typically takes 30-90 seconds
   - If Memory Only is slow, refresh the page

3. **Network issues**
   - Check internet connection stability
   - Try again during off-peak hours
   - Close other bandwidth-intensive applications

4. **System load**
   - Try again in a few minutes
   - Use smaller job quantities during busy periods
   - Consider scheduling batch searches for off-hours

### Poor Quality Results (Too Many "Bad" Jobs)

**Improvements**:

1. **Refine search terms**
   - Use more specific, professional job titles
   - Add quality indicators: "CDL driver benefits"
   - Avoid terms that attract low-quality postings

2. **Try different classifier**
   - CDL Traditional for driving jobs
   - Career Pathways for warehouse/entry-level positions

3. **Location considerations**
   - Some markets have better job quality than others
   - Major metro areas often have higher-quality positions
   - Consider expanding search radius

## Interface Issues

### Can't Access Certain Tabs or Features

**Check Permissions**:
- **🗓️ Batches & Scheduling**: Requires `can_access_batches` permission
- **Google Jobs features**: Requires `can_access_google_jobs` permission
- **⚙️ Admin Panel**: Admin-only access
- **Advanced Analytics**: May require elevated permissions

**Solutions**:
1. Contact your administrator to verify permission levels
2. Log out and log back in to refresh permissions
3. Verify you're using the correct login credentials

### Page Not Loading or Stuck

**Troubleshooting Steps**:
1. **Refresh the page** (F5 or Ctrl+R)
2. **Clear browser cache** and try again
3. **Try different browser** (Chrome, Firefox, Edge)
4. **Check browser console** for error messages (F12 → Console tab)
5. **Disable browser extensions** that might interfere

### Login Issues

**Username/Password Not Working**:
1. Verify credentials are correct (check caps lock)
2. Try typing instead of copy/paste
3. Contact administrator if credentials should work
4. Check for account lockouts or expiration

**Login Form Not Appearing**:
1. Wait 15-30 seconds for page to fully load
2. Refresh the page if form doesn't appear
3. Try opening in incognito/private browsing mode
4. Clear browser cookies and cache

## Export and PDF Issues

### PDF Generation Fails

**Common Fixes**:
1. **Reduce job count** in PDF export settings
2. **Check browser popup blocker** - may block PDF download
3. **Try different browser** - some handle PDFs better
4. **Ensure search has results** before attempting export

### PDF Missing Jobs or Data

**Settings to Check**:
1. **Maximum jobs setting** - may be set too low
2. **Quality level filters** - ensure "Good" and "So-So" are selected
3. **Route type filters** - check both "Local" and "OTR" if needed
4. **Search completed fully** before export

## Performance Issues

### Slow Response Times

**Optimization Tips**:
1. **Use Memory Only** searches whenever possible
2. **Start with small job quantities** (25-100)
3. **Close unnecessary browser tabs** and applications
4. **Check internet speed** - may need better connection
5. **Search during off-peak hours** (early morning, late evening)

### High API Costs

**Cost Management**:
1. **Prioritize Memory Only** searches (free)
2. **Use Fresh searches strategically** only when needed
3. **Start with test quantities** (25 jobs) for new locations
4. **Set up batch schedules** to keep memory fresh automatically
5. **Coordinate with other coaches** to avoid duplicate fresh searches

## Getting Help

### When to Contact Support

- **Permission issues** you can't resolve
- **Persistent technical problems** after trying troubleshooting
- **System errors** or unusual behavior
- **Questions about best practices** for your specific use case

### Information to Include

1. **Exact error messages** (screenshot if possible)
2. **Steps you were taking** when issue occurred
3. **Browser and version** you're using
4. **Search parameters** you were trying to use
5. **Whether issue is consistent** or intermittent

### Self-Help Resources

- **[Field Definitions](../reference/field-definitions.md)** - Parameter explanations
- **[Daily Workflows](../daily-workflows/)** - Step-by-step guides
- **[Features Guide](../features-guide/)** - Detailed feature explanations

---
*For additional support, contact your system administrator*
"""

        with open(self.output_dir / "troubleshooting" / "common-issues.md", 'w') as f:
            f.write(common_issues_content)

def generate_tutorial():
    """Generate complete tutorial documentation"""
    print("🚀 Generating FreeWorld Success Coach Portal Tutorial...")

    generator = QuickTutorialGenerator()
    generator.generate_complete_guide()

    print("✅ Tutorial generation complete!")
    print(f"📖 Open docs/coach-tutorial/README.md to get started")

if __name__ == "__main__":
    generate_tutorial()