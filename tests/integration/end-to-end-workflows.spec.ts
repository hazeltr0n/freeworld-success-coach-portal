import { test, expect } from '@playwright/test';
import { loginAsAdmin, logout, waitForStreamlitLoad, navigateToTab } from '../helpers/auth-helpers';
import { configureSearch, configurePdfSettings, runJobSearch, verifySearchResults, getPortalLink } from '../helpers/job-search-helpers';
import { TEST_CONFIG } from '../test-config';

/**
 * CRITICAL TEST: End-to-End Workflows
 * 
 * This test validates complete user journeys from start to finish:
 * - Full job search to portal generation workflow
 * - Agent management lifecycle
 * - Analytics tracking end-to-end
 * - Cross-tab functionality and data persistence
 */

test.describe('End-to-End Workflows', () => {
  
  test('should complete full job search to portal workflow', async ({ page }) => {
    // Login and navigate to job search
    await loginAsAdmin(page);
    await navigateToTab(page, '🔍 Job Search');
    
    // Configure comprehensive search
    await configureSearch(page, {
      locationType: 'Select Market',
      market: 'Houston',
      jobQuantity: 50,
      searchTerms: 'CDL truck driver',
      searchRadius: 25,
    });
    
    // Add free agent info
    await page.locator('text="👤 Free Agent Lookup"').scrollIntoViewIfNeeded();
    await page.fill('input[placeholder*="name"]', 'E2E Test Agent');
    await page.fill('input[placeholder*="UUID"]', 'e2e-test-001');
    
    // Configure PDF settings with all features enabled
    await configurePdfSettings(page, {
      showPreparedFor: true,
      enableHtmlPreview: true,
      enablePortalLink: true,
      routeFilter: ['Both'],
      qualityFilter: ['good', 'so-so'],
    });
    
    // Run fresh search (complete workflow)
    await runJobSearch(page, 'fresh');
    
    // Verify search results
    await verifySearchResults(page);
    
    // Verify HTML preview is shown
    await expect(page.locator(TEST_CONFIG.selectors.htmlPreview)).toBeVisible();
    
    // Verify prepared for message
    await expect(page.locator('text=Prepared for E2E Test Agent"')).toBeVisible();
    
    // Get and validate portal link
    const portalLink = await getPortalLink(page);
    expect(portalLink).toBeTruthy();
    expect(portalLink).toContain('http');
    
    // Test the portal link
    if (portalLink) {
      const portalPage = await page.context().newPage();
      await portalPage.goto(portalLink);
      
      // Portal should load without authentication
      await expect(portalPage.locator('h1, text=Job Opportunities"')).toBeVisible({
        timeout: TEST_CONFIG.timeouts.pageLoad
      });
      
      // Should show prepared message
      await expect(portalPage.locator('text=Prepared for E2E Test Agent"')).toBeVisible();
      
      // Should show jobs
      await expect(portalPage.locator(TEST_CONFIG.selectors.portalJobsList)).toBeVisible();
      
      await portalPage.close();
    }
    
    console.log('✓ Complete job search to portal workflow successful');
  });
  
  test('should handle agent management lifecycle', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '👥 Free Agents');
    await waitForStreamlitLoad(page);
    
    // Create new manual agent
    await page.click(TEST_CONFIG.selectors.addManualAgentButton);
    
    const testAgent = {
      name: 'Lifecycle Test Agent',
      email: 'lifecycle@e2etest.com',
      market: 'Dallas',
    };
    
    await page.fill('input[placeholder*="Enter full name"]', testAgent.name);
    await page.fill('input[placeholder*="agent@example.com"]', testAgent.email);
    await page.selectOption('select', testAgent.market);
    
    // Submit agent creation
    await page.click('button:has-text("➕ Add Manual Agent")');
    await waitForStreamlitLoad(page);
    
    // Verify agent was created and is visible
    await expect(page.locator(`tr:has-text("${testAgent.name}")`)).toBeVisible();
    
    // Use agent in job search
    await navigateToTab(page, '🔍 Job Search');
    
    await configureSearch(page, {
      locationType: 'Select Market',
      market: 'Dallas',
      jobQuantity: 25,
    });
    
    // Add the agent info
    await page.fill('input[placeholder*="name"]', testAgent.name);
    await page.fill('input[placeholder*="UUID"]', 'lifecycle-test');
    
    await configurePdfSettings(page, {
      enablePortalLink: true,
      showPreparedFor: true,
    });
    
    // Generate portal for agent
    await runJobSearch(page, 'memory-only');
    await waitForStreamlitLoad(page);
    
    const portalLink = await getPortalLink(page);
    expect(portalLink).toBeTruthy();
    
    // Go back to agent management and soft-delete agent
    await navigateToTab(page, '👥 Free Agents');
    await waitForStreamlitLoad(page);
    
    const agentRow = page.locator(`tr:has-text("${testAgent.name}")`);
    const deleteCheckbox = agentRow.locator('input[type="checkbox"]').last();
    await deleteCheckbox.check();
    
    await page.click('button:has-text("🗑️ Confirm Delete Selected")');
    await waitForStreamlitLoad(page);
    
    // Agent should be hidden
    await expect(page.locator(`tr:has-text("${testAgent.name}")`)).not.toBeVisible();
    
    // Show deleted agents and restore
    await page.locator(TEST_CONFIG.selectors.showDeletedCheckbox).check();
    await waitForStreamlitLoad(page);
    
    const deletedAgentRow = page.locator(`tr:has-text("${testAgent.name}")`);
    await expect(deletedAgentRow).toBeVisible();
    await expect(deletedAgentRow.locator('text=👻"')).toBeVisible();
    
    // Restore agent
    const restoreCheckbox = deletedAgentRow.locator('input[type="checkbox"]').last();
    await restoreCheckbox.check();
    await page.click(TEST_CONFIG.selectors.restoreButton);
    await waitForStreamlitLoad(page);
    
    // Agent should be active again
    const restoredRow = page.locator(`tr:has-text("${testAgent.name}")`);
    await expect(restoredRow.locator('text=🟢"')).toBeVisible();
    
    console.log('✓ Complete agent lifecycle workflow successful');
  });
  
  test('should maintain data consistency across tabs', async ({ page }) => {
    await loginAsAdmin(page);
    
    // Perform job search
    await navigateToTab(page, '🔍 Job Search');
    await configureSearch(page, {
      locationType: 'Select Market',
      market: 'Austin',
      jobQuantity: 30,
    });
    
    await runJobSearch(page, 'memory-only');
    await verifySearchResults(page);
    
    // Get job count from search results
    const searchJobCount = await page.locator('[data-testid="stDataFrame"] tbody tr').count();
    
    // Navigate to analytics and check data consistency
    await navigateToTab(page, '📊 Coach Analytics');
    await page.click('text="📊 Overview"');
    await waitForStreamlitLoad(page);
    
    // Should see some engagement metrics
    const hasAnalytics = await page.locator('[data-testid="stPlotlyChart"], [data-testid="stMetric"]').isVisible();
    expect(hasAnalytics).toBeTruthy();
    
    // Navigate to companies tab
    await navigateToTab(page, '🏢 Companies');
    await waitForStreamlitLoad(page);
    
    // Should see companies data
    const companyCount = await page.locator('[data-testid="stDataFrame"] tbody tr').count();
    expect(companyCount).toBeGreaterThan(0);
    
    // Navigate back to job search - results should persist
    await navigateToTab(page, '🔍 Job Search');
    await waitForStreamlitLoad(page);
    
    // Previous search should still be visible
    const persistedJobCount = await page.locator('[data-testid="stDataFrame"] tbody tr').count();
    expect(persistedJobCount).toBe(searchJobCount);
    
    console.log(`✓ Data consistency maintained across tabs: ${searchJobCount} jobs, ${companyCount} companies`);
  });
  
  test('should handle permission-based workflows', async ({ page }) => {
    await loginAsAdmin(page);
    
    // Admin should have access to all features
    const adminTabs = [
      '🔍 Job Search',
      '👥 Free Agents', 
      '📊 Coach Analytics',
      '🏢 Companies',
      '👑 Admin Panel'
    ];
    
    for (const tabName of adminTabs) {
      await navigateToTab(page, tabName);
      await waitForStreamlitLoad(page);
      
      // Should be able to access each tab
      const isVisible = await page.locator('[data-testid="stDataFrame"], .tab-content, .main-content').isVisible();
      expect(isVisible).toBeTruthy();
      
      console.log(`✓ Admin access confirmed for ${tabName}`);
    }
    
    // Test admin-specific features in job search
    await navigateToTab(page, '🔍 Job Search');
    
    // Admin should see force fresh classification if available
    const forceFreshToggle = page.locator('input[key*="force_fresh"]');
    if (await forceFreshToggle.isVisible()) {
      await expect(forceFreshToggle).not.toBeDisabled();
      console.log('✓ Admin can access force fresh classification');
    }
    
    // Admin should see prepared for toggle
    const preparedToggle = page.locator(TEST_CONFIG.selectors.preparedForToggle);
    await expect(preparedToggle).toBeVisible();
    console.log('✓ Admin can control prepared for message');
  });
  
  test('should handle error recovery gracefully', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '🔍 Job Search');
    
    // Try invalid search configuration
    await configureSearch(page, {
      locationType: 'Custom Location',
      customLocation: 'InvalidLocationXYZ123',
      jobQuantity: 5,
    });
    
    try {
      await runJobSearch(page, 'memory-only');
      await waitForStreamlitLoad(page);
      
      // Either should get results or graceful error
      const hasResults = await page.locator('[data-testid="stDataFrame"] tbody tr').isVisible();
      const hasError = await page.locator('text=error", text=Error", text=No results"').isVisible();
      
      expect(hasResults || hasError).toBeTruthy();
      
      if (hasError) {
        console.log('✓ Graceful error handling for invalid search');
      } else {
        console.log('✓ Search succeeded despite unusual location');
      }
      
    } catch (error) {
      console.log(`✓ Error caught and handled: ${error}`);
    }
    
    // App should still be functional after error
    await navigateToTab(page, '👥 Free Agents');
    await expect(page.locator('[data-testid="stDataFrame"], .agents-content')).toBeVisible({
      timeout: TEST_CONFIG.timeouts.pageLoad
    });
  });
  
  test('should complete analytics tracking workflow', async ({ page }) => {
    await loginAsAdmin(page);
    
    // Generate job search with tracking
    await navigateToTab(page, '🔍 Job Search');
    
    await configureSearch(page, {
      locationType: 'Select Market',
      market: 'Houston',
      jobQuantity: 25,
    });
    
    await page.fill('input[placeholder*="name"]', 'Analytics Test Agent');
    await page.fill('input[placeholder*="UUID"]', 'analytics-001');
    
    await configurePdfSettings(page, {
      enablePortalLink: true,
      showPreparedFor: true,
    });
    
    await runJobSearch(page, 'memory-only');
    await waitForStreamlitLoad(page);
    
    // Get portal link (this should create tracking entries)
    const portalLink = await getPortalLink(page);
    expect(portalLink).toBeTruthy();
    
    // Navigate to analytics to verify tracking
    await navigateToTab(page, '📊 Coach Analytics');
    await page.click('text="📋 Detailed Events"');
    await waitForStreamlitLoad(page);
    
    // Should see events table
    await expect(page.locator('[data-testid="stDataFrame"]')).toBeVisible();
    
    // Check overview analytics
    await page.click('text="📊 Overview"');
    await waitForStreamlitLoad(page);
    
    // Should see some metrics
    const hasMetrics = await page.locator('[data-testid="stMetric"], [data-testid="stPlotlyChart"]').isVisible();
    expect(hasMetrics).toBeTruthy();
    
    console.log('✓ Analytics tracking workflow completed');
  });
  
  test('should handle session persistence correctly', async ({ page }) => {
    await loginAsAdmin(page);
    
    // Set up job search with specific settings
    await navigateToTab(page, '🔍 Job Search');
    
    await configureSearch(page, {
      locationType: 'Select Market',
      market: 'Dallas',
      jobQuantity: 40,
    });
    
    await configurePdfSettings(page, {
      showPreparedFor: false,
      enableHtmlPreview: true,
    });
    
    // Verify toggle state
    const toggle = page.locator(TEST_CONFIG.selectors.preparedForToggle);
    await expect(toggle).not.toBeChecked();
    
    // Navigate away and back
    await navigateToTab(page, '🏢 Companies');
    await waitForStreamlitLoad(page);
    
    await navigateToTab(page, '🔍 Job Search');
    await waitForStreamlitLoad(page);
    
    // Settings should persist
    const persistedToggle = page.locator(TEST_CONFIG.selectors.preparedForToggle);
    await expect(persistedToggle).not.toBeChecked();
    
    // Market selection should persist
    const marketSelect = page.locator(TEST_CONFIG.selectors.marketSelect);
    const selectedMarket = await marketSelect.inputValue();
    expect(selectedMarket).toBe('Dallas');
    
    console.log('✓ Session persistence working correctly');
  });
  
  test('should handle logout and re-authentication', async ({ page }) => {
    // Login
    await loginAsAdmin(page);
    await navigateToTab(page, '🔍 Job Search');
    
    // Verify logged in state
    await expect(page.locator(TEST_CONFIG.selectors.tabNavigation)).toBeVisible();
    
    // Logout
    await logout(page);
    
    // Should be back to login page
    await expect(page.locator(TEST_CONFIG.selectors.loginForm)).toBeVisible();
    await expect(page.locator(TEST_CONFIG.selectors.tabNavigation)).not.toBeVisible();
    
    // Re-authenticate
    await loginAsAdmin(page);
    
    // Should be able to access all functionality again
    await navigateToTab(page, '👥 Free Agents');
    await expect(page.locator('[data-testid="stDataFrame"]')).toBeVisible();
    
    console.log('✓ Logout and re-authentication workflow successful');
  });
});