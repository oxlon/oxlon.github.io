// exports.mjs — builds the report in headless Chrome (both templates) and writes the .xlsx / .docx / .csv blobs to
// $RISK_SHOTS/exports for validation with python (openpyxl, zipfile + XML parsing).
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { launch, newPage, sleep, S } from './cdp.mjs';
const PANEL = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const out = path.join(S, 'exports'); fs.mkdirSync(out, { recursive: true });
const b = await launch(9343);
let bad = 0;
try {
  const p = await newPage(b, { width: 1440, height: 900 });
  for (const tpl of ['rehberlik', 'analitik']) {
    await p.goto(pathToFileURL(path.join(PANEL, 'index.html')).href + '?notour&t=' + tpl + '#/hesabat', 2500);
    await p.ev(`U.repApply('${tpl}'); U.route(true); 1`);
    await sleep(1500);
    for (const k of ['xlsx', 'docx', 'csv']) {
      const b64 = await p.ev(`U.REPX.${k}().then(U.blobB64)`);
      fs.writeFileSync(path.join(out, `${tpl}.${k}`), Buffer.from(b64, 'base64'));
      console.log(tpl, k, Math.round(Buffer.from(b64, 'base64').length / 1024) + ' KB');
    }
  }
  const errs = p.logs.filter(l => l.t === 'EXC' || l.t === 'error');
  if (errs.length) { bad++; console.log('XƏTA', errs.map(e => e.a).join(' | ')); }
} finally { b.close(); }
process.exit(bad ? 1 : 0);
