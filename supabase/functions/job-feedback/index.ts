import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Initialize Supabase client with service role key for server-side operations
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    const { candidate_id, job_id, job_url, job_title, company, feedback_type, location, coach } = await req.json()

    // Validate required fields
    if (!candidate_id || !job_url) {
      return new Response(
        JSON.stringify({ success: false, message: 'Missing required fields: candidate_id and job_url' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Insert feedback into database
    const { data, error } = await supabase
      .from('job_feedback')
      .insert({
        candidate_id,
        job_id: job_id || null,
        job_url,
        job_title: job_title || null,
        company: company || null,
        feedback_type: feedback_type || 'job_expired',
        location: location || null,
        coach: coach || null,
        created_at: new Date().toISOString()
      })

    if (error) {
      console.error('Database error:', error)
      return new Response(
        JSON.stringify({ success: false, message: 'Failed to save feedback' }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Enhanced feedback system with counters and expiry logic
    const permanentNegativeTypes = ['requires_experience', 'not_fair_chance_friendly']
    const temporaryNegativeTypes = ['job_expired']
    const positiveTypes = ['i_like_this_job', 'i_applied_to_this_job']

    if (permanentNegativeTypes.includes(feedback_type)) {
      console.log(`Setting permanent flag for ${feedback_type} feedback`)

      // Permanent negative feedback - set job_flagged = true
      // Use job_id for matching instead of URL matching
      if (job_id) {
        const { error: updateError } = await supabase
          .from('jobs')
          .update({ job_flagged: true })
          .eq('job_id', job_id)

        if (updateError) {
          console.error('Error flagging job by job_id:', updateError)
        } else {
          console.log(`Successfully flagged job by job_id: ${job_id}`)
        }
      } else {
        console.error('No job_id provided for permanent negative feedback')
      }

    } else if (temporaryNegativeTypes.includes(feedback_type)) {
      console.log(`Incrementing expired counter for ${feedback_type} feedback`)

      // Temporary negative feedback - get current value, increment, and update
      // Use job_id for matching instead of URL matching
      if (job_id) {
        try {
          console.log(`Looking up job with job_id: ${job_id}`)
          const { data: jobData, error: fetchError } = await supabase
            .from('jobs')
            .select('feedback_expired_links')
            .eq('job_id', job_id)

          console.log(`Lookup result: data=${JSON.stringify(jobData)}, error=${JSON.stringify(fetchError)}`)

          if (!fetchError && jobData && jobData.length > 0) {
            const currentCount = jobData[0].feedback_expired_links || 0
            console.log(`Current expired count: ${currentCount}, incrementing to ${currentCount + 1}`)

            const { error: updateError } = await supabase
              .from('jobs')
              .update({
                feedback_expired_links: currentCount + 1,
                last_expired_feedback_at: new Date().toISOString()
              })
              .eq('job_id', job_id)

            if (!updateError) {
              console.log(`✅ Successfully incremented expired counter by job_id: ${job_id}`)
            } else {
              console.error(`❌ Job ID update failed: ${updateError.message}`)
            }
          } else if (fetchError) {
            console.error(`❌ Job ID lookup failed: ${fetchError.message}`)
          } else {
            console.error(`❌ No job found with job_id: ${job_id}`)
          }
        } catch (error: any) {
          console.error(`❌ Job ID lookup exception: ${error.message}`)
        }
      } else {
        console.error('❌ No job_id provided for temporary negative feedback')
      }

    } else if (positiveTypes.includes(feedback_type)) {
      console.log(`Incrementing likes counter for ${feedback_type} feedback`)

      // Positive feedback - get current value, increment, and update
      // Use job_id for matching instead of URL matching
      if (job_id) {
        try {
          console.log(`Looking up job for likes with job_id: ${job_id}`)
          const { data: jobData, error: fetchError } = await supabase
            .from('jobs')
            .select('feedback_likes')
            .eq('job_id', job_id)

          console.log(`Likes lookup result: data=${JSON.stringify(jobData)}, error=${JSON.stringify(fetchError)}`)

          if (!fetchError && jobData && jobData.length > 0) {
            const currentCount = jobData[0].feedback_likes || 0
            console.log(`Current likes count: ${currentCount}, incrementing to ${currentCount + 1}`)

            const { error: updateError } = await supabase
              .from('jobs')
              .update({
                feedback_likes: currentCount + 1
              })
              .eq('job_id', job_id)

            if (!updateError) {
              console.log(`✅ Successfully incremented likes by job_id: ${job_id}`)
            } else {
              console.error(`❌ Job ID likes update failed: ${updateError.message}`)
            }
          } else if (fetchError) {
            console.error(`❌ Job ID likes lookup failed: ${fetchError.message}`)
          } else {
            console.error(`❌ No job found for likes with job_id: ${job_id}`)
          }
        } catch (error: any) {
          console.error(`❌ Job ID likes lookup exception: ${error.message}`)
        }
      } else {
        console.error('❌ No job_id provided for positive feedback')
      }

      // For "i_applied_to_this_job", also increment agent's application counter
      if (feedback_type === 'i_applied_to_this_job' && candidate_id) {
        console.log(`Incrementing application counter for agent ${candidate_id}`)

        try {
          const { data: agentData, error: fetchError } = await supabase
            .from('agent_profiles')
            .select('total_applications')
            .eq('agent_uuid', candidate_id)
            .single()

          if (!fetchError && agentData) {
            const currentApps = agentData.total_applications || 0
            const { error: agentError } = await supabase
              .from('agent_profiles')
              .update({
                total_applications: currentApps + 1,
                last_application_at: new Date().toISOString()
              })
              .eq('agent_uuid', candidate_id)

            if (agentError) {
              console.error('Error updating agent application counter:', agentError)
            } else {
              console.log('Successfully updated agent application counter')
            }
          } else {
            console.log(`Agent lookup failed: ${fetchError?.message}`)
          }
        } catch (error: any) {
          console.log(`Agent application counter update failed: ${error.message}`)
        }
      }
    }

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Feedback received. Thank you for helping us improve job quality!'
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Function error:', error)
    return new Response(
      JSON.stringify({ success: false, message: 'Internal server error' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})