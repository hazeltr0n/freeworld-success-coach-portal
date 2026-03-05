# pdf/html_pdf_generator.py
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from typing import List, Dict
import datetime as _dt
import base64
import pandas as pd
import re
import html as _html
import os
import threading

# Rate limiting for empty portal notifications (avoid spam)
_empty_portal_notified = {}  # {agent_id: last_notified_timestamp}
_NOTIFICATION_COOLDOWN_HOURS = 24


def _send_email_smtp(to_email: str, subject: str, html_body: str, text_body: str = None):
    """Send email via Gmail SMTP with app password (simple, no OAuth)."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    gmail_address = os.getenv('GMAIL_ADDRESS')
    gmail_app_password = os.getenv('GMAIL_APP_PASSWORD')

    if not gmail_address or not gmail_app_password:
        print("📧 GMAIL_ADDRESS or GMAIL_APP_PASSWORD not set, skipping email")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = gmail_address
        msg['To'] = to_email
        msg['Subject'] = subject

        if text_body:
            msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_address, gmail_app_password)
            server.sendmail(gmail_address, to_email, msg.as_string())

        print(f"📧 Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"📧 SMTP error: {e}")
        return False


def _notify_empty_portal(agent_name: str, agent_id: str, location: str, filters: dict = None):
    """Send email notification when an agent sees empty portal (rate-limited)."""
    try:
        # Rate limit: only notify once per agent per 24 hours
        now = _dt.datetime.now()
        cache_key = agent_id or agent_name or "unknown"
        last_notified = _empty_portal_notified.get(cache_key)

        if last_notified:
            hours_since = (now - last_notified).total_seconds() / 3600
            if hours_since < _NOTIFICATION_COOLDOWN_HOURS:
                print(f"📧 Skipping empty portal notification for {agent_name} (notified {hours_since:.1f}h ago)")
                return

        # Get notification email (default to james@freeworld.org)
        notify_email = os.getenv('NOTIFICATION_EMAIL', 'james@freeworld.org')

        # Build filter description
        filter_desc = []
        if filters:
            route_filter = filters.get('route_type_filter') or filters.get('route_filter')
            if route_filter:
                # Handle both list and string formats
                if isinstance(route_filter, list):
                    filter_desc.append(f"Routes: {', '.join(route_filter)}")
                else:
                    filter_desc.append(f"Routes: {route_filter}")
            if filters.get('fair_chance_only'):
                filter_desc.append("Fair chance only")
            quality_filter = filters.get('match_quality_filter') or filters.get('match_level')
            if quality_filter:
                # Handle both list and string formats
                if isinstance(quality_filter, list):
                    filter_desc.append(f"Quality: {', '.join(quality_filter)}")
                else:
                    filter_desc.append(f"Quality: {quality_filter}")

        filter_summary = " | ".join(filter_desc) if filter_desc else "Default filters"

        # Send notification in background thread to not block rendering
        def send_async():
            try:
                subject = f"🔍 Empty Portal: {agent_name or 'Unknown Agent'}"

                html_body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #dc2626;">🔍 Agent Portal Showing No Jobs</h2>
                    <p><strong>Agent:</strong> {agent_name or 'Unknown'}</p>
                    <p><strong>Agent ID:</strong> {agent_id or 'N/A'}</p>
                    <p><strong>Location:</strong> {location or 'Unknown'}</p>
                    <p><strong>Filters:</strong> {filter_summary}</p>
                    <p><strong>Time:</strong> {now.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <hr>
                    <p style="color: #666;">Consider running a fresh Indeed search for this market/filter combination.</p>
                </body>
                </html>
                """

                text_body = f"""Empty Portal Alert

Agent: {agent_name or 'Unknown'}
Agent ID: {agent_id or 'N/A'}
Location: {location or 'Unknown'}
Filters: {filter_summary}
Time: {now.strftime('%Y-%m-%d %H:%M:%S')}

Consider running a fresh Indeed search for this market/filter combination.
"""

                _send_email_smtp(notify_email, subject, html_body, text_body)
                print(f"📧 Empty portal notification sent for {agent_name}")

            except Exception as e:
                print(f"📧 Failed to send empty portal notification: {e}")

        # Update rate limit cache
        _empty_portal_notified[cache_key] = now

        # Send in background
        thread = threading.Thread(target=send_async, daemon=True)
        thread.start()

    except Exception as e:
        print(f"📧 Error in empty portal notification: {e}")


def process_inside_track_interest_notifications():
    """
    Poll inside_track_interests table for status='new' and send email notifications.
    Called by scheduled jobs or manually. Updates status to 'notified' after sending.
    """
    try:
        from supabase_utils import get_supabase_client
        supabase = get_supabase_client()

        # Get all new interests that haven't been notified
        result = supabase.table('inside_track_interests').select(
            '*, jobs!inner(job_title, company, location, market)'
        ).eq('status', 'new').execute()

        if not result.data:
            print("📧 No new inside track interests to notify")
            return 0

        notify_email = 'placement@freeworld.org'
        notified_count = 0

        for interest in result.data:
            try:
                job = interest.get('jobs', {})
                agent_name = interest.get('agent_name') or 'Unknown Agent'
                agent_email = interest.get('agent_email') or 'Not provided'
                agent_phone = interest.get('agent_phone') or 'Not provided'
                coach_name = interest.get('coach_username') or 'Unknown Coach'

                subject = f"🎯 New Partner Job Interest: {agent_name} → {job.get('job_title', 'Unknown Job')}"

                html_body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px;">
                    <h2 style="color: #004751;">🎯 New Partner Job Interest</h2>

                    <div style="background: #f4f4f4; padding: 16px; border-radius: 8px; margin: 16px 0;">
                        <h3 style="margin: 0 0 8px 0; color: #191931;">Free Agent Details</h3>
                        <p style="margin: 4px 0;"><strong>Name:</strong> {agent_name}</p>
                        <p style="margin: 4px 0;"><strong>Email:</strong> {agent_email}</p>
                        <p style="margin: 4px 0;"><strong>Phone:</strong> {agent_phone}</p>
                        <p style="margin: 4px 0;"><strong>Coach:</strong> {coach_name}</p>
                    </div>

                    <div style="background: #e8f5e9; padding: 16px; border-radius: 8px; margin: 16px 0;">
                        <h3 style="margin: 0 0 8px 0; color: #004751;">Job Details</h3>
                        <p style="margin: 4px 0;"><strong>Title:</strong> {job.get('job_title', 'N/A')}</p>
                        <p style="margin: 4px 0;"><strong>Company:</strong> {job.get('company', 'N/A')}</p>
                        <p style="margin: 4px 0;"><strong>Location:</strong> {job.get('location', 'N/A')}</p>
                        <p style="margin: 4px 0;"><strong>Market:</strong> {job.get('market', 'N/A')}</p>
                    </div>

                    <p style="color: #666; font-size: 14px;">
                        This Free Agent clicked "EXPRESS INTEREST" on a FreeWorld Partner job in their portal.
                        Please follow up with the agent and employer to facilitate the connection.
                    </p>

                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    <p style="color: #999; font-size: 12px;">
                        Sent automatically by Opptek Portal
                    </p>
                </body>
                </html>
                """

                text_body = f"""New Partner Job Interest

Free Agent: {agent_name}
Email: {agent_email}
Phone: {agent_phone}
Coach: {coach_name}

Job: {job.get('job_title', 'N/A')} at {job.get('company', 'N/A')}
Location: {job.get('location', 'N/A')}
Market: {job.get('market', 'N/A')}

Please follow up with the agent and employer to facilitate the connection.
"""

                if _send_email_smtp(notify_email, subject, html_body, text_body):
                    # Update status to 'notified'
                    supabase.table('inside_track_interests').update({
                        'status': 'notified'
                    }).eq('id', interest['id']).execute()
                    notified_count += 1
                    print(f"📧 Notified placement team about {agent_name} → {job.get('job_title')}")

            except Exception as e:
                print(f"📧 Error processing interest {interest.get('id')}: {e}")

        print(f"📧 Processed {notified_count} inside track interest notifications")
        return notified_count

    except Exception as e:
        print(f"📧 Error in inside track notifications: {e}")
        return 0


BASE = Path(__file__).resolve().parents[1]
TEMPLATES = BASE / "templates"
STATIC = BASE / "static"
ASSETS = BASE / "assets"
OUTFIT_FONT_DIR = BASE / "Outfit" / "static"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES)),
    autoescape=select_autoescape()
)

def _encode_asset_base64(path: Path) -> str:
    """Reads an asset file and returns its base64 encoded string."""
    if not path.exists():
        return ""
    try:
        mime_types = {
            ".jpg": "image/jpeg",
            ".png": "image/png",
            ".ttf": "font/truetype",
        }
        mime = mime_types.get(path.suffix, "")
        if not mime:
            return ""
        
        with open(path, "rb") as asset_file:
            encoded_string = base64.b64encode(asset_file.read()).decode("utf-8")
        return f"data:{mime};base64,{encoded_string}"
    except Exception:
        return ""

def jobs_dataframe_to_dicts(df, candidate_id: str = None, agent_name: str = None) -> List[Dict]:
    def _sanitize_html(val: str) -> str:
        try:
            s = _html.unescape(str(val or ''))
            # remove scripts/styles (with content)
            s = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', '', s)
            # CRITICAL: Remove ANY script/style tags - complete or incomplete (truncated)
            # Match <script...> OR <script... (without closing >) to end of string
            s = re.sub(r'(?i)<script[^>]*>?.*', '', s)
            s = re.sub(r'(?i)</script>', '', s)
            s = re.sub(r'(?i)<style[^>]*>?.*', '', s)
            s = re.sub(r'(?i)</style>', '', s)
            # convert block/line breaks
            s = re.sub(r'(?i)</p\s*>', '\n\n', s)
            s = re.sub(r'(?i)<br\s*/?>', '\n', s)
            s = re.sub(r'(?i)<li\b[^>]*>', '• ', s)
            s = re.sub(r'(?i)</li\s*>', '\n', s)
            # drop remaining tags
            s = re.sub(r'<[^>]+>', '', s)
            # collapse and convert to HTML
            s = re.sub(r'\n{3,}', '\n\n', s).strip()
            return s.replace('\n', '<br>')
        except Exception:
            return str(val or '')
    def _truncate_text(text: str, max_len: int = 300) -> str:
        try:
            s = (text or '').strip()
            if len(s) <= max_len:
                return s
            return s[: max_len - 1].rstrip() + '…'
        except Exception:
            return text or ''
    def _clean_text(val: any) -> str:
        try:
            if pd.isna(val):
                return ''
        except Exception:
            pass
        s = str(val) if val is not None else ''
        return '' if s.strip().lower() in ('nan', 'none', 'null') else s

    def _format_salary(val: any) -> str:
        # Prefer pre-formatted salary string
        txt = _clean_text(val)
        if not txt:
            return ''
        # If looks like a dict string, try to parse and render terse display
        if txt.startswith('{') and txt.endswith('}'):
            try:
                import ast
                d = ast.literal_eval(txt)
                # Support { 'baseSalary': {'unitOfWork': 'HOUR', 'range': {'min': x, 'max': y}}, 'currencyCode': 'USD' }
                base = d.get('baseSalary', {}) if isinstance(d, dict) else {}
                rng = base.get('range', {}) if isinstance(base, dict) else {}
                unit_raw = base.get('unitOfWork') or ''
                unit = str(unit_raw).lower() if unit_raw else ''
                cur = d.get('currencyCode', 'USD')
                if rng:
                    mn = rng.get('min') or rng.get('minimum')
                    mx = rng.get('max') or rng.get('maximum')
                    parts = []
                    if mn and mx:
                        parts.append(f"{cur} {mn}-{mx}")
                    elif mn:
                        parts.append(f"{cur} {mn}")
                    elif mx:
                        parts.append(f"{cur} {mx}")
                    if unit:
                        parts.append(f"per {unit}")
                    return ' '.join(parts)
            except Exception:
                pass
        return txt

    # Use unified sorting to match FPDF exactly
    try:
        from job_sorting_utils import apply_unified_sorting
        df_sorted = apply_unified_sorting(df)
    except Exception as e:
        # Fallback to original DataFrame if sorting fails
        print(f"⚠️ Unified sorting failed: {e}, using original order")
        df_sorted = df.copy()

    rows = []
    for _, r in df_sorted.iterrows():
        # Use .get() to avoid errors if a column is missing
        # Provide fallbacks for robustness
        title = _clean_text(r.get('source.title') or r.get('norm.title') or 'CDL Driver Position')
        company = _clean_text(r.get('source.company') or r.get('norm.company') or 'Trucking Company')
        city = _clean_text(r.get('norm.city', ''))
        state = _clean_text(r.get('norm.state', ''))
        location_fallback = _clean_text(r.get('norm.location') or r.get('source.location_raw') or '')
        route_type = r.get('ai.route_type', 'Unknown')
        ai_match_raw = r.get('ai.match', 'good')
        ai_match = str(ai_match_raw).lower() if ai_match_raw is not None else 'good'
        fair_raw = r.get('ai.fair_chance', False)
        # Normalize fair chance to a boolean
        fair_chance = False
        if isinstance(fair_raw, bool):
            fair_chance = fair_raw
        else:
            fair_str = str(fair_raw) if fair_raw is not None else ''
            fair_chance = fair_str.lower().find('fair_chance_employer') >= 0 or fair_str.lower() in ('true', 'yes', '1')
        # Build both summary and full description for responsive display
        description_summary = _sanitize_html(r.get('ai.summary') or 'Great opportunity for CDL drivers.')
        description_full = _sanitize_html(r.get('source.description') or r.get('job_description') or r.get('norm.description') or 'Great opportunity for CDL drivers.')
        # Use ai.summary as primary description, fallback to truncated full description if needed
        if not description_summary or description_summary == 'Great opportunity for CDL drivers.':
            description_summary = _truncate_text(description_full, 320)
        # Keep description_full as the complete, untruncated description
        # salary = _format_salary(r.get('norm.salary_display', ''))  # Removed per request

        # Logic for apply URL with proper fallback chain
        # Try tracking URL first, then fall back to source URL (canonical schema)
        tracked = _clean_text(r.get('meta.tracked_url', ''))
        source_url = _clean_text(r.get('source.url', ''))
        clean_url = _clean_text(r.get('clean_apply_url', ''))
        apply_instructions = _clean_text(r.get('apply_instructions', ''))

        # Use full job_id for database matching (not truncated)
        job_id = r.get('id.job', 'unknown')
        job_id_display = job_id[:8] if job_id != 'unknown' else 'unknown'
        print(f"🔍 HTML Job {job_id_display}: tracked='{tracked}', source='{source_url[:60]}...', clean='{clean_url[:60] if clean_url else 'None'}...'")

        # Check if this is an inside track (partner) job
        source = str(r.get('source', r.get('id.source', ''))).lower()
        is_inside_track = source == 'inside_track'
        inside_track_type = str(r.get('inside_track_type', 'inside_track')).lower()
        is_partner_opportunity = is_inside_track and inside_track_type == 'partner_opportunity'

        # Debug: Log partner opportunity detection
        if is_partner_opportunity:
            print(f"🤝 PARTNER DEBUG {job_id_display}: is_partner={is_partner_opportunity}, candidate_id='{candidate_id}', agent_name='{agent_name}'")

        # For partner opportunity jobs, use the interest form URL and hide company
        if is_partner_opportunity and candidate_id:
            from inside_track_manager import generate_interest_url
            apply_url = generate_interest_url(job_id, candidate_id, agent_name or '')
            display_link = "Express Interest"  # Special display text
            company = "FreeWorld Partner Opportunity"  # Hide real company name
            print(f"🤝 Partner Opportunity {job_id_display}: using interest form, hiding company")
        elif is_partner_opportunity and not candidate_id:
            # Partner opportunity but no candidate_id - cannot generate interest URL
            print(f"⚠️ PARTNER WARNING {job_id_display}: No candidate_id provided! Cannot generate interest URL.")
            apply_url = ""  # Will show "Apply link unavailable" - this is expected without candidate_id
            display_link = ""
            company = "FreeWorld Partner Opportunity"
        elif is_inside_track:
            # Regular inside track - use direct link if available, otherwise rely on apply_instructions
            # Only use clean_url if it's actually a URL (not phone/address instructions)
            original_url = source_url
            if not original_url and clean_url and clean_url.startswith(('http://', 'https://')):
                original_url = clean_url
            apply_url = original_url
            if original_url:
                display_url = original_url.replace('https://', '').replace('http://', '').replace('www.', '')
                if len(display_url) > 35:
                    display_url = display_url[:32] + '...'
                display_link = display_url
                print(f"📋 Inside Track Job {job_id_display}: using direct link")
            else:
                display_link = ''
                print(f"📋 Inside Track Job {job_id_display}: no URL, will use apply_instructions")
        else:
            # Use original job URL for display and tracking (skip Short.io tracked URLs)
            original_url = source_url or clean_url
            apply_url = original_url  # Always use original URL, not Short.io

            # Display truncated original URL so user knows where they're going
            # (e.g., "indeed.com/viewjob/jk=abc123..." instead of short.io link)
            if original_url:
                # Remove protocol and truncate to ~35 chars
                display_url = original_url.replace('https://', '').replace('http://', '').replace('www.', '')
                if len(display_url) > 35:
                    display_url = display_url[:32] + '...'
                display_link = display_url
            else:
                display_link = ''

        # Generate edge function URL for click tracking in PDFs
        # SKIP for partner opportunities - their URL goes directly to inside-track-interest edge function
        # which needs POST requests (click-redirect-lite only handles GET)
        tracking_url = apply_url  # Default to same as apply_url
        if apply_url and candidate_id and not is_partner_opportunity:
            try:
                from link_tracker import LinkTracker
                tracker = LinkTracker()

                # Extract metadata for tracking
                job_match = r.get('ai.match', 'unknown')
                job_route = r.get('ai.route_type', 'unknown')
                job_fair = 'true' if r.get('ai.fair_chance') else 'false'

                tags = [
                    f"candidate:{candidate_id}",
                    f"job_id:{job_id}",
                    f"match:{job_match}",
                    f"route:{job_route}",
                    f"fair:{job_fair}",
                    "type:job_application"
                ]

                # Generate edge function URL for tracking
                tracking_url = tracker.generate_edge_function_url(
                    target_url=apply_url,
                    candidate_id=candidate_id,
                    tags=tags
                )
                print(f"🔍 PDF Job {job_id}: Generated tracking URL for {apply_url[:50]}...")
            except Exception as e:
                print(f"⚠️ Failed to generate tracking URL for job {job_id}: {e}")
                tracking_url = apply_url

        # Logic for match badge and career pathway badges
        match_badge = ''
        career_pathway_badge = ''

        # Standard CDL match badges
        if ai_match == 'good':
            match_badge = 'Excellent Match'
        elif ai_match == 'so-so':
            match_badge = 'Possible Fit'

        # Career pathway badges (no emojis, same style as existing badges)
        career_pathway = r.get('ai.career_pathway', '')
        training_provided = r.get('ai.training_provided', False)

        if career_pathway and career_pathway != 'no_pathway':
            pathway_badge_map = {
                'dock_to_driver': 'Dock to Driver',
                'internal_cdl_training': 'CDL Training',
                'warehouse_to_driver': 'Warehouse to Driver',
                'logistics_progression': 'Logistics Career',
                'non_cdl_driving': 'Non-CDL Driving',
                'general_warehouse': 'Warehouse Work',
                'construction_apprentice': 'Construction Apprentice',
                'stepping_stone': 'Career Step'
            }
            career_pathway_badge = pathway_badge_map.get(career_pathway, '')

        # Add training badge if training is provided
        if training_provided and not career_pathway_badge:
            career_pathway_badge = 'Training Provided'

        rows.append({
            "title": title,
            "company": company,
            "city": city,
            "state": state,
            "location": location_fallback,
            "route_type": route_type,
            "match_badge": match_badge,
            "career_pathway_badge": career_pathway_badge,
            "fair_chance": bool(fair_chance),
            "is_inside_track": is_inside_track,  # Inside track job flag
            "is_partner_opportunity": is_partner_opportunity,  # Partner opportunity (anonymous) flag
            # Backwards compatibility key 'description' holds the summary
            "description": description_summary,
            "description_summary": description_summary,
            "description_full": description_full,
            "apply_url": tracking_url,  # Use tracking URL for actual clicks
            "apply_instructions": apply_instructions,  # Phone/address for jobs without URL
            "display_link": display_link,  # Keep Short.io link for display
            # Fields needed for feedback system (job_id for template, candidate_id for fallback)
            "job_id": job_id,
            "candidate_id": candidate_id or 'unknown',
            # "salary": salary,  # Removed per request
        })
    return rows

def render_jobs_html(jobs: List[Dict], agent_params=None, *, fragment: bool = False) -> str:
    """Renders the full report with header + multiple .page job cards."""
    agent_params = agent_params or {}
    location = agent_params.get("location") or "Unknown"
    
    # CRITICAL FIX: Ensure show_prepared_for is always a boolean for template processing
    if 'show_prepared_for' in agent_params:
        show_prepared_for = agent_params['show_prepared_for']
        if isinstance(show_prepared_for, str):
            agent_params['show_prepared_for'] = show_prepared_for.lower() not in ('false', '0', 'f', 'no', '')
        else:
            agent_params['show_prepared_for'] = bool(show_prepared_for)
    
    # Helpers: extract a clean first name from various formats
    def _first_name(raw: str, *, fallback: str) -> str:
        try:
            s = str(raw or "").strip()
            if not s:
                return fallback
            # Strip email domain if present
            s = s.split("@", 1)[0]
            # Normalize common separators (first.last, first_last, first-last)
            import re as _re
            s_norm = _re.sub(r"[._-]+", " ", s)
            words = s_norm.split()
            
            if not words:
                return fallback
            
            # Special handling: if first word is "Coach", take the second word as the name
            if len(words) >= 2 and words[0].lower() == "coach":
                first = words[1]
            else:
                first = words[0]
            
            # Title case but preserve all-caps abbreviations reasonably
            return first.title()
        except Exception:
            return fallback

    # Title page names: prefer explicit names; gracefully handle usernames like first.last
    # Only use fallbacks for _first_name processing, not for template logic
    raw_agent = agent_params.get("agent_name") or agent_params.get("name")
    raw_coach = agent_params.get("coach_name") or agent_params.get("coach_username")
    candidate_id = agent_params.get("agent_uuid") or agent_params.get("candidate_id") or ""

    # Check if agent has full profile (admin_portal_url) by querying database
    has_full_profile = False
    if candidate_id:
        try:
            from supabase_utils import get_client
            client = get_client()
            if client:
                result = client.table('agent_profiles').select('admin_portal_url').eq('agent_uuid', candidate_id).single().execute()
                has_full_profile = bool(result.data and result.data.get('admin_portal_url'))
        except Exception as e:
            print(f"⚠️ Could not check agent profile: {e}")
    
    # Only pass names to template if they were actually provided (not fallbacks)
    agent_first = _first_name(raw_agent, fallback="Free Agent") if raw_agent else None
    coach_first = _first_name(raw_coach, fallback="Coach") if raw_coach else None
    generated_on = _dt.datetime.now().strftime("%B %d, %Y")
    total = len(jobs)

    # Encode all assets to be embedded in the HTML
    # Load assets with fallbacks
    # Helper to pick the first available asset from candidates
    def _first_icon(*paths):
        for p in paths:
            enc = _encode_asset_base64(p)
            if enc:
                return enc
        return ""

    wordmark = _encode_asset_base64(ASSETS / "FW-Wordmark-Roots@3x.png")
    # Prefer a small, round/square icon; fall back to wordmark only if none found
    icon = _first_icon(
        ASSETS / "FW-Logo-Roots@2x.png",
        ASSETS / "fw_logo.png",
        BASE / "data" / "FW-Logo-Roots@2x.png",
        BASE / "data" / "fw_logo.png",
    ) or wordmark
    assets = {
        "font_regular": _encode_asset_base64(OUTFIT_FONT_DIR / "Outfit-Regular.ttf"),
        "font_bold": _encode_asset_base64(OUTFIT_FONT_DIR / "Outfit-Bold.ttf"),
        "bg_image": _encode_asset_base64(ASSETS / "highway_background.jpg"),
        "wordmark_logo": wordmark,
        "icon_logo": icon,
    }

    # Optionally hide job cards entirely via env flag (for quick QA/lockdown)
    if os.getenv('FREEWORLD_PORTAL_HIDE_JOBS', '0') == '1':
        jobs = []

    # Send notification if agent portal is showing no jobs
    if not jobs and raw_agent:
        _notify_empty_portal(
            agent_name=raw_agent,
            agent_id=candidate_id,
            location=location,
            filters=agent_params
        )

    # IMPORTANT: Do not generate or infer links here.
    # The Free Agent portal must only show the canonical tracked link provided by the pipeline.
    # If a job does not have meta.tracked_url, we intentionally leave the link blank.

    tmpl = env.get_template("report.html")
    try:
        html = tmpl.render(
            location=location,
            generated_on=generated_on,
            total_jobs=total,
            jobs=jobs,
            assets=assets,
            agent_name=agent_first,
            coach_name=coach_first,
            candidate_id=candidate_id,
            agent_params=agent_params,
            has_full_profile=has_full_profile,
        )
    except Exception as e:
        print(f"Error rendering report.html template: {e}")
        return f"<h1>Error rendering report</h1><p>{e}</p>"

    if not fragment:
        return html

    # Extract CSS from <style> tags
    style_match = re.search(r"<style>(.*?)</style>", html, flags=re.DOTALL|re.IGNORECASE)
    css_content = style_match.group(1).strip() if style_match else ""

    # Extract JavaScript from <script> tags
    script_matches = re.findall(r"<script[^>]*>(.*?)</script>", html, flags=re.DOTALL|re.IGNORECASE)
    js_content = "\n".join(match.strip() for match in script_matches if match.strip())

    # Return only what's inside <body>...</body> for portal injection
    body_match = re.search(r"<body[^>]*>(.*)</body>", html, flags=re.DOTALL|re.IGNORECASE)
    body_content = body_match.group(1).strip() if body_match else html

    # CRITICAL: Remove script tags from body content since we extract them separately
    # This prevents duplicate scripts and avoids issues if job descriptions contain </script>
    body_content = re.sub(r"<script[^>]*>.*?</script>", "", body_content, flags=re.DOTALL|re.IGNORECASE)

    # Build a complete HTML document for the iframe srcdoc
    # This ensures proper parsing and JavaScript execution
    result = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
"""
    result += css_content
    result += """
</style>
</head>
<body>
"""
    result += body_content
    if js_content:
        result += f"\n<script>\n{js_content}\n</script>"
    result += """
</body>
</html>"""
    return result


def export_pdf_playwright(html: str, output_path: str):
    from playwright.sync_api import sync_playwright
    from pathlib import Path
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "report.html"
        p.write_text(html, encoding="utf-8")
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.goto(p.as_uri(), wait_until="networkidle")
            page.pdf(
                path=output_path,
                format="Letter",
                print_background=True,
                margin={"top":"0","right":"0","bottom":"0","left":"0"}
            )
            browser.close()

def export_pdf_weasyprint(html: str, output_path: str):
    """Export PDF using Playwright (renamed for compatibility)"""
    export_pdf_playwright(html, output_path)
