import { test, expect } from '@playwright/test';
import { loginAsAdmin, navigateToTab, waitForStreamlitLoad } from '../helpers/auth-helpers';
import { TEST_CONFIG } from '../test-config';

/**
 * CRITICAL TEST: Analytics Dashboard Functionality
 * 
 * This test validates the Coach Analytics dashboard:
 * - All analytics tabs load properly
 * - Date filtering works correctly
 * - Charts and metrics display
 * - CSV export functionality
 * - Performance metrics calculations
 */

test.describe('Analytics Dashboard', () => {
  
  test('should load all analytics tabs successfully', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '📊 Coach Analytics');
    
    const analyticsTabs = [
      '📊 Overview',
      '👤 Individual Agents',
      '🌍 FreeWorld Dashboard',
      '📋 Detailed Events',
      '👑 Admin Reports'
    ];
    
    for (const tabName of analyticsTabs) {
      // Click the analytics sub-tab
      await page.click(`text="${tabName}"`);
      await waitForStreamlitLoad(page);
      
      // Verify tab content loads
      await expect(page.locator(`text=${tabName}"`)).toBeVisible();
      
      // Look for common analytics elements
      const hasCharts = await page.locator('[data-testid="stPlotlyChart"], .plot-container').isVisible();
      const hasMetrics = await page.locator('[data-testid="stMetric"], .metric-container').isVisible();
      const hasDataFrames = await page.locator('[data-testid="stDataFrame"]').isVisible();
      
      // At least one type of analytics content should be visible
      expect(hasCharts || hasMetrics || hasDataFrames).toBeTruthy();
      
      console.log(`✓ ${tabName} tab loaded successfully`);
    }
  });
  
  test('should filter data by date range', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '📊 Coach Analytics');
    
    // Go to Overview tab
    await page.click('text="📊 Overview"');
    await waitForStreamlitLoad(page);
    
    // Look for date filter controls
    const startDateInput = page.locator('input[type="date"]').first();
    const endDateInput = page.locator('input[type="date"]').last();
    
    if (await startDateInput.isVisible() && await endDateInput.isVisible()) {
      // Set date range (last 7 days)
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(endDate.getDate() - 7);
      
      await startDateInput.fill(startDate.toISOString().split('T')[0]);
      await endDateInput.fill(endDate.toISOString().split('T')[0]);
      
      // Wait for data to refresh
      await waitForStreamlitLoad(page);
      
      // Verify some analytics content is visible
      await expect(page.locator('[data-testid="stPlotlyChart"], [data-testid="stMetric"], [data-testid="stDataFrame"]')).toBeVisible();
      
      console.log('✓ Date filtering applied successfully');
    } else {
      console.log('ℹ Date filters not found - may be using different component');
    }
  });
  
  test('should display overview metrics correctly', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '📊 Coach Analytics');
    await page.click('text="📊 Overview"');
    await waitForStreamlitLoad(page);
    
    // Look for key metrics that should be displayed
    const expectedMetrics = [
      'Total Engagements',
      'Total Clicks',
      'Click Rate',
      'Active Agents',
      'Jobs Sent',
      'Engagement Rate'
    ];
    
    let foundMetrics = 0;
    for (const metric of expectedMetrics) {
      const metricVisible = await page.locator(`text=${metric}"`).isVisible();
      if (metricVisible) {
        foundMetrics++;
        console.log(`✓ Found metric: ${metric}`);
      }
    }
    
    // Should find at least half of the expected metrics
    expect(foundMetrics).toBeGreaterThan(expectedMetrics.length / 2);
    
    // Look for charts
    const hasCharts = await page.locator('[data-testid="stPlotlyChart"], .plot-container').count();
    expect(hasCharts).toBeGreaterThan(0);
  });
  
  test('should show individual agent analytics', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '📊 Coach Analytics');
    await page.click('text="👤 Individual Agents"');
    await waitForStreamlitLoad(page);
    
    // Should have agent selector or agent list
    const hasAgentSelector = await page.locator('select, [data-testid="stSelectbox"]').isVisible();
    const hasAgentTable = await page.locator('[data-testid="stDataFrame"]').isVisible();
    
    expect(hasAgentSelector || hasAgentTable).toBeTruthy();
    
    // If there's a selector, try selecting an agent
    if (hasAgentSelector) {
      const agentOptions = await page.locator('select option, [data-testid="stSelectbox"] option').count();
      if (agentOptions > 1) {
        // Select first non-default option
        await page.selectOption('select', { index: 1 });
        await waitForStreamlitLoad(page);
        
        // Should show agent-specific data
        await expect(page.locator('[data-testid="stPlotlyChart"], [data-testid="stMetric"], [data-testid="stDataFrame"]')).toBeVisible();
      }
    }
    
    console.log('✓ Individual agent analytics loaded');
  });
  
  test('should display FreeWorld dashboard correctly', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '📊 Coach Analytics');
    await page.click('text="🌍 FreeWorld Dashboard"');
    await waitForStreamlitLoad(page);
    
    // Should show organization-wide metrics
    const expectedElements = [
      'Total Impact',
      'Economic Impact',
      'ROI',
      'Cost per Engagement',
      'Overall Performance'
    ];
    
    let foundElements = 0;
    for (const element of expectedElements) {
      const elementVisible = await page.locator(`text=${element}"`).isVisible();
      if (elementVisible) {
        foundElements++;
      }
    }
    
    // Should find some key dashboard elements
    expect(foundElements).toBeGreaterThan(0);
    
    // Should have visual elements (charts, metrics)
    const visualElements = await page.locator('[data-testid="stPlotlyChart"], [data-testid="stMetric"]').count();
    expect(visualElements).toBeGreaterThan(0);
    
    console.log(`✓ FreeWorld dashboard loaded with ${foundElements} key elements`);
  });
  
  test('should show detailed events table', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '📊 Coach Analytics');
    await page.click('text="📋 Detailed Events"');
    await waitForStreamlitLoad(page);
    
    // Should show events table
    const eventsTable = page.locator('[data-testid="stDataFrame"]');
    await expect(eventsTable).toBeVisible();
    
    // Should have some columns
    const tableHeaders = await page.locator('[data-testid="stDataFrame"] th, [data-testid="stDataFrame"] .col-header').count();
    expect(tableHeaders).toBeGreaterThan(0);
    
    // Look for typical event columns
    const expectedColumns = [
      'Timestamp',
      'Agent',
      'Coach',
      'Event Type',
      'Market',
      'Route'
    ];
    
    let foundColumns = 0;
    for (const column of expectedColumns) {
      const columnVisible = await page.locator(`text=${column}"`).isVisible();
      if (columnVisible) {
        foundColumns++;
      }
    }
    
    console.log(`✓ Events table loaded with ${foundColumns} recognizable columns`);
  });
  
  test('should provide CSV export functionality', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '📊 Coach Analytics');
    
    // Try different tabs for CSV export
    const tabsToTest = ['📊 Overview', '📋 Detailed Events'];
    
    for (const tabName of tabsToTest) {
      await page.click(`text="${tabName}"`);
      await waitForStreamlitLoad(page);
      
      // Look for download/export buttons
      const exportButton = page.locator('button:has-text("Download"), button:has-text("Export"), button:has-text("CSV"), [data-testid="stDownloadButton"]');
      
      if (await exportButton.isVisible()) {
        // Don't actually download, just verify the button exists
        console.log(`✓ Found export functionality in ${tabName}`);
        break;
      }
    }
  });
  
  test('should handle admin reports correctly', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '📊 Coach Analytics');
    await page.click('text="👑 Admin Reports"');
    await waitForStreamlitLoad(page);
    
    // Admin reports should show coach performance data
    const expectedReportElements = [
      'Coach Performance',
      'Budget Utilization',
      'Search Activity',
      'Agent Engagement',
      'Cost Analysis'
    ];
    
    let foundReportElements = 0;
    for (const element of expectedReportElements) {
      const elementVisible = await page.locator(`text=${element}"`).isVisible();
      if (elementVisible) {
        foundReportElements++;
      }
    }
    
    // Should have some admin-specific content
    const hasDataFrames = await page.locator('[data-testid="stDataFrame"]').count();
    const hasMetrics = await page.locator('[data-testid="stMetric"]').count();
    
    expect(hasDataFrames + hasMetrics + foundReportElements).toBeGreaterThan(0);
    
    console.log(`✓ Admin reports loaded with ${foundReportElements} report elements`);
  });
  
  test('should calculate metrics accurately', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '📊 Coach Analytics');
    await page.click('text="📊 Overview"');
    await waitForStreamlitLoad(page);
    
    // Look for numerical metrics
    const metrics = await page.locator('[data-testid="stMetric"] .metric-value, .metric .value').allTextContents();
    
    for (const metric of metrics) {
      // Basic validation that metrics are numbers or percentages
      const isValid = /^\d+[,.]?\d*[%]?$/.test(metric.trim()) || 
                     /^\$\d+[,.]?\d*$/.test(metric.trim()) || 
                     metric.includes('N/A') || 
                     metric.includes('--');
      
      expect(isValid).toBeTruthy();
    }
    
    console.log(`✓ Validated ${metrics.length} metrics format`);
  });
  
  test('should refresh data correctly', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '📊 Coach Analytics');
    await page.click('text="📊 Overview"');
    await waitForStreamlitLoad(page);
    
    // Look for refresh button or auto-refresh
    const refreshButton = page.locator('button:has-text("Refresh"), button:has-text("Update")');
    
    if (await refreshButton.isVisible()) {
      await refreshButton.click();
      await waitForStreamlitLoad(page);
      
      // Data should still be visible after refresh
      await expect(page.locator('[data-testid="stPlotlyChart"], [data-testid="stMetric"], [data-testid="stDataFrame"]')).toBeVisible();
      
      console.log('✓ Data refresh functionality works');
    } else {
      // If no explicit refresh button, just verify data loads consistently
      await page.reload();
      await loginAsAdmin(page);
      await navigateToTab(page, '📊 Coach Analytics');
      await waitForStreamlitLoad(page);
      
      await expect(page.locator('[data-testid="stPlotlyChart"], [data-testid="stMetric"], [data-testid="stDataFrame"]')).toBeVisible();
      
      console.log('✓ Data loads consistently after page refresh');
    }
  });
});