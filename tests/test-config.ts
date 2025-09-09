/**
 * Test configuration and test data for FreeWorld Success Coach Portal
 */

export interface TestCoach {
  username: string;
  password: string;
  fullName: string;
  role: 'admin' | 'coach';
  permissions: {
    canGeneratePdf: boolean;
    canAccessBatches: boolean;
    canForceFreshClassification: boolean;
  };
}

export interface TestAgent {
  name: string;
  email: string;
  uuid: string;
  location: string;
  routeFilter: 'local' | 'otr' | 'both';
  fairChanceOnly: boolean;
  maxJobs: number;
}

export const TEST_CONFIG = {
  // Test environment URLs
  baseUrl: 'http://localhost:8501',
  
  // Test timeouts (in milliseconds)
  timeouts: {
    pageLoad: 30000,
    elementLoad: 10000,
    apiCall: 15000,
    search: 60000, // Job searches can take time
    pdfGeneration: 30000,
  },
  
  // Test coaches
  coaches: {
    admin: {
      username: 'admin.test',
      password: 'TestPass123',
      fullName: 'Admin Test User',
      role: 'admin' as const,
      permissions: {
        canGeneratePdf: true,
        canAccessBatches: true,
        canForceFreshClassification: true,
      }
    } as TestCoach,
    
    regularCoach: {
      username: 'coach.test',
      password: 'CoachPass123',
      fullName: 'Regular Coach Test',
      role: 'coach' as const,
      permissions: {
        canGeneratePdf: true,
        canAccessBatches: false,
        canForceFreshClassification: false,
      }
    } as TestCoach,
    
    restrictedCoach: {
      username: 'restricted.test',
      password: 'RestrictedPass123',
      fullName: 'Restricted Coach Test',
      role: 'coach' as const,
      permissions: {
        canGeneratePdf: false,
        canAccessBatches: false,
        canForceFreshClassification: false,
      }
    } as TestCoach,
  },
  
  // Test agents
  agents: {
    activeAgent: {
      name: 'John Test Driver',
      email: 'john.test@example.com',
      uuid: 'test-agent-001',
      location: 'Houston',
      routeFilter: 'both',
      fairChanceOnly: false,
      maxJobs: 25,
    } as TestAgent,
    
    deletedAgent: {
      name: 'Jane Deleted Driver',
      email: 'jane.deleted@example.com',
      uuid: 'test-agent-002',
      location: 'Dallas',
      routeFilter: 'local',
      fairChanceOnly: true,
      maxJobs: 15,
    } as TestAgent,
  },
  
  // Test search parameters
  searchParams: {
    defaultLocation: 'Houston',
    testKeywords: 'CDL driver',
    jobQuantity: 50,
    searchRadius: 25,
  },
  
  // Expected UI elements (selectors)
  selectors: {
    // Authentication
    loginForm: '[data-testid="stForm"]',
    usernameInput: 'input[type="text"]',
    passwordInput: 'input[type="password"]', 
    loginButton: 'button:has-text("🔓 Sign In")',
    
    // Navigation
    tabNavigation: '[data-testid="stHorizontalBlock"]',
    jobSearchTab: 'text="🔍 Job Search"',
    freeAgentsTab: 'text="👥 Free Agents"',
    analyticsTab: 'text="📊 Coach Analytics"',
    companiesTab: 'text="🏢 Companies"',
    batchesTab: 'text="🗓️ Batches & Scheduling"',
    adminTab: 'text="👑 Admin Panel"',
    
    // Job Search
    locationTypeSelect: 'select:first',
    marketSelect: 'select[key*="market"]',
    customLocationInput: 'input[placeholder*="location"]',
    jobQuantitySlider: '[data-testid="stSlider"]',
    searchTermsInput: 'input[placeholder*="search terms"]',
    searchRadiusSelect: 'select[key*="radius"]',
    
    // PDF Configuration
    preparedForToggle: 'input[key="tab_show_prepared_for"]',
    htmlPreviewToggle: 'input[key="tab_show_html_preview"]',
    portalLinkToggle: 'input[key="tab_generate_portal_link"]',
    pdfRouteFilter: 'select[key*="route"]',
    pdfQualityFilter: '[data-testid="stMultiSelect"]',
    
    // Search execution
    runSearchButton: 'button:has-text("🚀 Run Job Search")',
    memoryOnlyButton: 'button:has-text("Memory Only")',
    
    // Results
    resultsTable: '[data-testid="stDataFrame"]',
    pdfDownloadButton: 'button:has-text("📥 Download PDF")',
    htmlPreview: '[data-testid="stHtml"]',
    
    // Free Agents
    agentTable: '[data-testid="stDataEditor"]',
    addManualAgentButton: 'button:has-text("➕ Add Manual Agent")',
    showDeletedCheckbox: 'input:has-text("Show Deleted")',
    restoreButton: 'button:has-text("🔄 Confirm Restore Selected")',
    
    // Portal
    portalJobsList: '.job-card, .job-item',
    preparedForMessage: 'text=Prepared for"',
  },
  
  // Expected behaviors
  expectations: {
    // Job sorting order
    jobSortingOrder: ['Local', 'OTR', 'Regional', 'Unknown'],
    
    // Required fields
    requiredSearchFields: ['location'],
    requiredAgentFields: ['name', 'location'],
    
    // PDF generation
    expectedPdfSections: [
      'CDL Jobs',
      'quality jobs',
    ],
    
    // Portal access
    portalRequiredParams: ['agent', 'token'],
  }
};

export default TEST_CONFIG;