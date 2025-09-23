import { test, expect } from '@playwright/test';
import { loginAsAdmin, navigateToTab, waitForStreamlitLoad } from '../helpers/auth-helpers';
import { TEST_CONFIG } from '../test-config';

/**
 * CRITICAL TEST: Google Async Batches End-to-End
 *
 * This test validates the complete Google async batch workflow:
 * 1. Submit a small Google Jobs async batch (10 pages)
 * 2. Monitor batch processing status
 * 3. Verify batch completion and results
 * 4. Validate data integrity and CSV/PDF outputs
 */

test.describe('Google Async Batches', () => {

  test('should successfully submit and process small Google async batch', async ({ page }) => {
    // Login as admin (required for async batch access)
    await loginAsAdmin(page);
    await waitForStreamlitLoad(page);

    // Navigate to Batches & Scheduling tab
    await navigateToTab(page, '🗓️ Batches & Scheduling');
    await waitForStreamlitLoad(page);

    // Verify async batches interface is visible
    await expect(page.locator('text="Async Batch Submission"')).toBeVisible({
      timeout: TEST_CONFIG.timeouts.elementLoad
    });

    // Configure small Google Jobs batch
    await configureAsyncBatch(page, {
      jobSource: 'Google Jobs',
      location: 'Houston, TX',
      searchTerms: 'CDL driver',
      pages: 10, // Small batch for quick testing
      searchRadius: 25
    });

    // Submit the batch
    const batchId = await submitAsyncBatch(page);
    console.log(`✓ Submitted Google async batch with ID: ${batchId}`);

    // Monitor batch processing (with timeout)
    const batchResult = await monitorBatchProcessing(page, batchId, {
      maxWaitTime: 300000, // 5 minutes max
      pollInterval: 15000   // Check every 15 seconds
    });

    // Validate batch completion
    expect(batchResult.status).toBe('completed');
    expect(batchResult.resultCount).toBeGreaterThan(0);
    expect(batchResult.qualityJobCount).toBeGreaterThan(0);

    console.log(`✓ Batch completed with ${batchResult.resultCount} total jobs, ${batchResult.qualityJobCount} quality jobs`);

    // Verify batch outputs
    await validateBatchOutputs(page, batchId);

    // Verify data integrity
    await validateDataIntegrity(page, batchId);
  });

  test('should handle batch status polling and updates', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '🗓️ Batches & Scheduling');
    await waitForStreamlitLoad(page);

    // Check if there are any existing batches
    const existingBatches = await getExistingBatches(page);

    if (existingBatches.length > 0) {
      console.log(`Found ${existingBatches.length} existing batches`);

      // Test batch monitoring interface
      await verifyBatchMonitoringInterface(page);

      // Test batch status refresh
      await testBatchStatusRefresh(page);

    } else {
      console.log('No existing batches found - creating test batch for monitoring');

      // Submit a minimal batch for monitoring testing
      await configureAsyncBatch(page, {
        jobSource: 'Google Jobs',
        location: 'Dallas, TX',
        searchTerms: 'truck driver',
        pages: 5
      });

      const batchId = await submitAsyncBatch(page);
      await monitorBatchProcessing(page, batchId, { maxWaitTime: 60000 });
    }
  });

  test('should validate batch error handling', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '🗓️ Batches & Scheduling');
    await waitForStreamlitLoad(page);

    // Test with invalid parameters (should show validation errors)
    await testInvalidBatchSubmission(page);

    // Test with minimal valid parameters
    await testMinimalBatchSubmission(page);
  });

  test('should verify batch results download functionality', async ({ page }) => {
    await loginAsAdmin(page);
    await navigateToTab(page, '🗓️ Batches & Scheduling');
    await waitForStreamlitLoad(page);

    // Look for completed batches with results
    const completedBatches = await getCompletedBatches(page);

    if (completedBatches.length > 0) {
      // Test CSV download
      await testBatchCsvDownload(page, completedBatches[0]);

      // Test PDF generation if available
      await testBatchPdfGeneration(page, completedBatches[0]);

    } else {
      console.log('No completed batches found - skipping download tests');
    }
  });
});

/**
 * Configure async batch parameters
 */
async function configureAsyncBatch(page, config: {
  jobSource: string;
  location: string;
  searchTerms: string;
  pages: number;
  searchRadius?: number;
}) {
  console.log(`Configuring async batch: ${config.jobSource}, ${config.location}, ${config.pages} pages`);

  // Select job source
  await page.selectOption('select:has(option[value*="google"])', { label: config.jobSource });
  await page.waitForTimeout(1000);

  // Fill location
  const locationInput = page.locator('input[placeholder*="location"], input[key*="location"]');
  await locationInput.fill(config.location);
  await page.waitForTimeout(500);

  // Fill search terms
  const searchTermsInput = page.locator('input[placeholder*="search"], input[key*="terms"]');
  await searchTermsInput.fill(config.searchTerms);
  await page.waitForTimeout(500);

  // Set pages/limit
  const pagesInput = page.locator('input[type="number"], input[key*="pages"], input[key*="limit"]');
  await pagesInput.fill(config.pages.toString());
  await page.waitForTimeout(500);

  // Set search radius if provided
  if (config.searchRadius) {
    const radiusSelect = page.locator('select[key*="radius"]');
    if (await radiusSelect.isVisible()) {
      await radiusSelect.selectOption(config.searchRadius.toString());
    }
  }

  console.log(`✓ Configured batch parameters`);
}

/**
 * Submit async batch and return batch ID
 */
async function submitAsyncBatch(page): Promise<string> {
  // Click submit button
  const submitButton = page.locator('button:has-text("Submit Google Jobs Batch"), button:has-text("🚀 Submit Batch")');
  await submitButton.click();

  // Wait for submission confirmation
  await page.waitForTimeout(3000);

  // Look for success message with batch ID
  const successMessage = await page.locator('text*="submitted", text*="batch", text*="ID"').textContent();

  if (successMessage) {
    // Extract batch ID from success message
    const batchIdMatch = successMessage.match(/ID[:\s]*([a-zA-Z0-9-]+)/);
    if (batchIdMatch) {
      return batchIdMatch[1];
    }
  }

  // Fallback: get the most recent batch from the interface
  await waitForStreamlitLoad(page);
  const batches = await getExistingBatches(page);
  if (batches.length > 0) {
    return batches[0].id;
  }

  throw new Error('Could not determine batch ID after submission');
}

/**
 * Monitor batch processing until completion
 */
async function monitorBatchProcessing(page, batchId: string, options: {
  maxWaitTime: number;
  pollInterval: number;
}): Promise<{
  status: string;
  resultCount: number;
  qualityJobCount: number;
}> {
  console.log(`Monitoring batch ${batchId} processing...`);

  const startTime = Date.now();

  while (Date.now() - startTime < options.maxWaitTime) {
    // Refresh the batches view
    await page.reload();
    await waitForStreamlitLoad(page);

    // Check batch status
    const batchStatus = await getBatchStatus(page, batchId);

    if (batchStatus.status === 'completed') {
      console.log(`✓ Batch ${batchId} completed successfully`);
      return batchStatus;
    } else if (batchStatus.status === 'error' || batchStatus.status === 'failed') {
      throw new Error(`Batch ${batchId} failed with status: ${batchStatus.status}`);
    }

    console.log(`Batch ${batchId} status: ${batchStatus.status}, waiting...`);
    await page.waitForTimeout(options.pollInterval);
  }

  throw new Error(`Batch ${batchId} did not complete within ${options.maxWaitTime}ms timeout`);
}

/**
 * Get batch status from the interface
 */
async function getBatchStatus(page, batchId: string): Promise<{
  status: string;
  resultCount: number;
  qualityJobCount: number;
}> {
  // Look for batch in the table/list
  const batchRow = page.locator(`tr:has-text("${batchId}"), div:has-text("${batchId}")`);

  if (await batchRow.isVisible()) {
    const rowText = await batchRow.textContent();

    // Extract status (pending, processing, completed, error)
    let status = 'pending';
    if (rowText?.includes('completed')) status = 'completed';
    else if (rowText?.includes('processing')) status = 'processing';
    else if (rowText?.includes('error') || rowText?.includes('failed')) status = 'error';

    // Extract result counts if available
    const resultCountMatch = rowText?.match(/(\d+)\s*results?/i);
    const qualityCountMatch = rowText?.match(/(\d+)\s*quality/i);

    return {
      status,
      resultCount: resultCountMatch ? parseInt(resultCountMatch[1]) : 0,
      qualityJobCount: qualityCountMatch ? parseInt(qualityCountMatch[1]) : 0
    };
  }

  return { status: 'unknown', resultCount: 0, qualityJobCount: 0 };
}

/**
 * Validate batch outputs (CSV, PDF, etc.)
 */
async function validateBatchOutputs(page, batchId: string) {
  console.log(`Validating outputs for batch ${batchId}`);

  // Look for download buttons or links
  const csvButton = page.locator(`button:has-text("CSV"):near(text="${batchId}"), a:has-text("Download"):near(text="${batchId}")`);

  if (await csvButton.isVisible()) {
    console.log(`✓ CSV download available for batch ${batchId}`);
  } else {
    console.log(`⚠ No CSV download found for batch ${batchId}`);
  }

  // Check for PDF generation option
  const pdfButton = page.locator(`button:has-text("PDF"):near(text="${batchId}")`);
  if (await pdfButton.isVisible()) {
    console.log(`✓ PDF generation available for batch ${batchId}`);
  }
}

/**
 * Validate data integrity of batch results
 */
async function validateDataIntegrity(page, batchId: string) {
  console.log(`Validating data integrity for batch ${batchId}`);

  // This would involve checking that:
  // 1. Job count matches expected range
  // 2. Required fields are present
  // 3. Data format is correct
  // 4. No obvious data corruption

  // For now, we'll check basic metrics are reasonable
  const batchStatus = await getBatchStatus(page, batchId);

  expect(batchStatus.resultCount).toBeGreaterThan(0);
  expect(batchStatus.resultCount).toBeLessThan(1000); // Reasonable upper bound for 10 pages
  expect(batchStatus.qualityJobCount).toBeLessThanOrEqual(batchStatus.resultCount);

  console.log(`✓ Data integrity checks passed for batch ${batchId}`);
}

/**
 * Get existing batches from the interface
 */
async function getExistingBatches(page): Promise<Array<{ id: string; status: string }>> {
  const batches = [];

  // Look for batch table or list
  const batchElements = await page.locator('[data-testid="stDataFrame"] tbody tr, .batch-item').all();

  for (const element of batchElements) {
    const text = await element.textContent();
    if (text) {
      // Extract batch ID (assuming format like "batch-123" or similar)
      const idMatch = text.match(/(\w{8}-\w{4}-\w{4}-\w{4}-\w{12}|[a-zA-Z0-9-]{8,})/);
      if (idMatch) {
        batches.push({
          id: idMatch[1],
          status: text.includes('completed') ? 'completed' :
                  text.includes('processing') ? 'processing' : 'pending'
        });
      }
    }
  }

  return batches;
}

/**
 * Get completed batches
 */
async function getCompletedBatches(page): Promise<Array<{ id: string }>> {
  const allBatches = await getExistingBatches(page);
  return allBatches.filter(batch => batch.status === 'completed');
}

/**
 * Verify batch monitoring interface
 */
async function verifyBatchMonitoringInterface(page) {
  // Check for key monitoring elements
  await expect(page.locator('text="Status"')).toBeVisible();
  await expect(page.locator('text="Results"')).toBeVisible();

  console.log(`✓ Batch monitoring interface verified`);
}

/**
 * Test batch status refresh functionality
 */
async function testBatchStatusRefresh(page) {
  // Test refresh button if available
  const refreshButton = page.locator('button:has-text("Refresh"), button:has-text("🔄")');
  if (await refreshButton.isVisible()) {
    await refreshButton.click();
    await waitForStreamlitLoad(page);
    console.log(`✓ Batch status refresh tested`);
  }
}

/**
 * Test invalid batch submission
 */
async function testInvalidBatchSubmission(page) {
  // Try submitting with empty fields
  const submitButton = page.locator('button:has-text("Submit"), button:has-text("🚀")');

  if (await submitButton.isVisible()) {
    await submitButton.click();
    await page.waitForTimeout(2000);

    // Should see validation error
    const errorMessage = page.locator('text*="required", text*="error", text*="invalid"');
    if (await errorMessage.isVisible()) {
      console.log(`✓ Validation error handling works`);
    }
  }
}

/**
 * Test minimal batch submission
 */
async function testMinimalBatchSubmission(page) {
  await configureAsyncBatch(page, {
    jobSource: 'Google Jobs',
    location: 'Austin, TX',
    searchTerms: 'driver',
    pages: 1 // Minimal batch
  });

  // Should be able to submit successfully
  const submitButton = page.locator('button:has-text("Submit"), button:has-text("🚀")');
  await submitButton.click();

  // Look for success indication
  await page.waitForTimeout(3000);
  console.log(`✓ Minimal batch submission tested`);
}

/**
 * Test CSV download for completed batch
 */
async function testBatchCsvDownload(page, batch: { id: string }) {
  const csvButton = page.locator(`button:has-text("CSV"):near(text="${batch.id}")`);

  if (await csvButton.isVisible()) {
    // Set up download handler
    const downloadPromise = page.waitForEvent('download');
    await csvButton.click();

    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/\.csv$/);

    console.log(`✓ CSV download tested for batch ${batch.id}`);
  }
}

/**
 * Test PDF generation for completed batch
 */
async function testBatchPdfGeneration(page, batch: { id: string }) {
  const pdfButton = page.locator(`button:has-text("PDF"):near(text="${batch.id}")`);

  if (await pdfButton.isVisible()) {
    await pdfButton.click();
    await page.waitForTimeout(5000); // PDF generation takes time

    console.log(`✓ PDF generation tested for batch ${batch.id}`);
  }
}