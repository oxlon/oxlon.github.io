"""AUTO blocks of docs/VaR_CaR_metodologiya.md §15 — every number is rendered from the current outputs
(V1, V3, V5, K2–K5, FR3 stress), so the results section cannot go stale (v2.4 verification finding 4).
Markers: <!-- AUTO:vc_<tag> --> ... <!-- /AUTO:vc_<tag> -->. Called from docs.update_methodology()."""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from . import config

DOC = config.DOCS / "VaR_CaR_metodologiya.md"
O = config.OUTPUT


def az(x, nd: int = 1) -> str:
    try:
        x = float(x)
    except (TypeError, ValueError):
        return "—"
    if not np.isfinite(x):
        return "—"
    return f"{x:,.{nd}f}".replace(",", " ").replace(".", ",")


def _rd(name):
    p = O / name
    return pd.read_csv(p) if p.exists() else None


def _v1(x, kod, col="deyer"):
    r = x.loc[x["kod"] == kod, col]
    return r.iloc[0] if len(r) else np.nan


def blocks() -> dict[str, str]:
    out = {}
    V1, V3, V5 = _rd("V1_exposures.csv"), _rd("V3_var_es.csv"), _rd("V5_var_backtest.csv")
    K2, K3, K4, K5 = (_rd(f) for f in ("K2_car_distribution.csv", "K3_dsa_fan.csv", "K4_sofaz_adequacy.csv", "K5_cca.csv"))
    if V1 is not None:
        out["vc_exposures"] = (
            f"ARDNF aktivləri {az(_v1(V1, 'sofaz_total'))} mln USD ({_v1(V1, 'sofaz_total', 'tarix')}): sabit gəlirli "
            f"{az(_v1(V1, 'sofaz_class_fixed_income', 'pay_faiz'))}%, səhm {az(_v1(V1, 'sofaz_class_equities', 'pay_faiz'))}%, "
            f"qızıl {az(_v1(V1, 'sofaz_class_gold', 'pay_faiz'))}%, daşınmaz əmlak {az(_v1(V1, 'sofaz_class_real_estate', 'pay_faiz'))}%. "
            f"AMB ehtiyatları {az(_v1(V1, 'cbar_reserves'))} mln USD ({_v1(V1, 'cbar_reserves', 'tarix')}). Dövlət borcu "
            f"(MN bülleteni) {az(_v1(V1, 'debt_public_total'))} mln AZN ({_v1(V1, 'debt_public_total', 'tarix')}); "
            f"zəmanətli borc {az(_v1(V1, 'cl_guaranteed_total'))} mln AZN.")
    if V3 is not None:
        rows = ["| Horizont | Portfel | HS | Yaşa çəkili HS | MK t-kopula | EVT | Kornish–Fişer | Kök-zaman |",
                "|---|---|---|---|---|---|---|---|"]
        for pid in ("sofaz", "net_fx"):
            for h, hl in (("1g", "1 gün"), ("1a", "1 ay"), ("1il", "1 il")):
                cells = []
                for m in ("hs", "awhs", "mc_tcop", "evt", "cf", "sqrt_time"):
                    x = V3[(V3.portfel == pid) & (V3.horizont == h) & (V3.metod == m)].set_index("etibarlilik")
                    if not len(x):
                        cells.append("—")
                        continue
                    flag = "" if ("etibarli" not in x or bool(x["etibarli"].iloc[0])) else " (etibarsız)"
                    cells.append(f"{az(x['VaR_mln_usd'].get(0.95), 0)} / {az(x['VaR_mln_usd'].get(0.99), 0)}{flag}")
                rows.append(f"| {hl} | {pid} | " + " | ".join(cells) + " |")
        o = V3[V3.portfel == "oil_rev"].pivot_table(index="metod", columns="etibarlilik", values="VaR_mln_azn")
        oil = "; ".join(f"{m} {az(o.at[m, 0.95], 0)} / {az(o.at[m, 0.99], 0)}" for m in o.index)
        out["vc_var"] = ("VaR, mln USD (95% / 99%):\n\n" + "\n".join(rows) +
                         f"\n\nBüdcənin neft gəlirlərinə risk (mln AZN, 95% / 99%, vahid lövbər — FR1 bazası): {oil}.")
    if V5 is not None:
        t = V5[(V5.portfel == "sofaz") & V5.horizont.isin(["1g", "1a"]) & V5.test.astype(str).str.contains("Kupiec")]
        lines = [f"{r.horizont} {r.metod} {az(r.etibarlilik * 100, 0)}%: n = {int(r.n)}, pozuntu {int(r.pozuntu)} "
                 f"(gözlənilən {az(r.gozlenilen)}), p = {az(r.p_deyer, 3)} → {r.netice}" for r in t.itertuples()]
        out["vc_backtest"] = "ARDNF, Kupiec testi: " + "; ".join(lines) + ". 1 illik horizont yoxlanıla bilməz (n < 25)."
    if K2 is not None:
        x = K2[K2.variant == "şərti öhdəliklər xaric"].set_index("il")
        out["vc_car"] = "Fiskal kapital (K2, şərti öhdəliklər xaric): " + "; ".join(
            f"{y}: orta {az(x.at[y, 'NW_orta_mln_usd'], 0)}, CaR95 {az(x.at[y, 'CaR95_mln_usd'], 0)}, "
            f"CaR99 {az(x.at[y, 'CaR99_mln_usd'], 0)} mln USD" for y in (config.score_year(), config.FORECAST_YEARS[-1]))
    if K3 is not None:
        b = K3[K3.variant.str.startswith("əsas: RU")].set_index("il")
        y1, y2 = config.score_year(), config.FORECAST_YEARS[-1]
        out["vc_dsa"] = (
            f"Əsas variant: borc/ÜDM {y1} median {az(b.at[y1, 'p50'])}%, p95 {az(b.at[y1, 'p95'])}%; {y2} median "
            f"{az(b.at[y2, 'p50'])}%, p95 {az(b.at[y2, 'p95'])}% (FR1 baza {az(b.at[y2, 'baza_FR1_MN'])}%). "
            f"Maksimum ehtimallar (bütün illər, əsas): P(> 20%) = {az(b['P_borc_gt_20'].max(), 3)}, P(> 25%) = "
            f"{az(b['P_borc_gt_25'].max(), 3)}, P(> 30%, DR10) = {az(b['P_borc_gt_30'].max(), 3)}; GFN p95 maks. "
            f"{az(b['GFN_p95'].max())}% ÜDM; borc xidməti/gəlir p95 maks. {az(b['borc_xidmeti_gelir_p95'].max())}%.")
    if K4 is not None:
        ref = K4[(K4.ssenari == "istinad") & (K4.psi_kesir_ARDNF_den == 0)].set_index("il")
        sto = K4[K4.ssenari == "stoxastik"].set_index("il")
        y1, y2 = config.score_year(), config.FORECAST_YEARS[-1]
        txt = (f"İstinad yolunda transfert örtüyü {az(ref.at[y1, 'ortuk_ili'])} il ({y1}) → {az(ref.at[y2, 'ortuk_ili'])} il "
               f"({y2}); stoxastik {y1}: örtüyün p05-i {az(sto.at[y1, 'ortuk_ili_p05'])} il, P(örtük < 3 il) = "
               f"{az(sto.at[y1, 'P_ortuk_lt_hedd'], 3)}.")
        for sid in ("S1", "S3"):
            s = K4[(K4.ssenari == sid) & (K4.psi_kesir_ARDNF_den == 1)].set_index("il")
            if len(s):
                txt += f" {sid}: {y2} aktivləri {az(s.at[y2, 'ARDNF_mln_usd'] / 1000)} mlrd USD (istinaddan " \
                       f"{az(s.at[y2, 'ARDNF_istinaddan_ferq_mln_usd'] / 1000)} mlrd)."
        st = _rd("FR3_stress_scenarios.csv")
        if st is not None and "gosterici" in st:
            f = st[st["gosterici"].astype(str).str.startswith("büdcə") & st["ssenari"].isin(["S1", "S3"])]
            if len(f):
                txt += (" Stress dəstində S1/S3-ün büdcə balansı sapması: " + "; ".join(
                    f"{sid} {az(g['sapma'].min(), 2)}…{az(g['sapma'].max(), 2)}% ÜDM" for sid, g in f.groupby("ssenari")) + ".")
        out["vc_sofaz"] = txt
    if K5 is not None:
        out["vc_cca"] = ("CCA (əlavə, məlumatsız): qəzaya qədər məsafə " + "; ".join(
            f"{str(r.variant).split(':')[0]} {az(r.DD)}" for r in K5.itertuples()) +
            f"; aktivlərin qəzaya qədər düşməsi {az(K5['qezaya_qeder_aktiv_dusmesi_pct'].min(), 0)}–"
            f"{az(K5['qezaya_qeder_aktiv_dusmesi_pct'].max(), 0)}%.") if "qezaya_qeder_aktiv_dusmesi_pct" in K5 else ""
    return out


def update() -> list[str]:
    """Rewrite every vc_* AUTO block that exists in the document; returns the tags written."""
    if not DOC.exists():
        return []
    text, done = DOC.read_text(encoding="utf-8"), []
    for tag, body in blocks().items():
        pat = re.compile(rf"(<!-- AUTO:{tag} -->)(.*?)(<!-- /AUTO:{tag} -->)", re.S)
        if pat.search(text):
            text = pat.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(3)}", text)
            done.append(tag)
    DOC.write_text(text, encoding="utf-8")
    return done


if __name__ == "__main__":
    print(update())
