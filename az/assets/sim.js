// Multi-variable, multi-year macro-fiscal scenario simulator (first-order, documented).
(async function(){
  const D=await window.AZ.data(); if(!D.sim2) return;
  const B=D.sim2.base, C=D.sim2.coef, P=window.AZ.palette;
  const baseOil=D.sim2.base_oil, vatBase=D.sim2.vat_base, yrs=B.year;
  const el=id=>document.getElementById(id), v=id=>parseFloat(el(id).value);
  const LEV=[["oil","oilv",x=>"$"+x],["oilprod","oilprodv",x=>(x>0?"+":"")+x+"%"],
    ["fx","fxv",x=>x+"%"],["vat","vatv",x=>x+"%"],["gov","govv",x=>(x>0?"+":"")+x+"%"],
    ["rate","ratev",x=>(x>0?"+":"")+x+" pp"],["glob","globv",x=>(x>0?"+":"")+x+"%"]];

  function compute(){
    const oil=v("oil"),oilprod=v("oilprod"),fx=v("fx"),vat=v("vat"),gov=v("gov"),rate=v("rate"),glob=v("glob");
    LEV.forEach(([id,lab,f])=>el(lab).textContent=f(id==="oil"?oil:id==="oilprod"?oilprod:id==="fx"?fx:id==="vat"?vat:id==="gov"?gov:id==="rate"?rate:glob));
    const oilDev=(Math.pow(oil/baseOil,C.e_oilgdp)*(1+oilprod/100)-1)*100;            // oil VA, %
    const nonoilDev=C.gov_mult*gov+C.rate_demand*rate+C.global_exports*glob+C.vat_demand*(vat-vatBase); // non-oil GDP, %
    const inflDev=C.fx_passthrough*fx+C.vat_inflation*(vat-vatBase)+C.rate_inflation*rate;             // pp
    const balDev=(oilDev/100)*C.oil_rev_share+C.vat_rev_coef*(vat-vatBase)+C.gov_bal_coef*gov;          // %GDP
    const cabDev=(oilDev/100)*C.oil_export_share+0.05*fx;                                               // %GDP
    const gdpScn=[],inflScn=[],balScn=[],debtScn=[],gdpDev=[]; let dcum=0;
    for(let i=0;i<yrs.length;i++){
      const gd=B.oil_share[i]*oilDev+(1-B.oil_share[i])*nonoilDev; gdpDev.push(gd);
      gdpScn.push(B.gdp_nom[i]*(1+gd/100));
      inflScn.push(B.inflation[i]+inflDev);
      balScn.push(B.fiscal_bal[i]+balDev);
      dcum+=-balDev; debtScn.push(B.debt[i]+dcum);
    }
    return {oilDev,nonoilDev,inflDev,balDev,cabDev,gdpDev,gdpScn,inflScn,balScn,debtScn};
  }
  const sgn=(x,d=1)=>(x>0?"+":"")+x.toFixed(d);
  function path(div,base,scn,yt){
    Plotly.react(div,[
      {x:yrs,y:base,name:"Baseline",mode:"lines+markers",line:{color:P.muted,dash:"dot",width:2},marker:{size:5,symbol:"circle"}},
      {x:yrs,y:scn,name:"Scenario",mode:"lines+markers",line:{color:"#b03a2e",width:2.6},marker:{size:6,symbol:"diamond"}}
    ],window.AZ.layout({margin:{l:52,r:10,t:8,b:30},yaxis:{title:yt},legend:{orientation:"h",y:-0.22,font:{size:10}}}),window.AZ.cfg);
  }
  function paint(){
    const r=compute(), L=yrs.length-1;
    el("s_gdp").textContent=sgn(r.gdpDev[L])+"%"; el("s_gdp").style.color=r.gdpDev[L]<0?P.bad:P.good;
    el("s_infl").textContent=r.inflScn[L].toFixed(1)+"%"; el("s_infl").style.color=r.inflDev>0?P.bad:(r.inflDev<0?P.good:P.navy);
    el("s_bal").textContent=sgn(r.balScn[L])+"%"; el("s_bal").style.color=r.balScn[L]<0?P.bad:P.good;
    el("s_debt").textContent=r.debtScn[L].toFixed(0)+"%"; el("s_debt").style.color=r.debtScn[L]>B.debt[L]+0.5?P.bad:P.navy;
    el("s_cab").textContent=sgn(B.cab[L]+r.cabDev)+"%"; el("s_cab").style.color=(B.cab[L]+r.cabDev)<0?P.bad:P.good;
    path("simGdp",B.gdp_nom,r.gdpScn,"Nominal GDP (AZN mn)");
    path("simInfl",B.inflation,r.inflScn,"Inflation (%)");
    path("simBal",B.fiscal_bal,r.balScn,"Fiscal balance (% GDP)");
    path("simDebt",B.debt,r.debtScn,"Govt debt (% GDP)");
  }
  function set(o){const d={oil:baseOil,oilprod:0,fx:0,vat:vatBase,gov:0,rate:0,glob:0,...o};
    Object.entries(d).forEach(([k,val])=>{if(el(k))el(k).value=val;}); paint();}
  LEV.forEach(([id])=>el(id).addEventListener("input",paint));
  const presets={reset:{},p_oil50:{oil:50},p_deval:{oil:45,fx:30},
    p_recession:{oil:45,glob:-4,gov:-3},p_consol:{gov:-10,vat:20,rate:1}};
  Object.entries(presets).forEach(([id,o])=>{const b=el(id); if(b)b.addEventListener("click",()=>set(o));});
  paint();
})();
