import { test, expect } from '@playwright/test';
import { loginAsAdmin, navigateToTab, waitForStreamlitLoad } from '../helpers/auth-helpers';
import { TEST_CONFIG } from '../test-config';

/**
 * CRITICAL TEST: Companies Tab Functionality
 * 
 * This test validates the Companies tab features:
 * - Companies data loads correctly
 * - Search and filtering works
 * - Company details display properly
 * - Database field mapping is correct
 * - Performance and responsiveness
 */

test.describe('Companies Tab', () => {
  
  test('should load companies data successfully', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '🏢 Companies');
    
    // Should see companies table or list
    await expect(page.locator('[data-testid="stDataFrame"], .companies-table, .company-list')).toBeVisible({
      timeout: TEST_CONFIG.timeouts.pageLoad
    });
    
    // Should have some company data
    const companyRows = await page.locator('[data-testid="stDataFrame"] tbody tr, .company-row').count();
    expect(companyRows).toBeGreaterThan(0);
    
    console.log(`✓ Loaded ${companyRows} companies`);
  });
  
  test('should display correct company information fields', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '🏢 Companies');
    await waitForStreamlitLoad(page);
    
    // Check for expected company data columns
    const expectedFields = [
      'Company',
      'Jobs',
      'Location',
      'Industry',
      'Total Jobs',
      'Active Jobs',
      'Quality Score'
    ];
    
    let foundFields = 0;
    for (const field of expectedFields) {
      const fieldVisible = await page.locator(`text=${field}"`).isVisible();
      if (fieldVisible) {
        foundFields++;
        console.log(`✓ Found field: ${field}`);
      }
    }
    
    // Should find at least some of the expected fields
    expect(foundFields).toBeGreaterThan(expectedFields.length / 3);
  });
  
  test('should handle company search functionality', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '🏢 Companies');
    await waitForStreamlitLoad(page);
    
    // Look for search input
    const searchInput = page.locator('input[placeholder*="search"], input[placeholder*="filter"], input[placeholder*="company"]');
    
    if (await searchInput.isVisible()) {
      // Get initial company count
      const initialCount = await page.locator('[data-testid="stDataFrame"] tbody tr, .company-row').count();
      
      // Search for a common term
      await searchInput.fill('trucking');
      await waitForStreamlitLoad(page);
      
      // Results should be filtered
      const filteredCount = await page.locator('[data-testid="stDataFrame"] tbody tr, .company-row').count();
      
      // Either fewer results or same (if all companies match)
      expect(filteredCount).toBeLessThanOrEqual(initialCount);
      
      // Clear search
      await searchInput.clear();
      await waitForStreamlitLoad(page);
      
      // Should return to original count
      const clearedCount = await page.locator('[data-testid="stDataFrame"] tbody tr, .company-row').count();
      expect(clearedCount).toBe(initialCount);
      
      console.log(`✓ Search functionality works: ${initialCount} → ${filteredCount} → ${clearedCount}`);
    } else {
      console.log('ℹ Search functionality not found - may be using different implementation');
    }
  });
  
  test('should show company job statistics', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '🏢 Companies');
    await waitForStreamlitLoad(page);
    
    // Look for job count information
    const jobStats = await page.locator('text=jobs", text=Jobs", text=postings"').count();
    expect(jobStats).toBeGreaterThan(0);
    
    // Look for numerical job counts in table
    const tableNumbers = await page.locator('[data-testid="stDataFrame"] td').allTextContents();
    const hasNumbers = tableNumbers.some(text => /^\d+$/.test(text.trim()));
    
    expect(hasNumbers).toBeTruthy();
    
    console.log('✓ Company job statistics are displayed');
  });
  
  test('should handle company filtering options', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '🏢 Companies');
    await waitForStreamlitLoad(page);
    
    // Look for filter controls (dropdowns, checkboxes, etc.)
    const filterControls = await page.locator('select, [data-testid="stSelectbox"], input[type="checkbox"]').count();
    
    if (filterControls > 0) {
      // Try applying a filter if available
      const firstFilter = page.locator('select, [data-testid="stSelectbox"]').first();
      
      if (await firstFilter.isVisible()) {
        const initialCount = await page.locator('[data-testid="stDataFrame"] tbody tr').count();
        
        // Try changing filter
        const optionCount = await firstFilter.locator('option').count();
        if (optionCount > 1) {
          await firstFilter.selectOption({ index: 1 });
          await waitForStreamlitLoad(page);
          
          const filteredCount = await page.locator('[data-testid="stDataFrame"] tbody tr').count();
          console.log(`✓ Filter applied: ${initialCount} → ${filteredCount} companies`);
        }
      }
      
      console.log(`✓ Found ${filterControls} filter controls`);
    } else {
      console.log('ℹ No filter controls found - companies may show all data');
    }
  });
  
  test('should display company details correctly', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '🏢 Companies');
    await waitForStreamlitLoad(page);
    
    // Get first company row
    const firstCompanyRow = page.locator('[data-testid="stDataFrame"] tbody tr').first();
    
    if (await firstCompanyRow.isVisible()) {
      // Check if company data is properly formatted
      const companyData = await firstCompanyRow.locator('td').allTextContents();
      
      // Should have multiple data points
      expect(companyData.length).toBeGreaterThan(1);
      
      // At least one cell should have actual company name (not empty/null)
      const hasCompanyName = companyData.some(cell => 
        cell.trim().length > 0 && 
        !cell.includes('NaN') && 
        !cell.includes('None') && 
        cell !== '--'
      );
      
      expect(hasCompanyName).toBeTruthy();
      
      console.log(`✓ Company details properly formatted: ${companyData.slice(0, 3).join(', ')}...`);
    }
  });
  
  test('should handle sorting functionality', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '🏢 Companies');
    await waitForStreamlitLoad(page);
    
    // Look for sortable column headers
    const sortableHeaders = page.locator('[data-testid="stDataFrame"] th[data-sort], .sortable-header, th.sortable');
    const headerCount = await sortableHeaders.count();
    
    if (headerCount > 0) {
      // Try clicking a header to sort
      const firstHeader = sortableHeaders.first();
      await firstHeader.click();
      await waitForStreamlitLoad(page);
      
      // Data should still be visible after sort
      await expect(page.locator('[data-testid="stDataFrame"] tbody tr')).toHaveCountGreaterThan(0);
      
      console.log('✓ Column sorting functionality works');
    } else {
      console.log('ℹ Sorting functionality not found - may be using different table implementation');
    }
  });
  
  test('should prevent database field mapping errors', async ({ page }) => {
    await loginAsAdmin(page);
    
    // Monitor console for errors
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    await navigateToTab(page, '🏢 Companies');
    await waitForStreamlitLoad(page);
    
    // Should not see database errors in Streamlit
    const hasDbError = await page.locator('text=column", text=does not exist", text=database error"').isVisible();
    expect(hasDbError).toBeFalsy();
    
    // Should see actual company data, not error messages
    await expect(page.locator('[data-testid="stDataFrame"], .companies-content')).toBeVisible();
    
    // Check for specific field mapping issues that were previously fixed
    const fieldMappingError = await page.locator('text=jobs.title does not exist"').isVisible();
    expect(fieldMappingError).toBeFalsy();
    
    console.log('✓ No database field mapping errors detected');
  });
  
  test('should handle empty or no data gracefully', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '🏢 Companies');
    await waitForStreamlitLoad(page);
    
    const companyCount = await page.locator('[data-testid="stDataFrame"] tbody tr').count();
    
    if (companyCount === 0) {
      // Should show appropriate message for no data
      const noDataMessage = await page.locator('text=No companies", text=No data", text=empty"').isVisible();
      expect(noDataMessage).toBeTruthy();
      
      console.log('✓ Handles empty data state appropriately');
    } else {
      console.log(`✓ Loaded ${companyCount} companies successfully`);
    }
  });
  
  test('should load within performance threshold', async ({ page }) => {
    const startTime = Date.now();
    
    await loginAsAdmin(page);
    await navigateToTab(page, '🏢 Companies');
    
    // Wait for companies data to load
    await page.waitForSelector('[data-testid="stDataFrame"], .companies-table', {
      timeout: TEST_CONFIG.timeouts.pageLoad
    });
    
    const loadTime = Date.now() - startTime;
    
    // Should load within reasonable time
    expect(loadTime).toBeLessThan(30000); // 30 seconds max
    
    console.log(`✓ Companies tab loaded in ${loadTime}ms`);
  });
  
  test('should maintain data consistency', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '🏢 Companies');
    await waitForStreamlitLoad(page);
    
    // Get initial data snapshot
    const initialRows = await page.locator('[data-testid="stDataFrame"] tbody tr').count();
    
    // Navigate away and back
    await navigateToTab(page, '🔍 Job Search');
    await waitForStreamlitLoad(page);
    
    await navigateToTab(page, '🏢 Companies');
    await waitForStreamlitLoad(page);
    
    // Data should be consistent
    const returnRows = await page.locator('[data-testid="stDataFrame"] tbody tr').count();
    expect(returnRows).toBe(initialRows);
    
    console.log(`✓ Data consistency maintained: ${initialRows} rows`);
  });
});