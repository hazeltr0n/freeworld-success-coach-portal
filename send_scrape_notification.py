#!/usr/bin/env python3
"""
Send email notifications for completed scrapes via Gmail API
"""

import os
import base64
import json
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def load_gmail_credentials():
    """Load Gmail API credentials from environment or files"""

    # Try environment variable first (for GitHub Actions)
    creds_b64 = os.getenv('DRIVER_PULSE_GMAIL_CREDENTIALS')
    token_b64 = os.getenv('DRIVER_PULSE_GMAIL_TOKEN')

    if creds_b64 and token_b64:
        # Decode from base64
        creds_json = base64.b64decode(creds_b64).decode('utf-8')
        token_json = base64.b64decode(token_b64).decode('utf-8')

        # Parse credentials
        creds_data = json.loads(creds_json)
        token_data = json.loads(token_json)

        # Create credentials object
        credentials = Credentials(
            token=token_data.get('token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri=creds_data['installed']['token_uri'],
            client_id=creds_data['installed']['client_id'],
            client_secret=creds_data['installed']['client_secret'],
            scopes=token_data.get('scopes', ['https://www.googleapis.com/auth/gmail.send'])
        )

        return credentials

    # Fallback to local files
    elif os.path.exists('gmail_token.json'):
        with open('gmail_token.json', 'r') as f:
            token_data = json.load(f)

        with open('gmail_credentials.json', 'r') as f:
            creds_data = json.load(f)

        credentials = Credentials(
            token=token_data.get('token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri=creds_data['installed']['token_uri'],
            client_id=creds_data['installed']['client_id'],
            client_secret=creds_data['installed']['client_secret'],
            scopes=token_data.get('scopes', ['https://www.googleapis.com/auth/gmail.send'])
        )

        return credentials

    else:
        raise Exception("Gmail credentials not found in environment or files")


def send_email(to_email: str, subject: str, body_html: str, body_text: str = None):
    """Send email via Gmail API"""

    try:
        # Load credentials
        credentials = load_gmail_credentials()

        # Build Gmail service
        service = build('gmail', 'v1', credentials=credentials)

        # Create message
        message = MIMEMultipart('alternative')
        message['To'] = to_email
        message['Subject'] = subject

        # Add text version
        if body_text:
            text_part = MIMEText(body_text, 'plain')
            message.attach(text_part)

        # Add HTML version
        html_part = MIMEText(body_html, 'html')
        message.attach(html_part)

        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

        # Send message
        send_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()

        print(f"✅ Email sent successfully (Message ID: {send_message['id']})")
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
    else:
        print("Usage: python send_scrape_notification.py test")
        print("Or import and use send_scrape_completion_notification() function")
