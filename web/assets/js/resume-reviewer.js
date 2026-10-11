/* ============================================================
   Resume Reviewer AI — static web app (Demo 9 of 9)
   Rule engine mirrored from rules_engine.py — keep in sync.
   PDF parsing: PDF.js (CDN). DOCX parsing: mammoth.js (CDN).
   Everything runs in the visitor's browser. The resume file is
   NEVER uploaded anywhere; only review metadata is emailed to
   Preet via FormSubmit (name, LinkedIn, timestamp, score).
   ============================================================ */
'use strict';

const CURRENT_YEAR = 2026;

/* ---------------- lexicons ---------------- */
const EMAIL_RE = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g;
const PHONE_RE = /\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}/g;
const LINKEDIN_RE = /linkedin\.com\/in\/[A-Za-z0-9_\-]+\/?/gi;
const LOCATION_RE = /\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?,\s*[A-Z]{2}\b/;
const STREET_RE = /\b\d{1,5}\s+[A-Z][a-zA-Z]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Way|Terrace|Ter|Place|Pl|Parkway|Pkwy)\b|\bApt\.?\s*\w*\d+|\bSuite\s+\d+|\bUnit\s+\d+/i;
const SILLY_EMAIL_RE = /(sexy|hot|cool|dude|rockstar|ninja|guru|princess|queen|king|baby|babe|gamer|playboy|thug|swag|xoxo|420|69|\d{4,})/i;
const BULLET_RE = /^\s*[•\-\*▪‣–>]+\s+\S/;
const BULLET_MARKER_RE = /^\s*([•\-\*▪‣–>]+)\s+\S/;
const PRONOUN_RE = /(?<![A-Za-z])I(?![A-Za-z])|\b(me|my|mine|myself)\b/gi;
const CHART_RE = /[█▇▆▅▄▃▂▁■□▪▫●○]{3,}|(\|\s*){4,}/;
const TABLEY_RE = / {3,}|\t/g;
const MISSPELLINGS = ["recieve","seperate","occured","occurance","managment","experiance","accomodate","definately","untill","neccessary","tommorow","writting","calender","concious","dissapear","embarass","existance","freind","grammer","independant","knowlege","liason","noticable","persue","posession","publically","recomend","refering","sucessful","truely","acheive","beleive","arguement","useage","wierd","priviledge","maintainance","oppurtunity","suprise"];
const BUZZWORDS = ["synergy","synergies","guru","ninja","rockstar","rock star","thought leader","best-of-breed","best of breed","game-changer","game changer","disruptive","move the needle","self-starter"];
const ACTION_VERBS = new Set(("achieved built led launched designed developed delivered drove improved increased reduced cut saved automated architected implemented migrated optimized scaled streamlined spearheaded transformed created established founded grew boosted accelerated negotiated partnered mentored coached pioneered engineered deployed shipped owned championed orchestrated revamped modernized consolidated integrated analyzed evaluated identified resolved diagnosed prevented forecast modeled tested validated published presented authored secured ensured audited monitored maintained upgraded refactored prototyped piloted rolled generated doubled tripled slashed decreased expanded crafted wrote managed directed headed oversaw").split(" "));
const PRESENT_TENSE_FORMS = new Set(("manage manages lead leads develop develops build builds own owns drive drives oversee oversees direct directs head heads run runs maintain maintains support supports coordinate coordinates mentor mentors architect architects design designs implement implements work works").split(" "));
const MONTHS = ["jan","feb","mar","apr","may","jun","jul","aug","sep","sept","oct","nov","dec"];
const EXP_HEAD_SRC = "((work\\s+)?experience|work\\s+history|employment(\\s+history)?)";
const EXP_HEAD_RE = new RegExp("^\\s*(" + EXP_HEAD_SRC + ")\\b", "i");
const ANY_HEADING_RE = /^\s*(experience|education|skills|summary|projects|certifications|awards|publications|contact)\b/i;
const SKILLS = [["Python",[]],["SQL",[]],["Spark",["apache spark","pyspark"]],["Airflow",["apache airflow"]],["AWS",["amazon web services"]],["Azure",["microsoft azure"]],["GCP",["google cloud","google cloud platform"]],["Snowflake",[]],["Databricks",[]],["dbt",[]],["Kafka",["apache kafka"]],["Docker",[]],["Kubernetes",["k8s"]],["Terraform",[]],["CI/CD",["cicd","continuous integration"]],["Git",[]],["Linux",[]],["Machine Learning",["ml"]],["Deep Learning",[]],["TensorFlow",[]],["PyTorch",[]],["scikit-learn",["sklearn"]],["pandas",[]],["NumPy",["numpy"]],["Data Modeling",[]],["Data Warehouse",["data warehousing"]],["Data Lake",[]],["ETL",[]],["ELT",[]],["Data Pipeline",["data pipelines"]],["Streaming",["stream processing"]],["Real-time",["realtime"]],["Data Governance",[]],["Data Quality",[]],["Looker",[]],["Tableau",[]],["Power BI",["powerbi"]],["A/B Testing",["ab testing"]],["Statistics",["statistical"]],["NLP",["natural language processing"]],["LLMs",["llm","large language model"]],["RAG",["retrieval augmented generation"]],["MLOps",[]],["Feature Engineering",[]],["Data Visualization",[]],["Agile",[]],["Scrum",[]],["Jira",[]],["REST API",["rest","restful"]],["GraphQL",[]],["Microservices",[]],["PostgreSQL",["postgres"]],["MySQL",[]],["MongoDB",["mongo"]],["Redis",[]],["Elasticsearch",[]],["Redshift",[]],["BigQuery",[]],["Hadoop",[]],["Hive",[]],["Flink",[]],["Lambda",["aws lambda"]],["S3",[]],["EMR",[]],["Glue",["aws glue"]],["Java",[]],["Scala",[]],["Go",["golang"]],["JavaScript",[]],["TypeScript",[]],["Bash",["shell scripting"]],["R",[]],["Data Analysis",[]],["Data Science",[]],["Analytics",[]],["Business Intelligence",["bi"]],["KPI",["kpis"]],["Forecasting",[]],["Optimization",["optimisation"]],["Automation",[]],["Testing",[]],["Debugging",[]],["Documentation",[]],["Mentoring",[]],["Leadership",[]],["Communication",[]],["Project Management",[]],["Monitoring",[]],["Datadog",[]],["Grafana",[]],["Incident Management",["incident response","on-call","oncall"]]];
const SKILL_ALIASES = {};
SKILLS.forEach(([c, a]) => { SKILL_ALIASES[c] = a; });
const STOPWORDS = new Set(("the and for with you your will have has are our that this from they their who what about into over under between through during including such more most other some than then them these those when where which while been being also both each very just like well work working team role candidate looking join help able plus across within using used use new day per etc").split(" "));

function escRe(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }

/* ---------------- helpers ---------------- */
function linesOf(doc) { return doc.lines; }
function isHeadingLine(line) {
  const s = line.trim().replace(/^\*+|\*+$/g, "");
  if (!s || s.length > 30 || /\d/.test(s)) return false;
  const words = s.split(/\s+/);
  if (words.length < 1 || words.length > 4) return false;
  return s === s.toUpperCase() && /[A-Za-z]/.test(s);
}
function headerOf(doc) {
  const ls = linesOf(doc);
  let cut = ls.length;
  for (let i = 2; i < Math.min(ls.length, 12); i++) {
    if (isHeadingLine(ls[i])) { cut = i; break; }
  }
  return ls.slice(0, Math.min(cut, 10));
}
function bodyLinesOf(doc) { return linesOf(doc).slice(10); }
function emailsIn(text) {
  const out = new Set(); let m;
  EMAIL_RE.lastIndex = 0;
  while ((m = EMAIL_RE.exec(text))) out.add(m[0]);
  return [...out].sort();
}
function phonesIn(text) {
  const out = new Set(); let m;
  PHONE_RE.lastIndex = 0;
  while ((m = PHONE_RE.exec(text))) {
    const d = m[0].replace(/\D/g, "");
    if (d.length >= 10 && d.length <= 11) out.add(d.slice(-10));
  }
  return [...out].sort();
}
function looksLikeName(line) {
  const s = line.trim().replace(/^\*+|\*+$/g, "");
  if (!s || /\d/.test(s)) return false;
  if (["resume","cv","curriculum vitae"].includes(s.toLowerCase())) return false;
  const parts = s.split(/\s+/);
  if (parts.length < 2 || parts.length > 4) return false;
  return parts.every(p => {
    p = p.replace(/[,.]$/g, "");
    if (!p || !/[A-Z]/.test(p[0])) return false;
    if ((p.match(/[A-Z]/g) || []).length > 2) return false;
    return /^[A-Za-z.'-]+$/.test(p);
  });
}
function findName(doc) {
  for (const l of linesOf(doc).slice(0, 4)) if (looksLikeName(l)) return l.trim();
  return null;
}
function bulletsOf(doc) { return linesOf(doc).filter(l => BULLET_RE.test(l)); }
function sectionLines(doc, ...patterns) {
  const src = patterns.map(p => p.source ? p.source : p).join("|");
  const pat = new RegExp("^\\s*(" + src + ")\\b", "i");
  const out = []; let capture = false;
  for (const l of linesOf(doc)) {
    if (pat.test(l)) { capture = true; continue; }
    if (ANY_HEADING_RE.test(l)) { capture = false; continue; }
    if (capture && l.trim()) out.push(l);
  }
  return out;
}
function dateRanges(text) {
  const mon = MONTHS.join("|");
  const re = new RegExp(
    "(?:(?:" + mon + ")[a-z]*\\s+)?\\b((?:19|20)\\d{2})\\b\\s*[–—\\-]\\s*" +
    "(?:(?:" + mon + ")[a-z]*\\s+)?(?:\\d{1,2}/)?\\b((?:19|20)\\d{2}|present|current)\\b", "gi");
  const out = []; let m;
  while ((m = re.exec(text))) {
    const e = m[2].toLowerCase();
    out.push([parseInt(m[1], 10), (e === "present" || e === "current") ? null : parseInt(e, 10)]);
  }
  return out;
}
function yearsExperience(doc) {
  const rs = dateRanges(doc.text);
  if (!rs.length) return 0;
  return Math.max(0, Math.max(...rs.map(r => r[1] === null ? CURRENT_YEAR : r[1])) - Math.min(...rs.map(r => r[0])));
}
function stemVerb(w) {
  w = w.toLowerCase();
  if (ACTION_VERBS.has(w)) return w;
  for (const suf of ["ing","ed","es","s"]) {
    if (w.endsWith(suf) && w.length > suf.length + 2) {
      const c = w.slice(0, -suf.length);
      if (ACTION_VERBS.has(c)) return c;
    }
  }
  return w;
}
function firstWord(line) { const m = line.match(/[A-Za-z]+/); return m ? m[0] : ""; }
function stripBullet(l) { return l.replace(/^[•\-\*▪‣–>]+\s*/, ""); }
function rule(id, section, name, status, detail, suggestion) {
  return { id, section, name, status, detail, suggestion: suggestion || "" };
}

/* ---------------- header rules H1-H15 ---------------- */
function h1(doc) {
  const name = findName(doc);
  if (name) return rule("H1","Header","Name present","pass","Found name: " + name);
  const first = linesOf(doc).length ? linesOf(doc)[0].trim() : "(empty)";
  return rule("H1","Header","Name present","fail","First line doesn't look like a name: '" + first.slice(0,60) + "'",
    "Put your full name alone on the first line, in Title Case (e.g. 'Priya Sharma').");
}
function h2(doc) {
  const v = doc.name_font_largest;
  if (v === true) return rule("H2","Header","Name is prominent","pass","Name is the largest text on page 1.");
  if (v === null || v === undefined) return rule("H2","Header","Name is prominent","manual","Couldn't verify font size from this upload.",
    "Make your name the single largest text on the page (16-20pt) so recruiters see it first.");
  return rule("H2","Header","Name is prominent","fail","Something else on page 1 is larger than your name.",
    "Make your name the single largest text on the page (16-20pt) so recruiters see it first.");
}
function h3(doc) {
  for (const l of linesOf(doc).slice(0, 6)) {
    const s = l.trim().toLowerCase().replace(/^\*+|\*+$/g, "");
    if (["resume","cv","curriculum vitae"].includes(s) || /^(resume|cv)\s+of\b/.test(s))
      return rule("H3","Header","No 'Resume' title","fail","Found a title line: '" + l.trim().slice(0,40) + "'",
        "Delete it — the file name says it's a resume; use the space for your name and contact info.");
  }
  return rule("H3","Header","No 'Resume' title","pass","No wasted 'Resume'/'CV' title line.");
}
function h4(doc) {
  const e = emailsIn(headerOf(doc).join(" "));
  if (e.length) return rule("H4","Header","Email present","pass","Found: " + e[0]);
  return rule("H4","Header","Email present","fail","No email address in the header.","Add a professional email address under your name.");
}
function h5(doc) {
  const e = emailsIn(headerOf(doc).join(" "));
  if (!e.length) return rule("H5","Header","Single email only","manual","No email found (see H4).");
  if (e.length === 1) return rule("H5","Header","Single email only","pass","Exactly one email address.");
  return rule("H5","Header","Single email only","fail","Found " + e.length + " emails: " + e.join(", "),
    "Keep one email — two inboxes means missed messages.");
}
function h6(doc) {
  const e = emailsIn(headerOf(doc).join(" "));
  if (!e.length) return rule("H6","Header","Professional email","manual","No email found (see H4).");
  const local = e[0].split("@")[0];
  if (SILLY_EMAIL_RE.test(local))
    return rule("H6","Header","Professional email","fail","Email looks unprofessional: " + e[0],
      "Use firstname.lastname@domain — never nicknames, birth years, or numbers like 420/69.");
  return rule("H6","Header","Professional email","pass","Email looks professional.");
}
function h7(doc) {
  const p = phonesIn(headerOf(doc).join(" "));
  if (p.length) return rule("H7","Header","Phone present","pass","Found phone ending in " + p[0].slice(-4));
  return rule("H7","Header","Phone present","fail","No phone number in the header.","Add one phone number so recruiters can reach you quickly.");
}
function h8(doc) {
  const p = phonesIn(headerOf(doc).join(" "));
  if (!p.length) return rule("H8","Header","Single phone only","manual","No phone found (see H7).");
  if (p.length === 1) return rule("H8","Header","Single phone only","pass","Exactly one phone number.");
  return rule("H8","Header","Single phone only","fail","Found " + p.length + " phone numbers.","Keep one phone number — one clear way to call you.");
}
function h9(doc) {
  if (doc.text.toLowerCase().includes("linkedin.com/in/"))
    return rule("H9","Header","LinkedIn present","pass","LinkedIn profile link found.");
  return rule("H9","Header","LinkedIn present","fail","No linkedin.com/in/ link found.",
    "Add your LinkedIn URL (linkedin.com/in/yourname) — recruiters check it before they call.");
}
function h10(doc) {
  LINKEDIN_RE.lastIndex = 0;
  const ms = doc.text.match(LINKEDIN_RE) || [];
  if (!ms.length) return rule("H10","Header","LinkedIn URL valid","manual","No LinkedIn link found (see H9).");
  const bad = ms.filter(m => m.includes(" "));
  if (bad.length) return rule("H10","Header","LinkedIn URL valid","fail","LinkedIn URL looks broken: " + bad[0],
    "Use the clean form: linkedin.com/in/yourname (no spaces, no extra path).");
  return rule("H10","Header","LinkedIn URL valid","pass","LinkedIn URL format looks good: " + ms[0]);
}
function h11(doc) {
  if (LOCATION_RE.test(headerOf(doc).join(" ")))
    return rule("H11","Header","Location present","pass","Found City, ST location.");
  return rule("H11","Header","Location present","fail","No 'City, ST' location in the header.",
    "Add 'City, ST' (e.g. Boston, MA) — recruiters filter by location; never put your full street address.");
}
function h12(doc) {
  const imgs = doc.images;
  if (imgs === null || imgs === undefined)
    return rule("H12","Header","No photo","manual","Couldn't inspect images from this upload.",
      "US resumes don't include photos — remove yours if present (it also breaks some ATS parsers).");
  if (imgs === 0) return rule("H12","Header","No photo","pass","No embedded images detected.");
  return rule("H12","Header","No photo","fail","Detected " + imgs + " embedded image(s) — likely a photo.",
    "Remove the photo: US resumes don't include one, and it can break ATS parsing.");
}
function h13(doc) {
  const m = headerOf(doc).join(" ").match(STREET_RE);
  if (m) return rule("H13","Header","No street address","fail","Found address-like text: '" + m[0].slice(0,40) + "'",
    "Drop the street address — 'City, ST' is enough and safer. Street addresses waste prime header space.");
  return rule("H13","Header","No street address","pass","No street address in header.");
}
function h14(doc) {
  const header = headerOf(doc).join(" ");
  const signals = [EMAIL_RE.test(header), phonesIn(header).length > 0,
    header.toLowerCase().includes("linkedin.com/in/"), LOCATION_RE.test(header)]
    .filter(Boolean).length;
  EMAIL_RE.lastIndex = 0;
  const n = headerOf(doc).length;
  if (signals >= 3 && n <= 8)
    return rule("H14","Header","Compact header","pass","Contact block fits in " + n + " lines.");
  return rule("H14","Header","Compact header","fail","Header sprawls over " + n + " lines.",
    "Compress name + contact info into at most 8 lines — every line above the fold should earn its place.");
}
function h15(doc) {
  const t = doc.text.toLowerCase();
  const isTech = /\b(software|data|engineer|developer|github|python|java|machine learning)\b/.test(t);
  if (/github\.com\/[A-Za-z0-9_\-]+\/?(\s|$)/.test(doc.text))
    return rule("H15","Header","Portfolio/GitHub link","pass","GitHub/portfolio link found.");
  if (isTech) return rule("H15","Header","Portfolio/GitHub link","fail","Tech resume without a GitHub/portfolio link.",
    "Add github.com/yourname — hiring managers click it before the phone screen.");
  return rule("H15","Header","Portfolio/GitHub link","manual","Non-technical resume.",
    "Optional: a portfolio site link helps for design/writing roles.");
}

/* ---------------- body rules B1-B18 ---------------- */
function b1(doc) {
  const pages = doc.pages || 1, years = yearsExperience(doc);
  if (pages <= 1) return rule("B1","Body & Formatting","Length: one page","pass","Fits on one page.");
  if (pages === 2 && years >= 10)
    return rule("B1","Body & Formatting","Length: one page","pass","Two pages acceptable with ~" + years + " years experience.");
  if (pages === 2) return rule("B1","Body & Formatting","Length: one page","fail","Two pages with ~" + years + " years experience.",
    "Cut to one page: drop older roles, trim bullets to your 3 strongest per job.");
  return rule("B1","Body & Formatting","Length: one page","fail",pages + " pages detected.",
    "Resumes over 2 pages get skimmed, not read. Cut ruthlessly — one page per 10 years is the norm.");
}
function b2(doc) {
  const exp = sectionLines(doc, EXP_HEAD_RE);
  const starts = [];
  exp.forEach(l => dateRanges(l).forEach(([s]) => starts.push(s)));
  if (starts.length < 2)
    return rule("B2","Body & Formatting","Reverse-chronological","pass","Fewer than 2 dated roles — nothing to order.");
  const desc = [...starts].sort((a,b) => b - a);
  if (starts.every((s,i) => s === desc[i]))
    return rule("B2","Body & Formatting","Reverse-chronological","pass","Roles run newest-first.");
  return rule("B2","Body & Formatting","Reverse-chronological","fail","Job dates are not newest-first.",
    "List experience reverse-chronologically — recruiters spend ~7 seconds and start at the top.");
}
function b3(doc) {
  const bullets = bulletsOf(doc);
  if (!bullets.length) return rule("B3","Body & Formatting","Action verbs","manual","No bullet lines detected.",
    "Use bullets starting with strong action verbs (Built, Led, Delivered…).");
  const strong = bullets.filter(b => ACTION_VERBS.has(stemVerb(firstWord(stripBullet(b))))).length;
  const pct = Math.round(100 * strong / bullets.length);
  if (pct >= 70) return rule("B3","Body & Formatting","Action verbs","pass",pct + "% of " + bullets.length + " bullets start with action verbs.");
  const weak = bullets.filter(b => !ACTION_VERBS.has(stemVerb(firstWord(stripBullet(b))))).slice(0,1)
    .map(b => stripBullet(b).split(/\s+/).slice(0,4).join(" "));
  return rule("B3","Body & Formatting","Action verbs","fail","Only " + pct + "% of bullets start with action verbs.",
    "Start bullets with verbs: Built, Led, Delivered, Cut, Automated… e.g. '" + (weak[0] || "") + "'.");
}
function b4(doc) {
  const bullets = bulletsOf(doc);
  if (!bullets.length) return rule("B4","Body & Formatting","Quantified achievements","manual","No bullet lines detected.");
  const q = bullets.filter(b => /[\d%$]/.test(b)).length;
  const pct = Math.round(100 * q / bullets.length);
  if (pct >= 40) return rule("B4","Body & Formatting","Quantified achievements","pass",pct + "% of bullets include numbers.");
  return rule("B4","Body & Formatting","Quantified achievements","fail","Only " + pct + "% of bullets include numbers.",
    "Numbers get interviews: add %, $, time saved, users, or scale to at least 40% of bullets.");
}
function b5(doc) {
  PRONOUN_RE.lastIndex = 0;
  const hits = bodyLinesOf(doc).join(" ").match(PRONOUN_RE) || [];
  if (!hits.length) return rule("B5","Body & Formatting","No first-person pronouns","pass","No I/me/my found.");
  return rule("B5","Body & Formatting","No first-person pronouns","fail",
    "Found " + hits.length + " first-person pronoun(s), e.g. '" + hits[0] + "'.",
    "Drop I/me/my — resumes are understood to be about you. 'Built X' beats 'I built X'.");
}
function dateFormatLabels(text) {
  const labels = new Set(); const mon = MONTHS.join("|"); let m;
  const r1 = new RegExp("\\b(?:" + mon + ")[a-z]*\\s+\\d{4}\\b", "gi");
  while ((m = r1.exec(text))) labels.add("Mon YYYY");
  const r2 = /\b\d{1,2}[/\-]\d{4}\b/g;
  while ((m = r2.exec(text))) labels.add("MM/YYYY");
  const r3 = /(?<![\d/])\b(?:19|20)\d{2}\b(?![\d/])/g;
  while ((m = r3.exec(text))) labels.add("YYYY");
  return labels;
}
function b6(doc) {
  const labels = dateFormatLabels(doc.text);
  if (labels.size <= 2) return rule("B6","Body & Formatting","Consistent date format","pass",
    "Date formats in use: " + ([...labels].sort().join(", ") || "none found"));
  return rule("B6","Body & Formatting","Consistent date format","fail","Mixed date formats: " + [...labels].sort().join(", ") + ".",
    "Pick ONE date format (e.g. 'Jan 2020') and use it everywhere.");
}
function b7(doc) {
  const exp = sectionLines(doc, EXP_HEAD_RE);
  const bad = [];
  exp.forEach((line, i) => {
    dateRanges(line).forEach(([s, e]) => {
      if (e !== null && e < CURRENT_YEAR) {
        for (const bl of exp.slice(i + 1, i + 7)) {
          if (BULLET_RE.test(bl)) {
            const first = firstWord(stripBullet(bl)).toLowerCase();
            if (PRESENT_TENSE_FORMS.has(first)) { bad.push(bl.trim().slice(0,50)); break; }
          }
        }
      }
    });
  });
  if (!bad.length) return rule("B7","Body & Formatting","Consistent tense","pass","Past roles use past tense.");
  return rule("B7","Body & Formatting","Consistent tense","fail","Present-tense verbs in past roles, e.g. '" + bad[0] + "'.",
    "Past jobs → past tense (Built, Led). Only the current role may use present tense.");
}
function b8(doc) {
  const markers = new Set();
  linesOf(doc).forEach(l => { const m = l.match(BULLET_MARKER_RE); if (m) markers.add(m[1].trim()); });
  if (markers.size <= 1) return rule("B8","Body & Formatting","Bullet consistency","pass","One bullet style throughout.");
  return rule("B8","Body & Formatting","Bullet consistency","fail","Mixed bullet markers: " + [...markers].sort().join(", ") + ".",
    "Pick one bullet character (•) and use it everywhere.");
}
function b9(doc) {
  const text = linesOf(doc).join("\n");
  const need = [["Experience", EXP_HEAD_SRC], ["Education", "education|academic"], ["Skills", "skills|technical skills|core skills|competencies"]];
  const missing = need.filter(([k, p]) => !new RegExp("^\\s*(" + p + ")\\b", "im").test(text)).map(([k]) => k);
  if (!missing.length) return rule("B9","Body & Formatting","Standard section headings","pass","Experience, Education, Skills all present.");
  return rule("B9","Body & Formatting","Standard section headings","fail","Missing section(s): " + missing.join(", ") + ".",
    "Use standard headings — Experience, Education, Skills — so both recruiters and ATS find them.");
}
function b10(doc) {
  const sec = sectionLines(doc, /(technical\s+)?skills/i, /core\s+skills/i, /competencies/i).join("\n");
  const items = sec.split(/[,•\n|]/).map(s => s.trim().replace(/^[•\-*]+\s*/, "")).filter(s => s.length > 1);
  if (items.length >= 5) return rule("B10","Body & Formatting","Skills section","pass",items.length + " skills listed.");
  return rule("B10","Body & Formatting","Skills section","fail","Only " + items.length + " skill(s) listed.",
    "Add a Skills section with 5+ relevant skills — mirror the keywords from the job description.");
}
function b11(doc) {
  const t = doc.text.toLowerCase();
  const found = [...new Set(BUZZWORDS.filter(b => t.includes(b)))];
  if (found.length < 3) return rule("B11","Body & Formatting","No buzzword stuffing","pass","No buzzword stuffing detected.");
  return rule("B11","Body & Formatting","No buzzword stuffing","fail","Buzzwords found: " + found.join(", ") + ".",
    "Replace buzzwords with proof: instead of 'synergy', show the result you drove.");
}
function b12(doc) {
  const t = doc.text.toLowerCase();
  const found = [...new Set(MISSPELLINGS.filter(w => new RegExp("\\b" + w + "\\b").test(t)))];
  if (!found.length) return rule("B12","Body & Formatting","Spelling","pass",
    "No common misspellings found. (Automated check covers common errors only — proofread once more.)");
  return rule("B12","Body & Formatting","Spelling","fail","Possible misspellings: " + found.join(", ") + ".",
    "Fix these typos — one spelling error can end a candidacy.");
}
function b13(doc) {
  const n = linesOf(doc).filter(l => { TABLEY_RE.lastIndex = 0; const m = l.match(TABLEY_RE); return (m && m.length >= 2) || (l.match(/\|/g) || []).length >= 2; }).length;
  if (n < 5) return rule("B13","Body & Formatting","ATS-friendly layout","pass","No table-like structures detected.");
  return rule("B13","Body & Formatting","ATS-friendly layout","fail",n + " table-like lines detected.",
    "Avoid tables, text boxes, and multi-column layouts — many ATS parsers scramble them. Single column, plain bullets.");
}
function b14(doc) {
  const fonts = doc.fonts;
  if (!fonts || !fonts.length) return rule("B14","Body & Formatting","Readable fonts","manual","Couldn't inspect fonts from this upload.",
    "Use one clean font (e.g. Arial, Calibri), 10-12pt body, nothing below 8pt.");
  const fams = new Set(fonts.map(f => f.family));
  const tiny = fonts.filter(f => f.min_size < 8);
  if (fams.size <= 3 && !tiny.length)
    return rule("B14","Body & Formatting","Readable fonts","pass",fams.size + " font families, nothing below 8pt.");
  return rule("B14","Body & Formatting","Readable fonts","fail",fams.size + " font families" + (tiny.length ? "; text below 8pt found" : "") + ".",
    "Stick to 1-2 clean fonts, 10-12pt body — nothing below 8pt.");
}
function b15(doc) {
  if (!doc.has_text_layer)
    return rule("B15","Body & Formatting","Text is selectable","fail","No extractable text — looks like a scanned image.",
      "Export as a real PDF/DOCX with selectable text. Scanned resumes are invisible to ATS.");
  const cpp = doc.chars_per_page || 0;
  if (cpp < 200) return rule("B15","Body & Formatting","Text is selectable","fail","Only ~" + Math.round(cpp) + " chars/page extracted.",
    "The file may be image-based. Re-export with selectable text.");
  return rule("B15","Body & Formatting","Text is selectable","pass","Text layer looks healthy (~" + Math.round(cpp) + " chars/page).");
}
function b16(doc) {
  const header = headerOf(doc).join(" "), rest = bodyLinesOf(doc).join(" ");
  const he = new Set(emailsIn(header)), hp = new Set(phonesIn(header));
  const dupE = emailsIn(rest).filter(e => he.has(e)), dupP = phonesIn(rest).filter(p => hp.has(p));
  if (!dupE.length && !dupP.length)
    return rule("B16","Body & Formatting","Contact info not repeated","pass","Contact details appear once, in the header.");
  return rule("B16","Body & Formatting","Contact info not repeated","fail","Contact info repeated in the body.",
    "Contact details belong in the header only — repeating them wastes space.");
}
function b17(doc) {
  const sec = sectionLines(doc, /education/i, /academic/i).join("\n");
  if (!sec.trim()) return rule("B17","Body & Formatting","Education complete","fail","No Education section found.",
    "Add Education with degree, school, and graduation year.");
  const hasDegree = /\b(bachelor|master|b\.?\s?s\.?|m\.?\s?s\.?|mba|ph\.?\s?d\.?|b\.?\s?tech|associate)\b/i.test(sec);
  const hasYear = /\b(?:19|20)\d{2}\b/.test(sec);
  if (hasDegree && hasYear) return rule("B17","Body & Formatting","Education complete","pass","Degree and year present.");
  const missing = [["degree", hasDegree], ["year", hasYear]].filter(([, ok]) => !ok).map(([p]) => p).join(" and ");
  return rule("B17","Body & Formatting","Education complete","fail","Education section missing: " + missing + ".",
    "Each education entry needs degree, school, and year.");
}
function b18(doc) {
  const hits = linesOf(doc).filter(l => CHART_RE.test(l)).map(l => l.trim().slice(0, 40));
  if (!hits.length) return rule("B18","Body & Formatting","No chart artifacts","pass","No chart/graphic artifacts in text.");
  return rule("B18","Body & Formatting","No chart artifacts","fail","Found chart-like artifacts, e.g. '" + hits[0] + "'.",
    "Charts don't survive ATS parsing — convert visuals to plain quantified bullets.");
}
const HEADER_RULES = [h1,h2,h3,h4,h5,h6,h7,h8,h9,h10,h11,h12,h13,h14,h15];
const BODY_RULES = [b1,b2,b3,b4,b5,b6,b7,b8,b9,b10,b11,b12,b13,b14,b15,b16,b17,b18];

/* ---------------- JD matching ---------------- */
function skillIn(text, term, aliases) {
  for (const v of [term, ...aliases]) {
    if (new RegExp("(?<![A-Za-z0-9+#])" + escRe(v) + "(?![A-Za-z0-9+#])", "i").test(text)) return true;
  }
  return false;
}
function jdMatch(resumeText, jdText, expText) {
  const rl = resumeText.toLowerCase(), jl = jdText.toLowerCase();
  const el = (expText || "").toLowerCase();
  const jdSkills = SKILLS.filter(([c, a]) => skillIn(jl, c, a)).map(([c]) => c);
  const matched = jdSkills.filter(s => skillIn(rl, s, SKILL_ALIASES[s] || []));
  // A matched skill is also tagged *substantiated* when it appears in the
  // experience section. Skills showing up solely in keyword lists
  // (summary/skills sections) land in "unsubstantiated": they are listed
  // in the report and trigger rule B19 when the ratio is extreme, but
  // coverage scoring is unchanged so legitimate skills-section listings
  // are not punished. Mirrors Python rules_engine.jd_match.
  const substantiated = matched.filter(s => skillIn(el, s, SKILL_ALIASES[s] || []));
  const unsubstantiated = matched.filter(s => !substantiated.includes(s));
  const missing = jdSkills.filter(s => !matched.includes(s));
  const coverage = jdSkills.length ? 100 * matched.length / jdSkills.length : null;
  const freq = {};
  (jl.match(/[a-z][a-z\-]{3,}/g) || []).forEach(w => { if (!STOPWORDS.has(w)) freq[w] = (freq[w] || 0) + 1; });
  const top = Object.keys(freq).sort((a, b) => freq[b] - freq[a] || (a < b ? -1 : 1)).slice(0, 25);
  const missingKw = top.filter(w => !rl.includes(w)).slice(0, 10);
  return { jd_skills: jdSkills, matched, missing, coverage, missing_keywords: missingKw,
    substantiated, unsubstantiated };
}
/* B19 -- keyword-stuffing check (needs JD context; appended in review()).
   Mirrors Python rules_engine.b19_skills_backed_by_evidence. */
function b19(jd) {
  if (!jd || !jd.matched || !jd.matched.length) return null;
  const backed = (jd.substantiated || []).length;
  const ratio = backed / jd.matched.length;
  if (jd.matched.length >= 5 && ratio < 0.25) {
    return rule("B19", "Body & Formatting", "Skills backed by evidence", "fail",
      "Only " + backed + " of " + jd.matched.length + " matched skills (" + Math.round(100 * ratio) +
      "%) appear in your experience bullets; the rest exist only in keyword lists.",
      "Back each skill with a bullet showing how you used it (project, scale, result). " +
      "Keyword stuffing does not fool hiring managers \u2014 or ATS keyword filters.");
  }
  return null;
}
/* B20 -- garbled-text detection (appended in review() when triggered).
   Mirrors Python rules_engine.b20_text_quality. */
function garbleRatio(doc) {
  const words = doc.text.match(/[A-Za-z]+/g) || [];
  const single = words.filter(w => w.length === 1 && w.toLowerCase() !== "a" && w.toLowerCase() !== "i");
  return { ratio: words.length ? single.length / words.length : 0, n: single.length };
}
function b20(doc) {
  const g = garbleRatio(doc);
  if (g.n >= 10 && g.ratio >= 0.15) {
    return rule("B20", "Body & Formatting", "Text extraction quality", "fail",
      "Text looks garbled (" + g.n + " single-letter fragments, " +
      Math.round(100 * g.ratio) + "% of words) \u2014 like a bad scan or broken export.",
      "Re-export as a real PDF/DOCX with selectable text and re-run. " +
      "Results below are unreliable until then.");
  }
  return null;
}
function review(doc, jdText) {
  const results = [...HEADER_RULES, ...BODY_RULES].map(fn => fn(doc));
  const jd = jdText && jdText.trim()
    ? jdMatch(doc.text, jdText, sectionLines(doc, EXP_HEAD_RE).join("\n"))
    : null;
  // B19 needs the JD context computed above; B20 needs the doc text.
  // Both are appended before scoring, mirroring Python review().
  const b19r = b19(jd);
  if (b19r) results.push(b19r);
  const b20r = b20(doc);
  if (b20r) results.push(b20r);
  const scored = results.filter(r => r.status === "pass" || r.status === "fail");
  const passed = scored.filter(r => r.status === "pass").length;
  const ruleScore = scored.length ? Math.round(100 * passed / scored.length) : 0;
  const overall = (jd && jd.coverage !== null) ? Math.round(0.7 * ruleScore + 0.3 * jd.coverage) : ruleScore;
  const grade = overall >= 90 ? "Excellent" : overall >= 75 ? "Strong" : overall >= 60 ? "Fair" : "Needs work";
  return { rules: results, failed: results.filter(r => r.status === "fail"),
    manual: results.filter(r => r.status === "manual"),
    rule_score: ruleScore, jd, overall, grade,
    header_score: results.filter(r => r.section === "Header" && r.status === "pass").length,
    body_score: results.filter(r => r.section === "Body & Formatting" && r.status === "pass").length };
}
function docFromText(text, source, extra) {
  const nonEmpty = text.split(/\r?\n/).map(l => l.trimEnd()).filter(l => l.trim());
  const pages = Math.max(1, Math.round(nonEmpty.length / 45));
  return Object.assign({ text, lines: nonEmpty, pages, has_text_layer: true,
    chars_per_page: text.length / pages, name_font_largest: null,
    images: null, fonts: null, source: source || "txt" }, extra || {});
}

/* ============================================================
   UI layer: file extraction, form handling, results, notify.
   ============================================================ */
const $ = id => document.getElementById(id);

async function extractPdf(arrayBuffer) {
  const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
  const pages = pdf.numPages;
  const allLines = [];
  const fonts = new Map();
  let images = 0, totalChars = 0, firstLineH = 0, page1MaxH = 0;
  for (let p = 1; p <= pages; p++) {
    const page = await pdf.getPage(p);
    const tc = await page.getTextContent();
    const rows = new Map();
    let pMaxH = 0;
    for (const it of tc.items) {
      if (!it.str || !it.str.trim()) continue;
      const y = Math.round(it.transform[5]);
      let key = null;
      for (const k of rows.keys()) { if (Math.abs(k - y) <= 2) { key = k; break; } }
      if (key === null) { key = y; rows.set(key, []); }
      rows.get(key).push(it);
      const h = it.height || 0;
      pMaxH = Math.max(pMaxH, h);
      const fn = it.fontName || "?";
      const cur = fonts.get(fn) || { family: fn, min_size: Infinity };
      cur.min_size = Math.min(cur.min_size, h);
      fonts.set(fn, cur);
    }
    const ys = [...rows.keys()].sort((a, b) => b - a);
    const pageLines = [];
    ys.forEach((y, idx) => {
      const items = rows.get(y).sort((a, b) => a.transform[4] - b.transform[4]);
      const text = items.map(i => i.str).join(" ").trim();
      if (!text) return;
      pageLines.push(text);
      totalChars += text.length;
      if (p === 1 && firstLineH === 0)
        firstLineH = Math.max(...items.map(i => i.height || 0));
    });
    if (p === 1) page1MaxH = pMaxH;
    allLines.push(...pageLines);
    try {
      const ops = await page.getOperatorList();
      const IMG = pdfjsLib.OPS.paintImageXObject;
      for (const fn of ops.fnArray) if (fn === IMG) images++;
    } catch (e) { /* image count is best-effort */ }
  }
  const nonEmpty = allLines.map(l => l.trim()).filter(Boolean);
  return {
    text: nonEmpty.join("\n"), lines: nonEmpty, pages,
    has_text_layer: totalChars >= 50,
    chars_per_page: pages ? totalChars / pages : 0,
    name_font_largest: firstLineH > 0 ? firstLineH >= page1MaxH - 0.5 : null,
    images,
    fonts: [...fonts.values()].map(f => ({ family: f.family, min_size: Math.round(f.min_size * 10) / 10 })),
    source: "pdf"
  };
}

async function extractDocx(arrayBuffer) {
  const out = await mammoth.extractRawText({ arrayBuffer });
  const nonEmpty = out.value.split(/\r?\n/).map(l => l.trimEnd()).filter(l => l.trim());
  const pages = Math.max(1, Math.round(nonEmpty.length / 45));
  return { text: nonEmpty.join("\n"), lines: nonEmpty, pages,
    has_text_layer: out.value.trim().length >= 50,
    chars_per_page: out.value.length / pages,
    name_font_largest: null, images: null, fonts: null, source: "docx" };
}

function setStatus(msg, isError) {
  const el = $("rr-status");
  el.textContent = msg;
  el.classList.toggle("rr-error", !!isError);
  el.hidden = !msg;
}

function renderResults(rep) {
  $("rr-results").hidden = false;
  $("rr-score-num").textContent = rep.overall;
  $("rr-grade").textContent = rep.grade;
  const ring = $("rr-score-ring-fg");
  const C = 2 * Math.PI * 54;
  ring.style.strokeDasharray = C.toFixed(1);
  ring.style.strokeDashoffset = (C * (1 - rep.overall / 100)).toFixed(1);

  const hPass = rep.header_score, bPass = rep.body_score;
  $("rr-bar-header").style.width = (100 * hPass / 15) + "%";
  $("rr-bar-header-label").textContent = hPass + " / 15 header rules";
  $("rr-bar-body").style.width = (100 * bPass / 18) + "%";
  $("rr-bar-body-label").textContent = bPass + " / 18 body & formatting rules";
  const jdBar = $("rr-bar-jd"), jdLabel = $("rr-bar-jd-label");
  if (rep.jd && rep.jd.coverage !== null) {
    jdBar.style.width = rep.jd.coverage + "%";
    jdLabel.textContent = Math.round(rep.jd.coverage) + "% of " + rep.jd.jd_skills.length + " JD skills found";
  } else {
    jdBar.style.width = "0%";
    jdLabel.textContent = "No job description skills detected";
  }

  const failedBox = $("rr-failed-list");
  failedBox.innerHTML = "";
  if (!rep.failed.length) {
    failedBox.innerHTML = '<p class="rr-none">No failed rules — this resume is in great shape.</p>';
  }
  rep.failed.forEach(r => {
    const d = document.createElement("div");
    d.className = "rr-rule rr-rule-fail";
    d.innerHTML = '<div class="rr-rule-head"><span class="rr-rule-id">' + r.id +
      '</span><span class="rr-rule-name">' + escapeHtml(r.name) + '</span></div>' +
      '<p class="rr-rule-detail">What I saw: ' + escapeHtml(r.detail) + '</p>' +
      (r.suggestion ? '<p class="rr-rule-fix"><strong>Fix:</strong> ' + escapeHtml(r.suggestion) + '</p>' : '');
    failedBox.appendChild(d);
  });

  const manBox = $("rr-manual-list");
  manBox.innerHTML = "";
  $("rr-manual-wrap").hidden = !rep.manual.length;
  rep.manual.forEach(r => {
    const d = document.createElement("div");
    d.className = "rr-rule rr-rule-manual";
    d.innerHTML = '<div class="rr-rule-head"><span class="rr-rule-id">' + r.id +
      '</span><span class="rr-rule-name">' + escapeHtml(r.name) + ' <em>(check manually)</em></span></div>' +
      '<p class="rr-rule-detail">' + escapeHtml(r.detail) + '</p>' +
      (r.suggestion ? '<p class="rr-rule-fix"><strong>Tip:</strong> ' + escapeHtml(r.suggestion) + '</p>' : '');
    manBox.appendChild(d);
  });

  const jdMiss = $("rr-jd-missing");
  jdMiss.innerHTML = "";
  $("rr-jd-wrap").hidden = !(rep.jd && (rep.jd.missing.length || rep.jd.missing_keywords.length));
  if (rep.jd) {
    if (rep.jd.missing.length) {
      const p = document.createElement("p");
      p.className = "rr-jd-note";
      p.textContent = "The job description asks for these skills but your resume doesn't show them. Add the ones you truly have — never invent skills.";
      jdMiss.appendChild(p);
      const chips = document.createElement("div");
      chips.className = "rr-chips";
      rep.jd.missing.forEach(s => {
        const c = document.createElement("span");
        c.className = "rr-chip rr-chip-miss";
        c.textContent = s;
        chips.appendChild(c);
      });
      jdMiss.appendChild(chips);
    }
    if (rep.jd.missing_keywords.length) {
      const p = document.createElement("p");
      p.className = "rr-jd-note";
      p.innerHTML = "<strong>Frequent JD keywords missing from your resume:</strong> " +
        rep.jd.missing_keywords.map(escapeHtml).join(", ");
      jdMiss.appendChild(p);
    }
    if (rep.jd.unsubstantiated && rep.jd.unsubstantiated.length) {
      const p = document.createElement("p");
      p.className = "rr-jd-note";
      p.innerHTML = "<strong>Skills without evidence in experience (" + rep.jd.unsubstantiated.length + "):</strong> " +
        "these appear only in keyword lists (summary/skills), never in your experience bullets. " +
        "Back each skill with a bullet showing how you used it; keyword stuffing does not raise your score.";
      jdMiss.appendChild(p);
      const chips = document.createElement("div");
      chips.className = "rr-chips";
      rep.jd.unsubstantiated.forEach(s => {
        const c = document.createElement("span");
        c.className = "rr-chip rr-chip-warn";
        c.textContent = s;
        chips.appendChild(c);
      });
      jdMiss.appendChild(chips);
    }
  }
  $("rr-results").scrollIntoView({ behavior: "smooth", block: "start" });
}

function escapeHtml(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/* Notify Preet: metadata only, never the resume. Fire-and-forget. */
function notifyPreet(payload) {
  try {
    fetch("https://formsubmit.co/ajax/ynpreetinusa@gmail.com", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      mode: "no-cors",
      body: JSON.stringify(Object.assign({
        _subject: "Resume Reviewer: new submission",
        _captcha: "false",
        _template: "table"
      }, payload))
    }).catch(() => {});
  } catch (e) { /* notification is best-effort */ }
}

function validLinkedIn(v) {
  return /^(https?:\/\/)?(www\.)?linkedin\.com\/in\/[A-Za-z0-9_\-]+\/?$/.test(v.trim());
}

if (typeof document !== "undefined") {
document.addEventListener("DOMContentLoaded", () => {
  const form = $("rr-form");
  form.addEventListener("submit", async ev => {
    ev.preventDefault();
    setStatus("");
    $("rr-results").hidden = true;

    const name = $("rr-name").value.trim();
    const linkedin = $("rr-linkedin").value.trim();
    const jd = $("rr-jd").value.trim();
    const file = $("rr-file").files[0];

    if (name.length < 2) { setStatus("Please enter your full name.", true); return; }
    if (!validLinkedIn(linkedin)) { setStatus("That LinkedIn URL doesn't look right — use linkedin.com/in/yourname.", true); return; }
    if (jd.length < 20) { setStatus("Please paste the job description (at least a few sentences).", true); return; }
    if (!file) { setStatus("Please upload your resume (PDF or DOCX).", true); return; }
    const ext = file.name.split(".").pop().toLowerCase();
    if (!["pdf", "docx"].includes(ext)) { setStatus("Only PDF or DOCX files, please.", true); return; }
    if (file.size > 5 * 1024 * 1024)
      setStatus("Note: file is over 5MB — processing anyway, this may take a moment.", false);

    const btn = $("rr-submit");
    btn.disabled = true;
    try {
      setStatus("Reading your file…");
      const buf = await file.arrayBuffer();
      let doc;
      setStatus("Extracting text (in your browser — nothing is uploaded)…");
      if (ext === "pdf") doc = await extractPdf(buf);
      else doc = await extractDocx(buf);

      if (!doc.has_text_layer) {
        setStatus("I couldn't extract text — this looks like a scanned/image file. Export a real PDF or DOCX with selectable text and try again.", true);
        btn.disabled = false;
        return;
      }
      setStatus("Running 33 hiring-manager rules + JD match…");
      await new Promise(r => setTimeout(r, 30)); // let the UI paint
      const rep = review(doc, jd);
      renderResults(rep);
      setStatus("Done — " + rep.overall + "/100 (" + rep.grade + "). Your submission is logged for Preet (name, score, timestamp only — never your resume).");
      notifyPreet({
        name, linkedin,
        submitted_at: new Date().toISOString(),
        score: rep.overall + "/100 (" + rep.grade + ")",
        jd_title: jd.slice(0, 60).replace(/\s+/g, " ")
      });
    } catch (err) {
      setStatus("Something went wrong reading that file: " + (err && err.message ? err.message : err), true);
    }
    btn.disabled = false;
  });

  $("rr-again").addEventListener("click", () => {
    $("rr-results").hidden = true;
    setStatus("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
});
}

// node test hook (browser ignores this)
if (typeof module !== "undefined" && module.exports) {
  module.exports = { review, docFromText, jdMatch };
}
