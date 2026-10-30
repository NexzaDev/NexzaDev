"""Render the profile README and its self-hosted SVG cards into assets/svg/.

Run: python scripts/render.py            (live data when a network is available)
     python scripts/render.py --offline  (cached data only)

Every card is one self-contained SVG (CSS and SMIL only, no external fonts or
images) so GitHub can serve it through an <img>. Live numbers (GitHub, LeetCode,
profile views) are fetched on each run; a failed fetch keeps the last good value
in assets/svg/data.json.

Layout and visual language adapted from Sagargupta16/Sagargupta16 (MIT). The
vendor/ card renderers are his published actions; their MIT licenses are kept
next to them.
"""

from __future__ import annotations

import argparse
import datetime
import functools
import json
import os
import re
import urllib.request
from html import escape
from pathlib import Path

from vendor import github_stats_card, leetcode_card

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "svg"
DATA_FILE = OUT / "data.json"
README = ROOT / "README.md"
OFFLINE = False

USER = "NexzaDev"
LEETCODE_USER = "NexzaDev"
SITE = "https://nexza.dev"
EMAIL = "nexzadevbusiness@proton.me"
DESKTOP_MEDIA = "(min-width: 1012px)"

BG, CARD = "#0b1012", "#0f171c"
BLUE, BLUE_LIGHT, SKY = "#2563eb", "#60a5fa", "#38bdf8"
GREEN, AMBER = "#22c55e", "#f59e0b"
MONO = "'JetBrains Mono','SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"
SANS = "'Segoe UI',Inter,-apple-system,BlinkMacSystemFont,Helvetica,Arial,sans-serif"
MONO_CHAR = 7.6
SVG_CLOSE = "</svg>"

TITLE = "Network Engineer · Developer · Cyber Security"
HERO_LINES = [
    TITLE,
    "Networks, protocols and defensive security.",
    "Understand the service before testing it.",
    "Report findings, never exploit them.",
    "Web and scripting support the network work.",
]
HERO_NODES = [(620, 70, "LUA"), (730, 60, "NMAP"), (790, 140, "LINUX"),
              (690, 180, "PY"), (590, 160, "BASH"), (700, 118, "NSE")]
HERO_LINKS = [(0, 5), (1, 5), (2, 5), (3, 5), (4, 5), (0, 1), (2, 3), (3, 4)]

INTRO = [
    "Network engineer and security-minded developer focused on networking, protocols and defensive security. Web development and scripting support that work.",
    "Open-source tools are documented, informational and designed to report findings rather than exploit systems.",
    "Fully self-taught. I learn by reading the documentation, building a minimal implementation, then stress testing it myself.",
]
# (label, role, org, detail)
ROLES = [
    ("ONGOING", "Co-Founder, Lead Developer", "Sonix-Devs", "CYBER SECURITY"),
    ("OCT 2026", "Author, NSE script collection", "NexzaDev", "LUA  |  NMAP"),
]
FOCUS = [
    ("CORE", "Cybersecurity", "Defensive auditing"),
    ("CORE", "Network Security", "Nmap and NSE"),
    ("BUILD", "Discord Automation", "Bots and moderation"),
    ("BUILD", "Web Development", "Next.js and React"),
]
PROJECTS = [
    {"title": "Nmap-NSE-Script-Collection", "date": "October 2026", "tag": "SOURCE",
     "url": "https://github.com/NexzaDev/Nmap-NSE-Script-Collection",
     "text": "Custom Nmap NSE scripts for defensive, informational audits: missing security headers, insecure cookie flags and other misconfigurations across HTTP, DNS, SMB and TLS. Reports, never exploits.",
     "tools": ["Lua", "NSE", "Nmap", "Python"]},
    {"title": "Sonix-Devs", "date": "Ongoing", "tag": "ORG",
     "url": "https://github.com/Sonix-Devs",
     "text": "A cybersecurity focused programming platform building projects in ethical hacking, penetration testing, digital forensics and security research.",
     "tools": ["Security", "Forensics", "Research"]},
]
BACK = [
    ("HackTheBox", "Labs and machines for practical security"),
    ("freeCodeCamp", "Core web development curriculum"),
    ("roadmap.sh", "Structured paths for dev and security"),
    ("DataCode", "CS community with tutorials and practice"),
    ("W3Schools", "Quick reference for web technologies"),
    ("LeetCode", "Algorithms and data structures"),
    ("DevDocs", "Searchable API documentation"),
    ("Discord Developer Docs", "Official docs for apps and bots"),
]
ICON_ROWS = [
    ["linux", "bash", "python", "lua", "git", "github", "vscode", "figma"],
    ["javascript", "typescript", "html", "css", "react", "nextjs", "nodejs", "mongodb", "mysql"],
]
CHIPS = ["NSE", "Nmap", "WebSockets", "SQL", "Canva", "CapCut", "Network Security", "Defensive Auditing"]
HEADERS = [
    ("experience", "01", "Experience", "where I work and what I focus on"),
    ("projects", "02", "Featured Projects", "what I have built"),
    ("stack", "03", "Tech Stack and Tools", "what I work with daily"),
    ("background", "04", "Learning and Background", "where I learn"),
    ("stats", "05", "Coding Stats", "GitHub activity and LeetCode"),
]
CONNECT = [
    ("email", "Email", "protonmail", f"mailto:{EMAIL}"),
    ("discord", "Discord", "discord", "https://discord.com/users/1411992082733863006"),
    ("github", "GitHub", "github", f"https://github.com/{USER}"),
    ("x", "X", "x", f"https://x.com/{USER}"),
    ("instagram", "Instagram", "instagram", "https://www.instagram.com/nexzadev"),
    ("tiktok", "TikTok", "tiktok", "https://www.tiktok.com/@nexzadev"),
    ("portfolio", "Portfolio", "googlechrome", SITE),
    ("leetcode", "LeetCode", "leetcode", f"https://leetcode.com/u/{LEETCODE_USER}/"),
]


# ---------------------------------------------------------------- helpers
def esc(t: str) -> str:
    return escape(t, quote=True)


def svg_open(w, h, label) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">')


def wrap(text: str, width: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        if cur and len(cur) + 1 + len(word) > width:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    return lines + ([cur] if cur else [])


def write(name: str, content: str) -> None:
    (OUT / name).write_text(content + ("\n" if not content.endswith("\n") else ""), encoding="utf-8")


def fetch(url: str, body: dict | None = None, token: str | None = None, timeout: int = 20) -> bytes:
    if OFFLINE:
        raise RuntimeError("network disabled by --offline")
    if not url.startswith("https://"):
        raise ValueError(url)
    headers = {"User-Agent": "NexzaDev-readme-svgs", "Content-Type": "application/json",
               "Referer": "https://leetcode.com"}
    if token:
        headers["Authorization"] = f"bearer {token}"
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
        return resp.read()


def enter(at: float, dur: float = 0.4, shift: str = "", start: str = "0") -> str:
    """Poster-safe entrance: the element's own attributes hold the finished frame."""
    total = at + dur
    times = f'keyTimes="0;{at / total:.3f};1" dur="{total:.2f}s" fill="freeze"'
    out = f'<animate attributeName="opacity" values="{start};{start};1" {times}/>'
    if shift:
        out += f'<animateTransform attributeName="transform" type="translate" values="{shift};{shift};0 0" {times}/>'
    return out


def fade_group(at: float, body: str) -> str:
    return f"<g>{enter(at)}{body}</g>"


def rail(x1, x2, y, begin, dur) -> str:
    length, total = x2 - x1, begin + dur
    return (f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="rgba(255,255,255,0.10)" stroke-width="2"/>'
            f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{BLUE}" stroke-width="2" stroke-dasharray="{length}" stroke-dashoffset="0">'
            f'<animate attributeName="stroke-dashoffset" values="{length};{length};0" keyTimes="0;{begin / total:.3f};1" dur="{total:.2f}s" fill="freeze"/></line>')


def node(x, y, at, color, ring=False) -> str:
    out = ""
    if ring:
        out += (f'<circle class="now" cx="{x}" cy="{y}" r="7" fill="none" stroke="{color}" stroke-width="1.5">'
                f'<animate attributeName="opacity" values="0;1" keyTimes="0;1" calcMode="discrete" dur="{at:.2f}s" fill="freeze"/></circle>')
    return out + (f'<circle cx="{x}" cy="{y}" r="6" fill="{BG}" stroke="{color}" stroke-width="2">{enter(at, 0.3, start="0.25")}</circle>'
                  f'<circle cx="{x}" cy="{y}" r="2.6" fill="{color}">{enter(at, 0.3)}</circle>')


def rotating(lines, x, y, cls, size, color, slot=3.0, anchor="") -> str:
    n, dur, out = len(lines), slot * len(lines), []
    for i, text in enumerate(lines):
        rest = "" if i == 0 else ' opacity="0"'
        a, b, c, d = i / n, i / n + 0.04, i / n + 1 / n - 0.04, i / n + 1 / n
        times = sorted({0.0, round(a, 3), round(b, 3), round(c, 3), round(d, 3), 1.0})
        values = ["1" if round(b, 3) <= t <= round(c, 3) else "0" for t in times]
        out.append(f'<text class="{cls}" x="{x}" y="{y}" {anchor} fill="{color}" font-size="{size}"{rest}>{esc(text)}'
                   f'<animate attributeName="opacity" values="{";".join(values)}" keyTimes="{";".join(f"{t:g}" for t in times)}" '
                   f'dur="{dur}s" repeatCount="indefinite"/></text>')
    return "".join(out)


STYLE = (f"<style>.m{{font-family:{MONO};font-weight:700;letter-spacing:1.2px}}"
         f".n{{font-family:{SANS};font-weight:800;letter-spacing:-1px}}.s{{font-family:{SANS};font-weight:600}}"
         f".t{{font-family:{SANS};font-weight:700}}"
         ".now{animation:ring 2.2s ease-out infinite;transform-origin:center;transform-box:fill-box}"
         "@keyframes ring{0%{opacity:0.9;transform:scale(1)}100%{opacity:0;transform:scale(2.6)}}</style>")


def card_rect(w, h, rx=14, fill=BG) -> str:
    return f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="{fill}" stroke="rgba(255,255,255,0.08)"/>'


# ---------------------------------------------------------------- headers, divider
def render_header(num, title, sub, theme, mobile=False) -> str:
    w, h = (400, 58) if mobile else (840, 64)
    ink = "#f3f4f6" if theme == "dark" else "#0b1012"
    dim = "rgba(255,255,255,0.45)" if theme == "dark" else "rgba(11,16,18,0.55)"
    rule = "rgba(255,255,255,0.10)" if theme == "dark" else "rgba(11,16,18,0.12)"
    kicker = BLUE_LIGHT if theme == "dark" else "#1d4ed8"
    edge = SKY if theme == "dark" else "#0284c7"
    ts = 20 if mobile else 24
    return "".join([
        svg_open(w, h, title),
        f'<defs><linearGradient id="sweep" x1="0" x2="1"><stop offset="0" stop-color="{edge}" stop-opacity="0"/>'
        f'<stop offset="0.5" stop-color="{kicker}"/><stop offset="1" stop-color="{edge}" stop-opacity="0"/></linearGradient></defs>',
        f'<rect x="0" y="12" width="4" height="{h - 34}" rx="2" fill="{BLUE}"/>',
        f'<text x="18" y="24" fill="{kicker}" font-family="{MONO}" font-size="11" font-weight="700" letter-spacing="2">{num}  /  {esc((sub if not mobile else sub[:30]).upper())}</text>',
        f'<text x="18" y="{h - 18}" fill="{ink}" font-family="{SANS}" font-size="{ts}" font-weight="700">{esc(title)}</text>',
        f'<line x1="0" y1="{h - 4}" x2="{w}" y2="{h - 4}" stroke="{rule}" stroke-width="1"/>',
        f'<rect x="-160" y="{h - 5}" width="160" height="2" fill="url(#sweep)">'
        f'<animateTransform attributeName="transform" type="translate" values="0 0;{w + 160} 0" dur="4.5s" repeatCount="indefinite"/></rect>',
        f'<circle cx="{w - 8}" cy="30" r="3" fill="{dim}"/>',
        SVG_CLOSE])


def render_divider() -> str:
    w, h = 840, 14
    return "".join([
        svg_open(w, h, "divider"),
        f'<defs><linearGradient id="pulse" x1="0" x2="1"><stop offset="0" stop-color="{BLUE}" stop-opacity="0"/>'
        f'<stop offset="0.5" stop-color="{BLUE_LIGHT}"/><stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></linearGradient></defs>',
        f'<line x1="0" y1="7" x2="{w}" y2="7" stroke="rgba(127,127,127,0.28)" stroke-width="1"/>',
        f'<circle cx="{w / 2}" cy="7" r="2.5" fill="#4696f9"/>',
        '<rect x="-220" y="6" width="220" height="2" fill="url(#pulse)">'
        '<animateTransform attributeName="transform" type="translate" values="0 0;1060 0" dur="3.6s" repeatCount="indefinite"/></rect>',
        SVG_CLOSE])


# ---------------------------------------------------------------- hero
def render_hero(mobile=False) -> str:
    w, h = (400, 330) if mobile else (840, 250)
    label = f"{USER}. {TITLE}. Greece."
    defs = ('<defs><pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="rgba(255,255,255,0.035)" stroke-width="1"/></pattern>'
            f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0e1a24"/><stop offset="0.7" stop-color="{BG}"/></linearGradient>'
            f'<linearGradient id="scan" x1="0" x2="1"><stop offset="0" stop-color="{SKY}" stop-opacity="0"/><stop offset="0.5" stop-color="{SKY}" stop-opacity="0.10"/><stop offset="1" stop-color="{SKY}" stop-opacity="0"/></linearGradient>'
            f'<clipPath id="card"><rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="18"/></clipPath></defs>')
    parts = [svg_open(w, h, label), STYLE, defs,
             f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="18" fill="url(#bg)" stroke="rgba(255,255,255,0.09)"/>',
             f'<g clip-path="url(#card)"><rect width="{w}" height="{h}" fill="url(#grid)"/><rect x="-200" y="0" width="200" height="{h}" fill="url(#scan)">'
             f'<animateTransform attributeName="transform" type="translate" values="0 0;{w + 400} 0" dur="7s" repeatCount="indefinite"/></rect></g>']
    px = 28 if mobile else 44
    big = 44 if mobile else 58
    parts.append(f'<text class="m" x="{px}" y="56" fill="{BLUE_LIGHT}" font-size="11">HI, I AM</text>')
    parts.append(f'<text class="n" x="{px - 4}" y="{56 + big}" fill="#f8fafc" font-size="{big}">{USER}</text>')
    lines_y = 56 + big + 34
    if mobile:
        parts.append(f'<text class="s" x="{px}" y="{lines_y}" fill="rgba(255,255,255,0.85)" font-size="13">{esc(TITLE)}</text>')
        parts.append(rotating(HERO_LINES[1:], px, lines_y + 24, "s", 13, "rgba(255,255,255,0.6)"))
        pill_y = lines_y + 46
    else:
        parts.append(rotating(HERO_LINES, px, lines_y, "s", 18, "rgba(255,255,255,0.78)"))
        pill_y = lines_y + 24
    pw = 8 + 26 * 7.1 + 20
    parts.append(f'<rect x="{px}" y="{pill_y}" width="{pw:.0f}" height="28" rx="14" fill="{GREEN}14" stroke="{GREEN}55"/>')
    parts.append(f'<circle cx="{px + 18}" cy="{pill_y + 14}" r="4" fill="{GREEN}"><animate attributeName="opacity" values="1;0.35;1" dur="1.8s" repeatCount="indefinite"/></circle>')
    parts.append(f'<text class="m" x="{px + 30}" y="{pill_y + 18}" fill="{GREEN}" font-size="10.5" style="letter-spacing:1px">OPEN TO SECURITY PROJECTS</text>')
    parts.append(f'<text class="m" x="{px + pw + 14:.0f}" y="{pill_y + 18}" fill="rgba(255,255,255,0.6)" font-size="10.5" style="letter-spacing:1px">GREECE</text>')
    if mobile:
        nodes = [(94 + (x - 590) * 1.25, 266 + (y - 60) * 0.5, lab) for x, y, lab in HERO_NODES]
    else:
        nodes = HERO_NODES
    for a, b in HERO_LINKS:
        (x1, y1, _), (x2, y2, _) = nodes[a], nodes[b]
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="rgba(255,255,255,0.12)" stroke-width="1"/>')
    for i, (a, b) in enumerate(HERO_LINKS[:5]):
        (x1, y1, _), (x2, y2, _) = nodes[a], nodes[b]
        parts.append(f'<circle cx="{x1}" cy="{y1}" r="2.6" fill="{SKY}"><animateMotion dur="2.4s" begin="{i * 0.45:.2f}s" repeatCount="indefinite" path="M0 0 L{x2 - x1} {y2 - y1}"/></circle>')
    for i, (x, y, lab) in enumerate(nodes):
        hub = lab == "NSE"
        r = (20 if hub else 15) if mobile else (22 if hub else 17)
        stroke = BLUE if hub else "rgba(255,255,255,0.16)"
        fill = f"{BLUE}26" if hub else CARD
        parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="1.3"><animate attributeName="r" values="{r};{r + 1.5};{r}" dur="3s" begin="{i * 0.4:.1f}s" repeatCount="indefinite"/></circle>'
                     f'<text class="m" x="{x}" y="{y + 3.5}" text-anchor="middle" fill="{BLUE_LIGHT if hub else "rgba(255,255,255,0.7)"}" font-size="{9 if mobile else 10.5}" style="letter-spacing:0.5px">{lab}</text>')
    parts.append(SVG_CLOSE)
    return "".join(parts)


# ---------------------------------------------------------------- badges
def render_badges(data: dict, mobile=False):
    gh, lc = data.get("github") or {}, data.get("leetcode") or {}
    pills = []
    if data.get("views"):
        pills.append(("PROFILE VIEWS", f"{data['views']:,}", BLUE_LIGHT))
    if gh.get("followers") is not None:
        pills.append(("FOLLOWERS", f"{gh['followers']:,}", BLUE_LIGHT))
    if gh.get("stars") is not None:
        pills.append(("TOTAL STARS", f"{gh['stars']:,}", AMBER))
    if lc.get("solved"):
        pills.append(("LEETCODE", f"{lc['solved']} SOLVED", AMBER))
    pills += [("FOCUS", "NETWORK SECURITY", SKY), ("STATUS", "BUILDING", GREEN),
              ("LOCATION", "GREECE", BLUE_LIGHT), ("PORTFOLIO", "NEXZA.DEV", BLUE_LIGHT)]
    maxw = 380 if mobile else 800
    w = 400 if mobile else 840
    sizes = [24 + (len(k) + len(v)) * MONO_CHAR + 18 for k, v, _ in pills]
    rows, cur, curw = [], [], 0
    for p, s in zip(pills, sizes):
        if cur and curw + 12 + s > maxw:
            rows.append(cur)
            cur, curw = [], 0
        cur.append((p, s))
        curw += s + (12 if len(cur) > 1 else 0)
    rows.append(cur)
    h = 8 + len(rows) * 50 - 14
    alt = "; ".join(f"{k.title()} {v}" for k, v, _ in pills)
    parts = [svg_open(w, h, alt), f"<style>.m{{font-family:{MONO};font-weight:700;letter-spacing:1.2px}}</style>"]
    idx = 0
    for r, row in enumerate(rows):
        total = sum(s for _, s in row) + 12 * (len(row) - 1)
        x, y = (w - total) / 2, 4 + r * 50
        for (key, value, color), bw in row:
            kw = 16 + len(key) * MONO_CHAR
            parts.append(f'<g>{enter(0.1 + idx * 0.1, 0.4)}<rect x="{x:.1f}" y="{y}" width="{bw:.1f}" height="36" rx="18" fill="{CARD}" stroke="{color}55"/>'
                         f'<rect x="{x:.1f}" y="{y}" width="{kw:.1f}" height="36" rx="18" fill="{color}1f"/>'
                         f'<text class="m" x="{x + kw / 2:.1f}" y="{y + 22}" text-anchor="middle" fill="rgba(255,255,255,0.6)" font-size="10.5">{key}</text>'
                         f'<text class="m" x="{x + kw + (bw - kw) / 2:.1f}" y="{y + 22}" text-anchor="middle" fill="{color}" font-size="10.5">{esc(value)}</text></g>')
            x += bw + 12
            idx += 1
    parts.append(SVG_CLOSE)
    return "".join(parts), alt


# ---------------------------------------------------------------- intro
def render_intro(mobile=False) -> str:
    w = 400 if mobile else 840
    px = 24 if mobile else 36
    n = 40 if mobile else 92
    size = 13 if mobile else 15
    lh = int(size * 1.6)
    y, body = 54, []
    for p in INTRO:
        for line in wrap(p, n):
            body.append(f'<text class="s" x="{px}" y="{y}" fill="#cbd5e1" font-size="{size}" style="font-weight:500">{esc(line)}</text>')
            y += lh
        y += 12
    y += 4
    body.append(f'<rect x="{px}" y="{y - 8}" width="{w - 2 * px}" height="44" rx="10" fill="{BLUE}14" stroke="{BLUE}66"/>')
    body.append(f'<text class="m" x="{px + 14}" y="{y + 19}" fill="{BLUE_LIGHT}" font-size="10.5">CURRENTLY</text>')
    body.append(f'<text class="m" x="{px + 112}" y="{y + 19}" fill="#f3f4f6" font-size="{10 if mobile else 12.5}">Hardening Nmap-NSE-Script-Collection</text>')
    h = y + 50
    return "".join([svg_open(w, h, "About NexzaDev: self-taught network engineer in Greece. Currently hardening Nmap-NSE-Script-Collection."),
                    STYLE, card_rect(w, h, 14), f'<rect x="0" y="22" width="3" height="28" rx="1.5" fill="{BLUE_LIGHT}"/>',
                    f'<text class="m" x="{px}" y="32" fill="{BLUE_LIGHT}" font-size="10.5">ABOUT</text>', *body, SVG_CLOSE])


# ---------------------------------------------------------------- experience
def render_experience(mobile=False) -> str:
    alt = ("Experience: " + "; ".join(f"{d}, {r}, {o}" for d, r, o, _ in ROLES)
           + ". Focus areas: " + ", ".join(t for _, t, _ in FOCUS))
    if mobile:
        w, px = 400, 28
        h = 56 + len(ROLES) * 78 + 40 + len(FOCUS) * 54 + 16
        parts = [svg_open(w, h, alt), STYLE, card_rect(w, h),
                 f'<text class="m" x="24" y="30" fill="{BLUE_LIGHT}" font-size="10.5">CAREER</text>']
        y = 64
        parts.append(f'<line x1="{px}" y1="{y}" x2="{px}" y2="{y + (len(ROLES) - 1) * 78}" stroke="{BLUE}" stroke-width="2"/>')
        for i, (when, role, org, detail) in enumerate(ROLES):
            cur = i == 0
            color = GREEN if cur else BLUE_LIGHT
            parts.append(fade_group(0.1 + i * 0.15, node(px, y, 0.1 + i * 0.15, color, ring=cur) +
                         f'<text class="m" x="{px + 22}" y="{y - 4}" fill="{color}" font-size="10.5">{when}</text>'
                         f'<text class="t" x="{px + 22}" y="{y + 15}" fill="#f3f4f6" font-size="13.5">{esc(role)}</text>'
                         f'<text class="t" x="{px + 22}" y="{y + 33}" fill="rgba(255,255,255,0.72)" font-size="11.5">{esc(org)}</text>'
                         f'<text class="m" x="{px + 22}" y="{y + 49}" fill="rgba(255,255,255,0.55)" font-size="10">{detail}</text>'))
            y += 78
        y += 6
        parts.append(f'<text class="m" x="24" y="{y}" fill="{GREEN}" font-size="10.5">FOCUS AREAS</text>')
        y += 24
        for i, (kind, title, sub) in enumerate(FOCUS):
            parts.append(fade_group(0.5 + i * 0.12, node(px, y, 0.5 + i * 0.12, SKY) +
                         f'<text class="t" x="{px + 22}" y="{y + 4}" fill="#f3f4f6" font-size="13">{esc(title)}</text>'
                         f'<text class="m" x="{px + 22}" y="{y + 22}" fill="rgba(255,255,255,0.55)" font-size="10">{esc(sub.upper())}</text>'))
            y += 54
        parts.append(SVG_CLOSE)
        return "".join(parts)
    w, h = 840, 330
    left, right, top_y = 250, 590, 84
    start, stagger = 0.1, 0.12
    parts = [svg_open(w, h, alt), STYLE, card_rect(w, h),
             f'<text class="m" x="24" y="30" fill="{BLUE_LIGHT}" font-size="10.5">CAREER</text>',
             rail(left, right, top_y, start, stagger * (len(ROLES) - 1))]
    step = (right - left) / (len(ROLES) - 1)
    for i, (when, role, org, detail) in enumerate(ROLES):
        x, at, cur = left + i * step, start + stagger * i, i == 0
        color = GREEN if cur else BLUE_LIGHT
        parts.append(node(x, top_y, at, color, ring=cur))
        parts.append(fade_group(at,
                     f'<text class="m" x="{x}" y="{top_y - 22}" text-anchor="middle" fill="{color}" font-size="10.5">{when}</text>'
                     f'<text class="t" x="{x}" y="{top_y + 30}" text-anchor="middle" fill="#f3f4f6" font-size="13">{esc(role)}</text>'
                     f'<text class="t" x="{x}" y="{top_y + 47}" text-anchor="middle" fill="rgba(255,255,255,0.72)" font-size="11.5">{esc(org)}</text>'
                     f'<text class="m" x="{x}" y="{top_y + 63}" text-anchor="middle" fill="rgba(255,255,255,0.55)" font-size="10.5">{detail}</text>'))
    open_at = start + stagger + 0.08
    sub_y, sub_left, sub_right, bracket_y = 250, 120, 720, 186
    parts.append(f'<path d="M{left} {top_y + 72} V{bracket_y} H{sub_left} M{left} {bracket_y} H{sub_right}" fill="none" stroke="{GREEN}88" stroke-width="1.4" stroke-dasharray="3 4">{enter(open_at)}</path>')
    parts.append(fade_group(open_at, f'<text class="m" x="{sub_left}" y="{bracket_y - 8}" fill="{GREEN}" font-size="10.5">FOCUS AREAS</text>'))
    parts.append(rail(sub_left, sub_right, sub_y, open_at + 0.1, stagger * (len(FOCUS) - 1)))
    sstep = (sub_right - sub_left) / (len(FOCUS) - 1)
    for i, (kind, title, sub) in enumerate(FOCUS):
        x, at = sub_left + i * sstep, open_at + 0.1 + stagger * i
        parts.append(f'<line x1="{x}" y1="{bracket_y}" x2="{x}" y2="{sub_y - 8}" stroke="rgba(255,255,255,0.12)" stroke-width="1"/>')
        parts.append(node(x, sub_y, at, SKY))
        parts.append(fade_group(at,
                     f'<text class="m" x="{x}" y="{sub_y - 16}" text-anchor="middle" fill="{SKY}" font-size="10.5">{kind}</text>'
                     f'<text class="t" x="{x}" y="{sub_y + 28}" text-anchor="middle" fill="#f3f4f6" font-size="13">{esc(title)}</text>'
                     f'<text class="m" x="{x}" y="{sub_y + 46}" text-anchor="middle" fill="rgba(255,255,255,0.55)" font-size="10.5">{esc(sub.upper())}</text>'))
    parts.append(SVG_CLOSE)
    return "".join(parts)


# ---------------------------------------------------------------- projects
def chips(items, x, y, max_w, color) -> str:
    out, cx = [], x
    for item in items:
        w = 16 + len(item) * 7.5
        if cx + w > x + max_w:
            break
        out.append(f'<rect x="{cx:.1f}" y="{y}" width="{w:.1f}" height="20" rx="10" fill="{color}14" stroke="{color}55"/>'
                   f'<text class="m" x="{cx + w / 2:.1f}" y="{y + 14.5}" text-anchor="middle" fill="{color}" font-size="10.5">{esc(item)}</text>')
        cx += w + 6
    return "".join(out)


def render_project(p: dict, index: int, mobile=False) -> str:
    w = 320 if mobile else 410
    titles = wrap(p["title"], 25 if mobile else 34)
    lines = wrap(p["text"], 34 if mobile else 47)
    body_y = 62 + 24 * len(titles)
    lh = 21 if mobile else 20
    h = max(250 if mobile else 240, body_y + lh * len(lines) + 58)
    body = "".join(f'<text class="s" x="22" y="{body_y + j * lh}" fill="#cbd5e1" font-size="{15 if mobile else 14}" style="font-weight:500">{esc(l)}</text>' for j, l in enumerate(lines))
    return "".join([
        svg_open(w, h, f"{p['title']}: {p['text']}"),
        f"<style>.m{{font-family:{MONO};font-weight:700;letter-spacing:1px}}.t{{font-family:{SANS};font-weight:800}}.s{{font-family:{SANS}}}</style>",
        '<defs><linearGradient id="shine" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="#fff" stop-opacity="0.06"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'<clipPath id="c"><rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="16"/></clipPath></defs>',
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="16" fill="{CARD}" stroke="rgba(255,255,255,0.09)"/>',
        f'<rect x="0" y="22" width="3" height="28" rx="1.5" fill="{BLUE_LIGHT}"/>',
        f'<text class="m" x="22" y="34" fill="{BLUE_LIGHT}" font-size="10.5">{esc(p["date"].upper())}</text>',
        f'<text class="m" x="{w - 22}" y="34" text-anchor="end" fill="#a8b4c1" font-size="10.5">{p["tag"]}</text>',
        "".join(f'<text class="t" x="22" y="{62 + 24 * j}" fill="#f3f4f6" font-size="20">{esc(t)}</text>' for j, t in enumerate(titles)),
        body, chips(p["tools"][:5], 22, h - 38, w - 44, SKY),
        f'<g clip-path="url(#c)"><rect x="-140" y="0" width="120" height="{h}" fill="url(#shine)" transform="skewX(-18)">'
        f'<animateTransform attributeName="transform" type="translate" values="0 0;700 0" dur="6s" begin="{index * 0.7:.1f}s" repeatCount="indefinite" additive="sum"/></rect></g>',
        SVG_CLOSE])


def render_cta(label: str) -> str:
    w, h = 250, 44
    return "".join([svg_open(w, h, label),
                    f"<style>.m{{font-family:{MONO};font-weight:700;letter-spacing:1.2px}}</style>",
                    f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="22" fill="{BLUE}" stroke="{BLUE_LIGHT}88"/>',
                    f'<text class="m" x="{w / 2}" y="27" text-anchor="middle" fill="#fff" font-size="12">{esc(label)}  →</text>', SVG_CLOSE])


# ---------------------------------------------------------------- stack
_PATH_NUMBER = re.compile(r"-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def _short(m: re.Match) -> str:
    v = f"{float(m.group()):.1f}".rstrip("0").rstrip(".")
    v = "0" if v in ("-0", "") else v
    before = m.string[m.start() - 1] if m.start() else " "
    return (" " if before.isdigit() or before == "." else "") + v


def _round_paths(body: str) -> str:
    def one(m: re.Match) -> str:
        d = m.group(1)
        return m.group() if re.search(r"[aA]", d) else f' d="{_PATH_NUMBER.sub(_short, d)}"'
    return re.sub(r' d="([^"]+)"', one, body)


@functools.cache
def fetch_icon(name: str) -> str | None:
    try:
        raw = fetch(f"https://skillicons.dev/icons?i={name}").decode()
    except Exception as exc:  # noqa: BLE001
        print(f"icon {name} failed: {exc}")
        return None
    inner = raw.find("<svg", raw.find("<svg") + 1)
    end = raw.rfind(SVG_CLOSE, 0, raw.rfind(SVG_CLOSE))
    if inner == -1 or end == -1:
        return None
    body = raw[inner:end + len(SVG_CLOSE)]
    body = re.sub(r'\sid="([^"]+)"', lambda m: f' id="{name}-{m.group(1)}"', body)
    body = re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#{name}-{m.group(1)})", body)
    body = re.sub(r'href="#([^"]+)"', lambda m: f'href="#{name}-{m.group(1)}"', body)
    return f'<symbol id="i-{name}" viewBox="0 0 256 256">{_round_paths(body[body.find(">") + 1:body.rfind(SVG_CLOSE)])}</symbol>'


def render_stack(w=840) -> str:
    size, gap = 44, 14
    step = size + gap
    symbols, rows = [], []
    for row in ICON_ROWS:
        syms = [fetch_icon(n) for n in row]
        rows.append(("icons", row) if all(syms) else ("text", [n.title() for n in row]))
        symbols += [s for s in syms if s]
    rows.append(("text", CHIPS))
    ys, y = [], 22
    for kind, _ in rows:
        ys.append(y)
        y += (size if kind == "icons" else 34) + 18
    h = y + 4
    parts = [svg_open(w, h, "Tech stack: " + ", ".join(n for _, r in rows for n in r)),
             f"<style>.m{{font-family:{MONO};font-weight:700}}</style>",
             f"<defs>{''.join(symbols)}"
             f'<linearGradient id="fade" x1="0" x2="1"><stop offset="0" stop-color="{BG}"/><stop offset="0.08" stop-color="{BG}" stop-opacity="0"/>'
             f'<stop offset="0.92" stop-color="{BG}" stop-opacity="0"/><stop offset="1" stop-color="{BG}"/></linearGradient>'
             f'<clipPath id="win"><rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="14"/></clipPath></defs>',
             card_rect(w, h), '<g clip-path="url(#win)">']
    for r, ((kind, items), y) in enumerate(zip(rows, ys)):
        if kind == "icons":
            span = len(items) * step
            reps = int((w + span) // span) + 1
            uses = "".join(f'<use href="#i-{n}" x="{(k * len(items) + i) * step}" y="{y}" width="{size}" height="{size}"/>'
                           for k in range(reps) for i, n in enumerate(items))
        else:
            widths = [len(t) * 8.2 + 30 for t in items]
            span = sum(widths) + 10 * len(items)
            reps = int((w + span) // span) + 1
            uses, x = "", 0.0
            for _ in range(reps):
                for t, cw in zip(items, widths):
                    uses += (f'<rect x="{x:.1f}" y="{y}" width="{cw:.1f}" height="34" rx="17" fill="{CARD}" stroke="{BLUE_LIGHT}55"/>'
                             f'<text class="m" x="{x + cw / 2:.1f}" y="{y + 21}" text-anchor="middle" fill="#e5e7eb" font-size="12">{esc(t)}</text>')
                    x += cw + 10
        values = f"0 0;{-span} 0" if r % 2 == 0 else f"{-span} 0;0 0"
        parts.append(f'<g><animateTransform attributeName="transform" type="translate" values="{values}" dur="{max(len(items) * 1.8, 14):.1f}s" repeatCount="indefinite"/>{uses}</g>')
    parts.append(f'</g><rect x="0" y="0" width="{w}" height="{h}" rx="14" fill="url(#fade)"/></svg>')
    return "".join(parts)


# ---------------------------------------------------------------- learning grid
def render_background(mobile=False) -> str:
    w, gap = (400, 10) if mobile else (840, 10)
    cols = 1 if mobile else 2
    tw, th = (w - gap * (cols - 1)) / cols, 58
    parts = []
    for i, (n, d) in enumerate(BACK):
        r, c = divmod(i, cols)
        x, y = c * (tw + gap), r * (th + gap)
        parts.append(f'<rect x="{x + 0.5}" y="{y + 0.5}" width="{tw - 1}" height="{th - 1}" rx="12" fill="{CARD}" stroke="rgba(255,255,255,0.09)"/>'
                     f'<rect x="{x}" y="{y + 16}" width="3" height="{th - 32}" rx="1.5" fill="{BLUE_LIGHT}"/>'
                     f'<text x="{x + 20}" y="{y + 25}" font-family="{MONO}" font-weight="700" font-size="13" fill="{BLUE_LIGHT}">{esc(n)}</text>'
                     f'<text x="{x + 20}" y="{y + 44}" font-family="{SANS}" font-size="12" fill="#cbd5e1">{esc(d)}</text>')
    rows = (len(BACK) + cols - 1) // cols
    h = rows * th + (rows - 1) * gap
    return svg_open(w, h, "Learning platforms: " + ", ".join(n for n, _ in BACK)) + "".join(parts) + SVG_CLOSE


# ---------------------------------------------------------------- footer and buttons
def render_footer(mobile=False) -> str:
    w, h = (400, 200) if mobile else (840, 172)
    wave = f"M0 110 C {w / 6:.0f} 80, {w / 3:.0f} 140, {w / 2:.0f} 110 S {w * 5 / 6:.0f} 80, {w} 110"
    note = wrap("Open to collaboration on security tooling, NSE scripts and web and Discord automation.", 52 if mobile else 120)
    kicker = "NEXZADEV  |  CYBER SECURITY" if mobile else "NEXZADEV  |  NETWORK ENGINEER · DEVELOPER · CYBER SECURITY"
    return "".join([
        svg_open(w, h, "Thanks for visiting. More at nexza.dev. Open to collaboration on security tooling, NSE scripts and web and Discord automation."),
        f"<style>.s{{font-family:{SANS};font-weight:800}}.m{{font-family:{MONO};font-weight:700;letter-spacing:2px}}.d{{font-family:{SANS};font-weight:500}}</style>",
        card_rect(w, h),
        f'<text class="m" x="{w / 2}" y="34" text-anchor="middle" fill="{BLUE_LIGHT}" font-size="10.5">{kicker}</text>',
        rotating(["Thanks for visiting", "More at nexza.dev"], w / 2, 78, "s", 30, "#f3f4f6", anchor='text-anchor="middle"'),
        f'<path d="{wave}" fill="none" stroke="rgba(127,127,127,0.25)" stroke-width="1.2"/>',
        f'<path d="{wave}" fill="none" stroke="{BLUE_LIGHT}" stroke-width="2" stroke-dasharray="120 900" stroke-linecap="round"><animate attributeName="stroke-dashoffset" values="1020;0" dur="4s" repeatCount="indefinite"/></path>',
        "".join(f'<text class="d" x="{w / 2}" y="{148 + j * 16}" text-anchor="middle" fill="#a8b4c1" font-size="11">{esc(l)}</text>' for j, l in enumerate(note)),
        SVG_CLOSE])


@functools.cache
def simple_icon(slug: str) -> str | None:
    try:
        raw = fetch(f"https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/{slug}.svg").decode()
    except Exception as exc:  # noqa: BLE001
        print(f"simple icon {slug} failed: {exc}")
        return None
    m = re.search(r'<path d="([^"]+)"', raw)
    return m.group(1) if m else None


def render_button(label: str, icon_path: str | None, index: int) -> str:
    w, h = 128, 44
    icon = (f'<svg x="12" y="12" width="20" height="20" viewBox="0 0 24 24"><path d="{icon_path}" fill="rgba(255,255,255,0.9)"/></svg>' if icon_path else "")
    tx, anchor = (40, "") if icon_path else (w / 2, ' text-anchor="middle"')
    return "".join([svg_open(w, h, label),
                    f"<style>.m{{font-family:{MONO};font-weight:700;letter-spacing:0.4px}}</style>",
                    f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="22" fill="{CARD}" stroke="{BLUE_LIGHT}66"/>',
                    f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="22" fill="{BLUE}22" opacity="0"><animate attributeName="opacity" values="0;1;0;0" keyTimes="0;0.1;0.2;1" dur="5s" begin="{index * 0.5:.1f}s" repeatCount="indefinite"/></rect>',
                    icon, f'<text class="m" x="{tx}" y="28"{anchor} fill="#f3f4f6" font-size="12">{esc(label.upper())}</text>', SVG_CLOSE])


def placeholder(title: str, line: str) -> str:
    w, h = 840, 120
    return "".join([svg_open(w, h, f"{title}. {line}"), card_rect(w, h, 16, CARD),
                    f'<text x="28" y="48" font-family="{MONO}" font-size="12" font-weight="700" letter-spacing="2" fill="{BLUE_LIGHT}">{esc(title)}</text>',
                    f'<text x="28" y="82" font-family="{SANS}" font-size="15" fill="#cbd5e1">{esc(line)}</text>', SVG_CLOSE])


# ---------------------------------------------------------------- data
def load_data() -> dict:
    data = json.loads(DATA_FILE.read_text(encoding="utf-8")) if DATA_FILE.exists() else {}
    if OFFLINE:
        return data
    try:
        counts = re.findall(r">(\d[\d,]*)</text>", fetch(f"https://komarev.com/ghpvc/?username={USER.lower()}").decode())
        data["views"] = int(counts[-1].replace(",", ""))
    except Exception as exc:  # noqa: BLE001
        print(f"views fetch failed, keeping cached value: {exc}")
    try:
        query = ("query($u:String!){userContestRanking(username:$u){rating topPercentage attendedContestsCount badge{name}} "
                 "userContestRankingHistory(username:$u){attended rating} allQuestionsCount{difficulty count} "
                 "matchedUser(username:$u){submitStats{acSubmissionNum{difficulty count}}}}")
        raw = fetch("https://leetcode.com/graphql", {"query": query, "variables": {"u": LEETCODE_USER}})
        data["leetcode"] = leetcode_card.parse_profile(json.loads(raw), LEETCODE_USER)
    except Exception as exc:  # noqa: BLE001
        print(f"leetcode fetch failed, keeping cached value: {exc}")
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        try:
            data["github"] = github_stats_card.fetch_stats(USER, token, 6, set())
        except Exception as exc:  # noqa: BLE001
            print(f"github fetch failed, keeping cached value: {exc}")
    else:
        print("no GITHUB_TOKEN, keeping the last github stats")
    data["updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    return data


# ---------------------------------------------------------------- readme
def picture(name: str, alt: str, width="100%") -> str:
    mobile = name.replace(".svg", "-mobile.svg")
    if (OUT / mobile).exists():
        return (f'<picture><source media="{DESKTOP_MEDIA}" srcset="assets/svg/{name}" />'
                f'<img src="assets/svg/{mobile}" width="{width}" alt="{esc(alt)}" /></picture>')
    return f'<picture><img src="assets/svg/{name}" width="{width}" alt="{esc(alt)}" /></picture>'


def header_html(key: str, title: str) -> str:
    srcs = []
    for wide in (True, False):
        for theme in ("light", "dark"):
            name = f"header-{key}-{theme}{'' if wide else '-mobile'}.svg"
            media = f"(prefers-color-scheme: {theme})" + (f" and {DESKTOP_MEDIA}" if wide else "")
            srcs.append(f'<source media="{media}" srcset="assets/svg/{name}" />')
    return f'<picture>{"".join(srcs)}<img src="assets/svg/header-{key}-dark-mobile.svg" width="100%" alt="{esc(title)}" /></picture>'


def link(href: str, inner: str) -> str:
    return f'<a href="{href}">{inner}</a>'


def build_readme(badges_alt: str) -> str:
    div = '<picture><img src="assets/svg/divider.svg" width="100%" alt="" /></picture>'
    connect = '<p align="center">\n' + "\n".join(
        link(url, f'<picture><img src="assets/svg/connect-{key}.svg" width="128" alt="{label}" /></picture>') for key, label, _, url in CONNECT) + "\n</p>"
    hd = {k: header_html(k, t) for k, _, t, _ in HEADERS}
    projects = "\n".join(link(p["url"], f'<picture><source media="{DESKTOP_MEDIA}" srcset="assets/svg/project-{i}.svg" /><img src="assets/svg/project-{i}-mobile.svg" width="400" alt="{esc(p["title"] + ": " + p["text"])}" /></picture>') for i, p in enumerate(PROJECTS))
    cta_img = '<picture><img src="assets/svg/cta-repos.svg" width="250" alt="View all repositories" /></picture>'
    snake = (f'<picture>\n  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/{USER}/{USER}/output/github-snake-dark.svg" />\n'
             f'  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/{USER}/{USER}/output/github-snake.svg" />\n'
             f'  <img alt="Contribution snake" src="https://raw.githubusercontent.com/{USER}/{USER}/output/github-snake-dark.svg" width="100%" />\n</picture>')
    blocks = [
        "<!-- Generated by scripts/render.py. Edit the script, not this file. -->",
        link(SITE, picture("hero.svg", f"{USER}, {TITLE}, Greece")),
        link(SITE, picture("profile-badges.svg", badges_alt)),
        picture("intro.svg", "About NexzaDev: self-taught network engineer in Greece working across networking, development and security. Currently hardening Nmap-NSE-Script-Collection."),
        connect, div,
        hd["experience"],
        link("https://github.com/Sonix-Devs", picture("experience.svg", "Career: Co-Founder and Lead Developer at Sonix-Devs, author of Nmap-NSE-Script-Collection. Focus areas: cybersecurity, network security, Discord automation, web development.")),
        div, hd["projects"],
        f'<p align="center">\n{projects}\n</p>',
        f'<p align="center">\n{link(f"https://github.com/{USER}?tab=repositories", cta_img)}\n</p>',
        div, hd["stack"],
        picture("stack.svg", "Tech stack: " + ", ".join(n for r in ICON_ROWS for n in r) + ", " + ", ".join(CHIPS)),
        div, hd["background"],
        picture("background.svg", "Learning platforms: " + ", ".join(n for n, _ in BACK)),
        div, hd["stats"],
        link(f"https://github.com/{USER}", picture("github.svg", f"GitHub stats for @{USER}: contributions, commits, pull requests, stars, streak and languages")),
        link(f"https://leetcode.com/u/{LEETCODE_USER}/", picture("leetcode.svg", f"LeetCode stats for {LEETCODE_USER}")),
        snake, div,
        link(SITE, picture("footer.svg", "Thanks for visiting. More at nexza.dev. Open to collaboration on security tooling, NSE scripts and web and Discord automation.")),
        connect,
    ]
    return "\n\n".join(blocks) + "\n"


def main() -> None:
    global OFFLINE
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offline", action="store_true")
    OFFLINE = ap.parse_args().offline
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.svg"):
        if old.name not in ("github.svg", "leetcode.svg"):
            old.unlink()
    data = load_data()
    write("data.json", json.dumps(data, indent=2))
    gh = data.get("github")
    try:
        gh_svg = github_stats_card.render_card(gh, USER, f"GITHUB | @{USER.upper()}", BLUE_LIGHT) if gh else None
    except Exception as exc:  # noqa: BLE001
        print(f"github card failed: {exc}")
        gh_svg = None
    if gh_svg:
        write("github.svg", gh_svg)
    elif not (OUT / "github.svg").exists():
        write("github.svg", placeholder(f"GITHUB | @{USER.upper()}", "Stats appear after the first scheduled run of the render workflow."))
    lc = data.get("leetcode")
    try:
        lc_svg = leetcode_card.render_card(lc, LEETCODE_USER) if lc else None
    except Exception as exc:  # noqa: BLE001
        print(f"leetcode card failed: {exc}")
        lc_svg = None
    if lc_svg:
        write("leetcode.svg", lc_svg)
    elif not (OUT / "leetcode.svg").exists():
        write("leetcode.svg", placeholder(f"LEETCODE | {LEETCODE_USER.upper()}", "No public LeetCode data found yet for this username."))
    badges_alt = ""
    for mobile in (False, True):
        sfx = "-mobile" if mobile else ""
        write(f"hero{sfx}.svg", render_hero(mobile))
        svg, badges_alt = render_badges(data, mobile)
        write(f"profile-badges{sfx}.svg", svg)
        write(f"intro{sfx}.svg", render_intro(mobile))
        write(f"experience{sfx}.svg", render_experience(mobile))
        write(f"background{sfx}.svg", render_background(mobile))
        write(f"footer{sfx}.svg", render_footer(mobile))
        write(f"stack{sfx}.svg", render_stack(400 if mobile else 840))
        for i, p in enumerate(PROJECTS):
            write(f"project-{i}{sfx}.svg", render_project(p, i, mobile))
        for key, num, title, sub in HEADERS:
            for theme in ("dark", "light"):
                write(f"header-{key}-{theme}{sfx}.svg", render_header(num, title, sub, theme, mobile))
    write("divider.svg", render_divider())
    write("cta-repos.svg", render_cta("VIEW ALL REPOSITORIES"))
    for i, (key, label, slug, _) in enumerate(CONNECT):
        write(f"connect-{key}.svg", render_button(label, simple_icon(slug), i))
    README.write_text(build_readme(badges_alt), encoding="utf-8")
    refs = set(re.findall(r"assets/svg/([\w.-]+\.svg)", README.read_text(encoding="utf-8")))
    missing = sorted(m for m in refs if not (OUT / m).exists())
    if missing:
        raise SystemExit(f"README references missing files: {missing}")
    print("ok")


if __name__ == "__main__":
    main()
