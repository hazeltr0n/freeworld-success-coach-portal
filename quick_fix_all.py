#!/usr/bin/env python3
"""
Make three surgical, idempotent fixes to terminal_job_search.py:

1) Ensure def main(...) ends with a colon
2) In run_interactive(), define `generate_html = False` once after the "====" print
3) Change `batch_size=batch_size` -> `batch_size=args.batch_size`

Won't double-insert. Preserves formatting.
"""
from pathlib import Path
import re, sys

FILES = ["terminal_job_search.py"]  # add more files here if needed

def fix_main_colon(s: str) -> str:
    return re.sub(r"^(\s*def\s+main\s*\([^)]*\))\s*(\n)", lambda m: (m.group(1) if m.group(1).rstrip().endswith(":") else m.group(1)+":")+m.group(2), s, flags=re.M)

def add_interactive_default(s: str) -> str:
    m = re.search(r"^\s*def\s+run_interactive\s*\(\s*self[^)]*\):", s, re.M)
    if not m: return s
    start = m.end()
    end = s.find("\ndef ", start)
    if end == -1: end = len(s)
    block = s[start:end]

    if re.search(r"^\s*generate_html\s*=\s*False\s*$", block, re.M):
        return s

    # Find the exact line "print("=" * 60)"
    bar_line_str = "print(\"=\" * 60)"
    bar_line_pos = block.find(bar_line_str)
    
    if bar_line_pos != -1:
        insert_at = start + bar_line_pos + len(bar_line_str)
        # compute indentation from the next non-empty line or reuse the print's indent
        line_start = s.rfind("\n", 0, insert_at) + 1
        indent = re.match(r"\s*", s[line_start:insert_at]).group(0)
        ins = f"\n\n{indent}# Interactive mode default\n{indent}generate_html = False\n"
        return s[:insert_at] + ins + s[insert_at:]
    return s

def fix_batch_size(s: str) -> str:
    return re.sub(
        r"(\\bbatch_size\s*=\s*)batch_size\b",
        r"\1args.batch_size",
        s,
    )

def insert_generate_html_kwarg(s: str) -> str:
    # Insert `generate_html=generate_html,` immediately after a line with generate_csv=... inside a (...) arg list
    out, i, n, changed = [], 0, len(s), False
    while i < n:
        if s[i] != '(':
            out.append(s[i]); i += 1; continue
        start, depth, j, in_str = i, 0, i, None
        while j < n:
            c = s[j]
            if in_str:
                if c == '\\': j += 2; continue
                if c == in_str: in_str = None
                j += 1; continue
            if c in "'\"": in_str = c; j += 1; continue
            if c == '(': depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0: j += 1; break
            j += 1
        if depth != 0 or j > n:
            out.append(s[i]); i += 1; continue
        block = s[start:j]
        if ("generate_csv" in block) and ("generate_html" not in block):
            lines = block.splitlines(True)
            for idx, line in enumerate(lines):
                if "generate_csv" in line and "=" in line:
                    indent = line[:len(line) - len(line.lstrip())]
                    lines.insert(idx+1, f"{indent}generate_html=generate_html,\n")
                    block = "".join(lines)
                    changed = True
                    break
        out.append(block); i = j
    s2 = "".join(out)
    if changed and "# EDIT_APPLIED_insert_generate_html_kwarg" not in s2:
        s2 = s2.rstrip() + "\n# EDIT_APPLIED_insert_generate_html_kwarg\n"
    return s2

def process(path: Path) -> bool:
    if not path.exists(): return False
    s = path.read_text(encoding="utf-8")
    orig = s
    s = fix_main_colon(s)
    s = add_interactive_default(s)
    s = fix_batch_size(s)
    s = insert_generate_html_kwarg(s)
    if s != orig:
        path.write_text(s, encoding="utf-8")
        print(f"Updated {path}")
        return True
    print(f"No changes needed for {path}")
    return False

if __name__ == "__main__":
    changed_any = False
    for name in FILES:
        changed_any |= process(Path(name))
    sys.exit(0 if changed_any else 0)
