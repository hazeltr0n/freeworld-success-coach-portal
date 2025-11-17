#!/usr/bin/env python3
"""
Bulk delete old Short.io links to get under plan limits

This script will:
1. Fetch all links from your Short.io domain
2. Sort by creation date (oldest first)
3. Delete the oldest N links (default 20,000)
4. Show progress and summary

Usage:
    python3 bulk_delete_old_shortio_links.py --count 20000 --dry-run  # Preview only
    python3 bulk_delete_old_shortio_links.py --count 20000            # Actually delete
"""

import os
import sys
import argparse
import requests
import time
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load from both .env and .streamlit/secrets.toml
load_dotenv()

# Try to load from Streamlit secrets if available
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

class ShortIOBulkDeleter:
    def __init__(self):
        # Try multiple env var names
        self.api_key = (os.getenv('SHORT_IO_API_KEY') or
                       os.getenv('SHORT_API_KEY') or
                       os.getenv('SHORTIO_API_KEY'))
        self.domain = os.getenv('SHORT_DOMAIN', 'freeworldjobs.short.gy')
        self.base_url = "https://api.short.io"

        if not self.api_key:
            print("❌ ERROR: SHORT_IO_API_KEY not found in environment")
            print("   Checked: SHORT_IO_API_KEY, SHORT_API_KEY, SHORTIO_API_KEY")
            print("   Location: .env file and .streamlit/secrets.toml")
            sys.exit(1)

        self.session = requests.Session()
        self.session.headers.update({
            'authorization': self.api_key,
            'Content-Type': 'application/json',
            'accept': '*/*'
        })

        self.domain_id = None
        print(f"✅ Using Short.io API with domain: {self.domain}")
        print(f"   (Skipping validation - account is over limit)")

    def get_all_links(self, limit: int = None) -> List[Dict[str, Any]]:
        """Fetch all links from Short.io domain"""
        all_links = []
        offset = 0
        page_size = 150  # Short.io max per page

        print(f"\n🔍 Fetching links from Short.io...")

        while True:
            try:
                params = {
                    "domain": self.domain,  # Use domain name instead of domain_id
                    "limit": page_size,
                    "offset": offset
                }

                response = self.session.get(f"{self.base_url}/api/links", params=params)

                if response.status_code != 200:
                    print(f"⚠️ API error at offset {offset}: {response.status_code}")
                    break

                data = response.json()
                links = data.get('links', [])

                if not links:
                    break

                all_links.extend(links)
                print(f"  📦 Fetched {len(all_links)} links so far...", end='\r')

                # Stop if we've hit our limit
                if limit and len(all_links) >= limit:
                    all_links = all_links[:limit]
                    break

                # Stop if we've fetched everything
                if len(links) < page_size:
                    break

                offset += page_size
                time.sleep(0.1)  # Be nice to API

            except Exception as e:
                print(f"\n⚠️ Error fetching links: {e}")
                break

        print(f"\n✅ Fetched {len(all_links)} total links")
        return all_links

    def sort_links_by_age(self, links: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort links by creation date (oldest first)"""
        print("\n📅 Sorting links by age (oldest first)...")

        # Parse dates and sort
        for link in links:
            created = link.get('createdAt', '')
            try:
                # Short.io uses ISO format like "2024-01-15T10:30:45.000Z"
                link['_parsed_date'] = datetime.fromisoformat(created.replace('Z', '+00:00'))
            except:
                # Fallback to epoch if parsing fails
                link['_parsed_date'] = datetime.fromtimestamp(0)

        sorted_links = sorted(links, key=lambda x: x['_parsed_date'])

        # Show date range
        if sorted_links:
            oldest = sorted_links[0]['_parsed_date'].strftime('%Y-%m-%d')
            newest = sorted_links[-1]['_parsed_date'].strftime('%Y-%m-%d')
            print(f"  📊 Date range: {oldest} (oldest) → {newest} (newest)")

        return sorted_links

    def delete_links(self, links: List[Dict[str, Any]], dry_run: bool = True) -> Dict[str, int]:
        """Delete links from Short.io"""
        results = {
            'total': len(links),
            'deleted': 0,
            'failed': 0,
            'skipped': 0
        }

        if dry_run:
            print(f"\n🔍 DRY RUN - Would delete {len(links)} links (oldest first)")
            print("\n📋 Sample of links that would be deleted:")
            for i, link in enumerate(links[:10]):
                created = link.get('createdAt', 'unknown')
                title = link.get('title', 'Untitled')[:50]
                idstr = link.get('idString', 'unknown')
                print(f"  {i+1}. {created} - {title} (ID: {idstr})")

            if len(links) > 10:
                print(f"  ... and {len(links) - 10} more")

            return results

        print(f"\n🗑️  DELETING {len(links)} links...")
        print("⚠️  This cannot be undone! Ctrl+C to cancel within 5 seconds...")
        time.sleep(5)

        print("\n🚀 Starting deletion...")

        for i, link in enumerate(links, 1):
            link_id = link.get('idString', '')
            title = link.get('title', 'Untitled')[:40]

            if not link_id:
                results['skipped'] += 1
                continue

            try:
                delete_url = f"{self.base_url}/links/{link_id}"
                response = self.session.delete(delete_url)

                if response.status_code in [200, 204]:
                    results['deleted'] += 1
                    status = "✅"
                else:
                    results['failed'] += 1
                    status = "❌"

                # Progress update every 100 links
                if i % 100 == 0:
                    print(f"  Progress: {i}/{len(links)} ({results['deleted']} deleted, {results['failed']} failed)")

                # Small delay to avoid rate limiting
                if i % 50 == 0:
                    time.sleep(0.5)

            except Exception as e:
                results['failed'] += 1
                print(f"  ❌ Error deleting {link_id}: {e}")

        return results

    def run(self, count: int, dry_run: bool = True):
        """Main execution flow"""
        print("="*60)
        print("🗑️  Short.io Bulk Link Deleter")
        print("="*60)
        print(f"Domain: {self.domain}")
        print(f"Target deletions: {count:,} links")
        print(f"Mode: {'DRY RUN (preview only)' if dry_run else 'LIVE DELETION'}")
        print("="*60)

        # Fetch all links (or at least enough to delete the target count)
        all_links = self.get_all_links(limit=count + 1000)  # Get a bit extra

        if not all_links:
            print("\n❌ No links found to delete")
            return

        print(f"\n📊 Current total links: {len(all_links):,}")

        if len(all_links) < count:
            print(f"⚠️  WARNING: Only found {len(all_links):,} links, but you requested {count:,}")
            print(f"   Will delete all {len(all_links):,} available links")
            count = len(all_links)

        # Sort by age (oldest first)
        sorted_links = self.sort_links_by_age(all_links)

        # Take oldest N links
        links_to_delete = sorted_links[:count]

        # Show summary
        print(f"\n📋 Deletion Plan:")
        print(f"   • Total links in domain: {len(all_links):,}")
        print(f"   • Links to delete: {len(links_to_delete):,}")
        print(f"   • Links remaining: {len(all_links) - len(links_to_delete):,}")

        if links_to_delete:
            oldest = links_to_delete[0]['_parsed_date'].strftime('%Y-%m-%d')
            newest = links_to_delete[-1]['_parsed_date'].strftime('%Y-%m-%d')
            print(f"   • Date range to delete: {oldest} → {newest}")

        # Delete links
        results = self.delete_links(links_to_delete, dry_run=dry_run)

        # Final summary
        print("\n" + "="*60)
        print("📊 Final Summary")
        print("="*60)
        print(f"Total processed: {results['total']:,}")
        print(f"Successfully deleted: {results['deleted']:,}")
        print(f"Failed: {results['failed']:,}")
        print(f"Skipped: {results['skipped']:,}")

        if not dry_run:
            print(f"\n✅ Deletion complete!")
            print(f"   Estimated links remaining: ~{len(all_links) - results['deleted']:,}")
        else:
            print(f"\n💡 This was a DRY RUN - no links were deleted")
            print(f"   Remove --dry-run flag to actually delete links")


def main():
    parser = argparse.ArgumentParser(description='Bulk delete old Short.io links')
    parser.add_argument('--count', type=int, default=20000,
                       help='Number of oldest links to delete (default: 20000)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview only - do not actually delete')

    args = parser.parse_args()

    deleter = ShortIOBulkDeleter()
    deleter.run(count=args.count, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
