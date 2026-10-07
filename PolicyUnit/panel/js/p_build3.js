/* p_build3.js — Ssenari qurucusu, part 3: button actions (validate, run / offline approximation, save draft or official,
   duplicate, JSON export, new) and the list of bundled + server-side scenarios (open, run, promote, delete). */
(function () {
  'use strict';
  var U = window.U, B = U.BLD, A = U.API;
  function body() { var s = JSON.parse(JSON.stringify(B.s)); delete s.idManual; delete s.nameManual; delete s._saved; s.instruments.forEach(function (it) { if (it.target === '') it.target = null; }); return s; }
  U.bBody = body;
  function busy(v, on, msg) { B.busy = on; U.$$('#b-chk,#b-run,#b-save,#b-off', v).forEach(function (b) { b.disabled = on; }); if (msg) U.$('#b-val', v).innerHTML = '<div class="vmsg warn">' + U.esc(msg) + '</div>'; }
  function fail(v, what, e) { busy(v, false); U.$('#b-val', v).innerHTML = A.failHtml(what, e); }
  function validate(v, then) {
    var c = U.bCheck(B.s); c.src = 'brauzerdə yoxlama'; c.engines = U.bEngines(B.s);
    if (!c.valid || A.fileMode() || A.online === false) { B.val = c; if (!c.valid || !then) return then ? null : c; return then(c); }
    busy(v, true, 'Serverdə yoxlanılır…');
    return A.validate(body()).then(function (r) { busy(v, false); r.src = 'server'; B.val = r; return then && r.valid ? then(r) : r; }, function (e) { busy(v, false); c.src = 'brauzerdə yoxlama (server əlçatan deyil)'; B.val = c; return then ? then(c) : c; });
  }
  U.bClick = function (e, v, draw) {
    var t = e.target.closest('button,[data-add],[data-open]'); if (!t || B.busy) return;
    if (t.dataset.add) { U.bAdd(t.dataset.add); draw(v); U.toast('Alət əlavə edildi'); var rr = U.$$('.irow', v); if (rr.length) rr[rr.length - 1].scrollIntoView({ block: 'nearest' }); return; }
    if (t.dataset.act === 'rm') { B.s.instruments.splice(+t.closest('[data-row]').dataset.row, 1); B.val = null; U.bSave(); draw(v); return; }
    if (t.dataset.open) { var sc = U.scen(t.dataset.open); U.bLoad({ id: sc.id, name_az: sc.name, description_az: sc.desc, start_year: sc.start, instruments: sc.ins, tags: sc.tags }, t.dataset.copy === '1'); U.route(true); window.scrollTo(0, 0); return; }
    if (t.dataset.srv) return srvAct(t.dataset.srv, t.dataset.id, v, t.dataset.src);
    var id = t.id;
    if (id === 'b-chk') { var r = validate(v, null); if (r && r.then) r.then(function () { draw(v); }); else draw(v); }
    else if (id === 'b-run') {
      if (A.mode() === 'paket') { var c = U.bCheck(B.s); if (!c.valid) { B.val = c; c.src = 'brauzerdə yoxlama'; draw(v); return; } B.res = { approx: U.bApprox(B.s) }; draw(v); return; }
      validate(v, function () {
        busy(v, true, A.online ? 'Hesablanır… (bütün uyğun mühərriklər; adətən < 30 s)' : 'Brauzerdə hesablanır… (Python; ilk dəfə mühit yüklənir)');
        return A.run(null, { scenario: body(), wait: 60 }, function (p) { U.$('#b-val', v).innerHTML = '<div class="vmsg warn">Hesablanır: ' + U.esc((p.stage_az || p.stage || '') + ' · ' + U.nf(p.pct || 0, 0)) + ' %</div>'; })
          .then(function (res) { busy(v, false); B.res = res; draw(v); U.toast('Hesablama bitdi'); }, function (er) { fail(v, 'Hesablama', er); });
      }).then(function () { draw(v); });
    } else if (id === 'b-save' || id === 'b-off') {
      if (A.fileMode() || A.online === false) { var c2 = U.bCheck(B.s); B.val = c2; c2.src = 'brauzerdə yoxlama'; if (!c2.valid) { draw(v); return; } B.s._saved = B.s.id; B.s.idManual = true; saveLocal(); U.bSave(); U.toast('Server yoxdur — ssenari bu brauzerdə saxlanıldı; JSON faylını config/scenarios/ qovluğuna qoyun'); U.download(B.s.id + '.json', new Blob([JSON.stringify(body(), null, 1)], { type: 'application/json' })); U.bList(v); draw(v); return; }
      validate(v, function () { busy(v, true, 'Saxlanılır…'); return A.save(body(), id === 'b-off').then(function (r) { busy(v, false); B.s._saved = B.s.id; B.s.idManual = true; U.bSave(); U.toast(id === 'b-off' ? 'Rəsmi ssenari kimi saxlanıldı (config/scenarios/' + B.s.id + '.json)' : 'Qaralama saxlanıldı'); U.bList(v); B.val = { valid: true, errors: [], warnings: r.errors || [], src: 'server: saxlanıldı' }; draw(v); }, function (er) { fail(v, 'Saxlama', er); }); }).then(function () { draw(v); });
    } else if (id === 'b-dup') { U.bLoad(B.s, true); U.route(true); U.toast('Surət yaradıldı — kodu və adı dəyişin'); }
    else if (id === 'b-json') U.download((B.s.id || 'ssenari') + '.json', new Blob([JSON.stringify(body(), null, 1)], { type: 'application/json' }));
    else if (id === 'b-new') { U.bReset(); U.route(true); }
  };
  function local() { try { return JSON.parse(U.ls('policyPanel.saved') || '[]'); } catch (e) { return []; } }
  U.localScen = function (ids) { return local().filter(function (x) { return ids.indexOf(x.id) >= 0; }); };
  function saveLocal() { var L = local().filter(function (x) { return x.id !== B.s.id; }); L.push(body()); U.ls('policyPanel.saved', JSON.stringify(L)); }
  function insTxt(L) { return (L || []).map(function (i) { var m = U.instr(i.instrument) || {}; return (m.name_az || i.instrument) + ' ' + U.sg(i.size, 2) + ' ' + (U.UNITN[i.unit] || i.unit || '') + ' · ' + (i.years === 'all' ? 'daimi' : (i.years || []).join(', ')); }).join('; '); }
  U.toCompare = function (id) {
    var st = null; try { st = JSON.parse(U.ls('policyPanel.kpi') || 'null'); } catch (e) { st = null; }
    st = st && st.sel ? st : { sel: U.T('P5_kpi_catalogue').filter(function (k) { return k.default_selected === 'yes'; }).map(function (k) { return k.id; }), w: {}, sc: [] };
    if (st.sc.indexOf(id) < 0) st.sc.push(id); U.ls('policyPanel.kpi', JSON.stringify(st)); U.toast('Müqayisəyə əlavə edildi (' + st.sc.length + ' ssenari) — «KPI» bölməsi');
  };
  function srvAct(act, id, v, src) {
    var loc = local().filter(function (x) { return x.id === id; })[0], off = U.scen(id);
    if (act === 'cmp') { U.toCompare(id); return; }
    if (act === 'open' || act === 'dup') {
      if (src === 'server') { A.get(id).then(function (r) { U.bLoad(r.scenario || r, act === 'dup'); U.route(true); window.scrollTo(0, 0); }, function (e) { U.toast(e.message); }); return; }
      var sc = loc || (off ? { id: off.id, name_az: off.name, description_az: off.desc, start_year: off.start, instruments: off.ins, tags: off.tags } : null);
      if (sc) { U.bLoad(sc, act === 'dup' || src === 'rəsmi'); U.route(true); window.scrollTo(0, 0); U.toast(src === 'rəsmi' && act === 'open' ? 'Rəsmi ssenarinin surəti qurucuda açıldı' : 'Qurucuda açıldı'); }
      return;
    }
    if (act === 'run') {
      if (!A.online && src === 'rəsmi') { location.hash = '#/tesir?s=' + U.enc(id); U.toast('Bu ssenari paketdə hesablanıb — nəticələr açıldı'); return; }
      if (A.mode() === 'paket') {
        if (loc) { U.bLoad(loc, false); B.res = { approx: U.bApprox(B.s) }; U.route(true); } return;
      }
      U.$('#b-val', v).innerHTML = '<div class="vmsg warn">«' + U.esc(U.sname(id) || id) + '» hesablanır…</div>';
      var p = src === 'local' ? A.run(null, { scenario: loc, wait: 60 }) : A.run(id, { wait: 60 });
      p.then(function (r) { B.res = r; U.bDraw(v); var el = U.$('#b-res', v); if (el) el.scrollIntoView({ block: 'start' }); U.toast('Hesablama bitdi'); }, function (e) { U.$('#b-val', v).innerHTML = A.failHtml('Hesablama', e); });
      return;
    }
    if (act === 'ldel') { U.ls('policyPanel.saved', JSON.stringify(local().filter(function (x) { return x.id !== id; }))); U.bList(v); return; }
    var q = act === 'promote' ? A.promote(id).then(function () { U.toast('Rəsmi ssenariyə çevrildi'); U.bList(v); }) : act === 'del' ? A.del(id).then(function () { U.toast('Silindi'); U.bList(v); }) : Promise.resolve();
    q.catch(function (e) { U.toast(e.message); });
  }
  U.bSrv = srvAct;
  function btns(id, src) {
    var b = [['open', 'Aç'], ['run', 'Hesabla'], ['dup', 'Surət'], ['cmp', 'Müqayisəyə əlavə et']].concat(src === 'server' ? [['promote', 'Rəsmiləşdir'], ['del', 'Sil']] : src === 'local' ? [['ldel', 'Sil']] : []);
    return b.map(function (x) { return '<button type="button" class="btn sm' + (x[0] === 'run' ? ' pri' : x[0] === 'del' || x[0] === 'ldel' ? ' ghost' : '') + '" data-srv="' + x[0] + '" data-id="' + U.esc(id) + '" data-src="' + src + '">' + x[1] + '</button>'; }).join(' ');
  }
  var LC = [{ k: 'name', l: 'Ssenari', f: function (x, o) { return '<b>' + U.esc(x) + '</b>' + (o.desc ? '<div class="small muted">' + U.esc(o.desc) + '</div>' : ''); } }, { k: 'srcl', l: 'Mənbə' }, { k: 'ins', l: 'Alətlər (ölçü, illər)' }, { k: 'id', l: '', f: function (x, o) { return btns(x, o.src); } }];
  U.bList = function (v) {
    var el = U.$('#b-list', v); if (!el) return;
    var rows = U.official().map(function (s) { return { id: s.id, name: s.name, desc: s.desc, ins: insTxt(s.ins), src: 'rəsmi', srcl: 'rəsmi (hesablanıb)' }; })
      .concat(local().map(function (s) { return { id: s.id, name: s.name_az || s.id, desc: s.description_az, ins: insTxt(s.instruments), src: 'local', srcl: 'bu brauzerdə' }; }));
    var draw = function (extra) { el.innerHTML = U.dt('b-exist', rows.concat(extra || []), LC, { title: 'Mövcud ssenarilər', file: 'ssenariler', lim: 30, note: 'Hər hansı ssenarini bir kliklə hesablayın, qurucuda açın, surətini çıxarın və ya KPI müqayisəsinə əlavə edin — kodunu bilmək lazım deyil.' }); };
    draw();
    if (A.fileMode() || A.online === false) return;
    A.list('draft').then(function (r) {
      B.srvIds = {}; var S = (r.scenarios || []).map(function (x) { var sc = x.scenario || x; B.srvIds[x.id] = 1; return { id: x.id, name: x.name_az || sc.name_az || x.id, desc: sc.description_az || '', ins: insTxt(sc.instruments), src: 'server', srcl: 'serverdə qaralama' + (x.valid === false ? ' (xəta)' : '') }; });
      draw(S);
    }, function () { /* offline */ });
  };
})();
