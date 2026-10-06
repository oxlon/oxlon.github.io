"""b_tables.py — the remaining bundles, one per page family. Small tables go in whole; the big scalability, impact-map,
shock-library and upstream-catalog tables get string pooling (and are loaded only when a page needs them)."""
from . import bcore as C

PLAIN = {
    "var": ["V1_exposures.csv", "V1b_data_requests.csv", "V3_var_es.csv", "V4_var_contributions.csv", "V5_var_backtest.csv",
            "V6_var_history.csv", "K2_car_distribution.csv", "K3_dsa_fan.csv", "K4_sofaz_adequacy.csv", "K5_cca.csv"],
    "meas": ["FR3_measures_register.csv", "FR3_coverage.csv", "FR3_levers.csv", "FR3_status_history.csv",
             "FR3_stress_scenarios.csv", "FR3_historical_analogues.csv", "M1_measures_v2.csv", "M2_measure_effects.csv",
             "M3_portfolio.csv", "M4_frontier.csv", "M5_residual_v2.csv", "M6_implementation_plan.csv", "M7_strategy.csv"],
    "caem": ["C1_caem_signals.csv", "C1_band_reproduction.csv", "C4_caem_shock_index.csv", "C4_caem_variables.csv",
             "C4_caem_irf_validation.csv", "C5_transmission_comparison.csv", "C5_fr1_oscillation.csv", "C6_caem_findings.csv"],
    "nfr": ["NFR1_backtest_register.csv", "NFR1_backtest_results.csv", "NFR1_calibration.csv", "NFR1_brent_density_pit.csv",
            "NFR1_ews_brent_predictions.csv", "NFR1_ews_slowdown.csv", "NFR1_gar_rolling.csv", "NFR1_macro_fan_pit.csv",
            "?NFR1_calibration_shrinkage.csv"],
}


def build(tr):
    out = []
    for b, files in PLAIN.items():
        T = {}
        for f in files:
            req, f = not f.startswith("?"), f.lstrip("?")          # "?" = optional (newer output, shown when present)
            d = C.csv(f, b, required=req)
            if d is not None:
                T[f[:-4]] = C.table(tr.df(d))
        out.append((b, T))

    # scalability (lazy): S1 grid, S2 elasticities, S3 non-linearity, S5 parameters, S6 cross-model
    T = {}
    s1 = C.csv("S1_scalability_grid.csv", "scal")
    if s1 is not None:
        out.append(("s1", {"S1_scalability_grid": C.table(tr.df(s1), ["amil", "variant", "k_sigma", "olcu", "olcu_vahidi", "hedef_id", "hedef_ad",
                                                      "vahid", "il", "baza", "delta", "delta_pct", "qeyd"],
                                           sig=5, pool=("amil", "variant", "olcu_vahidi", "hedef_id", "hedef_ad", "vahid", "qeyd"))}))
    s2 = C.csv("S2_elasticities.csv", "scal")
    if s2 is not None:
        out.append(("s2", {"S2_elasticities": C.table(tr.df(s2), ["amil", "variant", "hedef_id", "il", "k_sigma", "delta_per_sigma",
                                                  "delta_per_unit", "vahid_cavab_izah", "elastiklik"],
                                       sig=5, pool=("amil", "variant", "hedef_id", "vahid_cavab_izah"))}))
    s3 = C.csv("S3_nonlinearity.csv", "scal")
    if s3 is not None:
        T["S3_nonlinearity"] = C.table(tr.df(s3), sig=5, pool=("amil", "amil_ad", "hedef_id", "hedef_ad", "vahid", "qeyd", "hedd_ad"))
    s5 = C.csv("S5_parameter_sensitivity.csv", "scal")
    if s5 is not None:
        T["S5_parameter_sensitivity"] = C.table(tr.df(s5), sig=5, pool=("amil", "amil_ad", "hedef_id", "hedef_ad", "parametr", "tenlik",
                                                                "parametr_ad", "metod", "komponent_id", "modul", "komponent_ad"))
    s6 = C.csv("S6_cross_model.csv", "scal")
    if s6 is not None:
        T["S6_cross_model"] = C.table(tr.df(s6), pool=("amil", "konsept", "konsept_ad", "model", "vahid", "miqyaslama"))
    out.append(("scal", T))

    s4 = C.csv("S4_impact_map.csv", "s4")
    if s4 is not None:
        out.append(("s4", {"S4_impact_map": C.table(tr.df(s4), ["amil", "seviyye", "modul", "qrup", "komponent_id", "komponent_ad",
                                                                "komponent_sayi", "sinif", "olcu_sinfi", "tesir_2027", "tesir_2030",
                                                                "ehemiyyet", "max_ehemiyyet", "sira"], sig=5,
                                                     pool=("amil", "seviyye", "modul", "qrup", "komponent_id", "komponent_ad",
                                                           "sinif", "olcu_sinfi"))}))

    lib = C.csv("C4_caem_shock_library.csv", "c4lib")
    L = {}
    if lib is not None:
        lib = lib.sort_values(["library", "shock_id", "variable", "horizon"])
        for (lb, sid, var), g in lib.groupby(["library", "shock_id", "variable"], sort=True):
            L.setdefault(f"{lb}|{sid}", {})[str(var)] = [C.fnum(v, 6) for v in g["response"]]
        out.append(("c4lib", {"C4_caem_shock_library": {"h": sorted(int(h) for h in lib["horizon"].unique()), "s": L}}))

    d1 = C.csv("D1_upstream_catalog.csv", "d1")
    sp = C.csv("spine_manifest.csv", "d1")
    T = {"D1_upstream_catalog": C.table(tr.df(d1), pool=("source", "unit", "years", "forecast_years", "scenarios", "row_ref",
                                                         "unit_group"))}
    if sp is not None:
        T["spine_manifest"] = C.table(sp)
    out.append(("d1", T))
    return out
