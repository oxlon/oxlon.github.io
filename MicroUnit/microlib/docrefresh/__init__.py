"""microlib.docrefresh — keeps the v2.2 passages of the FR1, FR3, FR4 and FR5 methodology documents current.

The notebooks regenerate only their own <!-- AUTO:... --> blocks.  The v2.2 notes (data and approaches adopted from the
Ministry's macro module, 2026-10-05) and the run-dependent v2.2 prose figures live in separate marker blocks
(<!-- AUTO:v22_<name> --> … <!-- /AUTO:v22_<name> -->; in FR4 <!-- AUTO:fr4v22_<name> -->, because FR4.ipynb matches its
own AUTO:v2 tag as a prefix) in docs/<M>_Methodology.md and docs/az/<M>_Metodologiya.md, regenerated here from the
run's output/ files.  run_all.py calls it after each of the four stages succeeds:

    python3 -m microlib.docrefresh FR1        # or FR3, FR4, FR5

Historical figures of the v2.1 -> v2.2 and v2.2 -> v2.3 changes are frozen in v22_reference.json; every current figure is
read from output/ (and data/ where noted). FR1's run-dependent figures that no CSV holds come from output/FR1_doc_figures.json
(FR1.ipynb Part 18.17); since v2.3 FR1 also generates its v2.3 note and the formerly hand-written §3.3/§7.1/§7.2/§7.5/§9
passages (AUTO:v23_* blocks).
"""
MODULES = ("FR1", "FR3", "FR4", "FR5")


def refresh(module):
    module = module.upper()
    if module == "FR1":
        from .fr1 import main
    elif module == "FR3":
        from .fr3 import main
    elif module in ("FR4", "FR5"):
        from .fr45 import fr4 as main4, fr5 as main5
        main = main4 if module == "FR4" else main5
    else:
        raise SystemExit(f"unknown module {module!r}; expected one of {', '.join(MODULES)}")
    main()
