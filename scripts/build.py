#!/usr/bin/env python3
"""Build the static site from data/complaints.json.

Pages:
  /              Complaints (the directory; the main page)
  /<model>/      Complaints for one model
  /stats/        By the numbers (charts)
  /record/       Subaru's record (timeline + bulletins)

Every complaint is rendered into the HTML so search engines (and readers without
JavaScript) see the full directory; assets/app.js only adds filtering and paging.

Usage: python3 scripts/build.py   (writes into the repo root)
"""
import collections
import datetime
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_URL = "https://greatergoodguy.github.io/subaru-carplay-issues/"
REPO_URL = "https://github.com/greatergoodguy/subaru-carplay-issues"
RETRIEVED = "October 15, 2026"
SITE_NAME = "Subaru CarPlay Issues"
# Google Form for the owner list. Paste the form's share link (forms.gle/... or docs.google.com/forms/...).
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeSVv6gIO2o5PjsALid5GGaNQbErP8bqMny797x85gv_3aR5w/viewform"
# Contact address for list removal / questions (use a dedicated address, not a personal one).
CONTACT_EMAIL = ""
USB_TSB_DATE = datetime.date(2023, 10, 2)    # TSB 15-314-23
EXTENSION_DATE = datetime.date(2025, 1, 28)  # TSB 15-322-25 / SOA announcement

TAGS = [  # (label in data, slug, display label) in display priority order
    ("CarPlay / Android Auto", "carplay", "CarPlay / Android Auto"),
    ("USB", "usb", "USB dropouts"),
    ("Bluetooth", "bluetooth", "Bluetooth"),
    ("Black / frozen screen", "black-screen", "Black or frozen screen"),
    ("Rebooting", "rebooting", "Rebooting"),
    ("Ghost touch / bubbling screen", "ghost-touch", "Ghost touch / bubbling"),
    ("Backup camera", "backup-camera", "Backup camera lost"),
    ("Audio loss", "audio-loss", "Audio loss"),
    ("Other infotainment failure", "other", "Other failure"),
]
SLUG = {t[0]: t[1] for t in TAGS}
SHORT = {t[0]: t[2] for t in TAGS}
MODEL_ORDER = ["Forester", "Outback", "Legacy", "Ascent", "Crosstrek", "Impreza", "WRX"]
COVERAGE = [  # from TSB 15-322-25R applicability
    ("Forester", "2019–23"), ("Impreza", "2019–23"), ("Crosstrek", "2019–23"),
    ("WRX / STI", "2019–23"), ("Ascent", "2019–22"), ("Outback", "2019–22"), ("Legacy", "2019–22"),
]
TSB_LINKS = {
    "15-322-25R": "https://static.nhtsa.gov/odi/tsbs/2025/MC-11014870-0001.pdf",
    "15-314-23": "https://static.nhtsa.gov/odi/tsbs/2023/MC-10244884-0001.pdf",
    "15-236-18R": "https://static.nhtsa.gov/odi/tsbs/2023/MC-10237273-0001.pdf",
}

# Simple line icons (paths in the style of Lucide, ISC license).
ICONS = {
    "carplay": '<rect x="5" y="2" width="14" height="20" rx="2"/><path d="M12 18h.01"/>',
    "usb": '<circle cx="10" cy="7" r="1"/><circle cx="4" cy="20" r="1"/><path d="M4.7 19.3 19 5"/><path d="m21 3-3 1 2 2Z"/><path d="M9.26 7.68 5 12l2 5"/><path d="m10 14 5 2 3.5-3.5"/><path d="m18 12 1-1 1 1-1 1Z"/>',
    "bluetooth": '<path d="m7 7 10 10-5 5V2l5 5L7 17"/>',
    "black-screen": '<path d="M17 17H4a2 2 0 0 1-2-2V5c0-1.5 1-2 1-2"/><path d="M22 15V5a2 2 0 0 0-2-2H9"/><path d="M8 21h8"/><path d="M12 17v4"/><path d="m2 2 20 20"/>',
    "rebooting": '<path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/>',
    "ghost-touch": '<path d="M14 4.1 12 6"/><path d="m5.1 8-2.9-.8"/><path d="m6 12-1.9 2"/><path d="M7.2 2.2 8 5.1"/><path d="M9.04 9.69a.5.5 0 0 1 .65-.65l11 4.5a.5.5 0 0 1-.07.95l-4.35 1.04a1 1 0 0 0-.74.74l-1.04 4.35a.5.5 0 0 1-.95.07z"/>',
    "backup-camera": '<path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/>',
    "audio-loss": '<path d="M11 4.7a.7.7 0 0 0-1.2-.5L6.4 7.6A1.4 1.4 0 0 1 5.4 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.4a1.4 1.4 0 0 1 1 .4l3.4 3.4a.7.7 0 0 0 1.2-.5z"/><path d="m22 9-6 6"/><path d="m16 9 6 6"/>',
    "other": '<circle cx="12" cy="12" r="10"/><path d="M12 8v4"/><path d="M12 16h.01"/>',
    "warn": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "file": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/>',
    "list": '<path d="M3 12h.01"/><path d="M3 18h.01"/><path d="M3 6h.01"/><path d="M8 12h13"/><path d="M8 18h13"/><path d="M8 6h13"/>',
    "chart": '<path d="M3 3v16a2 2 0 0 0 2 2h16"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "arrow": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "lock": '<rect width="18" height="11" x="3" y="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "clipboard": '<rect width="8" height="4" x="8" y="2" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/>',
}

e = html.escape


def icon(name, cls="i"):
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true">{ICONS[name]}</svg>'


def load():
    with open(os.path.join(ROOT, "data", "complaints.json")) as f:
        rows = json.load(f)
    order = [t[0] for t in TAGS]
    for r in rows:
        if r["model"].upper() == "WRX":
            r["model"] = "WRX"
        m, d, y = (r.get("filed") or "01/01/1900").split("/")
        r["_filed"] = datetime.date(int(y), int(m), int(d))
        r["tags"] = sorted(r["tags"], key=order.index)
    rows.sort(key=lambda r: (r["_filed"], r["odi"]), reverse=True)
    return rows


def years_label(rows):
    ys = sorted({r["year"] for r in rows})
    return f"{ys[0]}–{ys[-1]}" if len(ys) > 1 else str(ys[0])


def is_cp(r):
    return bool({"CarPlay / Android Auto", "USB"} & set(r["tags"]))


# ---------- page shell ----------

def page(*, title, description, path, body, root, tab, total, jsonld=None):
    canonical = BASE_URL + path
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    tabs = [("complaints", "", "list", f'Complaints <span class="n">{total}</span>'),
            ("stats", "stats/", "chart", "By the numbers"),
            ("record", "record/", "clock", "Subaru's record"),
            ("join", "join/", "users", "Join the owner list")]
    tab_html = "".join(
        f'<a href="{root}{href}"{" aria-current=\"page\"" if key == tab else ""}>{icon(ic)}{label}</a>'
        for key, href, ic, label in tabs)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{canonical}">
<meta name="twitter:card" content="summary">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{root}assets/style.css">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Crect width='24' height='24' rx='6' fill='%23b42318'/%3E%3Crect x='8' y='5' width='8' height='14' rx='1.5' fill='none' stroke='white' stroke-width='1.8'/%3E%3C/svg%3E">
{ld}
</head>
<body>
<header class="site-head"><div class="wrap">
<div class="top"><a class="brand" href="{root}"><span class="dot">{icon("carplay")}</span>{SITE_NAME}</a>
<span class="note">Independent owner project · Not affiliated with Subaru</span></div>
<nav class="tabs" aria-label="Sections">{tab_html}</nav>
</div></header>
<main>
{body}
</main>
<footer class="site"><div class="wrap">
<p><strong>Independent owner project.</strong> Not affiliated with, endorsed by, or sponsored by Subaru of America, Inc. or Subaru Corporation. Subaru, Forester, Outback, Legacy, Ascent, Crosstrek, Impreza, WRX, and Starlink are trademarks of their respective owners and are used only to identify the vehicles discussed.</p>
<p>Complaint text is from NHTSA's public complaint database (retrieved {RETRIEVED}). Complaints are owner reports that NHTSA has not verified. Headlines and symptom tags are this site's own summaries. Nothing here is legal advice.</p>
<p>Spotted an error? <a href="{REPO_URL}/issues">Open an issue on GitHub</a> · <a href="{root}data/complaints.json">Download the data (JSON)</a> · <a href="{root}stats/#method">How this was built</a></p>
</div></footer>
<script src="{root}assets/app.js" defer></script>
</body>
</html>
"""


# ---------- complaints (directory) ----------

def facts(rows, root):
    total = len(rows)
    after_usb = sum(1 for r in rows if r["_filed"] >= USB_TSB_DATE)
    return f"""<div class="facts">
<span class="fact"><b>{total}</b>owner complaints</span>
<span class="fact"><b>{sum(1 for r in rows if is_cp(r))}</b>involve CarPlay, Android Auto, or USB</span>
<a class="fact alert" href="{root}record/"><b>{after_usb}</b>filed after Subaru's USB fix bulletin (Oct 2023)</a>
</div>"""


def model_nav(all_rows, root, current=None):
    counts = collections.Counter(r["model"] for r in all_rows)
    links = [f'<a href="{root}"{" aria-current=\"page\"" if current is None else ""}>All models <span class="n">{len(all_rows)}</span></a>']
    for m in MODEL_ORDER:
        if counts[m]:
            cur = ' aria-current="page"' if m == current else ""
            links.append(f'<a href="{root}{m.lower()}/"{cur}>{m} <span class="n">{counts[m]}</span></a>')
    return f'<nav class="modelnav" aria-label="Filter by model">{"".join(links)}</nav>'


def complaint_html(r):
    primary = SLUG[r["tags"][0]]
    tags = "".join(f'<span class="tag">{e(SHORT[t])}</span>' for t in r["tags"])
    pre = ""
    if r.get("safety"):
        pre += f'<span class="tag safety">{icon("warn")}Safety impact</span>'
    slugs = "|".join(SLUG[t] for t in r["tags"])
    filed = r["_filed"].strftime("%b %-d, %Y")
    nhtsa = f"https://www.nhtsa.gov/vehicle/{r['year']}/SUBARU/{r['model'].upper()}"
    after = 1 if r["_filed"] >= EXTENSION_DATE else 0
    return f"""<article class="card c" id="odi-{r['odi']}" data-model="{e(r['model'].lower())}" data-year="{r['year']}" data-tags="{slugs}" data-safety="{1 if r.get('safety') else 0}" data-after="{after}">
<span class="sym">{icon(primary)}</span>
<div>
<h3>{e(r['headline'])}</h3>
<div class="meta"><span class="veh">{r['year']} {e(r['model'])}</span><span>Filed {filed}</span><span>NHTSA #{r['odi']}</span></div>
<div class="tags">{pre}{tags}</div>
<details><summary>Read the owner's complaint</summary>
<blockquote>{e(r['summary'])}</blockquote>
<p class="verify">Public record. Verify by searching #{r['odi']} on <a href="{nhtsa}" rel="nofollow">NHTSA's {r['year']} {e(r['model'])} page</a>.</p>
</details>
</div>
</article>"""


def directory(rows):
    tag_counts = collections.Counter(t for r in rows for t in r["tags"])
    chips = "".join(
        f'<button type="button" class="chip" data-tag="{slug}" aria-pressed="false">{e(short)} <span class="n">{tag_counts[label]}</span></button>'
        for label, slug, short in TAGS if tag_counts[label])
    year_opts = "".join(f'<option value="{y}">{y}</option>' for y in sorted({r["year"] for r in rows}))
    items = "\n".join(complaint_html(r) for r in rows)
    return f"""<div id="directory">
<div class="card toolbar" role="search">
<div class="row">
<label class="field">{icon("search")}<span class="sr-only">Search complaints</span><input type="search" id="q" placeholder="Search complaints: disconnect, cable, dealer, replaced…"></label>
<select id="f-year" aria-label="Model year"><option value="">All model years</option>{year_opts}</select>
</div>
<div class="row" aria-label="Filter by symptom">{chips}</div>
<div class="row"><label class="toggle"><input type="checkbox" id="f-safety"> Safety impact described</label></div>
<div class="resultbar"><span id="count" aria-live="polite">{len(rows)} complaints</span><button type="button" class="linkbtn" id="clear" hidden>Clear filters</button></div>
</div>
<div class="list" id="complaints">
{items}
</div>
<p class="empty" id="empty" hidden>No complaints match these filters.</p>
<div class="more-wrap"><button type="button" class="btn" id="more" hidden>Show more</button></div>
</div>"""


def complaints_page(rows, all_rows, root, model=None):
    if model:
        yr = years_label(rows)
        h1 = f'Subaru {model} CarPlay &amp; infotainment failures: <span class="hl">{len(rows)} owner complaints</span>'
        lede = (f"Every complaint below was filed with NHTSA by an owner of a {yr} Subaru {model}. Subaru has acknowledged these "
                f"failures in its own service bulletins, and owners are still reporting them.")
    else:
        h1 = 'Subaru CarPlay &amp; infotainment failures: <span class="hl">the owner complaint record</span>'
        lede = ("Every complaint below was filed with NHTSA by a 2019–2023 Subaru owner. Subaru has acknowledged these failures "
                "in its own service bulletins, and owners are still reporting them.")
    return f"""<div class="wrap">
<section class="intro">
<h1>{h1}</h1>
<p class="lede">{lede}</p>
{facts(rows, root)}
</section>
{cta(root)}
{model_nav(all_rows, root, model)}
{directory(rows)}
</div>"""


def cta(root):
    return f"""<a class="card cta" href="{root}join/">
<span class="ic">{icon("users")}</span>
<span class="txt"><b>Has this happened to your Subaru?</b><span>Join the owner list. More owners with documented problems means more leverage with Subaru, including possible group legal action.</span></span>
{icon("arrow")}
</a>"""


# ---------- join ----------

def join_page(root):
    if FORM_URL:
        embed = ""
        if "docs.google.com/forms" in FORM_URL:
            src = FORM_URL.split("?")[0].replace("/edit", "/viewform") + "?embedded=true"
            embed = f'<iframe class="form-embed" src="{e(src)}" title="Owner list sign-up form" loading="lazy">Loading…</iframe>'
        form = f"""<div class="card join-form">
<h2>Sign up</h2>
<p>It takes about a minute. No Google account needed.</p>
<p><a class="btn primary big" href="{e(FORM_URL)}" target="_blank" rel="noopener">Open the sign-up form {icon("arrow")}</a></p>
{embed}
</div>"""
    else:
        form = """<div class="card join-form placeholder"><h2>Sign up</h2><p>The sign-up form is coming soon.</p></div>"""
    contact = f' To be removed or ask a question, email <a href="mailto:{e(CONTACT_EMAIL)}">{e(CONTACT_EMAIL)}</a>.' if CONTACT_EMAIL else ""
    return f"""<div class="wrap">
<section class="intro">
<p class="eyebrow">Join the owner list</p>
<h1>Owners are stronger together</h1>
<p class="lede">If your 2019–2023 Subaru's CarPlay, USB, Bluetooth, or screen keeps failing, add yourself to the list. One complaint is easy to dismiss. Hundreds of documented owners are not, whether the goal is getting Subaru to fix cars or talking with a consumer-protection law firm about group action.</p>
</section>
<div class="join-grid">
<div class="card join-how">
<h2>What happens when you join</h2>
<ol>
<li><b>You get occasional updates</b> about this issue: new bulletins, repair outcomes, and next steps. No spam, and you can leave anytime.</li>
<li><b>If enough owners join,</b> the list may be used to approach consumer-protection law firms about whether a group case makes sense.</li>
<li><b>Your details go to a law firm only if you say so.</b> The form has a separate checkbox for that.</li>
</ol>
<p class="note">{icon("lock")} This site is run by a Subaru owner, not a law firm. Joining doesn't make you part of any lawsuit, and nothing here is legal advice. Your email is kept in a private sheet, never published, and never sold.{contact}</p>
</div>
{form}
</div>
</div>"""


# ---------- stats ----------

def symptom_chart(rows, root):
    c = collections.Counter(t for r in rows for t in r["tags"])
    items = [(slug, short, c[label]) for label, slug, short in TAGS if c[label]]
    items.sort(key=lambda x: (x[0] == "other", -x[2]))
    mx = max(x[2] for x in items)
    bars = "".join(
        f'<a class="hbar" href="{root}?symptom={slug}#directory" title="See the {n} {e(short)} complaints">'
        f'<span class="lab">{icon(slug)}{e(short)}</span>'
        f'<span><span class="fill" style="width:{n / mx * 100:.1f}%"></span></span>'
        f'<span class="val">{n}</span></a>'
        for slug, short, n in items)
    return f"""<div class="card chart"><h3>What owners report</h3>
<p class="sub">Complaints by symptom (one complaint can list several). Click to see them.</p>
<div class="hbars">{bars}</div></div>"""


def model_chart(rows, root):
    c = collections.Counter(r["model"] for r in rows)
    mx = max(c.values())
    bars = "".join(
        f'<a class="hbar" href="{root}{m.lower()}/" title="See the {c[m]} {m} complaints">'
        f'<span class="lab">{m}</span>'
        f'<span><span class="fill" style="width:{c[m] / mx * 100:.1f}%"></span></span>'
        f'<span class="val">{c[m]}</span></a>'
        for m in sorted((m for m in MODEL_ORDER if c[m]), key=lambda m: -c[m]))
    return f"""<div class="card chart"><h3>By model</h3>
<p class="sub">2019–2023 models listed in Subaru's head unit warranty extension. Click to see them.</p>
<div class="hbars">{bars}</div></div>"""


def years_chart(rows):
    c = collections.Counter(r["_filed"].year for r in rows)
    ys = list(range(min(c), max(c) + 1))
    mx = max(c.values())
    events = {USB_TSB_DATE.year: "USB fix bulletin", EXTENSION_DATE.year: "Warranty extended"}
    cols = "".join(
        f'<div class="col" title="{c[y]} complaints filed in {y}"><span class="v">{c[y]}</span><span class="f" style="height:{c[y] / mx * 100:.1f}%"></span></div>'
        for y in ys)
    xs = "".join(f'<div>{y}{f"<span class=ev>▲ {events[y]}</span>" if y in events else ""}</div>' for y in ys)
    return f"""<div class="card chart wide"><h3>Complaints keep coming after Subaru's fixes</h3>
<p class="sub">Complaints filed with NHTSA per year, with the dates of Subaru's own bulletins</p>
<div class="cols" role="img" aria-label="Complaints filed per year: {', '.join(f'{y}: {c[y]}' for y in ys)}">{cols}</div>
<div class="colx">{xs}</div>
<p class="foot">{ys[-1]} counts run through {RETRIEVED}.</p></div>"""


def stats_page(rows, root):
    total = len(rows)
    after_usb = sum(1 for r in rows if r["_filed"] >= USB_TSB_DATE)
    after_ext = sum(1 for r in rows if r["_filed"] >= EXTENSION_DATE)
    safety = sum(1 for r in rows if r.get("safety"))
    cp = sum(1 for r in rows if is_cp(r))
    kpis = [("", total, "owner complaints reviewed and listed"), ("", cp, "involve CarPlay, Android Auto, or USB"),
            ("", safety, "describe a safety impact while driving"), ("alert", after_ext, "filed after Subaru extended the warranty")]
    k = "".join(f'<div class="card kpi {c}"><b>{v}</b><span>{t}</span></div>' for c, v, t in kpis)
    return f"""<div class="wrap">
<section class="intro">
<p class="eyebrow">By the numbers</p>
<h1>The pattern in {total} owner complaints</h1>
<p class="lede">{after_usb} of these complaints were filed after Subaru published its USB fix for intermittent CarPlay loss, and {after_ext} after it extended the head unit warranty.</p>
</section>
<div class="kpis">{k}</div>
<div class="charts">{years_chart(rows)}{symptom_chart(rows, root)}{model_chart(rows, root)}</div>
<div class="card method" id="method">
<h3>How this data was built</h3>
<p>Source: NHTSA's public complaint database, retrieved {RETRIEVED}, for every model and model year listed in Subaru's head unit warranty extension (TSB 15-322-25R). Each candidate complaint was read individually and kept only if the owner describes an actual failure of the head unit, touchscreen, or phone connection (CarPlay, Android Auto, USB, Bluetooth), including failures that also take down the backup camera, climate controls, or driver-assist features shown on that screen. Passing mentions of the radio (for example in dead-battery reports), telematics/SOS subscription issues, and unrelated problems were excluded.</p>
<p>"Safety impact" means the owner reported distraction, lost navigation while driving, or losing the backup camera, climate controls, or driver-assist features. NHTSA complaints are unverified owner reports, and most owners never file one, so these counts are a floor, not a total.</p>
</div>
</div>"""


# ---------- record ----------

def record_page(rows, root):
    after_ext = sum(1 for r in rows if r["_filed"] >= EXTENSION_DATE)
    after_ext_cp = sum(1 for r in rows if r["_filed"] >= EXTENSION_DATE and is_cp(r))
    first = min(r["_filed"] for r in rows)
    events = [
        ("", "2018 – 2020", "Earlier class action over Starlink head units",
         "<em>Udeen v. Subaru of America</em> (D.N.J. 1:18-cv-17334) covered 2017–2018 vehicles with the Harman Gen 3.0 head unit. It settled in 2020 with an extended warranty for that earlier generation.", None),
        ("", first.strftime("%B %Y"), "Owners of 2019+ models begin filing complaints",
         f"The first complaint in this directory about a 2019–2023 head unit was filed with NHTSA in {first.strftime('%B %Y')}.", None),
        ("", "April 2023", "New class action covers 2019–2023 models",
         "<em>Cilluffo v. Subaru of America</em> (D.N.J. 1:23-cv-01897) alleged Starlink infotainment defects in 2019–2023 Outback, Legacy, Forester, Crosstrek, and WRX models, including phone-connection failures.", None),
        ("subaru", "October 2023", "Subaru publishes a USB fix for intermittent CarPlay loss",
         "TSB 15-314-23 describes intermittent loss of CarPlay and Android Auto through the USB port on Gen 3.1 head units, and introduces a redesigned USB terminal. It is officially listed for 2019 models only.", ("15-314-23", "Read TSB 15-314-23")),
        ("", "March 2024", "Court lets most claims proceed",
         "The court denied most of Subaru's motion to dismiss in <em>Cilluffo</em>.", None),
        ("subaru", "January 2025", "Subaru extends the head unit warranty to 8 years / 150,000 miles",
         "TSB 15-322-25 covers head unit failures causing CarPlay/Android Auto, Bluetooth, navigation, or touchscreen to stop working, black screens, lost audio, and reboots, and notes these issues may occur intermittently. Repairs require a dealer to confirm the head unit is the cause.", ("15-322-25R", "Read TSB 15-322-25R")),
        ("", "February 2025", "Class action ends without a class settlement",
         "The <em>Cilluffo</em> named plaintiffs' individual claims were dismissed after a private settlement. No class was certified, and there is no claim process for other owners.", None),
        ("now", f"Since January 2025", f"Owners keep reporting failures: {after_ext} more complaints",
         f"{after_ext} complaints in this directory were filed after the warranty extension was announced, {after_ext_cp} of them involving CarPlay, Android Auto, or USB.", None),
    ]
    items = []
    for kind, when, title, text, link in events:
        btn = f'<a class="btn" href="{TSB_LINKS[link[0]]}">{icon("file")}{link[1]} (PDF)</a>' if link else ""
        cls = "card ev-item" + (" subaru" if kind == "subaru" else "") + (" now" if kind == "now" else "")
        extra = ""
        items.append(f'<div class="{cls}"><span class="when">{when}</span><h3>{title}</h3><p>{text}{extra}</p>{btn}</div>')
    return f"""<div class="wrap">
<section class="intro">
<p class="eyebrow">Subaru's record</p>
<h1>What Subaru has acknowledged, and when</h1>
<p class="lede">Subaru's own technical service bulletins describe the same failures owners report: CarPlay dropping, USB connections cutting out, and head units failing. Here's the timeline, with links to the documents Subaru filed with NHTSA.</p>
</section>
<p class="legend"><span><i class="s"></i>Subaru's own bulletins</span><span><i></i>Lawsuits and complaints</span></p>
<div class="timeline">{"".join(items)}</div>

<section class="section" id="bulletins">
<div class="section-head"><h2>The bulletins</h2><p>Technical service bulletins are instructions Subaru issues to its dealers. These are the public copies filed with NHTSA.</p></div>
<div class="faq">
<details class="card" open><summary>TSB 15-322-25R: head unit warranty extension (Jan 2025)</summary><div>
<p>Extends coverage on Gen 3.1 and CP1 head units to 8 years / 150,000 miles for failures causing a black or blank screen, loss of audio, repeated rebooting, or inability to use CarPlay/Android Auto, navigation, Bluetooth, or the touchscreen. Repair path: software update first, then head unit replacement if the fault remains. Listed vehicles:</p>
<div class="covered">{"".join(f'<span class="pill"><b>{m}</b> {y}</span>' for m, y in COVERAGE)}</div>
<p style="margin-top:12px"><a class="btn primary" href="{TSB_LINKS['15-322-25R']}">{icon("file")}Read the bulletin (PDF)</a></p>
</div></details>
<details class="card"><summary>TSB 15-314-23: redesigned USB terminal (Oct 2023)</summary><div>
<p>Addresses intermittent communication loss with CarPlay and Android Auto through the USB port on Gen 3.1 Harman head units, with a new USB terminal and adapter cord. Officially listed for 2019 models.</p>
<p><a class="btn" href="{TSB_LINKS['15-314-23']}">{icon("file")}Read the bulletin (PDF)</a></p>
</div></details>
<details class="card"><summary>TSB 15-236-18R: Gen 3.1 head unit software (rev. May 2023)</summary><div>
<p>The software reprogramming procedure for Harman Gen 3.1 head units, including 2019–2023 Forester. Under the warranty extension, this is the first repair step before a replacement.</p>
<p><a class="btn" href="{TSB_LINKS['15-236-18R']}">{icon("file")}Read the bulletin (PDF)</a></p>
</div></details>
</div>
</section>

<section class="section" id="about">
<div class="section-head"><h2>Why this site exists</h2></div>
<div class="card method" style="margin-top:0">
<p>It was started by a 2023 Forester owner whose wired CarPlay disconnects on its own while driving. The dealer couldn't reproduce it during service visits, even after seeing video of it. Many owners in this directory describe the same thing: an intermittent failure, "could not duplicate," and advice to try another cable or a software update. Each report is easy to dismiss on its own. Together they are a pattern, and this site keeps that record public.</p>
</div>
<div style="margin-top:16px">{cta(root)}</div>
</section>
</div>"""


# ---------- build ----------

def build():
    rows = load()
    total = len(rows)
    pages = []
    dataset_ld = {
        "@context": "https://schema.org", "@type": "Dataset",
        "name": "Subaru infotainment, CarPlay, and USB owner complaints (2019–2023)",
        "description": f"{total} NHTSA owner complaints describing head unit, CarPlay, Android Auto, USB, and Bluetooth failures in 2019–2023 Subaru vehicles covered by TSB 15-322-25R, individually reviewed and tagged by symptom.",
        "url": BASE_URL, "isBasedOn": "https://www.nhtsa.gov/nhtsa-datasets-and-apis",
        "distribution": {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": BASE_URL + "data/complaints.json"},
        "temporalCoverage": "2019/2026",
        "keywords": ["Subaru", "CarPlay", "Android Auto", "USB", "infotainment", "head unit", "Starlink", "NHTSA complaints"],
    }
    common = dict(total=total)

    pages.append(("index.html", page(
        title="Subaru CarPlay Disconnecting & Infotainment Failures: Owner Complaint Record (2019–2023)",
        description=f"{total} NHTSA owner complaints about Subaru CarPlay and Android Auto disconnecting, USB dropouts, Bluetooth failures, and black or rebooting head units in 2019–2023 Forester, Outback, Crosstrek, Ascent, Legacy, Impreza, and WRX. Searchable, with Subaru's own service bulletins.",
        path="", body=complaints_page(rows, rows, ""), root="", tab="complaints", jsonld=dataset_ld, **common)))

    for m in MODEL_ORDER:
        mr = [r for r in rows if r["model"] == m]
        if not mr:
            continue
        yr = years_label(mr)
        pages.append((f"{m.lower()}/index.html", page(
            title=f"Subaru {m} CarPlay & Infotainment Problems: {len(mr)} Owner Complaints ({yr})",
            description=f"{len(mr)} NHTSA owner complaints about {yr} Subaru {m} head unit failures: CarPlay/Android Auto disconnecting, USB dropouts, Bluetooth failures, black or rebooting screens.",
            path=f"{m.lower()}/", body=complaints_page(mr, rows, "../", model=m), root="../", tab="complaints", **common)))

    pages.append(("stats/index.html", page(
        title="Subaru Infotainment Complaints by the Numbers: CarPlay, USB, Bluetooth (2019–2023)",
        description=f"Charts of {total} NHTSA owner complaints about Subaru head unit failures by symptom, model, and year, including complaints filed after Subaru's USB fix bulletin and warranty extension.",
        path="stats/", body=stats_page(rows, "../"), root="../", tab="stats", **common)))
    pages.append(("record/index.html", page(
        title="Subaru Starlink Head Unit Problems: Timeline of TSBs, Warranty Extension, and Lawsuits",
        description="What Subaru has acknowledged about 2019–2023 Starlink head unit failures, and when: TSB 15-314-23 (USB terminal), TSB 15-322-25R (8-year/150k warranty extension), and the Udeen and Cilluffo class actions.",
        path="record/", body=record_page(rows, "../"), root="../", tab="record", **common)))

    pages.append(("join/index.html", page(
        title="Join the Subaru CarPlay & Infotainment Owner List",
        description="Owners of 2019–2023 Subarus with CarPlay, USB, Bluetooth, or head unit failures: join the owner list for updates and possible group action.",
        path="join/", body=join_page("../"), root="../", tab="join", **common)))

    for rel, content in pages:
        out = os.path.join(ROOT, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w") as f:
            f.write(content)

    today = datetime.date.today().isoformat()
    urls = [BASE_URL, BASE_URL + "stats/", BASE_URL + "record/", BASE_URL + "join/"] + [BASE_URL + m.lower() + "/" for m in MODEL_ORDER if any(r["model"] == m for r in rows)]
    with open(os.path.join(ROOT, "sitemap.xml"), "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write("".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls))
        f.write("</urlset>\n")
    with open(os.path.join(ROOT, "robots.txt"), "w") as f:
        f.write(f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}sitemap.xml\n")
    open(os.path.join(ROOT, ".nojekyll"), "w").close()
    print(f"built {len(pages)} pages, {total} complaints")


if __name__ == "__main__":
    build()
