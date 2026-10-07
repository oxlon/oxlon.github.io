/* p_extra.js — additions shared by several pages: method ranges (P1_ranges: low / core / high with the explanation,
   e.g. the minimum-wage three-point range), long-run continuity checks (P1_longrun_continuity), the «ETİBARSIZ» flag
   of CAEM tax-fiscal rows, model-instability regions (P4_instability) and NFR1 tolerance sensitivity. */
(function () {
  'use strict';
  var U = window.U;
  U.ENG.riskfx = 'RiskUnit məzənnə ötürmə modeli (devalvasiya → İQİ)'; U.ENGS.riskfx = 'RiskUnit FX'; U.ENGC.riskfx = '#B3261E';
  U.ENG.microsim_spill = 'Mikrosimulyasiya (yuxarı maaşlara ötürmə ilə)'; U.ENGS.microsim_spill = 'Mikrosim. + ötürmə';
  U.VMAP.naive_rule = { prev: 'əvvəlki ilin nəticəsi', zero: 'sıfır təsir', io_direct: 'birbaşa IO ötürməsi', prev_d: 'əvvəlki ilin dəyişməsi', shock: 'tam mexaniki ötürmə', 'const': 'sabit' };
  U.BAD = function (s) { return /ETİBARSIZ/.test(String(s || '')); };
  U.noteFmt = function (x) { if (!x) return '<span class="muted">—</span>'; return (U.BAD(x) ? '<span class="chip bad" title="CAEM bu alətin vergi-fiskal kanalını düzgün ötürmür — müqayisə üçün istifadə etməyin">ETİBARSIZ</span> ' : '') + U.esc(x); };
  U.rangeSec = function (sc, only) {
    var R = U.T('P1_ranges').filter(function (r) { return r.scenario === sc && (!only || only.test(r.indicator)); });
    if (!R.length) return '';
    var mw = /^mw|min_wage/.test(sc) || (U.scen(sc) || { ins: [] }).ins.some(function (i) { return i.instrument === 'min_wage'; });
    return U.sec('Metodlar arası diapazon', (mw ? 'minimum əmək haqqı: üç nöqtə — mikrosimulyasiya (statik döşəmə), ötürmə ilə mikrosimulyasiya və MikroUnit (makro reaksiya)' : 'eyni göstəricinin müxtəlif metodlarla aşağı və yuxarı qiyməti'),
      '<div class="expl">Bir rəqəm əvəzinə <b>diapazon</b>: aşağı və yuxarı sərhəd müxtəlif metodlardan gəlir, «əsas» — MikroUnit zənciri. Geniş diapazon — nəticənin metod seçiminə həssas olduğunu göstərir; izah hər sətirdədir.</div>' +
      U.dt('rg-' + (only ? 'o' : 'a'), R, [{ k: 'label_az', l: 'Göstərici' }, { k: 'horizon', l: 'Müddət' }, { k: 'low', l: 'Aşağı', n: 1, d: 3 }, { k: 'low_method', l: 'metod', f: function (x) { return U.esc(U.ENGS[x] || x || ''); } }, { k: 'core_micro', l: 'Əsas (MikroUnit)', n: 1, d: 3 }, { k: 'high', l: 'Yuxarı', n: 1, d: 3 }, { k: 'high_method', l: 'metod', f: function (x) { return U.esc(U.ENGS[x] || x || ''); } }, { k: 'effect_unit', l: 'Vahid' }, { k: 'n_methods', l: 'Metod', n: 1 }, { k: 'excluded_az', l: 'Kənarlaşdırılan', f: function (x) { return x ? '<span class="chip bad" title="diapazona daxil edilməyib">ETİBARSIZ</span> ' + U.esc(x) : '<span class="muted">—</span>'; } }, { k: 'explanation_az', l: 'İzah' }], { title: 'Diapazonlar — ' + U.sname(sc), file: 'diapazon_' + sc, lim: 40 }));
  };
  U.continuity = function () {
    var C = U.T('P1_longrun_continuity'); if (!C.length) return '';
    var bad = C.filter(function (r) { return !(r.ok === true || r.ok === 'True'); }).length;
    return U.sec('Uzun müddətə keçidin fasiləsizliyi', '2030 (MikroUnit) → 2031 (struktur ekstrapolyasiya) addımı hədd daxilindədirmi; uyğunsuz: ' + bad + ' / ' + C.length,
      U.dt('m-cont', C.map(function (r) { return Object.assign({ name: U.sname(r.scenario) }, r); }), [{ k: 'name', l: 'Ssenari' }, { k: 'indicator', l: 'Göstərici' }, { k: 'measure', l: 'Ölçü' }, { k: 'v2029', l: '2029', n: 1, d: 3 }, { k: 'v2030', l: '2030', n: 1, d: 3 }, { k: 'v2031', l: '2031', n: 1, d: 3 }, { k: 'step_2030_31', l: 'Addım 2030→31', n: 1, d: 3 }, { k: 'limit', l: 'Hədd', n: 1 }, { k: 'ok', l: 'Uyğun', f: function (x) { return x === true || x === 'True' ? '<span class="chip acc">bəli</span>' : '<span class="chip bad">xeyr</span>'; } }], { title: 'P1 uzun müddət fasiləsizliyi', file: 'P1_longrun_continuity', lim: 40 }));
  };
  U.instab = function (v, sc) {
    var I = U.T('P4_instability').filter(function (r) { return r.scenario === sc; }).sort(function (a, b) { return b.share_rejected_all - a.share_rejected_all; });
    if (!I.length) return;
    var w = I[0].worst_region_az, sh = I[0].share_rejected_all, top = I.slice().sort(function (a, b) { return Math.max(b.reject_rate_z_gt_1 || 0, b['reject_rate_z_lt_-1'] || 0) - Math.max(a.reject_rate_z_gt_1 || 0, a['reject_rate_z_lt_-1'] || 0); }).slice(0, 10);
    v.insertAdjacentHTML('beforeend', U.sec('Modelin qeyri-sabitlik bölgəsi', 'həssaslıq çəkilişlərindən hansıları modeli qeyri-sabit edir (rədd edilir)',
      '<div class="expl">Həssaslıq təhlilində əmsallar standart xəta (SE) daxilində dəyişdirilir. Bəzi birləşmələrdə model zənciri <b>qeyri-sabit</b> olur (dəyərlər partlayır) və həmin çəkilişlər rədd edilir. Bütün çəkilişlərin <b>' + U.pct(sh, 1) + '</b>-i rədd edilib. Ən qeyri-sabit bölgə: ' + U.esc(w || '—') + '. Bu bölgədə nəticələrə etibar azdır; əmsallar bu istiqamətdə dəyişərsə (məs. yeni qiymətləndirmə), yenidən yoxlanılmalıdır.</div>' +
      '<div class="cols2"><div class="card pad"><h3>Rədd payı əmsala görə (|z| > 1)</h3><div id="ins-ch" class="ch"></div></div><div>' +
      U.dt('r-ins', I, [{ k: 'factor_label_az', l: 'Parametr' }, { k: 'value', l: 'Dəyər', n: 1, d: 3 }, { k: 'se', l: 'SE', n: 1, d: 3 }, { k: 'reject_rate_z_gt_1', l: 'z > +1', p: 1, d: 1 }, { k: 'reject_rate_z_lt_-1', l: 'z < −1', p: 1, d: 1 }, { k: 'mean_z_rejected', l: 'Orta z (rədd)', n: 1, d: 2 }, { k: 'n_rejected', l: 'Rədd', n: 1 }, { k: 'n_draws', l: 'Çəkiliş', n: 1 }], { title: 'Qeyri-sabitlik (P4_instability)', file: 'P4_instability' }) + '</div></div>'));
    U.barH(U.$('#ins-ch', v), top.map(function (r) { return r.factor_label_az; }), null, 'rədd edilən çəkilişlərin payı', { sets: [{ name: 'z > +1', v: top.map(function (r) { return r.reject_rate_z_gt_1; }), c: '#B3261E' }, { name: 'z < −1', v: top.map(function (r) { return r['reject_rate_z_lt_-1']; }), c: '#1F6FB2' }] });
  };
  U.msStatus = function (sc) {
    var S = U.T('P3_microsim_status'); if (!S.length) return '';
    var bad = S.filter(function (r) { return r.status !== 'ok'; }).length;
    return U.sec('Mikrosimulyasiyanın icra vəziyyəti', 'hər ssenari üçün: vəziyyət, ötürmə kanalı, sətir sayı' + (bad ? ' · problemli: ' + bad : ''), U.dt('o-st', S, [{ k: 'scenario_name', l: 'Ssenari', f: function (x, o) { return (o.scenario === sc ? '<b>' : '') + U.esc(x) + (o.scenario === sc ? '</b>' : ''); } }, { k: 'status', l: 'Vəziyyət', f: function (x) { return U.sigchip(x); } }, { k: 'channel', l: 'Kanal' }, { k: 'rows', l: 'Sətir', n: 1 }, { k: 'message_az', l: 'Mesaj' }], { title: 'P3_microsim_status', file: 'P3_microsim_status' }));
  };
  U.fresh = function () {
    var F = U.T('P1_freshness'); if (!F.length) return '';
    var bad = F.filter(function (r) { return r.status !== 'ok'; }).length;
    return U.sec('Vintaj və təzəlik yoxlaması', 'bütün girişlər eyni (cari) vintajdandırmı' + (bad ? ' · diqqət: ' + bad : ' · hamısı ok'), U.dt('m-fr', F, [{ k: 'check', l: 'Yoxlama' }, { k: 'status', l: 'Vəziyyət', f: function (x) { return U.sigchip(x); } }, { k: 'message_az', l: 'Mesaj' }], { title: 'P1_freshness', file: 'P1_freshness' }));
  };
  U.CONS_TXT = 'Ehtiyatlı reytinq: hər təsir KPI-ı metodlar arası diapazonun ən əlverişsiz sərhədi ilə götürülür (P1_ranges) — metodlar razılaşmayanda ssenari geri düşür.';
  U.tolSens = function () {
    var T = U.T('V_nfr1_tolerance_sensitivity'); if (!T.length) return '';
    var sets = U.uniq(T.map(function (r) { return r.tol_set; })), ev = U.uniq(T.map(function (r) { return r.event_id; }));
    var M = ev.map(function (e) { var o = { event: e }; sets.forEach(function (s) { var r = T.filter(function (x) { return x.event_id === e && x.tol_set === s; })[0]; o[s] = r ? r.verdict_az : ''; }); return o; });
    return U.sec('Hökmlərin tolerantlıq qaydasına həssaslığı', 'qatı / təklif olunan / yumşaq qaydalar — hökm qayda seçimindən asılıdırmı',
      U.dt('v-ts', M, [{ k: 'event', l: 'Hadisə' }].concat(sets.map(function (s) { return { k: s, l: s, f: function (x) { return U.sigchip(x); } }; })), { title: 'Hökmlər qaydalara görə', bare: true }) +
      U.dt('v-tsf', T, [{ k: 'tol_set', l: 'Qayda dəsti' }, { k: 'event_id', l: 'Hadisə' }, { k: 'n_ok', l: 'Uyğun', n: 1 }, { k: 'n_part', l: 'Qismən', n: 1 }, { k: 'n_fail', l: 'Uyğunsuz', n: 1 }, { k: 'n_low_power', l: 'Aşağı güc', n: 1 }, { k: 'primary_mean_score', l: 'Orta bal', n: 1, d: 2 }, { k: 'verdict_az', l: 'Hökm', f: function (x) { return U.sigchip(x); } }, { k: 'params', l: 'Parametrlər' }], { title: 'V_nfr1_tolerance_sensitivity', file: 'V_nfr1_tolerance_sensitivity' }));
  };
})();
