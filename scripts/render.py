import os
import textwrap
from xml.sax.saxutils import escape

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "svg")
os.makedirs(OUT, exist_ok=True)

G = "#00FF9C"
B = "#1E90FF"
BG = "#0d1117"
PANEL = "#111820"
LINE = "rgba(255,255,255,0.09)"
TXT = "#c9d1d9"
MUTED = "#8b949e"
MONO = "'JetBrains Mono','SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"
SANS = "'Segoe UI',Inter,-apple-system,BlinkMacSystemFont,Helvetica,Arial,sans-serif"


def e(t):
    return escape(t)


def save(name, w, h, body, label, defs=""):
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{e(label)}">'
        f"<defs>{defs}</defs>{body}</svg>"
    )
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg)


def text(x, y, s, size=14, fill=TXT, weight=400, family=SANS, extra=""):
    return f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" fill="{fill}" {extra}>{e(s)}</text>'


def lines(x, y, s, n, size=14, fill=TXT, lh=None, family=SANS, weight=400):
    lh = lh or int(size * 1.55)
    out = []
    ls = textwrap.wrap(s, n)
    for i, l in enumerate(ls):
        out.append(text(x, y + i * lh, l, size, fill, weight, family))
    return "".join(out), len(ls) * lh


def card_bg(w, h, rx=16):
    return (
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="{rx}" fill="url(#bg)" stroke="{LINE}"/>'
    )


BGDEF = (
    f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0f1b22"/><stop offset="0.7" stop-color="{BG}"/></linearGradient>'
    f'<pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="rgba(255,255,255,0.035)" stroke-width="1"/></pattern>'
    f'<linearGradient id="scan" x1="0" x2="1"><stop offset="0" stop-color="{G}" stop-opacity="0"/><stop offset="0.5" stop-color="{G}" stop-opacity="0.10"/><stop offset="1" stop-color="{G}" stop-opacity="0"/></linearGradient>'
    f'<linearGradient id="acc" x1="0" x2="1"><stop offset="0" stop-color="{G}"/><stop offset="1" stop-color="{B}"/></linearGradient>'
)


def clip(w, h, rx=16):
    return f'<clipPath id="c"><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="{rx}"/></clipPath>'


def hero(w, mobile):
    h = 230 if mobile else 250
    big = 52 if mobile else 78
    sub = 15 if mobile else 21
    tag = 12 if mobile else 14
    px = 28 if mobile else 48
    body = card_bg(w, h)
    body += f'<g clip-path="url(#c)"><rect width="{w}" height="{h}" fill="url(#grid)"/>'
    body += (
        f'<rect x="-200" y="0" width="200" height="{h}" fill="url(#scan)">'
        f'<animateTransform attributeName="transform" type="translate" from="0 0" to="{w+200} 0" dur="6s" repeatCount="indefinite"/></rect>'
    )
    body += "</g>"
    body += text(px, 56 if mobile else 64, "// NETWORK  ·  WEB  ·  SECURITY", 11 if mobile else 12, G, 700, MONO, 'letter-spacing="2"')
    body += text(px, 56 + big + (6 if mobile else 8), "NEXZA", big, "#ffffff", 800, SANS, 'letter-spacing="-2"')
    lw = 31 * ((11 if mobile else 12) * 0.55 + 1.7)
    body += f'<rect x="{px + lw + 6}" y="{(56 if mobile else 64) - (11 if mobile else 12)}" width="8" height="{14 if mobile else 15}" fill="{G}"><animate attributeName="opacity" values="1;0;1" dur="1.2s" repeatCount="indefinite"/></rect>'
    sy = 56 + big + (36 if mobile else 44)
    body += text(px, sy, "Network Engineer · Developer · Cyber Security", sub, B, 700)
    body += text(px, sy + (24 if mobile else 30), "Self-taught. Open-source tooling for networks, the web and security testing.", tag, MUTED, 500, MONO if False else SANS)
    body += f'<rect x="{px}" y="{h-8}" width="{w-2*px}" height="2" fill="url(#acc)" opacity="0.55"/>'
    return h, body, "Nexza. Network Engineer, Developer, Cyber Security."


def badges(w, mobile):
    items = [("LOCATION", "GREECE"), ("FOCUS", "SECURITY"), ("STATUS", "BUILDING"), ("PORTFOLIO", "NEXZA.DEV")]
    gap = 12
    px = 0
    if mobile:
        tw = (w - gap) / 2
        th = 64
        h = th * 2 + gap
        pos = [(0, 0), (tw + gap, 0), (0, th + gap), (tw + gap, th + gap)]
    else:
        tw = (w - gap * 3) / 4
        th = 76
        h = th
        pos = [(i * (tw + gap), 0) for i in range(4)]
    body = ""
    for (lab, val), (x, y) in zip(items, pos):
        body += f'<rect x="{x+0.5}" y="{y+0.5}" width="{tw-1}" height="{th-1}" rx="12" fill="{PANEL}" stroke="{LINE}"/>'
        body += f'<rect x="{x+14}" y="{y+14}" width="22" height="3" rx="1.5" fill="url(#acc)"/>'
        body += text(x + 14, y + 36, lab, 10, MUTED, 700, MONO, 'letter-spacing="2"')
        body += text(x + 14, y + th - 14, val, 17 if mobile else 20, G, 800)
    return h, body, "Location Greece; Focus Security; Status Actively building; Portfolio nexza.dev"


def intro(w, mobile):
    px = 24 if mobile else 32
    n = 40 if mobile else 92
    size = 13 if mobile else 15
    paras = [
        "Self-taught engineer based in Greece, working at the intersection of networking, software development and security. I build open source tools with a focus on defensive auditing and practical automation.",
        "My core work is Nmap NSE scripts in Lua for network service auditing, complemented by web development with Next.js and React, Discord platform automation. Everything I publish is safe on production infrastructure and clearly documented.",
        "I learn by reading the documentation, building a minimal implementation and stress testing it myself.",
    ]
    y = 40
    body = ""
    for p in paras:
        b, hh = lines(px, y, p, n, size, TXT)
        body += b
        y += hh + 14
    y += 6
    body += f'<rect x="{px}" y="{y-8}" width="{w-2*px}" height="46" rx="10" fill="rgba(0,255,156,0.06)" stroke="rgba(0,255,156,0.25)"/>'
    body += text(px + 14, y + 20, "CURRENTLY", 10, G, 700, MONO, 'letter-spacing="2"')
    body += text(px + 14 + (82 if True else 0), y + 20, "Hardening Nmap-NSE-Script-Collection", 12 if mobile else 14, "#ffffff", 700, MONO)
    h = y + 56
    full = card_bg(w, h) + f'<g clip-path="url(#c)"><rect width="{w}" height="{h}" fill="url(#grid)"/></g>' + body
    return h, full, "About Nexza: self-taught engineer in Greece working across networking, development and security. Currently hardening Nmap-NSE-Script-Collection."


def project(w, mobile):
    px = 24 if mobile else 32
    n = 40 if mobile else 88
    size = 13 if mobile else 14
    body = ""
    body += text(px, 38, "FEATURED REPOSITORY", 10, G, 700, MONO, 'letter-spacing="2"')
    body += text(px, 72, "Nmap-NSE-Script-Collection", 20 if mobile else 28, "#ffffff", 800)
    desc = "Custom Nmap NSE scripts in Lua for defensive security auditing. Each script targets a specific real world misconfiguration across services such as HTTP, DNS, SMB, SSL/TLS, FTP and databases, and reports findings in a clear, actionable format. Built to run standalone or as part of larger infrastructure scans."
    b, hh = lines(px, 104, desc, n, size, TXT)
    body += b
    y = 104 + hh + 8
    x = px
    for t in ["Lua", "NSE", "HTTP", "DNS", "SMB", "SSL/TLS", "FTP", "Databases"]:
        cw = len(t) * 7.4 + 22
        if x + cw > w - px:
            x = px
            y += 36
        body += f'<rect x="{x}" y="{y}" width="{cw}" height="26" rx="13" fill="rgba(30,144,255,0.10)" stroke="rgba(30,144,255,0.45)"/>'
        body += text(x + cw / 2, y + 17, t, 11, B, 700, MONO, 'text-anchor="middle"')
        x += cw + 8
    y += 50
    body += text(px, y, "View repository  →", 14, G, 700, MONO)
    h = y + 26
    full = card_bg(w, h) + f'<g clip-path="url(#c)"><rect width="{w}" height="{h}" fill="url(#grid)"/><rect x="0" y="0" width="5" height="{h}" fill="url(#acc)"/></g>' + body
    return h, full, "Nmap-NSE-Script-Collection: custom Nmap NSE scripts in Lua for defensive security auditing across HTTP, DNS, SMB, SSL/TLS, FTP and databases."


def experience(w, mobile):
    px = 24 if mobile else 32
    n = 40 if mobile else 88
    size = 13 if mobile else 14
    body = text(px, 38, "CURRENT ROLE", 10, G, 700, MONO, 'letter-spacing="2"')
    body += text(px, 72, "Co-Founder, Lead Developer", 20 if mobile else 28, "#ffffff", 800)
    body += text(px, 98, "Sonix-Devs  \u00b7  Ongoing", 13 if mobile else 14, B, 700, MONO)
    desc = "A cybersecurity focused programming platform building projects in ethical hacking, penetration testing, digital forensics and security research."
    b, hh = lines(px, 130, desc, n, size, TXT)
    body += b
    y = 130 + hh + 8
    x = px
    for t in ["Cyber Security", "Ethical Hacking", "Security Research"]:
        cw = len(t) * 7.4 + 22
        if x + cw > w - px:
            x = px
            y += 36
        body += f'<rect x="{x}" y="{y}" width="{cw}" height="26" rx="13" fill="rgba(30,144,255,0.10)" stroke="rgba(30,144,255,0.45)"/>'
        body += text(x + cw / 2, y + 17, t, 11, B, 700, MONO, 'text-anchor="middle"')
        x += cw + 8
    y += 50
    body += text(px, y, "github.com/Sonix-Devs  \u2192", 14, G, 700, MONO)
    h = y + 26
    full = card_bg(w, h) + f'<g clip-path="url(#c)"><rect width="{w}" height="{h}" fill="url(#grid)"/><rect x="0" y="0" width="5" height="{h}" fill="url(#acc)"/></g>' + body
    return h, full, "Experience: Co-Founder and Lead Developer at Sonix-Devs, a cybersecurity focused programming platform for ethical hacking, penetration testing, digital forensics and security research."


FOCUS = [
    ("Cybersecurity", "Defensive, non destructive auditing informed by an attacker perspective. Identify weaknesses, document them precisely and leave systems safer than found."),
    ("Network Security", "Nmap and NSE coverage for common services, surfacing open resolvers, weak ciphers and unauthenticated access. Written for reliable use on live environments."),
    ("Discord Automation", "Production grade bots for moderation, role hierarchies, XP and leveling systems and community workflows. Built for stability under real load."),
    ("Web Development", "End to end products with Next.js, React and Node.js, focused on performance, type safety and clean architecture. Statically exported on Cloudflare."),
]


def focus(w, mobile):
    gap = 12
    if mobile:
        cols = 1
    else:
        cols = 2
    tw = (w - gap * (cols - 1)) / cols
    n = int((tw - 36) / 6.9)
    tiles = []
    for t, d in FOCUS:
        ls = textwrap.wrap(d, n)
        tiles.append((t, ls))
    rows = [tiles[i:i + cols] for i in range(0, len(tiles), cols)]
    body = ""
    y = 0
    for r in rows:
        th = 58 + max(len(ls) for _, ls in r) * 18 + 12
        for i, (t, ls) in enumerate(r):
            x = i * (tw + gap)
            body += f'<rect x="{x+0.5}" y="{y+0.5}" width="{tw-1}" height="{th-1}" rx="12" fill="{PANEL}" stroke="{LINE}"/>'
            body += f'<rect x="{x+18}" y="{y+18}" width="22" height="3" rx="1.5" fill="url(#acc)"/>'
            body += text(x + 18, y + 44, t, 16, "#ffffff", 800)
            for j, l in enumerate(ls):
                body += text(x + 18, y + 70 + j * 18, l, 12, TXT)
        y += th + gap
    h = y - gap
    return h, body, "Focus areas: cybersecurity, network security, Discord automation and web development."


STACK = [
    ("NETWORKING & SECURITY", ["Linux", "Bash", "Python", "Lua", "NSE", "Nmap", "WebSockets"]),
    ("LANGUAGES", ["JavaScript", "TypeScript", "HTML", "CSS", "SQL"]),
    ("WEB & DATA", ["React", "Next.js", "Node.js", "MongoDB"]),
    ("TOOLS", ["Git/GitHub", "VS Code", "Figma", "Canva", "CapCut"]),
]


def stack(w, mobile):
    px = 24 if mobile else 32
    y = 36
    body = ""
    for lab, items in STACK:
        body += text(px, y, lab, 10, G, 700, MONO, 'letter-spacing="2"')
        y += 14
        x = px
        for t in items:
            cw = len(t) * 8.2 + 26
            if x + cw > w - px:
                x = px
                y += 38
            body += f'<rect x="{x}" y="{y}" width="{cw}" height="30" rx="8" fill="{PANEL}" stroke="{LINE}"/>'
            body += f'<circle cx="{x+12}" cy="{y+15}" r="3" fill="{G}"/>'
            body += text(x + 22, y + 20, t, 12, TXT, 700, MONO)
            x += cw + 8
        y += 54
    h = y - 8
    full = card_bg(w, h) + f'<g clip-path="url(#c)"><rect width="{w}" height="{h}" fill="url(#grid)"/></g>' + body
    return h, full, "Tech stack: Linux, Bash, Python, Lua, NSE, Nmap, WebSockets, JavaScript, TypeScript, HTML, CSS, SQL, React, Next.js, Node.js, MongoDB, Git/GitHub, VS Code, Figma, Canva, CapCut."


BACK = [
    ("HackTheBox", "Labs and machines for practical security"),
    ("freeCodeCamp", "Core web development curriculum"),
    ("roadmap.sh", "Structured paths for dev and security"),
    ("DataCode", "CS community with tutorials and practice sets"),
    ("W3Schools", "Quick reference for web technologies"),
    ("LeetCode", "Algorithms and data structures"),
    ("DevDocs", "Searchable API documentation"),
    ("Discord Developer Docs", "Official docs for apps and bots"),
    ("discord-api-docs", "Open source repo behind the API docs"),
]


def background(w, mobile):
    gap = 10
    cols = 1 if mobile else 2
    tw = (w - gap * (cols - 1)) / cols
    th = 58
    body = ""
    for i, (n, d) in enumerate(BACK):
        r, c = divmod(i, cols)
        x = c * (tw + gap)
        y = r * (th + gap)
        body += f'<rect x="{x+0.5}" y="{y+0.5}" width="{tw-1}" height="{th-1}" rx="10" fill="{PANEL}" stroke="{LINE}"/>'
        body += f'<rect x="{x+14}" y="{y+16}" width="3" height="{th-32}" rx="1.5" fill="url(#acc)"/>'
        body += text(x + 28, y + 24, n, 13, G, 700, MONO)
        body += text(x + 28, y + 44, d, 12, TXT)
    rows = (len(BACK) + cols - 1) // cols
    h = rows * th + (rows - 1) * gap
    return h, body, "Learning platforms: HackTheBox, freeCodeCamp, roadmap.sh, DataCode, W3Schools, LeetCode, DevDocs, Discord Developer Docs and discord-api-docs."


def footer(w, mobile):
    h = 120 if mobile else 96
    px = 24 if mobile else 32
    body = card_bg(w, h) + f'<g clip-path="url(#c)"><rect width="{w}" height="{h}" fill="url(#grid)"/></g>'
    body += text(px, 38, "Thanks for visiting.", 18 if mobile else 20, "#ffffff", 800)
    b, _ = lines(px, 64, "Open to collaboration on security tooling, NSE scripts and web and Discord automation.", 44 if mobile else 100, 12 if mobile else 13, MUTED)
    body += b
    body += f'<rect x="{px}" y="{h-10}" width="{w-2*px}" height="2" fill="url(#acc)" opacity="0.55"/>'
    return h, body, "Thanks for visiting. Open to collaboration on security tooling, NSE scripts and web and Discord automation."


def build(name, fn):
    for mobile in (False, True):
        w = 400 if mobile else 840
        h, body, label = fn(w, mobile)
        d = BGDEF + clip(w, h)
        save(f"{name}{'-mobile' if mobile else ''}.svg", w, h, body, label, d)


def section_header(title, mode, mobile):
    w = 400 if mobile else 840
    h = 46 if mobile else 56
    fg = "#e6edf3" if mode == "dark" else "#0d1117"
    ac = G if mode == "dark" else "#00a869"
    ln = "rgba(255,255,255,0.12)" if mode == "dark" else "rgba(13,17,23,0.15)"
    size = 18 if mobile else 22
    body = text(0, h / 2 + size / 3, ">", size, ac, 800, MONO)
    body += text(size + 8, h / 2 + size / 3, title.upper(), size, fg, 800, SANS, 'letter-spacing="3"')
    tw = len(title) * (size * 0.78) + size + 24
    body += f'<rect x="{tw}" y="{h/2}" width="{w-tw}" height="1" fill="{ln}"/>'
    body += f'<rect x="0" y="{h-4}" width="56" height="3" rx="1.5" fill="{ac}"/>'
    save(f"header-{title.lower().replace(' ', '-')}-{mode}{'-mobile' if mobile else ''}.svg", w, h, body, title)


def button(name, label, color, fg="#0d1117"):
    w, h = 128, 36
    body = f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="8" fill="{BG}" stroke="{color}" stroke-opacity="0.6"/>'
    body += f'<rect x="0.5" y="0.5" width="4" height="{h-1}" rx="2" fill="{color}"/>'
    body += text(w / 2 + 2, 23, label, 12, color, 700, MONO, 'text-anchor="middle" letter-spacing="1"')
    save(f"connect-{name}.svg", w, h, body, label)


def divider():
    body = f'<rect x="0" y="5" width="840" height="2" fill="url(#acc)" opacity="0.35"/>'
    body += f'<rect x="0" y="5" width="840" height="2" fill="url(#sh)"><animate attributeName="opacity" values="0.1;0.6;0.1" dur="4s" repeatCount="indefinite"/></rect>'
    d = f'<linearGradient id="acc" x1="0" x2="1"><stop offset="0" stop-color="{G}" stop-opacity="0"/><stop offset="0.5" stop-color="{G}"/><stop offset="1" stop-color="{B}" stop-opacity="0"/></linearGradient><linearGradient id="sh" x1="0" x2="1"><stop offset="0" stop-color="{B}" stop-opacity="0"/><stop offset="0.5" stop-color="#ffffff"/><stop offset="1" stop-color="{G}" stop-opacity="0"/></linearGradient>'
    save("divider.svg", 840, 12, body, "", d)


for name, fn in [
    ("hero", hero),
    ("badges", badges),
    ("intro", intro),
    ("experience", experience),
    ("project-nmap", project),
    ("focus", focus),
    ("stack", stack),
    ("background", background),
    ("footer", footer),
]:
    build(name, fn)

for t in ["About", "Experience", "Projects", "Focus Areas", "Technologies", "Background", "Coding Stats", "Connect"]:
    for mode in ("dark", "light"):
        for mobile in (False, True):
            section_header(t, mode, mobile)

button("email", "EMAIL", G)
button("discord", "DISCORD", "#5865F2")
button("github", "GITHUB", "#e6edf3")
button("x", "X", "#e6edf3")
button("instagram", "INSTAGRAM", "#E4405F")
button("tiktok", "TIKTOK", "#25F4EE")
divider()
