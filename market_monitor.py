#!/usr/bin/env python3
"""
Market Monitoring System
Monitors job counts across markets and sends email alerts when markets run empty
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple
from supabase_utils import get_client


def check_market_job_counts(hours: int = 72) -> Dict[str, int]:
    """
    Check job counts for all markets in the database

    Args:
        hours: How many hours back to check (default 72)

    Returns:
        Dictionary of {market: job_count}
    """
    client = get_client()
    if not client:
        print("❌ Could not connect to Supabase")
        return {}

    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

    # Get all quality jobs grouped by market
    result = client.table('jobs').select('market').gte('created_at', cutoff).in_('match_level', ['good', 'so-so']).execute()

    if not result.data:
        print(f"⚠️ No jobs found in any market in last {hours} hours")
        return {}

    # Count jobs per market
    market_counts = {}
    for job in result.data:
        market = job.get('market', 'Unknown')
        market_counts[market] = market_counts.get(market, 0) + 1

    return market_counts


def get_expected_markets() -> List[str]:
    """Get list of markets that should have jobs"""
    from free_agent_system import get_market_options
    return get_market_options()


def find_empty_markets(hours: int = 72) -> Tuple[List[str], Dict[str, int]]:
    """
    Find markets that have zero jobs

    Args:
        hours: How many hours back to check

    Returns:
        Tuple of (empty_markets_list, all_market_counts_dict)
    """
    market_counts = check_market_job_counts(hours)
    expected_markets = get_expected_markets()

    # Find markets with zero jobs
    empty_markets = [market for market in expected_markets if market_counts.get(market, 0) == 0]

    return empty_markets, market_counts


def send_email_alert(empty_markets: List[str], market_counts: Dict[str, int], hours: int = 72):
    """
    Send email alert about empty markets using Gmail API

    Args:
        empty_markets: List of markets with zero jobs
        market_counts: Dictionary of all market counts
        hours: Lookback period in hours
    """
    # Use Gmail API (same as DriverPulse 2FA)
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        import pickle
        import base64
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
    except ImportError:
        print("❌ Gmail API not available. Install google-api-python-client")
        return False

    recipient_email = 'james@freeworld.org'
    sender_email = os.getenv('DRIVER_PULSE_EMAIL', 'freeworldplacement@gmail.com')

    # Gmail API setup (reuse DriverPulse credentials)
    SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.readonly']

    creds = None
    token_path = 'token.pickle'

    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'🚨 Market Alert: {len(empty_markets)} Markets with Zero Jobs'
    msg['From'] = sender_email
    msg['To'] = recipient_email

    # Create HTML body
    html = f"""
    <html>
      <head>
        <style>
          body {{ font-family: Arial, sans-serif; }}
          .alert {{ background-color: #fff3cd; border: 1px solid #ffc107; padding: 15px; margin: 10px 0; border-radius: 5px; }}
          .empty-market {{ color: #dc3545; font-weight: bold; }}
          .ok-market {{ color: #28a745; }}
          table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
          th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
          th {{ background-color: #f8f9fa; }}
          .zero {{ background-color: #f8d7da; }}
        </style>
      </head>
      <body>
        <h2>🚨 Market Job Alert</h2>
        <div class="alert">
          <strong>⚠️ {len(empty_markets)} market(s) have ZERO jobs in the last {hours} hours!</strong>
        </div>

        <h3>Empty Markets (Need Immediate Scraping):</h3>
        <ul>
    """

    for market in empty_markets:
        html += f'<li class="empty-market">{market}</li>\n'

    html += """
        </ul>

        <h3>All Market Status:</h3>
        <table>
          <tr>
            <th>Market</th>
            <th>Job Count</th>
            <th>Status</th>
          </tr>
    """

    # Sort markets by job count
    sorted_markets = sorted(market_counts.items(), key=lambda x: x[1])

    for market, count in sorted_markets:
        status_class = 'zero' if count == 0 else ''
        status_text = '🚨 EMPTY' if count == 0 else '✅ OK'
        html += f'''
          <tr class="{status_class}">
            <td>{market}</td>
            <td>{count}</td>
            <td>{status_text}</td>
          </tr>
        '''

    # Add markets that have zero jobs but aren't in the database
    for market in empty_markets:
        if market not in market_counts:
            html += f'''
              <tr class="zero">
                <td>{market}</td>
                <td>0</td>
                <td>🚨 EMPTY</td>
              </tr>
            '''

    html += f"""
        </table>

        <h3>Action Required:</h3>
        <p>Please run a job search for the empty markets using:</p>
        <ul>
          <li><strong>DriverPulse Multi-Market Scraper</strong> - Fastest way to populate all markets</li>
          <li><strong>Async Batches</strong> - Schedule searches for specific markets</li>
          <li><strong>Manual Job Search</strong> - Search individual markets</li>
        </ul>

        <p><small>Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</small></p>
      </body>
    </html>
    """

    # Create plain text version
    text = f"""
Market Job Alert - {len(empty_markets)} Empty Markets

Empty Markets (Need Immediate Scraping):
{chr(10).join(f'- {market}' for market in empty_markets)}

All Market Status:
{chr(10).join(f'{market}: {count} jobs' for market, count in sorted_markets)}

Action Required:
Run a job search for the empty markets using DriverPulse, Async Batches, or Manual Search.

Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
    """

    # Attach parts
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    msg.attach(part1)
    msg.attach(part2)

    # Send email via Gmail API
    try:
        print(f"📧 Sending alert email to {recipient_email} via Gmail API...")

        # Encode message
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
        message = {'raw': raw_message}

        # Send
        service.users().messages().send(userId='me', body=message).execute()

        print(f"✅ Alert email sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        import traceback
        traceback.print_exc()
        return False


def send_daily_health_report(hours: int = 72):
    """
    Send comprehensive daily job health report

    Args:
        hours: Lookback period in hours (default 72)
    """
    print(f"📊 Generating daily job health report (last {hours} hours)...")

    empty_markets, market_counts = find_empty_markets(hours)
    expected_markets = get_expected_markets()
    total_jobs = sum(market_counts.values())

    # Use Gmail API for sending
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        import pickle
        import base64
    except ImportError:
        print("❌ Gmail API not available")
        return False

    recipient_email = 'james@freeworld.org'
    sender_email = os.getenv('DRIVER_PULSE_EMAIL', 'freeworldplacement@gmail.com')

    # Gmail API setup using Streamlit secrets (no credentials.json needed)
    SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.readonly']

    # Get credentials from environment/secrets
    try:
        import streamlit as st
        client_id = st.secrets.get('GMAIL_CLIENT_ID', os.getenv('GMAIL_CLIENT_ID'))
        client_secret = st.secrets.get('GMAIL_CLIENT_SECRET', os.getenv('GMAIL_CLIENT_SECRET'))
    except:
        client_id = os.getenv('GMAIL_CLIENT_ID')
        client_secret = os.getenv('GMAIL_CLIENT_SECRET')

    if not client_id or not client_secret:
        print("❌ Gmail credentials not found in secrets/environment")
        return False

    # Create client config dict from secrets
    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uris": ["http://localhost"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    }

    creds = None
    token_path = 'gmail_token.pickle'

    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    # Determine subject based on health
    if empty_markets:
        subject = f"🚨 Daily Job Health: {len(empty_markets)} Markets EMPTY"
    else:
        subject = f"✅ Daily Job Health: All Markets OK ({total_jobs} jobs)"

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email

    # Build HTML report
    html = f"""
    <html>
      <head>
        <style>
          body {{ font-family: Arial, sans-serif; }}
          .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
          .alert {{ background-color: #fff3cd; border: 1px solid #ffc107; padding: 15px; margin: 10px 0; border-radius: 5px; }}
          .success {{ background-color: #d4edda; border: 1px solid #28a745; padding: 15px; margin: 10px 0; border-radius: 5px; }}
          table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
          th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
          th {{ background-color: #f8f9fa; font-weight: bold; }}
          .zero {{ background-color: #f8d7da; color: #721c24; }}
          .low {{ background-color: #fff3cd; }}
          .ok {{ background-color: #d4edda; }}
          .summary {{ font-size: 1.2em; margin: 20px 0; }}
        </style>
      </head>
      <body>
        <div class="header">
          <h2>📊 Daily Job Health Report</h2>
          <p>Automated market monitoring for FreeWorld Success Coach Platform</p>
          <p><strong>Report Date:</strong> {datetime.now(timezone.utc).strftime('%A, %B %d, %Y at %H:%M UTC')}</p>
        </div>
    """

    # Alert or success message
    if empty_markets:
        html += f"""
        <div class="alert">
          <h3>🚨 Action Required: {len(empty_markets)} Markets Empty</h3>
          <p>The following markets have ZERO jobs and need immediate scraping:</p>
          <ul>
        """
        for market in sorted(empty_markets):
            html += f"<li><strong>{market}</strong></li>\n"
        html += """
          </ul>
        </div>
        """
    else:
        html += f"""
        <div class="success">
          <h3>✅ All Markets Healthy</h3>
          <p>All {len(expected_markets)} markets have active job listings.</p>
        </div>
        """

    # Summary stats
    html += f"""
        <div class="summary">
          <strong>Summary:</strong> {total_jobs} total jobs across {len([c for c in market_counts.values() if c > 0])} markets
        </div>

        <h3>Market Health Details (Last {hours} hours):</h3>
        <table>
          <tr>
            <th>Market</th>
            <th>Job Count</th>
            <th>Status</th>
          </tr>
    """

    # Sort markets: empty first, then by count (descending)
    sorted_markets = sorted(
        [(m, market_counts.get(m, 0)) for m in expected_markets],
        key=lambda x: (x[1] > 0, -x[1])
    )

    for market, count in sorted_markets:
        if count == 0:
            row_class = 'zero'
            status = '🚨 EMPTY - Scrape Needed'
        elif count < 10:
            row_class = 'low'
            status = '⚠️ Low'
        else:
            row_class = 'ok'
            status = '✅ Healthy'

        html += f"""
          <tr class="{row_class}">
            <td>{market}</td>
            <td>{count}</td>
            <td>{status}</td>
          </tr>
        """

    html += f"""
        </table>

        <h3>Recommended Actions:</h3>
    """

    if empty_markets:
        html += """
        <ul>
          <li><strong>Priority 1:</strong> Run DriverPulse Multi-Market Scraper to populate all empty markets</li>
          <li><strong>Priority 2:</strong> Schedule async batches for recurring searches</li>
          <li><strong>Priority 3:</strong> Check for API quota limits or scraping issues</li>
        </ul>
        """
    else:
        html += """
        <ul>
          <li>✅ No action required - all markets are healthy</li>
          <li>💡 Consider scheduling regular searches to maintain job freshness</li>
        </ul>
        """

    html += f"""
        <hr>
        <p><small>This is an automated report from FreeWorld Job Scraper<br>
        Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</small></p>
      </body>
    </html>
    """

    # Text version
    text = f"""
Daily Job Health Report - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}

{'='*60}
SUMMARY
{'='*60}
Total Jobs: {total_jobs}
Markets with Jobs: {len([c for c in market_counts.values() if c > 0])}/{len(expected_markets)}
Empty Markets: {len(empty_markets)}

"""

    if empty_markets:
        text += f"""
🚨 ALERT: {len(empty_markets)} Markets Need Scraping:
{chr(10).join(f'  - {m}' for m in sorted(empty_markets))}

"""

    text += f"""
{'='*60}
MARKET DETAILS (Last {hours} hours)
{'='*60}
"""

    for market, count in sorted_markets:
        status = '🚨 EMPTY' if count == 0 else ('⚠️ Low' if count < 10 else '✅ OK')
        text += f"{market:20s} {count:4d} jobs  {status}\n"

    # Attach parts
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    msg.attach(part1)
    msg.attach(part2)

    # Send via Gmail API
    try:
        print(f"📧 Sending daily health report to {recipient_email}...")
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
        message = {'raw': raw_message}
        service.users().messages().send(userId='me', body=message).execute()
        print(f"✅ Daily health report sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to send report: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_market_check(hours: int = 72, send_email: bool = True) -> Dict:
    """
    Run complete market check and optionally send alerts (deprecated - use send_daily_health_report)

    Args:
        hours: Lookback period in hours
        send_email: Whether to send email alerts

    Returns:
        Dictionary with check results
    """
    print(f"🔍 Checking market job counts (last {hours} hours)...")

    empty_markets, market_counts = find_empty_markets(hours)

    total_jobs = sum(market_counts.values())
    expected_markets = get_expected_markets()

    results = {
        'empty_markets': empty_markets,
        'market_counts': market_counts,
        'total_jobs': total_jobs,
        'total_markets': len(expected_markets),
        'markets_with_jobs': len([m for m in market_counts.values() if m > 0]),
        'check_time': datetime.now(timezone.utc).isoformat()
    }

    print(f"\n📊 Market Check Results:")
    print(f"   Total jobs: {total_jobs}")
    print(f"   Markets with jobs: {results['markets_with_jobs']}/{results['total_markets']}")
    print(f"   Empty markets: {len(empty_markets)}")

    if empty_markets:
        print(f"\n🚨 ALERT: {len(empty_markets)} markets have ZERO jobs!")
        for market in empty_markets:
            print(f"   - {market}")

        if send_email:
            send_email_alert(empty_markets, market_counts, hours)
    else:
        print(f"\n✅ All markets have jobs!")

    return results


if __name__ == '__main__':
    # Run daily health report from command line
    import sys

    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 72

    send_daily_health_report(hours=hours)
