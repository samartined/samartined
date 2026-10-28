"""Genera activity.svg: gráfico de contribuciones con el estilo del perfil."""
import re, datetime, urllib.request, os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

USER = os.environ.get("GH_USER", "samartined")
FONTS = os.environ.get("FONTS_DIR", "fonts")
BG, RED, LINE, DIM, CY = "#0D1117", "#FF5C57", "#C8383E", "#4A161D", "#5EF6FF"
LEVELS = ["#1A1016", "#5A1A22", "#9A2A33", "#D9413F", "#FF5C57"]
_f = {}

def text(s, font, size, x, y, fill, op=1, tr=0):
    f = _f.setdefault(font, TTFont(os.path.join(FONTS, font)))
    gs, cmap, s_ = f.getGlyphSet(), f.getBestCmap(), size / f["head"].unitsPerEm
    pen, cx = SVGPathPen(gs, ntos=lambda v: ("%.1f" % v).rstrip("0").rstrip(".")), 0
    for ch in s:
        g = cmap.get(ord(ch))
        if g is None: continue
        gs[g].draw(TransformPen(pen, (s_, 0, 0, -s_, x + cx, y)))
        cx += gs[g].width * s_ + tr
    return f'<path d="{pen.getCommands()}" fill="{fill}" opacity="{op}"/>', cx

def fetch():
    req = urllib.request.Request(f"https://github.com/users/{USER}/contributions", headers={"User-Agent": "Mozilla/5.0"})
    h = urllib.request.urlopen(req, timeout=30).read().decode()
    cells = re.findall(r'data-date="([\d-]+)" id="(contribution-day-component-(\d+)-(\d+))" data-level="(\d)"', h)
    tips = dict(re.findall(r'for="(contribution-day-component-\d+-\d+)"[^>]*>([^<]*)</tool-tip>', h))
    days = []
    for date, cid, row, col, lvl in cells:
        m = re.match(r"([\d,]+) contribution", tips.get(cid, ""))
        days.append((datetime.date.fromisoformat(date), int(row), int(col), int(lvl), int(m.group(1).replace(",", "")) if m else 0))
    return sorted(days)

def streaks(days):
    cur = best = run = 0
    for d in days:
        run = run + 1 if d[4] else 0
        best = max(best, run)
    for d in reversed(days):
        if d[0] == days[-1][0] and d[4] == 0: continue  # hoy aún sin contribuir no rompe la racha
        if d[4]: cur += 1
        else: break
    return cur, best

def build(days):
    W, H = 1200, 262
    out = []; a = out.append
    t = lambda *k, **kw: (a(text(*k, **kw)[0]), text(*k, **kw)[1])[1]
    ty = 6
    a(f'<path d="M22 {ty+26}H1178" stroke="{LINE}" stroke-width="1.5"/>')
    a(f'<path d="M40 {ty+26}V{ty}H170l12 12V{ty+26}" fill="#0E2A30" fill-opacity=".6" stroke="{CY}" stroke-width="1.5"/>')
    t("ACTIVITY", "Rajdhani-SemiBold.ttf", 20, 56, ty + 20, CY, tr=1.5)
    t("LAST 12 MONTHS", "ShareTechMono-Regular.ttf", 15, 1040, ty + 19, RED, .8)
    cs, gap, gx, gy = 16, 4, 52, 70
    ncol = max(d[2] for d in days) + 1
    gx = (W - (ncol * (cs + gap) - gap)) / 2
    seen = set()
    for date, row, col, lvl, n in days:
        x, y = gx + col * (cs + gap), gy + row * (cs + gap)
        stroke = f' stroke="{LINE}" stroke-opacity=".35"' if lvl == 0 else ""
        a(f'<rect x="{x:.1f}" y="{y}" width="{cs}" height="{cs}" fill="{LEVELS[lvl]}"{stroke}/>')
        if row == 0 and date.day <= 7 and date.month not in seen and col < ncol - 2:
            seen.add(date.month); t(date.strftime("%b").upper(), "ShareTechMono-Regular.ttf", 13, x, gy - 10, RED, .7)
    last = days[-1]
    a(f'<rect x="{gx + last[2]*(cs+gap) - 2:.1f}" y="{gy + last[1]*(cs+gap) - 2}" width="{cs+4}" height="{cs+4}" fill="none" stroke="{CY}" stroke-width="1.5"/>')
    a(f'<rect class="sweep" x="{gx - 2:.1f}" y="{gy - 4}" width="{cs + 4}" height="{7*(cs+gap)+4}" fill="{CY}" opacity=".18"/>')
    total = sum(d[4] for d in days); cur, best = streaks(days)
    sy = 248; x = gx
    for val, lab in [(f"{total:,}", "CONTRIBUTIONS"), (str(cur), "CURRENT STREAK"), (str(best), "LONGEST STREAK")]:
        w = t(val, "Rajdhani-Bold.ttf", 30, x, sy, RED, tr=1)
        w2 = t(lab, "ShareTechMono-Regular.ttf", 15, x + w + 10, sy - 3, CY, .9)
        x += w + 10 + w2 + 60
    lx = gx + ncol * (cs + gap) - gap - 5 * 18 - 70
    t("LESS", "ShareTechMono-Regular.ttf", 13, lx, sy - 4, RED, .7)
    for i, c in enumerate(LEVELS):
        a(f'<rect x="{lx + 42 + i*18:.1f}" y="{sy - 15}" width="13" height="13" fill="{c}"/>')
    t("MORE", "ShareTechMono-Regular.ttf", 13, lx + 42 + 5*18 + 4, sy - 4, RED, .7)
    span = (ncol - 1) * (cs + gap)
    css = (f".sweep{{animation:sw 12s linear infinite}}@keyframes sw{{0%{{transform:translateX(0);opacity:0}}3%{{opacity:.18}}"
           f"97%{{opacity:.18}}100%{{transform:translateX({span:.0f}px);opacity:0}}}}"
           "@media (prefers-reduced-motion:reduce){.sweep{animation:none;opacity:0}}")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
            f'<style>{css}</style><rect width="{W}" height="{H}" fill="{BG}"/>' + "".join(out) + "</svg>")

if __name__ == "__main__":
    open("activity.svg", "w").write(build(fetch()))
