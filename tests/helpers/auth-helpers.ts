import { Page, expect } from '@playwright/test';
import { TEST_CONFIG, TestCoach } from '../test-config';

/**
 * Authentication helper functions for FreeWorld Coach Portal tests
 */

/**
 * Login to the coach portal with given credentials
 */
export async function loginAsCoach(page: Page, coach: TestCoach) {
  await page.goto('/');
  
  // Wait for login form to appear
  await page.waitForSelector(TEST_CONFIG.selectors.loginForm, { 
    timeout: TEST_CONFIG.timeouts.pageLoad 
  });
  
  // Fill in credentials
  await page.fill(TEST_CONFIG.selectors.usernameInput, coach.username);
  await page.fill(TEST_CONFIG.selectors.passwordInput, coach.password);
  
  // Click login button
  await page.click(TEST_CONFIG.selectors.loginButton);
  
  // Wait for successful login (should see navigation tabs)
  await page.waitForSelector(TEST_CONFIG.selectors.tabNavigation, {
    timeout: TEST_CONFIG.timeouts.pageLoad
  });
  
  // Verify we're logged in by checking that navigation tabs are visible (indicates successful login)
  await expect(page.locator(TEST_CONFIG.selectors.tabNavigation)).toBeVisible();
}

/**
 * Login as admin user
 */
export async function loginAsAdmin(page: Page) {
  await loginAsCoach(page, TEST_CONFIG.coaches.admin);
}

/**
 * Login as regular coach
 */
export async function loginAsRegularCoach(page: Page) {
  await loginAsCoach(page, TEST_CONFIG.coaches.regularCoach);
}

/**
 * Login as restricted coach (no permissions)
 */
export async function loginAsRestrictedCoach(page: Page) {
  await loginAsCoach(page, TEST_CONFIG.coaches.restrictedCoach);
}

/**
 * Logout from the coach portal
 */
export async function logout(page: Page) {
  // Click hamburger menu
  await page.click('text="☰"');
  
  // Click sign out
  await page.click('text="🚪 Sign Out"');
  
  // Wait for login form to appear again
  await page.waitForSelector(TEST_CONFIG.selectors.loginForm);
}

/**
 * Verify user has access to specific tab
 */
export async function verifyTabAccess(page: Page, tabName: string, shouldHaveAccess: boolean = true) {
  const tabSelector = `text="${tabName}"`;
  
  if (shouldHaveAccess) {
    await expect(page.locator(tabSelector)).toBeVisible();
  } else {
    await expect(page.locator(tabSelector)).not.toBeVisible();
  }
}

/**
 * Navigate to specific tab
 */
export async function navigateToTab(page: Page, tabName: string) {
  await page.click(`text="${tabName}"`);
  
  // Wait for tab content to load
  await page.waitForTimeout(2000); // Give Streamlit time to render
}

/**
 * Verify admin permissions are working
 */
export async function verifyAdminAccess(page: Page) {
  // Should see Admin Panel tab
  await verifyTabAccess(page, '👑 Admin Panel', true);
  
  // Should not see Restricted tab
  await verifyTabAccess(page, '🔒 Restricted', false);
}

/**
 * Verify regular coach permissions
 */
export async function verifyCoachAccess(page: Page) {
  // Should not see Admin Panel tab
  await verifyTabAccess(page, '👑 Admin Panel', false);
  
  // Should see Restricted tab instead
  await verifyTabAccess(page, '🔒 Restricted', true);
}

/**
 * Handle Streamlit's dynamic loading
 */
export async function waitForStreamlitLoad(page: Page) {
  // Wait for Streamlit's main container to be ready
  await page.waitForSelector('[data-testid="stApp"]');
  
  // Wait for any loading spinners to disappear
  await page.waitForFunction(() => {
    const spinners = document.querySelectorAll('[data-testid="stSpinner"]');
    return spinners.length === 0;
  });
  
  // Small additional wait for dynamic content
  await page.waitForTimeout(1000);
}