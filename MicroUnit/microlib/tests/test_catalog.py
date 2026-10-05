"""Indicator catalogue writer (contract C)."""
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm

from microlib.catalog import COLUMNS, check_catalog, read_catalog, write_catalog
from microlib.registry import EquationRegistry

from ._harness import check, raises, tmpdir


def test_catalog_roundtrip_and_errors():
    d = tmpdir()
    p = os.path.join(d, "FR1_indicator_catalog.csv")
    rows = [{"id": "fr1:rva_man", "group_az": "Real sektor", "label_az": "Emal sənayesi ƏDV", "label_en": "Manufacturing",
             "unit_az": "mln manat", "kind": "level", "has_forecast": True, "scenarios": ["Baseline", "Adverse"],
             "has_band": True, "source_csv": "FR1_forecast_full.csv", "source_column": "rva_man",
             "equation_ids": ["FR1.C3_man"], "imputed_years": [2003]}]
    df = write_catalog(rows, p, "FR1")
    check(list(df.columns) == COLUMNS, "column order")
    back = read_catalog(p)
    check(back.loc[0, "scenarios"] == ["Baseline", "Adverse"] and bool(back.loc[0, "has_band"]) is True
          and back.loc[0, "imputed_years"] == ["2003"] and back.loc[0, "equation_ids"] == ["FR1.C3_man"], "lists/bools")
    check(back.loc[0, "module"] == "FR1" and back.loc[0, "freq"] == "A", "defaults")
    raises(ValueError, write_catalog, [{"id": "rva_man", "label_az": "x", "kind": "level"}], p, "FR1")
    raises(ValueError, write_catalog, [{"id": "fr1:a", "label_az": "x", "kind": "flow"}], p, "FR1")
    raises(ValueError, write_catalog, [{"id": "fr3:a", "label_az": "x", "kind": "rate"}], p, "FR1")


def test_catalog_vs_registry():
    d = tmpdir()
    yrs = np.arange(2000, 2026)
    rng = np.random.default_rng(0)
    x = np.cumsum(rng.normal(size=26))
    y = pd.Series(1 + 0.5 * x + rng.normal(0, 0.2, 26), yrs)
    X = pd.DataFrame({"x": x}, index=yrs)
    r = sm.OLS(y, sm.add_constant(X)).fit()
    reg = EquationRegistry("FR1")
    reg.add("FR1.A", y, X, estimator="OLS", cov="hac", fit_coef=r.params, fit_se={}, components=["fr1:a", "fr1:b"],
            subtask="T", title_az="T", title_en="T", dependent_label_az="y")
    ep = reg.write(os.path.join(d, "FR1_equations.json"))
    cp = os.path.join(d, "cat.csv")
    write_catalog([{"id": "fr1:a", "label_az": "a", "kind": "level", "equation_ids": ["FR1.A", "FR1.Z"]}], cp, "FR1")
    probs = check_catalog(cp, ep, {"series": {"fr1:a": {}, "fr1:c": {}}})
    check(any("fr1:b" in q for q in probs) and any("FR1.Z" in q for q in probs) and any("fr1:c" in q for q in probs),
          f"cross-check {probs}")
