"""patch_projectpage.py — upgrade the XModBench project page:
 #design : plain 6-config <ul> → visual 6 routing cards
 #tasks  : distribution.png + emoji task-grid → stats donut + table
           + 5 image-backed family cards (with subtask lists)
Idempotent-ish: matches exact current blocks; run once.
"""
import math
import pathlib

IDX = pathlib.Path("/scratch/xwang378/2025/xingruiwang.github.io/projects/XModBench/index.html")
s = IDX.read_text()

ICON = {"V": ("\U0001F5BC", "Vision"), "A": ("\U0001F50A", "Audio"), "T": ("\U0001F524", "Text")}
COL = {"V": "#8b5cf6", "A": "#5b8def", "T": "#2bc4a8"}
ROUTES = ["VT", "VA", "TA", "TV", "AV", "AT"]

def rcard(code):
    smod, emod = code[0], code[1]
    si, sl = ICON[smod]; ei, el = ICON[emod]
    return (f'<div class="cfg6-c">'
            f'<span class="cfg6-code">{smod}&rarr;{emod}</span>'
            f'<span class="cfg6-m" style="--c:{COL[smod]}">{si}<b>{sl}</b><i>context</i></span>'
            f'<span class="cfg6-ar">&rarr;</span>'
            f'<span class="cfg6-m" style="--c:{COL[emod]}">{ei}<b>{el}</b><i>candidates</i></span>'
            f'</div>')

CFG6 = ('<div class="cfg6">' + "".join(rcard(c) for c in ROUTES) + '</div>')

# ---- replace the plain 6-config <ul> in #design ----
OLD_UL = '''        <ul>
          <li><strong>Audio → Text (A→T)</strong>: Audio context, text candidates</li>
          <li><strong>Audio → Vision (A→V)</strong>: Audio context, visual candidates</li>
          <li><strong>Text → Audio (T→A)</strong>: Text context, audio candidates</li>
          <li><strong>Text → Vision (T→V)</strong>: Text context, visual candidates</li>
          <li><strong>Vision → Audio (V→A)</strong>: Visual context, audio candidates</li>
          <li><strong>Vision → Text (V→T)</strong>: Visual context, text candidates</li>
        </ul>'''
assert OLD_UL in s, "design <ul> not found"
s = s.replace(OLD_UL, "      </div>\n\n      " + CFG6 + "\n      <div class=\"content\">", 1)

# ---- #tasks: donut + stats table + family image cards ----
FAM = [
    ("Perception", "#5b8def", "fam_perception", 24000, 5,
     "Recognition of objects, activities and scenes across modalities",
     ["General activities", "Fine-grained activities", "Natural environments",
      "Musical instruments", "Instrument compositions"]),
    ("Spatial", "#f6a609", "fam_spatial", 7776, 3,
     "Object positions and motion in 2D / 3D space",
     ["2D Arrangement", "3D Localization", "3D Movement"]),
    ("Temporal", "#ef5a6e", "fam_temporal", 9000, 3,
     "Event order and frequency across time",
     ["Temporal Order", "Temporal Counting", "Temporal Calculation"]),
    ("Linguistic", "#2bc4a8", "fam_speech", 8244, 3,
     "OCR / ASR in cross-modal settings with affective understanding",
     ["Recognition (OCR/ASR)", "Translation (EN-ZH)", "Emotion Classification"]),
    ("Knowledge", "#8b5cf6", "fam_knowledge", 12300, 3,
     "Linking multimodal content with world & cultural knowledge",
     ["Music Genre", "Movie Recognition", "Singer Identification"]),
]
TOTAL = 61320

def pol(cx, cy, r, deg):
    a = math.radians(deg - 90)
    return cx + r * math.cos(a), cy + r * math.sin(a)

segs, legend, a0 = [], [], 0.0
for name, c, _, n, _, _, _ in FAM:
    sw = n / TOTAL * 360; a1 = a0 + sw
    x0, y0 = pol(230, 230, 175, a0); x1, y1 = pol(230, 230, 175, a1)
    xi1, yi1 = pol(230, 230, 105, a1); xi0, yi0 = pol(230, 230, 105, a0)
    lg = 1 if sw > 180 else 0
    segs.append(f'<path d="M{x0:.1f},{y0:.1f} A175,175 0 {lg} 1 {x1:.1f},{y1:.1f} '
                f'L{xi1:.1f},{yi1:.1f} A105,105 0 {lg} 0 {xi0:.1f},{yi0:.1f} Z" '
                f'fill="{c}"><title>{name}: {n:,}</title></path>')
    legend.append(f'<div class="dlg"><span style="background:{c}"></span>'
                  f'<b>{name}</b><i>{n:,} &middot; {n/TOTAL*100:.0f}%</i></div>')
    a0 = a1
DONUT = (f'<div class="statwrap"><svg viewBox="0 0 460 460" class="pdonut">'
         f'{"".join(segs)}<text x="230" y="218" text-anchor="middle" class="pdc1">61,320</text>'
         f'<text x="230" y="250" text-anchor="middle" class="pdc2">items &middot; 17 subtasks</text>'
         f'</svg><div class="dlgs">{"".join(legend)}</div></div>')

cards = ""
for name, c, img, n, ns, desc, subs in FAM:
    lis = "".join(f"<li>{x}</li>" for x in subs)
    cards += (f'<div class="famc" style="--c:{c}">'
              f'<div class="famc-im" style="background-image:url(./static/images/{img}.jpg)">'
              f'<span class="famc-n">{n:,}</span></div>'
              f'<div class="famc-b"><h4>{name}</h4><p>{desc}</p><ul>{lis}</ul></div></div>')
TASKS_NEW = (f'''<div class="content" style="text-align:center;">
        <p>XModBench covers <strong>5 task families</strong> with <strong>17 subtasks</strong> —
        perception, spatial, temporal, linguistic and external-knowledge reasoning, all in the
        modality-balanced multiple-choice format.</p>
        {DONUT}
      </div>

      <div class="famgrid">{cards}</div>''')

OLD_TASKS_START = '      <div class="content" style="text-align: center;">\n        <img src="./static/images/distribution.png"'
i0 = s.index(OLD_TASKS_START)
i1 = s.index('      <div class="content" style="margin-top: 48px;">', i0)  # Data Construction Pipeline
s = s[:i0] + TASKS_NEW + "\n\n" + s[i1:]

CSS = '''
    /* project-page: 6 config cards + family grid + donut */
    .cfg6{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:18px 0 26px}
    @media(max-width:760px){.cfg6{grid-template-columns:1fr}}
    .cfg6-c{display:flex;align-items:center;gap:14px;padding:12px 16px;border:1px solid #e2e8f0;
      border-radius:12px;background:#fff;box-shadow:0 2px 10px rgba(0,0,0,.04)}
    .cfg6-code{font:800 16px 'JetBrains Mono',monospace;color:#2d3748;width:54px}
    .cfg6-m{display:flex;flex-direction:column;align-items:center;flex:1;color:var(--c);font-size:22px}
    .cfg6-m b{font-size:14px;color:#2d3748;margin-top:2px}
    .cfg6-m i{font-size:11px;color:#a0aec0;font-style:normal;font-family:'JetBrains Mono',monospace}
    .cfg6-ar{color:#cbd5e0;font-size:20px}
    .statwrap{display:flex;align-items:center;justify-content:center;gap:48px;flex-wrap:wrap;margin:26px 0}
    .pdonut{width:300px;height:300px}.pdonut path{transition:transform .2s;transform-origin:230px 230px}
    .pdonut path:hover{transform:scale(1.04)}
    .pdc1{fill:#1a202c;font:800 34px 'Inter',sans-serif}.pdc2{fill:#718096;font:600 14px 'JetBrains Mono'}
    .dlgs{display:flex;flex-direction:column;gap:12px;text-align:left}
    .dlg{display:flex;align-items:center;gap:10px;font-size:15px;color:#2d3748}
    .dlg span{width:14px;height:14px;border-radius:4px}.dlg b{min-width:96px}.dlg i{color:#718096;font-style:normal;font-family:'JetBrains Mono';font-size:13px}
    .famgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:18px;margin:26px 0 8px}
    .famc{border:1px solid #e2e8f0;border-radius:14px;overflow:hidden;background:#fff;
      box-shadow:0 4px 16px rgba(0,0,0,.05);transition:transform .25s,box-shadow .25s}
    .famc:hover{transform:translateY(-4px);box-shadow:0 14px 34px rgba(43,108,176,.16)}
    .famc-im{height:130px;background-size:cover;background-position:center;position:relative;border-bottom:3px solid var(--c)}
    .famc-n{position:absolute;right:8px;bottom:8px;background:rgba(5,7,13,.72);color:#fff;
      font:600 12px 'JetBrains Mono';padding:3px 8px;border-radius:6px}
    .famc-b{padding:14px 16px}.famc-b h4{font-size:18px;color:var(--c);margin:0 0 6px}
    .famc-b p{font-size:13px;color:#718096;margin:0 0 10px;min-height:34px}
    .famc-b ul{list-style:none;margin:0;padding:0;font-size:13px;color:#4a5568}
    .famc-b li{padding:5px 0;border-top:1px solid #edf2f7}
'''
s = s.replace("</style>", CSS + "\n</style>", 1)
IDX.write_text(s)
print("patched:", IDX)
print("cfg6 cards:", s.count('class="cfg6-c"'), "| famc:", s.count('class="famc"'),
      "| donut segs:", s.count('<path d="M'))
print("distribution.png removed from #tasks:", s.count('distribution.png'))
print("sections", s.count('<section'), s.count('</section>'))
