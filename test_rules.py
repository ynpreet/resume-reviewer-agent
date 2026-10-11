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

    # ---- B19: keyword stuffing (conditional rule) ---------------------------
    stuff_txt = (
        "John Doe\n"
        "john.doe@example.com | 555-0100 | linkedin.com/in/johndoe | Boston, MA\n"
        "Summary: Python, SQL, AWS, Azure, GCP, Databricks, Spark, Kafka, ML, AI,\n"
        "leadership, communication, healthcare, finance.\n"
        "Experience:\n"
        "Data Analyst, Acme Corp, 2020 - 2024\n"
        "- Wrote reports and attended meetings.\n"
        "- Helped the team with various tasks.\n"
        "Education: B.S. Something, 2020\n"
    )
    stuff = review(doc_from_text(stuff_txt), jd)
    sf = failed_ids(stuff)
    check("B19: fires on keyword-stuffed resume", "B19" in sf,
          "failed=%s" % sorted(sf))
    b19_detail = next(r["detail"] for r in stuff["failed"] if r["id"] == "B19")
    check("B19: detail names the evidence ratio",
          "Only" in b19_detail and "matched skills" in b19_detail, b19_detail)
    check("B19: unsubstantiated skills listed",
          len(stuff["jd"]["unsubstantiated"]) >= 5,
          "got %d" % len(stuff["jd"]["unsubstantiated"]))
    check("B19: does not fire on strong resume",
          "B19" not in failed_ids(strong),
          "failed=%s" % sorted(failed_ids(strong)))
    check("B19: no JD means no B19",
          "B19" not in failed_ids(review(doc_from_text(stuff_txt), "")))

    # ---- B20: garbled-text detection (conditional rule) ---------------------
    garb_txt = (
        "J ane D oe P yth on D ata E ng ineer Experien ce: 20 22 - 20 26 "
        "B uilt a P ySp ark pip eline pro cess ing 10 mil lion re cords da ily "
        "and re duc ed run time fr om 8 ho urs to 2 ho urs. "
        "S kills: P yth on, S QL, A WS."
    )
    garb = review(doc_from_text(garb_txt), jd)
    gf = failed_ids(garb)
    check("B20: fires on garbled text", "B20" in gf,
          "failed=%s" % sorted(gf))
    b20_detail = next(r["detail"] for r in garb["failed"] if r["id"] == "B20")
    check("B20: detail names the fragment count",
          "single-letter fragments" in b20_detail, b20_detail)
    check("B20: does not fire on strong resume",
          "B20" not in failed_ids(strong),
          "failed=%s" % sorted(failed_ids(strong)))
    check("B20: does not fire on clean short text",
          "B20" not in failed_ids(review(doc_from_text("Jane Doe\nData Engineer"), "")))

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
