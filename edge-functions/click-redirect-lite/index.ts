/**
 * click-redirect-lite - Supabase Edge Function
 *
 * Minimal click redirector that:
 * - Accepts GET requests with query params
 *   - target: required, the destination URL to redirect to
 *   - candidate_id, coach, market, route, match, fair: optional context
 * - Inserts a row into public.click_events (schema provided in repo)
 * - Issues a 302 redirect to the target URL
 */
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type"
};

function isValidHttpUrl(url) {
  try {
    const u = new URL(url);
    return u.protocol === "http:" || u.protocol === "https:";
  } catch (_) {
    return false;
  }
}

serve(async (req) => {
  // CORS preflight
  if (req.method === "OPTIONS") {
    return new Response("ok", {
      headers: corsHeaders
    });
  }

  try {
    if (req.method !== "GET") {
      return new Response("Method not allowed", {
        status: 405,
        headers: corsHeaders
      });
    }

    const url = new URL(req.url);
    const target = url.searchParams.get("target") ?? "";

    if (!target || !isValidHttpUrl(target)) {
      return new Response(JSON.stringify({
        error: "Missing or invalid 'target' parameter"
      }), {
        status: 400,
        headers: {
          ...corsHeaders,
          "Content-Type": "application/json"
        }
      });
    }

    // Optional attribution/context
    const candidate_id = url.searchParams.get("candidate_id");
    const coach = url.searchParams.get("coach");
    const candidate_name = url.searchParams.get("candidate_name");
    const market = url.searchParams.get("market");
    const route = url.searchParams.get("route");
    const match = url.searchParams.get("match");
    const fairRaw = url.searchParams.get("fair");
    const fair = fairRaw ? [
      "1",
      "true",
      "yes"
    ].includes(fairRaw.toLowerCase()) : null;

    // Initialize Supabase
    const supabaseUrl = Deno.env.get("SUPABASE_URL");
    const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || Deno.env.get("SUPABASE_ANON_KEY");

    // Debug support: if debug=1, return JSON instead of redirect to make troubleshooting easy
    const debugMode = url.searchParams.get("debug") === "1";

    const debug = {
      timestamp: new Date().toISOString(),
      env: {
        has_supabase_url: Boolean(supabaseUrl),
        has_service_key: Boolean(serviceKey)
      },
      params: {
        candidate_id,
        coach,
        candidate_name,
        market,
        route,
        match,
        fair
      },
      insert: {
        attempted: false,
        error: null
      },
      target
    };

    if (supabaseUrl && serviceKey) {
      try {
        const supabase = createClient(supabaseUrl, serviceKey);

        // Best-effort insert; do not block redirect on failure
        // Compatibility: some deployments use 'original_url', others use 'target_url'.
        const base = {};
        if (candidate_id) base.candidate_id = candidate_id;
        if (coach) base.coach = coach;
        if (candidate_name) base.candidate_name = candidate_name;
        if (market) base.market = market;
        if (route) base.route = route;
        if (match) base.match = match;
        if (fair !== null) base.fair = fair;

        // Enrich missing fields from agent_profiles when candidate_id is present
        try {
          if (candidate_id && (!base.coach || !base.market || !base.candidate_name)) {
            const { data: agent, error: agentErr } = await supabase
              .from('agent_profiles')
              .select('agent_name, coach_username, search_config')
              .eq('agent_uuid', candidate_id)
              .maybeSingle();

            if (!agentErr && agent) {
              if (!base.coach && agent.coach_username) base.coach = agent.coach_username;
              if (!base.candidate_name && agent.agent_name) base.candidate_name = agent.agent_name;
              if (!base.market && agent.search_config) {
                try {
                  const cfg = typeof agent.search_config === 'string' ? JSON.parse(agent.search_config) : agent.search_config;
                  if (cfg && cfg.location) base.market = cfg.location;
                } catch (_) {}
              }
            }
          }
        } catch (_) {}

        debug.insert.attempted = true;

        // Try original_url first (matches existing shortio webhook schema)
        let errMsg = null;
        let res = await supabase.from("click_events").insert({
          ...base,
          original_url: target
        });

        if (res.error) {
          errMsg = res.error.message || String(res.error);
          // Retry with target_url field name
          res = await supabase.from("click_events").insert({
            ...base,
            target_url: target
          });
          if (res.error) {
            errMsg = res.error.message || String(res.error);
          } else {
            errMsg = null;
          }
        } else {
          errMsg = null;
        }

        if (errMsg) {
          debug.insert.error = errMsg;
          console.log("click-redirect-lite insert failed:", errMsg);
        } else {
          // Successfully logged click - now trigger analytics refresh for this agent
          if (candidate_id) {
            try {
              console.log(`Triggering analytics refresh for agent ${candidate_id} after click`);
              const { error: refreshError } = await supabase.rpc('refresh_free_agents_analytics');

              if (refreshError) {
                console.error('Error refreshing agent analytics after click:', refreshError);
              } else {
                console.log('Successfully refreshed agent analytics after click');
              }
            } catch (refreshErr) {
              console.error('Exception during analytics refresh after click:', refreshErr.message);
            }
          }
        }

      } catch (e) {
        debug.insert.attempted = true;
        debug.insert.error = e?.message || String(e);
        console.log("click-redirect-lite insert failed:", debug.insert.error);
      }
    } else {
      if (!supabaseUrl) console.log("click-redirect-lite missing SUPABASE_URL");
      if (!serviceKey) console.log("click-redirect-lite missing SUPABASE_SERVICE_ROLE_KEY/SUPABASE_ANON_KEY");
    }

    if (debugMode) {
      return new Response(JSON.stringify(debug, null, 2), {
        status: 200,
        headers: {
          ...corsHeaders,
          "Content-Type": "application/json"
        }
      });
    }

    // 302 redirect to target
    return new Response(null, {
      status: 302,
      headers: {
        ...corsHeaders,
        Location: target,
        "Cache-Control": "no-store"
      }
    });

  } catch (err) {
    return new Response(JSON.stringify({
      error: err?.message || "Internal error"
    }), {
      status: 500,
      headers: {
        ...corsHeaders,
        "Content-Type": "application/json"
      }
    });
  }
});