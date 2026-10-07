// cdp.mjs — minimal Chrome DevTools Protocol driver (Node global WebSocket), copied from the review scripts.
// Screenshots and the Chrome profile go to $POLICY_SHOTS (default: PolicyUnit/work/panel_shots).
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
export const S = process.env.POLICY_SHOTS || path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../work/panel_shots');
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
export { sleep };

export async function launch(port = 9333) {
  const ud = path.join(S, 'chrome-profile-' + port);
  fs.rmSync(ud, { recursive: true, force: true });
  const proc = spawn(CHROME, ['--headless=new', '--remote-debugging-port=' + port, '--user-data-dir=' + ud,
    '--no-first-run', '--no-default-browser-check', '--disable-gpu', '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
  fs.mkdirSync(path.join(S, 'shots'), { recursive: true });
  let ver;
  for (let i = 0; i < 50; i++) { try { ver = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json(); break; } catch (e) { await sleep(200); } }
  const ws = new WebSocket(ver.webSocketDebuggerUrl);
  await new Promise(r => ws.addEventListener('open', r, { once: true }));
  let id = 0; const pend = new Map(); const handlers = [];
  ws.addEventListener('message', (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pend.has(m.id)) { const { res, rej } = pend.get(m.id); pend.delete(m.id); m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result); }
    else handlers.forEach(h => h(m));
  });
  const send = (method, params = {}, sessionId) => new Promise((res, rej) => { const i = ++id; pend.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params, sessionId })); });
  const browser = { send, proc, handlers, close: () => { try { ws.close(); } catch (e) {} proc.kill('SIGKILL'); } };
  return browser;
}

export async function newPage(b, { width = 1440, height = 900, mobile = false, dl } = {}) {
  const { targetId } = await b.send('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await b.send('Target.attachToTarget', { targetId, flatten: true });
  const s = (m, p) => b.send(m, p, sessionId);
  const logs = [];
  b.handlers.push((m) => {
    if (m.sessionId !== sessionId) return;
    if (m.method === 'Runtime.consoleAPICalled') logs.push({ t: m.params.type, a: m.params.args.map(a => a.value ?? a.description ?? '').join(' ') });
    if (m.method === 'Runtime.exceptionThrown') logs.push({ t: 'EXC', a: (m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text) + ' @' + m.params.exceptionDetails.url + ':' + m.params.exceptionDetails.lineNumber });
    if (m.method === 'Log.entryAdded') logs.push({ t: 'log-' + m.params.entry.level, a: m.params.entry.text + ' ' + (m.params.entry.url || '') });
  });
  await s('Runtime.enable'); await s('Page.enable'); await s('Log.enable');
  await s('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile });
  if (mobile) await s('Emulation.setTouchEmulationEnabled', { enabled: true });
  if (dl) { fs.mkdirSync(dl, { recursive: true }); await b.send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: dl, eventsEnabled: true }); }
  const page = {
    s, logs, sessionId,
    async goto(url, wait = 2500) { await s('Page.navigate', { url }); await sleep(wait); },
    async ev(expr, awaitP = true) {
      const r = await s('Runtime.evaluate', { expression: expr, awaitPromise: awaitP, returnByValue: true, userGesture: true });
      if (r.exceptionDetails) throw new Error('eval: ' + (r.exceptionDetails.exception?.description || r.exceptionDetails.text));
      return r.result.value;
    },
    async shot(name, full = false) {
      let clip;
      if (full) { const m = await s('Page.getLayoutMetrics'); const h = Math.min(m.cssContentSize.height, 12000); clip = { x: 0, y: 0, width: m.cssContentSize.width, height: h, scale: 1 }; }
      const r = await s('Page.captureScreenshot', { format: 'png', captureBeyondViewport: full, ...(clip ? { clip } : {}) });
      fs.writeFileSync(path.join(S, 'shots', name + '.png'), Buffer.from(r.data, 'base64'));
    },
    async click(sel) { return page.ev(`(function(){var e=document.querySelector(${JSON.stringify(sel)}); if(!e) return 'NOEL'; e.scrollIntoView({block:'center'}); e.click(); return 'ok';})()`); },
    async pdf(file) { const r = await s('Page.printToPDF', { printBackground: true }); fs.writeFileSync(file, Buffer.from(r.data, 'base64')); },
  };
  return page;
}
