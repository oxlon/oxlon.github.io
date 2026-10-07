/* p_build4.js — Ssenari qurucusu, part 4: the page. «Mövcud ssenarilər» list (run / open / copy / compare in one click),
   the draft with an auto-generated code, the grouped searchable instrument picker (family → instrument with unit, range,
   default, description, engines), «Hesabla (saxlamadan)», and the «Kataloqlar» tab: instrument catalogue + glossary of
   every output variable (codes anywhere in the panel link here: U.gl). */
(function () {
  'use strict';
  var U = window.U, B = U.BLD, A = U.API;
  var SUB = [['', 'Qurucu'], ['kataloq', 'Kataloqlar: alətlər və göstəricilər']];
  var GL = null;
  U.glossary = function () { if (!GL) { GL = {}; U.T('glossary').forEach(function (r) { GL[r.indicator] = r; }); } return GL; };
  U.gl = function (code) {
    if (code == null || code === '') return '<span class="muted">—</span>';
    var g = U.glossary()[code];
    return '<a class="glk" href="#/qurucu/kataloq?g=' + U.enc(code) + '" title="' + U.esc(g ? g.label_az + (g.unit ? ' · ' + g.unit : '') + ' · ' + g.area : 'lüğətdə axtar') + '"><code>' + U.esc(code) + '</code></a>';
  };
  function picker() {
    var q = U.fold(B.pq || ''), by = U.by(U.T('cfg_instruments').filter(function (r) { return !q || U.fold(r.name_az + ' ' + r.description_az + ' ' + r.family).indexOf(q) >= 0; }), 'family');
    var cur = B.pick && U.instr(B.pick) ? B.pick : null;
    return '<div class="pick"><input type="search" id="b-pq" placeholder="alət axtar (məs. ƏDV, pensiya, tarif)…" value="' + U.esc(B.pq || '') + '" aria-label="Alət axtar">' +
      '<select id="b-pick" class="btn" aria-label="Siyasət aləti"><option value="">— alət seçin (' + U.T('cfg_instruments').length + ') —</option>' + Object.keys(by).map(function (f) { return '<optgroup label="' + U.esc(f) + '">' + by[f].map(function (r) { return U.opt(r.id, r.name_az + ' · ' + (U.UNITN[r.unit] || r.unit), cur); }).join('') + '</optgroup>'; }).join('') + '</select>' +
      '<button type="button" class="btn pri" id="b-addp"' + (cur ? '' : ' disabled') + '>Əlavə et</button></div><div id="b-pinfo">' + info(cur) + '</div>';
  }
  function info(id) {
    var m = id && U.instr(id); if (!m) return '<p class="small muted">Siyahıdan alət seçin — burada vahidi, icazə verilən aralığı, standart ölçünü, izahı və hansı modellərin onu hesabladığını görəcəksiniz.</p>';
    return '<div class="card pad" style="margin-top:6px">' + U.fam(m.family) + ' <b>' + U.esc(m.name_az) + '</b><div class="small" style="margin-top:4px">' + U.esc(m.description_az || '') + '</div>' +
      U.kv([['Vahid', U.esc(U.UNITN[m.unit] || m.unit)], ['İcazə verilən aralıq', '[' + U.nf(m.min) + '; ' + U.nf(m.max) + ']'], ['Standart ölçü', U.nf(m.default_size)], ['Hesablayan modellər', U.ids(m.engines).map(function (e) { return U.esc(U.ENG[e] || e); }).join(', ')], ['Birbaşa fiskal xərc', m.cost_rule && m.cost_rule !== 'none' ? 'var (maliyyələşmə seçilir)' : 'yoxdur']]) + '</div>';
  }
  function form() {
    var s = B.s;
    return '<div class="form" style="grid-template-columns:repeat(auto-fit,minmax(220px,1fr))"><label>Ssenarinin adı<input id="b-name" value="' + U.esc(s.name_az) + '" placeholder="alət seçdikdə avtomatik doldurulur"></label>' +
      '<label>Başlanğıc il<select id="b-start" class="btn">' + [2026, 2027, 2028, 2029, 2030].map(function (y) { return U.opt(y, y, s.start_year); }).join('') + '</select></label>' +
      '<label>Teqlər (istəyə görə, vergüllə)<input id="b-tags" value="' + U.esc((s.tags || []).join(', ')) + '"></label></div>' +
      '<p class="small" style="margin:6px 0">Kod: <code id="b-idv">' + U.esc(s.id) + '</code> <span class="muted">— ssenarinin fayl adı / identifikatoru; alətlərdən və başlanğıc ildən avtomatik yaranır.</span> ' +
      (s.idManual ? '<input id="b-id" value="' + U.esc(s.id) + '" class="dt-q" style="width:220px" aria-label="Kod"> <a href="#" id="b-idauto">avtomatik</a>' : '<a href="#" id="b-idedit">kodu dəyiş</a>') + '</p>' +
      '<div class="form"><label>Təsvir (istəyə görə)<textarea id="b-desc" rows="2">' + U.esc(s.description_az) + '</textarea></label></div>';
  }
  function catalogs(v) {
    var g = U.HQ.get('g');
    if (g) U.DT['k-gl'] = { q: g };
    var I = U.T('cfg_instruments').map(function (r) { return Object.assign({ range: '[' + U.nf(r.min) + '; ' + U.nf(r.max) + ']', unitl: U.UNITN[r.unit] || r.unit, eng: U.ids(r.engines).map(function (e) { return U.ENGS[e] || e; }).join(', ') }, r); });
    v.insertAdjacentHTML('beforeend', '<div class="expl">Panelin hər yerində görünən kodları burada tapın: <b>alətlər</b> (ssenaridə nə dəyişdirilir) və <b>göstəricilər</b> (nəticələrdə nə ölçülür). Cədvəlləri süzün, CSV və ya Excel kimi yükləyin.</div>' +
      U.dt('k-ins', I, [{ k: 'id', l: 'Kod', f: function (x) { return '<code>' + U.esc(x) + '</code>'; } }, { k: 'name_az', l: 'Ad' }, { k: 'family', l: 'Ailə' }, { k: 'unitl', l: 'Vahid' }, { k: 'range', l: 'Aralıq' }, { k: 'default_size', l: 'Standart ölçü', n: 1 }, { k: 'eng', l: 'Mühərriklər' }, { k: 'description_az', l: 'İzah' }, { k: 'id', l: '', f: function (x) { return '<a class="btn sm" href="#/qurucu?i=' + U.enc(x) + '">Ssenariyə əlavə et</a>'; } }], { title: 'Siyasət alətləri kataloqu (config/instruments.csv)', file: 'aletler_kataloqu' }) +
      U.dt('k-gl', U.T('glossary'), [{ k: 'indicator', l: 'Kod', f: function (x) { return '<code>' + U.esc(x) + '</code>'; } }, { k: 'label_az', l: 'Göstərici' }, { k: 'unit', l: 'Vahid' }, { k: 'area', l: 'Sahə (FR)' }, { k: 'engines', l: 'Mühərriklər', f: function (x) { return U.esc(U.ids(x).map(function (e) { return U.ENGS[e] || e; }).join(', ')); } }, { k: 'files', l: 'Çıxış faylları' }], { title: 'Nəticə göstəriciləri lüğəti (kod → ad, vahid, sahə)', file: 'gostericiler_lugeti', lim: 100 }));
  }
  U.pages.qurucu = function (v, p) {
    var sub = p[1] || '', q = U.HQ.get('from'), add = U.HQ.get('i');
    v.innerHTML = U.head('NFR4 — yeni ssenari konfiqurasiya ilə, proqramlaşdırmasız', 'Ssenari qurucusu', 'Mövcud ssenarini bir kliklə hesablayın və ya yenisini qurun: siyahıdan alət seçin, ölçünü (bazaya nisbətən), illəri, hədəfi və maliyyələşməni göstərin. Kod və ad avtomatik yaranır; saxlamaq məcburi deyil.') + U.subtabs('qurucu', SUB, sub) + '<div id="b-body"></div>';
    var b = U.$('#b-body', v);
    if (sub === 'kataloq') { catalogs(b); return; }
    if (q && U.scen(q)) { var sc = U.scen(q); U.bLoad({ id: sc.id, name_az: sc.name, description_az: sc.desc, start_year: sc.start, instruments: sc.ins, tags: sc.tags }, true); history.replaceState(null, '', '#/qurucu'); }
    if (add) { U.bAdd(add); history.replaceState(null, '', '#/qurucu'); }
    U.bSync();
    b.innerHTML = (A.mode() === 'brauzer' ? A.browserHtml('yeni ssenarinin hesablanması') : A.mode() === 'paket' ? A.offlineHtml('Yeni ssenarinin serverdə hesablanması və saxlanması') : '') + '<div id="b-list"></div>' +
      '<div class="card pad" style="margin-top:14px"><h3>Yeni ssenari</h3>' + '<h4>1. Siyasət alətləri</h4><div id="b-picker">' + picker() + '</div><div id="b-rows"></div>' +
      '<h4>2. Ad və başlanğıc il</h4>' + form() + '<h4>Tətbiq olunacaq metodlar</h4><div id="b-eng"></div>' +
      '<div class="toolbar"><button class="btn pri" id="b-run">Hesabla (saxlamadan)</button><button class="btn" id="b-chk">Yoxla</button><button class="btn" id="b-save">Qaralama kimi saxla</button>' + (!A.online ? '' : '<button class="btn ghost" id="b-off">Rəsmi ssenari kimi saxla</button>') +
      '<button class="btn ghost" id="b-dup">Surət</button><button class="btn ghost" id="b-json">JSON yüklə</button><label class="btn ghost">JSON idxal<input type="file" id="b-imp" accept=".json" hidden></label><button class="btn ghost" id="b-new">Yeni (təmizlə)</button></div>' +
      '<div id="b-val"></div></div><div id="b-res"></div>';
    U.bList(v); U.bDraw(v);
    var repick = function () { U.$('#b-picker', v).innerHTML = picker(); var i = U.$('#b-pq', v); i.focus(); i.setSelectionRange(i.value.length, i.value.length); };
    v.oninput = function (e) {
      var t = e.target, r = t.closest('[data-row]');
      if (t.id === 'b-pq') { B.pq = t.value; repick(); return; }
      if (r && t.dataset.f === 'size') { var it = B.s.instruments[+r.dataset.row], m = U.instr(it.instrument); it.size = U.parseNum(t.value); t.classList.toggle('bad', !U.isNum(it.size) || it.size < m.min || it.size > m.max); B.val = null; U.bSave(); U.$('#b-idv', v).textContent = B.s.id; if (!B.s.nameManual) U.$('#b-name', v).value = B.s.name_az; return; }
      if (t.id === 'b-name') { B.s.name_az = t.value; B.s.nameManual = !!t.value.trim(); } else if (t.id === 'b-id') B.s.id = t.value.trim(); else if (t.id === 'b-desc') B.s.description_az = t.value; else if (t.id === 'b-tags') B.s.tags = U.ids(t.value); else return;
      B.val = null; U.bSave();
    };
    v.onchange = function (e) {
      var t = e.target, r = t.closest('[data-row]');
      if (t.id === 'b-pick') { B.pick = t.value; U.$('#b-pinfo', v).innerHTML = info(B.pick); U.$('#b-addp', v).disabled = !B.pick; return; }
      if (t.id === 'b-start') { B.s.start_year = +t.value; B.s.instruments.forEach(function (it) { if (it.years !== 'all') it.years = (it.years || []).filter(function (y) { return y >= B.s.start_year; }); if (it.years !== 'all' && !it.years.length) it.years = [B.s.start_year]; }); }
      else if (t.id === 'b-imp' && t.files[0]) { var fr = new FileReader(); fr.onload = function () { try { U.bLoad(JSON.parse(fr.result), false); U.toast('Ssenari idxal edildi'); } catch (er) { U.toast('JSON oxunmadı: ' + er.message); } U.route(true); }; fr.readAsText(t.files[0]); return; }
      else if (r) {
        var it = B.s.instruments[+r.dataset.row], f = t.dataset.f;
        if (f === 'all') it.years = t.checked ? 'all' : [B.s.start_year];
        else if (f === 'y1' || f === 'y2') { var a = +U.$('[data-f=y1]', r).value, c = +U.$('[data-f=y2]', r).value, ys = []; for (var y = Math.min(a, c); y <= Math.max(a, c); y++) ys.push(y); it.years = ys; }
        else if (f === 'target') it.target = t.value || null; else if (f === 'financing') it.financing = t.value || null; else return;
      } else return;
      B.val = null; U.bSave(); U.bDraw(v);
    };
    v.onclick = function (e) {
      var t = e.target.closest('#b-addp,#b-idedit,#b-idauto');
      if (t && t.id === 'b-addp') { if (B.pick) { U.bAdd(B.pick); U.bSave(); U.bDraw(v); U.toast('Alət əlavə edildi: ' + U.instr(B.pick).name_az); } return; }
      if (t) { e.preventDefault(); B.s.idManual = t.id === 'b-idedit'; U.bSave(); U.route(true); return; }
      U.bClick(e, v, U.bDraw);
    };
  };
})();
