#!/usr/bin/env python3
"""
Convert GeoGebra Asymptote to parameterized LINE_THICKNESS and DOT_THICKNESS.

Usage:
    python ggb_to_param_asy.py input.asy > output.asy

Options:
    -size SIZE            Set overall figure size passed to size() (default: 12cm)
    -font FONT            Set fontsize used in defaultpen (default: 7.5)
    -lsf LSF              Override label scale factor lsf (default: from file or 0.1)
    -line VAL             Set LINE_THICKNESS value (default: 0.5)
    -dot VAL              Set DOT_THICKNESS value (default: 0.5)
"""

import re
import sys
import argparse
from pathlib import Path

HDR_TEMPLATE = """import graph;
size({size});

real lsf = {lsf_val};
real labelscalefactor = lsf;
real fontsize_base = {fontsize};
real LINE_THICKNESS = {line_thickness};
real DOT_THICKNESS  = {dot_thickness};

defaultpen(linewidth(LINE_THICKNESS) + fontsize(fontsize_base));
pen dotstyle = linewidth(DOT_THICKNESS) + black;

picture pic;
"""

# Pre-compile regular expressions for optimal performance
LSF_RE = re.compile(r"\breal\s+(?:lsf|labelscalefactor)\s*=\s*([^;]+);")

# Consolidate 7 header removal passes into 1 single pass
HEADER_REMOVAL_RE = re.compile(
    r"\bpen\s+dps\s*=\s*[^;]+;\s*|"
    r"\bdefaultpen\s*\(\s*dps\s*\)\s*;\s*|"
    r"\bimport\s+graph\s*;\s*|"
    r"\bsize\s*\([^;]+\)\s*;\s*|"
    r"\breal\s+(?:lsf|labelscalefactor)\s*=\s*[^;]+;\s*|"
    r"\bdefaultpen\s*\([^;]+\)\s*;\s*|"
    r"\bpen\s+dotstyle\s*=\s*[^;]+;\s*",
    flags=re.IGNORECASE
)

LINEWIDTH_RE = re.compile(r"linewidth\(\s*[\d.]+(?:pt)?\s*\)")

# Consolidate loops and multiple dot substitution passes into 1 single pass
DOT_STYLE_RE = re.compile(
    r"dot\(\s*(.*?)\s*,\s*(?:linewidth\([^)]*\)\s*\+\s*)?(?:dotstyle|ds|dp)\s*\)",
    flags=re.DOTALL
)

DRAW_CMD_RE = re.compile(r"\b(filldraw|draw|dot|label|xaxis|yaxis|clip)\s*\(")

BLANK_LINES_RE = re.compile(r"\n{3,}")


def transform(
    text: str,
    fontsize: float,
    lsf_override: str | None,
    line_thickness: str,
    dot_thickness: str,
    size: str,
) -> str:
    # Extract lsf or labelscalefactor if available (fallback to 0.1)
    lsf_match = LSF_RE.search(text)
    if lsf_override is not None:
        lsf_val = lsf_override.strip()
    else:
        lsf_val = lsf_match.group(1).strip() if lsf_match else "0.1"

    header = HDR_TEMPLATE.format(
        lsf_val=lsf_val,
        fontsize=f"{fontsize:g}",
        line_thickness=line_thickness,
        dot_thickness=dot_thickness,
        size=size,
    )

    # Apply all optimized regex substitutions
    body = HEADER_REMOVAL_RE.sub("", text)
    body = LINEWIDTH_RE.sub("linewidth(LINE_THICKNESS)", body)
    body = DOT_STYLE_RE.sub(r"dot(\1, dotstyle)", body)
    body = DRAW_CMD_RE.sub(r"\1(pic, ", body)
    body = BLANK_LINES_RE.sub("\n\n", body).strip()

    # Construct and return final string directly
    return f"{header}\n{body}\n\nadd(pic);\n// created by ggbparse.py, Abel Mathew\n"


def main():
    parser = argparse.ArgumentParser(
        description="Rewrite GeoGebra-exported .asy to use LINE_THICKNESS and DOT_THICKNESS; output to stdout."
    )
    parser.add_argument("input", type=Path, help="Input .asy filename")
    parser.add_argument("-size", "--size", type=str, default="12cm", help="Overall figure size passed to size() (default: 12cm)")
    parser.add_argument("-font", "--fontsize", type=float, default=7.5, help="Base fontsize used in defaultpen() (default: 7.5)")
    parser.add_argument("-lsf", "--lsf", type=str, default=None, help="Override label scale factor lsf (default: from file or 0.1)")
    parser.add_argument("-line", "--line-thickness", type=str, default="0.5", help="Value for LINE_THICKNESS in header (default: 0.5)")
    parser.add_argument("-dot", "--dot-thickness", type=str, default="0.5", help="Value for DOT_THICKNESS in header (default: 0.5)")

    args = parser.parse_args()

    try:
        text = args.input.read_text(encoding="utf-8")
        sys.stdout.write(
            transform(
                text,
                fontsize=args.fontsize,
                lsf_override=args.lsf,
                line_thickness=args.line_thickness,
                dot_thickness=args.dot_thickness,
                size=args.size,
            )
        )
    except Exception as e:
        sys.exit(f"Error reading '{args.input}': {e}")


if __name__ == "__main__":
    main()
