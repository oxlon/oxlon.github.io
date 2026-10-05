"""
nbextract — dəftərlərin kodundan sabit (literal) cədvəlləri oxuyur, kodu icra etmədən (ast).

İş kitabı ünvan cədvəlləri (FR1 VARMAP, FR3 WAGEMAP, FR4/FR5 `wb_rows(...)` çağırışları), region
siyahıları, DSK yükləmə siyahıları və s. Dəftər dəyişdikdə (mtime) yenidən oxunur.
"""
import ast, json, os, re
from pathlib import Path

_CACHE = {}


def code_cells(nb_path):
    """Kod hücrələri (IPython sehrli əmrləri `%`, `!` şərhə çevrilir)."""
    p = Path(nb_path)
    try:
        mt = p.stat().st_mtime_ns
    except OSError:
        return []
    key = ("cells", str(p))
    hit = _CACHE.get(key)
    if hit and hit[0] == mt:
        return hit[1]
    nb = json.loads(p.read_text(encoding="utf-8"))
    cells = []
    for c in nb.get("cells", []):
        if c.get("cell_type") != "code":
            continue
        s = c.get("source", "")
        s = "".join(s) if isinstance(s, list) else s
        s = "\n".join(("# " + l) if l.lstrip().startswith(("%", "!")) else l for l in s.splitlines())
        cells.append(s)
    _CACHE[key] = (mt, cells)
    return cells


def source(nb_path):
    return "\n".join(code_cells(nb_path))


class _Unresolved(Exception):
    pass


def _eval(node, env):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        raise _Unresolved(node.id)
    if isinstance(node, ast.Tuple):
        return tuple(_eval(e, env) for e in node.elts)
    if isinstance(node, ast.List):
        return [_eval(e, env) for e in node.elts]
    if isinstance(node, ast.Set):
        return {_eval(e, env) for e in node.elts}
    if isinstance(node, ast.Dict):
        if any(k is None for k in node.keys):                   # {**other}
            raise _Unresolved("**")
        return {_eval(k, env): _eval(v, env) for k, v in zip(node.keys, node.values)}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_eval(node.operand, env)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _eval(node.left, env) + _eval(node.right, env)
    raise _Unresolved(type(node).__name__)


def _assign_literals(tree, env):
    """Hücrədəki sadə `NAME = literal` və `A, B = 'x', 'y'` təyinatlarını env-ə yazır."""
    for st in tree.body:
        if not isinstance(st, ast.Assign) or len(st.targets) != 1:
            continue
        t = st.targets[0]
        try:
            if isinstance(t, ast.Name):
                env[t.id] = _eval(st.value, env)
            elif isinstance(t, ast.Tuple) and isinstance(st.value, ast.Tuple) and len(t.elts) == len(st.value.elts):
                vals = [_eval(v, env) for v in st.value.elts]
                for e, v in zip(t.elts, vals):
                    if isinstance(e, ast.Name):
                        env[e.id] = v
        except _Unresolved:
            continue


def _walk(nb_path):
    """(cell_index, ast tree, env-before-cell) ardıcıllığı; sintaksis xətalı hücrələr ötürülür."""
    env = {}
    for i, src in enumerate(code_cells(nb_path)):
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        before = dict(env)
        _assign_literals(tree, env)
        yield i, tree, before, env


def assigned(nb_path, name, default=None):
    """`name`-in sonuncu literal dəyəri (yoxdursa default)."""
    val = default
    for _, tree, _, env in _walk(nb_path):
        for st in tree.body:
            if isinstance(st, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in st.targets):
                if name in env:
                    val = env[name]
    return val


def calls(nb_path, func):
    """`func(...)` çağırışlarının həll edilə bilən mövqe arqumentləri: [(cell, [args...]), ...]."""
    out = []
    for i, tree, before, env in _walk(nb_path):
        local = dict(env)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == func:
                try:
                    out.append((i, [_eval(a, local) for a in node.args]))
                except _Unresolved:
                    out.append((i, None))
    return out


def regex_all(nb_path, pattern, flags=0):
    return re.findall(pattern, source(nb_path), flags)


def workbook_name(root, default="Statistik data dinamika 05.06.2026 +.xlsx"):
    """Dəftərlərin oxuduğu iş kitabının adı (hamısında eyni olmalıdır)."""
    names = set()
    for m in ("FR1", "FR3", "FR4", "FR5", "FR10", "FR12"):
        p = Path(root) / ("%s.ipynb" % m)
        if p.exists():
            names |= set(regex_all(p, r"Statistik data dinamika[^'\"\n]*?\.xlsx"))
    if len(names) == 1:
        return names.pop()
    return default if not names or default in names else sorted(names)[0]
