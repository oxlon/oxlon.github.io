// shots.mjs — headless-Chrome check of the Risk paneli: every page and sub-page (desktop 1440 and phone 390, ?notour),
// screenshots to $RISK_SHOTS/shots, JS errors (exceptions, console errors, window.onerror) → non-zero exit.
//   node panel/_build/shots.mjs [--only <route-substring>] [--desktop] [--full]
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { launch, newPage, sleep, S } from './cdp.mjs';

const PANEL = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const URL0 = pathToFileURL(path.join(PANEL, 'index.html')).href + '?notour';
const RISKS = Array.from({ length: 19 }, (_, i) => 'R' + String(i + 1).padStart(2, '0'));
const ROUTES = ['', 'reyestr', 'reyestr/xeberdarliq', 'reyestr/tarixce', 'reyestr/amiller', 'monitor', 'monitor/bazar', 'monitor/siqnal', 'monitor/tesir',
  'monitor/konsensus', 'paylanma', 'var', 'var/var', 'var/geri', 'var/car', 'var/dsa', 'var/ardnf', 'miqyas', 'miqyas/xerite', 'miqyas/parametr', 'miqyas/model',
  'stress', 'stress/qurucu', 'tedbir', 'tedbir/reyestr', 'tedbir/portfel', 'tedbir/plan', 'tedbir/strategiya', 'tedbir/qerar', 'caem', 'caem/balans', 'caem/kateqoriya',
  'caem/sok', 'caem/oturme', 'caem/tapinti', 'sinaq', 'hesabat', 'metod', 'metod/menbe', 'metod/cixis', 'metod/icra'].concat(RISKS.map(r => 'reyestr/' + r));
const args = process.argv.slice(2), only = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const sizes = args.includes('--desktop') ? [['d', 1440, 900, false]] : [['d', 1440, 900, false], ['m', 390, 844, true]];
const full = args.includes('--full');
const b = await launch(9341);
let bad = 0;
const report = [];
try {
  for (const [tag, w, h, mob] of sizes) {
    const p = await newPage(b, { width: w, height: h, mobile: mob });
    for (const r of ROUTES) {
      if (only && !r.includes(only)) continue;
      if (tag === 'm' && /^reyestr\/R(0[2-9]|1)/.test(r)) continue;          // phone: one drill-down is enough
      p.logs.length = 0;
      await p.goto(URL0 + '&n=' + (report.length + 1) + '#/' + r, 300);
      let ready = false;
      for (let i = 0; i < 40 && !ready; i++) { await sleep(250); ready = await p.ev("!/yüklənir/.test(document.querySelector('#view').innerText) && document.querySelector('#boot').hidden").catch(() => false); }
      await sleep(900);
      const err = await p.ev("document.documentElement.getAttribute('data-err')||''").catch(e => 'eval: ' + e.message);
      const ov = await p.ev("Math.max(0, document.documentElement.scrollWidth - window.innerWidth)").catch(() => -1);
      const logs = p.logs.filter(l => l.t === 'EXC' || l.t === 'error' || l.t === 'log-error');
      const name = tag + '_' + (r || 'home').replace(/\//g, '_');
      await p.shot(name, full || tag === 'd');
      const okk = !err && !logs.length && ready;
      if (!okk) bad++;
      report.push({ page: name, ok: okk, ready, overflow_px: ov, err, logs: logs.map(l => l.a).slice(0, 5) });
      console.log((okk ? 'ok  ' : 'XƏTA') + ' ' + name + (ov > 0 ? '  (üfüqi daşma ' + ov + ' px)' : '') + (err ? '  ' + err : '') + (logs.length ? '  ' + logs.map(l => l.a).join(' | ').slice(0, 300) : '') + (ready ? '' : '  (yüklənmə bitmədi)'));
    }
  }
} finally { b.close(); }
fs.writeFileSync(path.join(S, 'shots_report.json'), JSON.stringify(report, null, 1));
console.log(bad ? `EKRAN YOXLAMASI UĞURSUZ: ${bad} səhifədə xəta` : `EKRAN YOXLAMASI OK — ${report.length} görüntü, 0 JS xətası (${path.join(S, 'shots')})`);
process.exit(bad ? 1 : 0);
