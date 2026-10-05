'''Assemble FR10.ipynb from the part files in src/ (cells separated by "# %%" markers).
Usage: python3 build.py [--upto pNN] [--out path] [--script path]'''
import sys, json, re, glob, os
from pathlib import Path
HERE = Path(__file__).parent
SRC = sorted(glob.glob(str(HERE / 'src' / 'p*.py')))
args = sys.argv[1:]
upto = None; out = None; script = None
for i, a in enumerate(args):
    if a == '--upto': upto = args[i + 1]
    if a == '--out': out = args[i + 1]
    if a == '--script': script = args[i + 1]
if upto:
    SRC = [s for s in SRC if Path(s).name[:3] <= upto]
cells = []
for fn in SRC:
    txt = Path(fn).read_text()
    chunks = re.split(r'^# %%(.*)$', txt, flags=re.M)
    # chunks: [pre, tag1, body1, tag2, body2, ...]
    for tag, body in zip(chunks[1::2], chunks[2::2]):
        body = body.strip('\n')
        if not body.strip():
            continue
        if '[markdown]' in tag:
            lines = [l[2:] if l.startswith('# ') else (l[1:] if l.startswith('#') else l) for l in body.split('\n')]
            cells.append(('markdown', '\n'.join(lines)))
        else:
            cells.append(('code', body))
nb = {'cells': [], 'metadata': {'kernelspec': {'display_name': 'Python (MİİS model)', 'language': 'python', 'name': 'miis-model'},
                                 'language_info': {'name': 'python'}}, 'nbformat': 4, 'nbformat_minor': 5}
for i, (kind, src) in enumerate(cells):
    lines = src.split('\n')
    srcl = [l + '\n' for l in lines[:-1]] + [lines[-1]]
    c = {'cell_type': kind, 'id': f'fr10-{i:03d}', 'metadata': {}, 'source': srcl}
    if kind == 'code':
        c['execution_count'] = None; c['outputs'] = []
    nb['cells'].append(c)
if out:
    Path(out).write_text(json.dumps(nb, indent=1, ensure_ascii=False))
    print(f'{len(cells)} cells -> {out}')
if script:
    code = ['import matplotlib; matplotlib.use("Agg")',
            'def display(*a, **k):\n    for x in a:\n        try:\n            print(x.to_string() if hasattr(x, "to_string") else x)\n        except Exception:\n            print(x)']
    for kind, src in cells:
        if kind == 'code':
            code.append('\n'.join(l for l in src.split('\n') if not l.startswith('%')))
    Path(script).write_text('\n\n'.join(code))
    print(f'script -> {script}')
