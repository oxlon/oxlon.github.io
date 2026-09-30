#!/usr/bin/env python3
"""Anbara artımlı yükləmə nümunəsi — yalnız standart kitabxana.

    python3 sync_example.py --url http://127.0.0.1:8787 --token anbar-oxu

Vəziyyəti `sync_state.json` faylında saxlayır: hər çağırışda yalnız ötən dəfədən
sonra dəyişmiş nöqtələri gətirir və CSV-yə yazır.
"""
import argparse, csv, json, os, urllib.request

def get(url, token, path):
    req = urllib.request.Request(url.rstrip("/") + path, headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--token", required=True)
    ap.add_argument("--state", default="sync_state.json")
    ap.add_argument("--out", default="observations.csv")
    a = ap.parse_args()

    state = {"since_seq": 0}
    if os.path.exists(a.state):
        state = json.load(open(a.state))

    rows, seq = [], state.get("since_seq", 0)
    while True:
        d = get(a.url, a.token, "/v1/observations?since_seq=%d&limit=10000" % seq)
        items = d.get("items") or []
        if not items:
            break
        rows += items
        seq = max(i["seq"] for i in items)
        if len(items) < 10000:
            break

    new = not os.path.exists(a.out)
    with open(a.out, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["model", "code", "period", "value", "source", "actor", "revision", "updated_at", "seq"])
        for i in rows:
            w.writerow([i["model"], i["code"], i["period"], i["value"], i.get("source"),
                        i.get("actor"), i.get("revision"), i.get("updated_at"), i["seq"]])

    json.dump({"since_seq": seq}, open(a.state, "w"))
    print("gətirildi: %d nöqtə | son seq: %d | fayl: %s" % (len(rows), seq, a.out))

if __name__ == "__main__":
    main()
