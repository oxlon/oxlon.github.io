"""FR3 v2.3.6 Azerbaijani prose blocks (decimal comma; suffix-free phrasing after run-dependent numbers)."""
from .common import az, azm, azpm, az_poss, az_abl, RefreshError

NM = ['orta əmək haqqı', 'qeyri-neft sektoru əmək haqqı', 'özəl sektor əmək haqqı', 'dövlət sektoru əmək haqqı',
      'neft sektoru əmək haqqı']
_YS = {0: 'cu', 1: 'ci', 2: 'ci', 3: 'cü', 4: 'cü', 5: 'ci', 6: 'cı', 7: 'ci', 8: 'ci', 9: 'cu'}


def yr(y):
    if y % 100 >= 40 or (y % 10 == 0 and y % 100 not in (20, 30)):
        raise RefreshError(f'FR3 AZ doc: no ordinal suffix rule for {y}')
    return f"{y}-{_YS[y % 10] if y % 10 else ('ci' if y % 100 == 20 else 'cu')}"


def _and(ix):
    w = [NM[i] for i in ix]
    return w[0] if len(w) == 1 else ', '.join(w[:-1]) + ' və ' + w[-1]


def loc(n):
    return 'heç birində' if n == 0 else az_poss(n) + 'ndə'


def abl(x):
    return az_abl(int(round(abs(x) * 100)) % 100 or 10).split('-')[1]


def p_(p):
    return az(p, 3) if p < 0.01 else az(p, 2)


def blocks(V, C):
    B = {}
    a, o = C['avg'], C['oil']
    poor = 'zəifdir' if C['ncg'] <= 1 else 'qarışıq nəticə verir'
    y1, yN = C['y1'], C['yN']
    cg = (f"sabit artımdan isə {loc(C['ncg'])} üstündür, lakin {_and(C['cg_not'])} üzrə yox" if C['ncg']
          else 'sabit artımdan isə heç birində üstün deyil')
    B['head'] = (f"{y1}–{yr(yN)} illərdə Əsas ssenari üzrə orta əmək haqqının artımı **nominal ifadədə ildə\n"
                 f"{azpm(C['nom'])}%, real ifadədə {azpm(C['real'])}%** təşkil edir (ilk versiyada +5,26% / +1,19%). Proqnozun öz "
                 f"lövbərləmə qaydası ilə 2021–2025\nnümunədən kənar yoxlama **sabit artımla müqayisədə {poor}**: model 5 sıranın "
                 f"{loc(C['nrw'])} təsadüfi gəzişmədən, {cg} (orta əmək haqqı: təsadüfi gəzişməyə qarşı Theil U "
                 f"{az(a['U vs random walk'])}, sabit artıma qarşı {az(a['U vs const growth'])};\n2025-ci ilədək səviyyə xətası "
                 f"{azpm(a.err_2025, 1)}%).")
    B['bill26'] = f"{azpm(C['wbg'], 1)}% artır, yəni əmək haqqı artımı ({azpm(C['wg1'], 1)}%)"
    lo, hi, cv = V['gh']
    B['gh'] = (f"ADF* {azm(hi)}-{abl(hi)} {azm(lo)}-dək,\n5% kritik qiymətləri isə "
               f"{' / '.join(azm(x) for x in sorted(cv, reverse=True))}")
    sel = V['sel'].set_index(['group', 'candidate'])
    r0 = sel.loc[('E3', 'prod_non')].rolling_RMSE
    r = {c: sel.loc[('E3', c)] for c in ['prod_non + w_oil', 'prod_non + w_state', 'ratio: prod_non + mw']}
    c, p = V['spill_sp']
    st = ' — daha yaxşı deyil və daha mürəkkəbdir' if r['prod_non + w_state'].rolling_RMSE >= r0 else ''
    B['spill'] = '\n'.join([
        f"- Özəl sektor əmək haqqında **neft sektoru əmək haqqı (\"Holland xəstəliyi\")**: sürüşən RMSE {az(r['prod_non + w_oil'].rolling_RMSE)}%, "
        f"seçilmiş tənlikdə isə {az(r0)}% (DM p = {p_(r['prod_non + w_oil'].DM_p)}).",
        f"- **Dövlət sektoru əmək haqqının özəl sektor əmək haqqına ötürülməsi**: {az(r['prod_non + w_state'].rolling_RMSE)}%, seçilmiş "
        f"tənlikdə isə {az(r0)}% (DM p = {p_(r['prod_non + w_state'].DM_p)}){st}.",
        f"- **Özəl/dövlət nisbət modeli**: {az(r['ratio: prod_non + mw'].rolling_RMSE)}%, seçilmiş tənlikdə isə {az(r0)}% "
        f"(DM p = {p_(r['ratio: prod_non + mw'].DM_p)}).",
        f"- **Özəl sektor əmək haqqının dövlət sektoru əmək haqqına ötürülməsi** (OLS səviyyələri, fiskal imkanlar və minimum hədd ilə): "
        f"{azpm(c, 3)}, p = {az(p, 3)}."])
    B['p1'] = f"**{az(V['p1'])}** təşkil edir"
    Fs, Fw = V['iv_strongF'], V['iv_weakF']
    eqn = dict(E1='orta əmək haqqı', E2='qeyri-neft sektoru əmək haqqı', E3='özəl sektor əmək haqqı', E4='dövlət sektoru əmək haqqı')
    dw = V['dwh']
    B['dwh'] = (f"({Fs[2]} hal, birinci mərhələ F {Fs[0]:.0f}–{Fs[1]:.0f}: D18-siz dörd tənliyin hamısı) **Durbin–Wu–Hausman testi "
                f"{Fs[2]} halın\n{loc(len(dw))} ekzogenliyi rədd edir** (" + '; '.join(f"{eqn[e]}, p = {az(q, 3)}" for e, q in dw)
                + f"); D18 variantlarında alət zəifdir (F {az(Fw[0], 1)}–{az(Fw[1], 1)})")
    rm, rr, dmp = V['e3mw_rmse']
    lv, df, dp, l18, p18 = V['e3mw_lev']
    d18, d18se = V['mw_dols_d18']['E3']
    gain = (f"özəl sektor əmək haqqı üçün daha aşağı sürüşən RMSE verir ({az(rm)}%, onsuz isə {az(rr)}%, DM p = {az(dmp)})" if rm < rr
            else f"özəl sektor əmək haqqının sürüşən RMSE-sini yaxşılaşdırmır ({az(rm)}%, onsuz isə {az(rr)}%, DM p = {az(dmp)})")
    B['e3mw'] = (f"Homogen formada minimum əmək haqqı {gain}, işarəsi isə **mənfidir**. O, ≤2020 məlumatları üzrə **siyasət "
                 f"rıçaqlarının uyğunluğu qaydasını** ödəmir: (a) səviyyədə {azpm(lv, 3)}, fərq formasındakı qiymət isə {azpm(df, 3)} "
                 f"(p = {az(dp)}), yəni nə nəzəriyyəyə uyğun səviyyə təsiri, nə də fərqlərdə əhəmiyyətli təsir var; (b) 2019-cu il "
                 f"fiktiv dəyişəni (D18) ilə qiymət {azpm(l18, 3)} təşkil edir (p = {az(p18)}; D18 ilə tam nümunə DOLS qiyməti "
                 f"{azm(d18, 3)}, s.x. {az(d18se, 3)}) — islahatın zamanlaması ilə bağlı artefakt (islahat\ndövlət sektorunda əmək "
                 f"haqqını artırdı; özəl sektor əmək haqqı bunu izləmədi).")
    eg = list(V['eg'].values())
    B['eg'] = f"{az(min(eg))}–{az(max(eg))}"
    S = V['sim']
    w = '**zəifdir**' if S['e4F'] < 10 else 'güclüdür'
    j4 = '5% səviyyəsində rədd edilmir' if S['e4s'] >= 0.05 else '**rədd edilir**'
    j5 = '**rədd edilir**' if S['e5s'] < 0.05 else '5% səviyyəsində rədd edilmir'
    B['sim'] = (f"minimum əmək haqqı əmsalı (D18 ilə) OLS-də {az(S['e4o'], 3)}, 2SLS-də isə {az(S['e4i'], 3)} olur, lakin birinci "
                f"mərhələ {w} (F = {az(S['e4F'], 1)}), Sargan p = {az(S['e4s'], 3)}\n({j4}); E5 üçün OLS {azm(S['e5o'], 3)}, 2SLS isə "
                f"{azm(S['e5i'], 3)} verir, Sargan p = {az(S['e5s'], 3)} ({j5}). Bu fərqlər\nböyükdür. Dörd proqnoz tənliyi üzrə 3SLS "
                f"(2010–2025, 16 müşahidə) yalnız çarpaz yoxlamadır (dövlət sektoru əmək haqqında minimum\nəmək haqqı əmsalı "
                f"{az(V['sys3_e4'], 3)})")
    dm = ''
    parts = []
    if C['cg_worse']:
        parts.append(f"{_and(C['cg_worse'])} üzrə əhəmiyyətli dərəcədə *pis*")
    if C['cg_better']:
        parts.append(f"{_and(C['cg_better'])} üzrə isə əhəmiyyətli dərəcədə *yaxşı*")
    if parts:
        dm = f" Sabit artıma qarşı DM testi (p < 0,10) modelin {', '.join(parts)} olduğunu göstərir."
    an = C['anch']
    cgh = f"sabit artımdan isə {loc(C['ncg'])} üstündür" if C['ncg'] else 'sabit artımdan isə heç birində üstün deyil'
    B['holdtxt'] = (f"**Əsas nəticə: model 5 sıranın {loc(C['nrw'])} təsadüfi gəzişmədən üstündür (median U {az(C['mrw'])}), {cgh}\n"
                    f"(median U {az(C['mcg'])}).**{dm} Xətaların böyük hissəsi 2020-ci il (COVID ili) qalığı ilə lövbərləmədən və "
                    f"2021–22-ci illərin inflyasiya sıçrayışından qaynaqlanır:\nlövbər kimi 2018–2020 orta qalığından istifadə edildikdə "
                    f"(işarələnmiş həssaslıq variantı) RMSE {az(an[0], 1)}% (orta), {az(an[1], 1)}% (qeyri-neft),\n{az(an[2], 1)}% "
                    f"(özəl), {az(an[3], 1)}% (dövlət), {az(an[4], 1)}% (neft) olardı. Digər həssaslıq variantları: uzlaşdırılmamış "
                    f"E1-in özü üzrə orta əmək haqqı\nRMSE-si {az(a.raw_equation_RMSE, 1)}% təşkil edir; E1-ə sonlu çəki verilməsi "
                    f"{az(a.E1_weighted_RMSE, 1)}% verir; E1-ə *uyğun* uzlaşdırma — {az(a.E1_fixed_RMSE, 1)}%. Əmək haqqı fondu ayrıca "
                    f"hədəf deyil\n(onun xətası konstruksiyaya görə orta əmək haqqı xətasına bərabərdir). Neft sektoru üzrə xəta "
                    f"mükafatla bağlıdır: faktiki\ngöstərici {az(C['p25'])}× səviyyəsinə enərkən mükafat {az(C['p20'])}× səviyyəsində saxlanılıb.")
    B['af'] = ', '.join(f"E{i + 1} {azm(x, 3)}" for i, x in enumerate(C['af']))
    fa = C['fac']
    B['fac'] = (f"dövlət {az(fa['w_state'][0], 3)} → {az(fa['w_state'][1], 3)}, özəl {az(fa['w_priv'][0], 3)} → {az(fa['w_priv'][1], 3)}, "
                f"qeyri-neft {az(fa['w_non'][0], 3)} → {az(fa['w_non'][1], 3)}; uzlaşdırılmış aqreqat E1-in öz proqnozundan "
                f"{azpm(C['e1gap'][0], 1)}% → {azpm(C['e1gap'][1], 1)}%\nfərqlənir. {yr(y1)} ildə uzlaşdırılmış dəyərlər cari "
                f"qiymətləndirmələrdən {az(C['ncgap'], 1)}% daxilində fərqlənir")
    g, pr = C['mwg'], C['premN']
    B['lev'] = (f"**minimum əmək haqqı** ({yr(y1)} ildə qüvvədə olan qanuni səviyyə — {C['mw26']:.0f} manat, {yr(y1 + 1)} ildən isə ildə "
                f"{g[0]:.0f}% / {g[1]:.0f}% / {g[2]:.0f}% nominal artım) və\n**neft mükafatının trayektoriyası** ({yr(y1)} il cari "
                f"qiymətləndirmə dəyəri olan {az(C['prem26'])}× səviyyəsindən {yr(yN)} ilədək {az(pr[0], 1)}× / {az(pr[1], 1)}× / "
                f"{az(pr[2], 1)}× səviyyəsinə\nqədər)")
    r = C['rat']
    cr = f" ({yr(C['cross'])} ildə 1,00 həddini keçir)" if C['cross'] else ''
    B['bill'] = (f"Əsas ssenari üzrə əmək haqqı fondu: {yr(y1)} ildə {az(C['wb1'], 0)} mln manat ({azpm(C['wbg'], 1)}%), {yr(yN)} ildə "
                 f"{az(C['wbN'], 0)} mln manata qədər artır.\n**Dövlət/özəl nisbəti** Əsas ssenaridə {yr(y1)} ildə {az(r[0])}, "
                 f"{yr(yN)} ildə {az(r[1])} təşkil edir{cr},\n{yr(yN)} ildə Mənfi ssenaridə {az(r[2])}, İslahat ssenarisində isə "
                 f"{az(r[3])} olur; bu, dövlət sektoru tənliyindəki minimum əmək haqqı ilə\nmüəyyən edilir.")
    f1 = C['fr1']
    B['fr1gap'] = (f"{yr(y1)} ildə {azpm(f1[0], 1)}%, {yr(yN)}\nildə isə {azpm(f1[1], 1)}% fərqlənir (Əsas ssenari); ssenarilər üzrə "
                   f"fərq {azpm(f1[2], 1)}%-dən {azpm(f1[3], 1)}%-dək")
    hw, rs = C['hw'], C['rmse']
    B['sanity'] = (f"{yr(y1)} ildə {az(hw['w_avg'][0], 1)}%, {y1 + 1}–{yr(yN)} illərdə isə {hw['w_avg'][1]:.0f}–{hw['w_avg'][2]:.0f}% "
                   f"təşkil\nedir, nümunədən kənar yoxlamanın RMSE-si isə {az(rs['w_avg'], 1)}%-dir; dövlət sektoru əmək haqqı üzrə "
                   f"{az(rs['w_state'], 1)}%-ə qarşı {hw['w_state'][1]:.0f}–{hw['w_state'][2]:.0f}%; özəl sektor əmək\nhaqqı üzrə "
                   f"{az(rs['w_priv'], 1)}%-ə qarşı {hw['w_priv'][1]:.0f}–{hw['w_priv'][2]:.0f}%")
    urw, ucg = o['U vs random walk'], o['U vs const growth']
    rw = (f"təsadüfi gəzişmə bu mexanizmdən üstündür (U {az(urw)})" if urw > 1 else f"bu mexanizm təsadüfi gəzişmədən üstündür (U {az(urw)})")
    cgo = ('sabit artım isə təxminən eyni\n   nəticə verir' if 0.9 <= ucg <= 1.1 else 'sabit artım isə ondan üstündür' if ucg > 1
           else 'o isə sabit artımdan üstündür')
    l8, h8 = V['mw_rng']['E4']
    l3, h3 = V['mw_rng']['E3']
    c5 = (f"model beş sıranın {loc(C['ncg'])} sabit artımdan üstündür" if C['ncg'] else 'model beş sıranın heç\n   birində sabit artımdan üstün deyil')
    B['lim'] = (f"**Neft sektoru əmək haqqı** tənlik vasitəsilə proqnozlaşdırılmır: o, qeyri-neft sektoru əmək haqqının açıq bildirilmiş mükafat\n"
                f"   rıçağına hasilidir; nümunədən kənar yoxlamada {rw}, {cgo} ({az(ucg)}).\n"
                f"5. **Nümunədən kənar yoxlama sabit artımla müqayisədə {poor}**: proqnozun öz lövbərləmə qaydası ilə {c5} "
                f"(orta əmək haqqı U {az(a['U vs const growth'])}, 2025-ci ilədək {azpm(a.err_2025, 1)}%). Lövbər ili çox mühüm rol "
                f"oynayır (2018–20\n   orta qalığı ilə lövbərləmədə: {az(an[0], 1)}%).\n"
                f"6. Heç bir tənlik üçün **kointeqrasiya təsdiqlənmir** (EG və Gregory–Hansen); t-statistikaları təsviri xarakter daşıyır, baza\n"
                f"   düzəliş əmsalları isə sabit saxlanılır.\n"
                f"7. **Homogenlik nəzəri əsaslarla qoyulur**, baxmayaraq ki, qısa nümunədə özəl sektor əmək haqqı üçün rədd edilir; məhdudiyyətsiz\n"
                f"   forma özəl sektor əmək haqqının illik artımını {az(C['main_priv'])}% əvəzinə {az(C['e3u_priv'])}% verir.\n"
                f"8. **Minimum əmək haqqının təsiri qeyri-dəqiqdir**: dövlət sektoru üzrə {az(l8)}–{az(h8)} (proqnozda "
                f"{az(V['mw_dols']['E4'], 3)}; proqnoz dəqiqliyi\n   qiymətləndirilməmiş 2019 qırılma fiktiv dəyişəni ilə "
                f"{az(V['mw_dols_d18']['E4'][0], 3)}). Özəl sektor əmək haqqında onun qiymətləri mənfidir ({azm(l3)} ilə {azm(h3)}\n"
                f"   arasında), lakin rıçaq uyğunluğu qaydasını ödəmir, ona görə də orada çıxarılır; özəl sektora hər hansı həqiqi təsir nəzərə\n"
                f"   alınmır.")
    return B
