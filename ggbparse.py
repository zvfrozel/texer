#!/usr/bin/env python3
"""
Convert GeoGebra Asymptote to parameterized LINE_THICKNESS and DOT_THICKNESS.

Usage:
    python ggb_to_param_asy.py input.asy > output.asy
"""

import re
import sys
import argparse
from pathlib import Path

HDR_TEMPLATE = """import graph; size(12cm);
real lsf = {lsf_val};
real LINE_THICKNESS = 1;
real DOT_THICKNESS  = 3.5pt;

defaultpen(linewidth(LINE_THICKNESS) + fontsize(10));
pen ds = black, dp = linewidth(DOT_THICKNESS) + ds;
"""

def transform(text: str) -> str:
    # Extract lsf if available, don't extract size
    lsf_match = re.search(r"\breal\s+lsf\s*=\s*([^;]+);", text)
    lsf_val = lsf_match.group(1).strip() if lsf_match else "0.5"

    out = [HDR_TEMPLATE.format(lsf_val=lsf_val)]

    # Remove header-ish bits we’re replacing
    body = text
    body = re.sub(r"\bpen\s+dps\s*=\s*[^;]+;\s*", "", body)
    body = re.sub(r"\bdefaultpen\s*\(\s*dps\s*\)\s*;\s*", "", body)
    body = re.sub(r"\bimport\s+graph\s*;\s*", "", body)
    body = re.sub(r"\bsize\s*\([^;]+\)\s*;\s*", "", body, flags=re.IGNORECASE)
    body = re.sub(r"\breal\s+lsf\s*=\s*[^;]+;\s*", "", body)
    body = re.sub(r"\bdefaultpen\s*\([^;]+\)\s*;\s*", "", body)

    # Normalize linewidths for strokes to use LINE_THICKNESS
    body = re.sub(r"linewidth\(\s*[\d.]+(?:pt)?\s*\)", "linewidth(LINE_THICKNESS)", body)

    # Ensure dots use dp (scales with DOT_THICKNESS)
    body = re.sub(r"dot\(\s*([^,()]+)\s*,\s*linewidth\([^)]*\)\s*\+\s*ds\s*\)", r"dot(\1, dp)", body)
    body = re.sub(r"dot\(\s*([^,()]+)\s*,\s*ds\s*\)", r"dot(\1, dp)", body)

    # Tidy spacing
    body = re.sub(r"\n{3,}", "\n\n", body).strip()

    out.append(body)
    out.append("// created by ggbparse.py, Abel Mathew")
    return "\n".join(out).strip() + "\n"

def main():
    parser = argparse.ArgumentParser(
        description="Rewrite GeoGebra-exported .asy to use LINE_THICKNESS and DOT_THICKNESS; output to stdout."
    )
    parser.add_argument("input", type=Path, help="Input .asy filename")
    args = parser.parse_args()

    try:
        text = args.input.read_text(encoding="utf-8")
    except Exception as e:
        sys.stderr.write(f"Error reading '{args.input}': {e}\n")
        sys.exit(1)

    sys.stdout.write(transform(text))

if __name__ == "__main__":
    main()
