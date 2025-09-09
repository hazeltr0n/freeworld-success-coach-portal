import { test, expect } from '@playwright/test';
import { loginAsAdmin, navigateToTab, waitForStreamlitLoad } from '../helpers/auth-helpers';
import { 
  configureSearch, 
  runJobSearch,
  verifySearchResults,
  verifyJobSorting,
  getPortalLink
} from '../helpers/job-search-helpers';
import { TEST_CONFIG } from '../test-config';

/**
 * CRITICAL TEST: Job Sorting Order (Local → OTR → Unknown)
 * 
 * This test validates the recent fix for job sorting across all outputs:
 * - HTML preview
 * - PDF generation 
 * - Portal links
 * - Results table
 */

test.describe('Job Sorting Order', () => {
  
  test('should sort jobs Local → OTR → Unknown in search results', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '🔍 Job Search');
    
    // Configure search to get mixed route types
    await configureSearch(page, {
      locationType: 'Select Market',
      market: 'Houston', // Large market likely to have mixed routes
      jobQuantity: 100, // Get more jobs to test sorting
      searchTerms: 'CDL truck driver',
      searchRadius: 50, // Wider radius for more variety
    });
    
    // Run fresh search to get latest data
    await runJobSearch(page, 'fresh');
    
    // Verify results are displayed
    await verifySearchResults(page);
    
    // Verify job sorting order
    await verifyJobSorting(page);
    
    // Also check that quality jobs appear first within each route category
    await verifyQualityWithinRoutes(page);
  });
  
  test('should maintain sorting in HTML preview', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '🔍 Job Search');
    
    await configureSearch(page, {
      locationType: 'Select Market',
      market: 'Dallas',
      jobQuantity: 50,
      searchTerms: 'CDL',
    });
    
    // Enable HTML preview
    await configurePdfSettings(page, {
      enableHtmlPreview: true,
    });
    
    await runJobSearch(page, 'memory-only');
    await waitForStreamlitLoad(page);
    
    // Verify HTML preview is visible
    await expect(page.locator(TEST_CONFIG.selectors.htmlPreview)).toBeVisible();
    
    // Check sorting in HTML preview
    await verifySortingInHtmlPreview(page);
  });
  
  test('should maintain sorting in portal links', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '🔍 Job Search');
    
    await configureSearch(page, {
      locationType: 'Select Market',
      market: 'Austin',
      jobQuantity: 30,
    });
    
    // Enable portal link generation
    await configurePdfSettings(page, {
      enablePortalLink: true,
    });
    
    await runJobSearch(page, 'memory-only');
    await waitForStreamlitLoad(page);
    
    // Get portal link
    const portalLink = await getPortalLink(page);
    expect(portalLink).toBeTruthy();
    
    if (portalLink) {
      // Open portal and verify sorting
      const portalPage = await page.context().newPage();
      await portalPage.goto(portalLink);
      
      // Wait for jobs to load in portal
      await expect(portalPage.locator(TEST_CONFIG.selectors.portalJobsList)).toBeVisible({
        timeout: TEST_CONFIG.timeouts.pageLoad
      });
      
      // Verify sorting in portal
      await verifySortingInPortal(portalPage);
      
      await portalPage.close();
    }
  });
  
  test('should sort consistently across different markets', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '🔍 Job Search');
    
    const markets = ['Houston', 'Dallas', 'Austin'];
    
    for (const market of markets) {
      await configureSearch(page, {
        locationType: 'Select Market',
        market: market,
        jobQuantity: 50,
      });
      
      await runJobSearch(page, 'memory-only');
      await waitForStreamlitLoad(page);
      
      await verifySearchResults(page);
      await verifyJobSorting(page);
      
      console.log(`✓ Verified sorting for ${market}`);
    }
  });
  
  test('should sort correctly with route filters applied', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '🔍 Job Search');
    
    await configureSearch(page, {
      locationType: 'Select Market',
      market: 'Houston',
      jobQuantity: 100,
    });
    
    // Test with Local routes only
    await configurePdfSettings(page, {
      routeFilter: ['Local'],
      enableHtmlPreview: true,
    });
    
    await runJobSearch(page, 'memory-only');
    await waitForStreamlitLoad(page);
    
    // Verify only Local routes are shown
    await verifyRouteFilter(page, ['Local']);
    
    // Test with OTR routes only
    await configurePdfSettings(page, {
      routeFilter: ['OTR'],
    });
    
    await runJobSearch(page, 'memory-only');
    await waitForStreamlitLoad(page);
    
    // Verify only OTR routes are shown
    await verifyRouteFilter(page, ['OTR']);
    
    // Test with Both routes
    await configurePdfSettings(page, {
      routeFilter: ['Both'],
    });
    
    await runJobSearch(page, 'memory-only');
    await waitForStreamlitLoad(page);
    
    // Verify mixed routes are shown in correct order
    await verifyJobSorting(page);
  });
});

/**
 * Helper function to verify quality ordering within route categories
 */
async function verifyQualityWithinRoutes(page) {
  // Get all job rows
  const rows = await page.locator('[data-testid="stDataFrame"] tbody tr').all();
  
  let currentRoute = '';
  let lastQuality = 0; // 0 = good, 1 = so-so, 2 = bad
  
  for (const row of rows) {
    const routeCell = await row.locator('td:nth-child(5)').textContent(); // Assuming route is 5th column
    const qualityCell = await row.locator('td:nth-child(3)').textContent(); // Assuming quality is 3rd column
    
    if (routeCell && qualityCell) {
      // If we're still in the same route category
      if (routeCell === currentRoute) {
        const currentQuality = getQualityPriority(qualityCell);
        expect(currentQuality).toBeGreaterThanOrEqual(lastQuality);
        lastQuality = currentQuality;
      } else {
        // New route category, reset quality tracking
        currentRoute = routeCell;
        lastQuality = getQualityPriority(qualityCell);
      }
    }
  }
}

/**
 * Helper function to get quality priority for sorting verification
 */
function getQualityPriority(quality: string): number {
  if (quality.toLowerCase().includes('good')) return 0;
  if (quality.toLowerCase().includes('so-so')) return 1;
  return 2; // bad or unknown
}

/**
 * Helper function to verify sorting in HTML preview
 */
async function verifySortingInHtmlPreview(page) {
  // The HTML preview contains job cards, let's verify their order
  const jobCards = await page.locator('[data-testid="stHtml"] .job-card, [data-testid="stHtml"] .job-item').all();
  
  if (jobCards.length > 0) {
    let lastRoutePriority = -1;
    
    for (const card of jobCards) {
      const cardText = await card.textContent();
      if (cardText) {
        const routePriority = getRoutePriority(cardText);
        expect(routePriority).toBeGreaterThanOrEqual(lastRoutePriority);
        lastRoutePriority = routePriority;
      }
    }
  }
}

/**
 * Helper function to verify sorting in portal
 */
async function verifySortingInPortal(portalPage) {
  const jobItems = await portalPage.locator('.job-card, .job-item').all();
  
  if (jobItems.length > 0) {
    let lastRoutePriority = -1;
    
    for (const item of jobItems) {
      const itemText = await item.textContent();
      if (itemText) {
        const routePriority = getRoutePriority(itemText);
        expect(routePriority).toBeGreaterThanOrEqual(lastRoutePriority);
        lastRoutePriority = routePriority;
      }
    }
  }
}

/**
 * Helper function to get route priority for sorting verification
 */
function getRoutePriority(text: string): number {
  const lowerText = text.toLowerCase();
  if (lowerText.includes('local')) return 0;
  if (lowerText.includes('otr') || lowerText.includes('regional')) return 1;
  return 2; // unknown
}

/**
 * Helper function to verify route filter is working
 */
async function verifyRouteFilter(page, allowedRoutes: string[]) {
  const routeCells = await page.locator('[data-testid="stDataFrame"] tbody tr td:nth-child(5)').allTextContents();
  
  for (const routeText of routeCells) {
    const hasAllowedRoute = allowedRoutes.some(route => 
      routeText.toLowerCase().includes(route.toLowerCase())
    );
    expect(hasAllowedRoute).toBeTruthy();
  }
}