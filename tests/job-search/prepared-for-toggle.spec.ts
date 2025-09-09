import { test, expect } from '@playwright/test';
import { loginAsAdmin, navigateToTab, waitForStreamlitLoad } from '../helpers/auth-helpers';
import { 
  configureSearch, 
  configurePdfSettings, 
  addFreeAgentInfo, 
  runJobSearch,
  verifyHtmlPreview,
  getPortalLink
} from '../helpers/job-search-helpers';
import { TEST_CONFIG } from '../test-config';

/**
 * CRITICAL TEST: Prepared For Message Toggle
 * 
 * This test validates the recent fix for the prepared for message toggle.
 * The toggle should control whether the "Prepared for [Name] by Coach [Coach]" 
 * message appears in HTML preview, PDFs, and portal links.
 */

test.describe('Prepared For Message Toggle', () => {
  
  test('should show prepared message when toggle is ON', async ({ page }) => {
    // Login as admin (has all permissions)
    await loginAsAdmin(page);
    
    // Navigate to Job Search tab
    await navigateToTab(page, '🔍 Job Search');
    
    // Configure basic search
    await configureSearch(page, {
      locationType: 'Select Market',
      market: 'Houston',
      jobQuantity: 25,
      searchTerms: 'CDL driver',
    });
    
    // Add Free Agent info for personalization
    await addFreeAgentInfo(page, {
      name: 'John Test Driver',
      uuid: 'test-001',
    });
    
    // Configure PDF settings with prepared message ON
    await configurePdfSettings(page, {
      showPreparedFor: true,
      enableHtmlPreview: true,
      enablePortalLink: true,
    });
    
    // Run memory-only search (faster for testing)
    await runJobSearch(page, 'memory-only');
    
    // Wait for results
    await waitForStreamlitLoad(page);
    
    // Verify HTML preview shows prepared message
    await verifyHtmlPreview(page, {
      shouldShowPreparedFor: true,
      agentName: 'John Test Driver',
      coachName: 'Admin Test User',
    });
    
    // Get portal link and verify it works
    const portalLink = await getPortalLink(page);
    expect(portalLink).toBeTruthy();
    
    if (portalLink) {
      // Open portal in new page
      const portalPage = await page.context().newPage();
      await portalPage.goto(portalLink);
      
      // Verify prepared message appears in portal
      await expect(portalPage.locator('text=Prepared for John Test Driver"')).toBeVisible({
        timeout: TEST_CONFIG.timeouts.pageLoad
      });
      
      await portalPage.close();
    }
  });
  
  test('should hide prepared message when toggle is OFF', async ({ page }) => {
    // Login as admin
    await loginAsAdmin(page);
    
    // Navigate to Job Search tab
    await navigateToTab(page, '🔍 Job Search');
    
    // Configure basic search
    await configureSearch(page, {
      locationType: 'Select Market',
      market: 'Houston',
      jobQuantity: 25,
      searchTerms: 'CDL driver',
    });
    
    // Add Free Agent info for personalization
    await addFreeAgentInfo(page, {
      name: 'Jane Test Driver',
      uuid: 'test-002',
    });
    
    // Configure PDF settings with prepared message OFF
    await configurePdfSettings(page, {
      showPreparedFor: false, // This is the key test!
      enableHtmlPreview: true,
      enablePortalLink: true,
    });
    
    // Run memory-only search
    await runJobSearch(page, 'memory-only');
    
    // Wait for results
    await waitForStreamlitLoad(page);
    
    // Verify HTML preview does NOT show prepared message
    await verifyHtmlPreview(page, {
      shouldShowPreparedFor: false,
      agentName: 'Jane Test Driver',
    });
    
    // Get portal link and verify prepared message is hidden
    const portalLink = await getPortalLink(page);
    expect(portalLink).toBeTruthy();
    
    if (portalLink) {
      // Open portal in new page
      const portalPage = await page.context().newPage();
      await portalPage.goto(portalLink);
      
      // Verify prepared message does NOT appear in portal
      await expect(portalPage.locator('text=Prepared for"')).not.toBeVisible({
        timeout: 5000
      });
      
      // But verify the jobs are still shown
      await expect(portalPage.locator(TEST_CONFIG.selectors.portalJobsList)).toBeVisible({
        timeout: TEST_CONFIG.timeouts.pageLoad
      });
      
      await portalPage.close();
    }
  });
  
  test('should persist toggle state across searches', async ({ page }) => {
    // Login as admin
    await loginAsAdmin(page);
    
    // Navigate to Job Search tab
    await navigateToTab(page, '🔍 Job Search');
    
    // Configure basic search
    await configureSearch(page, {
      locationType: 'Select Market',
      market: 'Dallas',
      jobQuantity: 25,
    });
    
    // Set toggle OFF
    await configurePdfSettings(page, {
      showPreparedFor: false,
      enableHtmlPreview: true,
    });
    
    // Verify toggle is OFF
    const toggle = page.locator(TEST_CONFIG.selectors.preparedForToggle);
    await expect(toggle).not.toBeChecked();
    
    // Run first search
    await runJobSearch(page, 'memory-only');
    await waitForStreamlitLoad(page);
    
    // Verify toggle is still OFF after search
    await expect(toggle).not.toBeChecked();
    
    // Run second search with different parameters
    await configureSearch(page, {
      market: 'Austin',
      jobQuantity: 50,
    });
    
    await runJobSearch(page, 'memory-only');
    await waitForStreamlitLoad(page);
    
    // Verify toggle state persisted
    await expect(toggle).not.toBeChecked();
    
    // Now turn toggle ON
    await toggle.click();
    await expect(toggle).toBeChecked();
    
    // Run another search
    await runJobSearch(page, 'memory-only');
    await waitForStreamlitLoad(page);
    
    // Verify toggle is still ON
    await expect(toggle).toBeChecked();
  });
  
  test('should work with both admin and regular coach', async ({ page }) => {
    // Test with regular coach (not just admin)
    await loginAsAdmin(page); // Start with admin, then switch
    
    // Logout and login as regular coach
    await page.click('text="☰"');
    await page.click('text="🚪 Sign Out"');
    
    // Login as regular coach
    await page.fill(TEST_CONFIG.selectors.usernameInput, TEST_CONFIG.coaches.regularCoach.username);
    await page.fill(TEST_CONFIG.selectors.passwordInput, TEST_CONFIG.coaches.regularCoach.password);
    await page.click(TEST_CONFIG.selectors.loginButton);
    
    await waitForStreamlitLoad(page);
    
    // Navigate to Job Search
    await navigateToTab(page, '🔍 Job Search');
    
    // Configure search with prepared message OFF
    await configureSearch(page, {
      locationType: 'Select Market',
      market: 'Houston',
      jobQuantity: 25,
    });
    
    await addFreeAgentInfo(page, {
      name: 'Coach Test Agent',
      uuid: 'test-coach-001',
    });
    
    await configurePdfSettings(page, {
      showPreparedFor: false,
      enableHtmlPreview: true,
    });
    
    // Run search
    await runJobSearch(page, 'memory-only');
    await waitForStreamlitLoad(page);
    
    // Verify prepared message is hidden even for regular coach
    await verifyHtmlPreview(page, {
      shouldShowPreparedFor: false,
      agentName: 'Coach Test Agent',
    });
  });
  
});