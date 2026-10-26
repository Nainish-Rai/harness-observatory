#!/usr/bin/env python3
"""Render dashboard.html from harness-summary.json and dashboard.template.html (stdlib only).

    python3 -I render_dashboard.py [--summary harness-summary.json] [--out dashboard.html]

Trims embedded traces to fit --max-mb, dropping the smallest sessions by tokens first.
"""
import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", default="harness-summary.json")
    ap.add_argument("--template", default=os.path.join(HERE, "..", "assets", "dashboard.template.html"))
    ap.add_argument("--out", default="dashboard.html")
    ap.add_argument("--max-mb", type=float, default=8.0)
    a = ap.parse_args()
    with open(a.summary) as fh:
        data = json.load(fh)
    with open(a.template) as fh:
        tpl = fh.read()
    order = [s["id"] for s in data["sessions"] if s["id"] in data["traces"]]
    while True:
        blob = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
        if len(blob) / 1e6 <= a.max_mb or not order:
            break
        data["traces"].pop(order.pop(), None)  # smallest by tokens goes first
        data["traces_embedded"] = len(data["traces"])
    html = tpl.replace("/*__DATA__*/null", blob, 1)
    with open(a.out, "w") as fh:
        fh.write(html)
    print("%s: %.2f MB, %d traces embedded" % (os.path.basename(a.out), len(html) / 1e6, len(data["traces"])))


if __name__ == "__main__":
    main()
