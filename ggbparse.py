#!/usr/bin/env python3
"""
Convert GeoGebra Asymptote to parameterized LINE_THICKNESS and DOT_THICKNESS.

Usage:
    python ggb_to_param_asy.py input.asy > output.asy

Options:
    -size SIZE            Set overall figure size passed to size() (default: 12cm)
    -font FONT            Set fontsize used in defaultpen (default: 7.5)
    -lsf LSF              Override label scale factor lsf (default: from file or 0.2)
    -line VAL             Set LINE_THICKNESS value (default: 0.5)
    -dot VAL              Set DOT_THICKNESS value (default: 3pt)
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

def transform(
    text: str,
    fontsize: float,
    lsf_override: str | None,
    line_thickness: str,
    dot_thickness: str,
    size: str,
) -> str:
    # Extract lsf or labelscalefactor if available, don't extract size
    lsf_match = re.search(r"\breal\s+(?:lsf|labelscalefactor)\s*=\s*([^;]+);", text)
    if lsf_override is not None:
        lsf_val = lsf_override.strip()
    else:
        lsf_val = lsf_match.group(1).strip() if lsf_match else "0.2"

    fontsize_str = f"{fontsize:g}"

    out = [
        HDR_TEMPLATE.format(
            lsf_val=lsf_val,
            fontsize=fontsize_str,
            line_thickness=line_thickness,
            dot_thickness=dot_thickness,
            size=size,
        )
    ]

    body = text

    # Remove header-ish bits we’re replacing
    body = re.sub(r"\bpen\s+dps\s*=\s*[^;]+;\s*", "", body)
    body = re.sub(r"\bdefaultpen\s*\(\s*dps\s*\)\s*;\s*", "", body)
    body = re.sub(r"\bimport\s+graph\s*;\s*", "", body)
    body = re.sub(r"\bsize\s*\([^;]+\)\s*;\s*", "", body, flags=re.IGNORECASE)
    body = re.sub(r"\breal\s+(?:lsf|labelscalefactor)\s*=\s*[^;]+;\s*", "", body)
    body = re.sub(r"\bdefaultpen\s*\([^;]+\)\s*;\s*", "", body)
    body = re.sub(r"\bpen\s+dotstyle\s*=\s*[^;]+;\s*", "", body)

    # Normalize linewidths for strokes to use LINE_THICKNESS
    body = re.sub(r"linewidth\(\s*[\d.]+(?:pt)?\s*\)", "linewidth(LINE_THICKNESS)", body)

    # ----- DOTS: force everything to use dotstyle only -----

    # dot(..., linewidth(...) + dotstyle) -> dot(..., dotstyle)
    body = re.sub(
        r"dot\(\s*(.*?)\s*,\s*linewidth\([^)]*\)\s*\+\s*dotstyle\s*\)",
        r"dot(\1, dotstyle)",
        body,
        flags=re.DOTALL,
    )

    # dot(..., linewidth(...) + ds/dp) and dot(..., ds/dp) -> dot(..., dotstyle)
    for pen_name in ("ds", "dp"):
        body = re.sub(
            rf"dot\(\s*(.*?)\s*,\s*linewidth\([^)]*\)\s*\+\s*{pen_name}\s*\)",
            r"dot(\1, dotstyle)",
            body,
            flags=re.DOTALL,
        )
        body = re.sub(
            rf"dot\(\s*(.*?)\s*,\s*{pen_name}\s*\)",
            r"dot(\1, dotstyle)",
            body,
            flags=re.DOTALL,
        )

    # ----- Draw everything into picture `pic` -----
    body = re.sub(
        r"\b(filldraw|draw|dot|label|xaxis|yaxis|clip)\s*\(",
        r"\1(pic, ",
        body,
    )

    # Clean extra blank lines
    body = re.sub(r"\n{3,}", "\n\n", body).strip()

    out.append(body)
    out.append("add(pic);")
    out.append("// created by ggbparse.py, Abel Mathew")

    return "\n".join(out).strip() + "\n"

def main():
    parser = argparse.ArgumentParser(
        description="Rewrite GeoGebra-exported .asy to use LINE_THICKNESS and DOT_THICKNESS; output to stdout."
    )
    parser.add_argument("input", type=Path, help="Input .asy filename")
    parser.add_argument(
        "-size", "--size",
        type=str,
        default="12cm",
        help="Overall figure size passed to size() (default: 12cm)",
    )
    parser.add_argument(
        "-font", "--fontsize",
        type=float,
        default=7.5,
        help="Base fontsize used in defaultpen() (default: 7.5)",
    )
    parser.add_argument(
        "-lsf", "--lsf",
        type=str,
        default=None,
        help="Override label scale factor lsf (default: from file or 0.2)",
    )
    parser.add_argument(
        "-line", "--line-thickness",
        type=str,
        default="0.5",
        help="Value for LINE_THICKNESS in header (default: 0.5)",
    )
    parser.add_argument(
        "-dot", "--dot-thickness",
        type=str,
        default="3pt",
        help="Value for DOT_THICKNESS in header (default: 3pt)",
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
            size=args.size,
        )
    )

if __name__ == "__main__":
    main()
