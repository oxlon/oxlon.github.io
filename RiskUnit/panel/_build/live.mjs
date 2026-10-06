// live.mjs — end-to-end check of the live features against a running API (http://127.0.0.1:8791/panel/):
// stress builder run, scalability «Canlı hesabla», portfolio re-optimisation; reports JS errors.
import { launch, newPage, sleep } from './cdp.mjs';
const BASE = process.env.RISK_URL || 'http://127.0.0.1:8791/panel/';
const b = await launch(9345);
let bad = 0;
async function wait(p, expr, n = 120) { for (let i = 0; i < n; i++) { if (await p.ev(expr).catch(() => false)) return true; await sleep(500); } return false; }
try {
  const p = await newPage(b, { width: 1440, height: 900 });
  const steps = [['stress/qurucu', '#sb-run', "!!document.querySelector('[data-dt=sb-h]')", 'stress'],
    ['miqyas', '#sc-run', "!!document.querySelector('[data-dt=sc-rh]')", 'miqyaslanma'],
    ['tedbir/portfel', '#op-run', "!!document.querySelector('[data-dt=op-p]')", 'optimallaşdırma']];
  for (const [r, btn, done, nm] of steps) {
    await p.goto(BASE + '?notour#/' + r, 3500);
    await wait(p, `!!document.querySelector('${btn}')`);
    await p.click(btn);
    const ok = await wait(p, done);
    const txt = await p.ev("document.querySelector('#view').innerText.slice(0, 0)").catch(() => '');
    const errs = p.logs.filter(l => l.t === 'EXC' || l.t === 'error');
    const off = await p.ev("!!document.querySelector('.offline')");
    console.log((ok && !errs.length ? 'ok  ' : 'XƏTA') + ' ' + nm + (off ? ' (oflayn mesajı göstərildi)' : '') + (errs.length ? ' ' + errs.map(e => e.a).join(' | ').slice(0, 400) : '') + txt);
    if (!ok || errs.length) bad++;
    await p.shot('live_' + r.replace('/', '_'), true);
    p.logs.length = 0;
  }
} finally { b.close(); }
process.exit(bad ? 1 : 0);
