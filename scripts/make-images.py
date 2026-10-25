#!/usr/bin/env python3
"""Draws the site's images until the app can be captured: the app icon and favicons, the Open Graph cards and
the row of app screens, in English and French. Everything is drawn as HTML and SVG, then rendered by Chrome.

    python3 scripts/make-images.py            # everything
    python3 scripts/make-images.py screens    # or: icons, og, walks

Needs Google Chrome and cwebp (brew install webp). Once the app exists, replace the screens
with real captures from the simulator, like scripts/capture-screens.sh in ../porcom.
"""

import math
import os
import random
import struct
import subprocess
import sys
import tempfile

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(SITE, "assets")
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

# The palette: forest green, cream and charcoal.
CREAM = "#f4efe4"
CARD = "#fbf8f1"
CHARCOAL = "#1e211f"
MUTED = "#77756c"
LINE = "#e3dccc"
GREEN = "#2d5a3d"
GREEN_SOFT = "#dfe6d8"
LAND = "#ece6d7"
CONTOUR = "#d3c9b2"
WATER = "#cfdad2"
PARK = "#dde4d1"
STREET = "#fbf8f1"


# Drawing helpers -------------------------------------------------------------------------------------------------

def smooth(points, closed=False):
    """A Catmull-Rom curve through the points, as an SVG path."""
    if closed:
        pts = points[-1:] + points + points[:2]
    else:
        pts = points[:1] + points + points[-1:]
    d = f"M{pts[1][0]:.1f} {pts[1][1]:.1f}"
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d + ("Z" if closed else "")


def contours(cx, cy, rings, step, seed, squash=0.8):
    """Topographic lines: irregular rings around a summit, wobbling a little more as they widen."""
    rnd = random.Random(seed)
    waves = [(rnd.uniform(0.04, 0.1), rnd.randint(2, 4), rnd.uniform(0, 6.3)) for _ in range(3)]
    paths = []
    for r in range(1, rings + 1):
        radius = r * step
        pts = []
        for k in range(36):
            t = k / 36 * 2 * math.pi
            wobble = 1 + sum(a * (1 + r * 0.08) * math.sin(n * t + p + r * 0.15) for a, n, p in waves)
            pts.append((cx + math.cos(t) * radius * wobble, cy + math.sin(t) * radius * wobble * squash))
        paths.append(smooth(pts, closed=True))
    return paths


def mountain_map(w, h, route, seed=4, rings=14, step=26, peaks=None):
    peaks = peaks or [(w * 0.62, h * 0.38), (w * 0.18, h * 0.86)]
    lines = []
    for i, (px, py) in enumerate(peaks):
        lines += contours(px, py, rings if i == 0 else rings // 2, step, seed + i)
    contour_svg = "".join(f'<path d="{d}" fill="none" stroke="{CONTOUR}" stroke-width="{1.4 if j % 5 == 4 else 0.8}"/>'
                          for j, d in enumerate(lines))
    lake = smooth([(w * 0.02, h * 0.1), (w * 0.2, h * 0.04), (w * 0.3, h * 0.16), (w * 0.22, h * 0.3), (w * 0.05, h * 0.26)], True)
    return f"""<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">
      <rect width="{w}" height="{h}" fill="{LAND}"/>
      <path d="{lake}" fill="{WATER}"/>
      {contour_svg}
      {route_svg(route)}
    </svg>"""


def city_map(w, h, route, seed=7, park=None):
    rnd = random.Random(seed)
    streets = []
    x = -20
    while x < w + 40:
        streets.append(f'<path d="M{x:.0f} -20 L{x + h * 0.18:.0f} {h + 20}" stroke="{STREET}" stroke-width="{7 if rnd.random() < 0.2 else 3.5}"/>')
        x += rnd.uniform(26, 40)
    y = -10
    while y < h + 20:
        streets.append(f'<path d="M-20 {y:.0f} L{w + 20} {y - w * 0.08:.0f}" stroke="{STREET}" stroke-width="{7 if rnd.random() < 0.2 else 3.5}"/>')
        y += rnd.uniform(30, 46)
    park_svg = ""
    if park:
        park_svg = f'<path d="{smooth(park, True)}" fill="{PARK}"/>'
    return f"""<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">
      <rect width="{w}" height="{h}" fill="{LAND}"/>
      {park_svg}
      {''.join(streets)}
      {route_svg(route)}
    </svg>"""


def route_svg(route, width=4.2, dots=True):
    d = smooth(route)
    out = f'<path d="{d}" fill="none" stroke="{CARD}" stroke-width="{width + 4}" stroke-linecap="round" stroke-linejoin="round"/>'
    out += f'<path d="{d}" fill="none" stroke="{GREEN}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>'
    if dots:
        (sx, sy), (ex, ey) = route[0], route[-1]
        out += f'<circle cx="{sx}" cy="{sy}" r="6" fill="{CARD}" stroke="{GREEN}" stroke-width="3"/>'
        out += f'<circle cx="{ex}" cy="{ey}" r="6.5" fill="{GREEN}" stroke="{CARD}" stroke-width="3"/>'
    return out


def scale_route(route, sx, sy, ox=0, oy=0):
    return [(ox + x * sx, oy + y * sy) for x, y in route]


# Routes, drawn on a 100 × 100 grid and scaled to each map.
MOUNTAIN = [(12, 88), (20, 80), (26, 70), (24, 60), (32, 52), (40, 50), (46, 42), (52, 36), (60, 30), (66, 34),
            (70, 42), (76, 48), (82, 58), (78, 68), (68, 74), (58, 78), (46, 82), (34, 86), (22, 90)]
BLOCK = [(20, 30), (52, 26), (58, 50), (64, 74), (30, 80), (24, 56), (20, 34)]
PARK_LOOP = [(30, 80), (26, 62), (34, 44), (46, 30), (60, 24), (72, 34), (70, 52), (60, 64), (48, 72), (36, 82)]
CANAL = [(4, 70), (20, 64), (36, 60), (52, 52), (66, 46), (80, 40), (96, 30)]


# Text ---------------------------------------------------------------------------------------------------------------

T = {
    "en": {
        "journal": "Journal", "map": "Map", "stats": "Statistics", "profile": "Profile", "record": "Record",
        "october": "October", "summary": "4 explorations · 35.4 km",
        "entries": [
            ("Sat, Oct 18", "Mont Albert", "Gaspésie National Park", "18.2 km", "6 h 14", "870 m"),
            ("Wed, Oct 15", "Around the block", "Rosemont, Montréal", "2.1 km", "32 min", None),
            ("Sun, Oct 12", "Mount Royal by the Olmsted trail", "Montréal", "6.4 km", "1 h 38", "190 m"),
            ("Thu, Oct 9", "Along the Lachine Canal", "Montréal", "8.7 km", "1 h 55", None),
        ],
        "detail_date": "Saturday, October 18, 2026 · 8:42 a.m.",
        "distance": "Distance", "duration": "Duration", "elevation": "Elevation gain", "summit": "Highest point",
        "note_title": "Note",
        "note": "Fog until the plateau, then the caribou, far off. Cold hands, soup at the top.",
        "recording": "Recording", "paused_hint": "Your route stays on your iPhone",
        "pause": "Pause", "finish": "Finish", "add_photo": "Photo", "add_note": "Note",
        "this_year": "2026", "km_total": "km explored", "explorations": "Explorations", "hours": "Hours outside",
        "gain": "Elevation gain", "places": "Places", "by_month": "Distance by month",
        "months": "JFMAMJJASOND", "longest": "Longest", "shortest": "Shortest", "both_count": "Both count.",
        "your_map": "Your map", "map_sub": "37 places explored since January",
        "around": "Around Montréal", "around_n": "112 explorations",
        "decimal": ".",
    },
    "fr": {
        "journal": "Journal", "map": "Carte", "stats": "Statistiques", "profile": "Profil", "record": "Enregistrer",
        "october": "Octobre", "summary": "4 explorations · 35,4 km",
        "entries": [
            ("Sam. 18 oct.", "Mont Albert", "Parc national de la Gaspésie", "18,2 km", "6 h 14", "870 m"),
            ("Mer. 15 oct.", "Le tour du quartier", "Rosemont, Montréal", "2,1 km", "32 min", None),
            ("Dim. 12 oct.", "Le mont Royal par le chemin Olmsted", "Montréal", "6,4 km", "1 h 38", "190 m"),
            ("Jeu. 9 oct.", "Le long du canal de Lachine", "Montréal", "8,7 km", "1 h 55", None),
        ],
        "detail_date": "Samedi 18 octobre 2026 · 8 h 42",
        "distance": "Distance", "duration": "Durée", "elevation": "Dénivelé positif", "summit": "Point culminant",
        "note_title": "Note",
        "note": "Brouillard jusqu’au plateau, puis les caribous, au loin. Mains gelées, soupe au sommet.",
        "recording": "En cours", "paused_hint": "Ton parcours reste sur ton iPhone",
        "pause": "Pause", "finish": "Terminer", "add_photo": "Photo", "add_note": "Note",
        "this_year": "2026", "km_total": "km explorés", "explorations": "Explorations", "hours": "Heures dehors",
        "gain": "Dénivelé", "places": "Lieux", "by_month": "Distance par mois",
        "months": "JFMAMJJASOND", "longest": "La plus longue", "shortest": "La plus courte", "both_count": "Les deux comptent.",
        "your_map": "Ta carte", "map_sub": "37 lieux explorés depuis janvier",
        "around": "Autour de Montréal", "around_n": "112 explorations",
        "decimal": ",",
    },
}


# Screens --------------------------------------------------------------------------------------------------------------

W, H = 375, 815

ICONS = {
    "journal": '<path d="M6 4h10a2 2 0 0 1 2 2v14H8a2 2 0 0 1-2-2zM6 17a2 2 0 0 1 2-2h10M10 8h4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
    "map": '<path d="M3.5 6.5 9 4.5l6 2 5.5-2v13l-5.5 2-6-2-5.5 2zM9 4.5v13M15 6.5v13" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>',
    "stats": '<path d="M5 19V11M10 19V5M15 19v-6M20 19V8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    "profile": '<circle cx="12" cy="8.5" r="3.6" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M5 20c.8-3.6 3.6-5.4 7-5.4s6.2 1.8 7 5.4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
}

BASE_CSS = f"""
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ width: {W}px; height: {H}px; overflow: hidden; }}
body {{ background: {CREAM}; color: {CHARCOAL}; font-family: -apple-system, "SF Pro Text", system-ui, sans-serif;
  font-size: 15px; -webkit-font-smoothing: antialiased; position: relative; }}
.status {{ height: 50px; display: flex; justify-content: space-between; align-items: center; padding: 6px 30px 0 34px;
  font-weight: 600; font-size: 16px; position: relative; z-index: 3; }}
.status svg {{ height: 12px; }}
.large {{ font-family: ui-serif, "New York", Georgia, serif; font-size: 34px; font-weight: 600; padding: 6px 20px 0; }}
.muted {{ color: {MUTED}; }}
.tabs {{ position: absolute; left: 0; right: 0; bottom: 0; height: 84px; padding: 8px 14px 0; display: flex; justify-content: space-around;
  align-items: flex-start; background: rgb(251 248 241 / 0.92); border-top: 0.5px solid {LINE}; z-index: 4; }}
.tab {{ display: flex; flex-direction: column; align-items: center; gap: 2px; width: 64px; font-size: 10px; font-weight: 500; color: #a5a194; }}
.tab svg {{ width: 26px; height: 26px; }}
.tab.on {{ color: {GREEN}; }}
.rec {{ width: 50px; height: 50px; margin-top: -4px; border-radius: 50%; background: {GREEN}; display: grid; place-items: center;
  box-shadow: 0 6px 14px -6px rgb(45 90 61 / 0.7); }}
.rec span {{ width: 16px; height: 16px; border-radius: 50%; background: {CREAM}; }}
.home-ind {{ position: absolute; bottom: 8px; left: 50%; width: 134px; height: 5px; margin-left: -67px; border-radius: 3px; background: {CHARCOAL}; z-index: 5; }}
.card {{ background: {CARD}; border-radius: 18px; box-shadow: 0 0 0 0.5px {LINE}; }}
.num {{ font-weight: 600; font-variant-numeric: tabular-nums; }}
"""

STATUS = """<div class="status"><span>9:41</span><svg viewBox="0 0 70 12"><rect x="0" y="7" width="3" height="5" rx="1" fill="currentColor"/><rect x="5" y="5" width="3" height="7" rx="1" fill="currentColor"/><rect x="10" y="2.5" width="3" height="9.5" rx="1" fill="currentColor"/><rect x="15" y="0" width="3" height="12" rx="1" fill="currentColor"/><path d="M28 3.5a9 9 0 0 1 12 0l-1.4 1.5a7 7 0 0 0-9.2 0zM30.4 6.2a5.5 5.5 0 0 1 7.2 0L34 10z" fill="currentColor"/><rect x="46" y="0.5" width="21" height="11" rx="3.5" fill="none" stroke="currentColor" stroke-opacity=".4"/><rect x="48" y="2.5" width="17" height="7" rx="2" fill="currentColor"/><rect x="68" y="4" width="1.6" height="4" rx=".8" fill="currentColor" fill-opacity=".4"/></svg></div>"""


def tabs(t, on):
    def tab(key):
        cls = "tab on" if key == on else "tab"
        return f'<div class="{cls}"><svg viewBox="0 0 24 24">{ICONS[key]}</svg>{t[key]}</div>'
    return (f'<nav class="tabs">{tab("journal")}{tab("map")}<div class="rec"><span></span></div>'
            f'{tab("stats")}{tab("profile")}</nav><div class="home-ind"></div>')


def page(body, css=""):
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE_CSS}{css}</style></head><body>{body}</body></html>"


def thumb(kind, w=78, h=78):
    if kind == 0:
        return mountain_map(w, h, scale_route(MOUNTAIN, w / 100, h / 100), rings=8, step=8)
    if kind == 1:
        return city_map(w, h, scale_route(BLOCK, w / 100, h / 100))
    if kind == 2:
        park = scale_route([(14, 90), (10, 50), (30, 20), (70, 10), (92, 40), (86, 80), (50, 96)], w / 100, h / 100)
        return city_map(w, h, scale_route(PARK_LOOP, w / 100, h / 100), seed=3, park=park)
    water = smooth(scale_route([(0, 78), (40, 68), (100, 40), (100, 54), (40, 82), (0, 92)], w / 100, h / 100), True)
    return city_map(w, h, scale_route(CANAL, w / 100, h / 100), seed=11).replace(
        "<path", f'<path d="{water}" fill="{WATER}"/><path', 1)


def screen_home(t):
    css = f"""
    .month {{ display: flex; justify-content: space-between; align-items: baseline; padding: 22px 20px 10px; }}
    .month h2 {{ font-size: 20px; font-weight: 600; }}
    .month p {{ font-size: 13.5px; }}
    .entry {{ display: flex; gap: 14px; margin: 0 16px 12px; padding: 12px; }}
    .entry .t {{ flex: none; width: 78px; height: 78px; border-radius: 12px; overflow: hidden; }}
    .entry .t svg {{ display: block; }}
    .entry .d {{ font-size: 12.5px; text-transform: uppercase; letter-spacing: 0.04em; color: {GREEN}; font-weight: 600; }}
    .entry h3 {{ margin-top: 3px; font-size: 16.5px; font-weight: 600; line-height: 1.2; }}
    .entry .p {{ margin-top: 2px; font-size: 13.5px; }}
    .entry .s {{ margin-top: 7px; display: flex; gap: 12px; font-size: 13.5px; }}
    """
    entries = ""
    for i, (date, name, place, dist, dur, gain) in enumerate(t["entries"]):
        stats = f'<span class="num">{dist}</span><span class="muted num">{dur}</span>'
        if gain:
            stats += f'<span class="muted num">↑ {gain}</span>'
        entries += (f'<div class="entry card"><div class="t">{thumb(i)}</div><div><p class="d">{date}</p>'
                    f'<h3>{name}</h3><p class="p muted">{place}</p><p class="s">{stats}</p></div></div>')
    body = (f'{STATUS}<h1 class="large">{t["journal"]}</h1><div class="month"><h2>{t["october"]}</h2>'
            f'<p class="muted">{t["summary"]}</p></div>{entries}{tabs(t, "journal")}')
    return page(body, css)


def screen_detail(t):
    date, name, place, dist, dur, gain = t["entries"][0]
    summit = "1 151 m" if t["decimal"] == "," else "1,151 m"
    css = f"""
    .map {{ position: absolute; inset: 0 0 auto 0; height: 430px; }}
    .map svg {{ display: block; }}
    .back {{ position: absolute; top: 58px; left: 16px; width: 38px; height: 38px; border-radius: 50%; background: rgb(251 248 241 / 0.9);
      display: grid; place-items: center; z-index: 2; }}
    .sheet {{ position: absolute; top: 400px; left: 0; right: 0; bottom: 0; background: {CREAM}; border-radius: 26px 26px 0 0; padding: 12px 20px 0; }}
    .grab {{ width: 38px; height: 5px; border-radius: 3px; background: {LINE}; margin: 0 auto 14px; }}
    .sheet .d {{ font-size: 13px; }}
    .sheet h1 {{ margin-top: 4px; font-family: ui-serif, "New York", Georgia, serif; font-size: 28px; font-weight: 600; }}
    .sheet .p {{ font-size: 14.5px; margin-top: 1px; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 16px; }}
    .grid div {{ padding: 11px 14px; }}
    .grid p {{ font-size: 12.5px; }}
    .grid b {{ display: block; font-size: 22px; margin-top: 1px; }}
    .note {{ margin-top: 10px; padding: 12px 14px; font-size: 14px; line-height: 1.4; }}
    .note p:first-child {{ font-size: 12.5px; margin-bottom: 3px; }}
    """
    route = scale_route(MOUNTAIN, 3.6, 3.7, ox=8, oy=40)
    body = (f'<div class="map">{mountain_map(W, 430, route, seed=9, rings=16, step=28, peaks=[(250, 170), (40, 380)])}</div>'
            f'{STATUS}<div class="back"><svg width="14" height="14" viewBox="0 0 14 14"><path d="M9 2 4 7l5 5" fill="none" stroke="{CHARCOAL}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></div>'
            f'<div class="sheet"><div class="grab"></div><p class="d muted">{t["detail_date"]}</p><h1>{name}</h1><p class="p muted">{place}</p>'
            f'<div class="grid"><div class="card"><p class="muted">{t["distance"]}</p><b class="num">{dist}</b></div>'
            f'<div class="card"><p class="muted">{t["duration"]}</p><b class="num">{dur}</b></div>'
            f'<div class="card"><p class="muted">{t["elevation"]}</p><b class="num">{gain}</b></div>'
            f'<div class="card"><p class="muted">{t["summit"]}</p><b class="num">{summit}</b></div></div>'
            f'<div class="note card"><p class="muted">{t["note_title"]}</p><p>{t["note"]}</p></div></div>')
    return page(body, css)


def screen_record(t):
    dist = "4,86" if t["decimal"] == "," else "4.86"
    css = f"""
    .map {{ position: absolute; inset: 0; }}
    .map svg {{ display: block; }}
    .panel {{ position: absolute; left: 12px; right: 12px; bottom: 30px; padding: 20px 20px 18px; border-radius: 30px; background: {CARD};
      box-shadow: 0 0 0 0.5px {LINE}, 0 20px 40px -20px rgb(30 33 31 / 0.4); }}
    .live {{ display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 600; color: {GREEN}; text-transform: uppercase; letter-spacing: 0.06em; }}
    .live span {{ width: 8px; height: 8px; border-radius: 50%; background: {GREEN}; box-shadow: 0 0 0 4px {GREEN_SOFT}; }}
    .time {{ margin-top: 6px; font-size: 54px; letter-spacing: -0.01em; line-height: 1.05; }}
    .row {{ display: flex; gap: 28px; margin-top: 10px; }}
    .row b {{ display: block; font-size: 22px; }}
    .row p {{ font-size: 12.5px; }}
    .hint {{ margin-top: 14px; font-size: 12.5px; }}
    .btns {{ display: grid; grid-template-columns: 1fr 1fr 1.3fr 1.3fr; gap: 8px; margin-top: 16px; }}
    .btns div {{ height: 50px; border-radius: 16px; display: grid; place-items: center; font-weight: 600; font-size: 15px; background: {GREEN_SOFT}; color: {GREEN}; }}
    .btns .stop {{ background: {GREEN}; color: {CREAM}; }}
    .me {{ position: absolute; width: 22px; height: 22px; border-radius: 50%; background: #3d7bd9; border: 3px solid #fff;
      box-shadow: 0 0 0 10px rgb(61 123 217 / 0.16); }}
    """
    park = [(-20, 40), (120, 10), (300, 60), (400, 140), (390, 470), (200, 520), (-20, 460)]
    route = [(60, 700), (80, 560), (96, 430), (150, 360), (210, 300), (262, 236), (300, 258), (286, 330), (236, 372), (204, 420)]
    m = city_map(W, H, route, seed=5, park=park).replace(route_svg(route), route_svg(route, dots=False)
        + f'<circle cx="60" cy="700" r="6" fill="{CARD}" stroke="{GREEN}" stroke-width="3"/>')
    body = (f'<div class="map">{m}</div><div class="me" style="left: 193px; top: 409px"></div>{STATUS}'
            f'<div class="panel"><p class="live"><span></span>{t["recording"]}</p><p class="time num">1:12:08</p>'
            f'<div class="row"><div><b class="num">{dist} km</b><p class="muted">{t["distance"]}</p></div>'
            f'<div><b class="num">↑ 148 m</b><p class="muted">{t["elevation"]}</p></div></div>'
            f'<div class="btns"><div>{t["add_photo"]}</div><div>{t["add_note"]}</div><div>{t["pause"]}</div><div class="stop">{t["finish"]}</div></div>'
            f'<p class="hint muted">{t["paused_hint"]}</p></div>')
    return page(body, css)


def screen_stats(t):
    sep = " " if t["decimal"] == "," else ","
    km = [24, 31, 38, 52, 71, 84, 96, 78, 64, 74, 0, 0]
    bars = "".join(f'<div><i style="height: {max(v, 2) * 1.2:.0f}px{"; opacity: .25" if not v else ""}"></i><span>{m}</span></div>'
                   for v, m in zip(km, t["months"]))
    d = t["decimal"]
    css = f"""
    .hero {{ padding: 14px 20px 0; }}
    .hero b {{ font-size: 64px; line-height: 1; letter-spacing: -0.02em; color: {GREEN}; }}
    .hero p {{ margin-top: 4px; font-size: 15px; }}
    .tiles {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; padding: 18px 16px 0; }}
    .tiles div {{ padding: 12px 14px; }}
    .tiles b {{ display: block; font-size: 23px; }}
    .tiles p {{ font-size: 12.5px; }}
    .chart {{ margin: 12px 16px 0; padding: 14px 14px 10px; }}
    .chart h3 {{ font-size: 14px; font-weight: 600; }}
    .bars {{ display: flex; align-items: flex-end; justify-content: space-between; height: 140px; margin-top: 8px; }}
    .bars div {{ display: flex; flex-direction: column; align-items: center; gap: 5px; width: 18px; }}
    .bars i {{ display: block; width: 14px; border-radius: 5px; background: {GREEN}; }}
    .bars span {{ font-size: 10.5px; color: {MUTED}; }}
    .pair {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; padding: 10px 16px 0; }}
    .pair div {{ padding: 12px 14px; }}
    .pair p {{ font-size: 12.5px; }}
    .pair b {{ display: block; font-size: 19px; margin-top: 2px; }}
    .pair span {{ font-size: 12.5px; }}
    """
    body = (f'{STATUS}<h1 class="large">{t["stats"]}</h1>'
            f'<div class="hero"><b class="num">612</b><p class="muted">{t["km_total"]} · {t["this_year"]}</p></div>'
            f'<div class="tiles"><div class="card"><b class="num">128</b><p class="muted">{t["explorations"]}</p></div>'
            f'<div class="card"><b class="num">148</b><p class="muted">{t["hours"]}</p></div>'
            f'<div class="card"><b class="num">9{sep}340 m</b><p class="muted">{t["gain"]}</p></div>'
            f'<div class="card"><b class="num">37</b><p class="muted">{t["places"]}</p></div></div>'
            f'<div class="chart card"><h3>{t["by_month"]}</h3><div class="bars">{bars}</div></div>'
            f'<div class="pair"><div class="card"><p class="muted">{t["longest"]}</p><b class="num">18{d}2 km</b><span class="muted">Mont Albert</span></div>'
            f'<div class="card"><p class="muted">{t["shortest"]}</p><b class="num">0{d}9 km</b><span class="muted">Rosemont</span></div></div>'
            f'{tabs(t, "stats")}')
    return page(body, css)


def screen_map(t):
    css = f"""
    .map {{ position: absolute; inset: 0; }}
    .map svg {{ display: block; }}
    .top {{ position: absolute; top: 56px; left: 16px; right: 16px; padding: 14px 16px; z-index: 2;
      background: rgb(251 248 241 / 0.94); border-radius: 20px; box-shadow: 0 0 0 0.5px {LINE}; }}
    .top h1 {{ font-family: ui-serif, "New York", Georgia, serif; font-size: 25px; font-weight: 600; }}
    .top p {{ font-size: 13.5px; margin-top: 1px; }}
    .chip {{ position: absolute; left: 16px; bottom: 100px; padding: 10px 14px; border-radius: 16px; background: {CARD}; z-index: 2;
      box-shadow: 0 0 0 0.5px {LINE}, 0 10px 24px -14px rgb(30 33 31 / 0.5); font-size: 13.5px; }}
    .chip b {{ display: block; font-size: 15px; }}
    """
    rnd = random.Random(21)
    water = smooth([(-20, 560), (80, 520), (200, 540), (300, 500), (400, 470), (400, 600), (260, 640), (120, 640), (-20, 660)], True)
    island_routes = ""
    # Walks that follow the streets, plus a few longer ones along the river.
    axes = [(0.177, 0.984), (0.997, -0.08)]
    for _ in range(22):
        x, y = rnd.uniform(50, 330), rnd.uniform(170, 470)
        pts = [(x, y)]
        for k in range(rnd.randint(4, 8)):
            ax, ay = axes[k % 2]
            length = rnd.choice((-1, 1)) * rnd.uniform(18, 60)
            x, y = x + ax * length, y + ay * length
            pts.append((x, y))
        d = "M" + " L".join(f"{px:.1f} {py:.1f}" for px, py in pts)
        island_routes += f'<path d="{d}" fill="none" stroke="{GREEN}" stroke-opacity=".5" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>'
    for y in (505, 520):
        walk = [(x, y + 18 * math.sin(x / 60) - x * 0.08) for x in range(20, 360, 40)]
        island_routes += f'<path d="{smooth(walk)}" fill="none" stroke="{GREEN}" stroke-opacity=".55" stroke-width="2.6" stroke-linecap="round"/>'
    far = [(250, 700), (280, 670), (300, 690), (330, 660), (350, 690)]
    mountain = smooth([(160, 300), (190, 250), (250, 240), (270, 290), (230, 330), (180, 330)], True)
    rings = "".join(f'<path d="{d}" fill="none" stroke="{CONTOUR}" stroke-width="0.9"/>' for d in contours(220, 290, 6, 12, 2))
    m = city_map(W, H, [(0, 0), (0, 0)], seed=8).replace(route_svg([(0, 0), (0, 0)]), "")
    m = m.replace("</svg>", f'<path d="{mountain}" fill="{PARK}"/>{rings}<path d="{water}" fill="{WATER}"/>{island_routes}'
                  f'<path d="{smooth(far)}" fill="none" stroke="{GREEN}" stroke-width="2.6" stroke-linecap="round"/></svg>')
    body = (f'<div class="map">{m}</div>{STATUS}<div class="top"><h1>{t["your_map"]}</h1><p class="muted">{t["map_sub"]}</p></div>'
            f'<div class="chip"><b>{t["around"]}</b><span class="muted">{t["around_n"]}</span></div>{tabs(t, "map")}')
    return page(body, css)


SCREENS = {"record": screen_record, "stats": screen_stats, "home": screen_home, "detail": screen_detail, "map": screen_map}


# Rendering ------------------------------------------------------------------------------------------------------------

def render(html, out_png, width, height, scale=2):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(html)
        src = f.name
    try:
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--default-background-color=00000000",
                        f"--force-device-scale-factor={scale}", f"--window-size={width},{height}",
                        "--virtual-time-budget=4000", f"--screenshot={out_png}", f"file://{src}"],
                       check=True, capture_output=True)
    finally:
        os.unlink(src)


def encode(png, base):
    subprocess.run(["cwebp", "-quiet", "-q", "86", png, "-o", base + ".webp"], check=True)


def make_screens():
    tmp = tempfile.mkdtemp()
    for lang, t in T.items():
        out = os.path.join(ASSETS, "screens", lang)
        os.makedirs(out, exist_ok=True)
        for name, fn in SCREENS.items():
            png = os.path.join(tmp, f"{lang}-{name}.png")
            render(fn(t), png, W, H)
            encode(png, os.path.join(out, name))
            print("screen", lang, name)


ICON_SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
  <rect width="1024" height="1024" fill="{GREEN}"/>
  <g fill="none" stroke="{CREAM}" stroke-linecap="round" stroke-linejoin="round">
    <path d="M40 900C220 820 330 420 512 250S820 640 990 880" stroke-opacity=".16" stroke-width="18"/>
    <path d="M150 930C300 840 380 560 512 450S760 720 880 920" stroke-opacity=".16" stroke-width="18"/>
    <path d="M300 820C420 800 640 790 650 735S420 690 400 630 640 590 650 530 470 480 470 430 620 370 640 320" stroke-width="44"/>
  </g>
  <circle cx="300" cy="820" r="38" fill="{GREEN}" stroke="{CREAM}" stroke-width="26"/>
  <circle cx="648" cy="300" r="56" fill="{CREAM}"/>
</svg>"""


def ico(pngs, out):
    """An .ico holding PNG images, which every current browser reads."""
    data = [open(p, "rb").read() for p, _ in pngs]
    header = struct.pack("<HHH", 0, 1, len(pngs))
    offset = 6 + 16 * len(pngs)
    entries = b""
    for (p, size), blob in zip(pngs, data):
        entries += struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(blob), offset)
        offset += len(blob)
    with open(out, "wb") as f:
        f.write(header + entries + b"".join(data))


def make_icons():
    with open(os.path.join(ASSETS, "icon.svg"), "w") as f:
        f.write(ICON_SVG + "\n")
    tmp = tempfile.mkdtemp()
    square = lambda size, radius: page(
        f'<div style="width:{size}px;height:{size}px;border-radius:{radius}%;overflow:hidden">'
        f'{ICON_SVG.replace("<svg ", f"<svg width=\"{size}\" height=\"{size}\" ", 1)}</div>',
        f"html, body {{ width: {size}px; height: {size}px; background: transparent; }}")
    # The app icon, as iOS rounds it; the favicons are a little rounder so they read at small sizes.
    targets = [("icon.png", 512, 22.37), ("apple-touch-icon.png", 180, 0), ("android-chrome-512x512.png", 512, 22.37),
               ("android-chrome-192x192.png", 192, 22.37), ("favicon-32x32.png", 32, 24), ("favicon-16x16.png", 16, 24)]
    for name, size, radius in targets:
        png = os.path.join(tmp, name)
        render(square(size, radius), png, size, size, scale=1)
        os.replace(png, os.path.join(ASSETS, name))
        print("icon", name)
    ico([(os.path.join(ASSETS, "favicon-16x16.png"), 16), (os.path.join(ASSETS, "favicon-32x32.png"), 32)],
        os.path.join(SITE, "favicon.ico"))


OG = {
    "en": ("Every step tells a story.", "A journal of your walks and hikes, for iPhone. Free, no account, no ads."),
    "fr": ("Chaque pas raconte un parcours.", "Le journal de tes marches et randonnées, pour iPhone. Gratuit, sans compte, sans pub."),
}


def make_og():
    for lang, (title, line) in OG.items():
        route = scale_route(MOUNTAIN, 6.2, 5.2, ox=560, oy=60)
        art = mountain_map(1200, 630, route, seed=9, rings=22, step=30, peaks=[(900, 260), (620, 600)])
        html = page(
            f'<div class="art">{art}</div><div class="fade"></div><div class="txt">'
            f'<p class="brand"><img src="file://{ASSETS}/icon.png">Arpente</p><h1>{title}</h1><p class="line">{line}</p></div>',
            f"""html, body {{ width: 1200px; height: 630px; }}
            body {{ font-family: "Inter", -apple-system, system-ui; }}
            .art {{ position: absolute; inset: 0; }}
            .fade {{ position: absolute; inset: 0; background: linear-gradient(90deg, {CREAM} 38%, rgb(244 239 228 / 0) 70%); }}
            .txt {{ position: absolute; left: 80px; top: 92px; width: 600px; }}
            .brand {{ display: flex; align-items: center; gap: 16px; font-size: 30px; font-weight: 600; }}
            .brand img {{ width: 56px; height: 56px; border-radius: 13px; }}
            h1 {{ margin-top: 70px; font-size: 68px; font-weight: 600; line-height: 1.08; letter-spacing: -0.03em; }}
            .line {{ margin-top: 28px; font-size: 26px; line-height: 1.4; color: {MUTED}; width: 560px; text-wrap: balance; }}""")
        html = html.replace("<head>", "<head><link rel='stylesheet' href='https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap'>")
        render(html, os.path.join(ASSETS, f"og-{lang}.png"), 1200, 630, scale=1)
        print("og", lang)


def make_walks():
    """The two maps of the home page's "2 km or 18 km" section, kept as vectors."""
    out = os.path.join(ASSETS, "walks")
    os.makedirs(out, exist_ok=True)
    w, h = 560, 360
    park = scale_route([(70, 8), (98, 20), (96, 60), (78, 70), (64, 40)], w / 100, h / 100)
    block = city_map(w, h, scale_route([(30, 34), (58, 30), (63, 54), (68, 76), (36, 82), (31, 58), (30, 38)], w / 100, h / 100), seed=12, park=park)
    hike = mountain_map(w, h, scale_route(MOUNTAIN, 4.6, 3.2, ox=40, oy=26), seed=9, rings=16, step=22, peaks=[(330, 120), (60, 340)])
    for name, svg in (("neighborhood", block), ("mountain", hike)):
        with open(os.path.join(out, f"{name}.svg"), "w") as f:
            f.write(" ".join(svg.split()) + "\n")
        print("walk", name)


if __name__ == "__main__":
    jobs = sys.argv[1:] or ["icons", "screens", "og", "walks"]
    for job in jobs:
        {"icons": make_icons, "screens": make_screens, "og": make_og, "walks": make_walks}[job]()
