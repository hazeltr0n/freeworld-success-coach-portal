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
      let updateError = null

      // First try: Match by apply_url
      const { error: error1 } = await supabase
        .from('jobs')
        .update({ job_flagged: true })
        .eq('apply_url', job_url)

      if (error1) {
        console.log(`Direct apply_url match failed: ${error1.message}`)
        // Second try: Match by tracked_url
        const { error: error2 } = await supabase
          .from('jobs')
          .update({ job_flagged: true })
          .eq('tracked_url', job_url)

        if (error2) {
          console.log(`tracked_url match also failed: ${error2.message}`)
          updateError = error2
        } else {
          console.log(`Successfully flagged job by tracked_url`)
        }
      } else {
        console.log(`Successfully flagged job by apply_url`)
      }

      if (updateError) {
        console.error('Error flagging job:', updateError)
      }

    } else if (temporaryNegativeTypes.includes(feedback_type)) {
      console.log(`Incrementing expired counter for ${feedback_type} feedback`)

      // Temporary negative feedback - get current value, increment, and update
      let jobUpdated = false

      // First try: Match by apply_url
      try {
        const { data: jobData, error: fetchError } = await supabase
          .from('jobs')
          .select('feedback_expired_links')
          .eq('apply_url', job_url)
          .single()

        if (!fetchError && jobData) {
          const currentCount = jobData.feedback_expired_links || 0
          const { error: updateError1 } = await supabase
            .from('jobs')
            .update({
              feedback_expired_links: currentCount + 1,
              last_expired_feedback_at: new Date().toISOString()
            })
            .eq('apply_url', job_url)

          if (!updateError1) {
            console.log(`Successfully incremented expired counter by apply_url`)
            jobUpdated = true
          } else {
            console.log(`Apply URL update failed: ${updateError1.message}`)
          }
        }
      } catch (error: any) {
        console.log(`Apply URL lookup failed: ${error.message}`)
      }

      // Second try: Match by tracked_url if first attempt failed
      if (!jobUpdated) {
        try {
          const { data: jobData, error: fetchError } = await supabase
            .from('jobs')
            .select('feedback_expired_links')
            .eq('tracked_url', job_url)
            .single()

          if (!fetchError && jobData) {
            const currentCount = jobData.feedback_expired_links || 0
            const { error: updateError2 } = await supabase
              .from('jobs')
              .update({
                feedback_expired_links: currentCount + 1,
                last_expired_feedback_at: new Date().toISOString()
              })
              .eq('tracked_url', job_url)

            if (!updateError2) {
              console.log(`Successfully incremented expired counter by tracked_url`)
              jobUpdated = true
            } else {
              console.log(`Tracked URL update failed: ${updateError2.message}`)
            }
          } else {
            console.log(`Tracked URL lookup failed: ${fetchError?.message}`)
          }
        } catch (error: any) {
          console.log(`Tracked URL lookup failed: ${error.message}`)
        }
      }

      if (!jobUpdated) {
        console.error('Error incrementing expired counter: No matching job found')
      }

    } else if (positiveTypes.includes(feedback_type)) {
      console.log(`Incrementing likes counter for ${feedback_type} feedback`)

      // Positive feedback - get current value, increment, and update
      let jobUpdated = false

      // First try: Match by apply_url
      try {
        const { data: jobData, error: fetchError } = await supabase
          .from('jobs')
          .select('feedback_likes')
          .eq('apply_url', job_url)
          .single()

        if (!fetchError && jobData) {
          const currentCount = jobData.feedback_likes || 0
          const { error: updateError1 } = await supabase
            .from('jobs')
            .update({
              feedback_likes: currentCount + 1
            })
            .eq('apply_url', job_url)

          if (!updateError1) {
            console.log(`Successfully incremented likes by apply_url`)
            jobUpdated = true
          } else {
            console.log(`Apply URL likes update failed: ${updateError1.message}`)
          }
        }
      } catch (error: any) {
        console.log(`Apply URL likes lookup failed: ${error.message}`)
      }

      // Second try: Match by tracked_url if first attempt failed
      if (!jobUpdated) {
        try {
          const { data: jobData, error: fetchError } = await supabase
            .from('jobs')
            .select('feedback_likes')
            .eq('tracked_url', job_url)
            .single()

          if (!fetchError && jobData) {
            const currentCount = jobData.feedback_likes || 0
            const { error: updateError2 } = await supabase
              .from('jobs')
              .update({
                feedback_likes: currentCount + 1
              })
              .eq('tracked_url', job_url)

            if (!updateError2) {
              console.log(`Successfully incremented likes by tracked_url`)
              jobUpdated = true
            } else {
              console.log(`Tracked URL likes update failed: ${updateError2.message}`)
            }
          } else {
            console.log(`Tracked URL likes lookup failed: ${fetchError?.message}`)
          }
        } catch (error: any) {
          console.log(`Tracked URL likes lookup failed: ${error.message}`)
        }
      }

      if (!jobUpdated) {
        console.error('Error incrementing likes: No matching job found')
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