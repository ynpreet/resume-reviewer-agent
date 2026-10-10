#!/usr/bin/env python3
"""
Resume Reviewer AI -- fixture test suite.

Runs the rule engine over the three fixture resumes + sample JD and asserts
expected outcomes. Also cross-checks that every element ID referenced by the
web app's JS exists in the HTML (catches wiring typos before deploy).

Exit 0 = all assertions pass. Prints a per-assertion log.
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rules_engine import doc_from_text, review  # noqa: E402

PASS_COUNT = 0


def check(name, cond, detail=""):
    global PASS_COUNT
    status = "PASS" if cond else "FAIL"
    print("%s | %s %s" % (status, name, ("-- " + detail) if detail and not cond else ""))
    if cond:
        PASS_COUNT += 1
    else:
        raise SystemExit("ASSERTION FAILED: %s %s" % (name, detail))


def load(name):
    return (HERE / "fixtures" / name).read_text(encoding="utf-8")


def failed_ids(rep):
    return {r["id"] for r in rep["failed"]}


def main():
    jd = load("sample-jd.txt")

    # ---- strong resume -------------------------------------------------
    strong = review(doc_from_text(load("strong.txt")), jd)
    check("strong: overall >= 85", strong["overall"] >= 85,
          "got %d" % strong["overall"])
    check("strong: <= 3 failed rules", len(strong["failed"]) <= 3,
          "failed=%s" % sorted(failed_ids(strong)))
    check("strong: JD coverage >= 50%%", (strong["jd"]["coverage"] or 0) >= 50,
          "got %s" % strong["jd"]["coverage"])

    # ---- weak resume ---------------------------------------------------
    weak = review(doc_from_text(load("weak.txt")), jd)
    check("weak: overall <= 55", weak["overall"] <= 55,
          "got %d" % weak["overall"])
    check("weak: >= 12 failed rules", len(weak["failed"]) >= 12,
          "failed=%d" % len(weak["failed"]))
    wf = failed_ids(weak)
    for rid in ["H1", "H3", "H5", "H6", "H7", "H9", "H13",
                "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8",
                "B9", "B10", "B11", "B12", "B13", "B16", "B17", "B18"]:
        check("weak: %s fails" % rid, rid in wf, "not in %s" % sorted(wf))
    check("weak: JD coverage < 40%%", (weak["jd"]["coverage"] or 0) < 40,
          "got %s" % weak["jd"]["coverage"])

    # ---- edge: no contact info -----------------------------------------
    edge = review(doc_from_text(load("edge-nocontact.txt")), jd)
    ef = failed_ids(edge)
    for rid in ["H4", "H7", "H9"]:
        check("edge: %s fails" % rid, rid in ef)
    check("edge: no crash, score computed",
          isinstance(edge["overall"], int) and 0 <= edge["overall"] <= 100)
    check("edge: overall between weak and strong",
          weak["overall"] < edge["overall"] < strong["overall"],
          "weak=%d edge=%d strong=%d"
          % (weak["overall"], edge["overall"], strong["overall"]))

    # ---- determinism ----------------------------------------------------
    a = json.dumps(review(doc_from_text(load("strong.txt")), jd), sort_keys=True)
    b = json.dumps(review(doc_from_text(load("strong.txt")), jd), sort_keys=True)
    check("determinism: identical JSON on repeat runs", a == b)

    # ---- empty inputs don't crash ---------------------------------------
    empty = review(doc_from_text("", source="txt"), "")
    check("empty resume: no crash", isinstance(empty["overall"], int))
    nojd = review(doc_from_text(load("strong.txt")), "")
    check("empty JD: jd section is None", nojd["jd"] is None)

    # ---- HTML/JS ID wiring ----------------------------------------------
    html_p = HERE / "web" / "resume-reviewer.html"
    js_p = HERE / "web" / "assets" / "js" / "resume-reviewer.js"
    if html_p.exists() and js_p.exists():
        html = html_p.read_text(encoding="utf-8")
        js = js_p.read_text(encoding="utf-8")
        html_ids = set(re.findall(r'id="([^"]+)"', html))
        js_ids = set(re.findall(r"getElementById\('([^']+)'\)", js)) | \
            set(re.findall(r'getElementById\("([^"]+)"\)', js))
        missing = js_ids - html_ids
        check("HTML/JS wiring: all JS-referenced IDs exist in HTML",
              not missing, "missing=%s" % sorted(missing))
    else:
        print("SKIP | HTML/JS wiring check (web files not present yet)")

    print("\n%d assertions passed." % PASS_COUNT)


if __name__ == "__main__":
    main()
