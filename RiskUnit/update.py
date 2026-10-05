"""NFR2 — automatic update of risk scores when new data arrives (acceptance: ≤ 24 hours).

    python3 update.py                 # one cycle: fetch feeds, recompute if any input changed
    python3 update.py --no-fetch      # only check local inputs (registers, upstream model outputs)
    python3 update.py --force         # recompute even if nothing changed
    python3 update.py --watch 15      # stay running; check every 15 minutes (manual register edits)

Every input is fingerprinted: the latest vintage of each live feed, every upstream file of the
§15.5.1 macro model and the §15.5.2 micro unit, and every Ministry-editable file in input/.
When the fingerprint changes the full scoring pipeline runs (≈10 s) and output/NFR2_update_log.csv
records when the change was first seen, when the scores were rewritten and the lag in hours.
The schedule in scheduler/ runs one cycle every day at 07:00 and the watch mode can run beside
it, so the lag stays far inside 24 hours. A cycle that fails is logged and alerts on the next
successful run; it never leaves half-written scores (the pipeline writes after all stages succeed).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import traceback
from datetime import datetime, timezone

import pandas as pd

from riskunit import config, feeds

STATE = config.OUTPUT / "NFR2_state.json"
LOG = config.OUTPUT / "NFR2_update_log.csv"
LOG_COLS = ["basladi_utc", "bitdi_utc", "tetik", "deyisen_girisler", "ilk_goruldu_utc", "muddet_san", "sla_saat",
            "sla_odenilir", "yuksek_prioritet", "xeberdarliq_sayi", "baseline_id", "status"]


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha(p) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def fingerprint() -> dict[str, str]:
    fp = {}
    man = feeds.read_manifest()
    for r in man[man.status == "ok"].groupby("feed").tail(1).itertuples():
        fp[f"axın:{r.feed}"] = r.sha256
    for key, p in {**config.MACRO_FILES, **config.MICRO_FILES}.items():
        if p.exists():
            fp[f"model:{key}"] = _sha(p)
    for p in sorted(config.INPUT.glob("*.csv")):
        fp[f"giriş:{p.name}"] = _sha(p)
    return fp


def load_state() -> dict:
    return json.loads(STATE.read_text()) if STATE.exists() else {"fingerprint": {}, "pending_since": {}}


def append_log(row: dict) -> None:
    new = pd.DataFrame([row], columns=LOG_COLS)
    if LOG.exists():
        new = pd.concat([pd.read_csv(LOG), new], ignore_index=True)
    new.to_csv(LOG, index=False)


def cycle(fetch: bool = True, force: bool = False, verbose: bool = True) -> dict:
    started = now()
    if fetch:
        feeds.fetch_all(verbose=verbose)
    st = load_state()
    fp = fingerprint()
    changed = sorted(k for k in fp if st["fingerprint"].get(k) != fp[k])
    # a change stays "pending" (with its first-seen time) until a recompute succeeds
    pending = st.get("pending_since", {})
    for k in changed:
        pending.setdefault(k, started)
    if not pending and not force:
        if verbose:
            print("Dəyişiklik yoxdur — skorlar aktualdır.")
        return {"status": "dəyişiklik yoxdur"}
    first_seen = min(pending.values()) if pending else started
    trig = "məcburi" if force and not pending else "yeni məlumat"
    t0 = time.time()
    row = {"basladi_utc": started, "tetik": trig, "deyisen_girisler": ";".join(sorted(pending)) or "—",
           "ilk_goruldu_utc": first_seen}
    try:
        import run_all
        from riskunit import factors, spine
        spine.clear_caches()
        factors.clear_caches()
        c = run_all.build_context(verbose=verbose)
        from riskunit import docs, report
        report.build_all(c, pdf=True)
        docs.update_methodology(c)
        done = now()
        lag_h = (pd.Timestamp(done) - pd.Timestamp(first_seen)).total_seconds() / 3600
        row.update({"bitdi_utc": done, "muddet_san": round(time.time() - t0, 1), "sla_saat": round(lag_h, 3),
                    "sla_odenilir": lag_h <= factors.params()["update_sla_hours"],
                    "yuksek_prioritet": ";".join(c["S"][c["S"]["prioritet"] == "yüksək"]["risk_id"]),
                    "xeberdarliq_sayi": len(c["alerts"]), "baseline_id": c["baseline_id"], "status": "uğurlu"})
        STATE.write_text(json.dumps({"fingerprint": fingerprint(), "pending_since": {}, "last_success_utc": done},
                                    ensure_ascii=False, indent=1))
    except Exception as exc:
        row.update({"bitdi_utc": now(), "muddet_san": round(time.time() - t0, 1), "status": f"xəta: {exc!r}"[:300]})
        STATE.write_text(json.dumps({"fingerprint": st["fingerprint"], "pending_since": pending,
                                     "last_failure_utc": row["bitdi_utc"]}, ensure_ascii=False, indent=1))
        traceback.print_exc()
    append_log(row)
    if verbose:
        print(f"{row['status']}: {row['deyisen_girisler'][:120]} — gecikmə {row.get('sla_saat', '—')} saat")
    return row


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--watch", type=float, default=0, help="dəqiqə; 0 — bir dövr")
    a = ap.parse_args(argv)
    if a.watch:
        last_fetch = 0.0
        while True:
            fetch = not a.no_fetch and time.time() - last_fetch > 6 * 3600     # feeds at most every 6 h
            cycle(fetch=fetch, force=False)
            if fetch:
                last_fetch = time.time()
            time.sleep(a.watch * 60)
    r = cycle(fetch=not a.no_fetch, force=a.force)
    return 0 if r.get("status") in ("uğurlu", "dəyişiklik yoxdur") else 1


if __name__ == "__main__":
    sys.exit(main())
