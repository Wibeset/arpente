#!/usr/bin/env python3
"""Build the "best <app> alternatives" guides in English, French and Spanish.

The text lives in scripts/alternatives/{en,fr,es}.py; this script writes the pages and keeps
their entries in sitemap.xml and llms.txt up to date. Run from anywhere:

    python3 scripts/make-alternatives.py
"""
import html
import importlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent / "alternatives"))

SITE = "https://arpente.app"
TODAY = "2026-11-23"
LANGS = ["en", "fr", "es"]

# Order of the pages, their slugs, and when each was first published.
PAGES = [
    ("strava", {"en": "strava-alternative", "fr": "alternative-strava", "es": "alternativa-strava"}, "2026-11-21"),
    ("alltrails", {"en": "alltrails-alternative", "fr": "alternative-alltrails", "es": "alternativa-alltrails"}, "2026-11-21"),
    ("komoot", {"en": "komoot-alternative", "fr": "alternative-komoot", "es": "alternativa-komoot"}, "2026-11-21"),
    ("gaia", {"en": "gaia-gps-alternative", "fr": "alternative-gaia-gps", "es": "alternativa-gaia-gps"}, TODAY),
    ("wikiloc", {"en": "wikiloc-alternative", "fr": "alternative-wikiloc", "es": "alternativa-wikiloc"}, TODAY),
    ("outdooractive", {"en": "outdooractive-alternative", "fr": "alternative-outdooractive", "es": "alternativa-outdooractive"}, TODAY),
    ("mapmywalk", {"en": "map-my-walk-alternative", "fr": "alternative-map-my-walk", "es": "alternativa-map-my-walk"}, TODAY),
    ("relive", {"en": "relive-alternative", "fr": "alternative-relive", "es": "alternativa-relive"}, TODAY),
    ("polarsteps", {"en": "polarsteps-alternative", "fr": "alternative-polarsteps", "es": "alternativa-polarsteps"}, TODAY),
    ("pacer", {"en": "pacer-alternative", "fr": "alternative-pacer", "es": "alternativa-pacer"}, TODAY),
]

LOCALE = {"en": "en_CA", "fr": "fr_CA", "es": "es_ES"}
LANG_NAME = {"en": "English", "fr": "Français", "es": "Español"}

# Per language: home, privacy page, the other guides (path, label, blurb) and the footer links.
LANG = {
    "en": {
        "home": "",
        "privacy": "privacy/",
        "guides": [
            ("walking-journal/", "Walking journal", "A walking journal for your iPhone"),
            ("private-hiking-tracker/", "Private hiking tracker", "A private hiking tracker, with no account"),
            ("gpx-export/", "GPX export", "Export a walk or hike as GPX on iPhone"),
            ("free-walking-app/", "Free walking app", "A free walking app for iPhone, really free"),
            ("quebec-hikes/", "Hikes in Québec", "Three great hikes in Québec"),
            ("montreal-walks/", "Walks in Montréal", "Three walks in Montréal"),
        ],
        "footer": [
            ("support/", "Support"), ("privacy/", "Privacy"),
            ("strava-alternative/", "Strava alternative"), ("alltrails-alternative/", "AllTrails alternative"),
            ("komoot-alternative/", "Komoot alternative"), ("gpx-export/", "GPX export"),
            ("walking-journal/", "Walking journal"), ("quebec-hikes/", "Hikes in Québec"),
            ("montreal-walks/", "Walks in Montréal"),
        ],
    },
    "fr": {
        "home": "fr/",
        "privacy": "fr/confidentialite/",
        "guides": [
            ("fr/journal-de-marche/", "Journal de marche", "Un journal de marche pour ton iPhone"),
            ("fr/suivi-randonnee-sans-compte/", "Suivi de randonnée sans compte", "Un suivi de randonnée privé, sans compte"),
            ("fr/export-gpx/", "Export GPX", "Exporter une marche ou une randonnée en GPX sur iPhone"),
            ("fr/application-marche-gratuite/", "Application de marche gratuite", "Une application de marche gratuite pour iPhone, vraiment gratuite"),
            ("fr/randonnees-quebec/", "Randonnées au Québec", "Trois belles randonnées au Québec"),
            ("fr/marches-montreal/", "Marches à Montréal", "Trois marches à Montréal"),
        ],
        "footer": [
            ("fr/assistance/", "Assistance"), ("fr/confidentialite/", "Confidentialité"),
            ("fr/alternative-strava/", "Alternative à Strava"), ("fr/alternative-alltrails/", "Alternative à AllTrails"),
            ("fr/alternative-komoot/", "Alternative à Komoot"), ("fr/export-gpx/", "Export GPX"),
            ("fr/journal-de-marche/", "Journal de marche"), ("fr/randonnees-quebec/", "Randonnées au Québec"),
            ("fr/marches-montreal/", "Marches à Montréal"),
        ],
    },
    "es": {
        "home": "es/",
        "privacy": "es/privacidad/",
        "guides": [
            ("es/diario-de-caminatas/", "Diario de caminatas", "Un diario de caminatas para tu iPhone"),
            ("es/seguimiento-senderismo-sin-cuenta/", "Seguimiento de senderismo sin cuenta", "Un seguimiento de senderismo privado, sin cuenta"),
            ("es/exportar-gpx/", "Exportar GPX", "Exportar una caminata o ruta en GPX en iPhone"),
            ("es/app-caminar-gratis/", "App para caminar gratis", "Una app gratis para caminar en iPhone, gratis de verdad"),
            ("es/rutas-quebec/", "Rutas en Quebec", "Tres grandes rutas de senderismo en Quebec"),
            ("es/paseos-montreal/", "Paseos en Montreal", "Tres paseos en Montreal"),
        ],
        "footer": [
            ("es/soporte/", "Soporte"), ("es/privacidad/", "Privacidad"),
            ("es/alternativa-strava/", "Alternativa a Strava"), ("es/alternativa-alltrails/", "Alternativa a AllTrails"),
            ("es/alternativa-komoot/", "Alternativa a Komoot"), ("es/exportar-gpx/", "Exportar en GPX"),
            ("es/diario-de-caminatas/", "Diario de caminatas"), ("es/rutas-quebec/", "Rutas en Quebec"),
            ("es/paseos-montreal/", "Paseos en Montreal"),
        ],
    },
}

ORGANIZATION = {
    "@type": "Organization", "@id": f"{SITE}/#organization", "name": "Wibeset", "url": "https://wibeset.ca",
    "logo": {"@type": "ImageObject", "url": f"{SITE}/assets/icon.png", "width": 512, "height": 512},
    "email": "hello@wibeset.ca", "address": {"@type": "PostalAddress", "addressCountry": "CA"},
    "contactPoint": {"@type": "ContactPoint", "contactType": "customer support", "email": "hello@wibeset.ca", "availableLanguage": ["en", "fr"]},
}
WEBSITE = {"@type": "WebSite", "@id": f"{SITE}/#website", "url": f"{SITE}/", "name": "Arpente",
           "inLanguage": ["en", "fr", "es"], "publisher": {"@id": f"{SITE}/#organization"}}

e = html.escape


def path(lang, slug):
    return slug + "/" if lang == "en" else f"{lang}/{slug}/"


def join_names(names, word):
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + f" {word} " + names[-1]


def build(lang, pid, slugs, published, content, all_content):
    ui, rows, apps, page = content.UI, content.ROWS, content.APPS, content.PAGES[pid]
    cfg = LANG[lang]
    here = path(lang, slugs[lang])
    up = "../" * here.count("/")
    rel = lambda p: up + p
    url = f"{SITE}/{here}"
    name = apps[pid]["name"]
    title = f"{page['title']} — Arpente"
    home = rel(cfg["home"])

    alternates = "\n".join(
        f'  <link rel="alternate" hreflang="{l}" href="{SITE}/{path(l, slugs[l])}">' for l in LANGS
    ) + f'\n  <link rel="alternate" hreflang="x-default" href="{SITE}/{path("en", slugs["en"])}">'

    ranking = [("Arpente", page["arpente_best_for"], page["arpente_text"])] + [
        (apps[o]["name"], apps[o]["best_for"], apps[o]["text"]) for o in page["others"]
    ]

    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebPage", "@id": url, "url": url, "name": title, "description": page["description"],
         "inLanguage": lang, "datePublished": published, "dateModified": TODAY,
         "isPartOf": {"@id": f"{SITE}/#website"}, "about": {"@id": f"{SITE}/#app"},
         "mainEntity": {"@id": f"{url}#list"}},
        {"@type": "ItemList", "@id": f"{url}#list", "name": ui["list_name"].format(name=name),
         "itemListOrder": "https://schema.org/ItemListOrderAscending", "numberOfItems": len(ranking),
         "itemListElement": [
             {"@type": "ListItem", "position": i + 1, "name": n,
              **({"url": f"{SITE}/{cfg['home']}"} if i == 0 else {})}
             for i, (n, _, _) in enumerate(ranking)]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Arpente", "item": f"{SITE}/{cfg['home']}"},
            {"@type": "ListItem", "position": 2, "name": page["crumb"], "item": url}]},
        WEBSITE, ORGANIZATION,
    ]}

    items = "\n".join(
        f"""        <li>
          <h3>{i + 1}. {e(n)}</h3>
          <p class="best-for"><strong>{e(ui['best_for'])}:</strong> {e(b)}</p>
          <p>{e(t)}</p>
        </li>""" if lang != "fr" else
        f"""        <li>
          <h3>{i + 1}. {e(n)}</h3>
          <p class="best-for"><strong>{e(ui['best_for'])}&nbsp;:</strong> {e(b)}</p>
          <p>{e(t)}</p>
        </li>"""
        for i, (n, b, t) in enumerate(ranking)
    )

    table_rows = "\n".join(
        f'            <tr><th scope="row">{e(rows[k][0])}</th><td>{e(rows[k][1])}</td><td>{e(v)}</td></tr>'
        for k, v in page["rows"]
    )
    others = [name] + [apps[o]["name"] for o in page["others"]]
    note = ui["note"].format(names=join_names(others, ui["and"]))

    why = "\n".join(f"        <li><strong>{e(b)}</strong> {e(t)}</li>" for b, t in page["why"])

    guides = []
    for oid, oslugs, _ in PAGES:
        if oid == pid:
            continue
        oname = all_content.APPS[oid]["name"]
        guides.append((path(lang, oslugs[lang]), ui["alt_label"].format(name=oname), ui["alt_blurb"].format(name=oname)))
    guides += cfg["guides"]
    guides_html = "\n".join(
        f'        <li><span class="name"><a href="{rel(p)}">{e(l)}</a></span><p>{e(b)}</p></li>' for p, l, b in guides
    )

    footer = "\n".join(
        f'      <a href="{rel(p)}"{" aria-current=\"page\"" if p == here else ""}>{e(l)}</a>' for p, l in cfg["footer"]
    ) + "\n" + "\n".join(
        f'      <a href="{rel(path(l, slugs[l]))}" hreflang="{l}" lang="{l}">{LANG_NAME[l]}</a>' for l in LANGS if l != lang
    )

    og_alt = "\n".join(f'  <meta property="og:locale:alternate" content="{LOCALE[l]}">' for l in LANGS if l != lang)

    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(title)}</title>
  <meta name="description" content="{e(page['description'])}">
  <link rel="canonical" href="{url}">
{alternates}
  <meta name="color-scheme" content="dark">
  <meta name="theme-color" content="#0a0a0b">
  <link rel="icon" href="{rel('favicon.ico')}" sizes="any">
  <link rel="icon" type="image/png" sizes="32x32" href="{rel('assets/favicon-32x32.png')}">
  <link rel="icon" type="image/png" sizes="16x16" href="{rel('assets/favicon-16x16.png')}">
  <link rel="apple-touch-icon" sizes="180x180" href="{rel('assets/apple-touch-icon.png')}">
  <link rel="manifest" href="{rel('site.webmanifest')}">
  <link rel="preload" href="{rel('assets/fonts/headland-one-latin.woff2')}" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="{rel('assets/style.min.css')}">
  <script type="application/ld+json">{json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')}</script>
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Arpente">
  <meta property="og:title" content="{e(title)}">
  <meta property="og:description" content="{e(page['description'])}">
  <meta property="og:url" content="{url}">
  <meta property="og:locale" content="{LOCALE[lang]}">
{og_alt}
  <meta property="og:image" content="{SITE}/assets/og-{lang}.png">
  <meta property="og:image:alt" content="{e(title)}">
  <meta name="twitter:card" content="summary_large_image">
</head>
<body>
  <a class="skip" href="#main">{e(ui['skip'])}</a>
  <main id="main">
    <article class="legal">
      <nav class="breadcrumb" aria-label="{e(ui['breadcrumb'])}">
        <ol>
          <li><a href="{home}"><img src="{rel('assets/icon.png')}" width="20" height="20" alt="">Arpente</a></li>
          <li aria-current="page">{e(page['crumb'])}</li>
        </ol>
      </nav>
      <h1>{e(page['h1'])}</h1>
      <p class="updated">{e(ui['updated'])}</p>

      <p class="lede">{e(page['lede'])}</p>

      <h2>{e(ui['list_heading'].format(name=name))}</h2>
      <ol class="ranking">
{items}
      </ol>

      <h2>{e(ui['glance'].format(name=name))}</h2>
      <div class="table-scroll">
        <table class="compare">
          <thead>
            <tr><th scope="col"><span class="sr-only">{e(ui['feature'])}</span></th><th scope="col">Arpente</th><th scope="col">{e(name)}</th></tr>
          </thead>
          <tbody>
{table_rows}
          </tbody>
        </table>
      </div>
      <p class="note">{e(note)}</p>

      <h2>{e(ui['why'])}</h2>
      <ul>
{why}
      </ul>

      <h2>{e(ui['when'].format(name=name))}</h2>
      <p>{e(page['when'])}</p>

      <h2>{e(ui['soon_heading'])}</h2>
      <p>{ui['soon'].format(home=home)}</p>

      <h2>{e(ui['more'])}</h2>
      <ul class="rows guides">
{guides_html}
      </ul>
    </article>
  </main>

  <footer>
    <nav aria-label="{e(ui['footer_label'])}">
{footer}
    </nav>
    <p>{ui['made']}</p>
  </footer>
  <script src="{rel('assets/main.js')}" defer></script>
</body>
</html>
"""


def update_sitemap(contents):
    file = ROOT / "sitemap.xml"
    text = file.read_text()
    ours = {f"{SITE}/{path(l, s[l])}" for _, s, _ in PAGES for l in LANGS}
    blocks = re.findall(r"  <url>\n.*?  </url>\n", text, flags=re.S)
    first = None
    for b in blocks:
        loc = re.search(r"<loc>(.*?)</loc>", b).group(1)
        if loc in ours:
            first = text.index(b) if first is None else first
            text = text.replace(b, "", 1)
    new = ""
    for _, slugs, _ in PAGES:
        links = "".join(
            f'    <xhtml:link rel="alternate" hreflang="{l}" href="{SITE}/{path(l, slugs[l])}"/>\n' for l in LANGS
        ) + f'    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}/{path("en", slugs["en"])}"/>\n'
        for l in LANGS:
            new += f"  <url>\n    <loc>{SITE}/{path(l, slugs[l])}</loc>\n    <lastmod>{TODAY}</lastmod>\n{links}  </url>\n"
    at = first if first is not None else text.index("</urlset>")
    file.write_text(text[:at] + new + text[at:])


def update_llms(contents):
    file = ROOT / "llms.txt"
    lines = file.read_text().split("\n")
    ours = {f"{SITE}/{path(l, s[l])}" for _, s, _ in PAGES for l in LANGS}
    lines = [ln for ln in lines if not any(f"]({u})" in ln for u in ours)]
    for lang in LANGS:
        privacy = f"]({SITE}/{LANG[lang]['privacy']})"
        at = next(i for i, ln in enumerate(lines) if privacy in ln) + 1
        c = contents[lang]
        entries = [f"- [{c.PAGES[pid]['crumb']}]({SITE}/{path(lang, s[lang])}): {c.PAGES[pid]['description']}"
                   for pid, s, _ in PAGES]
        lines[at:at] = entries
    file.write_text("\n".join(lines))


def main():
    contents = {l: importlib.import_module(l) for l in LANGS}
    for lang, c in contents.items():
        for pid, slugs, published in PAGES:
            out = ROOT / path(lang, slugs[lang]) / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(build(lang, pid, slugs, published, c, c))
            print("wrote", out.relative_to(ROOT))
    update_sitemap(contents)
    update_llms(contents)
    print("updated sitemap.xml and llms.txt")


if __name__ == "__main__":
    main()
