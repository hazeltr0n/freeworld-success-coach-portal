import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.44.0';

serve(async (req) => {
  const url = new URL(req.url);
  const targetUrl = url.searchParams.get('target');
  const candidateId = url.searchParams.get('candidate_id');
  const coach = url.searchParams.get('coach');
  const market = url.searchParams.get('market');
  const route = url.searchParams.get('route');
  const match = url.searchParams.get('match');
  const fair = url.searchParams.get('fair');
  const shortId = crypto.randomUUID();

  // Initialize Supabase client
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL') ?? '', 
    Deno.env.get('SUPABASE_ANON_KEY') ?? '', 
    {
      global: {
        headers: {
          'x-my-custom-header': 'FreeWorld-Edge-Function'
        }
      }
    }
  );

  if (targetUrl) {
    // Create click event data
    const clickData = {
      clicked_at: new Date().toISOString(),
      original_url: targetUrl,
      candidate_id: candidateId,
      coach: coach,
      market: market,
      route: route,
      match: match,
      fair: fair === 'true',
      short_id: shortId
    };

    // Log click event to Supabase
    const { data, error } = await supabase.from('click_events').insert([clickData]);
    
    if (error) {
      console.error('Error logging click event:', error);
    }

    // Send to Zapier webhook
    try {
      const zapierUrl = 'https://hooks.zapier.com/hooks/catch/20082291/uhwh021/';
      await fetch(zapierUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event: 'job_click', payload: clickData })
      });
    } catch (zapError) {
      console.log('Zapier webhook failed (non-fatal):', zapError?.message);
    }

    // Redirect to target URL
    return new Response(null, {
      status: 302,
      headers: {
        'Location': targetUrl
      }
    });
  } else {
    return new Response('Missing target URL', {
      status: 400
    });
  }
});