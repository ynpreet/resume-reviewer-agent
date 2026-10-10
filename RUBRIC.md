# RUBRIC.md — Self-score vs. the PEAAII Hackathon Judging Rubric

Scored 1–5 per criterion against `~/workspace/peaii-hackathon/judging-rubric.md`, with concrete evidence, one honest gap per criterion, and how a student could close it.

| # | Criterion (weight) | Score | Points |
|---|---|---|---|
| 1 | Problem Definition & Real-World Impact (25) | 5/5 | 25 |
| 2 | Meaningful Agentic AI Behavior (20) | 4/5 | 16 |
| 3 | Working Prototype (15) | 5/5 | 15 |
| 4 | Innovation & Creativity (15) | 4/5 | 12 |
| 5 | Presentation & Communication (15) | 5/5 | 15 |
| 6 | Responsible AI & Feasibility (10) | 5/5 | 10 |
| | **TOTAL** | | **93/100** |

---

## 1. Problem Definition & Real-World Impact — 5/5 (25 pts)

**Evidence:** A specific user (Preet, drowning in "review my resume?" DMs)
and a specific end user (job seekers who need fixable feedback before they
apply). The pain is concrete and quantified: 33 named rules, a 0–100 score,
per-rule evidence + fix. The weak fixture (8/100, 25 failed rules) reads
like a real bad resume because it was built from real rejection reasons.

**Honest gap:** The 33 rules are drafted placeholders ("assume and build on
your own") — Preet hasn't yet substituted his real checklist, so the demo
proves the *machinery*, not his actual taste.

**Close it:** Have Preet annotate 10 real resumes he reviewed, diff the
engine's verdicts against his notes, and tune the rule set until they agree
— then the demo carries his authority, not just his format.

## 2. Meaningful Agentic AI Behavior — 4/5 (20 pts)

**Evidence:** The agentic loop is real and printed: validate → extract (PDF.js
layout, fonts, images) → verify (33 rules + JD skill-match) → explain (score
+ evidence + fix per rule) → notify (FormSubmit). It adapts: scanned PDFs
are refused, DOCX degrades layout rules to "manual," empty JDs skip the JD
section. A checklist PDF can't do any of this — it requires perception,
tool use, state, and gated action.

**Honest gap:** The "planning" is a fixed 5-stage pipeline, not dynamic
planning — the orchestrator never reorders or skips stages based on what it
finds (unlike the fryer-twist replanning in Demo 8).

**Close it:** Add one adaptive branch with teeth: if the JD skill-match finds
zero JD skills, replan into "JD quality check" mode and tell the user their
*pasted JD* is the problem (too short/vague) before scoring the resume.

## 3. Working Prototype — 5/5 (15 pts)

**Evidence:** Two working front-ends on one engine: the static web app
(preview via `python3 app.py` → localhost:8009) and the stdlib CLI.
`python3 demo.py fixtures/weak.txt fixtures/sample-jd.txt` prints a full
scored report in well under a second. TEST-LOG.md proves 38/38 assertions,
JS↔Python byte-identical output, and determinism.

**Honest gap:** The web app's PDF/DOCX parsing is only exercised manually
in the browser — the automated suite covers the engine on .txt, not
PDF.js/mammoth extraction paths.

**Close it:** Add a Playwright (or manual QA script) pass: upload a known
PDF and DOCX, assert the extracted line count and the H2/H12/B14 signals
match expected values, log it in TEST-LOG.md.

## 4. Innovation & Creativity — 4/5 (12 pts)

**Evidence:** Three design choices stand out: (1) privacy as architecture —
the resume never leaves the browser, and the *notification* carries only
metadata, which turns a creepy data flow into a trust feature; (2) the JD
skill-match makes feedback role-targeted instead of generic; (3) "manual"
checks as honest degradation instead of silent guessing. Resume linters
exist; an agentic, private, JD-aware reviewer with a human notification
loop is a creative composition.

**Honest gap:** The rule engine is deterministic pattern-matching — a judge
could argue it's a "smart linter," and the agentic-ness rests on the
orchestration (ingest→notify) rather than on reasoning.

**Close it:** Add the adaptive JD-quality replan from criterion 2, and one
cross-rule inference (e.g. "B4 quantified 0% AND B3 weak verbs → lead with
the achievements section rewrite, not 12 separate fixes") to show the agent
*reasoning over* its findings, not just listing them.

## 5. Presentation & Communication — 5/5 (15 pts)

**Evidence:** The README carries the full story: 30-second setup, ASCII
architecture diagram, 5-minute speaker-notes script with anticipated
questions, the deploy runbook (including the one-time FormSubmit activation
gotcha), and the engine-sync procedure so a student team can maintain it.
The product's own copy teaches ("fix the failed rules top-down, re-run,
watch the score move").

**Honest gap:** No visuals in the repo — the score ring and rule cards only
exist in the running web app; a judge reading the repo cold sees no
screenshot.

**Close it:** Add one annotated screenshot of a scored report (strong vs
weak side by side) to the README — captured from the localhost preview.

## 6. Responsible AI & Feasibility — 5/5 (10 pts)

**Evidence:** Guardrails are *in the product*: resume bytes never leave the
browser (verifiable in DevTools), notifications carry metadata only,
scanned PDFs are refused rather than scored, "manual" checks admit what
couldn't be verified, and every report prints "never invent skills." Zero
backend, zero cost, zero API keys — feasible on GitHub Pages indefinitely.

**Honest gap:** FormSubmit is a third-party free tier: rate limits and the
manual activation step are outside our control, and metadata (name +
LinkedIn) does leave the browser by design.

**Close it:** Document the FormSubmit limits in the README deploy section
and add a fallback: if the POST fails, show Preet's contact link so the
candidate can still reach him — the loop closes even when the service
doesn't.
