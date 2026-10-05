/* builder.js — Ssenari qurucusu, part 1: state and the editable inputs of every engine — exogenous paths 2026–2030
   (year cells, «% hamısına», bərpa), estimated coefficients (estimate ± SE, 95 % CI slider, «interval xaricinə icazə»)
   and module levers. Inputs come from data/inputs.js (engines' inputs()), so they render offline too. */
(function () {
  'use strict';
  var U = window.U, M = window.MICRO;
  var B = U.B = { base: 'Baseline', mod: 'FR1', sec: 'ex', ov: {}, out: {}, onlyEd: true, q: '', name: '', note: '', res: null, resInfo: null, savedId: null };
  U.MODS = ['FR1', 'FR3', 'FR4', 'FR5', 'FR10', 'FR12'];
  U.OPT_AZ = { shock: 'şok', reanchor: 'yenidən ankor', policy_oilrev: 'siyasət: neft gəlirləri', policy_level: 'siyasət: səviyyə', F4: 'F4 tənliyi',
    'cross-check': 'çarpaz yoxlama', fixed: 'sabit', weighted: 'çəkili', trend: 'trend', frozen: 'dondurulmuş', sigma: 'σ (pay)', kappa: 'κ (nisbət)',
    constant: 'sabit', drift: 'meyl', admin: 'inzibati', chosen: 'seçilmiş (DOLS)', difference: 'fərq forması', income_srv: 'xidmət qiyməti ilə gəlir',
    income_only: 'yalnız gəlir', neutral: 'neytral', construction_link: 'tikinti ilə əlaqə', labour_share: 'əməyin payı', fr1_wage: 'FR1 əmək haqqı',
    product_wage: 'məhsul əmək haqqı', 'true': 'bəli', 'false': 'xeyr', AGR: 'Kənd təsərrüfatı', IND: 'Sənaye', CON: 'Tikinti', TRD: 'Ticarət', TRA: 'Nəqliyyat',
    ACC: 'Yerləşdirmə və iaşə', ICT: 'İnformasiya və rabitə', REA: 'Daşınmaz əmlak', EDU: 'Təhsil', HEA: 'Səhiyyə', OTH: 'Digər sahələr', MOB: 'Mobil rabitə', BNK: 'Bank sektoru', CEM: 'Sement' };
  U.inputsOf = function (m) { return ((M.INP || {}).inputs || {})[m] || null; };
  function ov(m) { return B.ov[m] || (B.ov[m] = { exogenous: {}, coefficients: {}, levers: {} }); }
  U.bClean = function () {
    var o = {};
    U.MODS.forEach(function (m) {
      var x = B.ov[m]; if (!x) return;
      var y = {};
      ['exogenous', 'coefficients', 'levers'].forEach(function (k) { if (x[k] && Object.keys(x[k]).length) y[k] = x[k]; });
      if (Object.keys(y).length) o[m] = y;
    });
    return o;
  };
  U.bCount = function (m) { var x = B.ov[m]; return x ? Object.keys(x.exogenous).length + Object.keys(x.coefficients).length + Object.keys(x.levers).length : 0; };
  function baseOf(e) { var b = e.baseline || {}; return b[B.base] || b.Baseline || []; }
  function exRow(m, e) {
    var b = baseOf(e), cur = ov(m).exogenous[e.id], yrs = e.years || U.YEARS;
    var h = '<div class="assump" data-ex="' + U.esc(e.id) + '"><div><h4>' + U.esc(e.label_az || e.id) + '</h4><div class="src">' + U.esc(e.unit || '') + ' · <code>' + U.esc(e.id) + '</code>' + (e.source ? ' · ' + U.esc(e.source) : '') + '</div>' +
      (e.note_az ? '<div class="why">' + U.esc(e.note_az) + '</div>' : '') + '</div><div class="yrs" style="--ny:' + yrs.length + '">';
    yrs.forEach(function (y, i) {
      var v = cur ? cur[i] : b[i], mod = cur && U.isNum(cur[i]) && Math.abs(cur[i] - b[i]) > 1e-12 * Math.max(1, Math.abs(b[i]));
      h += '<div class="yr"><label>' + y + '</label><input inputmode="decimal" data-i="' + i + '" class="' + (mod ? 'mod' : '') + '" value="' + U.inFmt(v, 5) + '" data-d="' + U.inFmt(v, 5) + '" data-v="' + (U.isNum(v) ? v : '') + '" title="dəqiq dəyər: ' + U.inFull(v) + ' · baza: ' + U.inFull(b[i]) + '"></div>';
    });
    return h + '</div><div class="a-tools">Bütün illərə: <input data-pct placeholder="%" inputmode="decimal"> <button type="button" class="btn sm" data-act="pct">% tətbiq et</button>' +
      '<button type="button" class="btn sm ghost" data-act="reset">bərpa et</button>' + (cur ? '<span class="chip warn">dəyişdirilib</span>' : '') + '</div></div>';
  }
  function coefRow(m, c) {
    var key = c.eq_id + '|' + c.name, cur = ov(m).coefficients[key], v = U.isNum(cur) ? cur : c.value;
    var lo = U.isNum(c.ci_low) ? c.ci_low : c.value - 2 * (c.se || Math.abs(c.value) * 0.2 || 0.1), hi = U.isNum(c.ci_high) ? c.ci_high : c.value + 2 * (c.se || Math.abs(c.value) * 0.2 || 0.1);
    var wide = B.out[key], span = (hi - lo) || 1, smin = wide ? lo - 1.5 * span : lo, smax = wide ? hi + 1.5 * span : hi;
    var outside = U.isNum(cur) && U.isNum(c.ci_low) && (cur < c.ci_low || cur > c.ci_high);
    return '<div class="crow' + (U.isNum(cur) ? ' modr' : '') + '" data-co="' + U.esc(key) + '"><div class="c-l"><b>' + U.esc(c.label_az || c.name) + '</b> <code class="small">' + U.esc(c.name) + '</code>' +
      (c.ed === false || c.editable === false ? '<div class="small muted">' + U.esc(c.note_az || 'redaktə edilmir') + '</div>' : '') +
      '<div class="small muted">təxmin <b>' + U.sig(c.value) + '</b> ± ' + U.sig(c.se) + ' (standart xəta) · 95 % EI [' + U.sig(c.ci_low) + '; ' + U.sig(c.ci_high) + ']' + (c.sign_expected ? ' · gözlənilən işarə ' + (c.sign_expected > 0 ? '+' : '−') : '') + '</div></div>' +
      '<div class="c-r"><input type="range" min="' + smin + '" max="' + smax + '" step="' + (span / 200) + '" value="' + v + '"' + (c.editable === false ? ' disabled' : '') + '>' +
      '<input class="cnum" inputmode="decimal" value="' + U.inFmt(v, 4) + '" title="dəqiq dəyər: ' + U.inFull(v) + '"' + (c.editable === false ? ' disabled' : '') + '>' +
      '<label class="small"><input type="checkbox" data-out' + (wide ? ' checked' : '') + (c.editable === false ? ' disabled' : '') + '> interval xaricinə icazə</label>' +
      (U.isNum(cur) ? '<button type="button" class="btn sm ghost" data-act="creset">bərpa</button>' : '') +
      (outside ? '<div class="cwarn">' + U.icon('warn', 14) + ' Dəyər 95 % etibarlılıq intervalından kənardadır — nəticəni ehtiyatla şərh edin.</div>' : '') + '</div></div>';
  }
  function lvFmt(v) { return v == null ? '' : Array.isArray(v) ? v.map(lvFmt).join('; ') : typeof v === 'number' ? U.inFmt(v, 6) : String(v); }
  function lvFull(v) { return v == null ? '' : Array.isArray(v) ? v.map(lvFull).join('; ') : typeof v === 'number' ? U.inFull(v) : String(v); }
  function levRow(m, l) {
    var cur = ov(m).levers, has = Object.prototype.hasOwnProperty.call(cur, l.id), v = has ? cur[l.id] : l.value;
    var opts = l.options || l.choices, isBool = l.type === 'bool' || l.kind === 'bool' || typeof l.value === 'boolean';
    var bl = l.baseline && typeof l.baseline === 'object' && !Array.isArray(l.baseline) ? l.baseline[B.base] : null;
    var ctl;
    if (isBool) ctl = U.seg('lv-' + l.id, [['true', 'bəli'], ['false', 'xeyr']], String(v));
    else if (opts && opts.length) ctl = '<select class="btn sm" data-lv>' + opts.map(function (o) { return U.opt(String(o), U.OPT_AZ[o] || String(o), String(v)); }).join('') + '</select>';
    else ctl = '<input class="cnum" data-lv inputmode="decimal" value="' + U.esc(lvFmt(v)) + '" placeholder="' + U.esc(bl != null ? 'ssenari: ' + lvFmt(bl) : 'boş = baza') + '"' + (lvFmt(v) !== String(v == null ? '' : Array.isArray(v) ? v.join('; ') : v) ? ' title="dəqiq dəyər: ' + U.esc(lvFull(v)) + '"' : '') + '>' + (l.unit ? ' <span class="small muted">' + U.esc(l.unit) + '</span>' : '');
    var desc = l.options_az ? Object.keys(l.options_az).map(function (k) { return '<li><b>' + U.esc(U.OPT_AZ[k] || k) + '</b>: ' + U.esc(l.options_az[k]) + '</li>'; }).join('') : '';
    return '<div class="crow' + (has ? ' modr' : '') + '" data-lvid="' + U.esc(l.id) + '"><div class="c-l"><b>' + U.esc(l.label_az || l.id) + '</b>' + (l.note_az ? '<div class="small muted">' + U.esc(l.note_az) + '</div>' : '') +
      (desc ? '<ul class="small muted" style="margin:4px 0 0;padding-left:16px">' + desc + '</ul>' : '') + '</div><div class="c-r">' + ctl +
      (has ? ' <button type="button" class="btn sm ghost" data-act="lreset">bərpa</button>' : '') + '</div></div>';
  }
  U.bInputsHtml = function () {
    var m = B.mod, I = U.inputsOf(m);
    if (!I) return '<p class="muted">' + m + ' mühərrikinin girişləri tapılmadı' + (((M.INP || {}).errors || {})[m] ? ': ' + U.esc(M.INP.errors[m]) : '') + '.</p>';
    var q = U.fold(B.q || ''), h = '';
    if (B.sec === 'ex') {
      var ex = I.exogenous || [];
      if (m !== 'FR1') h += '<p class="small muted" style="margin:10px 16px">Bu dəyişənlərin əksəriyyəti zəncirdə FR1-dən (və ya yuxarı moduldan) gəlir. Burada dəyişsəniz, həmin yolun üzərinə yazılır.</p>';
      h += ex.filter(function (e) { return !q || U.fold(e.label_az + ' ' + e.id).indexOf(q) >= 0; }).map(function (e) { return exRow(m, e); }).join('') || '<p class="muted pad">Ekzogen dəyişən yoxdur.</p>';
    } else if (B.sec === 'co') {
      // one collapsible group per equation, closed by default (open: changed, filtered, or opened by the user)
      var groups = [], byEq = {}, co = ov(m).coefficients;
      (I.coefficients || []).filter(function (c) { return (!B.onlyEd || c.editable !== false) && (!q || U.fold((c.label_az || '') + ' ' + c.name + ' ' + c.eq_id + ' ' + (c.eq_title_az || '')).indexOf(q) >= 0); }).forEach(function (c) {
        if (!byEq[c.eq_id]) { byEq[c.eq_id] = { id: c.eq_id, t: c.eq_title_az, rows: [] }; groups.push(byEq[c.eq_id]); }
        byEq[c.eq_id].rows.push(c);
      });
      if (groups.length) h += '<div class="toolbar cgrp-tools"><span class="small muted">' + groups.length + ' tənlik · ' + groups.reduce(function (a, g) { return a + g.rows.length; }, 0) + ' əmsal — tənliyi açıb əmsalı dəyişin</span>' +
        '<button type="button" class="btn sm ghost" data-act="co-open">hamısını aç</button><button type="button" class="btn sm ghost" data-act="co-close">hamısını bağla</button></div>';
      groups.forEach(function (g) {
        var e = U.EQI[g.id], nmod = g.rows.filter(function (c) { return U.isNum(co[c.eq_id + '|' + c.name]); }).length, key = m + '|' + g.id;
        var open = q || nmod || (B.coOpen || {})[key];
        h += '<details class="cgrp" data-cg="' + U.esc(key) + '"' + (open ? ' open' : '') + '><summary class="grp-h"><span class="cg-t">' + U.esc(g.t || (e && e.t) || g.id) + '</span>' +
          '<span class="small muted">' + g.rows.length + ' əmsal</span>' + (nmod ? '<span class="chip warn">' + nmod + ' dəyişdirilib</span>' : '') +
          ' <button type="button" class="btn sm ghost" data-eq="' + U.esc(g.id) + '">tənlik ↗</button></summary>' + g.rows.map(function (c) { return coefRow(m, c); }).join('') + '</details>';
      });
      h = h || '<p class="muted pad">Uyğun əmsal yoxdur.</p>';
    } else {
      h += (I.levers || []).map(function (l) { return levRow(m, l); }).join('') || '<p class="muted pad">Alət yoxdur.</p>';
    }
    return h;
  };
  U.bSetEx = function (m, id, arr) {
    var I = U.inputsOf(m), e = (I.exogenous || []).filter(function (x) { return x.id === id; })[0], b = baseOf(e);
    var same = arr.every(function (v, i) { return !U.isNum(v) || Math.abs(v - b[i]) <= 1e-12 * Math.max(1, Math.abs(b[i])); });
    if (same) delete ov(m).exogenous[id]; else ov(m).exogenous[id] = arr.map(function (v, i) { return U.isNum(v) ? v : b[i]; });
  };
  U.bBase = baseOf;
  /* {pct: x} exogenous overrides (API / scenario files) → explicit 2026–2030 paths for the editable cells */
  U.bNorm = function () {
    U.MODS.forEach(function (m) {
      var x = B.ov[m], I = U.inputsOf(m); if (!x || !I) return;
      Object.keys(x.exogenous || {}).forEach(function (id) {
        var v = x.exogenous[id], e = (I.exogenous || []).filter(function (q) { return q.id === id; })[0];
        if (!Array.isArray(v) && v && U.isNum(v.pct) && e) x.exogenous[id] = baseOf(e).map(function (b) { return b * (1 + v.pct / 100); });
      });
    });
  };
  U.bOv = ov;
})();
