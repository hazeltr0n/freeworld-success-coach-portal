#!/usr/bin/env python3
"""
Find and compare the latest canonical CSVs by market or print latest for a market.

Usage:
  python tools/compare_latest.py <market_name> [other_csv]

Examples:
  python tools/compare_latest.py Houston
  python tools/compare_latest.py Dallas /path/to/terminal_run.csv
"""

import os
import glob
import sys
from pathlib import Path
from compare_canonical_metrics import summarize, print_metrics, print_diff


def latest_csv_for_market(base: Path, market: str) -> str | None:
    patt = f"FreeWorld_Jobs_{market}_*.csv"
    # Search both root and per-market directory patterns
    candidates = []
    candidates += glob.glob(str(base / patt))
    candidates += glob.glob(str(base / market / patt))
    candidates += glob.glob(str(base / f"{market}_*_*.csv"))
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    market = sys.argv[1]
    base = Path(os.getcwd()) / 'FreeWorld_Jobs'
    latest = latest_csv_for_market(base, market)
    if not latest:
        print(f"No CSV found for market: {market}")
        sys.exit(2)
    m = summarize(latest)
    print_metrics(m)
    if len(sys.argv) > 2:
        other = summarize(sys.argv[2])
        print_metrics(other)
        print_diff(m, other)


if __name__ == '__main__':
    main()

