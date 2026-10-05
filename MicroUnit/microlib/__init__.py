"""microlib — shared library for MicroUnit v2 (equation registry, diagnostics, robustness, engines, catalog).

Dependencies: numpy, pandas, scipy, statsmodels only.
    from microlib.registry import EquationRegistry
    from microlib.engines import base as eng
    from microlib.catalog import write_catalog
"""
__version__ = "2.0.0"

ROOT_DEFAULT = "/Users/econ0757/My Drive/OxLon/MIIS_Micro_Risk_Policy/MicroUnit"


def project_root():
    import os
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.environ.get("MICROUNIT_ROOT", here)
