"""check.py — link checker and figure checks, run at the end of every build.

* every relative href/src resolves to an existing file, and every #fragment to an id in the target page;
* no external (http/https) script, stylesheet or link — the site must work offline from file://;
* every <use href="#icon-…"> has a symbol in the inline sprite;
* every figure mount has an inline figdata JSON that parses, has traces, and x/y of equal length.
"""
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote


class _P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.ids, self.uses, self.mounts, self.symbols = [], set(), [], [], set()
        self.figdata = {}
        self._fig = None
        self._buf = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "symbol" and "id" in a:
            self.symbols.add(a["id"])
        if tag == "use":
            self.uses.append(a.get("href", ""))
        elif tag in ("a", "link") and a.get("href"):
            self.links.append((tag, a["href"]))
        elif tag == "script" and a.get("src"):
            self.links.append((tag, a["src"]))
        if tag == "div" and "fig-mount" in a.get("class", ""):
            self.mounts.append(a.get("data-fig"))
        if tag == "script" and a.get("type") == "application/json" and a.get("id", "").startswith("figdata-"):
            self._fig = a["id"][8:]
            self._buf = []

    def handle_data(self, data):
        if self._fig is not None:
            self._buf.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._fig is not None:
            self.figdata[self._fig] = "".join(self._buf)
            self._fig = None


def _parse(p, cache):
    if p not in cache:
        x = _P()
        x.feed(p.read_text(encoding="utf-8"))
        cache[p] = x
    return cache[p]


def _fig_ok(js):
    spec = json.loads(js)
    data = spec.get("data") or []
    if not data:
        return "no traces"
    for t in data:
        if "x" in t and "y" in t and len(t["x"]) != len(t["y"]):
            return f"x/y length mismatch in trace '{t.get('name')}'"
        ys = [y for y in (t.get("y") or t.get("x") or []) if y is not None]
        if not ys:
            return f"empty trace '{t.get('name')}'"
    return None


def run(site):
    site = Path(site)
    pages = sorted(p for p in site.rglob("*.html") if "assets" not in p.parts)
    cache, errors, stats = {}, [], []
    for p in pages:
        x = _parse(p, cache)
        rel = p.relative_to(site)
        n_links = 0
        for tag, href in x.links:
            if re.match(r"^(https?:)?//", href):
                errors.append(f"{rel}: external {tag} {href}")
                continue
            if href.startswith(("mailto:", "javascript:")):
                continue
            n_links += 1
            path, _, frag = href.partition("#")
            target = p if not path else (p.parent / unquote(path)).resolve()
            if not target.exists():
                errors.append(f"{rel}: broken link {href}")
                continue
            if frag and target.suffix == ".html":
                if frag not in _parse(target, cache).ids:
                    errors.append(f"{rel}: missing anchor {href}")
        for u in x.uses:
            if u.lstrip("#") not in x.symbols:
                errors.append(f"{rel}: icon {u} not in sprite")
        for m in x.mounts:
            js = x.figdata.get(m)
            if js is None:
                errors.append(f"{rel}: figure {m} has no inline data")
                continue
            try:
                msg = _fig_ok(js)
            except ValueError as e:
                msg = f"JSON does not parse ({e})"
            if msg:
                errors.append(f"{rel}: figure {m}: {msg}")
        tables = p.read_text(encoding="utf-8").count("<table")
        stats.append((str(rel), len(x.mounts), tables, n_links))
    print(f"\n{'page':28s} figures tables links")
    for r, f, t, n in stats:
        print(f"{r:28s} {f:7d} {t:6d} {n:5d}")
    print(f"pages {len(pages)}, figures {sum(s[1] for s in stats)}, tables {sum(s[2] for s in stats)}, "
          f"links checked {sum(s[3] for s in stats)}")
    if errors:
        print(f"LINK/FIGURE CHECK: {len(errors)} problem(s)")
        for e in errors:
            print("  -", e)
        return False
    print("LINK/FIGURE CHECK: OK — every link and anchor resolves, no external resources, every figure parses")
    return True
