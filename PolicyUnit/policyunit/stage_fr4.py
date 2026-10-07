"""Stage FR4 (MİİS §15.5.4): side effects, side-effect scenarios, RiskUnit integration (HTTP), mitigation
proposals, global sensitivity. Registered in run_all.py via register(R); writes P4_* (+ catalogue).

  python3 run_all.py --only fr4.side_effects[,fr4.kpi_refresh] [--scenario mw20_2027,...]
Long run (≈ 5–8 min for all scenarios first time; cached afterwards): start in background, poll logs/run_all.log."""
from __future__ import annotations

import time

import pandas as pd

from . import catalog, config, scenario as scn
from . import risk_link as RL, sensitivity as SN, side_effects as S

OWNER = "fr4"
FILES = {
    "P4_side_effects.csv": "FR4: hər ssenari (və avtomatik yan təsir ssenariləri) üçün tetiklənən yan təsirlər — ailə, "
                           "kəmiyyət, şiddət 1–4, üfüq, təsirlənən qrup/sektor, RiskUnit risk id-ləri, izah",
    "P4_side_effect_scenarios.csv": "FR4: avtomatik yan təsir ssenariləri (neft −1σ, manat −1σ, zəif ötürmə −1 SE, "
                                    "alternativ maliyyələşmə) — əsas göstəricilərin siyasət təsiri əsas vs şərt",
    "P4_risk_profile.csv": "FR4: RiskUnit stress/run — siyasətlə vs siyasətsiz şərti risk paylanması (qeyri-neft artımı, "
                           "İQİ, büdcə): hədd pozulma ehtimalı, ES10, P10, median; HTTP statusu (canlı/keş)",
    "P4_mitigation.csv": "FR4: azaldıcı tədbir təklifləri — qayda xəritəsi (T01–T30), siyasətə xas təkliflər "
                         "(ardıcıllıq, hədəfləmə, kompensasiya, maliyyələşmə), RiskUnit optimize/run portfeli, qalıq risk",
    "P4_kpi_inputs.csv": "FR4 → FR5: KPI girişləri (scenario, kpi, value): side_effects, risk_es",
    "P4_sensitivity.csv": "FR4: qlobal həssaslıq — Sobol S1/ST (Saltelli/Jansen), hər başlıq nəticəsi üçün ilk 3 sürücü, "
                          "yığılma (bootstrap CI), rədd edilən qeyri-sabit çəkilişlər",
    "P4_instability.csv": "FR4: MikroUnit zəncirinin dinamik qeyri-sabitlik bölgəsi (model riski) — rədd edilən Sobol "
                          "çəkilişlərinin payı, əmsal üzrə şərti rədd tezliyi (z > 1 / z < −1) və ən pis əmsal cütü bölgəsi",
    "P4_uncertainty_bands.csv": "FR4: siyasət təsirinin qeyri-müəyyənlik zolaqları (p05–p95; parametr qeyri-müəyyənliyi) — "
                                "proqnoz zolağı deyil",
}


def _p1(ids):
    p = config.OUTPUT / "P1_effects.csv"
    if not p.exists():
        return None
    f = pd.read_csv(p)
    return f if set(ids) <= set(f.scenario.unique()) else None


def _merge_write(df: pd.DataFrame, name: str, ids):
    p = config.OUTPUT / name
    if p.exists() and len(ids) < len(scn.all_ids()):
        old = pd.read_csv(p)
        if "scenario" in old.columns:
            df = pd.concat([old[~old.scenario.isin(ids)], df], ignore_index=True)
    catalog.write_csv(df, name, OWNER, FILES[name])


def run(args, log):
    t0 = time.perf_counter()
    ids = args.scenario.split(",") if getattr(args, "scenario", "") else scn.all_ids()
    p1 = _p1(ids)
    rules, mmap = S.load_rules(), RL.load_map()
    SE, PR, MI, KP, SR, VT = [], [], [], [], [], []
    with RL.server(log=log) as c, SN.Evaluator() as ev:
        sig = RL.sigma(c)
        log(f"  RiskUnit: {'canlı' if c.alive() else 'keş/əlçatmaz'}; σ = {sig or 'keşdən/defolt'}; "
            f"həssaslıq işçiləri: {ev.workers}")
        ctx = {"client": c, "evaluator": ev, "rules": rules, "mitigation_map": mmap, "sigma": sig, "log": log}
        for sid in ids:
            ts = time.perf_counter()
            s = scn.load(sid)
            frame = p1[p1.scenario == sid] if p1 is not None else None
            r = S.analyse(s, frame, ctx, mode="full")
            for k, v in r["status"].items():
                if k.startswith("variant:"):
                    log(f"  {sid}/{k[8:]}: yan təsir ssenarisi {v}")
            se = r["side_effects"]
            SE += se
            PR.append(r["risk_profile"])
            MI.append(r["mitigation"])
            KP += r["kpi_inputs"]
            VT += r["variant_table"]
            SR.append(r["sensitivity"])
            nb = sum(1 for x in se if x["variant"] == "base")
            log(f"  {sid}: yan təsirlər {nb} (+{len(se) - nb} şərti), variantlar {len(r['variants'])}, "
                f"tədbir sətirləri {len(r['mitigation'])}, RiskUnit: {r['status'].get('riskunit')}, "
                f"həssaslıq {r['status'].get('sensitivity')} ({time.perf_counter() - ts:.1f} s)")
    sens_df, bands_df, inst_df = SN.frames(SR)
    _merge_write(pd.DataFrame(SE, columns=S.SE_COLS + ["change_vs_base"]), "P4_side_effects.csv", ids)
    _merge_write(pd.DataFrame(VT), "P4_side_effect_scenarios.csv", ids)
    _merge_write(pd.concat(PR, ignore_index=True), "P4_risk_profile.csv", ids)
    _merge_write(pd.concat(MI, ignore_index=True), "P4_mitigation.csv", ids)
    _merge_write(pd.DataFrame(KP, columns=["scenario", "kpi", "value"]), "P4_kpi_inputs.csv", ids)
    _merge_write(sens_df, "P4_sensitivity.csv", ids)
    _merge_write(bands_df, "P4_uncertainty_bands.csv", ids)
    _merge_write(inst_df, "P4_instability.csv", ids)
    log(f"  FR4 yazıldı: {', '.join(FILES)} ({time.perf_counter() - t0:.0f} s)")


def kpi_refresh(args, log):
    """Recompute P5 with the fresh P4_kpi_inputs (core.scenarios runs before FR4)."""
    from . import kpi
    p = config.OUTPUT / "P1_effects.csv"
    if not p.exists():
        log("  P1_effects.csv yoxdur — buraxıldı")
        return
    kpis = args.kpi.split(",") if getattr(args, "kpi", "") else None
    vals, rank = kpi.compute(pd.read_csv(p), kpis)
    catalog.write_csv(vals, "P5_kpi_values.csv", "core", "FR5: seçilmiş KPI-ların dəyərləri, normallaşdırılmış bal "
                      "(0–1) və çəkilər (FR4 KPI girişləri ilə yenilənib)")
    catalog.write_csv(rank, "P5_ranking.csv", "core", "FR5: çoxkriteriyalı bal, xərc-effektivlik və ssenari reytinqi "
                      "(FR4 KPI girişləri ilə yenilənib)")
    log(f"  P5 yeniləndi ({len(vals)} sətir)")


def register(R):
    R.add("fr4.side_effects", run, owner=OWNER, after=["core.scenarios"], optional=True,
          description_az="FR4: yan təsirlər, yan təsir ssenariləri, RiskUnit (HTTP), azaldıcı tədbirlər, həssaslıq → P4_")
    R.add("fr4.kpi_refresh", kpi_refresh, owner=OWNER, after=["fr4.side_effects"], optional=True,
          description_az="FR5 KPI-larının FR4 girişləri (risk_es, side_effects) ilə yenilənməsi")
