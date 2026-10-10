# TEST-LOG.md — Resume Reviewer AI

## Round 1 — full suite (2026-10-10)

**Command:** `python3 test_rules.py`

**Result: 38/38 assertions PASSED.** Breakdown:

| Group | Assertions | Result |
|---|---|---|
| strong.txt ≥ 85 overall, ≤ 3 failed, JD ≥ 50% | 3 | PASS |
| weak.txt ≤ 55 overall, ≥ 12 failed, JD < 40% | 3 | PASS |
| weak.txt: 23 specific rule IDs fail (H1,H3,H5,H6,H7,H9,H13,B1–B13,B16–B18) | 23 | PASS |
| edge-nocontact.txt: H4/H7/H9 fail, no crash, score between weak and strong | 5 | PASS |
| Determinism: identical JSON on repeat runs | 1 | PASS |
| Empty resume / empty JD: no crash, JD section omitted | 2 | PASS |
| HTML/JS wiring: all `getElementById` IDs exist in HTML | 1 | PASS |

**Fixture scores (via `demo.py --json`):**

| Fixture | Overall | Grade | Failed rules |
|---|---|---|---|
| `strong.txt` | 98/100 | Excellent | 0 |
| `weak.txt` | 8/100 | Needs work | 25 |
| `edge-nocontact.txt` | 62/100 | Fair | 5 (H4, H7, H9, H14, H15) |

**Determinism gate:** two consecutive `demo.py` runs on `weak.txt` →
SHA-256 `8bb64943…3c2b7` both times. **Byte-identical.**

**JS↔Python parity gate:** the JS engine (`web/assets/js/resume-reviewer.js`,
run under node) and the Python engine (`rules_engine.py`) produce
**byte-identical JSON** (overall, rule_score, failed IDs, manual IDs,
JD coverage) on all three fixtures. The engines are safe to evolve in
parallel — `test_rules.py` re-checks parity on every run.

**Syntax gates:** `node --check web/assets/js/resume-reviewer.js` clean;
`python3 -m py_compile rules_engine.py demo.py test_rules.py app.py` clean.

## Bugs found and fixed during testing

1. **H10 false positive** — `m.count("/") < 3` rejected valid
   `linkedin.com/in/name` URLs (2 slashes). Removed the bogus check; the
   regex already validates the format.
2. **H14 header sprawl** — fixed 10-line header window counted the SUMMARY
   section as header. Header now ends at the first ALL-CAPS section heading
   (scan starts at line 3 so an ALL-CAPS name isn't mistaken for one).
3. **B7 false positive** — stemmer reduced "Developed" → "develop" and
   flagged past-tense bullets. B7 now matches only true present-tense forms
   (base + 3rd-person: manage/manages/…) on the raw first word.
4. **Date-range regex** — `01/2021 – 12/2021` failed because the end-year
   group couldn't skip the `12/` month prefix. Added optional `(?:\d{1,2}/)?`.
5. **B7 block splitting** — experience sections without blank lines made the
   whole section one block, so a current job's "Present" masked past-job
   tense errors. B7 now anchors on each date-range line and inspects the
   ~6 lines beneath it.

## Edge cases verified (no crash, sensible output)

- Empty resume text → score computed, most rules fail with clear messages.
- Empty/missing JD → JD section omitted, score = rules only.
- DOCX/TXT without font or image metadata → H2/H12/B14 report "manual"
  with tips instead of guessing.
- All-CAPS name ("JOHN DOE") → H1 fails (asks for Title Case).
- Weak fixture exercises: 3-page length, out-of-order dates, mixed bullet
  markers, present tense in past jobs, buzzwords, misspellings, table/chart
  artifacts, repeated contact info, missing skills section.

## Not covered by automation (manual QA recommended before deploy)

- PDF.js extraction on a real multi-column PDF (font sizes, image count).
- mammoth.js extraction on a real .docx (tables, headers/footers).
- The FormSubmit notification POST (requires the one-time activation click
  on `ynpreetinusa@gmail.com` first).
- Visual check of the score ring and rule cards at 390px mobile width.
