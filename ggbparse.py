#!/usr/bin/env python3
"""
Convert GeoGebra Asymptote to parameterized LINE_THICKNESS and DOT_THICKNESS.

Usage:
    python ggb_to_param_asy.py input.asy > output.asy

Options:
    -font FONT            Set fontsize used in defaultpen (default: 10)
    -lsf LSF              Override label scale factor lsf (default: from file or 0.5)
    -line VAL             Set LINE_THICKNESS value (default: 1)
    -dot VAL              Set DOT_THICKNESS value (default: 3.5pt)
"""

import re
import sys
import argparse
from pathlib import Path

HDR_TEMPLATE = """import graph; size(12cm);
real lsf = {lsf_val};
real fontsize = {fontsize};
real LINE_THICKNESS = {line_thickness};
real DOT_THICKNESS  = {dot_thickness};

defaultpen(linewidth(LINE_THICKNESS) + fontsize(fontsize));
pen ds = black, dp = linewidth(DOT_THICKNESS) + ds;
"""

def transform(
    text: str,
    fontsize: float,
    lsf_override: str | None,
    line_thickness: str,
    dot_thickness: str,
) -> str:
    # Extract lsf or labelscalefactor if available, don't extract size
    lsf_match = re.search(r"\breal\s+(?:lsf|labelscalefactor)\s*=\s*([^;]+);", text)
    if lsf_override is not None:
        lsf_val = lsf_override.strip()
    else:
        lsf_val = lsf_match.group(1).strip() if lsf_match else "0.5"

    fontsize_str = f"{fontsize:g}"

    out = [
        HDR_TEMPLATE.format(
            lsf_val=lsf_val,
            fontsize=fontsize_str,
            line_thickness=line_thickness,
            dot_thickness=dot_thickness,
        )
    ]

    # Remove header-ish bits we’re replacing
    body = text
    body = re.sub(r"\bpen\s+dps\s*=\s*[^;]+;\s*", "", body)
    body = re.sub(r"\bdefaultpen\s*\(\s*dps\s*\)\s*;\s*", "", body)
    body = re.sub(r"\bimport\s+graph\s*;\s*", "", body)
    body = re.sub(r"\bsize\s*\([^;]+\)\s*;\s*", "", body, flags=re.IGNORECASE)
    body = re.sub(r"\breal\s+(?:lsf|labelscalefactor)\s*=\s*[^;]+;\s*", "", body)
    body = re.sub(r"\bdefaultpen\s*\([^;]+\)\s*;\s*", "", body)

    # Normalize linewidths for strokes to use LINE_THICKNESS
    body = re.sub(r"linewidth\(\s*[\d.]+(?:pt)?\s*\)", "linewidth(LINE_THICKNESS)", body)

    # Ensure dots use dp (scales with DOT_THICKNESS)
    body = re.sub(
        r"dot\(\s*(.*?)\s*,\s*linewidth\([^)]*\)\s*\+\s*ds\s*\)",
        r"dot(\1, dp)",
        body,
        flags=re.DOTALL,
    )
    body = re.sub(
        r"dot\(\s*(.*?)\s*,\s*ds\s*\)",
        r"dot(\1, dp)",
        body,
        flags=re.DOTALL,
    )

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
    parser.add_argument(
        "-font", "--fontsize",
        type=float,
        default=10.0,
        help="Base fontsize used in defaultpen() (default: 10)",
    )
    parser.add_argument(
        "-lsf", "--lsf",
        type=str,
        default=None,
        help="Override label scale factor lsf (default: from file or 0.5)",
    )
    parser.add_argument(
        "-line", "--line-thickness",
        type=str,
        default="1",
        help="Value for LINE_THICKNESS in header (default: 1)",
    )
    parser.add_argument(
        "-dot", "--dot-thickness",
        type=str,
        default="3.5pt",
        help="Value for DOT_THICKNESS in header (default: 3.5pt)",
    )
    args = parser.parse_args()

    try:
        text = args.input.read_text(encoding="utf-8")
    except Exception as e:
        sys.stderr.write(f"Error reading '{args.input}': {e}\n")
        sys.exit(1)

    sys.stdout.write(
        transform(
            text,
            fontsize=args.fontsize,
            lsf_override=args.lsf,
            line_thickness=args.line_thickness,
            dot_thickness=args.dot_thickness,
        )
    )

if __name__ == "__main__":
    main()
