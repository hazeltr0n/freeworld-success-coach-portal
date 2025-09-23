#!/usr/bin/env python3
"""
Compare canonical CSV metrics between two runs (or print one).

Usage:
  python tools/compare_canonical_metrics.py <csv_a> [<csv_b>]

Metrics:
  - total_jobs
  - included_jobs (ai.match in ['good','so-so'] or route.final_status startswith included)
  - match breakdown (good/so-so/bad)
  - route counts (Local/OTR/Regional/Unknown)
"""

import sys
import pandas as pd
from typing import Dict


def summarize(path: str) -> Dict:
    df = pd.read_csv(path)
    metrics = {}
    metrics['path'] = path
    metrics['total_jobs'] = len(df)
    if 'ai.match' in df.columns:
        m = df['ai.match'].fillna('')
        metrics['ai_good'] = int((m == 'good').sum())
        metrics['ai_so_so'] = int((m == 'so-so').sum())
        metrics['ai_bad'] = int((m == 'bad').sum())
        metrics['included_jobs'] = metrics['ai_good'] + metrics['ai_so_so']
    elif 'route.final_status' in df.columns:
        s = df['route.final_status'].astype(str)
        metrics['included_jobs'] = int(s.str.startswith('included').sum())
    else:
        metrics['included_jobs'] = metrics['total_jobs']
    # Route counts
    if 'ai.route_type' in df.columns:
        r = df['ai.route_type'].fillna('Unknown')
        metrics['routes_local'] = int((r == 'Local').sum())
        metrics['routes_otr'] = int((r == 'OTR').sum())
        metrics['routes_regional'] = int((r == 'Regional').sum())
        metrics['routes_unknown'] = int((r == 'Unknown').sum())
    return metrics


def print_metrics(m: Dict):
    print(f"\n== {m['path']} ==")
    print(f"total_jobs: {m.get('total_jobs', 0)}")
    print(f"included_jobs: {m.get('included_jobs', 0)}")
    if 'ai_good' in m:
        print(f"ai_good: {m['ai_good']}, ai_so_so: {m.get('ai_so_so', 0)}, ai_bad: {m.get('ai_bad', 0)}")
    if 'routes_local' in m:
        print(
            "routes - local: {local}, otr: {otr}, regional: {regional}, unknown: {unk}".format(
                local=m.get('routes_local', 0),
                otr=m.get('routes_otr', 0),
                regional=m.get('routes_regional', 0),
                unk=m.get('routes_unknown', 0),
            )
        )


def print_diff(a: Dict, b: Dict):
    print("\n== DIFF ==")
    keys = set(a.keys()) | set(b.keys())
    for k in sorted(keys):
        if k == 'path':
            continue
        va = a.get(k)
        vb = b.get(k)
        if va != vb:
            print(f"{k}: {va} -> {vb}")
    print("== END DIFF ==\n")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    a = summarize(sys.argv[1])
    print_metrics(a)
    if len(sys.argv) > 2:
        b = summarize(sys.argv[2])
        print_metrics(b)
        print_diff(a, b)


if __name__ == '__main__':
    main()

