"""build_teaser.py — assemble the self-contained XModBench HTML teaser
(S1 hook + S7 card pass). Embeds the real vggss dog image + bark audio
(base64) so the .html is fully portable. Local tool, not shipped."""
import pathlib

A = pathlib.Path("/scratch/xwang378/2025/lmms-eval/lmms_eval/tasks/xmod_bench/teaser_assets")
IMG = A.joinpath("dog_img_b64.txt").read_text().strip()
WAV = A.joinpath("dog_wav_b64.txt").read_text().strip()
OUT = pathlib.Path("/scratch/xwang378/2025/lmms-eval/lmms_eval/tasks/xmod_bench/xmodbench_teaser_short.html")

HTML = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>XModBench — teaser</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
<style>
:root{--blue:#2b6cb0;--g1:#667eea;--g2:#764ba2;--ok:#38d39f;--bad:#ff5a6e;--ink:#e8edf6;--dim:#8b96ad}
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;background:#05070d;font-family:'Inter',sans-serif;overflow:hidden}
#wrap{position:fixed;inset:0;display:grid;place-items:center;background:#05070d}
#stage{position:relative;width:min(100vw,177.78vh);height:min(56.25vw,100vh);
 background:radial-gradient(120% 90% at 50% 0%,#101a33 0%,#0a0e1a 55%,#05070d 100%);
 overflow:hidden;color:var(--ink);box-shadow:0 0 120px rgba(102,126,234,.12) inset}
.scene{position:absolute;inset:0;display:grid;place-items:center;opacity:0;transition:opacity .6s ease}
.scene.on{opacity:1}
.q{font-size:2.6vh;letter-spacing:.04em;color:var(--dim);font-weight:500;
 font-family:'JetBrains Mono',monospace}
/* S1 */
.gr{background:linear-gradient(90deg,var(--g1),#9aa7ff);-webkit-background-clip:text;background-clip:text;color:transparent}
#s1{align-content:center;gap:3.4vh}
#s1 .s1top{position:absolute;top:5.5%;left:0;width:100%;text-align:center;font:800 5vh 'Inter',sans-serif;letter-spacing:-.01em;color:#eef2fb;line-height:1.1}
#s1 .row{display:flex;gap:7vw;align-items:center}
.card{display:flex;flex-direction:column;align-items:center;gap:2.2vh;opacity:0;transform:translateY(18px)}
.card.in{opacity:1;transform:none;transition:all .7s cubic-bezier(.2,.7,.2,1)}
.media{width:26vh;height:26vh;border-radius:18px;overflow:hidden;
 box-shadow:0 18px 50px rgba(0,0,0,.55);border:1px solid rgba(255,255,255,.08);position:relative}
.media img{width:100%;height:100%;object-fit:cover;filter:saturate(1.05)}
.wave{display:flex;align-items:center;justify-content:center;gap:.7vh;
 width:100%;height:100%;background:linear-gradient(160deg,#1a2440,#0c1226)}
.wave i{width:1.1vh;background:linear-gradient(180deg,var(--g1),var(--g2));border-radius:3px;
 height:14%;animation:eq 1s ease-in-out infinite}
.playing .wave i{animation-duration:.55s}
@keyframes eq{0%,100%{height:14%}50%{height:78%}}
.tag{font-family:'JetBrains Mono',monospace;font-size:2.1vh;font-weight:500;color:var(--dim)}
.ans{font-size:2.7vh;font-weight:700;padding:.7vh 2vh;border-radius:999px;opacity:0;transform:scale(.7)}
.ans.show{opacity:1;transform:scale(1);transition:all .45s cubic-bezier(.2,1.6,.4,1)}
.ans.ok{color:var(--ok);background:rgba(56,211,159,.12);border:1px solid rgba(56,211,159,.4)}
.ans.bad{color:var(--bad);background:rgba(255,90,110,.12);border:1px solid rgba(255,90,110,.4)}
#neq{position:absolute;display:flex;align-items:center;gap:4.5vw;font-size:12vh;font-weight:800;
 opacity:0;transform:scale(.6);filter:blur(6px)}
#neq.slam{opacity:1;transform:scale(1);filter:blur(0);transition:all .55s cubic-bezier(.2,1.5,.3,1)}
#neq .ne{color:var(--bad);text-shadow:0 0 36px rgba(255,90,110,.65)}
#neq.slam .ne{animation:pulse 1.05s ease-in-out infinite}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.18)}}
.line{position:absolute;bottom:9%;width:100%;text-align:center;font-size:3vh;font-weight:600;
 color:#cfd8ea;opacity:0;transform:translateY(14px)}
.line.show{opacity:1;transform:none;transition:all .7s ease .1s}
.line b{background:linear-gradient(90deg,var(--g1),#9aa7ff);-webkit-background-clip:text;background-clip:text;color:transparent}
/* S7 */
#s7{background:radial-gradient(110% 90% at 50% 35%,#16224a 0%,#0a1024 60%,#05070d 100%)}
#s7 .logo{font-size:9vh;font-weight:800;letter-spacing:-.02em}
#s7 .logo .x{background:linear-gradient(90deg,var(--g1),var(--g2));-webkit-background-clip:text;background-clip:text;color:transparent}
#s7 .sub{margin-top:1.6vh;font-size:2.8vh;color:var(--dim);font-weight:500;letter-spacing:.18em;text-transform:uppercase}
#s7 .url{margin-top:3.4vh;font-family:'JetBrains Mono',monospace;font-size:2vh;color:#7fa6ff}
#s7 .badge{display:inline-block;margin-top:2vh;padding:.6vh 1.8vh;border:1px solid rgba(127,166,255,.4);
 border-radius:999px;font-size:1.9vh;color:#9db8ff;letter-spacing:.15em}
/* S2 — modality triangle + 6 task arrows */
#s2 .wrap2{position:relative;width:100%;height:100%;display:grid;place-items:center}
#s2 svg{width:82%;height:82%}
#s2 .head{position:absolute;top:7%;width:100%;text-align:center;font-size:3.2vh;font-weight:700;
 color:#dfe6f5;opacity:0;transform:translateY(-12px);transition:all .6s ease}
#s2 .head.show{opacity:1;transform:none}
#s2 .head b{background:linear-gradient(90deg,#667eea,#9aa7ff);-webkit-background-clip:text;background-clip:text;color:transparent}
#s2 .sub2{position:absolute;bottom:7%;width:100%;text-align:center;font-size:1.9vh;color:#8b96ad;
 font-family:'JetBrains Mono',monospace;opacity:0;transition:opacity .6s ease .1s}
#s2 .sub2.show{opacity:1}
#s2 .ball{opacity:0;transform:scale(.2);transform-box:fill-box;transform-origin:center;
 transition:transform .55s cubic-bezier(.2,1.6,.35,1),opacity .4s}
#s2 .ball.in{opacity:1;transform:scale(1)}
#s2 .arr{stroke-dasharray:1;stroke-dashoffset:1;transition:stroke-dashoffset .6s ease}
#s2 .arr.draw{stroke-dashoffset:0}
#s2 .alab{opacity:0;transition:opacity .4s ease}
#s2 .alab.draw{opacity:1}
/* shared scene chrome (S3–S6) */
.scene .wrap2{position:relative;width:100%;height:100%;display:grid;place-items:center}
.scene .head{position:absolute;top:8%;width:100%;text-align:center;font-size:3.2vh;font-weight:700;
 color:#dfe6f5;opacity:0;transform:translateY(-12px);transition:all .6s ease}
.scene .head.show{opacity:1;transform:none}
.scene .head b{background:linear-gradient(90deg,#667eea,#9aa7ff);-webkit-background-clip:text;background-clip:text;color:transparent}
.scene .sub2{position:absolute;bottom:7.5%;width:100%;text-align:center;font-size:2vh;color:#8b96ad;
 font-family:'JetBrains Mono',monospace;opacity:0;transition:opacity .6s ease}
.scene .sub2.show{opacity:1}.scene .sub2 b{color:#cfd8ea}
/* S3 family bands */
.fams{display:flex;flex-direction:column;gap:1.6vh;width:62%}
.fam{display:flex;align-items:baseline;gap:1.4vw;padding:1.5vh 2.4vw;border-radius:12px;
 background:linear-gradient(90deg,color-mix(in srgb,var(--c) 26%,transparent),transparent);
 border-left:5px solid var(--c);opacity:0;transform:translateX(-40px);
 transition:opacity .5s ease,transform .55s cubic-bezier(.2,1,.3,1)}
.fam.in{opacity:1;transform:none}
.fam b{font-size:2.8vh;color:#fff;min-width:11vw}.fam i{font-size:1.9vh;color:#9fb0cb;font-style:normal}
/* S4 collapse bars */
.bars{display:flex;align-items:flex-end;gap:3.2vw;height:52vh}
.bar{position:relative;width:7vw;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%}
.bar .fl{width:100%;height:0;background:var(--c);border-radius:8px 8px 0 0;
 transition:height 1s cubic-bezier(.3,.7,.3,1)}
.bar.grow .fl{height:var(--h)}
.bar .v{font-size:2.6vh;font-weight:800;color:#fff;margin-bottom:.6vh;opacity:0;transition:opacity .4s ease .6s}
.bar.grow .v{opacity:1}
.bar em{margin-top:1vh;font-size:1.8vh;color:#aab6d0;font-style:normal}
.bar.dz.flash .fl{background:#ff4d63;box-shadow:0 0 26px rgba(255,77,99,.6)}
.bar.dz.flash .v{color:#ff8a98}
/* S5 seesaw + imbalance */
.seesaw{position:relative;width:46vw;height:24vh;margin-top:2vh}
.beam{position:absolute;top:42%;left:0;width:100%;height:2.4vh;border-radius:6px;
 background:linear-gradient(90deg,#5b8def,#2bc4a8);transform:rotate(0deg);
 transform-origin:50% 50%;transition:transform 1s cubic-bezier(.3,.8,.3,1);
 display:flex;justify-content:space-between;align-items:center}
.seesaw.tip .beam{transform:rotate(-11deg)}
.pan{transform:translateY(-3.2vh);font-size:2.1vh;font-weight:700;color:#fff;text-align:center}
.pan small{font-size:1.5vh;color:#cbd5e0;font-weight:500}
.piv{position:absolute;left:calc(50% - 1.4vh);top:42%;border-left:1.4vh solid transparent;
 border-right:1.4vh solid transparent;border-bottom:7vh solid #2a3550}
.imb{display:flex;flex-direction:column;gap:1.4vh;margin-top:3vh;width:46vw}
.ia{display:flex;align-items:center;gap:1.2vw;font-family:'JetBrains Mono',monospace;font-size:2vh;color:#cbd5e0}
.ia span{width:5vw}.ia .ib{height:2.4vh;width:0;background:linear-gradient(90deg,#667eea,#764ba2);
 border-radius:4px;transition:width .9s cubic-bezier(.3,.8,.3,1)}
.imb.go .ib{width:var(--w)}
/* S6 insight split */
.split6{display:flex;gap:3vw}
.opt{width:24vw;padding:3vh 2vw;border-radius:16px;text-align:center;border:1.5px solid;
 opacity:0;transform:translateY(20px);transition:all .6s ease}
.opt.in{opacity:1;transform:none}
.opt .ot{font-size:2.4vh;font-weight:800;color:#fff}
.opt .oc{font-size:1.8vh;color:#9fb0cb;margin:1.4vh 0}
.opt .om{font-size:2.4vh;font-weight:800}
.o-bad{border-color:rgba(255,90,110,.45);background:rgba(255,90,110,.07)}
.o-bad .om{color:#ff6e7e}
.o-good{border-color:rgba(56,211,159,.3);background:rgba(56,211,159,.05);transition:all .6s ease,background .6s ease,border-color .6s ease}
.o-good.lit{border-color:rgba(56,211,159,.75);background:rgba(56,211,159,.16);box-shadow:0 0 40px rgba(56,211,159,.22)}
.o-good .om{color:#38d39f}
.ctl{position:fixed;right:18px;bottom:14px;display:flex;gap:10px;z-index:9;font-family:'JetBrains Mono',monospace}
.ctl button{background:rgba(255,255,255,.06);color:#aab6d0;border:1px solid rgba(255,255,255,.12);
 padding:7px 13px;border-radius:8px;font-size:12px;cursor:pointer;backdrop-filter:blur(6px)}
.ctl button:hover{color:#fff;border-color:rgba(127,166,255,.5)}
</style></head><body>
<div id="wrap"><div id="stage">
  <section id="s1" class="scene">
    <div class="s1top">For <span class="gr">Omni-modality Language Models</span></div>
    <div class="q" id="q1">Which represents a dog?</div>
    <div class="row">
      <div class="card" id="cImg">
        <div class="media"><img src="data:image/jpeg;base64,__IMG__" alt="dog"></div>
        <div class="tag">model sees &nbsp;&rarr;</div>
        <div class="ans ok" id="aImg">&#128054; &nbsp;Dog &nbsp;&#10003;</div>
      </div>
      <div class="card" id="cAud">
        <div class="media"><div class="wave" id="wave"></div></div>
        <div class="tag">model hears &nbsp;&rarr;</div>
        <div class="ans bad" id="aAud">&ldquo;a person talking&rdquo; &nbsp;&#10007;</div>
      </div>
    </div>
    <div id="neq"><span>&#128054;</span><span class="ne">&ne;</span><span>&#128266;</span></div>
    <div class="line" id="ln1">A model that knows a dog <b>by sight</b> can&rsquo;t <b>hear</b> one.</div>
  </section>
  <section id="s2" class="scene">
    <div class="wrap2">
      <div class="head" id="s2h">XModBench probes <b>6 cross-modal directions</b></div>
      __S2SVG__
      <div class="sub2" id="s2s">Audio &middot; Vision (Image &cup; Video) &middot; Text &nbsp;—&nbsp; every ordered pair</div>
    </div>
  </section>
  <section id="s3" class="scene"><div class="wrap2">
    <div class="head" id="s3h">5 broad task families &middot; 17 subtasks &middot; <b>61,320</b> samples</div>
    <div class="fams">
      <div class="fam" style="--c:#5b8def"><b>Perception</b><i>what is it?</i></div>
      <div class="fam" style="--c:#f6a609"><b>Spatial</b><i>where / direction?</i></div>
      <div class="fam" style="--c:#ef5a6e"><b>Temporal</b><i>order &amp; counting</i></div>
      <div class="fam" style="--c:#2bc4a8"><b>Linguistic</b><i>speech &amp; translation</i></div>
      <div class="fam" style="--c:#8b5cf6"><b>Knowledge</b><i>music, movie, emotion</i></div>
    </div>
  </div></section>
  <section id="s4" class="scene"><div class="wrap2">
    <div class="head" id="s4h">But <b>spatial &amp; temporal reasoning collapses</b></div>
    <div class="bars" id="bars">
      <div class="bar" style="--c:#5b8def;--h:79.7%"><span class="v">79.7</span><div class="fl"></div><em>Perception</em></div>
      <div class="bar dz" style="--c:#f6a609;--h:35.2%"><span class="v">35.2</span><div class="fl"></div><em>Spatial</em></div>
      <div class="bar dz" style="--c:#ef5a6e;--h:41.4%"><span class="v">41.4</span><div class="fl"></div><em>Temporal</em></div>
      <div class="bar" style="--c:#2bc4a8;--h:82.5%"><span class="v">82.5</span><div class="fl"></div><em>Linguistic</em></div>
      <div class="bar" style="--c:#8b5cf6;--h:77.4%"><span class="v">77.4</span><div class="fl"></div><em>Knowledge</em></div>
    </div>
    <div class="sub2" id="s4s">spatial 35.2 / temporal 41.4 &nbsp;vs&nbsp; linguistic 82.5 &nbsp;&mdash;&nbsp; accuracy %, Qwen3-Omni on XModBench-Lite</div>
  </div></section>
  <section id="s5" class="scene"><div class="wrap2">
    <div class="head" id="s5h">The <b>same knowledge</b>, unequal across modalities</div>
    <div class="seesaw" id="seesaw">
      <div class="beam"><span class="pan pl">Audio<br><small>low</small></span><span class="pan pr">Text<br><small>high</small></span></div>
      <div class="piv"></div>
    </div>
    <div class="imb">
      <div class="ia"><span>A&rarr;T</span><div class="ib" style="--w:78%"></div></div>
      <div class="ia"><span>T&rarr;A</span><div class="ib" style="--w:46%"></div></div>
    </div>
    <div class="sub2" id="s5s">modality <b>disparity</b> &nbsp;&amp;&nbsp; directional <b>imbalance</b></div>
  </div></section>
  <section id="s7" class="scene">
    <div style="text-align:center">
      <div class="logo"><span class="x">XMod</span>Bench</div>
      <div class="sub">Cross-Modal Consistency</div>
      <div><span class="badge">ICLR 2026</span></div>
      <div class="url">xingruiwang.github.io/projects/XModBench</div>
    </div>
  </section>
</div></div>
<div class="ctl">
  <button id="snd">&#128264; sound: off</button>
  <button id="rep">&#8634; replay</button>
</div>
<audio id="bark" preload="auto" src="data:audio/wav;base64,__WAV__"></audio>
<script>
const $=s=>document.querySelector(s);
const wave=$('#wave');for(let i=0;i<28;i++){const b=document.createElement('i');
 b.style.animationDelay=(i*0.045)+'s';wave.appendChild(b);}
let sound=false;const bark=$('#bark');
$('#snd').onclick=()=>{sound=!sound;$('#snd').innerHTML=(sound?'&#128266;':'&#128264;')+' sound: '+(sound?'on':'off');};
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function run(){
  // reset
  for(const id of ['s1','s2','s3','s4','s5','s7']) $('#'+id).classList.remove('on');
  for(const id of ['cImg','cAud']) $('#'+id).classList.remove('in');
  for(const id of ['aImg','aAud']) $('#'+id).classList.remove('show');
  document.querySelectorAll('#s2 .ball').forEach(b=>b.classList.remove('in'));
  document.querySelectorAll('#s2 .arr,#s2 .alab').forEach(a=>a.classList.remove('draw'));
  document.querySelectorAll('.fam').forEach(f=>f.classList.remove('in'));
  document.querySelectorAll('.bar').forEach(b=>b.classList.remove('grow','flash'));
  $('#seesaw').classList.remove('tip');
  document.querySelector('.imb').classList.remove('go');
  for(const id of ['s2h','s2s','s3h','s4h','s4s','s5h','s5s'])
    {const el=$('#'+id); if(el) el.classList.remove('show');}
  $('#neq').classList.remove('slam');$('#ln1').classList.remove('show');
  $('#q1').style.opacity=0;wave.parentElement.parentElement.classList.remove('playing');
  await sleep(120);
  $('#s1').classList.add('on');
  await sleep(300);$('#q1').style.transition='opacity .5s';$('#q1').style.opacity=1;
  await sleep(700);$('#cImg').classList.add('in');
  await sleep(750);$('#aImg').classList.add('show');
  await sleep(700);$('#cAud').classList.add('in');
  wave.parentElement.parentElement.classList.add('playing');
  if(sound){try{bark.currentTime=0;bark.volume=.85;await bark.play();}catch(e){}}
  await sleep(1500);$('#aAud').classList.add('show');
  await sleep(800);
  $('#cImg').style.transition='opacity .5s';$('#cAud').style.transition='opacity .5s';
  $('#cImg').style.opacity=.12;$('#cAud').style.opacity=.12;$('#q1').style.opacity=0;
  $('#neq').classList.add('slam');
  await sleep(750);$('#ln1').classList.add('show');
  await sleep(2600);
  $('#s1').classList.remove('on');
  await sleep(620);
  // ---- S2: modality triangle + 6 task arrows ----
  $('#s2').classList.add('on');
  await sleep(300);$('#s2h').classList.add('show');
  const balls=[...document.querySelectorAll('#s2 .ball')];
  for(const b of balls){b.classList.add('in');await sleep(240);}
  await sleep(250);
  const arrs=[...document.querySelectorAll('#s2 .arr')];
  const labs=[...document.querySelectorAll('#s2 .alab')];
  for(let i=0;i<arrs.length;i++){arrs[i].classList.add('draw');labs[i].classList.add('draw');await sleep(360);}
  await sleep(300);$('#s2s').classList.add('show');
  await sleep(2400);
  $('#s2').classList.remove('on');
  await sleep(560);
  // ---- S3: 5 task families ----
  $('#s3').classList.add('on');
  await sleep(300);$('#s3h').classList.add('show');
  for(const f of document.querySelectorAll('.fam')){f.classList.add('in');await sleep(280);}
  await sleep(2200);
  $('#s3').classList.remove('on');
  await sleep(560);
  // ---- S4: spatial/temporal collapse ----
  $('#s4').classList.add('on');
  await sleep(300);$('#s4h').classList.add('show');
  await sleep(400);document.querySelectorAll('.bar').forEach(b=>b.classList.add('grow'));
  await sleep(1300);
  document.querySelectorAll('.bar.dz').forEach(b=>b.classList.add('flash'));
  await sleep(500);$('#s4s').classList.add('show');
  await sleep(2600);
  $('#s4').classList.remove('on');
  await sleep(560);
  // ---- S5: disparity + imbalance ----
  $('#s5').classList.add('on');
  await sleep(300);$('#s5h').classList.add('show');
  await sleep(500);$('#seesaw').classList.add('tip');
  await sleep(900);document.querySelector('.imb').classList.add('go');
  await sleep(900);$('#s5s').classList.add('show');
  await sleep(2400);
  $('#s5').classList.remove('on');
  await sleep(620);$('#s7').classList.add('on');
  await sleep(3000);
  $('#s7').classList.remove('on');
  await sleep(700);
  $('#cImg').style.opacity='';$('#cAud').style.opacity='';
  run();           // loop
}
$('#rep').onclick=()=>{location.reload();};
run();
</script></body></html>"""

import math

def _build_s2():
    R = 62
    nodes = {  # id: (cx, cy, label, glyph, color)
        "A": (500, 145, "Audio", "\U0001F50A", "#5b8def"),
        "V": (245, 432, "Vision", "\U0001F441", "#8b5cf6"),
        "T": (755, 432, "Text", "T", "#2bc4a8"),
    }
    # 6 ordered tasks; bow sign separates the two directions of a pair
    # both directions of a pair use bow=+1; the perpendicular already
    # flips with direction, so the two arrows curve to opposite sides.
    tasks = [("A", "V", +1, "A→V"), ("V", "A", +1, "V→A"),
             ("A", "T", +1, "A→T"), ("T", "A", +1, "T→A"),
             ("V", "T", +1, "V→T"), ("T", "V", +1, "T→V")]

    def pt(cx, cy, tx, ty, r):
        d = math.hypot(tx - cx, ty - cy)
        return cx + (tx - cx) / d * r, cy + (ty - cy) / d * r

    arrows, labels = [], []
    for i, (s, e, bow, lab) in enumerate(tasks):
        sx, sy, *_ = nodes[s]; ex, ey, *_ = nodes[e]
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        dx, dy = ex - sx, ey - sy
        L = math.hypot(dx, dy)
        px, py = -dy / L, dx / L            # perpendicular
        cxp, cyp = mx + px * bow * 95, my + py * bow * 95
        a0 = pt(sx, sy, cxp, cyp, R + 6)
        a1 = pt(ex, ey, cxp, cyp, R + 14)
        col = nodes[s][4]
        arrows.append(
            f'<path class="arr" pathLength="1" d="M{a0[0]:.1f},{a0[1]:.1f} '
            f'Q{cxp:.1f},{cyp:.1f} {a1[0]:.1f},{a1[1]:.1f}" fill="none" '
            f'stroke="{col}" stroke-width="4.5" marker-end="url(#ah-{i})" '
            f'stroke-linecap="round"/>'
            f'<marker id="ah-{i}" viewBox="0 0 10 10" refX="8" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{col}"/></marker>')
        lxx, lyy = mx + px * bow * 118, my + py * bow * 118
        labels.append(
            f'<text class="alab" x="{lxx:.0f}" y="{lyy:.0f}" fill="{col}" '
            f'font-size="20" font-weight="700" text-anchor="middle" '
            f'font-family="JetBrains Mono,monospace">{lab}</text>')

    balls = []
    for nid, (cx, cy, lab, gly, c) in nodes.items():
        balls.append(
            f'<g class="ball" data-n="{nid}">'
            f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="{c}" '
            f'fill-opacity="0.16" stroke="{c}" stroke-width="3"/>'
            f'<text x="{cx}" y="{cy - 4}" text-anchor="middle" font-size="34">{gly}</text>'
            f'<text x="{cx}" y="{cy + 30}" text-anchor="middle" fill="#e8edf6" '
            f'font-size="20" font-weight="700" font-family="Inter,sans-serif">{lab}</text></g>')

    return ('<svg viewBox="0 0 1000 560">'
            + "".join(arrows) + "".join(labels) + "".join(balls) + "</svg>")


OUT.write_text(HTML.replace("__IMG__", IMG).replace("__WAV__", WAV)
                .replace("__S2SVG__", _build_s2()))
print(f"wrote {OUT}  ({OUT.stat().st_size//1024} KB, self-contained)")
