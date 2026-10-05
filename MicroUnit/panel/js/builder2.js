/* builder2.js — Ssenari qurucusu, part 2: the page (#/ssenari), input events, the chained run through
   /api/v1/scenarios/run (FR1 → FR3, FR4, FR5, FR10 → FR12) and save / reset / export / import. Results: builder3.js. */
(function () {
  'use strict';
  var U = window.U, B = U.B;
  function num(s) { return U.parseNum(s); }
  U.bHead = function (sub) {
    var on = U.API.online;
    return '<div class="eyebrow">Ssenarilər</div><div class="hrow"><h1 class="h1" style="margin-top:4px">' + (sub === 'saxlanmis' ? 'Saxlanmış ssenarilər' : sub === 'hazir' ? 'Hazır ssenarilər: Əsas, Mənfi, İslahat' : 'Ssenari qurucusu') + '</h1>' +
      '<span class="hbtns"><span class="chip ' + (on ? 'acc' : on === false ? 'bad' : '') + '" id="api-pill">' + (on ? 'server: qoşulub' : on === false ? 'server: əlçatan deyil' : 'server yoxlanılır…') + '</span>' +
      '<button type="button" class="btn sm ghost" id="api-set2">Server ayarları</button></span></div>' +
      '<div class="toolbar" style="margin-top:6px">' + U.seg('ss-sub', [['qurucu', 'Qurucu'], ['saxlanmis', 'Saxlanmış ssenarilər'], ['hazir', 'Hazır ssenarilər']], sub) + '</div>';
  };
  function page(v) {
    var mods = U.MODS.map(function (m) { var n = U.bCount(m); return [m, m + (n ? ' · ' + n : '')]; });
    var h = U.bHead('qurucu') + (U.API.online === false ? U.API.offlineHtml() : '') +
      '<p class="lead" style="font-size:14.5px">Üç addım: <b>1.</b> baza ssenarisini seçin; <b>2.</b> ekzogen fərziyyələri, əmsalları və ya alətləri dəyişin (sarı xanalar); <b>3.</b> «Hesabla» — FR1-in nəticəsi FR3, FR4, FR5, FR10 və FR12-yə ötürülür və bütün modulların 2026–2030 nəticələri Əsas ilə müqayisədə göstərilir.</p>' +
      '<div class="scen-layout"><div class="card bld-l"><div class="toolbar" style="margin:12px 16px"><span class="small muted">Baza ssenarisi</span>' +
      U.seg('b-base', [['Baseline', 'Əsas'], ['Adverse', 'Mənfi'], ['Reform', 'İslahat']], B.base) + '</div>' +
      '<div class="sectabs" style="margin:0 16px 10px" id="b-mod">' + mods.map(function (m) { return '<button type="button" class="stab' + (m[0] === B.mod ? ' on' : '') + '" data-v="' + m[0] + '">' + m[1] + '</button>'; }).join('') + '</div>' +
      '<div class="toolbar" style="margin:0 16px 8px">' + U.seg('b-sec', [['ex', 'Ekzogen fərziyyələr'], ['co', 'Əmsallar'], ['lv', 'Alətlər']], B.sec) +
      '<input type="search" id="b-q" placeholder="süzgəc…" value="' + U.esc(B.q) + '" style="height:28px;border:1px solid var(--line);border-radius:7px;padding:0 8px">' +
      (B.sec === 'co' ? '<label class="small"><input type="checkbox" id="b-ed"' + (B.onlyEd ? ' checked' : '') + '> yalnız redaktə edilə bilənlər</label>' : '') + '</div>' +
      '<div id="b-inputs">' + U.bInputsHtml() + '</div>' +
      '<div class="b-dock"><button type="button" class="btn pri" data-run="1">Hesabla</button>' + (B.res ? '<button type="button" class="btn" data-jump="1">Nəticələr ↓</button>' : '') +
      '<span class="small muted" id="b-dock-sum">' + dockSum() + '</span></div></div>' +
      '<div class="impact"><div class="card pad"><h3 style="font-size:16px">Ssenari</h3><div class="form"><label>Ad<input id="b-name" value="' + U.esc(B.name) + '" placeholder="məs. Neft −20 %"></label>' +
      '<label>Qeyd<input id="b-note" value="' + U.esc(B.note) + '" placeholder="istəyə görə"></label></div>' +
      '<div class="small" id="b-sum" style="margin:8px 0">' + summary() + '</div>' +
      '<div class="toolbar" style="margin:8px 0 0"><button type="button" class="btn pri" id="b-run">Hesabla</button><button type="button" class="btn" id="b-save">Saxla</button>' +
      '<button type="button" class="btn ghost" id="b-reset">Hamısını sıfırla</button></div>' +
      '<div class="toolbar" style="margin:6px 0 0"><button type="button" class="btn sm" id="b-exp">JSON ixrac</button><label class="btn sm" style="cursor:pointer">JSON idxal<input type="file" id="b-imp" accept=".json,application/json" hidden></label>' +
      (B.res ? '<a class="btn sm" href="#/hesabat?cur=1">Hesabata əlavə et</a>' : '') + '</div>' +
      (B.res ? '<button type="button" class="btn sm ghost b-jump" data-jump="1">↓ Nəticələrə keç</button>' : '') +
      '<div id="b-status" class="small muted" style="margin-top:8px"></div></div></div></div>' +
      '<section class="sec" id="b-results">' + (U.bResultsHtml ? U.bResultsHtml() : '') + '</section>';
    v.innerHTML = h;
  }
  function dockSum() { var n = U.MODS.reduce(function (a, m) { return a + U.bCount(m); }, 0); return n ? n + ' dəyişiklik' : 'dəyişiklik yoxdur'; }
  U.bJump = function () { var r = U.$('#b-results'); if (r) r.scrollIntoView({ behavior: 'smooth', block: 'start' }); };
  function summary() {
    var parts = [];
    U.MODS.forEach(function (m) { var x = B.ov[m]; if (!x) return; var a = Object.keys(x.exogenous).length, c = Object.keys(x.coefficients).length, l = Object.keys(x.levers).length;
      if (a + c + l) parts.push('<b>' + m + '</b>: ' + [a ? a + ' ekzogen' : '', c ? c + ' əmsal' : '', l ? l + ' alət' : ''].filter(Boolean).join(', ')); });
    return parts.length ? 'Dəyişikliklər — ' + parts.join(' · ') : '<span class="muted">Hələ dəyişiklik yoxdur: «Hesabla» baza ssenarisini təkrar hesablayacaq.</span>';
  }
  function refreshInputs() { U.$('#b-inputs').innerHTML = U.bInputsHtml(); U.$('#b-sum').innerHTML = summary(); var ds = U.$('#b-dock-sum'); if (ds) ds.textContent = dockSum(); U.$$('#b-mod .stab').forEach(function (b) { var n = U.bCount(b.getAttribute('data-v')); b.textContent = b.getAttribute('data-v') + (n ? ' · ' + n : ''); }); }
  U.bRefresh = refreshInputs;
  function status(t, cls) { var el = U.$('#b-status'); if (el) { el.className = 'small ' + (cls || 'muted'); el.innerHTML = t; } }
  U.bRun = function () {
    B.name = (U.$('#b-name') || {}).value || B.name; B.note = (U.$('#b-note') || {}).value || B.note;
    status('Hesablanır… (zəncir: FR1 → FR3, FR4, FR5, FR10 → FR12)');
    var btn = U.$('#b-run'); if (btn) btn.disabled = true;
    return U.API.run({ overrides: U.bClean(), scenario: B.base, save: false }).then(function (j) {
      U.bSetResult(j.result, { seconds: j.seconds, base: B.base, overrides: U.bClean(), name: B.name || 'Adsız ssenari' });
      // re-render the builder (the «Nəticələr ↓» buttons appear) and jump to the results
      if (U.$('#b-inputs')) { U.route(true); setTimeout(U.bJump, 60); }
      else { var r = U.$('#b-results'); if (r) { r.innerHTML = U.bResultsHtml(); U.bResultsBind(); U.bJump(); } }
      status('Hazırdır: ' + (j.seconds != null ? U.nf(j.seconds, 1) + ' san.' : '') + ' · nəticələr aşağıda', 'up');
    }).catch(function (e) { status(U.esc(e.message), 'down'); if (window.console) console.warn(e); }).then(function () { var b2 = U.$('#b-run'); if (b2) b2.disabled = false; });
  };
  U.bSave = function () {
    B.name = U.$('#b-name').value.trim(); B.note = U.$('#b-note').value.trim();
    if (!B.name) { status('Ssenariyə ad verin.', 'down'); U.$('#b-name').focus(); return Promise.resolve(); }
    var go = B.res && B.resInfo && JSON.stringify(B.resInfo.overrides) === JSON.stringify(U.bClean()) && B.resInfo.base === B.base ? Promise.resolve() : U.bRun();
    return go.then(function () {
      if (!B.raw) return;
      var body = { name: B.name, author: U.ls('mikroPanel.author') || 'panel', scenario: B.base, overrides: U.bClean(), result: B.raw, note: B.note };
      if (B.savedId && B.savedName === B.name) body.id = B.savedId;
      return U.API.save(body).then(function (j) { var s = j && j.id ? j : (j.saved || {}); B.savedId = s.id; B.savedName = B.name; status('Saxlanıldı: «' + U.esc(B.name) + '» (' + U.esc(s.id || '') + ')', 'up'); U.toast('Ssenari saxlanıldı'); if (U.savedLoad) U.savedLoad(); },
        function (e) { status(U.esc(e.message), 'down'); });
    });
  };
  U.bExport = function () {
    var o = { format: 'mikro-ssenari/1', name: B.name || 'ssenari', scenario: B.base, note: B.note, overrides: U.bClean(), created: new Date().toISOString(), result: B.res || null };
    U.download((B.name || 'ssenari').replace(/[^\wəöüğışçİ\-]+/gi, '_') + '.json', new Blob([JSON.stringify(o, null, 1)], { type: 'application/json' }));
  };
  function importFile(f) {
    var r = new FileReader();
    r.onload = function () {
      try {
        var o = JSON.parse(r.result); B.ov = {}; B.out = {};
        Object.keys(o.overrides || {}).forEach(function (m) { var x = o.overrides[m]; B.ov[m] = { exogenous: x.exogenous || {}, coefficients: x.coefficients || {}, levers: x.levers || {} }; });
        B.base = o.scenario || 'Baseline'; B.name = o.name || ''; B.note = o.note || ''; B.savedId = null; U.bNorm();
        if (o.result) U.bSetCompact(o.result, { base: B.base, overrides: U.bClean(), name: B.name });
        U.route(true); U.toast('Ssenari idxal olundu');
      } catch (e) { U.toast('Fayl oxunmadı: ' + e.message); }
    };
    r.readAsText(f);
  }
  U.pages.ssenari = function (v, p) {
    var sub = p[1] || 'qurucu';
    if (sub === 'saxlanmis') { U.savedPage(v); return; }
    if (sub === 'hazir') { U.readyPage(v); return; }
    page(v);
    if (B.res) U.bResultsBind();
    var inp = U.$('#b-inputs');
    inp.addEventListener('toggle', function (e) { var d = e.target; if (d && d.classList && d.classList.contains('cgrp')) { B.coOpen = B.coOpen || {}; B.coOpen[d.getAttribute('data-cg')] = d.open; } }, true);
    v.onclick = function (e) {
      var t = e.target, s;
      if ((s = t.closest('#ss-sub [data-v]'))) { location.hash = '#/ssenari' + (s.getAttribute('data-v') === 'qurucu' ? '' : '/' + s.getAttribute('data-v')); return; }
      if ((s = t.closest('#b-base [data-v]'))) { B.base = s.getAttribute('data-v'); U.route(true); return; }
      if ((s = t.closest('#b-mod [data-v]'))) { B.mod = s.getAttribute('data-v'); U.route(true); return; }
      if ((s = t.closest('#b-sec [data-v]'))) { B.sec = s.getAttribute('data-v'); U.route(true); return; }
      if (t.id === 'api-set2' || t.id === 'api-set') { U.API.openSettings(); return; }
      if (t.id === 'api-retry') { U.API.ping().then(function () { U.route(true); }); return; }
      if (t.closest('summary [data-eq]')) { e.preventDefault(); return; }    // «tənlik ↗» opens the dialog, not the group
      if (t.id === 'b-run' || t.closest('[data-run]')) { U.bRun(); return; }
      if (t.closest('[data-jump]')) { U.bJump(); return; }
      if (t.getAttribute('data-act') === 'co-open' || t.getAttribute('data-act') === 'co-close') {
        B.coOpen = B.coOpen || {}; var op = t.getAttribute('data-act') === 'co-open';
        U.$$('#b-inputs details.cgrp').forEach(function (d) { B.coOpen[d.getAttribute('data-cg')] = op; d.open = op; }); return;
      }
      if (t.id === 'b-save') { U.bSave(); return; }
      if (t.id === 'b-exp') { U.bExport(); return; }
      if (t.id === 'b-reset') { B.ov = {}; B.out = {}; U.route(true); return; }
      var row = t.closest('[data-ex]'), act = t.getAttribute('data-act');
      if (row && act) {
        var id = row.getAttribute('data-ex'), I = U.inputsOf(B.mod), ex = I.exogenous.filter(function (x) { return x.id === id; })[0], b = U.bBase(ex);
        if (act === 'reset') U.bSetEx(B.mod, id, b.slice());
        if (act === 'pct') { var pc = num(row.querySelector('[data-pct]').value); if (pc == null || isNaN(pc)) { U.toast('Faizi yazın, məs. −20'); return; } U.bSetEx(B.mod, id, b.map(function (x) { return x * (1 + pc / 100); })); }
        refreshInputs(); return;
      }
      var cr = t.closest('[data-co]');
      if (cr && act === 'creset') { delete U.bOv(B.mod).coefficients[cr.getAttribute('data-co')]; refreshInputs(); return; }
      var lr = t.closest('[data-lvid]');
      if (lr && act === 'lreset') { delete U.bOv(B.mod).levers[lr.getAttribute('data-lvid')]; refreshInputs(); return; }
      if (lr && (s = t.closest('.seg [data-v]'))) { U.bOv(B.mod).levers[lr.getAttribute('data-lvid')] = s.getAttribute('data-v') === 'true'; refreshInputs(); return; }
      if (U.bResultsClick) U.bResultsClick(e);
    };
    inp.onchange = function (e) {
      var t = e.target, row = t.closest('[data-ex]'), cr = t.closest('[data-co]'), lr = t.closest('[data-lvid]');
      if (row && t.hasAttribute('data-i')) {
        var arr = U.$$('input[data-i]', row).map(function (x) { return x.value === x.getAttribute('data-d') && x.getAttribute('data-v') !== '' && x.hasAttribute('data-v') ? Number(x.getAttribute('data-v')) : num(x.value); });   // untouched cells keep full precision
        U.bSetEx(B.mod, row.getAttribute('data-ex'), arr); refreshInputs(); return;
      }
      if (cr) {
        var key = cr.getAttribute('data-co');
        if (t.hasAttribute('data-out')) { B.out[key] = t.checked; refreshInputs(); return; }
        var val = t.type === 'range' ? Number(t.value) : num(t.value);
        if (val == null || isNaN(val)) return;
        var c = U.inputsOf(B.mod).coefficients.filter(function (x) { return x.eq_id + '|' + x.name === key; })[0];
        if (U.isNum(c.ci_low) && U.isNum(c.ci_high) && (val < c.ci_low || val > c.ci_high) && !B.out[key]) { val = Math.min(Math.max(val, c.ci_low), c.ci_high); U.toast('Dəyər 95 % intervalına çəkildi. Kənara çıxmaq üçün «interval xaricinə icazə» seçin.'); }
        if (Math.abs(val - c.value) < 1e-15) delete U.bOv(B.mod).coefficients[key]; else U.bOv(B.mod).coefficients[key] = val;
        refreshInputs(); return;
      }
      if (lr && t.hasAttribute('data-lv')) {
        var id = lr.getAttribute('data-lvid'), L = U.inputsOf(B.mod).levers.filter(function (x) { return x.id === id; })[0], raw = t.value;
        var o = U.bOv(B.mod).levers;
        if (t.tagName === 'SELECT') { if (raw === String(L.value)) delete o[id]; else o[id] = raw === 'true' ? true : raw === 'false' ? false : raw; }
        else if (raw.trim() === '') delete o[id];
        else { var parts = raw.split(/[;]/).map(num); o[id] = parts.length > 1 ? parts : parts[0]; }
        refreshInputs();
      }
    };
    inp.oninput = function (e) { var t = e.target; if (t.type === 'range') { var n = t.parentNode.querySelector('.cnum'); if (n) { n.value = U.inFmt(t.value, 4); n.title = 'dəqiq dəyər: ' + U.inFull(t.value); } } };
    U.$('#b-q').oninput = U.debounce(function (e) { B.q = e.target.value; refreshInputs(); }, 250);
    var ed = U.$('#b-ed'); if (ed) ed.onchange = function () { B.onlyEd = ed.checked; refreshInputs(); };
    U.$('#b-imp').onchange = function (e) { if (e.target.files[0]) importFile(e.target.files[0]); };
  };
  U.API.onChange(function () { if (/^#\/ssenari/.test(location.hash)) U.route(true); });
})();
