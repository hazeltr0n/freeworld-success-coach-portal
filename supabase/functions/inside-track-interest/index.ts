/**
 * inside-track-interest - Supabase Edge Function
 *
 * Handles Free Agent interest in Inside Track (partner) jobs.
 * - GET: Shows a confirmation page with job details
 * - POST: Records interest and shows thank you page
 *
 * Query params:
 * - job_id: The inside track job ID (required)
 * - agent_id: Free Agent UUID (required)
 * - agent_name: Free Agent name (optional, for display)
 */
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

// Simple SMTP email sender - mimics Python's smtplib approach
async function sendEmailSmtp(
  to: string,
  subject: string,
  htmlBody: string,
  textBody?: string
): Promise<boolean> {
  const gmailAddress = Deno.env.get("GMAIL_ADDRESS");
  const gmailAppPassword = Deno.env.get("GMAIL_APP_PASSWORD");

  if (!gmailAddress || !gmailAppPassword) {
    console.log("📧 GMAIL credentials not set");
    return false;
  }

  try {
    const boundary = "----=_Part_" + Math.random().toString(36).substring(2);

    // Build email like Python's MIMEMultipart('alternative')
    let emailContent = `From: ${gmailAddress}\r\n`;
    emailContent += `To: ${to}\r\n`;
    emailContent += `Subject: ${subject}\r\n`;
    emailContent += `MIME-Version: 1.0\r\n`;
    emailContent += `Content-Type: multipart/alternative; boundary="${boundary}"\r\n`;
    emailContent += `\r\n`;

    // Plain text part (if provided)
    if (textBody) {
      emailContent += `--${boundary}\r\n`;
      emailContent += `Content-Type: text/plain; charset="utf-8"\r\n`;
      emailContent += `\r\n`;
      emailContent += `${textBody}\r\n`;
    }

    // HTML part
    emailContent += `--${boundary}\r\n`;
    emailContent += `Content-Type: text/html; charset="utf-8"\r\n`;
    emailContent += `\r\n`;
    emailContent += `${htmlBody}\r\n`;
    emailContent += `--${boundary}--\r\n`;

    // Connect to Gmail SMTP over TLS
    const conn = await Deno.connectTls({
      hostname: "smtp.gmail.com",
      port: 465,
    });

    const encoder = new TextEncoder();
    const decoder = new TextDecoder();

    async function send(cmd: string): Promise<string> {
      await conn.write(encoder.encode(cmd + "\r\n"));
      const buf = new Uint8Array(1024);
      const n = await conn.read(buf);
      return decoder.decode(buf.subarray(0, n || 0));
    }

    async function read(): Promise<string> {
      const buf = new Uint8Array(1024);
      const n = await conn.read(buf);
      return decoder.decode(buf.subarray(0, n || 0));
    }

    // SMTP conversation
    await read(); // greeting
    await send(`EHLO localhost`);
    await send(`AUTH LOGIN`);
    await send(btoa(gmailAddress));
    await send(btoa(gmailAppPassword));
    await send(`MAIL FROM:<${gmailAddress}>`);
    await send(`RCPT TO:<${to}>`);
    await send(`DATA`);
    await conn.write(encoder.encode(emailContent + "\r\n.\r\n"));
    await read();
    await send(`QUIT`);

    conn.close();
    console.log(`📧 Email sent to ${to}`);
    return true;
  } catch (e) {
    console.error("📧 SMTP error:", e);
    return false;
  }
}

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
};

// FreeWorld brand colors
const STYLES = `
  :root {
    --fw-roots: #004751;
    --fw-midnight: #191931;
    --fw-freedom-green: #CDF95C;
    --fw-horizon-grey: #F4F4F4;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--fw-horizon-grey);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
  }
  .card {
    background: white;
    border-radius: 16px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.1);
    max-width: 480px;
    width: 100%;
    overflow: hidden;
  }
  .header {
    background: linear-gradient(135deg, var(--fw-midnight), #32326e);
    color: white;
    padding: 24px;
    text-align: center;
  }
  .header h1 { font-size: 20px; margin-bottom: 8px; }
  .header .badge {
    display: inline-block;
    background: var(--fw-freedom-green);
    color: var(--fw-midnight);
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
  }
  .content { padding: 24px; }
  .job-title { font-size: 22px; color: var(--fw-roots); margin-bottom: 8px; }
  .company { font-size: 16px; color: #666; margin-bottom: 16px; }
  .details { background: var(--fw-horizon-grey); padding: 16px; border-radius: 8px; margin-bottom: 20px; }
  .details p { margin: 8px 0; font-size: 14px; color: #444; }
  .details strong { color: var(--fw-midnight); }
  .description { font-size: 14px; line-height: 1.6; color: #444; margin-bottom: 24px; }
  .btn {
    display: block;
    width: 100%;
    padding: 16px 24px;
    font-size: 16px;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    text-align: center;
    text-decoration: none;
    transition: transform 0.2s, box-shadow 0.2s;
  }
  .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
  .btn-primary {
    background: var(--fw-freedom-green);
    color: var(--fw-midnight);
  }
  .btn-secondary {
    background: white;
    color: var(--fw-roots);
    border: 2px solid var(--fw-roots);
    margin-top: 12px;
  }
  .success-icon { font-size: 64px; margin-bottom: 16px; }
  .footer { text-align: center; padding: 16px; color: #999; font-size: 12px; }
  .error { color: #dc2626; background: #fef2f2; padding: 16px; border-radius: 8px; margin-bottom: 16px; }
  .form-group { margin-bottom: 16px; }
  .form-group label { display: block; font-weight: 600; margin-bottom: 6px; color: var(--fw-midnight); }
  .form-group input {
    width: 100%;
    padding: 12px;
    border: 2px solid #ddd;
    border-radius: 8px;
    font-size: 16px;
    transition: border-color 0.2s;
  }
  .form-group input:focus { outline: none; border-color: var(--fw-roots); }
  .form-note { font-size: 13px; color: #666; margin-top: 4px; }
`;

function renderPage(title: string, body: string): Response {
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title} - FreeWorld</title>
  <style>${STYLES}</style>
</head>
<body>
  ${body}
</body>
</html>`;

  return new Response(html, {
    headers: { ...corsHeaders, "Content-Type": "text/html; charset=utf-8" },
  });
}

serve(async (req) => {
  // CORS preflight
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
  const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  const supabase = createClient(supabaseUrl, supabaseServiceKey);

  const url = new URL(req.url);
  const job_id = url.searchParams.get("job_id");
  const agent_id = url.searchParams.get("agent_id");
  const agent_name = url.searchParams.get("agent_name") || "Free Agent";

  // Validate required params
  if (!job_id || !agent_id) {
    return renderPage("Error", `
      <div class="card">
        <div class="header">
          <div class="badge">FREEWORLD PARTNER OPPORTUNITY</div>
          <h1>Invalid Link</h1>
        </div>
        <div class="content">
          <div class="error">
            <p>This link is missing required information. Please use the link from your job feed.</p>
          </div>
        </div>
      </div>
    `);
  }

  // Fetch job details
  const { data: job, error: jobError } = await supabase
    .from("jobs")
    .select("*")
    .eq("job_id", job_id)
    .eq("source", "inside_track")
    .single();

  if (jobError || !job) {
    return renderPage("Job Not Found", `
      <div class="card">
        <div class="header">
          <div class="badge">FREEWORLD PARTNER OPPORTUNITY</div>
          <h1>Job Not Found</h1>
        </div>
        <div class="content">
          <div class="error">
            <p>This job posting is no longer available. Please check your job feed for current opportunities.</p>
          </div>
        </div>
      </div>
    `);
  }

  // Fetch agent details
  const { data: agent } = await supabase
    .from("agent_profiles")
    .select("agent_name, agent_email, admin_portal_url")
    .eq("agent_uuid", agent_id)
    .single();

  // Check if this is a fetch request (wants JSON) vs browser navigation (wants HTML)
  const acceptHeader = req.headers.get("accept") || "";
  const wantsJson = acceptHeader.includes("application/json") || req.headers.get("content-type")?.includes("application/json");

  // Check if agent has full profile (admin_portal_url means they're a known agent)
  const hasFullProfile = agent?.admin_portal_url ? true : false;

  // Handle POST - Record interest
  if (req.method === "POST") {
    try {
      // Get name/phone from query params (from JS fetch) or form data
      let formName = url.searchParams.get("name") || "";
      let formPhone = url.searchParams.get("phone") || "";

      // Also check form data as fallback
      const contentType = req.headers.get("content-type") || "";
      if (!formName && !formPhone && contentType.includes("application/x-www-form-urlencoded")) {
        const formData = await req.formData();
        formName = (formData.get("name") as string) || "";
        formPhone = (formData.get("phone") as string) || "";
      }

      // If agent doesn't have full profile, require name and phone
      if (!hasFullProfile && (!formName || !formPhone)) {
        if (wantsJson) {
          return new Response(JSON.stringify({ success: false, error: "Name and phone required" }), {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          });
        }
        return renderPage("Missing Information", `
          <div class="card">
            <div class="header">
              <div class="badge">FREEWORLD PARTNER OPPORTUNITY</div>
              <h1>Missing Information</h1>
            </div>
            <div class="content">
              <div class="error">
                <p>Please provide your name and phone number so we can contact you about this opportunity.</p>
              </div>
            </div>
          </div>
        `);
      }

      // For generic links (with phone), generate a deterministic UUID from the phone
      // This allows multiple people using the same generic link to each have their own record
      let effectiveAgentId = agent_id;
      if (formPhone) {
        // Create a deterministic UUID from phone number using a simple hash
        const phoneClean = formPhone.replace(/\D/g, ''); // Remove non-digits
        const encoder = new TextEncoder();
        const data = encoder.encode(`generic-link-phone:${phoneClean}`);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = new Uint8Array(hashBuffer);
        // Convert first 16 bytes to UUID format
        const hex = Array.from(hashArray.slice(0, 16)).map(b => b.toString(16).padStart(2, '0')).join('');
        effectiveAgentId = `${hex.slice(0,8)}-${hex.slice(8,12)}-${hex.slice(12,16)}-${hex.slice(16,20)}-${hex.slice(20,32)}`;
        console.log(`📱 Generic link: Generated UUID ${effectiveAgentId} from phone ${formPhone}`);
      }

      // Check for existing interest using the effective agent ID
      const { data: existing } = await supabase
        .from("inside_track_interests")
        .select("id")
        .eq("job_id", job_id)
        .eq("agent_uuid", effectiveAgentId)
        .single();

      if (existing) {
        if (wantsJson) {
          return new Response(JSON.stringify({ success: true, already_registered: true, message: "Already registered" }), {
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          });
        }
        return renderPage("Already Registered", `
          <div class="card">
            <div class="header">
              <div class="badge">FREEWORLD PARTNER OPPORTUNITY</div>
              <h1>Already Registered</h1>
            </div>
            <div class="content" style="text-align: center;">
              <div class="success-icon">✅</div>
              <h2 class="job-title">You're Already On The List!</h2>
              <p class="description">
                You've already expressed interest in this position. Your Success Coach has been notified and will be in touch soon.
              </p>
            </div>
            <div class="footer">
              <p>FreeWorld Partner Opportunity</p>
            </div>
          </div>
        `);
      }

      // Determine agent info - form data takes priority (user entered it)
      const finalAgentName = formName || agent?.agent_name || agent_name;
      const finalAgentEmail = agent?.agent_email || null;
      const finalAgentPhone = formPhone || null;

      // Insert interest record (effectiveAgentId was computed earlier)
      const { error: insertError } = await supabase
        .from("inside_track_interests")
        .insert({
          job_id: job_id,
          agent_uuid: effectiveAgentId,
          agent_name: finalAgentName,
          agent_email: finalAgentEmail,
          agent_phone: finalAgentPhone,
          coach_username: job.success_coach,
          status: "new",
        });

      if (insertError) {
        console.error("Insert error:", insertError);
        throw new Error("Failed to record interest");
      }

      // Send email notification
      const agentDisplayName = finalAgentName || "Unknown Agent";
      const agentEmail = finalAgentEmail || "Not provided";
      const agentPhone = finalAgentPhone || "";
      const adminPortalUrl = agent?.admin_portal_url || "";
      // Capitalize coach name
      const rawCoachName = job.success_coach || "Unknown Coach";
      const coachName = rawCoachName.charAt(0).toUpperCase() + rawCoachName.slice(1);

      const portalUrl = "https://fwcareercoach.streamlit.app";

      const htmlBody = `<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px;">
<h2 style="color: #004751;">New Partner Job Interest</h2>
<div style="background: #f4f4f4; padding: 16px; border-radius: 8px; margin: 16px 0;">
<h3 style="margin: 0 0 8px 0; color: #191931;">Free Agent Details</h3>
<p style="margin: 4px 0;"><strong>Name:</strong> ${agentDisplayName}</p>
${agentEmail !== "Not provided" ? `<p style="margin: 4px 0;"><strong>Email:</strong> ${agentEmail}</p>` : ""}
${agentPhone ? `<p style="margin: 4px 0;"><strong>Phone:</strong> ${agentPhone}</p>` : ""}
<p style="margin: 4px 0;"><strong>Coach:</strong> ${coachName}</p>
${adminPortalUrl ? `<p style="margin: 4px 0;"><a href="${adminPortalUrl}" style="color: #004751; font-weight: bold;">View Agent Profile</a></p>` : ""}
</div>
<div style="background: #e8f5e9; padding: 16px; border-radius: 8px; margin: 16px 0;">
<h3 style="margin: 0 0 8px 0; color: #004751;">Job Details</h3>
<p style="margin: 4px 0;"><strong>Title:</strong> ${job.job_title}</p>
<p style="margin: 4px 0;"><strong>Company:</strong> ${job.company}</p>
<p style="margin: 4px 0;"><strong>Location:</strong> ${job.location}</p>
<p style="margin: 4px 0;"><strong>Market:</strong> ${job.market || "N/A"}</p>
</div>
<p style="color: #666; font-size: 14px;">
This Free Agent clicked EXPRESS INTEREST on a FreeWorld Partner job in their portal.
Please follow up with the agent and employer to facilitate the connection.
</p>
<p style="margin-top: 16px;">
<a href="${portalUrl}" style="color: #004751; font-weight: bold;">Open Coach Portal</a>
</p>
<hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
<p style="color: #999; font-size: 12px;">Sent automatically by Opptek Portal</p>
</body>
</html>`;

      const textBody = `New Partner Job Interest

Free Agent: ${agentDisplayName}
${agentEmail !== "Not provided" ? `Email: ${agentEmail}` : ""}
${agentPhone ? `Phone: ${agentPhone}` : ""}
Coach: ${coachName}
${adminPortalUrl ? `Agent Profile: ${adminPortalUrl}` : ""}

Job: ${job.job_title} at ${job.company}
Location: ${job.location}
Market: ${job.market || "N/A"}

Please follow up with the agent and employer.

Coach Portal: ${portalUrl}`;

      await sendEmailSmtp(
        "placement@freeworld.org",
        `New Partner Job Interest: ${agentDisplayName} - ${job.job_title}`,
        htmlBody,
        textBody
      );

      console.log(`✅ Interest recorded for ${agent?.agent_name || agent_name} → ${job.job_title}`);

      if (wantsJson) {
        return new Response(JSON.stringify({ success: true, message: "Interest registered" }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        });
      }

      return renderPage("Interest Registered", `
        <div class="card">
          <div class="header">
            <div class="badge">FREEWORLD PARTNER OPPORTUNITY</div>
            <h1>You're In!</h1>
          </div>
          <div class="content" style="text-align: center;">
            <div class="success-icon">🎉</div>
            <h2 class="job-title">Interest Registered!</h2>
            <p class="company">${job.job_title} at ${job.company}</p>
            <p class="description">
              Great news! Your Success Coach has been notified that you're interested in this partner opportunity.
              They'll reach out to you soon with next steps.
            </p>
            <p class="description" style="font-weight: 600; color: var(--fw-roots);">
              This is a FreeWorld partner job, which means we have a direct connection to help you get hired!
            </p>
          </div>
          <div class="footer">
            <p>Your coach will contact you shortly</p>
          </div>
        </div>
      `);

    } catch (err) {
      console.error("Error recording interest:", err);
      if (wantsJson) {
        return new Response(JSON.stringify({ success: false, error: "Failed to record interest" }), {
          status: 500,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        });
      }
      return renderPage("Error", `
        <div class="card">
          <div class="header">
            <div class="badge">FREEWORLD PARTNER OPPORTUNITY</div>
            <h1>Something Went Wrong</h1>
          </div>
          <div class="content">
            <div class="error">
              <p>We couldn't record your interest. Please try again or contact your Success Coach directly.</p>
            </div>
          </div>
        </div>
      `);
    }
  }

  // Handle GET - Show confirmation page
  const description = job.summary || job.job_description || "";
  const truncatedDesc = description.length > 300
    ? description.substring(0, 300) + "..."
    : description;

  const baseUrl = "https://yqbdltothngundojuebk.supabase.co/functions/v1/inside-track-interest";
  const formAction = `${baseUrl}?job_id=${job_id}&agent_id=${agent_id}&agent_name=${encodeURIComponent(agent_name)}`;

  // If agent doesn't have full profile, show form to collect name and phone
  if (!hasFullProfile) {
    return renderPage(`${job.job_title} - Partner Opportunity`, `
      <div class="card">
        <div class="header">
          <div class="badge">FREEWORLD PARTNER OPPORTUNITY</div>
          <h1>Exclusive Job Opportunity</h1>
        </div>
        <div class="content">
          <h2 class="job-title">${job.job_title}</h2>
          <p class="company">${job.company} • ${job.location}</p>

          <div class="details">
            ${job.route_type ? `<p><strong>Route Type:</strong> ${job.route_type}</p>` : ""}
            ${job.salary ? `<p><strong>Pay:</strong> ${job.salary}</p>` : ""}
            ${job.fair_chance === "fair_chance_employer" ? `<p><strong>✅ Fair Chance Employer</strong></p>` : ""}
          </div>

          <p class="description">${truncatedDesc}</p>

          <form method="POST" action="${formAction}">
            <div class="form-group">
              <label for="name">Your Name *</label>
              <input type="text" id="name" name="name" required placeholder="Enter your full name">
            </div>
            <div class="form-group">
              <label for="phone">Phone Number *</label>
              <input type="tel" id="phone" name="phone" required placeholder="(555) 123-4567">
              <p class="form-note">We'll use this to contact you about the opportunity</p>
            </div>
            <button type="submit" class="btn btn-primary">
              ✋ I'm Interested - Notify My Coach
            </button>
          </form>

          <p style="text-align: center; margin-top: 16px; font-size: 13px; color: #666;">
            Your Success Coach will be notified and will help you apply.
          </p>
        </div>
        <div class="footer">
          <p>FreeWorld Partner Jobs give you a direct connection to employers</p>
        </div>
      </div>
    `);
  }

  // Agent has full profile - show simple confirmation
  return renderPage(`${job.job_title} - Partner Opportunity`, `
    <div class="card">
      <div class="header">
        <div class="badge">FREEWORLD PARTNER OPPORTUNITY</div>
        <h1>Exclusive Job Opportunity</h1>
      </div>
      <div class="content">
        <h2 class="job-title">${job.job_title}</h2>
        <p class="company">${job.company} • ${job.location}</p>

        <div class="details">
          ${job.route_type ? `<p><strong>Route Type:</strong> ${job.route_type}</p>` : ""}
          ${job.salary ? `<p><strong>Pay:</strong> ${job.salary}</p>` : ""}
          ${job.fair_chance === "fair_chance_employer" ? `<p><strong>✅ Fair Chance Employer</strong></p>` : ""}
        </div>

        <p class="description">${truncatedDesc}</p>

        <form method="POST" action="${formAction}">
          <button type="submit" class="btn btn-primary">
            ✋ I'm Interested - Notify My Coach
          </button>
        </form>

        <p style="text-align: center; margin-top: 16px; font-size: 13px; color: #666;">
          By clicking above, your Success Coach will be notified and will help you apply.
        </p>
      </div>
      <div class="footer">
        <p>FreeWorld Partner Jobs give you a direct connection to employers</p>
      </div>
    </div>
  `);
});
