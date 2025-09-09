import { Page, expect } from '@playwright/test';
import { TEST_CONFIG } from '../test-config';
import { waitForStreamlitLoad } from './auth-helpers';

/**
 * Job Search helper functions for FreeWorld Coach Portal tests
 */

/**
 * Configure basic search parameters
 */
export async function configureSearch(page: Page, options: {
  locationType?: 'Select Market' | 'Custom Location';
  market?: string;
  customLocation?: string;
  jobQuantity?: number;
  searchTerms?: string;
  searchRadius?: number;
}) {
  // Navigate to Job Search tab if not already there
  const isOnJobSearch = await page.locator(TEST_CONFIG.selectors.jobSearchTab).isVisible();
  if (!isOnJobSearch) {
    await page.click(TEST_CONFIG.selectors.jobSearchTab);
    await waitForStreamlitLoad(page);
  }
  
  // Configure location type
  if (options.locationType) {
    await page.selectOption(TEST_CONFIG.selectors.locationTypeSelect, options.locationType);
    await waitForStreamlitLoad(page);
  }
  
  // Configure market or custom location
  if (options.market && options.locationType === 'Select Market') {
    await page.selectOption(TEST_CONFIG.selectors.marketSelect, options.market);
  } else if (options.customLocation && options.locationType === 'Custom Location') {
    await page.fill(TEST_CONFIG.selectors.customLocationInput, options.customLocation);
  }
  
  // Configure job quantity
  if (options.jobQuantity) {
    // Streamlit slider requires special handling
    await page.locator(TEST_CONFIG.selectors.jobQuantitySlider).fill(options.jobQuantity.toString());
  }
  
  // Configure search terms
  if (options.searchTerms) {
    await page.fill(TEST_CONFIG.selectors.searchTermsInput, options.searchTerms);
  }
  
  // Configure search radius
  if (options.searchRadius) {
    await page.selectOption(TEST_CONFIG.selectors.searchRadiusSelect, options.searchRadius.toString());
  }
}

/**
 * Configure PDF generation settings
 */
export async function configurePdfSettings(page: Page, options: {
  showPreparedFor?: boolean;
  enableHtmlPreview?: boolean;
  enablePortalLink?: boolean;
  routeFilter?: string[];
  qualityFilter?: string[];
  fairChanceOnly?: boolean;
  maxJobs?: number;
}) {
  // Scroll to PDF configuration section
  await page.locator('text="📄 Free Agent Portal/PDF Configuration"').scrollIntoViewIfNeeded();
  
  // Configure prepared for message toggle
  if (options.showPreparedFor !== undefined) {
    const toggle = page.locator(TEST_CONFIG.selectors.preparedForToggle);
    const isChecked = await toggle.isChecked();
    
    if (isChecked !== options.showPreparedFor) {
      await toggle.click();
    }
  }
  
  // Configure HTML preview
  if (options.enableHtmlPreview !== undefined) {
    const toggle = page.locator(TEST_CONFIG.selectors.htmlPreviewToggle);
    const isChecked = await toggle.isChecked();
    
    if (isChecked !== options.enableHtmlPreview) {
      await toggle.click();
    }
  }
  
  // Configure portal link generation
  if (options.enablePortalLink !== undefined) {
    const toggle = page.locator(TEST_CONFIG.selectors.portalLinkToggle);
    const isChecked = await toggle.isChecked();
    
    if (isChecked !== options.enablePortalLink) {
      await toggle.click();
    }
  }
  
  // Configure route filter
  if (options.routeFilter) {
    await page.selectOption(TEST_CONFIG.selectors.pdfRouteFilter, options.routeFilter);
  }
  
  // Configure quality filter (multi-select)
  if (options.qualityFilter) {
    const multiSelect = page.locator(TEST_CONFIG.selectors.pdfQualityFilter);
    
    // Clear existing selections
    await multiSelect.click();
    await page.keyboard.press('Control+a');
    await page.keyboard.press('Delete');
    
    // Select new options
    for (const quality of options.qualityFilter) {
      await multiSelect.click();
      await page.click(`text="${quality}"`);
    }
    
    // Click outside to close dropdown
    await page.click('body');
  }
  
  await waitForStreamlitLoad(page);
}

/**
 * Add Free Agent information for personalized results
 */
export async function addFreeAgentInfo(page: Page, options: {
  name?: string;
  uuid?: string;
  email?: string;
}) {
  // Find Free Agent Lookup section
  await page.locator('text="👤 Free Agent Lookup"').scrollIntoViewIfNeeded();
  
  if (options.name) {
    await page.fill('input[placeholder*="name"]', options.name);
  }
  
  if (options.uuid) {
    await page.fill('input[placeholder*="UUID"]', options.uuid);
  }
  
  if (options.email) {
    await page.fill('input[placeholder*="email"]', options.email);
  }
  
  await waitForStreamlitLoad(page);
}

/**
 * Execute a job search
 */
export async function runJobSearch(page: Page, searchType: 'fresh' | 'memory' | 'memory-only' = 'fresh') {
  let buttonSelector: string;
  
  switch (searchType) {
    case 'fresh':
      buttonSelector = TEST_CONFIG.selectors.runSearchButton;
      break;
    case 'memory':
      // Assuming memory search uses same button but with memory mode selected
      buttonSelector = TEST_CONFIG.selectors.runSearchButton;
      break;
    case 'memory-only':
      buttonSelector = TEST_CONFIG.selectors.memoryOnlyButton;
      break;
  }
  
  await page.click(buttonSelector);
  
  // Wait for search to complete
  await page.waitForSelector(TEST_CONFIG.selectors.resultsTable, {
    timeout: TEST_CONFIG.timeouts.search
  });
  
  await waitForStreamlitLoad(page);
}

/**
 * Verify search results are displayed
 */
export async function verifySearchResults(page: Page) {
  // Check that results table is visible
  await expect(page.locator(TEST_CONFIG.selectors.resultsTable)).toBeVisible();
  
  // Check that we have some job results
  const jobRows = await page.locator('[data-testid="stDataFrame"] tbody tr').count();
  expect(jobRows).toBeGreaterThan(0);
}

/**
 * Verify job sorting order (Local → OTR → Unknown)
 */
export async function verifyJobSorting(page: Page) {
  // Get all route type values from the results table
  const routeValues = await page.locator('[data-testid="stDataFrame"] tbody tr td:nth-child(5)').allTextContents();
  
  let lastPriority = -1;
  
  for (const route of routeValues) {
    let currentPriority: number;
    
    if (route.toLowerCase().includes('local')) {
      currentPriority = 0;
    } else if (route.toLowerCase().includes('otr') || route.toLowerCase().includes('regional')) {
      currentPriority = 1;
    } else {
      currentPriority = 2; // Unknown
    }
    
    // Verify sorting order is maintained
    expect(currentPriority).toBeGreaterThanOrEqual(lastPriority);
    lastPriority = currentPriority;
  }
}

/**
 * Generate and download PDF
 */
export async function generatePdf(page: Page): Promise<boolean> {
  try {
    // Click PDF download button
    await page.click(TEST_CONFIG.selectors.pdfDownloadButton);
    
    // Wait for PDF generation (this might trigger a download)
    await page.waitForTimeout(TEST_CONFIG.timeouts.pdfGeneration);
    
    return true;
  } catch (error) {
    console.error('PDF generation failed:', error);
    return false;
  }
}

/**
 * Verify HTML preview is displayed correctly
 */
export async function verifyHtmlPreview(page: Page, options: {
  shouldShowPreparedFor?: boolean;
  agentName?: string;
  coachName?: string;
}) {
  // Check that HTML preview is visible
  await expect(page.locator(TEST_CONFIG.selectors.htmlPreview)).toBeVisible();
  
  // Verify prepared for message based on toggle setting
  if (options.shouldShowPreparedFor && options.agentName) {
    await expect(page.locator(TEST_CONFIG.selectors.preparedForMessage)).toBeVisible();
    
    if (options.coachName) {
      await expect(page.locator(`text=Prepared for ${options.agentName} by Coach ${options.coachName}"`)).toBeVisible();
    }
  } else {
    await expect(page.locator(TEST_CONFIG.selectors.preparedForMessage)).not.toBeVisible();
  }
}

/**
 * Get generated portal link
 */
export async function getPortalLink(page: Page): Promise<string | null> {
  try {
    // Look for portal link in the results
    const linkElement = await page.locator('text=https://"').first();
    const linkText = await linkElement.textContent();
    
    return linkText?.trim() || null;
  } catch (error) {
    console.error('Could not find portal link:', error);
    return null;
  }
}