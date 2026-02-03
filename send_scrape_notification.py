#!/usr/bin/env python3
"""
Send email notifications for completed scrapes via Gmail SMTP
"""

import os
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(to_email: str, subject: str, body_html: str, body_text: str = None):
    """Send email via Gmail SMTP with app password"""

    # Get credentials from environment
    gmail_address = os.getenv('GMAIL_ADDRESS')
    gmail_app_password = os.getenv('GMAIL_APP_PASSWORD')

    if not gmail_address or not gmail_app_password:
        print("❌ GMAIL_ADDRESS or GMAIL_APP_PASSWORD not set")
        return False

    try:
        # Create message
        message = MIMEMultipart('alternative')
        message['From'] = gmail_address
        message['To'] = to_email
        message['Subject'] = subject

        # Add text version
        if body_text:
            text_part = MIMEText(body_text, 'plain')
            message.attach(text_part)

        # Add HTML version
        html_part = MIMEText(body_html, 'html')
        message.attach(html_part)

        # Send via SMTP
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_address, gmail_app_password)
            server.sendmail(gmail_address, to_email, message.as_string())

        print(f"✅ Email sent successfully to {to_email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        import traceback
        traceback.print_exc()
        return False


def format_scrape_notification(scrape_type: str, results: dict):
    """Format scrape completion notification email"""

    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

    # Extract summary stats
    total_jobs = results.get('total_jobs', 0)
    quality_jobs = results.get('quality_jobs', 0)
    scrapes_run = results.get('scrapes_run', 0)

    # Get breakdown by source
    indeed_results = results.get('indeed_results', {})
    driverpulse_results = results.get('driverpulse_results', {})
    google_results = results.get('google_results', {})

    # Build source breakdown HTML
    source_breakdown_html = ""
    source_breakdown_text = ""

    if indeed_results:
        ind_total = indeed_results.get('total_jobs', 0)
        ind_quality = indeed_results.get('quality_jobs', 0)
        ind_scrapes = indeed_results.get('scrapes_run', 0)
        source_breakdown_html += f"""
                <div class="stats">
                    <h3>📋 Indeed Scrapes</h3>
                    <ul>
                        <li><strong>Searches:</strong> {ind_scrapes} (across all markets)</li>
                        <li><strong>Total Jobs:</strong> {ind_total:,}</li>
                        <li><strong>Quality Jobs:</strong> {ind_quality:,}</li>
                        <li><strong>Quality Rate:</strong> {(ind_quality/ind_total*100) if ind_total > 0 else 0:.1f}%</li>
                    </ul>
                </div>
        """
        source_breakdown_text += f"""
    Indeed Scrapes:
    - Searches: {ind_scrapes} (across all markets)
    - Total Jobs: {ind_total:,}
    - Quality Jobs: {ind_quality:,}
    - Quality Rate: {(ind_quality/ind_total*100) if ind_total > 0 else 0:.1f}%
    """

    if driverpulse_results:
        dp_total = driverpulse_results.get('total_jobs', 0)
        dp_quality = driverpulse_results.get('quality_jobs', 0)
        dp_scrapes = driverpulse_results.get('scrapes_run', 0)
        source_breakdown_html += f"""
                <div class="stats">
                    <h3>🚛 DriverPulse Scrapes</h3>
                    <ul>
                        <li><strong>Searches:</strong> {dp_scrapes}</li>
                        <li><strong>Total Jobs:</strong> {dp_total:,}</li>
                        <li><strong>Quality Jobs:</strong> {dp_quality:,}</li>
                        <li><strong>Quality Rate:</strong> {(dp_quality/dp_total*100) if dp_total > 0 else 0:.1f}%</li>
                    </ul>
                </div>
        """
        source_breakdown_text += f"""
    DriverPulse Scrapes:
    - Searches: {dp_scrapes}
    - Total Jobs: {dp_total:,}
    - Quality Jobs: {dp_quality:,}
    - Quality Rate: {(dp_quality/dp_total*100) if dp_total > 0 else 0:.1f}%
    """

    if google_results:
        g_total = google_results.get('total_jobs', 0)
        g_quality = google_results.get('quality_jobs', 0)
        g_queries = google_results.get('queries_submitted', 0)
        source_breakdown_html += f"""
                <div class="stats">
                    <h3>🌐 Google Scrapes</h3>
                    <ul>
                        <li><strong>Queries Submitted:</strong> {g_queries}</li>
                        <li><strong>Status:</strong> Submitted to Outscraper</li>
                        <li><strong>Expected Jobs:</strong> ~{g_queries * 50:,}</li>
                    </ul>
                    <p><em>Results will be processed by poller in 30-120 minutes</em></p>
                </div>
        """
        source_breakdown_text += f"""
    Google Scrapes:
    - Queries Submitted: {g_queries}
    - Status: Submitted to Outscraper
    - Expected Jobs: ~{g_queries * 50:,}
    (Results will be processed by poller in 30-120 minutes)
    """

    # Build HTML body
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px; }}
            .content {{ background-color: #f9f9f9; padding: 20px; margin-top: 20px; border-radius: 5px; }}
            .stats {{ background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #4CAF50; }}
            .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>🎯 {scrape_type} Scrape Complete</h2>
            </div>

            <div class="content">
                <p><strong>Completion Time:</strong> {timestamp}</p>

                <div class="stats">
                    <h3>📊 Overall Summary</h3>
                    <ul>
                        <li><strong>Total Scrapes:</strong> {scrapes_run}</li>
                        <li><strong>Total Jobs Processed:</strong> {total_jobs:,}</li>
                        <li><strong>Quality Jobs (Good/So-So):</strong> {quality_jobs:,}</li>
                        <li><strong>Overall Quality Rate:</strong> {(quality_jobs/total_jobs*100) if total_jobs > 0 else 0:.1f}%</li>
                    </ul>
                </div>

                {source_breakdown_html}

                <p>All completed jobs have been uploaded to Supabase and are available in the agent portal.</p>
            </div>

            <div class="footer">
                <p>Generated automatically by Opptek Scheduled Scraper</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Build text version
    text_body = f"""
    {scrape_type} Scrape Complete

    Completion Time: {timestamp}

    Overall Summary:
    - Total Scrapes: {scrapes_run}
    - Total Jobs Processed: {total_jobs:,}
    - Quality Jobs (Good/So-So): {quality_jobs:,}
    - Overall Quality Rate: {(quality_jobs/total_jobs*100) if total_jobs > 0 else 0:.1f}%

    {source_breakdown_text}

    All completed jobs have been uploaded to Supabase and are available in the agent portal.

    ---
    Generated automatically by Opptek Scheduled Scraper
    """

    return html_body, text_body


def send_scrape_completion_notification(scrape_type: str, results: dict, recipient_email: str):
    """Send scrape completion notification"""

    # Format email content
    html_body, text_body = format_scrape_notification(scrape_type, results)

    # Create subject line
    subject = f"✅ {scrape_type} Scrape Complete - {results.get('quality_jobs', 0):,} Quality Jobs"

    # Send email
    return send_email(recipient_email, subject, html_body, text_body)


def format_detailed_scrape_report(scrape_type: str, results: dict):
    """Format detailed scrape report with quality, route, and fair chance breakdowns"""

    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

    # Extract summary stats
    total_jobs = results.get('total_jobs', 0)
    quality_jobs = results.get('quality_jobs', 0)

    # Quality breakdown
    ai_good = results.get('ai_good', 0)
    ai_so_so = results.get('ai_so_so', 0)
    ai_bad = results.get('ai_bad', 0)

    # Route breakdown
    local_routes = results.get('local_routes', 0)
    regional_routes = results.get('regional_routes', 0)
    otr_routes = results.get('otr_routes', 0)
    unknown_routes = results.get('unknown_routes', 0)

    # Fair chance breakdown
    fair_chance_employer = results.get('fair_chance_employer', 0)
    background_check_required = results.get('background_check_required', 0)
    clean_record_required = results.get('clean_record_required', 0)
    no_requirements_mentioned = results.get('no_requirements_mentioned', 0)

    # Source info
    source_name = results.get('source_name', scrape_type)
    markets_searched = results.get('markets_searched', [])
    search_terms = results.get('search_terms', [])

    # Calculate percentages
    quality_pct = (quality_jobs / total_jobs * 100) if total_jobs > 0 else 0
    good_pct = (ai_good / total_jobs * 100) if total_jobs > 0 else 0
    so_so_pct = (ai_so_so / total_jobs * 100) if total_jobs > 0 else 0
    bad_pct = (ai_bad / total_jobs * 100) if total_jobs > 0 else 0

    # Fair chance percentage (of quality jobs)
    fc_employer_pct = (fair_chance_employer / quality_jobs * 100) if quality_jobs > 0 else 0

    # Build HTML body
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 650px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #4CAF50, #2E7D32); color: white; padding: 25px; text-align: center; border-radius: 8px; }}
            .header h2 {{ margin: 0; font-size: 24px; }}
            .content {{ background-color: #f9f9f9; padding: 25px; margin-top: 20px; border-radius: 8px; }}
            .stats {{ background-color: white; padding: 18px; margin: 15px 0; border-left: 4px solid #4CAF50; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            .stats h3 {{ margin-top: 0; color: #2E7D32; font-size: 16px; }}
            .stats ul {{ margin: 10px 0 0 0; padding-left: 20px; }}
            .stats li {{ margin: 6px 0; }}
            .breakdown-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-top: 15px; }}
            .breakdown-item {{ background: #f5f5f5; padding: 12px; border-radius: 6px; text-align: center; }}
            .breakdown-item .value {{ font-size: 24px; font-weight: bold; color: #2E7D32; }}
            .breakdown-item .label {{ font-size: 12px; color: #666; margin-top: 4px; }}
            .good {{ color: #4CAF50; }}
            .so-so {{ color: #FF9800; }}
            .bad {{ color: #f44336; }}
            .fair-chance {{ color: #2196F3; }}
            .highlight {{ background-color: #E8F5E9; padding: 15px; border-radius: 6px; margin: 15px 0; }}
            .footer {{ margin-top: 25px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; text-align: center; }}
            table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; }}
            th {{ background-color: #f5f5f5; font-weight: 600; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>📊 {scrape_type} Scrape Report</h2>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">{timestamp}</p>
            </div>

            <div class="content">
                <!-- Summary Highlight -->
                <div class="highlight">
                    <strong>🎯 Summary:</strong> Found <strong>{total_jobs:,}</strong> total jobs,
                    <strong class="good">{quality_jobs:,}</strong> quality jobs ({quality_pct:.1f}%)
                </div>

                <!-- Quality Breakdown -->
                <div class="stats">
                    <h3>📈 Quality Breakdown</h3>
                    <table>
                        <tr>
                            <th>Rating</th>
                            <th>Count</th>
                            <th>Percentage</th>
                        </tr>
                        <tr>
                            <td><span class="good">✅ Good</span></td>
                            <td><strong>{ai_good:,}</strong></td>
                            <td>{good_pct:.1f}%</td>
                        </tr>
                        <tr>
                            <td><span class="so-so">⚡ So-So</span></td>
                            <td><strong>{ai_so_so:,}</strong></td>
                            <td>{so_so_pct:.1f}%</td>
                        </tr>
                        <tr>
                            <td><span class="bad">❌ Bad</span></td>
                            <td><strong>{ai_bad:,}</strong></td>
                            <td>{bad_pct:.1f}%</td>
                        </tr>
                    </table>
                </div>

                <!-- Route Breakdown -->
                <div class="stats">
                    <h3>🛣️ Route Type Breakdown</h3>
                    <p style="font-size: 12px; color: #666; margin-top: 0;">(Quality jobs only)</p>
                    <table>
                        <tr>
                            <th>Route Type</th>
                            <th>Count</th>
                        </tr>
                        <tr>
                            <td>🏠 Local</td>
                            <td><strong>{local_routes:,}</strong></td>
                        </tr>
                        <tr>
                            <td>📍 Regional</td>
                            <td><strong>{regional_routes:,}</strong></td>
                        </tr>
                        <tr>
                            <td>🚛 OTR (Over The Road)</td>
                            <td><strong>{otr_routes:,}</strong></td>
                        </tr>
                        <tr>
                            <td>❓ Unknown</td>
                            <td><strong>{unknown_routes:,}</strong></td>
                        </tr>
                    </table>
                </div>

                <!-- Fair Chance Breakdown -->
                <div class="stats">
                    <h3>🤝 Fair Chance Breakdown</h3>
                    <p style="font-size: 12px; color: #666; margin-top: 0;">(Quality jobs only)</p>
                    <table>
                        <tr>
                            <th>Status</th>
                            <th>Count</th>
                        </tr>
                        <tr>
                            <td><span class="fair-chance">✅ Fair Chance Employer</span></td>
                            <td><strong>{fair_chance_employer:,}</strong> ({fc_employer_pct:.1f}%)</td>
                        </tr>
                        <tr>
                            <td>⚠️ Background Check Required</td>
                            <td><strong>{background_check_required:,}</strong></td>
                        </tr>
                        <tr>
                            <td>🚫 Clean Record Required</td>
                            <td><strong>{clean_record_required:,}</strong></td>
                        </tr>
                        <tr>
                            <td>❓ No Requirements Mentioned</td>
                            <td><strong>{no_requirements_mentioned:,}</strong></td>
                        </tr>
                    </table>
                </div>

                <!-- Search Details -->
                <div class="stats">
                    <h3>🔍 Search Configuration</h3>
                    <ul>
                        <li><strong>Source:</strong> {source_name}</li>
                        <li><strong>Markets:</strong> {', '.join(markets_searched) if markets_searched else 'N/A'}</li>
                        <li><strong>Search Terms:</strong> {', '.join(search_terms) if search_terms else 'N/A'}</li>
                    </ul>
                </div>

                <p style="margin-top: 20px;">All quality jobs have been uploaded to Supabase and are available in the agent portal.</p>
            </div>

            <div class="footer">
                <p>🤖 Generated automatically by Opptek Scheduled Scraper</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Build text version
    text_body = f"""
{scrape_type} SCRAPE REPORT
{'='*50}
Completion Time: {timestamp}

SUMMARY
-------
Total Jobs: {total_jobs:,}
Quality Jobs: {quality_jobs:,} ({quality_pct:.1f}%)

QUALITY BREAKDOWN
-----------------
Good:   {ai_good:,} ({good_pct:.1f}%)
So-So:  {ai_so_so:,} ({so_so_pct:.1f}%)
Bad:    {ai_bad:,} ({bad_pct:.1f}%)

ROUTE TYPE BREAKDOWN (Quality Jobs)
-----------------------------------
Local:    {local_routes:,}
Regional: {regional_routes:,}
OTR:      {otr_routes:,}
Unknown:  {unknown_routes:,}

FAIR CHANCE BREAKDOWN (Quality Jobs)
------------------------------------
Fair Chance Employer:      {fair_chance_employer:,} ({fc_employer_pct:.1f}%)
Background Check Required: {background_check_required:,}
Clean Record Required:     {clean_record_required:,}
No Requirements Mentioned: {no_requirements_mentioned:,}

SEARCH CONFIGURATION
--------------------
Source: {source_name}
Markets: {', '.join(markets_searched) if markets_searched else 'N/A'}
Search Terms: {', '.join(search_terms) if search_terms else 'N/A'}

All quality jobs have been uploaded to Supabase and are available in the agent portal.

---
Generated automatically by Opptek Scheduled Scraper
    """

    return html_body, text_body


def send_detailed_scrape_report(scrape_type: str, results: dict, recipient_email: str):
    """Send detailed scrape report with quality, route, and fair chance breakdowns"""

    # Format email content
    html_body, text_body = format_detailed_scrape_report(scrape_type, results)

    # Create subject line with key metrics
    total_jobs = results.get('total_jobs', 0)
    quality_jobs = results.get('quality_jobs', 0)
    fair_chance = results.get('fair_chance_employer', 0)

    subject = f"📊 {scrape_type}: {quality_jobs:,} quality jobs ({fair_chance} fair chance)"

    # Send email
    return send_email(recipient_email, subject, html_body, text_body)


def collect_job_stats_from_dataframe(df) -> dict:
    """
    Collect detailed job statistics from a DataFrame.
    Use this helper to build the results dict for send_detailed_scrape_report.

    Args:
        df: Pandas DataFrame with canonical schema fields

    Returns:
        dict with all stats needed for the detailed report
    """
    if df is None or df.empty:
        return {
            'total_jobs': 0,
            'quality_jobs': 0,
            'ai_good': 0,
            'ai_so_so': 0,
            'ai_bad': 0,
            'local_routes': 0,
            'regional_routes': 0,
            'otr_routes': 0,
            'unknown_routes': 0,
            'fair_chance_employer': 0,
            'background_check_required': 0,
            'clean_record_required': 0,
            'no_requirements_mentioned': 0
        }

    total_jobs = len(df)

    # Quality breakdown
    ai_match_col = 'ai.match' if 'ai.match' in df.columns else 'match_level'
    ai_good = len(df[df[ai_match_col] == 'good']) if ai_match_col in df.columns else 0
    ai_so_so = len(df[df[ai_match_col] == 'so-so']) if ai_match_col in df.columns else 0
    ai_bad = len(df[df[ai_match_col] == 'bad']) if ai_match_col in df.columns else 0
    quality_jobs = ai_good + ai_so_so

    # Filter to quality jobs for route and fair chance breakdowns
    quality_df = df[df[ai_match_col].isin(['good', 'so-so'])] if ai_match_col in df.columns else df

    # Route breakdown (quality jobs only)
    route_col = 'ai.route_type' if 'ai.route_type' in df.columns else 'route_type'
    if route_col in quality_df.columns:
        local_routes = len(quality_df[quality_df[route_col] == 'Local'])
        regional_routes = len(quality_df[quality_df[route_col] == 'Regional'])
        otr_routes = len(quality_df[quality_df[route_col] == 'OTR'])
        unknown_routes = len(quality_df[quality_df[route_col] == 'Unknown'])
    else:
        local_routes = regional_routes = otr_routes = unknown_routes = 0

    # Fair chance breakdown (quality jobs only)
    fc_col = 'ai.fair_chance' if 'ai.fair_chance' in df.columns else 'fair_chance'
    if fc_col in quality_df.columns:
        fair_chance_employer = len(quality_df[quality_df[fc_col] == 'fair_chance_employer'])
        background_check_required = len(quality_df[quality_df[fc_col] == 'background_check_required'])
        clean_record_required = len(quality_df[quality_df[fc_col] == 'clean_record_required'])
        no_requirements_mentioned = len(quality_df[quality_df[fc_col] == 'no_requirements_mentioned'])
    else:
        fair_chance_employer = background_check_required = clean_record_required = no_requirements_mentioned = 0

    return {
        'total_jobs': total_jobs,
        'quality_jobs': quality_jobs,
        'ai_good': ai_good,
        'ai_so_so': ai_so_so,
        'ai_bad': ai_bad,
        'local_routes': local_routes,
        'regional_routes': regional_routes,
        'otr_routes': otr_routes,
        'unknown_routes': unknown_routes,
        'fair_chance_employer': fair_chance_employer,
        'background_check_required': background_check_required,
        'clean_record_required': clean_record_required,
        'no_requirements_mentioned': no_requirements_mentioned
    }


def send_zero_jobs_alert(scrape_type: str, error_details: dict, recipient_email: str):
    """
    Send alert when a scrape action completes with 0 jobs added to Supabase.
    This indicates a failure that needs investigation.
    """

    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

    # Extract error details
    raw_jobs = error_details.get('raw_jobs', 0)
    after_dedup = error_details.get('after_dedup', 0)
    classification_errors = error_details.get('classification_errors', 0)
    storage_error = error_details.get('storage_error', '')
    markets_searched = error_details.get('markets_searched', [])
    run_id = error_details.get('run_id', 'unknown')

    # Build HTML body
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #f44336, #c62828); color: white; padding: 25px; text-align: center; border-radius: 8px; }}
            .header h2 {{ margin: 0; font-size: 24px; }}
            .content {{ background-color: #fff3f3; padding: 25px; margin-top: 20px; border-radius: 8px; border: 1px solid #ffcdd2; }}
            .stats {{ background-color: white; padding: 18px; margin: 15px 0; border-left: 4px solid #f44336; border-radius: 4px; }}
            .stats h3 {{ margin-top: 0; color: #c62828; font-size: 16px; }}
            .error-box {{ background-color: #ffebee; padding: 15px; border-radius: 6px; margin: 15px 0; font-family: monospace; font-size: 13px; }}
            .footer {{ margin-top: 25px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>⚠️ ALERT: {scrape_type} - 0 Jobs Uploaded</h2>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">{timestamp}</p>
            </div>

            <div class="content">
                <p><strong>The {scrape_type} scrape completed but uploaded 0 jobs to Supabase.</strong></p>
                <p>This likely indicates a pipeline failure that needs investigation.</p>

                <div class="stats">
                    <h3>📊 Pipeline Statistics</h3>
                    <ul>
                        <li><strong>Run ID:</strong> {run_id}</li>
                        <li><strong>Raw jobs scraped:</strong> {raw_jobs:,}</li>
                        <li><strong>After deduplication:</strong> {after_dedup:,}</li>
                        <li><strong>Classification errors:</strong> {classification_errors:,}</li>
                        <li><strong>Jobs uploaded:</strong> 0 ❌</li>
                    </ul>
                </div>

                <div class="stats">
                    <h3>🔍 Search Configuration</h3>
                    <ul>
                        <li><strong>Source:</strong> {scrape_type}</li>
                        <li><strong>Markets:</strong> {', '.join(markets_searched) if markets_searched else 'N/A'}</li>
                    </ul>
                </div>

                {f'<div class="error-box"><strong>Error:</strong><br>{storage_error}</div>' if storage_error else ''}

                <p style="margin-top: 20px;"><strong>Recommended Actions:</strong></p>
                <ul>
                    <li>Check GitHub Actions logs for the run</li>
                    <li>Verify API keys (OpenAI, Supabase) are valid</li>
                    <li>Check if the source website changed structure</li>
                    <li>Review any error messages in the pipeline output</li>
                </ul>
            </div>

            <div class="footer">
                <p>🤖 Opptek Pipeline Alert System</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Build text version
    text_body = f"""
⚠️ ALERT: {scrape_type} - 0 JOBS UPLOADED
{'='*50}
Time: {timestamp}

The {scrape_type} scrape completed but uploaded 0 jobs to Supabase.
This likely indicates a pipeline failure that needs investigation.

PIPELINE STATISTICS
-------------------
Run ID: {run_id}
Raw jobs scraped: {raw_jobs:,}
After deduplication: {after_dedup:,}
Classification errors: {classification_errors:,}
Jobs uploaded: 0 ❌

SEARCH CONFIGURATION
--------------------
Source: {scrape_type}
Markets: {', '.join(markets_searched) if markets_searched else 'N/A'}

{f'ERROR: {storage_error}' if storage_error else ''}

RECOMMENDED ACTIONS
-------------------
- Check GitHub Actions logs for the run
- Verify API keys (OpenAI, Supabase) are valid
- Check if the source website changed structure
- Review any error messages in the pipeline output

---
Opptek Pipeline Alert System
    """

    # Create urgent subject line
    subject = f"⚠️ ALERT: {scrape_type} Scrape Failed - 0 Jobs Uploaded"

    # Send email
    return send_email(recipient_email, subject, html_body, text_body)


if __name__ == "__main__":
    import sys

    # Test mode - send sample notification
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_results = {
            'total_jobs': 10250,
            'quality_jobs': 6543,
            'scrapes_run': 11
        }

        recipient = os.getenv('NOTIFICATION_EMAIL', 'test@example.com')
        send_scrape_completion_notification("Test", test_results, recipient)

    elif len(sys.argv) > 1 and sys.argv[1] == "test-detailed":
        # Test detailed report
        test_results = {
            'total_jobs': 1250,
            'quality_jobs': 847,
            'ai_good': 523,
            'ai_so_so': 324,
            'ai_bad': 403,
            'local_routes': 312,
            'regional_routes': 245,
            'otr_routes': 198,
            'unknown_routes': 92,
            'fair_chance_employer': 156,
            'background_check_required': 234,
            'clean_record_required': 89,
            'no_requirements_mentioned': 368,
            'source_name': 'Indeed',
            'markets_searched': ['Dallas', 'Houston', 'Phoenix', 'Denver'],
            'search_terms': ['CDL Driver', 'Class A Driver', 'Local CDL Home Daily']
        }

        recipient = os.getenv('NOTIFICATION_EMAIL', 'test@example.com')
        print(f"Sending detailed test report to {recipient}...")
        send_detailed_scrape_report("Indeed Test", test_results, recipient)

    else:
        print("Usage: python send_scrape_notification.py test")
        print("       python send_scrape_notification.py test-detailed")
        print("Or import and use send_scrape_completion_notification() or send_detailed_scrape_report()")
