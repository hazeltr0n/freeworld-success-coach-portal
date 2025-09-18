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

    // For negative feedback, update the job classification to 'bad' to remove from future searches
    const negativeTypes = ['job_expired', 'requires_experience', 'not_fair_chance_friendly']
    if (negativeTypes.includes(feedback_type)) {
      console.log(`Marking job as bad due to ${feedback_type} feedback`)

      // Update jobs table to mark this job as 'bad' classification
      const { error: updateError } = await supabase
        .from('jobs')
        .update({
          ai_match: 'bad',
          ai_summary: `Marked as bad due to agent feedback: ${feedback_type}`
        })
        .eq('apply_url', job_url)

      if (updateError) {
        console.error('Error updating job classification:', updateError)
        // Don't fail the feedback submission if job update fails
      } else {
        console.log('Successfully marked job as bad classification')
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