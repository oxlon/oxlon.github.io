"""
helpers — sınaq mühiti: müvəqqəti MicroUnit kökü (lazımi qovluqların surəti) və təsadüfi portda server.

Real `data/` qovluğuna HEÇ VAXT yazılmır: hər şey müvəqqəti kökdə baş verir. Dəftərlərin yalnız kod
hücrələri köçürülür və birinci hücrəyə icranı dayandıran sətir əlavə olunur (FR1–FR5 mütləq yollarla real
output/ qovluğuna yazdığı üçün sınaq surəti heç vaxt icra edilməməlidir); server --dry-run-runs ilə işləyir.
"""
import csv, json, os, re, shutil, subprocess, sys, tempfile, time, urllib.error, urllib.request
from pathlib import Path

API = Path(__file__).resolve().parent.parent
REAL_ROOT = API.parent
TESTS = Path(__file__).resolve().parent
READ, WRITE = "t-read", "t-write"
TOKENS = "%s:read,%s:write" % (READ, WRITE)
STOP_CELL = "raise RuntimeError('SINAQ SURƏTİ — bu dəftər icra edilməməlidir (test copy, do not execute)')\n"
SYN = "SYNTHETIC — not real enterprise data"


def tmpdir(prefix):
    base = os.environ.get("MICRO_TEST_TMP") or None
    return Path(tempfile.mkdtemp(prefix=prefix, dir=base))


def strip_notebook(src, dst):
    nb = json.loads(Path(src).read_text(encoding="utf-8"))
    cells = [{"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": STOP_CELL}]
    for c in nb["cells"]:
        if c.get("cell_type") == "code":
            cells.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": c["source"]})
    Path(dst).write_text(json.dumps({"cells": cells, "metadata": nb.get("metadata", {}), "nbformat": 4, "nbformat_minor": 5},
                                    ensure_ascii=False), encoding="utf-8")


def head_csv(src, dst, n, mutate=None):
    with open(src, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        rows = [r for _, r in zip(range(n), rd)]
        fields = rd.fieldnames
    if mutate:
        rows = mutate(rows) or rows
    with open(dst, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return dst


def make_root(with_workbook=False):
    """Müvəqqəti kök: run_all.py, kod-only dəftərlər, panel/site (kiçik), data sxemləri, kiçik output faylları."""
    root = tmpdir("microunit-test-")
    shutil.copy2(REAL_ROOT / "run_all.py", root / "run_all.py")
    shutil.copy2(REAL_ROOT / "index.html", root / "index.html")
    for m in ("FR1", "FR3", "FR4", "FR5", "FR10", "FR12"):
        strip_notebook(REAL_ROOT / ("%s.ipynb" % m), root / ("%s.ipynb" % m))
    (root / "panel" / "assets").mkdir(parents=True)
    (root / "panel" / "data").mkdir()
    (root / "panel" / "_build").mkdir()
    shutil.copy2(REAL_ROOT / "panel" / "index.html", root / "panel" / "index.html")
    shutil.copy2(REAL_ROOT / "panel" / "assets" / "panel.css", root / "panel" / "assets" / "panel.css")
    (root / "panel" / "_build" / "pcore.py").write_text("SECRET_SOURCE = 1\n", encoding="utf-8")
    (root / "panel" / "build_panel.py").write_text("print('stub')\n", encoding="utf-8")
    (root / "site").mkdir()
    shutil.copy2(REAL_ROOT / "site" / "index.html", root / "site" / "index.html")
    (root / "site" / "build_site.py").write_text("print('stub')\n", encoding="utf-8")
    d = root / "data"
    for sub in ("firm_panel", "business_register", "dsk", "dsk_services", "dsk_enterprise/industry", "dsk_competition/current"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(REAL_ROOT / "data/firm_panel/FR10_firm_panel_column_map.csv", d / "firm_panel")
    shutil.copy2(REAL_ROOT / "data/business_register/FR12_business_register_column_map.csv", d / "business_register")
    head_csv(REAL_ROOT / "data/firm_panel/FR10_firm_panel_SYNTHETIC.csv", d / "firm_panel/FR10_firm_panel_SYNTHETIC.csv", 400)
    head_csv(REAL_ROOT / "data/business_register/FR12_business_register_SYNTHETIC.csv",
             d / "business_register/FR12_business_register_SYNTHETIC.csv", 400)
    shutil.copy2(REAL_ROOT / "data/dsk/002_1-2en.xls", d / "dsk" / "002_1-2en.xls")
    (d / "secret.txt").write_text("TOP-SECRET", encoding="utf-8")
    if with_workbook:
        for p in (REAL_ROOT / "data").glob("Statistik data dinamika*.xlsx"):
            shutil.copy2(p, d / p.name)
    out = root / "output"
    out.mkdir()
    for f in ("FR10_dsk_manifest.csv", "FR12_dsk_manifest.csv"):
        shutil.copy2(REAL_ROOT / "output" / f, out / f)
    (out / "FR10_SYNTHETIC_entry_exit.csv").write_text("a\n1\n", encoding="utf-8")
    return root


class ServerProc:
    """api/server.py alt prosesi; --port 0 ilə başladılır, real port stdout-dan oxunur."""

    def __init__(self, root, *extra, env=None):
        self.root = Path(root)
        e = dict(os.environ, API_TOKENS=TOKENS, MICRO_NO_NETWORK="1", PYTHONDONTWRITEBYTECODE="1")
        e.update(env or {})
        args = [sys.executable, str(API / "server.py"), "--port", "0", "--root", str(root), "--db", str(Path(root) / "test.db"),
                "--dry-run-runs", "--quiet"] + list(extra)
        self.p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=e, text=True)
        self.lines, t0 = [], time.time()
        while time.time() - t0 < 30:
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError("server başlamadı: " + "".join(self.lines))
            self.lines.append(line)
            m = re.search(r"http://127\.0\.0\.1:(\d+)/api/v1/health", line)
            if m:
                self.base = "http://127.0.0.1:%s" % m.group(1)
                break
        else:
            raise RuntimeError("server vaxtında başlamadı")
        import threading

        def drain():                       # keep reading so the server never blocks on a full pipe
            for line in self.p.stdout:
                self.lines.append(line)
        threading.Thread(target=drain, daemon=True).start()

    def stop(self):
        self.p.terminate()
        try:
            self.p.wait(10)
        except subprocess.TimeoutExpired:
            self.p.kill()
            self.p.wait(5)

    def req(self, method, path, body=None, token=READ, headers=None, raw=False):
        h = dict(headers or {})
        if token:
            h["Authorization"] = "Bearer " + token
        data = body
        if isinstance(body, (dict, list)):
            data = json.dumps(body).encode("utf-8")
            h.setdefault("Content-Type", "application/json")
        r = urllib.request.Request(self.base + path, data=data, method=method, headers=h)
        try:
            with urllib.request.urlopen(r, timeout=120) as resp:
                code, hdrs, payload = resp.status, dict(resp.headers), resp.read()
        except urllib.error.HTTPError as e:
            code, hdrs, payload = e.code, dict(e.headers), e.read()
        if raw:
            return code, hdrs, payload
        try:
            return code, json.loads(payload.decode("utf-8")) if payload else None
        except ValueError:
            return code, payload

    def wait_run(self, rid, timeout=60):
        t0 = time.time()
        while time.time() - t0 < timeout:
            code, r = self.req("GET", "/api/v1/runs/%s" % rid)
            if code == 200 and r["status"] not in ("running", "queued"):
                return r
            time.sleep(0.3)
        raise AssertionError("icra vaxtında bitmədi: %s" % rid)


def raw_http(base, path):
    """http.client ilə xam yol (urllib yolu normallaşdırmır, amma əmin olmaq üçün)."""
    import http.client
    host, port = base.replace("http://", "").split(":")
    c = http.client.HTTPConnection(host, int(port), timeout=30)
    c.putrequest("GET", path, skip_accept_encoding=True)
    c.endheaders()
    r = c.getresponse()
    body = r.read()
    c.close()
    return r.status, body


def firm_panel_rows(n=200, real=True):
    rows = []
    with open(REAL_ROOT / "data/firm_panel/FR10_firm_panel_SYNTHETIC.csv", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        for _, r in zip(range(n), rd):
            if real:
                r["data_status"] = "Ministry test copy"
            rows.append(r)
        return rd.fieldnames, rows


def to_csv_bytes(fields, rows):
    import io
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode("utf-8")
