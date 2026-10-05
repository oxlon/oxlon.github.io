#!/usr/bin/env python3
"""MİİS müştəri nümunəsi — yalnız standart kitabxana.

Faylı yükləyir → yoxlama hesabatını göstərir → tətbiq edir → icranı başladır → bitənə qədər izləyir →
proqnozları CSV-yə yazır.

    python3 sync_example.py --url http://127.0.0.1:8790 --token mikro-yaz \\
        --file FR10_firm_panel.csv --kind firm_panel --out proqnozlar.csv

    # yalnız proqnozları götürmək (oxu nişanı kifayətdir):
    python3 sync_example.py --url http://127.0.0.1:8790 --token mikro-oxu --module FR4 --out fr4.csv
"""
import argparse, csv, json, os, sys, time, urllib.error, urllib.parse, urllib.request


def call(a, method, path, body=None, headers=None):
    h = {"Authorization": "Bearer " + a.token, **(headers or {})}
    data = body
    if isinstance(body, (dict, list)):
        data = json.dumps(body).encode("utf-8")
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(a.url.rstrip("/") + path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8") or "null")


def upload(a):
    with open(a.file, "rb") as f:
        data = f.read()
    hdr = {"Content-Type": "application/octet-stream", "X-Filename": urllib.parse.quote(os.path.basename(a.file))}
    if a.kind:
        hdr["X-Kind"] = a.kind
    if a.subfolder:
        hdr["X-Subfolder"] = a.subfolder
    code, d = call(a, "POST", "/api/v1/uploads", data, hdr)
    if code not in (201, 422):
        sys.exit("yükləmə alınmadı (%s): %s" % (code, (d or {}).get("error")))
    v = d["validation"]
    print("yükləmə %s: %s — %d səhv, %d xəbərdarlıq" % (d["upload"]["id"], "QƏBUL EDİLDİ" if v["ok"] else "RƏDD EDİLDİ",
                                                       len(v.get("errors") or []), len(v.get("warnings") or [])))
    for e in (v.get("errors") or [])[:20]:
        where = ("sətir %s, %s: " % (e["row"], e.get("field"))) if e.get("row") else ""
        print("   XƏTA  %s%s" % (where, e.get("message")))
    if not v["ok"]:
        sys.exit(1)
    return d["upload"]["id"], v


def wait(a, rid):
    last = None
    while True:
        code, r = call(a, "GET", "/api/v1/runs/%s" % rid)
        cur = (r.get("progress") or {}).get("current")
        if cur != last:
            print("   %5.1f%%  %s" % (r.get("percent", 0), cur or ""))
            last = cur
        if r["status"] not in ("running", "queued"):
            return r
        time.sleep(a.poll)


def forecasts(a):
    q = {"scenario": a.scenario} if a.scenario else {}
    if a.module:
        q["module"] = a.module
    if a.ids:
        q["id"] = a.ids
    code, d = call(a, "GET", "/api/v1/forecasts?" + urllib.parse.urlencode(q))
    if code != 200:
        sys.exit("proqnozlar alınmadı (%s): %s" % (code, (d or {}).get("error")))
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "module", "label_az", "unit_az", "scenario", "period", "value"])
        for it in d["items"]:
            m = d["series"].get(it["id"], {})
            w.writerow([it["id"], it["module"], m.get("label_az"), m.get("unit_az"), it["scenario"], it["period"], it["value"]])
    print("proqnozlar: %d nöqtə, %d göstərici (mənbə: %s) → %s" % (len(d["items"]), len(d["series"]), d["source"], a.out))


def main():
    ap = argparse.ArgumentParser(description="MikroModel API müştəri nümunəsi")
    ap.add_argument("--url", default="http://127.0.0.1:8790")
    ap.add_argument("--token", required=True)
    ap.add_argument("--file", help="yüklənəcək fayl")
    ap.add_argument("--kind", help="workbook | dsk | firm_panel | business_register | series (verilməzsə addan)")
    ap.add_argument("--subfolder", help="DSK faylı üçün, məs. dsk_services")
    ap.add_argument("--no-run", action="store_true", help="tətbiq et, amma icra etmə")
    ap.add_argument("--module", help="proqnozlar üçün modul, məs. FR4")
    ap.add_argument("--ids", help="vergüllə ayrılmış göstəricilər, məs. fr1:rgdp,fr1:cpi")
    ap.add_argument("--scenario", default="Baseline,Adverse,Reform")
    ap.add_argument("--out", default="proqnozlar.csv")
    ap.add_argument("--poll", type=float, default=5.0)
    a = ap.parse_args()
    module = a.module
    if a.file:
        uid, v = upload(a)
        code, ap_ = call(a, "POST", "/api/v1/uploads/%s/apply%s" % (uid, "" if a.no_run else "?run=1"))
        if code != 200:
            sys.exit("tətbiq alınmadı (%s): %s" % (code, ap_["error"]["message"]))
        print("tətbiq olundu → %s; ehtiyat nüsxə: %s" % (ap_["apply"]["target"], ap_["apply"].get("backup") or "—"))
        run = ap_.get("run") or {}
        if run.get("id"):
            print("icra %s: %s" % (run["id"], " → ".join(run.get("plan") or [])))
            r = wait(a, run["id"])
            ok = r["status"] in ("ok", "dry-run")
            print("icra bitdi: %s%s" % (r["status"], "" if ok else (" — " + str((r.get("manifest") or {}).get("error")))))
            if not ok:
                print(r.get("stage_log_tail") or "")
                sys.exit(1)
        elif run.get("queued"):
            print("icra növbəyə qoyuldu: %s" % ", ".join(run["stages"]))
        module = module or (v.get("first_stage") if not a.ids else None)
    if module or a.ids:
        a.module = module
        forecasts(a)


if __name__ == "__main__":
    main()
