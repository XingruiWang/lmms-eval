"""patch_pp2.py — make the XModBench project page dynamic & precise:
 #design  : static cfg6 grid -> interactive 3-ball / 6-arrow triangle
            + template + live routing example
 #tasks   : donut -> interactive; hovering a family draws a subtask
            tree (counts + % that reconcile exactly to the donut)
 famgrid subtask labels aligned to the accurate canonical grouping.
"""
import math
import pathlib

IDX = pathlib.Path("/scratch/xwang378/2025/xingruiwang.github.io/projects/XModBench/index.html")
s = IDX.read_text()

# ---------------- Widget 1: interactive triangle ----------------
NODES = {"A": (320, 78, "Audio", "\U0001F50A", "#5b8def"),
         "V": (120, 332, "Vision", "\U0001F5BC", "#8b5cf6"),
         "T": (520, 332, "Text", "\U0001F524", "#2bc4a8")}
TASKS = [("V", "T"), ("V", "A"), ("T", "A"), ("T", "V"), ("A", "V"), ("A", "T")]
R = 46

def _pt(cx, cy, tx, ty, r):
    d = math.hypot(tx - cx, ty - cy)
    return cx + (tx - cx) / d * r, cy + (ty - cy) / d * r

arrows = []
for i, (a, b) in enumerate(TASKS):
    sx, sy = NODES[a][0], NODES[a][1]
    ex, ey = NODES[b][0], NODES[b][1]
    mx, my = (sx + ex) / 2, (sy + ey) / 2
    dx, dy = ex - sx, ey - sy
    L = math.hypot(dx, dy)
    px, py = -dy / L, dx / L
    cxp, cyp = mx + px * 62, my + py * 62
    p0 = _pt(sx, sy, cxp, cyp, R + 5)
    p1 = _pt(ex, ey, cxp, cyp, R + 12)
    c = NODES[a][4]
    code = a + "→" + b
    arrows.append(
        f'<path class="t-arr" data-r="{a}{b}" d="M{p0[0]:.1f},{p0[1]:.1f} '
        f'Q{cxp:.1f},{cyp:.1f} {p1[0]:.1f},{p1[1]:.1f}" fill="none" stroke="{c}" '
        f'stroke-width="3.4" marker-end="url(#tah{i})" stroke-linecap="round"/>'
        f'<marker id="tah{i}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" '
        f'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>')
balls = []
for nid, (cx, cy, lab, gly, c) in NODES.items():
    balls.append(
        f'<g class="t-ball" data-n="{nid}"><circle cx="{cx}" cy="{cy}" r="{R}" fill="{c}" '
        f'fill-opacity="0.12" stroke="{c}" stroke-width="2.5"/>'
        f'<text x="{cx}" y="{cy-2}" text-anchor="middle" font-size="26">{gly}</text>'
        f'<text x="{cx}" y="{cy+24}" text-anchor="middle" fill="#2d3748" font-size="15" '
        f'font-weight="700" font-family="Inter,sans-serif">{lab}</text></g>')
TRI = ('<div class="tri-wrap"><div class="tri-svg"><svg viewBox="0 0 640 420">'
       + "".join(arrows) + "".join(balls) + '</svg></div>'
       '<div class="tri-side">'
       '<div class="tri-tpl">Each item is a four-choice question — a '
       '<code>&lt;context&gt;</code> (the stem) and four <code>&lt;candidates&gt;</code> '
       '(options). Permuting the modality of each yields <b>six configurations</b>.</div>'
       '<div class="tri-ex" id="triEx">'
       '<div class="tri-code" id="triCode">V&rarr;T</div>'
       '<div class="tri-rowx"><span class="tri-pill" id="triCtx">&#128062; image context</span>'
       '<span class="tri-arx">&rarr;</span>'
       '<span class="tri-pill" id="triCand">4 &times; text candidates</span></div>'
       '<div class="tri-hint">hover a ball or an arrow</div></div></div></div>')

OLD_CFG6_LINE_START = '        <div class="cfg6">'
i0 = s.index(OLD_CFG6_LINE_START)
i1 = s.index("\n", i0)
s = s[:i0] + "        " + TRI + s[i1:]

# ---------------- Widget 2: interactive donut + subtask tree ----------------
FAMS = [("Perception", "#5b8def", 24000), ("Spatial", "#f6a609", 7776),
        ("Temporal", "#ef5a6e", 9000), ("Linguistic", "#2bc4a8", 8244),
        ("Knowledge", "#8b5cf6", 12300)]
SUB = {
    "Perception": [("General activities", 6000), ("Fine-grained recognition", 6000),
                   ("Musical instruments", 6000), ("Instrument comparison", 3000),
                   ("Natural environments", 3000)],
    "Spatial": [("2D Arrangement", 2790), ("3D Localization", 2340), ("3D Movement", 2646)],
    "Temporal": [("Temporal Order", 3000), ("Temporal Counting", 3000),
                 ("Temporal Calculation", 3000)],
    "Linguistic": [("Recognition (OCR / ASR)", 4032), ("Translation (EN–ZH)", 4212)],
    "Knowledge": [("Music Genre", 6000), ("Emotion Classification", 4200),
                  ("Movie Matching", 1200), ("Singer ID", 900)],
}
TOTAL = 61320

def pol(cx, cy, r, deg):
    a = math.radians(deg - 90)
    return cx + r * math.cos(a), cy + r * math.sin(a)
segs, legend, a0 = [], [], 0.0
for name, c, n in FAMS:
    sw = n / TOTAL * 360
    a1 = a0 + sw
    x0, y0 = pol(230, 230, 175, a0); x1, y1 = pol(230, 230, 175, a1)
    xi1, yi1 = pol(230, 230, 100, a1); xi0, yi0 = pol(230, 230, 100, a0)
    lg = 1 if sw > 180 else 0
    segs.append(f'<path class="pseg" data-fam="{name}" d="M{x0:.1f},{y0:.1f} '
                f'A175,175 0 {lg} 1 {x1:.1f},{y1:.1f} L{xi1:.1f},{yi1:.1f} '
                f'A100,100 0 {lg} 0 {xi0:.1f},{yi0:.1f} Z" fill="{c}"><title>{name}: {n:,}</title></path>')
    legend.append(f'<div class="dlg" data-fam="{name}"><span style="background:{c}"></span>'
                  f'<b>{name}</b><i>{n:,} &middot; {n/TOTAL*100:.0f}%</i></div>')
    a0 = a1
DONUT = (f'<div class="statwrap"><div class="donut-col">'
         f'<svg viewBox="0 0 460 460" class="pdonut">{"".join(segs)}'
         f'<text x="230" y="216" text-anchor="middle" class="pdc1">61,320</text>'
         f'<text x="230" y="248" text-anchor="middle" class="pdc2">items &middot; 17 subtasks</text></svg>'
         f'<div class="dlgs">{"".join(legend)}</div></div>'
         f'<div class="subtree" id="subtree"><div class="st-hint">Hover a family to see its subtasks</div></div></div>')

OLD_STAT = '        <div class="statwrap">'
j0 = s.index(OLD_STAT)
j1 = s.index("\n", j0)
s = s[:j0] + "        " + DONUT + s[j1:]

# ---------------- align famgrid subtask labels (accuracy) ----------------
FAM_LBL = {
    "Perception": ["General activities", "Fine-grained recognition", "Musical instruments",
                   "Instrument comparison", "Natural environments"],
    "Spatial": ["2D Arrangement", "3D Localization", "3D Movement"],
    "Temporal": ["Temporal Order", "Temporal Counting", "Temporal Calculation"],
    "Linguistic": ["Recognition (OCR/ASR)", "Translation (EN-ZH)"],
    "Knowledge": ["Music Genre", "Emotion Classification", "Movie Matching", "Singer ID"],
}
for fam, lbls in FAM_LBL.items():
    a = s.index(f'<h4>{fam}</h4>')
    ul0 = s.index("<ul>", a); ul1 = s.index("</ul>", ul0)
    s = s[:ul0] + "<ul>" + "".join(f"<li>{x}</li>" for x in lbls) + s[ul1:]

# ---------------- CSS ----------------
import json
SUBJSON = json.dumps({k: v for k, v in SUB.items()})
FCOL = json.dumps({n: c for n, c, _ in FAMS})
CSS = '''
    /* interactive triangle */
    .tri-wrap{display:grid;grid-template-columns:1.3fr 1fr;gap:30px;align-items:center;margin:22px 0 28px}
    @media(max-width:820px){.tri-wrap{grid-template-columns:1fr}}
    .tri-svg svg{width:100%;height:auto}
    .t-arr{opacity:.28;transition:opacity .2s,stroke-width .2s;cursor:pointer}
    .t-arr.lit{opacity:1;stroke-width:5}
    .t-ball{cursor:pointer}.t-ball circle{transition:fill-opacity .2s,r .2s}
    .t-ball.lit circle{fill-opacity:.3}
    .tri-side{display:flex;flex-direction:column;gap:16px}
    .tri-tpl{font-size:15px;color:#4a5568;line-height:1.6;border-left:3px solid #667eea;padding:10px 16px;background:#f7fafc;border-radius:0 10px 10px 0}
    .tri-tpl code{font-family:'JetBrains Mono',monospace;color:#2b6cb0}
    .tri-ex{border:1px solid #e2e8f0;border-radius:12px;padding:18px;text-align:center;background:#fff}
    .tri-code{font:800 26px 'JetBrains Mono',monospace;color:#2d3748;margin-bottom:12px}
    .tri-rowx{display:flex;align-items:center;justify-content:center;gap:12px;flex-wrap:wrap}
    .tri-pill{padding:7px 14px;border-radius:999px;background:#edf2f7;font-size:14px;font-weight:600;color:#2d3748}
    .tri-arx{color:#a0aec0;font-size:18px}
    .tri-hint{margin-top:12px;font-size:12px;color:#a0aec0;font-family:'JetBrains Mono',monospace}
    /* interactive donut + subtask tree */
    .statwrap{display:flex;align-items:center;justify-content:center;gap:46px;flex-wrap:wrap;margin:26px 0}
    .donut-col{display:flex;align-items:center;gap:34px;flex-wrap:wrap}
    .pdonut{width:300px;height:300px}
    .pseg{cursor:pointer;transition:opacity .18s,transform .18s;transform-origin:230px 230px}
    .pseg.dim{opacity:.22}.pseg.sel{transform:scale(1.05)}
    .pdc1{fill:#1a202c;font:800 34px 'Inter',sans-serif}.pdc2{fill:#718096;font:600 13px 'JetBrains Mono'}
    .dlgs{display:flex;flex-direction:column;gap:11px;text-align:left}
    .dlg{display:flex;align-items:center;gap:10px;font-size:15px;color:#2d3748;cursor:pointer;padding:4px 8px;border-radius:8px;transition:background .15s}
    .dlg:hover,.dlg.sel{background:#edf2f7}
    .dlg span{width:14px;height:14px;border-radius:4px}.dlg b{min-width:92px}.dlg i{color:#718096;font-style:normal;font-family:'JetBrains Mono';font-size:13px}
    .subtree{min-width:300px;max-width:360px;border:1px solid #e2e8f0;border-radius:14px;background:#fff;padding:18px 20px;min-height:240px}
    .st-hint{color:#a0aec0;font-size:14px;text-align:center;padding-top:90px;font-family:'JetBrains Mono',monospace}
    .st-h{display:flex;align-items:baseline;gap:10px;margin-bottom:14px;border-bottom:1px solid #edf2f7;padding-bottom:10px}
    .st-h b{font-size:19px;color:var(--c)}.st-h i{font-style:normal;font-family:'JetBrains Mono';font-size:13px;color:#718096}
    .st-row{display:flex;align-items:center;gap:10px;margin:9px 0;font-size:14px}
    .st-row .nm{flex:1;color:#2d3748}
    .st-bar{height:8px;border-radius:4px;background:var(--c);min-width:6px}
    .st-row .ct{font-family:'JetBrains Mono',monospace;font-size:12px;color:#718096;width:78px;text-align:right}
'''
JS = '''
<script>(function(){
  // triangle interaction
  const EX={A:["&#128266; audio","Audio"],V:["&#128062; image","Vision"],T:["&#128292; text","Text"]};
  function setEx(code){const a=code[0],b=code[1];
    document.getElementById("triCode").innerHTML=a+"&rarr;"+b;
    document.getElementById("triCtx").innerHTML=EX[a][0]+" context";
    document.getElementById("triCand").innerHTML="4 &times; "+EX[b][1].toLowerCase()+" candidates";}
  const arrs=[...document.querySelectorAll(".t-arr")];
  arrs.forEach(p=>{p.addEventListener("mouseenter",()=>{
      arrs.forEach(q=>q.classList.toggle("lit",q===p));setEx(p.dataset.r);});
    p.addEventListener("mouseleave",()=>arrs.forEach(q=>q.classList.remove("lit")));});
  document.querySelectorAll(".t-ball").forEach(g=>{
    g.addEventListener("mouseenter",()=>{const n=g.dataset.n;
      arrs.forEach(q=>q.classList.toggle("lit",q.dataset.r.indexOf(n)>=0));});
    g.addEventListener("mouseleave",()=>arrs.forEach(q=>q.classList.remove("lit")));});
  // donut + subtask tree
  const SUB=__SUBJSON__, FC=__FCOL__, TOT=61320;
  const box=document.getElementById("subtree");
  function tree(fam){
    const subs=SUB[fam],c=FC[fam],ft=subs.reduce((a,b)=>a+b[1],0),mx=Math.max(...subs.map(x=>x[1]));
    let h='<div class="st-h" style="--c:'+c+'"><b>'+fam+'</b><i>'+ft.toLocaleString()
      +' &middot; '+(ft/TOT*100).toFixed(0)+'% of XModBench &middot; '+subs.length+' subtasks</i></div>';
    subs.forEach(([nm,n])=>{h+='<div class="st-row" style="--c:'+c+'"><span class="nm">'+nm
      +'</span><span class="st-bar" style="width:'+(n/mx*120+6)+'px"></span>'
      +'<span class="ct">'+n.toLocaleString()+' &middot; '+(n/TOT*100).toFixed(1)+'%</span></div>';});
    box.innerHTML=h;}
  function sel(fam){
    document.querySelectorAll(".pseg").forEach(p=>{p.classList.toggle("sel",p.dataset.fam===fam);
      p.classList.toggle("dim",p.dataset.fam!==fam);});
    document.querySelectorAll(".dlg").forEach(d=>d.classList.toggle("sel",d.dataset.fam===fam));
    tree(fam);}
  function clr(){document.querySelectorAll(".pseg").forEach(p=>p.classList.remove("sel","dim"));
    document.querySelectorAll(".dlg").forEach(d=>d.classList.remove("sel"));}
  document.querySelectorAll("[data-fam]").forEach(el=>{
    el.style.cursor="pointer";
    el.addEventListener("mouseenter",()=>sel(el.dataset.fam));});
  const sw=document.querySelector(".statwrap");
  if(sw) sw.addEventListener("mouseleave",clr);
  tree("Perception");          // default view
})();</script>'''
JS = JS.replace("__SUBJSON__", SUBJSON).replace("__FCOL__", FCOL)
s = s.replace("</style>", CSS + "\n</style>", 1)
s = s.replace("</body>", JS + "\n</body>", 1)
IDX.write_text(s)
print("patched:", IDX)
print("t-arr:", s.count('class="t-arr"'), "| t-ball:", s.count('class="t-ball"'),
      "| pseg:", s.count('class="pseg"'), "| cfg6 gone:", 'class="cfg6"' not in s)
