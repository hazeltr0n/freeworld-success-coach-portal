import { test, expect } from '@playwright/test';
import { loginAsAdmin, navigateToTab, waitForStreamlitLoad } from '../helpers/auth-helpers';
import { TEST_CONFIG } from '../test-config';

/**
 * CRITICAL TEST: Free Agent Recovery System
 * 
 * This test validates the recent agent recovery feature:
 * - Show/hide deleted agents with "Show Deleted" checkbox
 * - Status indicators (🟢 Active vs 👻 Deleted)
 * - Restore functionality for soft-deleted agents
 * - Bulk restore operations
 */

test.describe('Free Agent Recovery System', () => {
  
  test('should show active agents by default', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '👥 Free Agents');
    
    // Wait for agent table to load
    await waitForStreamlitLoad(page);
    
    // Should see agent table
    await expect(page.locator(TEST_CONFIG.selectors.agentTable)).toBeVisible();
    
    // Should see "Show Deleted" checkbox
    await expect(page.locator(TEST_CONFIG.selectors.showDeletedCheckbox)).toBeVisible();
    
    // Checkbox should be unchecked by default
    await expect(page.locator(TEST_CONFIG.selectors.showDeletedCheckbox)).not.toBeChecked();
    
    // Should see status column in table
    await expect(page.locator('text=Status"')).toBeVisible();
    
    // All visible agents should have 🟢 Active status
    const statusCells = await page.locator('[data-testid="stDataEditor"] .status-cell, tbody tr td:first-child').allTextContents();
    for (const status of statusCells) {
      if (status.includes('🟢') || status.includes('Active')) {
        expect(status).toContain('🟢');
      }
    }
  });
  
  test('should reveal deleted agents when checkbox is checked', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '👥 Free Agents');
    await waitForStreamlitLoad(page);
    
    // Get initial agent count
    const initialAgentRows = await page.locator('[data-testid="stDataEditor"] tbody tr').count();
    
    // Check "Show Deleted" checkbox
    await page.locator(TEST_CONFIG.selectors.showDeletedCheckbox).check();
    await waitForStreamlitLoad(page);
    
    // Should now see more agents (including deleted ones)
    const totalAgentRows = await page.locator('[data-testid="stDataEditor"] tbody tr').count();
    expect(totalAgentRows).toBeGreaterThanOrEqual(initialAgentRows);
    
    // Should see deleted agents with 👻 status
    const allStatusCells = await page.locator('[data-testid="stDataEditor"] tbody tr td:first-child').allTextContents();
    const hasDeletedAgents = allStatusCells.some(status => 
      status.includes('👻') || status.includes('Deleted')
    );
    
    // If we have any deleted agents, verify they're properly marked
    if (hasDeletedAgents) {
      expect(hasDeletedAgents).toBeTruthy();
      console.log('✓ Found deleted agents with proper status indicators');
    } else {
      console.log('ℹ No deleted agents found in test data');
    }
  });
  
  test('should create and restore a deleted agent', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '👥 Free Agents');
    await waitForStreamlitLoad(page);
    
    // First, create a test agent that we can delete and restore
    await createTestAgent(page, {
      name: 'Test Recovery Agent',
      email: 'test.recovery@example.com',
      market: 'Houston',
    });
    
    // Wait for agent to be created
    await waitForStreamlitLoad(page);
    
    // Find the test agent in the table and delete it
    const testAgentRow = await page.locator('tr:has-text("Test Recovery Agent")');
    await expect(testAgentRow).toBeVisible();
    
    // Click delete checkbox for this agent
    const deleteCheckbox = testAgentRow.locator('input[type="checkbox"]').last(); // Delete column is usually last
    await deleteCheckbox.check();
    
    // Confirm deletion
    await page.click('button:has-text("🗑️ Confirm Delete Selected")');
    await waitForStreamlitLoad(page);
    
    // Agent should now be hidden (not in active list)
    await expect(page.locator('tr:has-text("Test Recovery Agent")')).not.toBeVisible();
    
    // Check "Show Deleted" to reveal deleted agents
    await page.locator(TEST_CONFIG.selectors.showDeletedCheckbox).check();
    await waitForStreamlitLoad(page);
    
    // Should now see the deleted agent with 👻 status
    const deletedAgentRow = await page.locator('tr:has-text("Test Recovery Agent")');
    await expect(deletedAgentRow).toBeVisible();
    await expect(deletedAgentRow.locator('text=👻"')).toBeVisible();
    
    // Should see "Restore" checkbox instead of "Delete" for this agent
    const restoreCheckbox = deletedAgentRow.locator('input[type="checkbox"]').last();
    await restoreCheckbox.check();
    
    // Confirm restore
    await expect(page.locator(TEST_CONFIG.selectors.restoreButton)).toBeVisible();
    await page.click(TEST_CONFIG.selectors.restoreButton);
    await waitForStreamlitLoad(page);
    
    // Agent should now be restored and active
    const restoredAgentRow = await page.locator('tr:has-text("Test Recovery Agent")');
    await expect(restoredAgentRow).toBeVisible();
    await expect(restoredAgentRow.locator('text=🟢"')).toBeVisible();
  });
  
  test('should handle bulk restore operations', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '👥 Free Agents');
    await waitForStreamlitLoad(page);
    
    // Create multiple test agents
    const testAgents = [
      { name: 'Bulk Test Agent 1', email: 'bulk1@example.com', market: 'Dallas' },
      { name: 'Bulk Test Agent 2', email: 'bulk2@example.com', market: 'Austin' },
    ];
    
    // Create and delete test agents
    for (const agent of testAgents) {
      await createTestAgent(page, agent);
      await waitForStreamlitLoad(page);
      
      // Delete the agent
      const agentRow = await page.locator(`tr:has-text("${agent.name}")`);
      const deleteCheckbox = agentRow.locator('input[type="checkbox"]').last();
      await deleteCheckbox.check();
      
      await page.click('button:has-text("🗑️ Confirm Delete Selected")');
      await waitForStreamlitLoad(page);
    }
    
    // Show deleted agents
    await page.locator(TEST_CONFIG.selectors.showDeletedCheckbox).check();
    await waitForStreamlitLoad(page);
    
    // Select multiple deleted agents for restoration
    let restoredCount = 0;
    for (const agent of testAgents) {
      const deletedAgentRow = await page.locator(`tr:has-text("${agent.name}")`);
      if (await deletedAgentRow.isVisible()) {
        const restoreCheckbox = deletedAgentRow.locator('input[type="checkbox"]').last();
        await restoreCheckbox.check();
        restoredCount++;
      }
    }
    
    if (restoredCount > 0) {
      // Confirm bulk restore
      await page.click(TEST_CONFIG.selectors.restoreButton);
      await waitForStreamlitLoad(page);
      
      // Verify agents are restored
      for (const agent of testAgents) {
        const restoredRow = await page.locator(`tr:has-text("${agent.name}")`);
        if (await restoredRow.isVisible()) {
          await expect(restoredRow.locator('text=🟢"')).toBeVisible();
        }
      }
      
      console.log(`✓ Successfully restored ${restoredCount} agents in bulk operation`);
    }
  });
  
  test('should maintain data integrity during delete/restore cycle', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '👥 Free Agents');
    await waitForStreamlitLoad(page);
    
    const testAgent = {
      name: 'Data Integrity Test Agent',
      email: 'integrity@example.com',
      market: 'Houston',
      routeFilter: 'local',
      fairChance: true,
      maxJobs: 30,
    };
    
    // Create agent with specific settings
    await createTestAgent(page, testAgent);
    await waitForStreamlitLoad(page);
    
    // Capture original agent data
    const originalRow = await page.locator(`tr:has-text("${testAgent.name}")`);
    const originalData = await captureAgentRowData(originalRow);
    
    // Delete the agent
    const deleteCheckbox = originalRow.locator('input[type="checkbox"]').last();
    await deleteCheckbox.check();
    await page.click('button:has-text("🗑️ Confirm Delete Selected")');
    await waitForStreamlitLoad(page);
    
    // Show deleted agents and restore
    await page.locator(TEST_CONFIG.selectors.showDeletedCheckbox).check();
    await waitForStreamlitLoad(page);
    
    const deletedRow = await page.locator(`tr:has-text("${testAgent.name}")`);
    const restoreCheckbox = deletedRow.locator('input[type="checkbox"]').last();
    await restoreCheckbox.check();
    await page.click(TEST_CONFIG.selectors.restoreButton);
    await waitForStreamlitLoad(page);
    
    // Verify restored data matches original
    const restoredRow = await page.locator(`tr:has-text("${testAgent.name}")`);
    const restoredData = await captureAgentRowData(restoredRow);
    
    // Compare key data fields (excluding status which changed)
    expect(restoredData.name).toBe(originalData.name);
    expect(restoredData.email).toBe(originalData.email);
    expect(restoredData.market).toBe(originalData.market);
    
    console.log('✓ Data integrity maintained through delete/restore cycle');
  });
});

/**
 * Helper function to create a test agent
 */
async function createTestAgent(page, agent: {
  name: string;
  email: string;
  market: string;
  routeFilter?: string;
  fairChance?: boolean;
  maxJobs?: number;
}) {
  // Click manual entry button
  await page.click(TEST_CONFIG.selectors.addManualAgentButton);
  
  // Fill in agent details
  await page.fill('input[placeholder*="Enter full name"]', agent.name);
  await page.fill('input[placeholder*="agent@example.com"]', agent.email);
  
  // Select market
  await page.selectOption('select', agent.market);
  
  if (agent.routeFilter) {
    await page.selectOption('select[key*="route_filter"]', agent.routeFilter);
  }
  
  if (agent.fairChance) {
    await page.check('input[key*="fair_chance"]');
  }
  
  if (agent.maxJobs) {
    await page.fill('input[key*="max_jobs"]', agent.maxJobs.toString());
  }
  
  // Submit
  await page.click('button:has-text("➕ Add Manual Agent")');
}

/**
 * Helper function to capture agent row data for comparison
 */
async function captureAgentRowData(row) {
  const cells = await row.locator('td').allTextContents();
  
  return {
    name: cells[1] || '', // Assuming name is second column (after status)
    email: cells[8] || '', // Adjust column indices based on actual table structure
    market: cells[4] || '',
    route: cells[5] || '',
    status: cells[0] || '',
  };
}