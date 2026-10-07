// live.mjs — end-to-end check of the live features against a running PolicyUnit API (http://127.0.0.1:8792/panel/):
// builder «Yoxla» + «Hesabla» of a copied scenario, KPI «Serverdə müqayisə et»; reports JS errors.
import { launch, newPage, sleep } from './cdp.mjs';
const BASE = process.env.POLICY_URL || 'http://127.0.0.1:8792/panel/';
const b = await launch(9345);
let bad = 0;
async function wait(p, expr, n = 120) { for (let i = 0; i < n; i++) { if (await p.ev(expr).catch(() => false)) return true; await sleep(500); } return false; }
try {
  const p = await newPage(b, { width: 1440, height: 900 });
  // 1) new scenario only via lists / dropdowns → «Hesabla (saxlamadan)»
  await p.goto(BASE + '?notour#/qurucu', 3500);
  await wait(p, "!!document.querySelector('#b-pick')");
  await p.ev("U.bReset(); U.route(true); 1"); await sleep(800);
  await p.ev("(function(){var s=document.querySelector('#b-pick'); s.value='vat_rate'; s.dispatchEvent(new Event('change',{bubbles:true})); document.querySelector('#b-addp').click(); return 1;})()");
  await sleep(500);
  const idv = await p.ev("document.querySelector('#b-idv').textContent");
  await p.click('#b-run');
  let ok = await wait(p, "!!document.querySelector('[data-dt=b-hw]') || /alınmadı/.test(document.querySelector('#b-val').innerText)", 240);
  let hw = await p.ev("!!document.querySelector('[data-dt=b-hw]')");
  console.log((ok && hw ? 'ok  ' : 'XƏTA') + ' siyahıdan qurulmuş ssenari, saxlamadan hesablama (kod ' + idv + ')'); if (!(ok && hw)) bad++;
  await p.shot('live_qurucu_yeni', true);
  // 2) existing scenario in one click
  await p.goto(BASE + '?notour#/qurucu', 3500);
  await wait(p, "!!document.querySelector('[data-srv=run][data-src=rəsmi]')");
  await p.ev("U.BLD.res = null; 1");
  await p.click('[data-srv=run][data-src=rəsmi]');
  ok = await wait(p, "!!document.querySelector('[data-dt=b-hw]') || /alınmadı/.test(document.querySelector('#b-val').innerText)", 240);
  hw = await p.ev("!!document.querySelector('[data-dt=b-hw]')");
  console.log((ok && hw ? 'ok  ' : 'XƏTA') + ' mövcud ssenari bir kliklə'); if (!(ok && hw)) bad++;
  await p.shot('live_qurucu_movcud', true);
  const steps = [['kpi', '#k-srv', "!!document.querySelector('[data-dt=k-srvr]') || !!document.querySelector('#k-srvres .offline')", 'KPI müqayisəsi']];
  for (const [r, btn, done, nm] of steps) {
    await p.goto(BASE + '?notour#/' + r, 3500);
    await wait(p, `!!document.querySelector('${btn}')`);
    await p.click(btn);
    const ok = await wait(p, done, 240);
    const errs = p.logs.filter(l => l.t === 'EXC' || l.t === 'error');
    const off = await p.ev("!!document.querySelector('.offline')");
    console.log((ok && !errs.length ? 'ok  ' : 'XƏTA') + ' ' + nm + (off ? ' (oflayn / xəta mesajı göstərildi)' : '') + (errs.length ? ' ' + errs.map(e => e.a).join(' | ').slice(0, 400) : ''));
    if (!ok || errs.length) bad++;
    await p.shot('live_' + nm.replace(/\s/g, '_'), true);
    p.logs.length = 0;
  }
} finally { b.close(); }
process.exit(bad ? 1 : 0);
