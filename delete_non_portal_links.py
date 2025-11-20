#!/usr/bin/env python3
"""
Delete all Short.io links that are NOT portal links.

Portal links are identified by:
- Title starting with "Portal -" or "Portal:"
- Or having tag "type:portal_access"

Usage:
    python3 delete_non_portal_links.py --dry-run  # Preview only
    python3 delete_non_portal_links.py            # Actually delete
"""

import os
import sys
import argparse
import requests
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

load_dotenv()

# Try to load from Streamlit secrets
try:
    import toml
    secrets_path = os.path.join(os.getcwd(), '.streamlit', 'secrets.toml')
    if os.path.exists(secrets_path):
        with open(secrets_path, 'r') as f:
            secrets = toml.load(f)
            for key, value in secrets.items():
                if key not in os.environ:
                    os.environ[key] = str(value)
except:
    pass


def is_portal_link(link: Dict[str, Any]) -> bool:
    """Check if a link is a portal link based on title or tags"""
    title = link.get('title', '') or ''

    # Check title patterns
    if title.startswith('Portal -') or title.startswith('Portal:'):
        return True

    # Check tags for portal indicator
    tags = link.get('tags', []) or []
    if isinstance(tags, list):
        for tag in tags:
            if 'portal' in str(tag).lower():
                return True

    return False


class ShortIONonPortalDeleter:
    def __init__(self):
        self.api_key = (os.getenv('SHORT_IO_API_KEY') or
                       os.getenv('SHORT_API_KEY') or
                       os.getenv('SHORTIO_API_KEY'))
        self.domain = os.getenv('SHORT_DOMAIN', 'freeworldjobs.short.gy')
        self.base_url = "https://api.short.io"
        self.domain_id: Optional[int] = None

        if not self.api_key:
            print("ERROR: SHORT_IO_API_KEY not found")
            sys.exit(1)

        self.session = requests.Session()
        self.session.headers.update({
            'authorization': self.api_key,
            'Content-Type': 'application/json',
            'accept': '*/*'
        })

        print(f"Using Short.io domain: {self.domain}")

    def _resolve_domain_id(self) -> Optional[int]:
        """Resolve Short.io domain ID by creating a temp link and extracting DomainId.

        Immediately deletes the temp link. Returns None if resolution fails.
        """
        try:
            payload = {"originalURL": "https://www.google.com", "domain": self.domain}
            resp = self.session.post(f"{self.base_url}/links", json=payload, timeout=20)
            if resp.status_code != 200:
                print(f"Domain ID probe failed: {resp.status_code} - {resp.text[:200]}")
                return None
            data = resp.json()
            dom_id = data.get('domainId') or data.get('DomainId')
            # Best-effort cleanup of temp link
            try:
                if 'idString' in data:
                    requests.delete(
                        f"{self.base_url}/links/{data['idString']}",
                        headers={'authorization': self.session.headers['authorization']},
                        timeout=20,
                    )
            except Exception:
                pass
            try:
                return int(dom_id) if dom_id is not None else None
            except Exception:
                return None
        except Exception as e:
            print(f"Error resolving domain ID: {e}")
            return None

    def get_all_links(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch all links using cursor-based pagination"""
        all_links = []
        page_size = 150
        next_token = None

        print("\nFetching all links from Short.io...")

        if not self.domain_id:
            self.domain_id = self._resolve_domain_id() or 1475162  # fallback
            print(f"Resolved domain ID: {self.domain_id}")

        while True:
            try:
                params = {"domain_id": self.domain_id, "limit": page_size}
                if next_token:
                    params["pageToken"] = next_token

                response = self.session.get(f"{self.base_url}/api/links", params=params)

                if response.status_code != 200:
                    print(f"API error: {response.status_code}")
                    break

                data = response.json()
                links = data.get('links', [])

                if not links:
                    break

                all_links.extend(links)
                print(f"  Fetched {len(all_links)} links...", end='\r')

                if limit and len(all_links) >= limit:
                    all_links = all_links[:limit]
                    break

                next_token = data.get('nextPageToken')
                if not next_token:
                    break

                time.sleep(0.1)

            except Exception as e:
                print(f"\nError fetching links: {e}")
                break

        print(f"\nTotal links fetched: {len(all_links)}")
        return all_links

    def categorize_links(self, links: List[Dict[str, Any]]) -> tuple:
        """Separate portal links from non-portal links"""
        portal_links = []
        non_portal_links = []

        for link in links:
            if is_portal_link(link):
                portal_links.append(link)
            else:
                non_portal_links.append(link)

        return portal_links, non_portal_links

    def delete_links(self, links: List[Dict[str, Any]], dry_run: bool = True, *, skip_confirm: bool = False) -> Dict[str, int]:
        """Delete the specified links"""
        results = {
            'total': len(links),
            'deleted': 0,
            'failed': 0,
        }

        if dry_run:
            print(f"\nDRY RUN - Would delete {len(links)} non-portal links")
            print("\nSample of links to delete:")
            for i, link in enumerate(links[:15]):
                title = link.get('title', 'Untitled')[:50]
                idstr = link.get('idString', 'unknown')
                created = link.get('createdAt', 'unknown')[:10]
                print(f"  {i+1}. [{created}] {title} (ID: {idstr})")

            if len(links) > 15:
                print(f"  ... and {len(links) - 15} more")
            return results

        print(f"\nDELETING {len(links)} non-portal links...")
        if not skip_confirm:
            print("This cannot be undone! Ctrl+C to cancel within 5 seconds...")
            time.sleep(5)

        print("\nStarting deletion...")

        for i, link in enumerate(links, 1):
            link_id = link.get('idString', '')

            if not link_id:
                results['failed'] += 1
                continue

            try:
                # DELETE requests must NOT have Content-Type header
                response = requests.delete(
                    f"{self.base_url}/links/{link_id}",
                    headers={'authorization': self.session.headers['authorization']}
                )

                if response.status_code in [200, 204]:
                    results['deleted'] += 1
                else:
                    results['failed'] += 1

                if i % 100 == 0:
                    print(f"  Progress: {i}/{len(links)} ({results['deleted']} deleted, {results['failed']} failed)")

                if i % 50 == 0:
                    time.sleep(0.5)

            except Exception as e:
                results['failed'] += 1
                print(f"  Error deleting {link_id}: {e}")

        return results

    def run(self, dry_run: bool = True, limit: Optional[int] = None, delete_one: bool = False, skip_confirm: bool = False, batch_size: Optional[int] = None):
        """Main execution"""
        print("=" * 60)
        print("Short.io Non-Portal Link Deleter")
        print("=" * 60)

        # Fetch all links
        all_links = self.get_all_links(limit=limit)

        if not all_links:
            print("\nNo links found")
            return

        # Categorize
        portal_links, non_portal_links = self.categorize_links(all_links)

        print(f"\nLink Analysis:")
        print(f"  Total links: {len(all_links)}")
        print(f"  Portal links (KEEP): {len(portal_links)}")
        print(f"  Non-portal links (DELETE): {len(non_portal_links)}")

        if not non_portal_links:
            print("\nNo non-portal links to delete!")
            return

        # Show sample of portal links being kept
        if portal_links:
            print(f"\nSample portal links being KEPT:")
            for i, link in enumerate(portal_links[:5]):
                title = link.get('title', 'Untitled')[:50]
                print(f"  {i+1}. {title}")

        # Delete non-portal links
        if delete_one:
            print("\nTest mode: deleting ONLY ONE non-portal link")
            if not skip_confirm:
                print("This cannot be undone! Ctrl+C to cancel within 5 seconds...")
                time.sleep(5)
            results = self.delete_links(non_portal_links[:1], dry_run=False, skip_confirm=True)
        else:
            if not dry_run and batch_size and batch_size > 0:
                print(f"\nBatch deletion enabled: {batch_size} per batch")
                aggregate = {'total': 0, 'deleted': 0, 'failed': 0}
                for start in range(0, len(non_portal_links), batch_size):
                    batch = non_portal_links[start:start+batch_size]
                    print(f"\nProcessing batch {start//batch_size + 1} ({len(batch)} links)...")
                    batch_result = self.delete_links(batch, dry_run=False, skip_confirm=skip_confirm)
                    aggregate['total'] += batch_result['total']
                    aggregate['deleted'] += batch_result['deleted']
                    aggregate['failed'] += batch_result['failed']
                results = aggregate
            else:
                results = self.delete_links(non_portal_links, dry_run=dry_run, skip_confirm=skip_confirm)

        # Summary
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        print(f"Portal links kept: {len(portal_links)}")
        print(f"Non-portal links processed: {results['total']}")
        print(f"Successfully deleted: {results['deleted']}")
        print(f"Failed: {results['failed']}")

        if dry_run:
            print(f"\nThis was a DRY RUN - no links were deleted")
            print(f"Remove --dry-run flag to actually delete")


def main():
    parser = argparse.ArgumentParser(description='Delete all non-portal Short.io links')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview only - do not actually delete')
    parser.add_argument('--limit', type=int, default=None,
                       help='Max links to fetch for quick tests')
    parser.add_argument('--delete-one', action='store_true',
                       help='Delete only one non-portal link (ignores --dry-run)')
    parser.add_argument('--skip-confirm', action='store_true',
                       help='Skip 5s safety wait before deletion')
    parser.add_argument('--batch-size', type=int, default=None,
                       help='Delete in batches of this size (live mode only)')

    args = parser.parse_args()

    deleter = ShortIONonPortalDeleter()
    deleter.run(
        dry_run=args.dry_run,
        limit=args.limit,
        delete_one=args.delete_one,
        skip_confirm=args.skip_confirm,
        batch_size=args.batch_size,
    )


if __name__ == "__main__":
    main()
