#!/usr/bin/env python3
"""
Resume Reviewer AI -- shared rule engine (stdlib only).

Implements the 33 resume rules (15 header + 18 body/formatting) plus the
job-description keyword-match analysis. The same logic is mirrored in
web/assets/js/resume-reviewer.js for the static GitHub Pages app; keep the
two in sync when editing (see README section "Keeping the two engines in
sync").

Document model (dict):
    text            full extracted text (str)
    lines           non-empty lines in reading order (list[str])
    pages           page count, or estimated (int)
    has_text_layer  True unless the PDF was a scanned image (bool)
    chars_per_page  average extractable chars per page (float)
    name_font_largest  True/False/None (None = unknown, e.g. DOCX/TXT)
    images          embedded image count, or None if unknown (int|None)
    fonts           list of {"family": str, "min_size": float} or None
    source          "pdf" | "docx" | "txt"

Each rule returns {"id","section","name","status","detail","suggestion"}
status is one of "pass" | "fail" | "manual".
"manual" = the check needs human eyes (e.g. photo detection on a .txt
upload); manual checks are listed in the report but excluded from scoring.

Determinism: CURRENT_YEAR is fixed (no wall clock) so scores are stable.
"""

import re

CURRENT_YEAR = 2026

# ---------------------------------------------------------------------------
# Lexicons
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
LINKEDIN_RE = re.compile(r"linkedin\.com/in/[A-Za-z0-9_\-]+/?", re.IGNORECASE)
LOCATION_RE = re.compile(r"\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?,\s*[A-Z]{2}\b")
STREET_RE = re.compile(
    r"\b\d{1,5}\s+[A-Z][a-zA-Z]+\s+"
    r"(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|"
    r"Way|Terrace|Ter|Place|Pl|Parkway|Pkwy)\b"
    r"|\bApt\.?\s*\w*\d+|\bSuite\s+\d+|\bUnit\s+\d+",
    re.IGNORECASE,
)
SILLY_EMAIL_RE = re.compile(
    r"(sexy|hot|cool|dude|rockstar|ninja|guru|princess|queen|king|baby|babe|"
    r"gamer|playboy|thug|swag|xoxo|420|69|\d{4,})",
    re.IGNORECASE,
)
BULLET_RE = re.compile(r"^\s*[•\-\*▪‣–>]+\s+\S")
BULLET_MARKER_RE = re.compile(r"^\s*([•\-\*▪‣–>]+)\s+\S")
PRONOUN_RE = re.compile(r"(?<![A-Za-z])I(?![A-Za-z])|\b(me|my|mine|myself)\b", re.IGNORECASE)
CHART_RE = re.compile(r"[█▇▆▅▄▃▂▁■□▪▫●○]{3,}|(\|\s*){4,}")
TABLEY_RE = re.compile(r" {3,}|\t")
MISSPELLINGS = [
    "recieve", "seperate", "occured", "occurance", "managment", "experiance",
    "accomodate", "definately", "untill", "neccessary", "tommorow", "writting",
    "calender", "concious", "dissapear", "embarass", "existance", "freind",
    "grammer", "independant", "knowlege", "liason", "noticable", "persue",
    "posession", "publically", "recomend", "refering", "sucessful", "truely",
    "acheive", "beleive", "arguement", "useage", "wierd", "priviledge",
    "maintainance", "oppurtunity", "suprise",
]
BUZZWORDS = [
    "synergy", "synergies", "guru", "ninja", "rockstar", "rock star",
    "thought leader", "best-of-breed", "best of breed", "game-changer",
    "game changer", "disruptive", "move the needle", "self-starter",
]
ACTION_VERBS = {
    "achieved", "built", "led", "launched", "designed", "developed",
    "delivered", "drove", "improved", "increased", "reduced", "cut", "saved",
    "automated", "architected", "implemented", "migrated", "optimized",
    "scaled", "streamlined", "spearheaded", "transformed", "created",
    "established", "founded", "grew", "boosted", "accelerated", "negotiated",
    "partnered", "mentored", "coached", "pioneered", "engineered", "deployed",
    "shipped", "owned", "championed", "orchestrated", "revamped", "modernized",
    "consolidated", "integrated", "analyzed", "evaluated", "identified",
    "resolved", "diagnosed", "prevented", "forecast", "modeled", "tested",
    "validated", "published", "presented", "authored", "secured", "ensured",
    "audited", "monitored", "maintained", "upgraded", "refactored",
    "prototyped", "piloted", "rolled", "generated", "drove", "doubled",
    "tripled", "slashed", "decreased", "grew", "expanded", "launched",
    "crafted", "wrote", "managed", "directed", "headed", "oversaw",
}
# Present-tense verb forms (base + 3rd-person) that should not open bullets
# in *past* jobs. Past-tense (-ed) and -ing forms are intentionally absent.
PRESENT_TENSE_FORMS = {
    "manage", "manages", "lead", "leads", "develop", "develops", "build",
    "builds", "own", "owns", "drive", "drives", "oversee", "oversees",
    "direct", "directs", "head", "heads", "run", "runs", "maintain",
    "maintains", "support", "supports", "coordinate", "coordinates",
    "mentor", "mentors", "architect", "architects", "design", "designs",
    "implement", "implements", "work", "works",
}
# Section-heading patterns shared by the experience-related rules.
EXP_HEAD = r"((work\s+)?experience|work\s+history|employment(\s+history)?)"
MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep",
          "sept", "oct", "nov", "dec")

# Skill lexicon for JD matching: (canonical, [aliases]).
SKILLS = [
    ("Python", []), ("SQL", []), ("Spark", ["apache spark", "pyspark"]),
    ("Airflow", ["apache airflow"]), ("AWS", ["amazon web services"]),
    ("Azure", ["microsoft azure"]), ("GCP", ["google cloud", "google cloud platform"]),
    ("Snowflake", []), ("Databricks", []), ("dbt", []),
    ("Kafka", ["apache kafka"]), ("Docker", []), ("Kubernetes", ["k8s"]),
    ("Terraform", []), ("CI/CD", ["cicd", "continuous integration"]),
    ("Git", []), ("Linux", []), ("Machine Learning", ["ml"]),
    ("Deep Learning", []), ("TensorFlow", []), ("PyTorch", []),
    ("scikit-learn", ["sklearn"]), ("pandas", []), ("NumPy", ["numpy"]),
    ("Data Modeling", []), ("Data Warehouse", ["data warehousing"]),
    ("Data Lake", []), ("ETL", []), ("ELT", []), ("Data Pipeline", ["data pipelines"]),
    ("Streaming", ["stream processing"]), ("Real-time", ["realtime"]),
    ("Data Governance", []), ("Data Quality", []),
    ("Looker", []), ("Tableau", []), ("Power BI", ["powerbi"]),
    ("A/B Testing", ["ab testing"]), ("Statistics", ["statistical"]),
    ("NLP", ["natural language processing"]), ("LLMs", ["llm", "large language model"]),
    ("RAG", ["retrieval augmented generation"]), ("MLOps", []),
    ("Feature Engineering", []), ("Data Visualization", []),
    ("Agile", []), ("Scrum", []), ("Jira", []),
    ("REST API", ["rest", "restful"]), ("GraphQL", []), ("Microservices", []),
    ("PostgreSQL", ["postgres"]), ("MySQL", []), ("MongoDB", ["mongo"]),
    ("Redis", []), ("Elasticsearch", []), ("Redshift", []), ("BigQuery", []),
    ("Hadoop", []), ("Hive", []), ("Flink", []),
    ("Lambda", ["aws lambda"]), ("S3", []), ("EMR", []), ("Glue", ["aws glue"]),
    ("Java", []), ("Scala", []), ("Go", ["golang"]), ("JavaScript", []),
    ("TypeScript", []), ("Bash", ["shell scripting"]), ("R", []),
    ("Data Analysis", []), ("Data Science", []), ("Analytics", []),
    ("Business Intelligence", ["bi"]), ("KPI", ["kpis"]),
    ("Forecasting", []), ("Optimization", ["optimisation"]),
    ("Automation", []), ("Testing", []), ("Debugging", []),
    ("Documentation", []), ("Mentoring", []), ("Leadership", []),
    ("Communication", []), ("Project Management", []),
    ("Monitoring", []), ("Datadog", []), ("Grafana", []),
    ("Incident Management", ["incident response", "on-call", "oncall"]),
]

STOPWORDS = {
    "the", "and", "for", "with", "you", "your", "will", "have", "has",
    "are", "our", "that", "this", "from", "they", "their", "who", "what",
    "about", "into", "over", "under", "between", "through", "during",
    "including", "such", "more", "most", "other", "some", "than", "then",
    "them", "these", "those", "when", "where", "which", "while", "been",
    "being", "also", "both", "each", "very", "just", "like", "well",
    "work", "working", "team", "role", "candidate", "looking", "join",
    "help", "able", "plus", "across", "within", "using", "used", "use",
    "new", "day", "per", "etc", "including",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lines(doc):
    return doc.get("lines", [])


def _is_heading_line(line):
    """ALL-CAPS short line like SUMMARY / WORK HISTORY (not a name line)."""
    s = line.strip().strip("*").strip()
    if not s or len(s) > 30 or re.search(r"\d", s):
        return False
    words = s.split()
    if not 1 <= len(words) <= 4:
        return False
    return s == s.upper() and any(c.isalpha() for c in s)


def _header(doc):
    """Contact block: lines before the first section heading (max 10).

    The scan starts at line 3 so an ALL-CAPS name (e.g. 'JOHN DOE') is not
    mistaken for a heading.
    """
    lines = _lines(doc)
    cut = len(lines)
    for i in range(2, min(len(lines), 12)):
        if _is_heading_line(lines[i]):
            cut = i
            break
    return lines[:min(cut, 10)]


def _body_lines(doc):
    return _lines(doc)[10:]


def _emails(text):
    return sorted(set(EMAIL_RE.findall(text)))


def _phones(text):
    found = set()
    for m in PHONE_RE.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        if 10 <= len(digits) <= 11:
            found.add(digits[-10:])
    return sorted(found)


def _looks_like_name(line):
    s = line.strip().strip("*").strip()
    if not s or re.search(r"\d", s):
        return False
    if s.lower() in ("resume", "cv", "curriculum vitae"):
        return False
    parts = s.split()
    if not 2 <= len(parts) <= 4:
        return False
    for p in parts:
        p = p.strip(",.")
        if not p or not p[0].isupper():
            return False
        if sum(1 for c in p if c.isupper()) > 2:
            return False
        if not all(c.isalpha() or c in ".'-" for c in p):
            return False
    return True


def _find_name(doc):
    for line in _lines(doc)[:4]:
        if _looks_like_name(line):
            return line.strip()
    return None


def _bullets(doc):
    return [l for l in _lines(doc) if BULLET_RE.match(l)]


def _section_lines(doc, *headings):
    """Lines belonging to sections whose heading matches any pattern."""
    lines = _lines(doc)
    pat = re.compile(r"^\s*(" + "|".join(headings) + r")\b", re.IGNORECASE)
    any_heading = re.compile(
        r"^\s*(experience|education|skills|summary|projects|certifications|"
        r"awards|publications|contact)\b", re.IGNORECASE)
    out, capture = [], False
    for l in lines:
        if pat.match(l):
            capture = True
            continue
        if any_heading.match(l):
            capture = False
            continue
        if capture and l.strip():
            out.append(l)
    return out


def _date_ranges(text):
    """Extract (start_year, end_year|None for present) tuples."""
    mon = "|".join(MONTHS)
    ranges = []
    pat_full = re.compile(
        r"(?:(?:" + mon + r")[a-z]*\s+)?\b((?:19|20)\d{2})\b\s*[–—\-]\s*"
        r"(?:(?:" + mon + r")[a-z]*\s+)?(?:\d{1,2}/)?"
        r"\b((?:19|20)\d{2}|present|current)\b",
        re.IGNORECASE)
    for m in pat_full.finditer(text):
        start = int(m.group(1))
        end_raw = m.group(2).lower()
        end = None if end_raw in ("present", "current") else int(end_raw)
        ranges.append((start, end))
    return ranges


def _stem_verb(word):
    w = word.lower()
    if w in ACTION_VERBS:
        return w
    for suf in ("ing", "ed", "es", "s"):
        if w.endswith(suf) and len(w) > len(suf) + 2:
            cand = w[: -len(suf)]
            if cand in ACTION_VERBS:
                return cand
    return w


def _first_word(line):
    m = re.search(r"[A-Za-z]+", line)
    return m.group(0) if m else ""


def _rule(rid, section, name, status, detail, suggestion=""):
    return {"id": rid, "section": section, "name": name,
            "status": status, "detail": detail, "suggestion": suggestion}


# ---------------------------------------------------------------------------
# Header rules H1-H15
# ---------------------------------------------------------------------------

def h1_name_present(doc):
    name = _find_name(doc)
    if name:
        return _rule("H1", "Header", "Name present", "pass",
                     "Found name: %s" % name)
    first = _lines(doc)[0].strip() if _lines(doc) else "(empty)"
    return _rule("H1", "Header", "Name present", "fail",
                 "First line doesn't look like a name: '%s'" % first[:60],
                 "Put your full name alone on the first line, in Title Case "
                 "(e.g. 'Priya Sharma').")


def h2_name_prominent(doc):
    v = doc.get("name_font_largest")
    if v is True:
        return _rule("H2", "Header", "Name is prominent", "pass",
                     "Name is the largest text on page 1.")
    if v is None:
        return _rule("H2", "Header", "Name is prominent", "manual",
                     "Couldn't verify font size from this upload.",
                     "Make your name the single largest text on the page "
                     "(16-20pt) so recruiters see it first.")
    return _rule("H2", "Header", "Name is prominent", "fail",
                 "Something else on page 1 is larger than your name.",
                 "Make your name the single largest text on the page "
                 "(16-20pt) so recruiters see it first.")


def h3_no_resume_title(doc):
    for l in _lines(doc)[:6]:
        s = l.strip().lower().strip("*")
        if s in ("resume", "cv", "curriculum vitae") or \
                re.match(r"^(resume|cv)\s+of\b", s):
            return _rule("H3", "Header", "No 'Resume' title", "fail",
                         "Found a title line: '%s'" % l.strip()[:40],
                         "Delete it — the file name says it's a resume; use "
                         "the space for your name and contact info.")
    return _rule("H3", "Header", "No 'Resume' title", "pass",
                 "No wasted 'Resume'/'CV' title line.")


def h4_email_present(doc):
    emails = _emails(" ".join(_header(doc)))
    if emails:
        return _rule("H4", "Header", "Email present", "pass",
                     "Found: %s" % emails[0])
    return _rule("H4", "Header", "Email present", "fail",
                 "No email address in the header.",
                 "Add a professional email address under your name.")


def h5_single_email(doc):
    emails = _emails(" ".join(_header(doc)))
    if not emails:
        return _rule("H5", "Header", "Single email only", "manual",
                     "No email found (see H4).")
    if len(emails) == 1:
        return _rule("H5", "Header", "Single email only", "pass",
                     "Exactly one email address.")
    return _rule("H5", "Header", "Single email only", "fail",
                 "Found %d emails: %s" % (len(emails), ", ".join(emails)),
                 "Keep one email — two inboxes means missed messages.")


def h6_email_professional(doc):
    emails = _emails(" ".join(_header(doc)))
    if not emails:
        return _rule("H6", "Header", "Professional email", "manual",
                     "No email found (see H4).")
    local = emails[0].split("@")[0]
    if SILLY_EMAIL_RE.search(local):
        return _rule("H6", "Header", "Professional email", "fail",
                     "Email looks unprofessional: %s" % emails[0],
                     "Use firstname.lastname@domain — never nicknames, "
                     "birth years, or numbers like 420/69.")
    return _rule("H6", "Header", "Professional email", "pass",
                 "Email looks professional.")


def h7_phone_present(doc):
    phones = _phones(" ".join(_header(doc)))
    if phones:
        return _rule("H7", "Header", "Phone present", "pass",
                     "Found phone ending in %s" % phones[0][-4:])
    return _rule("H7", "Header", "Phone present", "fail",
                 "No phone number in the header.",
                 "Add one phone number so recruiters can reach you quickly.")


def h8_single_phone(doc):
    phones = _phones(" ".join(_header(doc)))
    if not phones:
        return _rule("H8", "Header", "Single phone only", "manual",
                     "No phone found (see H7).")
    if len(phones) == 1:
        return _rule("H8", "Header", "Single phone only", "pass",
                     "Exactly one phone number.")
    return _rule("H8", "Header", "Single phone only", "fail",
                 "Found %d phone numbers." % len(phones),
                 "Keep one phone number — one clear way to call you.")


def h9_linkedin_present(doc):
    if "linkedin.com/in/" in doc["text"].lower():
        return _rule("H9", "Header", "LinkedIn present", "pass",
                     "LinkedIn profile link found.")
    return _rule("H9", "Header", "LinkedIn present", "fail",
                 "No linkedin.com/in/ link found.",
                 "Add your LinkedIn URL (linkedin.com/in/yourname) — "
                 "recruiters check it before they call.")


def h10_linkedin_valid(doc):
    ms = LINKEDIN_RE.findall(doc["text"])
    if not ms:
        return _rule("H10", "Header", "LinkedIn URL valid", "manual",
                     "No LinkedIn link found (see H9).")
    bad = [m for m in ms if " " in m]
    if bad:
        return _rule("H10", "Header", "LinkedIn URL valid", "fail",
                     "LinkedIn URL looks broken: %s" % bad[0],
                     "Use the clean form: linkedin.com/in/yourname "
                     "(no spaces, no extra path).")
    return _rule("H10", "Header", "LinkedIn URL valid", "pass",
                 "LinkedIn URL format looks good: %s" % ms[0])


def h11_location_present(doc):
    if LOCATION_RE.search(" ".join(_header(doc))):
        return _rule("H11", "Header", "Location present", "pass",
                     "Found City, ST location.")
    return _rule("H11", "Header", "Location present", "fail",
                 "No 'City, ST' location in the header.",
                 "Add 'City, ST' (e.g. Boston, MA) — recruiters filter by "
                 "location; never put your full street address.")


def h12_no_photo(doc):
    imgs = doc.get("images")
    if imgs is None:
        return _rule("H12", "Header", "No photo", "manual",
                     "Couldn't inspect images from this upload.",
                     "US resumes don't include photos — remove yours if "
                     "present (it also breaks some ATS parsers).")
    if imgs == 0:
        return _rule("H12", "Header", "No photo", "pass",
                     "No embedded images detected.")
    return _rule("H12", "Header", "No photo", "fail",
                 "Detected %d embedded image(s) — likely a photo." % imgs,
                 "Remove the photo: US resumes don't include one, and it "
                 "can break ATS parsing.")


def h13_no_street_address(doc):
    m = STREET_RE.search(" ".join(_header(doc)))
    if m:
        return _rule("H13", "Header", "No street address", "fail",
                     "Found address-like text: '%s'" % m.group(0)[:40],
                     "Drop the street address — 'City, ST' is enough and "
                     "safer. Street addresses waste prime header space.")
    return _rule("H13", "Header", "No street address", "pass",
                 "No street address in header.")


def h14_header_compact(doc):
    header = " ".join(_header(doc))
    signals = sum([
        bool(EMAIL_RE.search(header)),
        bool(_phones(header)),
        "linkedin.com/in/" in header.lower(),
        bool(LOCATION_RE.search(header)),
    ])
    n = len(_header(doc))
    if signals >= 3 and n <= 8:
        return _rule("H14", "Header", "Compact header", "pass",
                     "Contact block fits in %d lines." % n)
    return _rule("H14", "Header", "Compact header", "fail",
                 "Header sprawls over %d lines." % n,
                 "Compress name + contact info into at most 8 lines — "
                 "every line above the fold should earn its place.")


def h15_portfolio_tech(doc):
    text = doc["text"].lower()
    is_tech = bool(re.search(
        r"\b(software|data|engineer|developer|github|python|java|machine learning)\b",
        text))
    has_portfolio = bool(re.search(r"github\.com/[A-Za-z0-9_\-]+/?(\s|$)",
                                   doc["text"]))
    if has_portfolio:
        return _rule("H15", "Header", "Portfolio/GitHub link", "pass",
                     "GitHub/portfolio link found.")
    if is_tech:
        return _rule("H15", "Header", "Portfolio/GitHub link", "fail",
                     "Tech resume without a GitHub/portfolio link.",
                     "Add github.com/yourname — hiring managers click it "
                     "before the phone screen.")
    return _rule("H15", "Header", "Portfolio/GitHub link", "manual",
                 "Non-technical resume.",
                 "Optional: a portfolio site link helps for design/writing "
                 "roles.")


# ---------------------------------------------------------------------------
# Body / formatting rules B1-B18
# ---------------------------------------------------------------------------

def b1_length_ok(doc):
    pages = doc.get("pages", 1)
    years = _years_experience(doc)
    if pages <= 1:
        return _rule("B1", "Body & Formatting", "Length: one page", "pass",
                     "Fits on one page.")
    if pages == 2 and years >= 10:
        return _rule("B1", "Body & Formatting", "Length: one page", "pass",
                     "Two pages acceptable with ~%d years experience."
                     % years)
    if pages == 2:
        return _rule("B1", "Body & Formatting", "Length: one page", "fail",
                     "Two pages with ~%d years experience." % years,
                     "Cut to one page: drop older roles, trim bullets to "
                     "your 3 strongest per job.")
    return _rule("B1", "Body & Formatting", "Length: one page", "fail",
                 "%d pages detected." % pages,
                 "Resumes over 2 pages get skimmed, not read. Cut ruthlessly "
                 "— one page per 10 years is the norm.")


def _years_experience(doc):
    ranges = _date_ranges(doc["text"])
    if not ranges:
        return 0
    starts = [s for s, _ in ranges]
    ends = [e if e else CURRENT_YEAR for _, e in ranges]
    return max(0, max(ends) - min(starts))


def b2_reverse_chron(doc):
    exp = _section_lines(doc, EXP_HEAD)
    ranges = _date_ranges("\n".join(exp))
    starts = [s for s, _ in ranges]
    if len(starts) < 2:
        return _rule("B2", "Body & Formatting", "Reverse-chronological", "pass",
                     "Fewer than 2 dated roles — nothing to order.")
    if starts == sorted(starts, reverse=True):
        return _rule("B2", "Body & Formatting", "Reverse-chronological",
                     "pass", "Roles run newest-first.")
    return _rule("B2", "Body & Formatting", "Reverse-chronological", "fail",
                 "Job dates are not newest-first.",
                 "List experience reverse-chronologically — recruiters spend "
                 "~7 seconds and start at the top.")


def b3_action_verbs(doc):
    bullets = _bullets(doc)
    if not bullets:
        return _rule("B3", "Body & Formatting", "Action verbs", "manual",
                     "No bullet lines detected.",
                     "Use bullets starting with strong action verbs "
                     "(Built, Led, Delivered…).")
    strong = sum(1 for b in bullets
                 if _stem_verb(_first_word(re.sub(r"^[•\-\*▪‣–>]+\s*", "", b)))
                 in ACTION_VERBS)
    pct = 100 * strong / len(bullets)
    if pct >= 70:
        return _rule("B3", "Body & Formatting", "Action verbs", "pass",
                     "%d%% of %d bullets start with action verbs."
                     % (round(pct), len(bullets)))
    weak = [re.sub(r"^[•\-\*▪‣–>]+\s*", "", b).split()[:4] for b in bullets
            if _stem_verb(_first_word(re.sub(r"^[•\-\*▪‣–>]+\s*", "", b)))
            not in ACTION_VERBS][:3]
    return _rule("B3", "Body & Formatting", "Action verbs", "fail",
                 "Only %d%% of bullets start with action verbs."
                 % round(pct),
                 "Start bullets with verbs: Built, Led, Delivered, Cut, "
                 "Automated… e.g. '%s'."
                 % " ".join(weak[0]) if weak else "")


def b4_quantified(doc):
    bullets = _bullets(doc)
    if not bullets:
        return _rule("B4", "Body & Formatting", "Quantified achievements",
                     "manual", "No bullet lines detected.")
    q = sum(1 for b in bullets if re.search(r"\d|%|\$", b))
    pct = 100 * q / len(bullets)
    if pct >= 40:
        return _rule("B4", "Body & Formatting", "Quantified achievements",
                     "pass", "%d%% of bullets include numbers." % round(pct))
    return _rule("B4", "Body & Formatting", "Quantified achievements",
                 "fail", "Only %d%% of bullets include numbers."
                 % round(pct),
                 "Numbers get interviews: add %, $, time saved, users, "
                 "or scale to at least 40% of bullets.")


def b5_no_pronouns(doc):
    body = " ".join(_body_lines(doc))
    hits = PRONOUN_RE.findall(body)
    if not hits:
        return _rule("B5", "Body & Formatting", "No first-person pronouns",
                     "pass", "No I/me/my found.")
    flat = [h if isinstance(h, str) else h[0] for h in hits]
    return _rule("B5", "Body & Formatting", "No first-person pronouns",
                 "fail", "Found %d first-person pronoun(s), e.g. '%s'."
                 % (len(flat), flat[0]),
                 "Drop I/me/my — resumes are understood to be about you. "
                 "'Built X' beats 'I built X'.")


def _date_format_labels(text):
    labels = set()
    mon = "|".join(MONTHS)
    for m in re.finditer(r"\b(?:" + mon + r")[a-z]*\s+\d{4}\b", text, re.I):
        labels.add("Mon YYYY")
    for m in re.finditer(r"\b\d{1,2}[/\-]\d{4}\b", text):
        labels.add("MM/YYYY")
    for m in re.finditer(r"(?<![\d/])\b(?:19|20)\d{2}\b(?![\d/])", text):
        labels.add("YYYY")
    return labels


def b6_date_format_consistent(doc):
    labels = _date_format_labels(doc["text"])
    if len(labels) <= 2:
        return _rule("B6", "Body & Formatting", "Consistent date format",
                     "pass", "Date formats in use: %s."
                     % (", ".join(sorted(labels)) or "none found"))
    return _rule("B6", "Body & Formatting", "Consistent date format", "fail",
                 "Mixed date formats: %s." % ", ".join(sorted(labels)),
                 "Pick ONE date format (e.g. 'Jan 2020') and use it "
                 "everywhere.")


def b7_tense_consistent(doc):
    exp = _section_lines(doc, EXP_HEAD)
    bad = []
    for i, line in enumerate(exp):
        for start, end in _date_ranges(line):
            if end is not None and end < CURRENT_YEAR:
                # past job: inspect the ~6 lines under its date line
                for bl in exp[i + 1:i + 7]:
                    if BULLET_RE.match(bl):
                        first = _first_word(
                            re.sub(r"^[•\-\*▪‣–>]+\s*", "", bl)).lower()
                        if first in PRESENT_TENSE_FORMS:
                            bad.append(bl.strip()[:50])
                            break
    if not bad:
        return _rule("B7", "Body & Formatting", "Consistent tense", "pass",
                     "Past roles use past tense.")
    return _rule("B7", "Body & Formatting", "Consistent tense", "fail",
                 "Present-tense verbs in past roles, e.g. '%s'." % bad[0],
                 "Past jobs → past tense (Built, Led). Only the current "
                 "role may use present tense.")


def b8_bullet_consistency(doc):
    markers = set()
    for l in _lines(doc):
        m = BULLET_MARKER_RE.match(l)
        if m:
            markers.add(m.group(1).strip())
    if len(markers) <= 1:
        return _rule("B8", "Body & Formatting", "Bullet consistency", "pass",
                     "One bullet style throughout.")
    return _rule("B8", "Body & Formatting", "Bullet consistency", "fail",
                 "Mixed bullet markers: %s." % ", ".join(sorted(markers)),
                 "Pick one bullet character (•) and use it everywhere.")


def b9_section_headings(doc):
    text = "\n".join(_lines(doc))
    need = {"Experience": EXP_HEAD,
            "Education": r"education|academic",
            "Skills": r"skills|technical skills|core skills|competencies"}
    missing = [k for k, p in need.items()
               if not re.search(r"^\s*(" + p + r")\b", text,
                                re.IGNORECASE | re.MULTILINE)]
    if not missing:
        return _rule("B9", "Body & Formatting", "Standard section headings",
                     "pass", "Experience, Education, Skills all present.")
    return _rule("B9", "Body & Formatting", "Standard section headings",
                 "fail", "Missing section(s): %s." % ", ".join(missing),
                 "Use standard headings — Experience, Education, Skills — "
                 "so both recruiters and ATS find them.")


def b10_skills_section(doc):
    sec = _section_lines(doc, r"(technical\s+)?skills", r"core\s+skills",
                         r"competencies")
    items = [i.strip(" •-,") for i in re.split(r"[,•\n|]", "\n".join(sec))]
    items = [i for i in items if len(i) > 1]
    if len(items) >= 5:
        return _rule("B10", "Body & Formatting", "Skills section", "pass",
                     "%d skills listed." % len(items))
    return _rule("B10", "Body & Formatting", "Skills section", "fail",
                 "Only %d skill(s) listed." % len(items),
                 "Add a Skills section with 5+ relevant skills — mirror the "
                 "keywords from the job description.")


def b11_no_buzzwords(doc):
    text = doc["text"].lower()
    found = sorted({b for b in BUZZWORDS if b in text})
    if len(found) < 3:
        return _rule("B11", "Body & Formatting", "No buzzword stuffing",
                     "pass", "No buzzword stuffing detected.")
    return _rule("B11", "Body & Formatting", "No buzzword stuffing", "fail",
                 "Buzzwords found: %s." % ", ".join(found),
                 "Replace buzzwords with proof: instead of 'synergy', show "
                 "the result you drove.")


def b12_spelling(doc):
    text = doc["text"].lower()
    found = sorted({w for w in MISSPELLINGS
                    if re.search(r"\b" + w + r"\b", text)})
    if not found:
        return _rule("B12", "Body & Formatting", "Spelling", "pass",
                     "No common misspellings found. (Automated check covers "
                     "common errors only — proofread once more.)")
    return _rule("B12", "Body & Formatting", "Spelling", "fail",
                 "Possible misspellings: %s." % ", ".join(found),
                 "Fix these typos — one spelling error can end a candidacy.")


def b13_ats_tables(doc):
    n = sum(1 for l in _lines(doc)
            if len(TABLEY_RE.findall(l)) >= 2 or l.count("|") >= 2)
    if n < 5:
        return _rule("B13", "Body & Formatting", "ATS-friendly layout",
                     "pass", "No table-like structures detected.")
    return _rule("B13", "Body & Formatting", "ATS-friendly layout", "fail",
                 "%d table-like lines detected." % n,
                 "Avoid tables, text boxes, and multi-column layouts — many "
                 "ATS parsers scramble them. Single column, plain bullets.")


def b14_font_readable(doc):
    fonts = doc.get("fonts")
    if not fonts:
        return _rule("B14", "Body & Formatting", "Readable fonts", "manual",
                     "Couldn't inspect fonts from this upload.",
                     "Use one clean font (e.g. Arial, Calibri), 10-12pt "
                     "body, nothing below 8pt.")
    fams = {f.get("family", "?") for f in fonts}
    tiny = [f for f in fonts if f.get("min_size", 99) < 8]
    if len(fams) <= 3 and not tiny:
        return _rule("B14", "Body & Formatting", "Readable fonts", "pass",
                     "%d font families, nothing below 8pt." % len(fams))
    return _rule("B14", "Body & Formatting", "Readable fonts", "fail",
                 "%d font families%s." % (
                     len(fams), "; text below 8pt found" if tiny else ""),
                 "Stick to 1-2 clean fonts, 10-12pt body — nothing below "
                 "8pt.")


def b15_text_selectable(doc):
    if not doc.get("has_text_layer", True):
        return _rule("B15", "Body & Formatting", "Text is selectable",
                     "fail", "No extractable text — looks like a scanned image.",
                     "Export as a real PDF/DOCX with selectable text. "
                     "Scanned resumes are invisible to ATS.")
    cpp = doc.get("chars_per_page", 0)
    if cpp < 200:
        return _rule("B15", "Body & Formatting", "Text is selectable",
                     "fail", "Only ~%d chars/page extracted." % round(cpp),
                     "The file may be image-based. Re-export with "
                     "selectable text.")
    return _rule("B15", "Body & Formatting", "Text is selectable", "pass",
                 "Text layer looks healthy (~%d chars/page)." % round(cpp))


def b16_contact_once(doc):
    header = " ".join(_header(doc))
    rest = " ".join(_body_lines(doc))
    h_emails, h_phones = set(_emails(header)), set(_phones(header))
    dup_e = [e for e in _emails(rest) if e in h_emails]
    dup_p = [p for p in _phones(rest) if p in h_phones]
    if not dup_e and not dup_p:
        return _rule("B16", "Body & Formatting", "Contact info not repeated",
                     "pass", "Contact details appear once, in the header.")
    return _rule("B16", "Body & Formatting", "Contact info not repeated",
                 "fail", "Contact info repeated in the body.",
                 "Contact details belong in the header only — repeating "
                 "them wastes space.")


def b17_education_complete(doc):
    sec = "\n".join(_section_lines(doc, r"education", r"academic"))
    if not sec.strip():
        return _rule("B17", "Body & Formatting", "Education complete",
                     "fail", "No Education section found.",
                     "Add Education with degree, school, and graduation "
                     "year.")
    has_degree = bool(re.search(
        r"\b(bachelor|master|b\.?\s?s\.?|m\.?\s?s\.?|mba|ph\.?\s?d\.?|"
        r"b\.?\s?tech|associate)\b", sec, re.IGNORECASE))
    has_year = bool(re.search(r"\b(?:19|20)\d{2}\b", sec))
    if has_degree and has_year:
        return _rule("B17", "Body & Formatting", "Education complete",
                     "pass", "Degree and year present.")
    missing = " and ".join([p for p, ok in
                            (("degree", has_degree), ("year", has_year))
                            if not ok])
    return _rule("B17", "Body & Formatting", "Education complete", "fail",
                 "Education section missing: %s." % missing,
                 "Each education entry needs degree, school, and year.")


def b18_no_chart_artifacts(doc):
    hits = [l.strip()[:40] for l in _lines(doc) if CHART_RE.search(l)]
    if not hits:
        return _rule("B18", "Body & Formatting", "No chart artifacts",
                     "pass", "No chart/graphic artifacts in text.")
    return _rule("B18", "Body & Formatting", "No chart artifacts", "fail",
                 "Found chart-like artifacts, e.g. '%s'." % hits[0],
                 "Charts don't survive ATS parsing — convert visuals to "
                 "plain quantified bullets.")


HEADER_RULES = [h1_name_present, h2_name_prominent, h3_no_resume_title,
                h4_email_present, h5_single_email, h6_email_professional,
                h7_phone_present, h8_single_phone, h9_linkedin_present,
                h10_linkedin_valid, h11_location_present, h12_no_photo,
                h13_no_street_address, h14_header_compact, h15_portfolio_tech]
BODY_RULES = [b1_length_ok, b2_reverse_chron, b3_action_verbs,
              b4_quantified, b5_no_pronouns, b6_date_format_consistent,
              b7_tense_consistent, b8_bullet_consistency, b9_section_headings,
              b10_skills_section, b11_no_buzzwords, b12_spelling,
              b13_ats_tables, b14_font_readable, b15_text_selectable,
              b16_contact_once, b17_education_complete, b18_no_chart_artifacts]
ALL_RULES = HEADER_RULES + BODY_RULES


# ---------------------------------------------------------------------------
# JD keyword matching
# ---------------------------------------------------------------------------

def _skill_in(text, term, aliases):
    variants = [term] + aliases
    for v in variants:
        if re.search(r"(?<![A-Za-z0-9+#])" + re.escape(v) +
                     r"(?![A-Za-z0-9+#])", text, re.IGNORECASE):
            return True
    return False


def jd_match(resume_text, jd_text):
    """Return {jd_skills, matched, missing, coverage, top_missing_keywords}."""
    rl, jl = resume_text.lower(), jd_text.lower()
    jd_skills = [canon for canon, aliases in SKILLS
                 if _skill_in(jl, canon, aliases)]
    matched = [s for s in jd_skills
               if _skill_in(rl, s, dict(SKILLS)[s])]
    missing = [s for s in jd_skills if s not in matched]
    coverage = (100.0 * len(matched) / len(jd_skills)) if jd_skills else None

    freq = {}
    for w in re.findall(r"[a-z][a-z\-]{3,}", jl):
        if w not in STOPWORDS:
            freq[w] = freq.get(w, 0) + 1
    top = sorted(freq, key=lambda w: (-freq[w], w))[:25]
    missing_kw = [w for w in top if w not in rl][:10]
    return {"jd_skills": jd_skills, "matched": matched, "missing": missing,
            "coverage": coverage, "missing_keywords": missing_kw}


# ---------------------------------------------------------------------------
# Full review
# ---------------------------------------------------------------------------

def review(doc, jd_text=""):
    results = [fn(doc) for fn in ALL_RULES]
    scored = [r for r in results if r["status"] in ("pass", "fail")]
    passed = sum(1 for r in scored if r["status"] == "pass")
    rule_score = round(100 * passed / len(scored)) if scored else 0
    jd = jd_match(doc["text"], jd_text) if jd_text.strip() else None
    if jd and jd["coverage"] is not None:
        overall = round(0.7 * rule_score + 0.3 * jd["coverage"])
    else:
        overall = rule_score
    failed = [r for r in results if r["status"] == "fail"]
    manual = [r for r in results if r["status"] == "manual"]
    grade = ("Excellent" if overall >= 90 else "Strong" if overall >= 75
             else "Fair" if overall >= 60 else "Needs work")
    return {"rules": results, "failed": failed, "manual": manual,
            "rule_score": rule_score, "jd": jd, "overall": overall,
            "grade": grade}


def doc_from_text(text, source="txt", pages=None, **kw):
    lines = [l.rstrip() for l in text.splitlines()]
    non_empty = [l for l in lines if l.strip()]
    n_pages = pages or max(1, round(len(non_empty) / 45))
    doc = {"text": text, "lines": non_empty, "pages": n_pages,
           "has_text_layer": True,
           "chars_per_page": len(text) / n_pages,
           "name_font_largest": None, "images": None, "fonts": None,
           "source": source}
    doc.update(kw)
    return doc
