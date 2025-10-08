// Supabase Edge Function to trigger scheduled batch execution
// This function will be called by pg_cron every hour

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
  try {
    // Only allow POST requests (from pg_cron or manual triggers)
    if (req.method !== 'POST') {
      return new Response(
        JSON.stringify({ error: 'Method not allowed' }),
        { status: 405, headers: { 'Content-Type': 'application/json' } }
      )
    }

    // Verify authorization (optional but recommended)
    const authHeader = req.headers.get('Authorization')
    const expectedToken = Deno.env.get('CRON_SECRET')

    if (expectedToken && authHeader !== `Bearer ${expectedToken}`) {
      return new Response(
        JSON.stringify({ error: 'Unauthorized' }),
        { status: 401, headers: { 'Content-Type': 'application/json' } }
      )
    }

    console.log('🔄 Scheduled batch runner triggered')
    console.log('⏰', new Date().toISOString())

    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseKey)

    // Get current time
    const now = new Date().toISOString()

    // Find all scheduled jobs that are due to run
    const { data: dueJobs, error: queryError } = await supabase
      .from('async_job_queue')
      .select('*')
      .eq('status', 'scheduled')
      .lte('scheduled_run_at', now)
      .order('scheduled_run_at', { ascending: true })

    if (queryError) {
      console.error('❌ Error querying jobs:', queryError)
      return new Response(
        JSON.stringify({ error: 'Database query failed', details: queryError }),
        { status: 500, headers: { 'Content-Type': 'application/json' } }
      )
    }

    if (!dueJobs || dueJobs.length === 0) {
      console.log('📭 No scheduled batches due to run')
      return new Response(
        JSON.stringify({ message: 'No batches due', executed: 0 }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      )
    }

    console.log(`📋 Found ${dueJobs.length} batch(es) to execute`)

    const results = []

    // Process each due job
    for (const job of dueJobs) {
      try {
        console.log(`🚀 Executing batch ${job.id} (${job.job_type})`)

        // Update status to 'submitted' to mark it as being processed
        const { error: updateError } = await supabase
          .from('async_job_queue')
          .update({
            status: 'submitted',
            submitted_at: new Date().toISOString()
          })
          .eq('id', job.id)

        if (updateError) {
          console.error(`❌ Failed to update job ${job.id}:`, updateError)
          results.push({
            job_id: job.id,
            success: false,
            error: 'Failed to update job status'
          })
          continue
        }

        // For recurring batches, create next run
        const frequency = job.search_params?.frequency
        if (frequency && frequency !== 'Once') {
          console.log(`🔄 Recurring batch - scheduling next run...`)

          // Calculate next run time
          const currentRun = new Date(job.scheduled_run_at)
          let nextRun = new Date(currentRun)

          if (frequency.toLowerCase() === 'daily') {
            nextRun.setDate(nextRun.getDate() + 1)
          } else if (frequency.toLowerCase() === 'weekly') {
            nextRun.setDate(nextRun.getDate() + 7)
          } else {
            nextRun.setDate(nextRun.getDate() + 1)
          }

          // Create new scheduled job
          const newJobData = {
            ...job,
            id: undefined, // Remove ID so a new one is created
            status: 'scheduled',
            scheduled_run_at: nextRun.toISOString(),
            submitted_at: null,
            completed_at: null,
            result_count: 0,
            quality_job_count: 0,
            created_at: new Date().toISOString()
          }

          const { error: createError } = await supabase
            .from('async_job_queue')
            .insert(newJobData)

          if (createError) {
            console.error('❌ Failed to create next run:', createError)
          } else {
            console.log(`📅 Next run scheduled for ${nextRun.toISOString()}`)
          }
        }

        results.push({
          job_id: job.id,
          success: true,
          job_type: job.job_type
        })

      } catch (error) {
        console.error(`❌ Error processing job ${job.id}:`, error)
        results.push({
          job_id: job.id,
          success: false,
          error: error.message
        })
      }
    }

    const executed = results.filter(r => r.success).length
    const failed = results.filter(r => !r.success).length

    console.log(`✅ Executed: ${executed}, ❌ Failed: ${failed}`)

    return new Response(
      JSON.stringify({
        message: 'Batch execution complete',
        executed,
        failed,
        results
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('❌ Edge function error:', error)
    return new Response(
      JSON.stringify({ error: 'Internal server error', details: error.message }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    )
  }
})
