"""build_teaser_full.py -> xmodbench_teaser.html  (main animated teaser)

Flow:
  s1  dog-image  ≠  dog-audio   (hook, kept from the short teaser)
  s2  3 modality balls + 6 task arrows
  s3  "Same question, six configurations": one MC item shown as
        V→T  (image ctx, text candidates)
        →scroll-swap candidates→audio, title fades→ V→A (same image, audio)
        →title fades→ T→A (text ctx, audio candidates)
        →all fade out → reveal the <context>/<candidates> definition
          (top) and the 6 routing rows (below)
  s4  5 task families (image impression + subtasks)
  s5  detailed statistics as a donut
  s6  closing card
Loops. Self-contained (dog image/audio + family images base64-inlined).
"""
import base64
import math
import pathlib

H = pathlib.Path("/scratch/xwang378/2025/lmms-eval/lmms_eval/tasks/xmod_bench")
A = H / "teaser_assets"
OUT = H / "xmodbench_teaser.html"

DOG = "data:image/jpeg;base64," + (A / "dog_img_b64.txt").read_text().strip()
WAV = "data:audio/wav;base64," + (A / "dog_wav_b64.txt").read_text().strip()
def fimg(k): return "data:image/jpeg;base64," + base64.b64encode((A / f"fam_{k}.jpg").read_bytes()).decode()
FAM = [
    ("Perception", "#5b8def", fimg("perception"), 24000,
     ["General activities", "Fine-grained activities", "Natural environments",
      "Musical instruments", "Instrument compositions"]),
    ("Spatial", "#f6a609", fimg("spatial"), 7776,
     ["2D Arrangement", "3D Localization", "3D Movement"]),
    ("Temporal", "#ef5a6e", fimg("temporal"), 9000,
     ["Temporal Order", "Temporal Counting", "Temporal Calculation"]),
    ("Linguistic", "#2bc4a8", fimg("speech"), 8244,
     ["Recognition (OCR/ASR)", "Translation (EN-ZH)", "Emotion Classification"]),
    ("Knowledge", "#8b5cf6", fimg("knowledge"), 12300,
     ["Music Genre", "Movie Recognition", "Singer Identification"]),
]
TOTAL = 61320
CHOICES = ["dog howling", "chicken clucking", "crocodile hissing", "cuckoo bird calling"]


# ---- s2 : 3 balls + 6 arrows ----
def build_s2():
    R = 62
    nodes = {"A": (500, 145, "Audio", "\U0001F50A", "#5b8def"),
             "V": (245, 432, "Vision", "\U0001F441", "#8b5cf6"),
             "T": (755, 432, "Text", "T", "#2bc4a8")}
    tasks = [("A", "V", "A→V"), ("V", "A", "V→A"), ("A", "T", "A→T"),
             ("T", "A", "T→A"), ("V", "T", "V→T"), ("T", "V", "T→V")]

    def pt(cx, cy, tx, ty, r):
        d = math.hypot(tx - cx, ty - cy)
        return cx + (tx - cx) / d * r, cy + (ty - cy) / d * r
    arrows, labels = [], []
    for i, (s, e, lab) in enumerate(tasks):
        sx, sy, *_ = nodes[s]; ex, ey, *_ = nodes[e]
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        dx, dy = ex - sx, ey - sy
        L = math.hypot(dx, dy)
        px, py = -dy / L, dx / L
        cxp, cyp = mx + px * 95, my + py * 95
        a0 = pt(sx, sy, cxp, cyp, R + 6)
        a1 = pt(ex, ey, cxp, cyp, R + 14)
        c = nodes[s][4]
        arrows.append(
            f'<path class="arr" pathLength="1" d="M{a0[0]:.1f},{a0[1]:.1f} '
            f'Q{cxp:.1f},{cyp:.1f} {a1[0]:.1f},{a1[1]:.1f}" fill="none" stroke="{c}" '
            f'stroke-width="4.5" marker-end="url(#ah{i})" stroke-linecap="round"/>'
            f'<marker id="ah{i}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" '
            f'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>')
        lx, ly = mx + px * 118, my + py * 118
        labels.append(f'<text class="alab" x="{lx:.0f}" y="{ly:.0f}" fill="{c}" font-size="20" '
                       f'font-weight="700" text-anchor="middle" font-family="JetBrains Mono,monospace">{lab}</text>')
    balls = []
    for nid, (cx, cy, lab, gly, c) in nodes.items():
        balls.append(
            f'<g class="ball" data-n="{nid}"><circle cx="{cx}" cy="{cy}" r="{R}" fill="{c}" '
            f'fill-opacity="0.16" stroke="{c}" stroke-width="3"/>'
            f'<text x="{cx}" y="{cy-4}" text-anchor="middle" font-size="34">{gly}</text>'
            f'<text x="{cx}" y="{cy+30}" text-anchor="middle" fill="#e8edf6" font-size="20" '
            f'font-weight="700" font-family="Inter,sans-serif">{lab}</text></g>')
    return '<svg viewBox="0 0 1000 560">' + "".join(arrows) + "".join(labels) + "".join(balls) + "</svg>"


WV = ('<svg class="wv" viewBox="0 0 60 24">' +
      "".join(f'<rect x="{i*5+2}" y="{12-h}" width="3" height="{h*2}" rx="1"/>'
              for i, h in enumerate([3, 7, 11, 6, 9, 4, 8, 10, 5, 7, 3])) + "</svg>")


def opts(kind):
    out = []
    for i, c in enumerate(CHOICES):
        ok = " ok" if i == 0 else ""
        L = "ABCD"[i]
        if kind == "text":
            out.append(f'<div class="opt{ok}"><b>{L}</b><span>{c}</span></div>')
        else:
            out.append(f'<div class="opt{ok}"><b>{L}</b>{WV}<span class="mut">{c}</span></div>')
    return "".join(out)


IMG_CTX = f'<div class="qstem">Which sound matches what is shown?</div><img class="cimg" src="{DOG}">'
TXT_CTX = '<div class="qstem">Which sound matches what is shown?</div><div class="ctext">[ a dog, mid-shot, outdoors ]</div>'

SIX = ('<div class="six" id="tsix">'
       '<div class="crow"><span class="cc">V→T</span><span class="cn" style="--c:#8b5cf6">🖼 Vision</span><span class="ar">context&nbsp;→&nbsp;candidates</span><span class="cn" style="--c:#2bc4a8">🔤 Text</span></div>'
       '<div class="crow"><span class="cc">V→A</span><span class="cn" style="--c:#8b5cf6">🖼 Vision</span><span class="ar">context&nbsp;→&nbsp;candidates</span><span class="cn" style="--c:#5b8def">🔊 Audio</span></div>'
       '<div class="crow"><span class="cc">T→A</span><span class="cn" style="--c:#2bc4a8">🔤 Text</span><span class="ar">context&nbsp;→&nbsp;candidates</span><span class="cn" style="--c:#5b8def">🔊 Audio</span></div>'
       '<div class="crow"><span class="cc">T→V</span><span class="cn" style="--c:#2bc4a8">🔤 Text</span><span class="ar">context&nbsp;→&nbsp;candidates</span><span class="cn" style="--c:#8b5cf6">🖼 Vision</span></div>'
       '<div class="crow"><span class="cc">A→V</span><span class="cn" style="--c:#5b8def">🔊 Audio</span><span class="ar">context&nbsp;→&nbsp;candidates</span><span class="cn" style="--c:#8b5cf6">🖼 Vision</span></div>'
       '<div class="crow"><span class="cc">A→T</span><span class="cn" style="--c:#5b8def">🔊 Audio</span><span class="ar">context&nbsp;→&nbsp;candidates</span><span class="cn" style="--c:#2bc4a8">🔤 Text</span></div>'
       '</div>')
DEF = ('<div class="def" id="tdef">A <code>&lt;context&gt;</code> + four <code>&lt;candidates&gt;</code>; '
       'the modality of each is varied to form <b>V→T, V→A, T→A, T→V, A→V, A→T</b>. '
       'Identical semantics, six modality routings — isolating cross-modal consistency.</div>')

def fvid(k):
    return "data:video/mp4;base64," + base64.b64encode((A / f"fam_{k}.mp4").read_bytes()).decode()
VID = {"Spatial": fvid("spatial"), "Temporal": fvid("temporal"), "Knowledge": fvid("knowledge")}

def _fc(n, c, im, q, subs):
    if n in VID:
        media = (f'<div class="fc-im"><video autoplay muted loop playsinline '
                 f'src="{VID[n]}"></video></div>')
    else:
        media = f'<div class="fc-im" style="background-image:url({im})"></div>'
    return (f'<div class="fc" style="--c:{c}">{media}'
            f'<div class="fc-b"><b>{n}</b><span>{q:,} items</span><ul>'
            + "".join(f"<li>{s}</li>" for s in subs) + '</ul></div></div>')
fam_cards = "".join(_fc(*f) for f in FAM)


def pol(cx, cy, r, deg):
    a = math.radians(deg - 90)
    return cx + r * math.cos(a), cy + r * math.sin(a)
segs, legend, a0 = [], [], 0.0
for n, c, im, q, subs in FAM:
    sw = q / TOTAL * 360; a1 = a0 + sw
    x0, y0 = pol(230, 230, 175, a0); x1, y1 = pol(230, 230, 175, a1)
    xi1, yi1 = pol(230, 230, 100, a1); xi0, yi0 = pol(230, 230, 100, a0)
    lg = 1 if sw > 180 else 0
    segs.append(f'<path class="seg" style="--i:{len(segs)}" d="M{x0:.1f},{y0:.1f} '
                f'A175,175 0 {lg} 1 {x1:.1f},{y1:.1f} L{xi1:.1f},{yi1:.1f} '
                f'A100,100 0 {lg} 0 {xi0:.1f},{yi0:.1f} Z" fill="{c}"/>')
    legend.append(f'<div class="lg"><span style="background:{c}"></span>{n} &middot; {q:,} ({q/TOTAL*100:.0f}%)</div>')
    a0 = a1
DONUT = (f'<svg viewBox="0 0 460 460" class="donut">{"".join(segs)}'
         f'<text x="230" y="220" text-anchor="middle" class="dc1">61,320</text>'
         f'<text x="230" y="250" text-anchor="middle" class="dc2">items · 17 subtasks</text></svg>'
         f'<div class="lgs">{"".join(legend)}</div>')

HTML = r'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>XModBench — teaser</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
<style>
:root{--g1:#667eea;--g2:#764ba2;--ok:#38d39f;--bad:#ff5a6e;--ink:#e8edf6;--dim:#8b96ad}
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;background:#05070d;font-family:'Inter',sans-serif;overflow:hidden}
#wrap{position:fixed;inset:0;display:grid;place-items:center;background:#05070d}
#stage{position:relative;width:min(100vw,177.78vh);height:min(56.25vw,100vh);
 background:radial-gradient(120% 90% at 50% 0%,#101a33 0%,#0a0e1a 55%,#05070d 100%);overflow:hidden;color:var(--ink)}
.scene{position:absolute;inset:0;display:grid;place-items:center;opacity:0;transition:opacity .6s ease;padding:0 6vw}
.scene.on{opacity:1}
.k{font:600 1.7vh 'JetBrains Mono',monospace;letter-spacing:.22em;text-transform:uppercase;color:#7c89a6}
.gr{background:linear-gradient(90deg,var(--g1),#9aa7ff);-webkit-background-clip:text;background-clip:text;color:transparent}
/* s1 hook */
#s1 .s1top{position:absolute;top:5.5%;left:0;width:100%;text-align:center;
 font:800 5vh 'Inter',sans-serif;letter-spacing:-.01em;color:#eef2fb;line-height:1.1}
#s1 .s1top .gr{font-weight:800}
#s1 .q{font:500 2.5vh 'JetBrains Mono',monospace;color:var(--dim)}
#s1 .row{display:flex;gap:7vw;align-items:center}
.card{display:flex;flex-direction:column;align-items:center;gap:2vh;opacity:0;transform:translateY(18px)}
.card.in{opacity:1;transform:none;transition:all .7s cubic-bezier(.2,.7,.2,1)}
.media{width:25vh;height:25vh;border-radius:18px;overflow:hidden;border:1px solid rgba(255,255,255,.08)}
.media img{width:100%;height:100%;object-fit:cover}
.wave{display:flex;align-items:center;justify-content:center;gap:.7vh;width:100%;height:100%;background:linear-gradient(160deg,#1a2440,#0c1226)}
.wave i{width:1.1vh;background:linear-gradient(180deg,var(--g1),var(--g2));border-radius:3px;height:14%;animation:eq 1s ease-in-out infinite}
@keyframes eq{0%,100%{height:14%}50%{height:78%}}
.tag{font:500 2vh 'JetBrains Mono',monospace;color:var(--dim)}
.ans{font-size:2.6vh;font-weight:700;padding:.7vh 2vh;border-radius:999px;opacity:0;transform:scale(.7)}
.ans.show{opacity:1;transform:scale(1);transition:all .45s cubic-bezier(.2,1.6,.4,1)}
.ans.ok{color:var(--ok);background:rgba(56,211,159,.12);border:1px solid rgba(56,211,159,.4)}
.ans.bad{color:var(--bad);background:rgba(255,90,110,.12);border:1px solid rgba(255,90,110,.4)}
#neq{position:absolute;display:flex;align-items:center;gap:4vw;font-size:11vh;font-weight:800;opacity:0;transform:scale(.6);filter:blur(6px)}
#neq.slam{opacity:1;transform:scale(1);filter:blur(0);transition:all .55s cubic-bezier(.2,1.5,.3,1)}
#neq .ne{color:var(--bad);text-shadow:0 0 36px rgba(255,90,110,.65)}
#neq.slam .ne{animation:pulse 1.05s ease-in-out infinite}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.18)}}
.line{position:absolute;bottom:9%;width:100%;text-align:center;font-size:2.8vh;font-weight:600;color:#cfd8ea;opacity:0;transform:translateY(14px)}
.line.show{opacity:1;transform:none;transition:all .7s ease}
.line b{color:#9aa7ff}
/* s2 balls */
#s2 .wrap2{position:relative;width:100%;height:100%;display:grid;place-items:center}
#s2 svg{width:80%;height:80%}
#s2 .head{position:absolute;top:7%;width:100%;text-align:center;font-size:3vh;font-weight:700;color:#dfe6f5;opacity:0;transform:translateY(-12px);transition:all .6s}
#s2 .head.show{opacity:1;transform:none}
.ball{opacity:0;transform:scale(.2);transform-box:fill-box;transform-origin:center;transition:transform .55s cubic-bezier(.2,1.6,.35,1),opacity .4s}
.ball.in{opacity:1;transform:scale(1)}
.arr{stroke-dasharray:1;stroke-dashoffset:1;transition:stroke-dashoffset .6s ease}
.arr.draw{stroke-dashoffset:0}.alab{opacity:0;transition:opacity .4s}.alab.draw{opacity:1}
/* s3 template */
#s3{display:flex;flex-direction:column;align-items:center;justify-content:center;
 padding:5vh 6vw;gap:2.6vh}
#s3 .thead{flex:none;text-align:center;max-width:80vw}
#s3 .thead .k{margin-bottom:.8vh}
#s3 .thead .h{font-size:3.2vh;font-weight:800}
#s3 .thead .s{font-size:1.55vh;color:var(--dim);max-width:62vw;margin:1vh auto 0;line-height:1.55}
#s3 .s3body{position:relative;display:grid;width:64vw;flex:none}
#s3 .s3body>div{grid-area:1/1;align-self:center}
.mc{width:100%;border:1px solid #1e2a44;border-radius:16px;background:#0d1426;overflow:hidden;
 opacity:0;transform:translateY(20px);transition:opacity .55s ease,transform .55s ease}
.mc.in{opacity:1;transform:none}
.mc-tag{font:600 2vh 'JetBrains Mono',monospace;padding:1.3vh 2vw;background:#111b32;color:#bcd0f5;
 border-bottom:1px solid #1e2a44;transition:opacity .35s ease}
.mc-tag.fade{opacity:0}.mc-tag i{color:#7c89a6;font-style:normal}
.mc-body{display:grid;grid-template-columns:1fr 1fr;gap:2vw;padding:2.2vh 2vw}
.mc-ctx{transition:opacity .4s ease}.mc-ctx.fade{opacity:0}
.qstem{font-size:1.8vh;color:#cdd8ec;margin-bottom:1vh;font-weight:600}
.cimg{width:100%;max-height:30vh;object-fit:cover;border-radius:10px;display:block}
.ctext{font:500 2vh 'JetBrains Mono';color:#9fb0cb;padding:3vh 2vh;border:1px dashed #2a3a5c;border-radius:10px;text-align:center}
.mc-opts{display:flex;flex-direction:column;gap:1vh;justify-content:center;transition:transform .5s cubic-bezier(.3,.8,.3,1),opacity .45s ease}
.mc-opts.up{transform:translateY(-26px);opacity:0}
.opt{display:flex;align-items:center;gap:1vw;padding:1.1vh 1.2vw;border:1px solid #25324f;border-radius:10px;background:#0b1322;font-size:1.7vh}
.opt b{width:2.4vh;height:2.4vh;flex:none;border-radius:5px;background:#1c2740;color:#aab6d0;font-size:1.3vh;display:grid;place-items:center}
.opt.ok{border-color:rgba(56,211,159,.5);background:rgba(56,211,159,.08)}.opt.ok b{background:var(--ok);color:#06281d}
.opt .mut{color:#8b96ad}.wv{width:60px;height:24px;flex:none}.wv rect{fill:#5b8def}
.tend{display:flex;flex-direction:column;align-items:center;gap:2vh;width:100%;opacity:0;transform:translateY(18px);transition:all .6s ease}
.tend.on{opacity:1;transform:none}
.def{border-left:3px solid var(--g1);padding:1.6vh 2vw;background:#0c1426;border-radius:0 12px 12px 0;font-size:2vh;color:#aebcd6;line-height:1.5}
.def code{font-family:'JetBrains Mono';color:#9db8ff}.def b{color:#cfd8ea}
.six{display:flex;flex-direction:column;gap:1vh;width:100%}
.crow{display:flex;align-items:center;gap:1.4vw;padding:1.1vh 1.5vw;border:1px solid #20304e;border-radius:11px;background:#0c1528;
 opacity:0;transform:translateX(-22px);transition:opacity .45s ease,transform .45s cubic-bezier(.2,1,.3,1)}
.six.go .crow{opacity:1;transform:none}
.crow .cc{font:700 2vh 'JetBrains Mono';color:#fff;width:5vw}
.crow .cn{font-weight:700;color:var(--c)}.crow .ar{flex:1;text-align:center;font:500 1.5vh 'JetBrains Mono';color:#6b7796}
/* s4 families */
#s4 .ht{position:absolute;top:7%;width:100%;text-align:center;font-size:3.6vh;font-weight:800}
.fcs{display:flex;gap:1.2vw;width:88vw;justify-content:center}
.fc{flex:1;border-radius:14px;overflow:hidden;background:#0d1426;border:1px solid #1e2a44;opacity:0;transform:translateY(20px);transition:all .55s cubic-bezier(.2,1,.3,1)}
.fc.in{opacity:1;transform:none}
.fc-im{height:15vh;background-size:cover;background-position:center;border-bottom:3px solid var(--c);overflow:hidden}
.fc-im video{width:100%;height:100%;object-fit:cover;display:block}
.fc-b{padding:1.3vh 1vw}.fc-b b{font-size:2vh;color:#fff}
.fc-b span{display:block;font:500 1.3vh 'JetBrains Mono';color:var(--c);margin:.3vh 0 .9vh}
.fc-b ul{list-style:none;font-size:1.4vh;color:#9fb0cb}.fc-b li{padding:.2vh 0;border-top:1px solid #18223a}
/* s5 donut */
#s5 .ht{position:absolute;top:7%;width:100%;text-align:center;font-size:3.6vh;font-weight:800}
.dwrap{display:flex;align-items:center;gap:4vw}
.donut{width:40vh;height:40vh}
.donut .seg{opacity:0;transform-box:fill-box;transform-origin:230px 230px;transform:scale(.4);transition:opacity .5s,transform .6s cubic-bezier(.2,1.4,.3,1)}
.donut.go .seg{opacity:1;transform:none;transition-delay:calc(var(--i)*.13s)}
.dc1{fill:#fff;font:800 4.4vh 'Inter'}.dc2{fill:var(--dim);font:600 1.8vh 'JetBrains Mono'}
.lgs{display:flex;flex-direction:column;gap:1.4vh}.lg{display:flex;align-items:center;gap:1vw;font-size:2.1vh;color:#cfd8ea}
.lg span{width:1.6vh;height:1.6vh;border-radius:4px}
/* s6 card */
#s6 .logo{font-size:8vh;font-weight:800}.url{margin-top:3vh;font:500 2vh 'JetBrains Mono';color:#7fa6ff}
.badge{display:inline-block;margin-top:2vh;padding:.6vh 1.8vh;border:1px solid rgba(127,166,255,.4);border-radius:999px;font:600 1.8vh 'JetBrains Mono';color:#9db8ff;letter-spacing:.15em}
#s6 .sub{font-size:2.4vh;color:var(--dim);margin-top:1.4vh}
/* experiment scenes (xpA collapse / xpB disparity / xpC insight) */
.xb-wrap{position:relative;width:100%;height:100%;display:grid;place-items:center}
.xb-head{position:absolute;top:8%;width:100%;text-align:center;font-size:3.4vh;font-weight:700;color:#dfe6f5;opacity:0;transform:translateY(-12px);transition:all .6s}
.xb-head.show{opacity:1;transform:none}.xb-head b{color:#9aa7ff}
.xb-sub{position:absolute;bottom:8%;width:100%;text-align:center;font:500 2vh 'JetBrains Mono',monospace;color:#8b96ad;opacity:0;transition:opacity .6s}
.xb-sub.show{opacity:1}.xb-sub b{color:#cfd8ea}
.xb-bars{display:flex;align-items:flex-end;gap:3.2vw;height:50vh}
.xb-bar{position:relative;width:7vw;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%}
.xb-bar .fl{width:100%;height:0;background:var(--c);border-radius:8px 8px 0 0;transition:height 1s cubic-bezier(.3,.7,.3,1)}
.xb-bar.grow .fl{height:var(--h)}
.xb-bar .v{font-size:2.6vh;font-weight:800;color:#fff;margin-bottom:.6vh;opacity:0;transition:opacity .4s ease .6s}
.xb-bar.grow .v{opacity:1}.xb-bar em{margin-top:1vh;font-size:1.8vh;color:#aab6d0;font-style:normal}
.xb-bar.dz.flash .fl{background:#ff4d63;box-shadow:0 0 26px rgba(255,77,99,.6)}
.xb-bar.dz.flash .v{color:#ff8a98}
.xb-seesaw{position:relative;width:46vw;height:24vh;margin-top:2vh}
.xb-beam{position:absolute;top:42%;left:0;width:100%;height:2.4vh;border-radius:6px;background:linear-gradient(90deg,#5b8def,#2bc4a8);transform:rotate(0);transform-origin:50% 50%;transition:transform 1s cubic-bezier(.3,.8,.3,1);display:flex;justify-content:space-between;align-items:center}
.xb-seesaw.tip .xb-beam{transform:rotate(-11deg)}
.xb-pan{transform:translateY(-3.2vh);font-size:2.1vh;font-weight:700;color:#fff;text-align:center}.xb-pan small{font-size:1.5vh;color:#cbd5e0;font-weight:500}
.xb-piv{position:absolute;left:calc(50% - 1.4vh);top:42%;border-left:1.4vh solid transparent;border-right:1.4vh solid transparent;border-bottom:7vh solid #2a3550}
.xb-imb{display:flex;flex-direction:column;gap:1.3vh;margin-top:3vh;width:50vw}
.xb-mname{font:600 1.7vh 'JetBrains Mono',monospace;color:#9fb0cb;margin-bottom:.4vh}
.xb-ia{display:flex;align-items:center;gap:1.2vw;font-family:'JetBrains Mono',monospace;font-size:2vh;color:#cbd5e0}
.xb-ia span{width:4vw}
.xb-ia .ib{position:relative;height:3.2vh;width:0;background:linear-gradient(90deg,#667eea,#764ba2);border-radius:5px;transition:width .9s cubic-bezier(.3,.8,.3,1)}
.xb-ia .ib2{background:linear-gradient(90deg,#5b6bb0,#7c5fa0)}
.xb-ia .ib i{position:absolute;right:.8vw;top:50%;transform:translateY(-50%);font-style:normal;font-weight:800;font-size:1.8vh;color:#fff;opacity:0;transition:opacity .4s ease .5s}
.xb-imb.go .ib{width:var(--w)}.xb-imb.go .ib i{opacity:1}
.xb-drop{display:flex;align-items:center;gap:1.4vw;margin-top:1.4vh;opacity:0;transform:scale(.8);
 transition:opacity .5s ease .5s,transform .55s cubic-bezier(.2,1.6,.3,1) .5s}
.xb-imb.go .xb-drop{opacity:1;transform:none}
.xb-drop b{font:800 6vh 'Inter',sans-serif;color:#ff5a6e;text-shadow:0 0 28px rgba(255,90,110,.5);line-height:1}
.xb-drop small{font:600 1.5vh 'JetBrains Mono',monospace;color:#ff9aa6;text-transform:uppercase;letter-spacing:.1em;line-height:1.4}
.xb-split{display:flex;gap:3vw}
.xb-card{width:24vw;padding:3vh 2vw;border-radius:16px;text-align:center;border:1.5px solid;opacity:0;transform:translateY(20px);transition:all .6s ease}
.xb-card.in{opacity:1;transform:none}
.xb-card .ot{font-size:2.3vh;font-weight:800;color:#fff}.xb-card .oc{font-size:1.7vh;color:#9fb0cb;margin:1.4vh 0}.xb-card .om{font-size:2.3vh;font-weight:800}
.xb-bad{border-color:rgba(255,90,110,.45);background:rgba(255,90,110,.07)}.xb-bad .om{color:#ff6e7e}
.xb-good{border-color:rgba(56,211,159,.3);background:rgba(56,211,159,.05)}
.xb-good.lit{border-color:rgba(56,211,159,.75);background:rgba(56,211,159,.16);box-shadow:0 0 40px rgba(56,211,159,.22)}
.xb-good .om{color:#38d39f}
.ctl{position:fixed;right:18px;bottom:14px;z-index:9}
.ctl button{background:rgba(255,255,255,.06);color:#aab6d0;border:1px solid rgba(255,255,255,.12);padding:7px 13px;border-radius:8px;font:12px 'JetBrains Mono';cursor:pointer}
</style></head><body>
<div id="wrap"><div id="stage">

  <section id="s1" class="scene">
    <div class="s1top">For <span class="gr">Omni-modality Language Models</span></div>
    <div class="q" id="q1">Which represents a dog?</div>
    <div class="row">
      <div class="card" id="cImg"><div class="media"><img src="__DOG__"></div>
        <div class="tag">model sees &rarr;</div><div class="ans ok" id="aImg">🐕 &nbsp;Dog &nbsp;✓</div></div>
      <div class="card" id="cAud"><div class="media"><div class="wave" id="wave"></div></div>
        <div class="tag">model hears &rarr;</div><div class="ans bad" id="aAud">&ldquo;a person talking&rdquo; &nbsp;✗</div></div>
    </div>
    <div id="neq"><span>🐕</span><span class="ne">&ne;</span><span>🔊</span></div>
    <div class="line" id="ln1">A model that knows a dog <b>by sight</b> can&rsquo;t <b>hear</b> one.</div>
  </section>

  <section id="s2" class="scene"><div class="wrap2">
    <div class="head" id="s2h">Three modalities &nbsp;·&nbsp; <span class="gr">six cross-modal directions</span></div>
    __S2SVG__
  </div></section>

  <section id="s3" class="scene">
    <div class="thead">
      <div class="k">The template</div>
      <div class="h">Same question, <span class="gr">six configurations</span></div>
      <div class="s">Each item is a four-choice multiple-choice question — a <code style="color:#9db8ff">&lt;context&gt;</code> (the question stem) and four <code style="color:#9db8ff">&lt;candidates&gt;</code> (answer options). Swap which modality carries the context and which carries the candidates, and one item becomes six.</div>
    </div>
    <div class="s3body">
      <div class="mc" id="mc">
        <div class="mc-tag" id="mcTag">V &rarr; T &nbsp;<i>(vision context, text candidates)</i></div>
        <div class="mc-body">
          <div class="mc-ctx" id="mcCtx">__IMGCTX__</div>
          <div class="mc-opts" id="mcOpts">__OPT_T__</div>
        </div>
      </div>
      <div class="tend" id="tend">__DEF____SIX__</div>
    </div>
  </section>

  <section id="s4" class="scene">
    <div class="ht">Five <span class="gr">task families</span>, 17 subtasks</div>
    <div class="fcs" id="fcs">__FAMS__</div>
  </section>

  <section id="s5" class="scene">
    <div class="ht">Detailed <span class="gr">statistics</span></div>
    <div class="dwrap" id="dwrap">__DONUT__</div>
  </section>

  <section id="xpA" class="scene"><div class="xb-wrap">
    <div class="xb-head" id="xpAh">But <b>spatial &amp; temporal reasoning collapses</b></div>
    <div class="xb-bars">
      <div class="xb-bar" style="--c:#5b8def;--h:79.7%"><span class="v">79.7</span><div class="fl"></div><em>Perception</em></div>
      <div class="xb-bar dz" style="--c:#f6a609;--h:35.2%"><span class="v">35.2</span><div class="fl"></div><em>Spatial</em></div>
      <div class="xb-bar dz" style="--c:#ef5a6e;--h:41.4%"><span class="v">41.4</span><div class="fl"></div><em>Temporal</em></div>
      <div class="xb-bar" style="--c:#2bc4a8;--h:82.5%"><span class="v">82.5</span><div class="fl"></div><em>Linguistic</em></div>
      <div class="xb-bar" style="--c:#8b5cf6;--h:77.4%"><span class="v">77.4</span><div class="fl"></div><em>Knowledge</em></div>
    </div>
    <div class="xb-sub" id="xpAs">spatial 35.2 / temporal 41.4 &nbsp;vs&nbsp; linguistic 82.5 &nbsp;&mdash;&nbsp; accuracy %, Qwen3-Omni on XModBench-Lite</div>
  </div></section>

  <section id="xpB" class="scene"><div class="xb-wrap">
    <div class="xb-head" id="xpBh">The <b>same knowledge</b>, unequal across modalities</div>
    <div class="xb-seesaw" id="seesaw">
      <div class="xb-beam"><span class="xb-pan">Audio<br><small>low</small></span><span class="xb-pan">Text<br><small>high</small></span></div>
      <div class="xb-piv"></div>
    </div>
    <div class="xb-imb" id="ximb">
      <div class="xb-mname">Qwen3-Omni &nbsp;·&nbsp; directional imbalance (V&harr;T) &nbsp;·&nbsp; accuracy&nbsp;%</div>
      <div class="xb-ia"><span>V&rarr;T</span><div class="ib" style="--w:79.7%"><i>79.7</i></div></div>
      <div class="xb-ia"><span>T&rarr;V</span><div class="ib ib2" style="--w:66.0%"><i>66.0</i></div></div>
      <div class="xb-drop"><b>&minus;13.7</b><small>capability lost when the<br>same pair is asked the other way</small></div>
    </div>
    <div class="xb-sub" id="xpBs">same knowledge, asked V&rarr;T vs T&rarr;V &nbsp;&mdash;&nbsp; <b>13.7-pt</b> directional gap (Qwen3-Omni, XModBench-Lite)</div>
  </div></section>

  <section id="s6" class="scene">
    <div style="text-align:center">
      <div class="logo"><span class="gr">XMod</span>Bench</div>
      <div class="sub">Cross-modal consistency, measured.</div>
      <div><span class="badge">ICLR 2026</span></div>
      <div class="url">xingruiwang.github.io/projects/XModBench</div>
    </div>
  </section>

</div></div>
<div class="ctl"><button id="rep">&#8634; replay</button></div>
<audio id="bark" preload="auto" src="__WAV__"></audio>
<script>
const $=s=>document.querySelector(s),sleep=ms=>new Promise(r=>setTimeout(r,ms));
const OPT_T=`__OPT_T__`,OPT_A=`__OPT_A__`,IMGCTX=`__IMGCTX__`,TXTCTX=`__TXTCTX__`;
const wave=$('#wave');for(let i=0;i<26;i++){const b=document.createElement('i');b.style.animationDelay=(i*.045)+'s';wave.appendChild(b);}
const ALL=['s1','s2','s3','s4','s5','xpA','xpB','s6'];
function reset(){ALL.forEach(x=>$('#'+x).classList.remove('on'));
 ['cImg','cAud'].forEach(x=>$('#'+x).classList.remove('in'));
 ['aImg','aAud'].forEach(x=>$('#'+x).classList.remove('show'));
 $('#neq').classList.remove('slam');$('#ln1').classList.remove('show');$('#q1').style.opacity=0;
 document.querySelectorAll('#s2 .ball').forEach(b=>b.classList.remove('in'));
 document.querySelectorAll('#s2 .arr,#s2 .alab').forEach(a=>a.classList.remove('draw'));
 $('#s2h').classList.remove('show');
 $('#mc').classList.remove('in');$('#mcOpts').classList.remove('up');$('#mcTag').classList.remove('fade');
 $('#mcCtx').classList.remove('fade');$('#tend').classList.remove('on');$('#tsix').classList.remove('go');
 $('#mcTag').innerHTML='V &rarr; T &nbsp;<i>(vision context, text candidates)</i>';
 $('#mcCtx').innerHTML=IMGCTX;$('#mcOpts').innerHTML=OPT_T;
 document.querySelectorAll('.xb-bar').forEach(b=>b.classList.remove('grow','flash'));
 $('#seesaw').classList.remove('tip');$('#ximb').classList.remove('go');
 ['xpAh','xpAs','xpBh','xpBs'].forEach(x=>{const e=$('#'+x);if(e)e.classList.remove('show');});
 document.querySelectorAll('.fc').forEach(c=>c.classList.remove('in'));
 const d=$('.donut');if(d)d.classList.remove('go');}
async function swapOpts(html){const o=$('#mcOpts');o.classList.add('up');await sleep(420);
 o.innerHTML=html;o.classList.remove('up');await sleep(420);}
async function fadeTag(html){const t=$('#mcTag');t.classList.add('fade');await sleep(320);
 t.innerHTML=html;t.classList.remove('fade');await sleep(320);}
async function fadeCtx(html){const c=$('#mcCtx');c.classList.add('fade');await sleep(360);
 c.innerHTML=html;c.classList.remove('fade');await sleep(360);}
async function run(){
 reset();await sleep(140);
 // s1
 $('#s1').classList.add('on');await sleep(280);$('#q1').style.transition='opacity .5s';$('#q1').style.opacity=1;
 await sleep(620);$('#cImg').classList.add('in');await sleep(680);$('#aImg').classList.add('show');
 await sleep(620);$('#cAud').classList.add('in');try{$('#bark').volume=.0;}catch(e){}
 await sleep(1300);$('#aAud').classList.add('show');await sleep(750);
 $('#cImg').style.transition=$('#cAud').style.transition='opacity .5s';
 $('#cImg').style.opacity=.12;$('#cAud').style.opacity=.12;$('#q1').style.opacity=0;
 $('#neq').classList.add('slam');await sleep(720);$('#ln1').classList.add('show');await sleep(2400);
 $('#cImg').style.opacity=$('#cAud').style.opacity='';$('#s1').classList.remove('on');await sleep(620);
 // s2
 $('#s2').classList.add('on');await sleep(300);$('#s2h').classList.add('show');
 for(const b of document.querySelectorAll('#s2 .ball')){b.classList.add('in');await sleep(230);}
 await sleep(220);const ar=[...document.querySelectorAll('#s2 .arr')],la=[...document.querySelectorAll('#s2 .alab')];
 for(let i=0;i<ar.length;i++){ar[i].classList.add('draw');la[i].classList.add('draw');await sleep(330);}
 await sleep(2200);$('#s2').classList.remove('on');await sleep(620);
 // s3 template
 $('#s3').classList.add('on');await sleep(500);$('#mc').classList.add('in');
 await sleep(2600);                                   // V→T shown
 await swapOpts(OPT_A);await fadeTag('V &rarr; A &nbsp;<i>(same image, audio candidates)</i>');
 await sleep(2400);                                   // V→A
 await fadeTag('T &rarr; A &nbsp;<i>(text context, audio candidates)</i>');await fadeCtx(TXTCTX);
 await sleep(2600);                                   // T→A
 $('#mc').classList.remove('in');await sleep(620);
 $('#tend').classList.add('on');await sleep(500);$('#tsix').classList.add('go');
 await sleep(3600);$('#s3').classList.remove('on');await sleep(620);
 // s4
 $('#s4').classList.add('on');await sleep(650);
 for(const c of document.querySelectorAll('#fcs .fc')){c.classList.add('in');await sleep(330);}
 await sleep(3000);$('#s4').classList.remove('on');await sleep(620);
 // s5
 $('#s5').classList.add('on');await sleep(500);$('.donut').classList.add('go');
 await sleep(3400);$('#s5').classList.remove('on');await sleep(620);
 // xpA — spatial/temporal collapse
 $('#xpA').classList.add('on');await sleep(300);$('#xpAh').classList.add('show');
 await sleep(400);document.querySelectorAll('.xb-bar').forEach(b=>b.classList.add('grow'));
 await sleep(1300);document.querySelectorAll('.xb-bar.dz').forEach(b=>b.classList.add('flash'));
 await sleep(500);$('#xpAs').classList.add('show');await sleep(2600);
 $('#xpA').classList.remove('on');await sleep(560);
 // xpB — disparity + imbalance
 $('#xpB').classList.add('on');await sleep(300);$('#xpBh').classList.add('show');
 await sleep(500);$('#seesaw').classList.add('tip');
 await sleep(900);$('#ximb').classList.add('go');
 await sleep(900);$('#xpBs').classList.add('show');await sleep(2400);
 $('#xpB').classList.remove('on');await sleep(620);
 // s6
 $('#s6').classList.add('on');await sleep(3200);$('#s6').classList.remove('on');await sleep(700);
 run();
}
$('#rep').onclick=()=>location.reload();
run();
</script></body></html>'''

HTML = (HTML.replace("__DOG__", DOG).replace("__WAV__", WAV)
        .replace("__S2SVG__", build_s2())
        .replace("__OPT_T__", opts("text")).replace("__OPT_A__", opts("audio"))
        .replace("__IMGCTX__", IMG_CTX).replace("__TXTCTX__", TXT_CTX)
        .replace("__DEF__", DEF).replace("__SIX__", SIX)
        .replace("__FAMS__", fam_cards).replace("__DONUT__", DONUT))
OUT.write_text(HTML)
print(f"wrote {OUT}  ({OUT.stat().st_size//1024} KB)")
