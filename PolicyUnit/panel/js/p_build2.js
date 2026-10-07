/* p_build2.js — Ssenari qurucusu, part 2: instrument rows, validation messages, the result view (server run or the
   labelled offline approximation, FR4 fields) and U.bDraw (re-render of the draft). Page: p_build4.js. */
(function () {
  'use strict';
  var U = window.U, B = U.BLD, A = U.API;
  function yrs(it) { return it.years === 'all' ? null : (it.years || []); }
  function row(it, i) {
    var m = U.instr(it.instrument) || { name_az: it.instrument, min: '', max: '' }, t = U.targets(m), ys = yrs(it), y0 = B.s.start_year, out = U.isNum(it.size) && (it.size < m.min || it.size > m.max);
    var yo = function (on) { var o = []; for (var y = y0; y <= 2035; y++) o.push(U.opt(y, y, on)); return o.join(''); };
    return '<div class="irow" data-row="' + i + '"><label>' + U.fam(m.family) + ' ' + U.esc(m.name_az) + '<span class="small muted" style="font-weight:400">' + U.esc(U.UNITN[m.unit] || m.unit) + ' · icazə [' + U.nf(m.min) + '; ' + U.nf(m.max) + '] · standart ' + U.nf(m.default_size) + '</span></label>' +
      '<label>Ölçü<input data-f="size" inputmode="decimal" class="' + (out ? 'bad' : '') + '" value="' + (U.isNum(it.size) ? String(it.size).replace('.', ',') : '') + '"></label>' +
      '<label>İllər: başlanğıc<select data-f="y1"' + (ys ? '' : ' disabled') + '>' + yo(ys ? ys[0] : y0) + '</select></label>' +
      '<label>son<select data-f="y2"' + (ys ? '' : ' disabled') + '>' + yo(ys ? ys[ys.length - 1] : 2035) + '</select><span class="small" style="font-weight:400"><input type="checkbox" data-f="all"' + (ys ? '' : ' checked') + ' style="width:auto;height:auto"> daimi (2035-ə qədər)</span></label>' +
      (t ? '<label>' + U.esc(t[1]) + '<select data-f="target">' + (t[2] ? '' : U.opt('', '— (hamısı / standart)', it.target || '')) + t[0].map(function (o) { return U.opt(o[0], o[1] + ' (' + o[0] + ')', it.target || ''); }).join('') + '</select></label>' : '<label>Hədəf<select disabled><option>tətbiq edilmir</option></select></label>') +
      (U.needsFin(m) ? '<label>Maliyyələşmə<select data-f="financing">' + Object.keys(U.FINN).map(function (k) { return U.opt(k, U.FINN[k], it.financing); }).join('') + '</select></label>' : '<label>Maliyyələşmə<select disabled><option>birbaşa xərc yoxdur</option></select></label>') +
      '<button type="button" class="btn sm ghost" data-act="rm" title="Aləti çıxar" style="align-self:end">✕</button>' +
      '<div class="hint">' + U.esc(m.description_az || '') + ' · mühərriklər: ' + U.ids(m.engines).map(function (e) { return U.ENGS[e] || e; }).join(', ') + '</div></div>';
  }
  function vmsg(r, src) {
    if (!r) return '';
    var h = '<div class="vmsg ' + (r.valid ? (r.warnings && r.warnings.length ? 'warn' : 'ok') : 'bad') + '"><b>' + (r.valid ? 'Ssenari düzgündür' : 'Ssenaridə xəta var') + '</b> <span class="small">(' + U.esc(src) + ')</span>';
    if (r.errors && r.errors.length) h += '<ul>' + r.errors.map(function (e) { return '<li>' + U.esc(e) + '</li>'; }).join('') + '</ul>';
    if (r.warnings && r.warnings.length) h += '<ul>' + r.warnings.map(function (e) { return '<li>' + U.esc(e) + '</li>'; }).join('') + '</ul>';
    return h + (r.engines ? '<div class="small">Tətbiq olunacaq mühərriklər: ' + r.engines.map(function (e) { return U.ENGS[e] || e; }).join(', ') + '</div>' : '') + '</div>';
  }
  function wide(rows) {
    var by = {}; rows.forEach(function (r) { var o = by[r.indicator] = by[r.indicator] || { label_az: r.label_az, effect_unit: r.effect_unit }; o[r.horizon] = r.effect; });
    return Object.keys(by).map(function (k) { var o = by[k]; return { indicator: k, label_az: o.label_az, 'qısa': o['qısa'], 'orta': o['orta'], 'uzun': o['uzun'], effect_unit: o.effect_unit }; });
  }
  var WC = [{ k: 'indicator', l: 'Kod', f: function (x) { return U.gl(x); } }, { k: 'label_az', l: 'Göstərici' }, { k: 'qısa', l: 'Qısa', n: 1, d: 3 }, { k: 'orta', l: 'Orta', n: 1, d: 3 }, { k: 'uzun', l: 'Uzun', n: 1, d: 3 }, { k: 'effect_unit', l: 'Vahid' }];
  function result() {
    var r = B.res; if (!r) return '';
    if (r.approx) {
      var a = r.approx;
      return '<div class="note-w"><b>Oflayn təqribi baxış — dəqiq nəticə deyil.</b> Paketdəki tək alətli ssenarilərin nəticələri ölçü nisbətində xətti miqyaslanıb və cəmlənib (' + a.parts.map(function (p) { return U.esc(p.ref.name) + ' × ' + U.nf(p.k, 2); }).join('; ') + '). Qeyri-xəttilik, il fərqləri və alətlərin qarşılıqlı təsiri nəzərə alınmır.' + (a.miss.length ? ' Nümunəsi olmayan alətlər nəzərə alınmayıb: ' + U.esc(a.miss.join(', ')) + '.' : '') + ' Dəqiq hesablama üçün serveri başladın.</div>' +
        (a.rows.length ? U.dt('b-apx', wide(a.rows), WC, { title: 'Təqribi əsas göstəricilər (bazadan fərq)', file: 'teqribi_baxis' }) : '');
    }
    var se = (r.side_effects || {}).items || [], hw = r.headline_wide || wide(r.headline || []);
    return '<div class="vmsg ok"><b>Hesablama bitdi</b> · ' + U.nf(r.seconds, 1) + ' s' + (r.cached ? ' · keşdən' : '') + (r.run_id ? ' · iş ' + U.esc(r.run_id) : '') + '</div>' +
      (r.text_az ? '<div class="expl">' + U.esc(r.text_az) + '</div>' : '') +
      U.dt('b-hw', hw, WC, { title: 'Əsas göstəricilər (bazadan fərq)', file: 'ssenari_neticeleri' }) +
      (r.engines ? U.dt('b-eng', r.engines, [{ k: 'label_az', l: 'Mühərrik' }, { k: 'status', l: 'Vəziyyət', f: function (x) { return U.sigchip(x); } }, { k: 'rows', l: 'Sətir', n: 1 }, { k: 'seconds', l: 'Vaxt, s', n: 1 }, { k: 'message_az', l: 'Mesaj' }], { title: 'Mühərriklər', bare: true }) : '') +
      (se.length ? U.dt('b-se', se, [{ k: 'severity_az', l: 'Ciddilik', f: function (x, o) { return '<span class="sev s' + o.severity + '">' + U.esc(x) + '</span>'; } }, { k: 'name_az', l: 'Yan təsir' }, { k: 'explanation_az', l: 'İzah' }, { k: 'variant_name_az', l: 'Şərt', f: function (x, o) { return U.esc(x || (o.variant === 'base' ? 'əsas ssenari' : o.variant)); } }], { title: 'Yan təsirlər (FR4)' }) : '') +
      U.fr4Live(r.side_effects || {}) + ((r.warnings || []).length ? '<div class="note-w">' + r.warnings.map(U.esc).join('<br>') + '</div>' : '');
  }
  U.MENBE = 'Risk göstəricisinin əsas mənbəyi: «RiskUnit» — siyasət sürüşməsi RiskUnit modelinin öz zəncirindən (dəqiq); «PolicyUnit sürüşməsi» — RiskUnit bu alətin kanalını görmədikdə (overlay / proksi) PolicyUnit-in hesabladığı təsir RiskUnit paylanmasına əlavə olunur (çarpaz yoxlama).';
  U.fr4Live = function (se) {
    var h = '', V = se.variants || [], rp = (se.risk_profile || {}).rows || [], st = se.status_detail || {};
    if (V.length) h += U.dt('b-var', V, [{ k: 'variant_name_az', l: 'Şərt' }, { k: 'label_az', l: 'Göstərici' }, { k: 'horizon', l: 'Müddət' }, { k: 'effect_base', l: 'Əsas təsir', n: 1, d: 3 }, { k: 'effect_variant', l: 'Şərtlə təsir', n: 1, d: 3 }, { k: 'change', l: 'Dəyişmə', n: 1, d: 3 }, { k: 'effect_unit', l: 'Vahid' }], { title: 'Avtomatik yan təsir ssenariləri' + (se.variant_ids ? ' (' + se.variant_ids.length + ')' : ''), file: 'yan_tesir_ssenarileri' });
    if (rp.length) h += U.dt('b-rp', rp, [{ k: 'variant_name_az', l: 'Şərt' }, { k: 'indicator_az', l: 'Göstərici' }, { k: 'year', l: 'İl', n: 1 }, { k: 'threshold', l: 'Hədd' }, { k: 'P_without', l: 'Siyasətsiz', p: 1, d: 1 }, { k: 'P_with', l: 'Siyasətlə', p: 1, d: 1 }, { k: 'esas_menbe', l: 'Əsas mənbə' }], { title: 'Risk profili (RiskUnit)', note: U.MENBE, file: 'risk_profili' });
    if ((se.esas_menbe || []).length) h += '<p class="small"><b>Əsas mənbələr:</b> ' + se.esas_menbe.map(U.esc).join('; ') + ' <span class="muted">— ' + U.MENBE + '</span></p>';
    var sd = Object.keys(st); if (sd.length) h += '<p class="small muted"><b>FR4 mərhələləri:</b> ' + sd.map(function (k) { return U.esc(k) + ': ' + U.esc(typeof st[k] === 'object' ? JSON.stringify(st[k]) : st[k]); }).join(' · ') + '</p>';
    return h;
  };
  U.bDraw = function (v) {
    var s = B.s, chk = U.bCheck(s), on = A.live();
    U.$('#b-rows', v).innerHTML = s.instruments.length ? s.instruments.map(row).join('') : '<p class="muted">Hələ alət yoxdur — yuxarıdakı siyahıdan alət seçin və «Əlavə et» düyməsini basın.</p>';
    U.$('#b-eng', v).innerHTML = U.bEngines(s).map(function (e) { return '<span class="chip" style="color:' + U.ENGC[e] + '">' + U.esc(U.ENG[e] || e) + '</span>'; }).join(' ') || '<span class="muted small">—</span>';
    U.$('#b-val', v).innerHTML = B.val ? vmsg(B.val, B.val.src) : (chk.errors.length && s.instruments.length ? vmsg(chk, 'brauzerdə yoxlama') : '');
    U.$('#b-res', v).innerHTML = result();
    U.$('#b-run', v).textContent = on ? 'Hesabla (saxlamadan)' : 'Təqribi baxış (oflayn)';
    var idb = U.$('#b-idv', v); if (idb) idb.textContent = s.id; var nm = U.$('#b-name', v); if (nm && !s.nameManual && document.activeElement !== nm) nm.value = s.name_az;
  };
})();
