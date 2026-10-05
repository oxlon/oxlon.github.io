"""python3 -m microlib.docrefresh FR1|FR3|FR4|FR5 [...]  — exit code 1 (with the reason on stderr) on any failure."""
import sys

from . import MODULES, refresh
from .common import RefreshError


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or any(a.upper() not in MODULES for a in args):
        print(f"usage: python3 -m microlib.docrefresh {{{'|'.join(MODULES)}}} [...]", file=sys.stderr)
        return 2
    for m in args:
        try:
            refresh(m)
        except (RefreshError, KeyError, IndexError, FileNotFoundError, ValueError) as e:
            print(f"docrefresh {m.upper()} failed: {type(e).__name__}: {e}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
