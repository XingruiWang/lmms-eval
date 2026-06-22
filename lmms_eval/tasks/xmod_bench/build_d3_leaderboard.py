"""Patch the website leaderboard into one interactive D3 widget:
 - prominent segmented title toggle: By configuration | By task family
 - single sortable table; small grey Full/Lite toggle at its top-right
 - 3 D3 charts (radar / modality-disparity dropping bars / imbalance scatter)
All driven by one {split, view} state. Data inlined from xmod_scores.json.
"""
import json
import pathlib

IDX = pathlib.Path("/scratch/xwang378/2025/xingruiwang.github.io/projects/XModBench/index.html")
DATA = json.load(open("/scratch/xwang378/2025/lmms-eval/lmms_eval/tasks/xmod_bench/xmod_scores.json"))
DATA_MIN = json.dumps(DATA, separators=(",", ":"))

html = IDX.read_text()
start = html.index('      <div class="content">\n        <h3 class="section-subtitle">Full Benchmark')
end = html.index("  </section>", start)

WIDGET = r'''      <div class="content">
        <p>One interactive view of the full benchmark and the lite split. Switch the
        breakdown in the title; toggle Full / Lite at the table's top-right; click any
        column header to sort. The three charts update with the table.</p>

        <div class="lbx">
          <div class="lbx-seg" role="tablist">
            <button id="vCfg" class="on">By configuration</button>
            <button id="vFam">By task family</button>
          </div>

          <div class="lbx-card">
            <div class="lbx-split"><span id="sFull" class="on">Full</span><span class="sep">·</span><span id="sLite">Lite</span></div>
            <div class="tab-wrap"><table class="lb-table" id="lbT"><thead></thead><tbody></tbody></table></div>
            <p class="lb-note" id="lbNote"></p>
          </div>

          <div class="lbx-charts">
            <div class="lbx-chart"><h4>Task Competence (by family)</h4><div id="cRadar"></div></div>
            <div class="lbx-chart"><h4>Modality Disparity (bars drop = worse on audio)</h4><div id="cDisp"></div></div>
            <div class="lbx-chart"><h4>Directional Imbalance</h4><div id="cImb"></div></div>
          </div>
        </div>
      </div>
    </div>
'''

STYLE = r'''
    /* interactive leaderboard widget */
    .lbx-seg{display:inline-flex;border:1px solid #cbd5e0;border-radius:10px;overflow:hidden;margin:6px 0 16px}
    .lbx-seg button{font:600 15px/1 'Inter',sans-serif;padding:11px 22px;background:#fff;color:#4a5568;border:0;cursor:pointer}
    .lbx-seg button.on{background:linear-gradient(90deg,#667eea,#764ba2);color:#fff}
    .lbx-card{position:relative;border:1px solid #e2e8f0;border-radius:12px;padding:14px 16px 6px;background:#fff}
    .lbx-split{position:absolute;top:10px;right:16px;font:500 12px 'JetBrains Mono',monospace;color:#a0aec0}
    .lbx-split span{cursor:pointer}.lbx-split span.on{color:#2b6cb0;font-weight:700}
    .lbx-split .sep{margin:0 6px;cursor:default;color:#cbd5e0}
    .lb-table th{cursor:pointer;user-select:none}.lb-table th:first-child{cursor:default}
    .lb-table th .ar{color:#90cdf4;font-size:11px}
    .lbx-charts{display:grid;grid-template-columns:1fr;gap:26px;margin-top:26px}
    @media(min-width:980px){.lbx-charts{grid-template-columns:1fr 1fr}.lbx-chart:first-child{grid-column:1/-1}}
    .lbx-chart h4{font:700 15px 'Inter',sans-serif;color:#2d3748;margin:0 0 6px}
    .lbx-chart svg{max-width:100%;height:auto;font-family:'Inter',sans-serif}
    .lbx-tip{position:fixed;pointer-events:none;background:#1a202c;color:#fff;font:500 12px 'Inter';padding:6px 9px;border-radius:6px;opacity:0;transition:opacity .12s;z-index:99}
'''

SCRIPT = r'''
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<script>
(function(){
  const DATA = __DATA__;
  const CFG=["a2t","a2v","t2a","t2v","v2a","v2t"];
  const CFGL={a2t:"A→T",a2v:"A→V",t2a:"T→A",t2v:"T→V",v2a:"V→A",v2t:"V→T"};
  const FAM=["perception","spatial","temporal","linguistic","knowledge"];
  const FAML={perception:"Perception",spatial:"Spatial",temporal:"Temporal",linguistic:"Linguistic",knowledge:"Knowledge"};
  const st={split:"full",view:"config",sortKey:"avg",asc:false};
  const tip=d3.select("body").append("div").attr("class","lbx-tip");
  const col=d3.scaleOrdinal(d3.schemeTableau10.concat(d3.schemeSet3));

  function rows(){
    const d=DATA[st.split]; const keys=st.view==="config"?CFG:FAM;
    return Object.keys(d).map(m=>{
      const o={model:m, _cfg:d[m].config};
      keys.forEach(k=> o[k]= st.view==="config"? d[m].config[k] : d[m].family[k]);
      o.avg = st.view==="config"? d[m].config_avg : d[m].family_avg;
      return o;
    });
  }
  function table(){
    const keys=st.view==="config"?CFG:FAM, lab=st.view==="config"?CFGL:FAML;
    const data=rows().sort((a,b)=>{const x=a[st.sortKey],y=b[st.sortKey];
      if(typeof x==="string")return st.asc?d3.ascending(x,y):d3.descending(x,y);
      return st.asc?x-y:y-x;});
    const best={}; keys.concat("avg").forEach(k=>best[k]=d3.max(data,r=>r[k]));
    const T=d3.select("#lbT");
    const head=[["model","Model"]].concat(keys.map(k=>[k,lab[k]])).concat([["avg","Avg."]]);
    T.select("thead").html("<tr>"+head.map(([k,l])=>{
      const ar=st.sortKey===k?(st.asc?" ▲":" ▼"):"";
      return `<th data-k="${k}">${l}<span class="ar">${ar}</span></th>`;}).join("")+"</tr>");
    T.select("tbody").html(data.map(r=>"<tr><td>"+r.model+"</td>"+
      keys.concat("avg").map(k=>{const v=r[k];
        const b=(v===best[k]&&k!=="model")?' class="best"':"";
        return `<td${b}>${v==null?"—":v.toFixed(1)}</td>`;}).join("")+"</tr>").join(""));
    T.selectAll("th").on("click",function(){const k=this.dataset.k;
      if(st.sortKey===k)st.asc=!st.asc; else {st.sortKey=k;st.asc=(k==="model");}
      table();});
    d3.select("#lbNote").html(st.split==="full"
      ? "Full benchmark (61,320 samples), paper numbers — 12 models (vision-only & Gemini 2.0 Flash omitted)."
      : "XModBench-Lite (6,000) — reproduced via the lmms-eval port + author Lite logs.");
  }
  // ---- radar (family) ----
  function radar(){
    const box=d3.select("#cRadar").html(""), W=560,H=420,R=150,cx=W/2,cy=H/2+8;
    const svg=box.append("svg").attr("viewBox",`0 0 ${W} ${H}`);
    const d=DATA[st.split], ms=Object.keys(d);
    const ang=i=>-Math.PI/2+i*2*Math.PI/FAM.length;
    [20,40,60,80,100].forEach(v=>{svg.append("circle").attr("cx",cx).attr("cy",cy)
      .attr("r",R*v/100).attr("fill","none").attr("stroke","#e2e8f0");});
    FAM.forEach((f,i)=>{const x=cx+Math.cos(ang(i))*R,y=cy+Math.sin(ang(i))*R;
      svg.append("line").attr("x1",cx).attr("y1",cy).attr("x2",x).attr("y2",y).attr("stroke","#e2e8f0");
      svg.append("text").attr("x",cx+Math.cos(ang(i))*(R+22)).attr("y",cy+Math.sin(ang(i))*(R+22))
        .attr("text-anchor","middle").attr("dy",".35em").attr("font-size",12).attr("font-weight",700)
        .attr("fill","#4a5568").text(FAML[f]);});
    ms.forEach((m,k)=>{const pts=FAM.map((f,i)=>{const r=R*d[m].family[f]/100;
      return [cx+Math.cos(ang(i))*r,cy+Math.sin(ang(i))*r];});
      svg.append("path").attr("d",d3.line()(pts)+"Z").attr("fill",col(m)).attr("fill-opacity",.04)
        .attr("stroke",col(m)).attr("stroke-width",1.8)
        .on("mousemove",e=>tip.style("opacity",1).style("left",(e.clientX+12)+"px").style("top",(e.clientY-10)+"px")
          .html(m+"<br>"+FAM.map(f=>FAML[f]+": "+d[m].family[f]).join("<br>")))
        .on("mouseleave",()=>tip.style("opacity",0));});
    const lg=svg.append("g").attr("transform",`translate(${W-4},14)`);
    ms.forEach((m,i)=>{const g=lg.append("g").attr("transform",`translate(0,${i*15})`);
      g.append("rect").attr("x",-9).attr("width",9).attr("height",9).attr("fill",col(m));
      g.append("text").attr("x",-13).attr("y",8).attr("text-anchor","end").attr("font-size",10).text(m);});
  }
  // ---- disparity dropping bars ----
  function disp(){
    const box=d3.select("#cDisp").html(""), d=DATA[st.split], ms=Object.keys(d);
    const P=[["Audio vs Text",c=>(c.a2v+c.v2a)/2-(c.t2v+c.v2t)/2],
             ["Visual vs Text",c=>(c.v2a+c.a2v)/2-(c.t2a+c.a2t)/2],
             ["Audio vs Vision",c=>(c.a2t+c.t2a)/2-(c.v2t+c.t2v)/2]];
    const all=[].concat(...P.map(([,f])=>ms.map(m=>f(d[m].config))));
    const ymin=Math.min(...all)*1.15, W=560,H=300,pad=46,pw=(W-2*pad)/3;
    const svg=d3.select("#cDisp").append("svg").attr("viewBox",`0 0 ${W} ${H}`);
    P.forEach(([t,f],pi)=>{const x0=pad+pi*pw;
      const data=ms.map(m=>[m,f(d[m].config)]).sort((a,b)=>b[1]-a[1]);
      const y=d3.scaleLinear().domain([ymin,Math.max(2,d3.max(all))]).range([H-46,24]);
      const xb=d3.scaleBand().domain(data.map(r=>r[0])).range([x0+8,x0+pw-8]).padding(.28);
      svg.append("text").attr("x",x0+pw/2).attr("y",16).attr("text-anchor","middle")
        .attr("font-size",11).attr("font-weight",700).attr("fill","#2d3748").text(t);
      svg.append("line").attr("x1",x0+4).attr("x2",x0+pw-4).attr("y1",y(0)).attr("y2",y(0)).attr("stroke","#222");
      data.forEach(([m,v])=>{svg.append("rect").attr("x",xb(m)).attr("width",xb.bandwidth())
        .attr("y",Math.min(y(0),y(v))).attr("height",Math.abs(y(v)-y(0))).attr("fill",col(m))
        .on("mousemove",e=>tip.style("opacity",1).style("left",(e.clientX+12)+"px").style("top",(e.clientY-10)+"px").html(m+"<br>"+t+": "+v.toFixed(1)))
        .on("mouseleave",()=>tip.style("opacity",0));});});
    svg.append("text").attr("x",6).attr("y",H-6).attr("font-size",10).attr("fill","#718096")
      .text("↓ below 0 = systematically worse on audio");
  }
  // ---- imbalance scatter ----
  function imb(){
    const box=d3.select("#cImb").html(""), d=DATA[st.split], ms=Object.keys(d);
    const P=[["A–T","a2t","t2a"],["A–V","a2v","v2a"],["V–T","v2t","t2v"]];
    const W=560,H=300,pad=44,pw=(W-2*pad)/3;
    const svg=d3.select("#cImb").append("svg").attr("viewBox",`0 0 ${W} ${H}`);
    P.forEach(([t,i,j],pi)=>{const x0=pad+pi*pw;
      const pts=ms.map(m=>{const c=d[m].config;return [m,(c[i]+c[j])/2,Math.abs(c[i]-c[j])];});
      const x=d3.scaleLinear().domain(d3.extent(pts,p=>p[1])).nice().range([x0+10,x0+pw-12]);
      const y=d3.scaleLinear().domain([0,d3.max(pts,p=>p[2])*1.15||1]).range([H-40,26]);
      svg.append("text").attr("x",x0+pw/2).attr("y",16).attr("text-anchor","middle")
        .attr("font-size",11).attr("font-weight",700).attr("fill","#2d3748").text(t);
      svg.append("line").attr("x1",x0+6).attr("x2",x0+pw-6).attr("y1",H-38).attr("y2",H-38).attr("stroke","#cbd5e0");
      pts.forEach(([m,a,b])=>svg.append("circle").attr("cx",x(a)).attr("cy",y(b)).attr("r",6)
        .attr("fill",col(m)).attr("stroke","#fff").attr("stroke-width",1.2)
        .on("mousemove",e=>tip.style("opacity",1).style("left",(e.clientX+12)+"px").style("top",(e.clientY-10)+"px")
          .html(m+"<br>"+t+" competence "+a.toFixed(1)+"<br>imbalance "+b.toFixed(1)))
        .on("mouseleave",()=>tip.style("opacity",0)));});
    svg.append("text").attr("x",6).attr("y",H-6).attr("font-size",10).attr("fill","#718096")
      .text("x = pair competence   ·   y = |direction gap|");
  }
  function render(){table();radar();disp();imb();}
  function seg(v){st.view=v;st.sortKey=(v==="config"?"avg":"avg");
    d3.select("#vCfg").classed("on",v==="config");d3.select("#vFam").classed("on",v==="family");render();}
  function spl(s){st.split=s;d3.select("#sFull").classed("on",s==="full");
    d3.select("#sLite").classed("on",s==="lite");render();}
  d3.select("#vCfg").on("click",()=>seg("config"));
  d3.select("#vFam").on("click",()=>seg("family"));
  d3.select("#sFull").on("click",()=>spl("full"));
  d3.select("#sLite").on("click",()=>spl("lite"));
  render();
})();
</script>
'''

new = WIDGET
patched = html[:start] + new + html[end:]
# inject style before </style> of the first style block, script before </body>
patched = patched.replace("\n    /* interactive leaderboard widget */", "", 0)
patched = patched.replace("</style>", STYLE + "\n</style>", 1)
patched = patched.replace("</body>", SCRIPT.replace("__DATA__", DATA_MIN) + "\n</body>", 1)
IDX.write_text(patched)
print("patched", IDX, "| widget bytes", len(new), "| data bytes", len(DATA_MIN))
