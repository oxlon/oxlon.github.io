// shared helpers: KaTeX auto-render, mobile nav, Plotly theming, data loader
window.AZ = {
  palette:{navy:"#1a2038",navy2:"#2a3650",accent:"#1d7a8c",gold:"#b9852a",bad:"#b13f2e",good:"#2f7d54",muted:"#525b7a"},
  layout(extra={}){
    return Object.assign({
      font:{family:"-apple-system,Segoe UI,Inter,system-ui,sans-serif",size:12,color:"#17212e"},
      margin:{l:54,r:18,t:30,b:42}, paper_bgcolor:"#fff", plot_bgcolor:"#fff",
      xaxis:{gridcolor:"#eee",zeroline:false}, yaxis:{gridcolor:"#eee",zeroline:false},
      legend:{orientation:"h",y:-0.18,font:{size:11}}, hovermode:"x unified"
    }, extra);
  },
  cfg:{responsive:true,displayModeBar:false},
  data(){ return Promise.resolve(window.__ANALYTICS__||{}); },  // embedded; works from file://
  // Bank-of-England-style fan chart: nested probability bands in one colour tone.
  fan(div,F,opts){
    opts=opts||{}; const P=this.palette;
    const fy=F.fc.map(d=>d.year);
    const RED="#b03a2e", RF=(a)=>`rgba(176,58,46,${a})`;     // reddish, Bank-of-England style
    const band=(hi,lo,a,nm)=>({x:fy.concat([...fy].reverse()),
      y:F.fc.map(d=>d[hi]).concat([...F.fc].reverse().map(d=>d[lo])),
      fill:"toself",fillcolor:RF(a),line:{color:"transparent"},hoverinfo:"skip",name:nm});
    const t=[band("hi80","lo80",0.13,"80% interval"),band("hi50","lo50",0.26,"50% interval"),
      {x:F.hist.map(d=>d.year),y:F.hist.map(d=>d.val),mode:"lines+markers",
       line:{color:P.navy,width:2.5},marker:{size:5,symbol:"circle"},name:"Outturn"},
      {x:fy,y:F.fc.map(d=>d.central),mode:"lines",line:{color:RED,width:2.6},name:"Baseline forecast"}];
    if(F.weo&&F.weo.length) t.push({x:F.weo.map(d=>d.year),y:F.weo.map(d=>d.val),
      mode:"lines+markers",line:{color:P.gold,width:2,dash:"dash"},marker:{symbol:"diamond",size:6},name:"IMF WEO"});
    const bx=fy[0];   // jump-off year: rule, bands and central forecast all begin here
    Plotly.newPlot(div,t,this.layout({margin:{l:54,r:16,t:26,b:54},yaxis:{title:opts.ytitle||""},
      shapes:[{type:"line",x0:bx,x1:bx,y0:0,y1:1,yref:"paper",line:{color:"#9aa3ad",dash:"dot"}}],
      annotations:[{x:bx,y:1.06,yref:"paper",xanchor:"right",showarrow:false,text:"outturn  ",font:{size:10,color:"#8a93a0"}},
        {x:bx,y:1.06,yref:"paper",xanchor:"left",showarrow:false,text:"  forecast",font:{size:10,color:"#8a93a0"}}]}),this.cfg);
  },
  // generic forecast line chart: outturn (navy) bridged to one or more forecast lines
  fc(div,hist,lines,opts){
    opts=opts||{}; const P=this.palette;
    const hx=hist.map(d=>d.x), hy=hist.map(d=>d.y);
    const last=hx.length?hx[hx.length-1]:null, lastv=hy.length?hy[hy.length-1]:null;
    const tr=[{x:hx,y:hy,mode:"lines+markers",name:opts.histName||"Outturn",line:{color:P.navy,width:2.4},marker:{size:5,symbol:"circle"}}];
    lines.forEach(L=>{const br=(L.bridge!==false&&last!=null);
      tr.push({x:(br?[last]:[]).concat(L.x),y:(br?[lastv]:[]).concat(L.y),mode:"lines+markers",name:L.name,
        line:{color:L.color||P.accent,width:L.width||2.3,dash:L.dash||"solid"},marker:{size:5,symbol:L.symbol||"diamond"}});});
    Plotly.newPlot(div,tr,this.layout(Object.assign({margin:{l:60,r:14,t:10,b:54},yaxis:{title:opts.ytitle||""},
      legend:{orientation:"h",y:-0.2,font:{size:10}}},opts.layout||{})),this.cfg);
  }
};
document.addEventListener("DOMContentLoaded",()=>{
  const mb=document.querySelector(".menu-btn"), nav=document.querySelector(".nav");
  if(mb && nav) mb.addEventListener("click",()=>{
    const open=nav.classList.toggle("open");
    mb.setAttribute("aria-expanded", String(open));
  });

  const currentFile=(window.location.pathname.split("/").pop()||"index.html").replace(/\.html$/,"")||"index";
  const active=document.querySelector(`.nav a[data-slug="${currentFile}"]`);
  if(active){
    document.querySelectorAll(".nav a.active").forEach(a=>a.classList.remove("active"));
    active.classList.add("active");
    active.setAttribute("aria-current","page");
    active.scrollIntoView({block:"nearest"});
  }

  const topbar=document.querySelector(".topbar");
  if(topbar && !topbar.querySelector(".topbar-actions")){
    const actions=document.createElement("div");
    actions.className="topbar-actions";
    const print=document.createElement("button");
    print.type="button";
    print.className="report-action";
    print.textContent="Print";
    print.addEventListener("click",()=>window.print());
    actions.appendChild(print);
    topbar.appendChild(actions);
  }

  document.querySelectorAll('a[href^="http"]').forEach(a=>{
    if(a.hostname && a.hostname!==window.location.hostname){
      a.target="_blank";
      a.rel="noopener";
    }
  });

  const pagerPrev=document.querySelector(".pager a:not(.next)");
  const pagerNext=document.querySelector(".pager a.next");
  window.addEventListener("keydown",(e)=>{
    if(e.defaultPrevented || /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;
    if(e.key==="ArrowLeft" && pagerPrev) window.location.href=pagerPrev.href;
    if(e.key==="ArrowRight" && pagerNext) window.location.href=pagerNext.href;
  });

  let resizeTimer=0;
  window.addEventListener("resize",()=>{
    if(!window.Plotly) return;
    clearTimeout(resizeTimer);
    resizeTimer=setTimeout(()=>{
      document.querySelectorAll(".js-plotly-plot").forEach(el=>Plotly.Plots.resize(el));
    },120);
  });

  if(window.renderMathInElement){
    renderMathInElement(document.body,{delimiters:[
      {left:"$$",right:"$$",display:true},{left:"\\(",right:"\\)",display:false},
      {left:"$",right:"$",display:false}],throwOnError:false});
  }
});
