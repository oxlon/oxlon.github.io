// Interactive macro-fiscal simulator — recomputes client-side from estimated coefficients.
(async function(){
  const D = await window.AZ.data(); const S = D.sim, SR = D.series;
  const P = window.AZ.palette;
  const fY = SR.year.filter(y=>y>=2025);
  const baseGDP = SR.year.map((y,i)=>({y,g:SR.gdp_nom[i]})).filter(o=>o.y>=2025);
  const els = id=>document.getElementById(id);
  const get = id=>parseFloat(els(id).value);

  function compute(){
    const oil=get("oil"), vat=get("vat"), fx=get("fx"), gov=get("gov");
    els("oilv").textContent="$"+oil; els("vatv").textContent=vat+"%";
    els("fxv").textContent=fx+"%"; els("govv").textContent=(gov>0?"+":"")+gov+"%";
    // --- channels (first-order, documented) ---
    const oilGDP = (Math.pow(oil/S.base_oil, S.e_oilgdp)-1)*S.oil_share_2030*100; // %GDP via oil
    const vatDrag = -0.10*(vat-S.vat_base);            // demand drag: -0.1%GDP per +1pp VAT
    const govPush =  0.45*gov*(1-S.oil_share_2030);    // spending multiplier on non-oil GDP
    const gdpDev = oilGDP + vatDrag + govPush;
    const inflFX = fx*S.fx_passthrough;                // FX pass-through to CPI (estimated)
    const inflVAT = 0.35*(vat-S.vat_base);             // ~0.35pp CPI per +1pp VAT (consumption weight)
    const inflDev = inflFX + inflVAT;
    const oilFisc = (Math.max(oil-25,0)/Math.max(S.base_oil-25,0)-1)*100; // oil take vs base
    const vatRev = (vat/S.vat_base-1)*S.vat_rev_share_gdp;                // %GDP revenue
    const fiscBal = oilFisc*S.oil_share_2030*0.6 + vatRev - gov*0.30;     // %GDP balance change (stylised)
    return {gdpDev,inflDev,fiscBal,oil};
  }
  function fmt(x,s=1){return (x>0?"+":"")+x.toFixed(s);}
  function paint(){
    const r=compute();
    els("s_gdp").textContent=fmt(r.gdpDev)+"%"; els("s_gdp").style.color=r.gdpDev<0?P.bad:P.good;
    els("s_infl").textContent=fmt(r.inflDev)+" pp"; els("s_infl").style.color=r.inflDev>0?P.bad:P.good;
    els("s_fisc").textContent=fmt(r.fiscBal)+"% GDP"; els("s_fisc").style.color=r.fiscBal<0?P.bad:P.good;
    const scen=baseGDP.map(o=>o.g*(1+r.gdpDev/100));
    Plotly.react("simPlot",[
      {x:fY,y:baseGDP.map(o=>o.g),name:"Base forecast",mode:"lines+markers",line:{color:P.muted,dash:"dot"}},
      {x:fY,y:scen,name:"Scenario",mode:"lines+markers",line:{color:P.accent,width:3}}
    ],window.AZ.layout({yaxis:{title:"Nominal GDP (mln AZN)",gridcolor:"#eee"}}),{displayModeBar:false,responsive:true});
    Plotly.react("simBars",[{
      type:"bar",orientation:"h",
      y:["GDP level","Inflation","Fiscal balance"],x:[r.gdpDev,r.inflDev,r.fiscBal],
      marker:{color:[r.gdpDev<0?P.bad:P.good,r.inflDev>0?P.bad:P.good,r.fiscBal<0?P.bad:P.good]},
      text:[fmt(r.gdpDev)+"%",fmt(r.inflDev)+"pp",fmt(r.fiscBal)+"%"],textposition:"auto"
    }],window.AZ.layout({margin:{l:100,r:20,t:10,b:30},height:200,xaxis:{zeroline:true,zerolinecolor:"#999"}}),{displayModeBar:false,responsive:true});
  }
  ["oil","vat","fx","gov"].forEach(id=>els(id).addEventListener("input",paint));
  const rb=els("reset"); if(rb) rb.addEventListener("click",()=>{
    els("oil").value=S.base_oil; els("vat").value=S.vat_base; els("fx").value=0; els("gov").value=0; paint();});
  paint();
})();
