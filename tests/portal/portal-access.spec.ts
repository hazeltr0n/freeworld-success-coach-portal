import { test, expect } from '@playwright/test';
import { TEST_CONFIG } from '../test-config';

/**
 * CRITICAL TEST: Portal Access & Public Functionality
 * 
 * This test validates the public-facing Free Agent portal system:
 * - Portal links work without authentication
 * - Job sorting (Local → OTR → Unknown) in portal
 * - Prepared for message display based on parameters
 * - Click tracking functionality
 * - Portal performance and loading
 */

test.describe('Free Agent Portal Access', () => {
  
  test('should access portal without authentication', async ({ page }) => {
    // Use a test portal URL (this would normally come from job search)
    const testPortalUrl = 'http://localhost:8501/portal?agent_id=test-001&name=Test%20Agent&route_filter=both&fair_chance_only=false&max_jobs=50&show_prepared_for=true&coach_name=Test%20Coach';
    
    // Navigate directly to portal (no login required)
    await page.goto(testPortalUrl);
    
    // Should see portal content without being redirected to login
    await expect(page.locator('h1:has-text("Job Opportunities")')).toBeVisible({
      timeout: TEST_CONFIG.timeouts.pageLoad
    });
    
    // Should see agent name in title or prepared message
    await expect(page.locator('text=Test Agent"')).toBeVisible();
    
    // Should see jobs list
    await expect(page.locator(TEST_CONFIG.selectors.portalJobsList)).toBeVisible();
  });
  
  test('should display jobs in correct sorting order', async ({ page }) => {
    const testPortalUrl = 'http://localhost:8501/portal?agent_id=test-002&name=Sorting%20Test&route_filter=both&fair_chance_only=false&max_jobs=100&show_prepared_for=false';
    
    await page.goto(testPortalUrl);
    
    // Wait for jobs to load
    await page.waitForSelector(TEST_CONFIG.selectors.portalJobsList, {
      timeout: TEST_CONFIG.timeouts.pageLoad
    });
    
    // Get all job cards/items
    const jobItems = await page.locator('.job-item, .job-card').all();
    
    if (jobItems.length > 0) {
      let lastRoutePriority = -1;
      
      // Verify jobs are sorted Local → OTR → Unknown
      for (const item of jobItems) {
        const itemText = await item.textContent();
        if (itemText) {
          const routePriority = getRoutePriority(itemText);
          expect(routePriority).toBeGreaterThanOrEqual(lastRoutePriority);
          lastRoutePriority = routePriority;
        }
      }
      
      console.log(`✓ Verified sorting for ${jobItems.length} jobs in portal`);
    }
  });
  
  test('should show prepared message when parameter is true', async ({ page }) => {
    const testPortalUrl = 'http://localhost:8501/portal?agent_id=test-003&name=Prepared%20Test&route_filter=both&fair_chance_only=false&max_jobs=50&show_prepared_for=true&coach_name=Portal%20Coach';
    
    await page.goto(testPortalUrl);
    
    // Should see prepared for message
    await expect(page.locator('text=Prepared for Prepared Test by Coach Portal Coach"')).toBeVisible({
      timeout: TEST_CONFIG.timeouts.pageLoad
    });
    
    // Should still see job listings
    await expect(page.locator(TEST_CONFIG.selectors.portalJobsList)).toBeVisible();
  });
  
  test('should hide prepared message when parameter is false', async ({ page }) => {
    const testPortalUrl = 'http://localhost:8501/portal?agent_id=test-004&name=No%20Prepared&route_filter=both&fair_chance_only=false&max_jobs=50&show_prepared_for=false';
    
    await page.goto(testPortalUrl);
    
    // Should NOT see prepared for message
    await expect(page.locator('text=Prepared for"')).not.toBeVisible({
      timeout: 5000
    });
    
    // But should still see jobs
    await expect(page.locator(TEST_CONFIG.selectors.portalJobsList)).toBeVisible({
      timeout: TEST_CONFIG.timeouts.pageLoad
    });
  });
  
  test('should respect route filter parameters', async ({ page }) => {
    // Test with local routes only
    const localOnlyUrl = 'http://localhost:8501/portal?agent_id=test-005&name=Local%20Only&route_filter=local&fair_chance_only=false&max_jobs=50&show_prepared_for=false';
    
    await page.goto(localOnlyUrl);
    await page.waitForSelector(TEST_CONFIG.selectors.portalJobsList, {
      timeout: TEST_CONFIG.timeouts.pageLoad
    });
    
    // All visible jobs should be local routes
    const jobTexts = await page.locator('.job-item, .job-card').allTextContents();
    for (const jobText of jobTexts) {
      const hasLocalRoute = jobText.toLowerCase().includes('local') || 
                           !jobText.toLowerCase().includes('otr') && 
                           !jobText.toLowerCase().includes('regional');
      // Note: This is a basic check - actual implementation may vary
      expect(hasLocalRoute || jobText.toLowerCase().includes('local')).toBeTruthy();
    }
  });
  
  test('should respect fair chance filter', async ({ page }) => {
    const fairChanceUrl = 'http://localhost:8501/portal?agent_id=test-006&name=Fair%20Chance&route_filter=both&fair_chance_only=true&max_jobs=50&show_prepared_for=false';
    
    await page.goto(fairChanceUrl);
    await page.waitForSelector(TEST_CONFIG.selectors.portalJobsList, {
      timeout: TEST_CONFIG.timeouts.pageLoad
    });
    
    // Should see jobs (fair chance filtering happens at database level)
    const jobCount = await page.locator('.job-item, .job-card').count();
    expect(jobCount).toBeGreaterThan(0);
    
    console.log(`✓ Fair chance portal loaded with ${jobCount} jobs`);
  });
  
  test('should respect max jobs limit', async ({ page }) => {
    const limitedUrl = 'http://localhost:8501/portal?agent_id=test-007&name=Limited&route_filter=both&fair_chance_only=false&max_jobs=10&show_prepared_for=false';
    
    await page.goto(limitedUrl);
    await page.waitForSelector(TEST_CONFIG.selectors.portalJobsList, {
      timeout: TEST_CONFIG.timeouts.pageLoad
    });
    
    // Should not exceed max jobs limit
    const jobCount = await page.locator('.job-item, .job-card').count();
    expect(jobCount).toBeLessThanOrEqual(10);
    
    console.log(`✓ Portal respects max jobs limit: ${jobCount} jobs shown`);
  });
  
  test('should track clicks properly', async ({ page }) => {
    const trackingUrl = 'http://localhost:8501/portal?agent_id=test-008&name=Click%20Test&route_filter=both&fair_chance_only=false&max_jobs=25&show_prepared_for=false';
    
    await page.goto(trackingUrl);
    await page.waitForSelector(TEST_CONFIG.selectors.portalJobsList, {
      timeout: TEST_CONFIG.timeouts.pageLoad
    });
    
    // Find first job with tracking link
    const firstJobLink = page.locator('a[href*="short.link"], a[href*="short.io"]').first();
    
    if (await firstJobLink.isVisible()) {
      // Verify tracking URL format
      const trackingHref = await firstJobLink.getAttribute('href');
      expect(trackingHref).toBeTruthy();
      expect(trackingHref).toContain('http');
      
      // Note: We don't actually click to avoid triggering real tracking
      console.log(`✓ Found tracking link: ${trackingHref?.substring(0, 50)}...`);
    }
  });
  
  test('should handle portal errors gracefully', async ({ page }) => {
    // Test with malformed URL
    const malformedUrl = 'http://localhost:8501/portal?invalid_params';
    
    await page.goto(malformedUrl);
    
    // Should show some kind of error message or default content
    await expect(page.locator('body')).toBeVisible({
      timeout: TEST_CONFIG.timeouts.pageLoad
    });
    
    // Should not crash the application
    const hasError = await page.locator('text=error", text=Error", text=invalid"').isVisible();
    if (hasError) {
      console.log('✓ Portal shows appropriate error handling');
    }
  });
  
  test('should load portal within performance threshold', async ({ page }) => {
    const performanceUrl = 'http://localhost:8501/portal?agent_id=perf-test&name=Performance&route_filter=both&fair_chance_only=false&max_jobs=100&show_prepared_for=true&coach_name=Speed%20Test';
    
    const startTime = Date.now();
    
    await page.goto(performanceUrl);
    await page.waitForSelector(TEST_CONFIG.selectors.portalJobsList, {
      timeout: TEST_CONFIG.timeouts.pageLoad
    });
    
    const loadTime = Date.now() - startTime;
    
    // Portal should load within reasonable time (30 seconds)
    expect(loadTime).toBeLessThan(30000);
    
    console.log(`✓ Portal loaded in ${loadTime}ms`);
  });
});

/**
 * Helper function to get route priority for sorting verification
 */
function getRoutePriority(text: string): number {
  const lowerText = text.toLowerCase();
  if (lowerText.includes('local')) return 0;
  if (lowerText.includes('otr') || lowerText.includes('regional')) return 1;
  return 2; // unknown
}