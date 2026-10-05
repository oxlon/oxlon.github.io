# %% [markdown]
# ## Hissə 15 — Sənaye təşkilatı nəzəriyyəsi ilə ssenari təhlili
#
# Kalibrlənmiş, şəffaf **Kurno (Cournot) alətləri dəsti**. Bazar HHI-si (simmetrik ekvivalent müəssisə sayı $N = 1/HHI$),
# kalibrləmə nöqtəsində tələbin elastikliyi ε və davranış parametri θ (1 = Kurno, < 1 daha rəqabətli) ilə xülasə edilir.
# Sahənin Lerner indeksi $L=\theta\,HHI/\varepsilon$; qiymət və buraxılış 1-ə normallaşdırıldıqda son hədd xərci
# $c = 1-L$; xətti tələb $P = a - bQ$, burada $b = 1/\varepsilon$, $a = 1 + b$.
#
# | Ssenari | Mexanizm |
# |---|---|
# | (a) bazara giriş / lisenziyalaşdırmanın sadələşdirilməsi | $N \to N+\Delta N$; simmetrik tarazlıq $Q = N(a-c)/(b(N+\theta))$ |
# | (b) birləşmə | $\Delta HHI = 2s_1s_2$, istifadə olunan HHI heç vaxt $s_1^2+s_2^2$-dən aşağı deyil; ilkin yoxlama hədləri: ABŞ 2010 (1500/2500; ΔHHI 100/200) və AB (ΔHHI ≥ 250 ilə HHI 1000–2000, ΔHHI ≥ 150 ilə > 2000); Farrell–Shapiro: qiymət yalnız birləşmiş müəssisənin son hədd xərci ən azı birləşmədən əvvəlki əlavə qiymət (markup) qədər azaldıqda düşür |
# | (c) xərc şoku / vahidə görə vergi *t* | ötürülmə əmsalı $dP/dc = N/(N+\theta)$ (xətti tələb); $N\varepsilon/(N\varepsilon-\theta)$ (sabit elastiklik) |
# | (d) idxal rəqabəti | *m* payı və η təklif elastikliyi ilə rəqabətli idxal kənarı (fringe): $L=\theta\,HHI_d(1-m)/(\varepsilon+\eta m)$ |
# | (e) dövlət müəssisəsi | **qarışıq oliqopoliya** (De Fraja və Delbono 1989; Matsumura 1998-də olduğu kimi qismən özəlləşdirmə), aşağıda |
#
# **Qarışıq oliqopoliya.** Son hədd xərci artan $c + k q_0$ olan bir dövlət müəssisəsi (buraxılış payı σ)
# $\lambda\,\pi_0 + (1-\lambda)\,W$ ifadəsini maksimallaşdırır (λ = 0: rifahı maksimallaşdıran dövlət müəssisəsi; λ = 1: tam
# özəlləşdirilmiş); son hədd xərci *c* olan *n* simmetrik özəl müəssisə θ davranışı ilə Kurno oyununu oynayır. Birinci
# tərtib şərtlər: dövlət müəssisəsi $P = c + k q_0 + \lambda\theta b q_0$, özəl $P = c + \theta b q_i$. Mövcud vəziyyətdə
# kalibrləmə (λ = 0, P = 1, Q = 1): $c = 1-\theta b(1-\sigma)/n$, $k = \theta b (1-\sigma)/(n\sigma)$ (fərziyyə: dövlət
# müəssisəsinin son hədd xərci özəl müəssisələrin səviyyəsindən başlayır və buraxılışla artır) və
# $n = (1-\sigma)^2/(HHI-\sigma^2)$, belə ki, istifadə olunan HHI heç vaxt σ²-dən aşağı deyil (və n ≥ 1). Ssenari λ-nı 0,5
# və ya 1-ə qaldırır və tarazlıq **ədədi üsulla həll edilir** (`scipy.optimize.fsolve`).
#
# Rifah (xətti tələb, dəqiq): $\Delta CS=\tfrac12(Q_0+Q_1)(P_0-P_1)$, $\Delta PS$ = mənfəətlərin dəyişməsi; ilkin bazar
# gəlirinin %-i ilə və bazarın gəliri məlum olduqda (A qatının qrupları) mln manatla. Nümunələr **illüstrativdir**
# (fərziyyələr açıq göstərilir); B qatında real məlumatlar olduqda eyni funksiyalar müəssisə səviyyəli HHI üzərində işləyir.

# %%
from scipy.optimize import fsolve
def lin_eq(N, eps, theta, c, a_b):
    a, b = a_b; Q = N * (a - c) / (b * (N + theta)); return a - b * Q, Q
def calibrate(hhi, eps, theta):
    L = min(theta * hhi / eps, 0.95); b = 1 / eps
    return dict(L=L, c=1 - L, a=1 + b, b=b, N=theta / (L * eps) if L > 0 else np.inf)
def outcome(P0, Q0, c0, P1, Q1, c1, rev_mn, dps=None):
    dcs = 0.5 * (Q0 + Q1) * (P0 - P1); dps = (P1 - c1) * Q1 - (P0 - c0) * Q0 if dps is None else dps
    return dict(d_price_pct=(P1 / P0 - 1) * 100, d_markup_pp=((P1 - c1) / P1 - (P0 - c0) / P0) * 100, d_output_pct=(Q1 / Q0 - 1) * 100,
                d_cs_pct_rev=dcs / (P0 * Q0) * 100, d_ps_pct_rev=dps / (P0 * Q0) * 100,
                d_cs_mn=dcs / (P0 * Q0) * rev_mn if rev_mn == rev_mn else np.nan, d_ps_mn=dps / (P0 * Q0) * rev_mn if rev_mn == rev_mn else np.nan)
def sc_entry(hhi, eps, theta, dN, rev):
    k = calibrate(hhi, eps, theta); P0, Q0 = lin_eq(k['N'], eps, theta, k['c'], (k['a'], k['b'])); P1, Q1 = lin_eq(k['N'] + dN, eps, theta, k['c'], (k['a'], k['b']))
    return outcome(P0, Q0, k['c'], P1, Q1, k['c'], rev)
def sc_merger(hhi, eps, theta, s1, s2, rev):
    hhi = max(hhi, s1 ** 2 + s2 ** 2); dH = 2 * s1 * s2; h1 = hhi + dH
    us = 'presumed to enhance market power' if h1 > .25 and dH > .02 else ('potentially raises significant concerns' if h1 > .15 and dH > .01 else 'unlikely to have adverse effects')
    eu = 'concern' if ((h1 > .2 and dH >= .015) or (.1 <= h1 <= .2 and dH >= .025)) else 'no presumption'
    k = calibrate(hhi, eps, theta); P0, Q0 = lin_eq(k['N'], eps, theta, k['c'], (k['a'], k['b']))
    P1, Q1 = lin_eq(max(theta / (min(theta * h1 / eps, 0.95) * eps), 1.0), eps, theta, k['c'], (k['a'], k['b']))
    return outcome(P0, Q0, k['c'], P1, Q1, k['c'], rev) | dict(hhi_used=hhi * 1e4, hhi_post=h1 * 1e4, d_hhi=dH * 1e4, us_2010_screen=us, eu_screen=eu, fs_required_mc_cut_pct=(P0 - k['c']) / k['c'] * 100)
def sc_cost(hhi, eps, theta, t, rev):
    k = calibrate(hhi, eps, theta); P0, Q0 = lin_eq(k['N'], eps, theta, k['c'], (k['a'], k['b'])); P1, Q1 = lin_eq(k['N'], eps, theta, k['c'] + t, (k['a'], k['b']))
    ne = k['N'] * eps
    return outcome(P0, Q0, k['c'], P1, Q1, k['c'] + t, rev) | dict(passthrough_linear=(P1 - P0) / t, passthrough_const_elast=ne / (ne - theta) if ne > theta else np.nan)
def sc_import(hhi_d, eps, theta, m0, m1, eta, rev):
    L0 = min(theta * hhi_d * (1 - m0) / (eps + eta * m0), .95); L1 = min(theta * hhi_d * (1 - m1) / (eps + eta * m1), .95)
    b = 1 / eps; a = 1 + b; c = 1 - L0; P1 = c / (1 - L1); Q1 = max(a - P1, 0) / b
    return outcome(1.0, 1.0, c, P1, Q1, c, rev)
def mixed_oligopoly(hhi, sigma, eps, theta, lam, rev, n_max=1000):
    b = 1 / eps; a = 1 + b
    hhi = min(max(hhi, sigma ** 2 + (1 - sigma) ** 2 / n_max), sigma ** 2 + (1 - sigma) ** 2)     # n between 1 and n_max
    n = (1 - sigma) ** 2 / (hhi - sigma ** 2); c = 1 - theta * b * (1 - sigma) / n; k = theta * b * (1 - sigma) / (n * sigma)
    def foc(x, lm):
        q0, q = x; P = a - b * (q0 + n * q)
        return [P - c - k * q0 - lm * theta * b * q0, P - c - theta * b * q]
    x0 = fsolve(foc, [sigma, (1 - sigma) / n], args=(0.0,), xtol=1e-12); x1 = fsolve(foc, x0, args=(lam,), xtol=1e-12)
    pr = lambda q0, q: (a - b * (q0 + n * q)) * (q0 + n * q) - c * (q0 + n * q) - k * q0 ** 2 / 2
    P0, Q0 = a - b * (x0[0] + n * x0[1]), x0[0] + n * x0[1]; P1, Q1 = a - b * (x1[0] + n * x1[1]), x1[0] + n * x1[1]
    mc_avg = lambda q0, q: (c * n * q + (c + k * q0) * q0) / (q0 + n * q)
    o = outcome(P0, Q0, mc_avg(*x0), P1, Q1, mc_avg(*x1), rev, dps=pr(*x1) - pr(*x0))
    return o | dict(hhi_used=hhi * 1e4, n_private=n, soe_share_after=x1[0] / Q1 * 100, d_welfare_pct_rev=o['d_cs_pct_rev'] + o['d_ps_pct_rev'],
                    calib_resid=float(abs(P0 - 1) + abs(Q0 - 1) + abs(x0[0] - sigma)))
_k = calibrate(0.25, 1.0, 1.0); _P, _Q = lin_eq(_k['N'], 1.0, 1.0, _k['c'], (_k['a'], _k['b']))
chk('Cournot calibration reproduces P = 1, Q = 1 at the calibration point', float(abs(_P - 1) + abs(_Q - 1)), abs(_P - 1) + abs(_Q - 1) < 1e-9)
for th_ in (1.0, 0.5):
    _kk = calibrate(0.25, 1.0, th_); _e = sc_cost(0.25, 1.0, th_, 0.01, 1.0)
    chk(f'linear Cournot pass-through equals N/(N+θ), θ = {th_}', float(abs(_e['passthrough_linear'] - _kk['N'] / (_kk['N'] + th_))), abs(_e['passthrough_linear'] - _kk['N'] / (_kk['N'] + th_)) < 1e-9)
_m = mixed_oligopoly(0.2, 0.3, 1.0, 1.0, 0.0, 1.0)
chk('mixed oligopoly: calibration reproduces P = 1, Q = 1, SOE share σ; λ = 0 leaves the equilibrium unchanged', _m['calib_resid'] + abs(_m['d_price_pct']), _m['calib_resid'] + abs(_m['d_price_pct']) < 1e-8)
print('IO toolkit: calibrate, sc_entry, sc_merger, sc_cost, sc_import, mixed_oligopoly (De Fraja-Delbono, numerical equilibrium)')
