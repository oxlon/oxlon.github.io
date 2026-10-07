"""
instrument_rules — yeni alət + adapter sətirlərinin statik yoxlanması (Azərbaycan dilində xətalar) və hər mühərrikin
qəbul etdiyi target_key nümunələri (mövcud adapters.csv + MikroUnit girişlər kataloqu).
"""
import re

import pu

ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,40}$")
GENERIC = ["pct", "add", "level", "target", "target_gdp", "shock_gdp", "target_rev"]
TRANSFORMS = [
    {"id": "pct", "label_az": "ölçü % kimi tətbiq olunur (səviyyəyə nisbətən)"},
    {"id": "add", "label_az": "ölçü bazaya əlavə olunur (f.b. və ya vahid)"},
    {"id": "level", "label_az": "ölçü səviyyə kimi verilir"},
    {"id": "target", "label_az": "CAEM: yol məcburi verilir (f.b.)"},
    {"id": "target_gdp", "label_az": "CAEM: xərc ÜDM-ə % kimi"},
    {"id": "shock_gdp", "label_az": "CAEM: şok ÜDM-ə % kimi"},
    {"id": "target_rev", "label_az": "CAEM: vergi gəliri ÜDM-ə % kimi"},
    {"id": "custom:<funksiya>", "label_az": "mühərrikdə mövcud xüsusi çevirmə (adapters.csv-də işlənənlərdən)"},
    {"id": "<transform>*k", "label_az": "miqyas əmsalı, məs. add*0.5"},
]
CAEM_STATES = ["gcap_y", "pb_y", "vatax_y", "ptax_y", "pitax_y", "otax_y", "CR", "dS", "dta", "dP", "dx"]
CUSTOM_HOME = {"micro": ("micro_map", "c_"), "microsim": ("eng_microsim", "c_")}


def _adapters():
    with pu.ENGINE_LOCK:
        return pu.P("registry").adapters().copy()


def target_keys():
    """{engine: [{key, transforms[], example_instrument}]} from adapters.csv (+ CAEM state codes)."""
    ad = _adapters()
    out = {}
    for (e, k), g in ad.groupby(["engine", "target_key"]):
        out.setdefault(e, []).append({"key": k, "transforms": sorted(set(g["transform"])),
                                      "example_instrument": g["instrument"].iloc[0], "note_az": g["note_az"].iloc[0]})
    have = {x["key"] for x in out.get("caem", [])}
    for s in CAEM_STATES:
        if s not in have:
            out.setdefault("caem", []).append({"key": s, "transforms": ["target", "target_gdp", "shock_gdp", "target_rev"],
                                               "example_instrument": None, "note_az": "CAEM AZE Model vəziyyət kodu"})
    return out


def _micro_ids(module, kind):
    try:
        with pu.ENGINE_LOCK:
            cat = pu.P("microbridge").catalogue(module)
        items = cat.get(kind) or []
        return {str(x.get("id") or x.get("name")) for x in items if isinstance(x, dict)}
    except Exception:
        return None


def _custom_ok(engine, name, ad):
    if ((ad["engine"] == engine) & (ad["transform"].str.split("*").str[0] == name)).any():
        return True
    home = CUSTOM_HOME.get(engine)
    if home:
        try:
            mod = pu.P(home[0])
            return hasattr(mod, home[1] + name.split(":", 1)[1])
        except Exception:
            return False
    return False


def _target_ok(engine, key, ad):
    known = set(ad[ad["engine"] == engine]["target_key"])
    if key in known:
        return None
    if engine == "caem":
        return None if key in CAEM_STATES else "CAEM vəziyyət kodu olmalıdır: %s" % ", ".join(CAEM_STATES)
    if engine == "micro":
        parts = key.split("/", 2)
        if len(parts) == 2 and parts[0] == "overlay" and parts[1] in ("price", "income", "supply"):
            return None
        if len(parts) != 3:
            return "MikroUnit açarı MODUL/növ/id formatında olmalıdır (məs. FR1/exogenous/minwage)"
        mod, kind, eid = parts
        ids = _micro_ids(mod, kind)
        if ids is None:
            return "MikroUnit-də «%s/%s» girişləri oxunmadı" % (mod, kind)
        if eid.split("=")[0].split(":")[0] not in ids and eid not in ids:
            return "MikroUnit %s %s siyahısında «%s» yoxdur" % (mod, kind, eid)
        return None
    if engine == "microsim" and key.startswith("param:"):
        import csv
        try:
            with open(pu.P("config").CONFIG / "tax_benefit.csv", encoding="utf-8") as f:
                params = {r["param"] for r in csv.DictReader(f)}
        except OSError:
            params = set()
        return None if key[6:].split("@")[0] in params else "tax_benefit.csv-də belə parametr yoxdur: %s" % key[6:]
    return "%s mühərrikinin mövcud girişlərindən biri olmalıdır (GET /api/v1/instruments/schema → target_keys)" % engine


def static_errors(ins, ads, existing):
    reg, c = pu.P("registry"), pu.P("config")
    e, w = [], []
    iid = str(ins.get("id") or "")
    if not ID_RE.match(iid):
        e.append("id '%s': kiçik latın hərfi ilə başlamalı, yalnız a–z, 0–9, '_' (2–41 simvol)" % iid)
    if iid in {x["id"] for x in existing}:
        e.append("id '%s' artıq kataloqda var" % iid)
    if not str(ins.get("name_az") or "").strip():
        e.append("name_az (alətin adı) tələb olunur")
    if ins.get("family") not in reg.FAMILIES:
        e.append("ailə '%s' yanlışdır — mümkün olanlar: %s" % (ins.get("family"), ", ".join(reg.FAMILIES)))
    if ins.get("unit") not in reg.UNITS:
        e.append("vahid '%s' yanlışdır — mümkün olanlar: %s" % (ins.get("unit"), ", ".join(reg.UNITS)))
    nums = {}
    for k in ("default_size", "min", "max"):
        v = ins.get(k)
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            e.append("'%s' ədəd olmalıdır" % k)
        else:
            nums[k] = float(v)
    if len(nums) == 3 and not (nums["min"] <= nums["default_size"] <= nums["max"]):
        e.append("min ≤ default_size ≤ max şərti pozulub")
    if len(nums) == 3 and nums["default_size"] == 0:
        e.append("default_size sıfır ola bilməz (sınaq hesablaması üçün)")
    for x in ("name_az", "description_az"):
        if any(ch in str(ins.get(x) or "") for ch in "\r\n"):
            e.append("%s sətir keçidi ehtiva edə bilməz" % x)
    cr = str(ins.get("cost_rule") or "none")
    if not re.match(r"^(none|spend|mw_budget|revenue:(vat|cit|pit|customs)|benefit:[a-z0-9_]+)$", cr):
        e.append("cost_rule '%s' yanlışdır (none | spend | revenue:<vat|cit|pit|customs> | benefit:<param> | mw_budget)" % cr)
    if str(ins.get("cost_in_fr1") or "no") not in ("yes", "no"):
        e.append("cost_in_fr1 yes və ya no olmalıdır")
    engines = ins.get("engines") or []
    for en in engines:
        if en not in c.ENGINE_MODULES:
            e.append("naməlum mühərrik '%s' — mümkün olanlar: %s" % (en, ", ".join(c.ENGINE_ORDER)))
    if not ads:
        e.append("ən azı bir adapter sətri tələb olunur (alət → mühərrik → giriş)")
    ad = _adapters()
    for i, a in enumerate(ads, 1):
        p = "adapter #%d (%s)" % (i, a.get("engine"))
        en, tk, tr = a.get("engine"), str(a.get("target_key") or ""), str(a.get("transform") or "")
        if en not in c.ENGINE_MODULES:
            e.append("%s: naməlum mühərrik" % p)
            continue
        if en not in engines:
            e.append("%s: mühərrik alətin engines siyahısında yoxdur" % p)
        if not tk:
            e.append("%s: target_key tələb olunur" % p)
        try:
            name, k = reg.parse_transform(tr)
        except Exception as ex:
            e.append("%s: %s" % (p, ex))
            continue
        if not name:
            e.append("%s: transform tələb olunur" % p)
        elif name.startswith("custom:"):
            if not _custom_ok(en, name, ad):
                e.append("%s: '%s' bu mühərrikdə mövcud xüsusi çevirmə deyil" % (p, name))
        elif name not in GENERIC:
            e.append("%s: transform '%s' yanlışdır (%s və ya custom:<funksiya>)" % (p, name, ", ".join(GENERIC)))
        if tk and not name.startswith("custom:"):
            msg = _target_ok(en, tk, ad)
            if msg:
                e.append("%s: target_key '%s' — %s" % (p, tk, msg))
        if any(ch in str(a.get("note_az") or "") for ch in "\r\n"):
            e.append("%s: note_az sətir keçidi ehtiva edə bilməz" % p)
    for en in engines:
        if en != "longrun" and not any(a.get("engine") == en for a in ads):
            w.append("%s mühərriki üçün adapter verilməyib — bu mühərrik aləti görməyəcək" % en)
    return e, w
