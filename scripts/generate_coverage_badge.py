# scripts/generate_coverage_badge.py
import json
import sys

COVERAGE_PATH = "coverage.json"
BADGE_PATH = "coverage-badge.svg"

def get_coverage_percentage(path):
    with open(path) as f:
        data = json.load(f)
        total = data["totals"]
        return total["percent_covered_display"]

def generate_svg(percent):
    color = "red"
    try:
        pct = float(percent)
        if pct >= 90:
            color = "brightgreen"
        elif pct >= 75:
            color = "yellow"
        elif pct >= 50:
            color = "orange"
    except:
        pass

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="120" height="20">
  <rect width="60" height="20" fill="#555"/>
  <rect x="60" width="60" height="20" fill="{color}"/>
  <text x="30" y="14" fill="#fff" font-family="Verdana" font-size="11" text-anchor="middle">coverage</text>
  <text x="90" y="14" fill="#fff" font-family="Verdana" font-size="11" text-anchor="middle">{percent}%</text>
</svg>"""

if __name__ == "__main__":
    pct = get_coverage_percentage(COVERAGE_PATH)
    svg = generate_svg(pct)
    with open(BADGE_PATH, "w") as f:
        f.write(svg)
    print(f"Generated coverage badge with {pct}% coverage")
