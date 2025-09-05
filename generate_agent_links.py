#!/usr/bin/env python3
"""
Generate Free Agent portal links from a CSV of agent profile rows.

Reads a CSV and emits a new CSV with a `portal_url` column using the
same encoded config scheme used by the portal (`config=...`).

Usage:
  python3 tools/generate_agent_links.py \
      "/path/to/agent_profiles_rows.csv" \
      --output links_with_urls.csv \
      --base https://fwcareercoach.streamlit.app

Column detection is flexible. It looks for these keys (case-insensitive):
  - agent_uuid: agent_uuid, agent, candidate_id, agent id, airtable id
  - agent_name: agent_name, name, candidate_name, full name
  - coach_username: coach_username, coach, coach user, coach id
  - location: location, market, city
  - route_filter: route_filter, route (defaults: both)
  - fair_chance_only: fair_chance_only, fair (true/false)
  - max_jobs: max_jobs, limit (int; defaults 25)
  - experience_level: experience_level, experience (entry/experienced/both; defaults both)

Outputs original columns + `portal_url`.
"""

import sys
import csv
import argparse
import base64
import json
from typing import Dict, Any


def encode_agent_params(params: Dict[str, Any]) -> str:
    payload = {
        'agent_uuid': params.get('agent_uuid', ''),
        'agent_name': params.get('agent_name', ''),
        'location': params.get('location', 'Houston'),
        'route_filter': params.get('route_filter', 'both'),
        'fair_chance_only': bool(params.get('fair_chance_only', False)),
        'max_jobs': int(params.get('max_jobs', 25) or 25),
        'experience_level': params.get('experience_level', 'both'),
        'coach_username': params.get('coach_username', ''),
    }
    js = json.dumps(payload, separators=(',', ':'))
    return base64.urlsafe_b64encode(js.encode()).decode()


def norm(s: str) -> str:
    return (s or '').strip().lower().replace(' ', '').replace('_', '')


def pick(row: Dict[str, str], *candidates: str, default: Any = '') -> Any:
    row_lc = {k.lower(): v for k, v in row.items()}
    for c in candidates:
        for k, v in row_lc.items():
            if norm(k) == norm(c):
                return v
    return default


def parse_bool(val: str) -> bool:
    s = str(val).strip().lower()
    return s in ('1', 'true', 'yes', 'y')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('csv_path', help='Input CSV of agent rows')
    ap.add_argument('--output', '-o', default='agent_links.csv', help='Output CSV path')
    ap.add_argument('--base', default='https://fwcareercoach.streamlit.app', help='Portal base URL')
    args = ap.parse_args()

    rows = []
    with open(args.csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                agent_uuid = pick(row, 'agent_uuid', 'agent', 'candidate_id', 'airtableid', 'agentid')
                agent_name = pick(row, 'agent_name', 'name', 'candidate_name', 'fullname')
                coach_username = pick(row, 'coach_username', 'coach', 'coachuser', 'coachid')
                location = pick(row, 'location', 'market', 'city') or 'Houston'
                route_filter = (pick(row, 'route_filter', 'route') or 'both').lower()
                fair_chance_only = parse_bool(pick(row, 'fair_chance_only', 'fair'))
                max_jobs_raw = pick(row, 'max_jobs', 'limit')
                try:
                    max_jobs = int(max_jobs_raw) if str(max_jobs_raw).strip() else 25
                except Exception:
                    max_jobs = 25
                experience_level = (pick(row, 'experience_level', 'experience') or 'both').lower()

                params = {
                    'agent_uuid': agent_uuid,
                    'agent_name': agent_name,
                    'coach_username': coach_username,
                    'location': location,
                    'route_filter': route_filter if route_filter in ('local', 'otr', 'both') else 'both',
                    'fair_chance_only': fair_chance_only,
                    'max_jobs': max_jobs,
                    'experience_level': experience_level if experience_level in ('entry', 'experienced', 'both') else 'both',
                }

                cfg = encode_agent_params(params)
                portal_url = f"{args.base}/agent_job_feed?config={cfg}"
                row_out = dict(row)
                row_out['portal_url'] = portal_url
                rows.append(row_out)
            except Exception as e:
                row_out = dict(row)
                row_out['portal_url'] = f"ERROR: {e}"
                rows.append(row_out)

    # Write output
    fieldnames = list(rows[0].keys()) if rows else []
    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Print a quick sample
    print(f"✅ Wrote {len(rows)} rows to {args.output}")
    if rows:
        print(f"Example link: {rows[0].get('portal_url','')}")
    return 0


if __name__ == '__main__':
    sys.exit(main())

