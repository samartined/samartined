"""Genera activity.svg: repositorios marcados con el topic 'showcase', ordenados por último push."""
import datetime, json, os, urllib.request
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

USER, TOPIC, ROWS = os.environ.get("GH_USER", "samartined"), "showcase", 4
FONTS = os.environ.get("FONTS_DIR", "fonts")
BG, RED, LINE, DIM, CY, SLOT = "#0D1117", "#FF5C57", "#C8383E", "#4A161D", "#5EF6FF", "#160D13"
B, S, MD, MO = "Rajdhani-Bold.ttf", "Rajdhani-SemiBold.ttf", "Rajdhani-Medium.ttf", "ShareTechMono-Regular.ttf"
_f = {}

def font(name):
    return _f.setdefault(name, TTFont(os.path.join(FONTS, name)))

def width(s, name, size, tr=0):
    f = font(name); gs, cmap = f.getGlyphSet(), f.getBestCmap()
    return sum(gs[cmap[ord(c)]].width * size / f["head"].unitsPerEm + tr for c in s if ord(c) in cmap)

def text(s, name, size, x, y, fill, op=1, tr=0):
    f = font(name); gs, cmap, k = f.getGlyphSet(), f.getBestCmap(), size / f["head"].unitsPerEm
    pen, cx = SVGPathPen(gs, ntos=lambda v: ("%.1f" % v).rstrip("0").rstrip(".")), 0
    for c in s:
        if ord(c) not in cmap: continue
        g = gs[cmap[ord(c)]]; g.draw(TransformPen(pen, (k, 0, 0, -k, x + cx, y))); cx += g.width * k + tr
    return f'<path d="{pen.getCommands()}" fill="{fill}" opacity="{op}"/>'

def fit(s, name, size, maxw):
    s = " ".join(s.split())
    if width(s, name, size) <= maxw: return s
    while s and width(s + "...", name, size) > maxw: s = s[:-1]
    return s.rstrip(" ,.;:") + "..."

def ago(ts, now):
    d = (now - datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))).days
    if d < 1: return "TODAY"
    if d < 2: return "1 DAY AGO"
    if d < 14: return f"{d} DAYS AGO"
    if d < 45: return f"{d // 7} WEEKS AGO"
    if d < 365: return f"{d // 30} MONTH{'S' if d >= 60 else ''} AGO"
    return f"{d // 365} YEAR{'S' if d >= 730 else ''} AGO"

def fetch():
    req = urllib.request.Request(f"https://api.github.com/users/{USER}/repos?per_page=100&sort=pushed&type=owner",
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": USER})
    if os.environ.get("GH_TOKEN"): req.add_header("Authorization", "Bearer " + os.environ["GH_TOKEN"])
    repos = json.load(urllib.request.urlopen(req, timeout=30))
    repos = [r for r in repos if TOPIC in (r.get("topics") or []) and not r["fork"] and not r["archived"]]
    return sorted(repos, key=lambda r: r["pushed_at"], reverse=True)[:ROWS]

def build(repos, now):
    W, H = 1200, 366
    o = []; a = o.append
    a(f'<path d="M22 32H1178" stroke="{LINE}" stroke-width="1.5"/>')
    a(f'<path d="M40 32V6H246l12 12V32" fill="#0E2A30" fill-opacity=".6" stroke="{CY}" stroke-width="1.5"/>')
    a(text("RECENTLY UPDATED", S, 20, 56, 26, CY, tr=1.5))
    a(text("UPDATED DAILY", MO, 15, 1178 - width("UPDATED DAILY", MO, 15), 25, RED, .8))
    x0, y0, rw, rh, step = 40, 52, 1120, 64, 78
    for i, r in enumerate(repos):
        y = y0 + i * step; hot = i == 0
        box = f"M{x0} {y}H{x0+rw}V{y+rh-10}l-10 10H{x0}z"
        if hot: a(f'<path d="{box}" fill="#0E2A30" fill-opacity=".85" stroke="{CY}" stroke-width="1.6"/><rect x="{x0}" y="{y}" width="4" height="{rh}" fill="{CY}"/>')
        else: a(f'<path d="{box}" fill="{SLOT}" stroke="{LINE}" stroke-opacity=".5" stroke-width="1.2"/><rect x="{x0}" y="{y}" width="4" height="{rh}" fill="{DIM}"/>')
        a(text(fit(r["name"], S, 23, 820), S, 23, x0 + 20, y + 28, CY if hot else RED, tr=.5))
        a(text(fit(r.get("description") or "", MD, 18, 820), MD, 18, x0 + 20, y + 52, RED, .88))
        lang = (r.get("language") or "-").upper()
        a(f'<rect x="{x0 + 880}" y="{y + 27}" width="9" height="9" fill="{CY}" opacity=".85"/>')
        a(text(lang, MO, 15, x0 + 896, y + 37, CY, .9))
        when = ago(r["pushed_at"], now)
        a(text(when, MO, 15, x0 + rw - 24 - width(when, MO, 15), y + 37, CY if hot else RED, .9))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>' + "".join(o) + "</svg>")

if __name__ == "__main__":
    now = datetime.datetime.now(datetime.timezone.utc)
    open("activity.svg", "w").write(build(fetch(), now))
