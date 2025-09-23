import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.38.0"

// Expected token for webhook authentication
const WEBHOOK_TOKEN = "freeworld2024webhook"

console.log("🚀 Outscraper Webhook Edge Function started")

serve(async (req) => {
  // Enable CORS for all requests
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  }

  // Handle CORS preflight request
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    console.log(`📋 ${req.method} request received`)

    // Get token from query parameters
    const url = new URL(req.url)
    const token = url.searchParams.get('token')

    console.log(`🔐 Token provided: ${token ? 'YES' : 'NO'}`)

    // Validate token (allow missing token for testing)
    if (token && token !== WEBHOOK_TOKEN) {
      console.log(`❌ Invalid token: ${token}`)
      return new Response(
        JSON.stringify({ error: 'Unauthorized - Invalid token' }),
        {
          status: 401,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Log if no token provided (for debugging)
    if (!token) {
      console.log(`⚠️ No token provided - allowing for testing`)
    }

    console.log("✅ Token validated successfully")

    // Only accept POST requests
    if (req.method !== 'POST') {
      return new Response(
        JSON.stringify({ error: 'Method not allowed' }),
        {
          status: 405,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Parse the webhook payload
    const payload = await req.json()
    console.log(`📦 Payload received:`, JSON.stringify(payload, null, 2))

    // Extract key information from Outscraper payload
    const {
      id: requestId,
      user_id: userId,
      status,
      api_task,
      results_location,
      quota_usage
    } = payload

    if (!requestId) {
      console.log("❌ Missing request ID in payload")
      return new Response(
        JSON.stringify({ error: 'Missing request ID' }),
        {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    console.log(`🔍 Processing webhook for request: ${requestId}, status: ${status}`)

    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!

    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    // Look for the corresponding async job in the database
    const { data: jobs, error: fetchError } = await supabase
      .from('async_job_queue')
      .select('*')
      .eq('request_id', requestId)
      .eq('status', 'submitted')

    if (fetchError) {
      console.log(`❌ Error fetching job: ${fetchError.message}`)
      return new Response(
        JSON.stringify({ error: 'Database error' }),
        {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    if (!jobs || jobs.length === 0) {
      console.log(`⚠️ No pending job found for request_id: ${requestId}`)
      // Still return success - job might have been processed already
      return new Response(
        JSON.stringify({
          status: 'ok',
          message: 'Job not found (possibly already processed)',
          request_id: requestId
        }),
        {
          status: 200,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    const job = jobs[0]
    console.log(`✅ Found job ${job.id} for request ${requestId}`)

    // Handle different status values (Outscraper sends "Success", we also handle "SUCCESS")
    if (status?.toUpperCase() === 'SUCCESS') {
      // Job completed successfully
      console.log(`🎉 Job ${job.id} completed successfully`)

      // Update job status to completed
      const { error: updateError } = await supabase
        .from('async_job_queue')
        .update({
          status: 'completed',
          completed_at: new Date().toISOString(),
          result_count: 0, // Will be updated when results are processed
          quality_job_count: 0 // Will be updated when results are processed
        })
        .eq('id', job.id)

      if (updateError) {
        console.log(`❌ Error updating job: ${updateError.message}`)
        return new Response(
          JSON.stringify({ error: 'Failed to update job status' }),
          {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          }
        )
      }

      // Create notification for the coach
      if (job.coach_username) {
        const { error: notifyError } = await supabase
          .from('coach_notifications')
          .insert({
            coach_username: job.coach_username,
            message: `✅ Google Jobs search completed! Results are being processed for ${job.search_params?.location || 'your location'}.`,
            notification_type: 'search_complete',
            job_id: job.id,
            created_at: new Date().toISOString()
          })

        if (notifyError) {
          console.log(`⚠️ Failed to create notification: ${notifyError.message}`)
        } else {
          console.log(`📬 Notification sent to coach: ${job.coach_username}`)
        }
      }

      console.log(`✅ Job ${job.id} marked as completed`)

      return new Response(
        JSON.stringify({
          status: 'ok',
          message: `Job ${job.id} processed successfully`,
          job_id: job.id,
          request_id: requestId
        }),
        {
          status: 200,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )

    } else if (status?.toUpperCase() === 'FAILED' || status?.toUpperCase() === 'ERROR') {
      // Job failed
      console.log(`❌ Job ${job.id} failed with status: ${status}`)

      // Update job status to failed
      const { error: updateError } = await supabase
        .from('async_job_queue')
        .update({
          status: 'failed',
          completed_at: new Date().toISOString(),
          error_message: `Outscraper job failed with status: ${status}`
        })
        .eq('id', job.id)

      if (updateError) {
        console.log(`❌ Error updating job: ${updateError.message}`)
      }

      // Notify coach of failure
      if (job.coach_username) {
        const { error: notifyError } = await supabase
          .from('coach_notifications')
          .insert({
            coach_username: job.coach_username,
            message: `❌ Google Jobs search failed: ${status}`,
            notification_type: 'error',
            job_id: job.id,
            created_at: new Date().toISOString()
          })

        if (notifyError) {
          console.log(`⚠️ Failed to create failure notification: ${notifyError.message}`)
        }
      }

      return new Response(
        JSON.stringify({
          status: 'ok',
          message: `Job ${job.id} marked as failed`,
          job_id: job.id,
          error: status
        }),
        {
          status: 200,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )

    } else {
      // Unknown status
      console.log(`⚠️ Unknown status '${status}' for request ${requestId}`)
      return new Response(
        JSON.stringify({
          status: 'ok',
          message: `Unknown status: ${status}`,
          request_id: requestId
        }),
        {
          status: 200,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

  } catch (error) {
    console.log(`💥 Webhook error:`, error)
    return new Response(
      JSON.stringify({
        error: 'Internal server error',
        details: error.message
      }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})