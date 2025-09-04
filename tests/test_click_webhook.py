#!/usr/bin/env python3
"""
End-to-end test for Short.io → Supabase Edge Function pipeline.

Usage examples:
  # 1) Provide full function URL (including ?token=...)
  python3 tests/test_click_webhook.py --function-url "https://<project>.functions.supabase.co/shortio-clicks?token=..."

  # 2) Or set env SHORTIO_WEBHOOK_URL and just run:
  SHORTIO_WEBHOOK_URL="https://<project>.functions.supabase.co/shortio-clicks?token=..." \
    python3 tests/test_click_webhook.py

Requires env for Supabase reads:
  SUPABASE_URL, SUPABASE_ANON_KEY
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

try:
    import requests
except Exception as e:
    print("requests package required. pip install requests", file=sys.stderr)
    raise

try:
    from supabase import create_client
except Exception:
    create_client = None


def get_env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)


def build_test_payload(short_id: str, candidate_id: str, coach_tag: str = "coach:hazeltr0n") -> dict:
    return {
        "link": {
            "idString": short_id,
            "shortURL": f"https://freeworldjobs.short.gy/{short_id}",
            "originalURL": "https://indeed.com/viewjob?jk=123",
            "tags": [
                coach_tag,
                "market:Dallas",
                "route:local",
                "match:good",
                "fair:true",
                f"candidate:{candidate_id}",
            ],
        },
        "referrer": "https://t.co",
        "country": "US",
        "userAgent": "Test-Agent/1.0",
    }


def post_event(function_url: str, payload: dict) -> tuple[int, str]:
    try:
        r = requests.post(function_url, json=payload, timeout=15)
        return r.status_code, r.text
    except Exception as e:
        return 0, str(e)


def fetch_supabase_rows(url: str, key: str, table: str, filters: dict, limit: int = 5):
    if not create_client:
        return []
    client = create_client(url, key)
    q = client.table(table).select("*")
    for col, val in filters.items():
        q = q.eq(col, val)
    q = q.order("clicked_at" if table == "click_events" else "last_click", desc=True).limit(limit)
    res = q.execute()
    return res.data or []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--function-url", dest="function_url", default=get_env("SHORTIO_WEBHOOK_URL"),
                    help="Full Edge Function URL including ?token=...")
    ap.add_argument("--coach", dest="coach", default=get_env("TEST_COACH", "hazeltr0n"),
                    help="Coach username to tag in test event")
    ap.add_argument("--timeout", dest="timeout", type=int, default=20,
                    help="Seconds to wait for DB propagation")
    args = ap.parse_args()

    if not args.function_url:
        print("error: --function-url or env SHORTIO_WEBHOOK_URL is required", file=sys.stderr)
        sys.exit(2)

    supabase_url = get_env("SUPABASE_URL")
    supabase_key = get_env("SUPABASE_ANON_KEY")
    if not (supabase_url and supabase_key):
        print("warning: SUPABASE_URL/SUPABASE_ANON_KEY not set. Will skip DB verification.")

    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    short_id = f"test{ts[-8:]}"
    candidate_id = f"TEST-{ts[-6:]}"
    payload = build_test_payload(short_id, candidate_id, coach_tag=f"coach:{args.coach}")

    print(f"Posting test event to function: {args.function_url}")
    status, body = post_event(args.function_url, payload)
    print(f"Function response: {status}\n{body[:500]}")
    if status != 200:
        print("❌ Function did not return 200. Check token, secrets, and logs.")
        sys.exit(1)

    if not (supabase_url and supabase_key):
        print("✅ Function call succeeded. Skipping DB checks (no Supabase env).")
        sys.exit(0)

    print("Waiting for DB propagation...")
    deadline = time.time() + args.timeout
    found = False
    while time.time() < deadline:
        rows = fetch_supabase_rows(supabase_url, supabase_key, "click_events", {"short_id": short_id}, limit=1)
        if rows:
            print("✅ Found click_events row:")
            print(json.dumps(rows[0], indent=2, default=str))
            found = True
            break
        time.sleep(1)

    if not found:
        print("❌ No click_events row found in time window.")
        sys.exit(1)

    # Check candidate aggregate
    agg = fetch_supabase_rows(supabase_url, supabase_key, "candidate_clicks", {"candidate_id": candidate_id}, limit=1)
    if agg:
        print("✅ candidate_clicks updated:")
        print(json.dumps(agg[0], indent=2, default=str))
    else:
        print("⚠️ candidate_clicks not updated (no candidate tag processed or RPC missing).")

    print("All tests completed.")


if __name__ == "__main__":
    main()

