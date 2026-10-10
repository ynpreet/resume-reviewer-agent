#!/usr/bin/env python3
"""
Resume Reviewer AI -- agentic resume feedback (CLI).

Demo 9 of 9 - Agentic AI Workshop

An agent that reads a resume (.txt) and a job description (.txt), runs 33
hiring-manager rules (15 header + 18 body/formatting) plus a JD keyword-match
analysis, and prints a scored report with specific, fixable suggestions.

Usage:
    python3 demo.py fixtures/strong.txt fixtures/sample-jd.txt
    python3 demo.py my-resume.txt job-desc.txt --json

PDF/DOCX parsing is web-app only (web/resume-reviewer.html) -- the CLI takes
plain .txt so it stays stdlib-only and fully offline. Paste resume text into
a .txt file to use the CLI.

Deterministic: fixed CURRENT_YEAR, sorted iteration -- byte-identical
output on every run (see TEST-LOG.md).
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rules_engine import doc_from_text, review  # noqa: E402


def _print_report(rep, name):
    bar = lambda s: "█" * (s // 5) + "░" * (20 - s // 5)  # noqa: E731
    print("=" * 64)
    print("RESUME REVIEWER AI -- report for %s" % name)
    print("=" * 64)
    print("Overall score : %d/100  [%s]  (%s)"
          % (rep["overall"], bar(rep["overall"]), rep["grade"]))
    print("Rules score   : %d/100  (%d passed, %d failed, %d manual checks)"
          % (rep["rule_score"],
             sum(1 for r in rep["rules"] if r["status"] == "pass"),
             len(rep["failed"]), len(rep["manual"])))
    if rep["jd"] and rep["jd"]["coverage"] is not None:
        print("JD match      : %d%% of %d JD skills found in resume"
              % (round(rep["jd"]["coverage"]), len(rep["jd"]["jd_skills"])))
    print()

    if rep["failed"]:
        print("--- FAILED RULES (%d) ---" % len(rep["failed"]))
        for r in rep["failed"]:
            print("[%s] %s" % (r["id"], r["name"]))
            print("      What I saw: %s" % r["detail"])
            if r["suggestion"]:
                print("      Fix: %s" % r["suggestion"])
        print()
    else:
        print("No failed rules. This resume is in great shape.\n")

    if rep["jd"]:
        jd = rep["jd"]
        if jd["missing"]:
            print("--- MISSING JD SKILLS (%d) ---" % len(jd["missing"]))
            print("The job description asks for these; your resume doesn't "
                  "show them:")
            for s in jd["missing"]:
                print("  - %s" % s)
            print("  Fix: add the ones you truly have (never invent skills).")
            print()
        if jd["missing_keywords"]:
            print("--- JD KEYWORDS MISSING FROM RESUME ---")
            print(", ".join(jd["missing_keywords"]))
            print()

    if rep["manual"]:
        print("--- MANUAL CHECKS (%d) ---" % len(rep["manual"]))
        for r in rep["manual"]:
            print("[%s] %s: %s" % (r["id"], r["name"], r["detail"]))
            if r["suggestion"]:
                print("      Tip: %s" % r["suggestion"])
        print()

    print("Tip: fix the failed rules top-down, re-run, watch the score move.")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Resume Reviewer AI: 33-rule resume feedback + JD match.")
    ap.add_argument("resume", help="Resume as .txt file")
    ap.add_argument("jd", nargs="?", default="",
                    help="Job description as .txt file (optional)")
    ap.add_argument("--json", action="store_true",
                    help="Print machine-readable JSON instead of the report")
    args = ap.parse_args(argv)

    resume_text = Path(args.resume).read_text(encoding="utf-8")
    jd_text = Path(args.jd).read_text(encoding="utf-8") if args.jd else ""
    doc = doc_from_text(resume_text, source="txt")
    rep = review(doc, jd_text)

    if args.json:
        print(json.dumps(rep, indent=2, sort_keys=True))
    else:
        _print_report(rep, Path(args.resume).name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
