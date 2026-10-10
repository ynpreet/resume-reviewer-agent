# Resume Reviewer AI — An Agentic AI System for Instant Resume Feedback

**Demo 9 of 9 · Agentic AI Workshop**

> **Open in Chrome (live web UI — the way to present this demo):**
>
> ```bash
> cd ~/workspace/agentic-ai-workshop/resume-reviewer
> python3 app.py
> ```
>
> Then open **http://localhost:8009/resume-reviewer.html** in Chrome, fill the
> form, and upload a resume (PDF or DOCX). The page runs the real rule engine
> in your browser — no backend, no uploads, stdlib-grade determinism. If port
> 8009 is already taken, the server says so and exits; stop the other copy
> first.
>
> Terminal fallback: `python3 demo.py fixtures/strong.txt fixtures/sample-jd.txt`
> (takes plain .txt so the CLI stays stdlib-only and offline).

**Deployed version:** `https://datawithpreet.github.io/resume-reviewer.html`
(the `web/` folder, copied as-is onto GitHub Pages — see "Deploy" below).

---

## Real-world problem, target users, market need, and differentiation

**The problem.** Preet gets asked constantly: *"Can you review my resume?"*
One-by-one reviews don't scale, and generic online checkers give vague
advice ("add more action verbs!") without checking the things hiring managers
actually reject resumes for — a missing LinkedIn, two email addresses, a
scanned PDF no ATS can read, or zero overlap with the job description's
skills.

**Target users.** Job seekers (especially data/engineering students and
early-career professionals) who want specific, fixable feedback before they
apply — and Preet, who wants every submission to reach him as a lightweight
notification instead of a DM thread.

**Market need.** Resume feedback is either expensive (coaches), slow (humans),
or shallow (keyword counters). What candidates need is a *checklist with
teeth*: the concrete header/body rules recruiters apply in the first 7
seconds, plus a targeted answer to "does my resume match *this* job
description?"

**Differentiation.** **Resume Reviewer AI** is an *agentic* system, not a
linter. One orchestrator plans the review, calls tools to extract and
inspect, and works the full loop: **ingest → extract → verify → score →
explain → notify**. Its signature moves: (1) it grades against 33 explicit,
editable hiring-manager rules instead of vibes; (2) it runs a
job-description skill-match so feedback is *targeted to the role*, not
generic; (3) it notifies Preet on every submission with metadata only —
the resume itself never leaves the visitor's browser.

---

## Meaningful Agentic AI functionality

**Why an agent — not a checklist PDF, not a chatbot:**

| | Checklist PDF | Chatbot | Resume Reviewer AI (agentic) |
|---|---|---|---|
| Reads | — (you do the work) | Can't parse files | Extracts text from PDF/DOCX itself |
| Checks | You eyeball 33 rules | Summarizes text | Runs all 33 rules programmatically |
| Targets | Generic advice | Generic advice | JD skill-match: missing skills per role |
| Explains | Static tips | Vague | Each failure cites what was seen + the fix |
| Acts | — | — | Scores, grades, notifies Preet on submit |
| Adapts | — | — | Graceful degradation: scanned PDFs, DOCX without font data, empty JD |

The thesis in one line: **ingest → extract → verify → score → explain →
notify, in one workflow** — it doesn't just list rules, it *applies* them
to your file, proves what it found, and closes the loop with a human.

---

## Project scope, inputs, outputs, constraints, success criteria, and definition of done

**Scope.** A deterministic rule engine (33 rules) + JD skill-match, shipped
two ways: a static web app (the product, on GitHub Pages) and a stdlib CLI
(for the workshop/test harness). Both share the same rule semantics —
verified byte-identical on fixtures (see TEST-LOG.md).

**Inputs.**

- Web: full name (required), LinkedIn URL (required, format-validated),
  job description text (required), resume file — PDF or DOCX (required).
- CLI: resume as `.txt`, JD as `.txt` (PDF/DOCX parsing is web-only).

**Outputs.**

- Overall score 0–100 (70% rules + 30% JD skill coverage) with a grade
  (Excellent / Strong / Fair / Needs work).
- Per-section breakdown: Header x/15, Body & Formatting x/18, JD skill %.
- Every failed rule with *what was seen* and *the specific fix*.
- Manual checks (photo, font size on non-PDF uploads) flagged for human eyes.
- Missing JD skills + frequent JD keywords absent from the resume.
- A FormSubmit email to Preet per submission (metadata only).

**Constraints.** Zero backend, zero cost, zero API keys. Web app runs
entirely client-side; resume bytes never leave the browser. CLI is stdlib
only and fully offline. Fixed CURRENT_YEAR (2026), sorted iteration →
deterministic scores.

**Success criteria.** Strong fixture ≥ 85, weak fixture ≤ 55 with ≥ 12
rules failing, edge fixtures never crash, JS↔Python engines byte-identical,
all 38 test assertions green.

**Definition of done.** All four files run green (`demo.py` on 3 fixtures,
`test_rules.py` 38/38, `node --check`, `py_compile`); README carries all 10
checklist sections; TEST-LOG.md records the gates passing.

---

## Documented single-agent or multi-agent workflow

**Single-agent workflow** — one orchestrator + five capability tool groups.
Deliberately **not** five separate agents: one decision-maker, one audit
trail, one score.

```
                    ┌─────────────────────────────────┐
                    │        ORCHESTRATOR (1 agent)     │
                    │  plan → act → observe → replan  │
                    │  (ingest → extract → verify →   │
                    │   score → explain → notify)     │
                    └───────────────┬─────────────────┘
        ┌───────────────┬───────────┼───────────┬───────────────┐
        ▼               ▼           ▼           ▼               ▼
   (A) Ingest      (B) Extract   (C) Verify  (D) Explain    (E) Notify
   ┌──────────┐   ┌────────┐   ┌─────────┐   ┌──────────┐   ┌──────────┐
   │validate_ │   │pdf.js_ │   │run_33_  │   │score_   │   │formsubmit│
   │inputs    │   │extract │   │rules    │   │report   │   │_post    │
   │check_    │   │mammoth_│   │jd_skill │   │render_  │   └──────────┘
   │file_type │   │extract │   │_match  │   │results  │
   │check_    │   │detect_ │   │grade    │   │suggest_ │
   │file_size │   │scanned │   └─────────┘   │fixes    │
   └──────────┘   └────────┘                 └──────────┘
```

**The five capabilities:**

- **(A) Ingest & validate** — name present, LinkedIn URL matches
  `linkedin.com/in/...`, JD non-trivial, file is PDF/DOCX; >5MB warns but
  proceeds; scanned/image PDFs are rejected with a clear message instead of
  scoring garbage.
- **(B) Extract** — PDF.js gives text + line layout + font sizes + embedded
  image count; mammoth gives DOCX text. Layout-aware rules (name
  prominence, photo detection, font size) degrade to "manual check" when the
  source can't provide the signal — the agent says what it *couldn't*
  verify instead of guessing.
- **(C) Verify** — all 33 rules run (see the full list below), then the JD
  skill-match: a ~90-term skill lexicon (data-engineering heavy) is matched
  against the JD, and each JD skill is checked against the resume.
- **(D) Explain** — score = 70% rules + 30% JD coverage; every failure
  prints *what was seen* ("Found 2 emails: …") and *the fix* ("Keep one
  email…"); missing JD skills are listed with the "never invent skills"
  honesty rule.
- **(E) Notify** — fire-and-forget POST of metadata only (name, LinkedIn,
  timestamp, score, JD title) to FormSubmit → Preet's inbox. Best-effort:
  a notification failure never blocks the user's report.

---

## Working prototype evidence, source code, and setup instructions

### Setup — static web app preview (recommended for presenting)

```bash
cd ~/workspace/agentic-ai-workshop/resume-reviewer
python3 app.py
```

Open **http://localhost:8009/resume-reviewer.html** in Chrome. Fill the
form (paste `fixtures/sample-jd.txt` into the JD box, upload any PDF
resume), click **Review my resume**, and watch the score ring, the
per-section bars, and the failed-rule cards render. Fully client-side —
open DevTools Network tab and confirm: the resume file is never uploaded.

### Terminal fallback

```bash
python3 demo.py fixtures/strong.txt fixtures/sample-jd.txt
python3 demo.py fixtures/weak.txt fixtures/sample-jd.txt --json
```

Same engine, printed in the terminal. Deterministic — byte-identical on
every run (fixed CURRENT_YEAR, sorted iteration).

### Files

- `web/resume-reviewer.html` — the product page (form + results)
- `web/assets/css/resume-reviewer.css` — black-and-white editorial styling
  matching datawithpreet.github.io
- `web/assets/js/resume-reviewer.js` — rule engine (mirrors
  `rules_engine.py`) + PDF/DOCX extraction + UI + FormSubmit notify
- `rules_engine.py` — shared Python rule engine (importable; CLI-tested)
- `demo.py` — stdlib CLI (`resume.txt` + `jd.txt` → printed report)
- `app.py` — localhost preview server for `web/` (port 8009)
- `fixtures/` — `strong.txt`, `weak.txt`, `edge-nocontact.txt`,
  `sample-jd.txt`
- `test_rules.py` — 38-assertion suite (fixtures + determinism + HTML/JS
  ID wiring)
- `TEST-LOG.md`, `RUBRIC.md`, `CHECKLIST.md`, `requirements.txt`

### Deploy (for the website step — not done here)

1. Copy `web/resume-reviewer.html` → repo root as `resume-reviewer.html`,
   `web/assets/` → repo `assets/` (merge with existing).
2. Push to `datawithpreet/datawithpreet.github.io` on `main`.
3. Add the 9th project card on `demos.html` linking to `/resume-reviewer.html`.
4. **FormSubmit activation (one-time):** the first real submission triggers
   an activation email to `ynpreetinusa@gmail.com` — click it once, or
   notifications stay queued.

### Keeping the two engines in sync

`rules_engine.py` (Python) and `web/assets/js/resume-reviewer.js` (JS)
implement the same 33 rules with the same thresholds. When editing:

1. Change the Python engine first.
2. Mirror the change in the JS engine (same rule IDs, same regexes, same
   thresholds — the lexicons are laid out in the same order).
3. Run `python3 test_rules.py` (includes the JS↔Python parity check via
   node) — all 38 must pass.

### Speaker notes (5-minute walkthrough)

1. **Hook (30s):** "Preet gets asked for resume reviews constantly. A
   checklist PDF doesn't scale and chatbots can't read your file. Watch an
   agent do the whole job."
2. **Ingest (45s):** Fill the form with a real resume. Point at the privacy
   note: "the file never leaves this tab — open the Network tab and check."
3. **Verify (1m30s):** Submit. Walk the score ring and one failed rule:
   read *what was seen* and *the fix* aloud. "It doesn't say 'improve your
   summary' — it says you have two emails and which one looks unprofessional."
4. **JD match (1m):** Show the missing-skills chips. "Generic checkers can't
   do this — the feedback is *for this job description*." Read the honesty
   line: "add the ones you truly have — never invent skills."
5. **Notify + honesty (45s):** "Preet just got an email — name, LinkedIn,
   score. Not the resume. That's the privacy design." Close with: "33 rules,
   all editable — Preet's actual checklist, not vibes."

Anticipated questions:

- *"Why not use an LLM?"* — Determinism and cost: the same resume scores
  the same every time (TEST-LOG.md proves it), it runs free on GitHub
  Pages forever, and every suggestion cites the exact evidence.
- *"What about scanned PDFs?"* — Detected and refused with a clear message
  rather than scored — the agent won't grade garbage.
- *"Can Preet change the rules?"* — Yes: they're a numbered list in
  `rules_engine.py` / the JS file, each with its check and suggestion text.
  Edit, re-run `test_rules.py`.

---

## Functional and end-to-end testing, realistic scenarios, failure cases, reliability, and human oversight

**Realistic scenarios (end to end).** Strong resume → 98/100 Excellent, zero
failed rules, 92% JD coverage. Weak resume → 8/100, 25 failed rules, each
with evidence + fix. No-contact-info resume → H4/H7/H9 fail cleanly, no
crash, sensible mid score.

**Failure cases the demo handles:**

- **Scanned/image PDF.** `has_text_layer` false (< 50 chars extracted) →
  refused with "export a real PDF/DOCX with selectable text" instead of a
  fake score. The agent never grades garbage.
- **>5MB file.** Warns but proceeds (large PDFs parse fine; the warning
  sets expectations).
- **Invalid LinkedIn URL / empty JD / missing file.** Inline form errors;
  submit is blocked before any work starts.
- **DOCX without font/image data.** Layout rules (H2, H12, B14) report
  "manual" with the tip, instead of guessing — honest degradation.
- **Empty resume / empty JD.** No crash; JD section omitted when no JD.
- **Notification failure.** FormSubmit POST is fire-and-forget; a network
  failure never blocks the user's report.

**Reliability gate.** `TEST-LOG.md` records: 38/38 assertions green,
JS↔Python byte-identical on all fixtures, `node --check` clean,
`py_compile` clean, determinism (repeat runs identical JSON).

**Human oversight.** Preet owns the rules list (edit anytime); every
submission notifies him with metadata; "manual" checks explicitly ask for
human eyes; the "never invent skills" line is printed on every report.

---

## Focus, feasibility, and avoidance of unnecessary complexity

One orchestrator, four capability tool groups, one shared rule engine —
stdlib Python + vanilla JS. Deliberately *not* built:

- **No LLM.** Deterministic rules beat vibes for checklists: same file,
  same score, every time, at zero cost.
- **No backend.** GitHub Pages serves static files; FormSubmit handles the
  one outbound email. Nothing to host, nothing to pay for, nothing that
  can leak resumes.
- **No multi-agent swarm.** Extraction, verification, explanation, and
  notification share one document model — four agents would need a fifth
  to coordinate them.
- **No ATS black box.** The checks are transparent and cited per rule; a
  student can read all 33 in one sitting.

Feasibility: ~700 lines of Python a student can read end to end, and the
web app is three static files. The shape transfers directly to production:
swap FormSubmit for a real intake queue, add Preet's real rules.

---

## Interdisciplinary team roles and division of labor

| Role | Owns in this demo | Concrete component |
|---|---|---|
| **Domain researcher** | Hiring-manager rules | The 33 rules: what each checks, why it matters, the fix text (Preet's checklist, encoded) |
| **Agent engineer** | Orchestrator + capabilities | Ingest→extract→verify→explain→notify loop, graceful degradation, notify fire-and-forget |
| **Data engineer** | Extraction + JD matching | PDF.js/DOCX text+layout extraction, skill lexicon, JD coverage math |
| **UX / storyteller** | The candidate narrative | Score ring, per-rule evidence+fix cards, privacy-by-design copy, speaker notes |
| **QA** | Determinism + parity gates | 38-assertion suite, JS↔Python byte-identical gate, fixture trio, TEST-LOG.md |

---

## Limitations, risks, and responsible AI (ethics, privacy, security, safety)

**Privacy by design (in the product, not just the README):**

- The resume file is parsed with PDF.js/mammoth **in the visitor's
  browser** — it is never uploaded, posted, or logged anywhere. The only
  network call is the FormSubmit metadata POST (name, LinkedIn, timestamp,
  score, JD title).
- The UI states this plainly next to the form, and the footer repeats it.

**Honesty rules (printed in the product):**

- Every failed rule cites *what was seen* — no generic advice.
- Missing JD skills carry the line: "add the ones you truly have — never
  invent skills."
- "Manual" checks say what couldn't be verified instead of guessing.
- Scanned PDFs are refused, not scored.

**Data honesty — what's real vs what's a demo:**

| In the demo | In a real deployment |
|---|---|
| 33 drafted rules (Preet's placeholders) | Preet's real 33 rules, tuned from his reviews |
| Fixture .txt resumes (synthetic) | Visitors' real PDF/DOCX uploads |
| FormSubmit free tier for notifications | FormSubmit or a real intake queue/CRM |
| Skill lexicon (~90 terms, data-heavy) | Expanded lexicon and/or role-specific packs |

**Risks.** Rule-based feedback can feel harsh — mitigated by the grade
framing and fix-first copy ("fix the failed rules top-down"). A wrong rule
is worse than no rule — mitigated by Preet owning the editable list and
the per-rule evidence display. FormSubmit free tier has submission limits —
fine for a demo; swap later.

---

## Practical value, adoption path, and measurable outcomes

**Practical value.** Candidates get specific, fixable feedback in seconds
("two emails — drop CoolDude1998@yahoo.com") instead of waiting days for a
human. Preet gets a notification per submission instead of DM chaos — a
pipeline, not a pile.

**Adoption path.** 1) Preet replaces the drafted rules with his real
checklist (same format). 2) Deploy `web/` to GitHub Pages + 9th demos card.
3) Click the one-time FormSubmit activation email. 4) Later: role-specific
rule packs (SDE vs data vs PM), resume-version diffing ("re-run and watch
the score move" is already the UX).

**Measurable outcomes.** Today: 38/38 tests green, JS↔Python byte-identical,
strong 98 / weak 8 separation on fixtures. In production: submissions/week,
score distribution, and which rules fail most (tells Preet what to teach).

---

## The 33 rules (full list — edit freely)

**Header (15).** H1 Name present · H2 Name is prominent (largest text) ·
H3 No "Resume"/"CV" title line · H4 Email present · H5 Single email only ·
H6 Professional email (no nicknames/birth years) · H7 Phone present ·
H8 Single phone only · H9 LinkedIn URL present · H10 LinkedIn URL valid
format · H11 Location as City, ST · H12 No photo · H13 No street address ·
H14 Compact header (contact block ≤ 8 lines) · H15 Portfolio/GitHub link
(tech resumes).

**Body & Formatting (18).** B1 Length: one page (two OK at 10+ yrs exp) ·
B2 Reverse-chronological · B3 ≥70% bullets start with action verbs ·
B4 ≥40% bullets quantified · B5 No first-person pronouns · B6 Consistent
date format · B7 Tense consistent (past jobs = past tense) · B8 One bullet
marker style · B9 Standard section headings · B10 Skills section (5+) ·
B11 No buzzword stuffing · B12 Spelling (common misspellings) ·
B13 ATS-friendly layout (no tables/text boxes) · B14 Readable fonts
(1–3 families, ≥8pt) · B15 Text selectable (not scanned) · B16 Contact info
not repeated in body · B17 Education complete (degree + school + year) ·
B18 No chart/graphic artifacts.

**JD match.** ~90-term skill lexicon matched against the JD, then checked
against the resume → coverage % + missing skills + missing frequent
keywords. Score = 70% rules + 30% JD coverage.

---

*Built for the Agentic AI Workshop · Demo 9 of 9*
