# Complete Field Definitions

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
