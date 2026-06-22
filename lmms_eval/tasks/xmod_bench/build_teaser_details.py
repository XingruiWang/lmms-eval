"""build_teaser_details.py — xmodbench_teaser_details.html

A richer, scroll-based explainer (separate from xmodbench_teaser.html):
 1. the four-choice config template (real MC example, V→T → V→A → T→A,
    then collapses into the 6 config rows + <context>/<candidates> def)
 2. the 5 task families (vision impression, one real image each)
 3. detailed statistics (task / subtask / counts, 61,320)
 4. results (the 3 analysis figures)
Self-contained: every image is inlined base64.
"""
import base64
import pathlib

H = pathlib.Path("/scratch/xwang378/2025/lmms-eval/lmms_eval/tasks/xmod_bench")
A = H / "teaser_assets"
OUT = H / "xmodbench_teaser_details.html"


def b64(p, mime="image/jpeg"):
    return f"data:{mime};base64," + base64.b64encode(pathlib.Path(p).read_bytes()).decode()


DOG = "data:image/jpeg;base64," + (A / "dog_img_b64.txt").read_text().strip()
FAM_IMG = {k: b64(A / f"fam_{k}.jpg") for k in
           ["perception", "spatial", "temporal", "speech", "knowledge"]}
FIG = {n: b64(H / f"figures/fig{n}.png", "image/png") for n in
       ["1_task_competence_radar", "2_modality_disparity", "3_directional_imbalance"]}

STATS = [
    ("Perception", "#5b8def", 24000,
     [("finegrained", 6000), ("general_activities", 6000), ("instruments", 6000),
      ("instruments_comp", 3000), ("natures", 3000)]),
    ("Spatial", "#f6a609", 7776,
     [("3D_movements", 2646), ("arrangements", 2790), ("panorama", 2340)]),
    ("Temporal", "#ef5a6e", 9000,
     [("calculation", 3000), ("count", 3000), ("order", 3000)]),
    ("Linguistic", "#2bc4a8", 8244,
     [("recognition", 4032), ("translation", 4212)]),
    ("Knowledge", "#8b5cf6", 12300,
     [("emotion_classification", 4200), ("movie_matching", 1200),
      ("music_genre_classification", 6000), ("singer_identification", 900)]),
]
TASK_DESC = {
    "perception": "What is it? — finegrained recognition, instruments, scenes",
    "spatial": "Where / which direction? — 3D motion, arrangement, panorama",
    "temporal": "When & how many? — order, counting, calculation over time",
    "speech": "Linguistic — speech recognition & translation",
    "knowledge": "External knowledge — music genre, movie, singer, emotion",
}

WAVE = ('<svg class="wv" viewBox="0 0 60 24">' +
        "".join(f'<rect x="{i*5+2}" y="{12-h}" width="3" height="{h*2}" rx="1"/>'
                for i, h in enumerate([3, 7, 11, 6, 9, 4, 8, 10, 5, 7, 3])) + "</svg>")

CHOICES = ["dog howling", "chicken clucking", "crocodile hissing", "cuckoo bird calling"]


def opt_text(letter, txt, ok=False):
    return (f'<div class="opt{" ok" if ok else ""}"><b>{letter}</b>'
            f'<span>{txt}</span></div>')


def opt_aud(letter, txt, ok=False):
    return (f'<div class="opt{" ok" if ok else ""}"><b>{letter}</b>'
            f'{WAVE}<span class="mut">{txt}</span></div>')


def mc_card(tag, ctx_html, opts_html, note):
    return f'''<div class="mc">
      <div class="mc-tag">{tag}</div>
      <div class="mc-body">
        <div class="mc-ctx">{ctx_html}</div>
        <div class="mc-opts">{opts_html}</div>
      </div>
      <div class="mc-note">{note}</div>
    </div>'''


Q = "Which sound matches what is shown?"
img_ctx = f'<div class="qstem">{Q}</div><img class="cimg" src="{DOG}">'
txt_ctx = f'<div class="qstem">{Q}</div><div class="ctext">[ a dog, mid-shot, outdoors ]</div>'

ex_vt = mc_card("V → T &nbsp;<i>(vision context, text candidates)</i>", img_ctx,
                "".join(opt_text("ABCD"[i], c, i == 0) for i, c in enumerate(CHOICES)),
                "context = image &nbsp;·&nbsp; 4 candidates = text")
ex_va = mc_card("V → A &nbsp;<i>(same image, audio candidates)</i>", img_ctx,
                "".join(opt_aud("ABCD"[i], c, i == 0) for i, c in enumerate(CHOICES)),
                "context = image &nbsp;·&nbsp; 4 candidates = audio clips")
ex_ta = mc_card("T → A &nbsp;<i>(text context, audio candidates)</i>", txt_ctx,
                "".join(opt_aud("ABCD"[i], c, i == 0) for i, c in enumerate(CHOICES)),
                "context = text &nbsp;·&nbsp; 4 candidates = audio clips")

ICON = {"V": ("🖼", "Vision", "#8b5cf6"), "A": ("🔊", "Audio", "#5b8def"),
        "T": ("🔤", "Text", "#2bc4a8")}
ROWS6 = ["VT", "VA", "TA", "TV", "AV", "AT"]


def cfg_row(code):
    s, e = code[0], code[1]
    gi, gl, gc = ICON[s]
    hi, hl, hc = ICON[e]
    return (f'<div class="crow"><span class="cc">{code[0]}→{code[1]}</span>'
            f'<span class="cn" style="--c:{gc}">{gi} {gl}</span>'
            f'<span class="ar">context&nbsp;→&nbsp;candidates</span>'
            f'<span class="cn" style="--c:{hc}">{hi} {hl}</span></div>')


fam_cards = "".join(
    f'<div class="fc reveal"><img src="{FAM_IMG[k]}"><div class="fct">'
    f'<b>{k.title() if k!="speech" else "Linguistic"}</b>'
    f'<span>{TASK_DESC[k]}</span></div></div>'
    for k in ["perception", "spatial", "temporal", "speech", "knowledge"])

stat_rows = ""
for fam, c, tot, subs in STATS:
    stat_rows += (f'<tr class="fhdr"><td><span class="dot" style="background:{c}"></span>'
                  f'{fam}</td><td></td><td class="num">{tot:,}</td></tr>')
    for st, n in subs:
        stat_rows += f'<tr><td></td><td>{st}</td><td class="num">{n:,}</td></tr>'

HTML = r'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>XModBench — how it works</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
<style>
:root{--g1:#667eea;--g2:#764ba2;--ok:#38d39f}
*{margin:0;padding:0;box-sizing:border-box}
body{background:#070a12;color:#e8edf6;font-family:'Inter',sans-serif;line-height:1.5}
.sec{max-width:1120px;margin:0 auto;padding:9vh 5vw}
.k{font:600 13px 'JetBrains Mono',monospace;letter-spacing:.22em;text-transform:uppercase;color:#7c89a6}
h1{font-size:clamp(30px,5vw,56px);font-weight:800;margin:14px 0 10px;letter-spacing:-.02em}
h2{font-size:clamp(24px,3.4vw,38px);font-weight:800;margin:8px 0 6px}
h1 .x,h2 .x{background:linear-gradient(90deg,var(--g1),#9aa7ff);-webkit-background-clip:text;background-clip:text;color:transparent}
.lead{font-size:clamp(16px,1.7vw,20px);color:#9fb0cb;max-width:760px}
.reveal{opacity:0;transform:translateY(26px);transition:opacity .7s ease,transform .7s cubic-bezier(.2,.8,.3,1)}
.reveal.seen{opacity:1;transform:none}
.hero{min-height:86vh;display:flex;flex-direction:column;justify-content:center;
 background:radial-gradient(120% 80% at 50% 0%,#16204000,#0c1426 60%,#070a12)}
.badge{display:inline-block;margin-top:22px;padding:7px 16px;border:1px solid rgba(127,166,255,.4);
 border-radius:999px;font:600 13px 'JetBrains Mono';color:#9db8ff;letter-spacing:.16em}
/* config template */
.tmpl{display:grid;grid-template-columns:1.55fr 1fr;gap:34px;align-items:start;margin-top:30px}
@media(max-width:900px){.tmpl{grid-template-columns:1fr}}
.mc{border:1px solid #1e2a44;border-radius:16px;background:#0d1426;margin-bottom:18px;overflow:hidden;
 transition:opacity .6s ease,filter .6s ease}
.mc-tag{font:600 14px 'JetBrains Mono';padding:11px 16px;background:#111b32;color:#bcd0f5;border-bottom:1px solid #1e2a44}
.mc-tag i{color:#7c89a6;font-style:normal}
.mc-body{display:grid;grid-template-columns:1fr 1fr;gap:18px;padding:18px}
@media(max-width:680px){.mc-body{grid-template-columns:1fr}}
.qstem{font-size:15px;color:#cdd8ec;margin-bottom:10px;font-weight:600}
.cimg{width:100%;border-radius:10px;display:block}
.ctext{font:500 15px 'JetBrains Mono';color:#9fb0cb;padding:20px;border:1px dashed #2a3a5c;border-radius:10px;text-align:center}
.mc-opts{display:flex;flex-direction:column;gap:9px;justify-content:center}
.opt{display:flex;align-items:center;gap:11px;padding:10px 13px;border:1px solid #25324f;
 border-radius:10px;background:#0b1322;font-size:14px}
.opt b{width:20px;height:20px;flex:none;border-radius:5px;background:#1c2740;color:#aab6d0;
 font-size:12px;display:grid;place-items:center}
.opt.ok{border-color:rgba(56,211,159,.5);background:rgba(56,211,159,.08)}
.opt.ok b{background:var(--ok);color:#06281d}
.opt .mut{color:#8b96ad}.wv{width:60px;height:24px;flex:none}.wv rect{fill:#5b8def}
.mc-note{font:500 12px 'JetBrains Mono';color:#7c89a6;padding:9px 16px;border-top:1px solid #1e2a44}
.tmpl.collapsed .mc{opacity:.16;filter:saturate(.3)}
.six{margin-top:8px}
.crow{display:flex;align-items:center;gap:14px;padding:11px 15px;border:1px solid #20304e;
 border-radius:11px;background:#0c1528;margin-bottom:9px;opacity:0;transform:translateX(-22px);
 transition:opacity .5s ease,transform .5s cubic-bezier(.2,1,.3,1)}
.six.go .crow{opacity:1;transform:none}
.crow .cc{font:700 15px 'JetBrains Mono';color:#fff;width:46px}
.crow .cn{font-weight:700;color:var(--c)}
.crow .ar{flex:1;text-align:center;font:500 12px 'JetBrains Mono';color:#6b7796}
.def{border-left:3px solid var(--g1);padding:14px 18px;background:#0c1426;border-radius:0 12px 12px 0;
 font-size:15px;color:#aebcd6;margin-top:18px}
.def code{font-family:'JetBrains Mono';color:#9db8ff}
/* tasks */
.fcs{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:18px;margin-top:30px}
.fc{border:1px solid #1e2a44;border-radius:14px;overflow:hidden;background:#0d1426}
.fc img{width:100%;height:140px;object-fit:cover;display:block;filter:saturate(1.05)}
.fct{padding:13px 15px}.fct b{font-size:17px}.fct span{display:block;color:#8b96ad;font-size:13px;margin-top:5px}
/* stats */
.stab{width:100%;border-collapse:collapse;margin-top:26px;font-size:15px}
.stab td{padding:9px 14px;border-bottom:1px solid #18223a}
.stab .fhdr td{font-weight:800;color:#fff;background:#0e1830}
.stab .num{text-align:right;font-family:'JetBrains Mono';color:#bcd0f5}
.stab .dot{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:9px;vertical-align:middle}
.tot{margin-top:16px;font:700 20px 'Inter';color:#fff}.tot b{color:#9db8ff}
/* results */
.figs{display:flex;flex-direction:column;gap:30px;margin-top:30px}
.figc{border:1px solid #1e2a44;border-radius:14px;background:#0d1426;padding:16px}
.figc h3{font-size:17px;margin-bottom:4px}.figc p{color:#8b96ad;font-size:13px;margin-bottom:12px}
.figc img{width:100%;border-radius:8px;background:#fff}
.foot{text-align:center;padding:7vh 5vw;color:#7c89a6;font-size:14px}
.foot a{color:#9db8ff;text-decoration:none}
</style></head><body>

<section class="sec hero">
  <div class="k">ICLR 2026 · arXiv 2510.15148</div>
  <h1><span class="x">XModBench</span> — how it works</h1>
  <p class="lead">One question, asked across every modality. A four-choice template,
  five task families, 61,320 items — and what current omni-models actually do with them.</p>
  <span class="badge">scroll ↓</span>
</section>

<section class="sec">
  <div class="k reveal">The template</div>
  <h2 class="reveal">Same question, <span class="x">six configurations</span></h2>
  <p class="lead reveal">Each item is a four-choice multiple-choice question — a
  <code>&lt;context&gt;</code> (the question stem) and four <code>&lt;candidates&gt;</code>
  (answer options). Swap which modality carries the context and which carries the
  candidates, and one item becomes six.</p>
  <div class="tmpl" id="tmpl">
    <div class="exwrap reveal">__EX_VT____EX_VA____EX_TA__</div>
    <div>
      <div class="six reveal" id="six">__SIX__</div>
      <div class="def reveal">A <code>&lt;context&gt;</code> + four <code>&lt;candidates&gt;</code>;
      the modality of each is varied to form <b>V→T, V→A, T→A, T→V, A→V, A→T</b>.
      Identical semantics, six modality routings — isolating cross-modal consistency.</div>
    </div>
  </div>
</section>

<section class="sec">
  <div class="k reveal">The tasks</div>
  <h2 class="reveal">Five <span class="x">task families</span>, 17 subtasks</h2>
  <p class="lead reveal">Broad coverage of what a model must actually understand —
  perception, spatial, temporal, linguistic and external-knowledge reasoning.</p>
  <div class="fcs">__FAMS__</div>
</section>

<section class="sec">
  <div class="k reveal">The scale</div>
  <h2 class="reveal">Detailed <span class="x">statistics</span></h2>
  <table class="stab reveal"><tbody>__STATS__</tbody></table>
  <div class="tot reveal">Total: <b>61,320</b> items &nbsp;=&nbsp; 5 families · 17 subtasks · 6 configurations</div>
</section>

<section class="sec">
  <div class="k reveal">The results</div>
  <h2 class="reveal">What models <span class="x">actually do</span></h2>
  <p class="lead reveal">Full benchmark, 12 models (paper numbers). Spatial &amp; temporal
  collapse; every model is systematically weaker on audio; directions of one pair disagree.</p>
  <div class="figs">
    <div class="figc reveal"><h3>Task Competence Gaps</h3><p>Per task family — spatial &amp; temporal stay pinched for every model.</p><img src="__FIG1__"></div>
    <div class="figc reveal"><h3>Modality Disparity</h3><p>Bars drop below zero: models are systematically worse on audio.</p><img src="__FIG2__"></div>
    <div class="figc reveal"><h3>Directional Imbalance</h3><p>The two directions of one modality pair disagree.</p><img src="__FIG3__"></div>
  </div>
</section>

<div class="foot">XModBench · ICLR 2026 ·
 <a href="https://xingruiwang.github.io/projects/XModBench/">project page</a> ·
 <a href="https://arxiv.org/abs/2510.15148">paper</a> ·
 <a href="https://huggingface.co/datasets/RyanWW/XModBench">dataset</a></div>

<script>
const io=new IntersectionObserver((es)=>{es.forEach(e=>{if(e.isIntersecting){
  e.target.classList.add('seen');
  if(e.target.id==='six'){setTimeout(()=>{e.target.classList.add('go');
    document.getElementById('tmpl').classList.add('collapsed');},700);}
}});},{threshold:.18});
document.querySelectorAll('.reveal').forEach(el=>io.observe(el));
</script>
</body></html>'''

HTML = (HTML.replace("__EX_VT__", ex_vt).replace("__EX_VA__", ex_va)
        .replace("__EX_TA__", ex_ta)
        .replace("__SIX__", "".join(cfg_row(c) for c in ROWS6))
        .replace("__FAMS__", fam_cards).replace("__STATS__", stat_rows)
        .replace("__FIG1__", FIG["1_task_competence_radar"])
        .replace("__FIG2__", FIG["2_modality_disparity"])
        .replace("__FIG3__", FIG["3_directional_imbalance"]))
OUT.write_text(HTML)
print(f"wrote {OUT}  ({OUT.stat().st_size//1024} KB)")
