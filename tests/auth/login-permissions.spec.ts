import { test, expect } from '@playwright/test';
import { 
  loginAsAdmin, 
  loginAsRegularCoach, 
  loginAsRestrictedCoach,
  logout,
  verifyAdminAccess,
  verifyCoachAccess,
  verifyTabAccess,
  navigateToTab,
  waitForStreamlitLoad 
} from '../helpers/auth-helpers';
import { TEST_CONFIG } from '../test-config';

/**
 * Authentication and Permission Tests
 * 
 * Validates login/logout functionality and role-based access control
 */

test.describe('Authentication & Permissions', () => {
  
  test('should login successfully with valid admin credentials', async ({ page }) => {
    await loginAsAdmin(page);
    
    // Verify we're logged in by checking for navigation
    await expect(page.locator(TEST_CONFIG.selectors.tabNavigation)).toBeVisible();
    
    // Verify admin access
    await verifyAdminAccess(page);
    
    // Should see all main tabs
    await verifyTabAccess(page, '🔍 Job Search', true);
    await verifyTabAccess(page, '👥 Free Agents', true);
    await verifyTabAccess(page, '📊 Coach Analytics', true);
    await verifyTabAccess(page, '🏢 Companies', true);
    await verifyTabAccess(page, '👑 Admin Panel', true);
  });
  
  test('should login successfully with regular coach credentials', async ({ page }) => {
    await loginAsRegularCoach(page);
    
    await expect(page.locator(TEST_CONFIG.selectors.tabNavigation)).toBeVisible();
    
    // Verify regular coach access (no admin panel)
    await verifyCoachAccess(page);
    
    // Should see main tabs but not admin
    await verifyTabAccess(page, '🔍 Job Search', true);
    await verifyTabAccess(page, '👥 Free Agents', true);
    await verifyTabAccess(page, '📊 Coach Analytics', true);
    await verifyTabAccess(page, '🏢 Companies', true);
    await verifyTabAccess(page, '🔒 Restricted', true);
  });
  
  test('should reject invalid credentials', async ({ page }) => {
    await page.goto('/');
    
    // Wait for login form
    await page.waitForSelector(TEST_CONFIG.selectors.loginForm);
    
    // Try invalid credentials
    await page.fill(TEST_CONFIG.selectors.usernameInput, 'invalid.user');
    await page.fill(TEST_CONFIG.selectors.passwordInput, 'wrongpassword');
    await page.click(TEST_CONFIG.selectors.loginButton);
    
    // Should see error message or remain on login page
    await page.waitForTimeout(3000); // Give time for error to show
    
    // Should still be on login page
    await expect(page.locator(TEST_CONFIG.selectors.loginForm)).toBeVisible();
    
    // Should not see navigation (indicating failed login)
    await expect(page.locator(TEST_CONFIG.selectors.tabNavigation)).not.toBeVisible();
  });
  
  test('should logout successfully', async ({ page }) => {
    // Login first
    await loginAsAdmin(page);
    
    // Verify logged in
    await expect(page.locator(TEST_CONFIG.selectors.tabNavigation)).toBeVisible();
    
    // Logout
    await logout(page);
    
    // Should be back to login page
    await expect(page.locator(TEST_CONFIG.selectors.loginForm)).toBeVisible();
    
    // Should not see navigation
    await expect(page.locator(TEST_CONFIG.selectors.tabNavigation)).not.toBeVisible();
  });
  
  test('should handle session persistence across page refresh', async ({ page }) => {
    await loginAsAdmin(page);
    
    // Verify logged in
    await expect(page.locator(TEST_CONFIG.selectors.tabNavigation)).toBeVisible();
    
    // Refresh page
    await page.reload();
    
    // Should still be logged in
    await expect(page.locator(TEST_CONFIG.selectors.tabNavigation)).toBeVisible({
      timeout: TEST_CONFIG.timeouts.pageLoad
    });
    
    // Should still have admin access
    await verifyAdminAccess(page);
  });
  
  test('should show correct permission-based features', async ({ page }) => {
    // Test with admin (full permissions)
    await loginAsAdmin(page);
    await navigateToTab(page, '🔍 Job Search');
    
    // Admin should see PDF generation options
    await expect(page.locator('text=📄 Free Agent Portal/PDF Configuration"')).toBeVisible();
    
    // Should see force fresh classification if available
    const forceFreshToggle = page.locator('input[key*="force_fresh"]');
    if (await forceFreshToggle.isVisible()) {
      // Admin should be able to use this feature
      await expect(forceFreshToggle).not.toBeDisabled();
    }
    
    // Logout and test with restricted coach
    await logout(page);
    await loginAsRestrictedCoach(page);
    await navigateToTab(page, '🔍 Job Search');
    
    // Restricted coach might not see PDF options
    const pdfSection = page.locator('text=📄 Free Agent Portal/PDF Configuration"');
    const hasPdfAccess = await pdfSection.isVisible();
    
    if (!hasPdfAccess) {
      await expect(page.locator('text=PDF generation not available"')).toBeVisible();
    }
  });
  
  test('should handle password change functionality', async ({ page }) => {
    await loginAsAdmin(page);
    
    // Click hamburger menu
    await page.click('text="☰"');
    
    // Click change password
    await page.click('text="🔑 Change Password"');
    
    // Should see password change form
    await expect(page.locator('input[key="new_password_input"]')).toBeVisible();
    await expect(page.locator('input[key="confirm_password_input"]')).toBeVisible();
    
    // Test validation (passwords don't match)
    await page.fill('input[key="new_password_input"]', 'newpassword123');
    await page.fill('input[key="confirm_password_input"]', 'differentpassword');
    await page.click('button[key="update_password_btn"]');
    
    // Should show error
    await expect(page.locator('text=don\'t match"')).toBeVisible();
    
    // Cancel password change
    await page.click('button[key="cancel_password_btn"]');
    
    // Form should be hidden
    await expect(page.locator('input[key="new_password_input"]')).not.toBeVisible();
  });
  
  test('should restrict access to batches tab based on permissions', async ({ page }) => {
    await loginAsRegularCoach(page);
    
    // Check if batches tab is visible (depends on permission)
    const batchesTab = page.locator(TEST_CONFIG.selectors.batchesTab);
    const hasBatchesAccess = await batchesTab.isVisible();
    
    if (hasBatchesAccess) {
      // If visible, should be able to click it
      await batchesTab.click();
      await waitForStreamlitLoad(page);
      
      // Should not see access denied message
      await expect(page.locator('text=Access to Batches & Scheduling is not enabled"')).not.toBeVisible();
    } else {
      // If not visible, that's also correct (permission-based hiding)
      console.log('ℹ Batches tab hidden due to permissions (expected behavior)');
    }
    
    // Test with admin
    await logout(page);
    await loginAsAdmin(page);
    
    // Admin should definitely have access to batches if the tab exists
    const adminBatchesTab = page.locator(TEST_CONFIG.selectors.batchesTab);
    if (await adminBatchesTab.isVisible()) {
      await adminBatchesTab.click();
      await waitForStreamlitLoad(page);
      
      // Should not see access denied
      await expect(page.locator('text=Access to Batches & Scheduling is not enabled"')).not.toBeVisible();
    }
  });
  
  test('should navigate between all accessible tabs', async ({ page }) => {
    await loginAsAdmin(page);
    
    const tabs = [
      '🔍 Job Search',
      '👥 Free Agents', 
      '📊 Coach Analytics',
      '🏢 Companies',
      '👑 Admin Panel'
    ];
    
    // Check if batches tab is available
    const batchesTab = page.locator(TEST_CONFIG.selectors.batchesTab);
    if (await batchesTab.isVisible()) {
      tabs.splice(1, 0, '🗓️ Batches & Scheduling'); // Insert after Job Search
    }
    
    // Navigate through each tab
    for (const tabName of tabs) {
      await navigateToTab(page, tabName);
      
      // Verify we're on the correct tab by checking for tab-specific content
      switch (tabName) {
        case '🔍 Job Search':
          await expect(page.locator('text=Search Parameters"')).toBeVisible();
          break;
        case '👥 Free Agents':
          await expect(page.locator('text=Free Agent Management" , text=Your Free Agents"')).toBeVisible();
          break;
        case '📊 Coach Analytics':
          await expect(page.locator('text=Coach Performance Analytics" , text=Analytics Dashboard"')).toBeVisible();
          break;
        case '🏢 Companies':
          await expect(page.locator('text=Companies" , text=company" ')).toBeVisible();
          break;
        case '👑 Admin Panel':
          await expect(page.locator('text=Admin" , text=administration"')).toBeVisible();
          break;
      }
      
      console.log(`✓ Successfully navigated to ${tabName}`);
    }
  });
});