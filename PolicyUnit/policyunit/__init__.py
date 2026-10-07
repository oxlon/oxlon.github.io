"""PolicyUnit — MİİS §15.5.4 İqtisadi Siyasətlərin Təsir Analizi.

Policy impact = scenario − baseline of the same vintage (counterfactual, əks-faktual).
Engines (plug-ins, `run(scenario, ctx) -> engine_base.Result`): eng_micro (MicroUnit FR1→FR12 chain,
the core), eng_caem (Ministry CAEM AZE Model — comparison), eng_oxlon (oil/partner/FX only, on a copy),
eng_io (input-output), eng_microsim (household microsimulation), eng_longrun (2031–2035 structural
extrapolation). `integrate.run_scenario` combines them; `kpi` scores scenarios (FR5).
"""
__version__ = "1.0.0"
