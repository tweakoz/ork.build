#!/bin/sh
# Relocatable trampoline: re-exec under THIS venv's interpreter (bin_priv/../../bin/python3),
# so the tree-sitter deps get installed INTO the venv where the cpp-db build tool actually
# runs (ork.cpp.db.build.py) -- NOT into whatever `python3` PATH resolves to (ork.python 3.14t,
# which is the wrong environment and pins an incompatible tree-sitter).
"exec" "$(dirname $0)/../../bin/python3" "$0" "$@"
"""
Set up the C++ entity-database build dependencies (tree-sitter) in THIS venv.

The cpp-db build engine (obt.cpp_build -> obt.cpp_parser_descent / cpp_stack_analyzer /
cpp_access_analyzer) needs the tree-sitter core + the C++ grammar binding:

  - tree-sitter        core parser (0.22+ API: `parser.language = Language(capsule)`)
  - tree-sitter-cpp    the C++ grammar

The query tools (search / members / objects / inhtree) read SQLite only and do NOT need
tree-sitter -- only the builder does. Only the C++ grammar is required; no obt module imports
the python/lua/glsl grammars, so they are intentionally not installed here.
"""

import sys
import argparse
import subprocess

# Verified-working, pinned versions for the 0.22+ tree-sitter API used by cpp_parser_descent.
# (tree-sitter core 0.22 removed Parser.set_language() and the 2-arg Language(ptr, name) form;
#  the obt parser modules use `parser.language = Language(ts_cpp.language())` which needs >= 0.22.)
REQUIREMENTS = [
    "tree-sitter==0.26.0",
    "tree-sitter-cpp==0.23.4",
]


def _pip(pip_args):
    return subprocess.run([sys.executable, "-m", "pip", *pip_args]).returncode


def _verify():
    """Confirm the parser actually constructs under the installed tree-sitter API."""
    import tree_sitter
    import tree_sitter_cpp
    from tree_sitter import Language, Parser
    parser = Parser()
    parser.language = Language(tree_sitter_cpp.language())
    return tree_sitter.__version__


def main():
    ap = argparse.ArgumentParser(
        description="Install the tree-sitter build deps for the C++ entity DB into this venv"
    )
    ap.add_argument("--dry-run", action="store_true",
                    help="print the target interpreter and requirements without installing")
    ap.add_argument("--upgrade", "-U", action="store_true",
                    help="pass --upgrade to pip (force reinstall to the pinned versions)")
    args = ap.parse_args()

    print(f"Target interpreter : {sys.executable}")
    print("Requirements       :")
    for req in REQUIREMENTS:
        print(f"  - {req}")

    if args.dry_run:
        print("(dry-run: nothing installed)")
        return 0

    pip_args = ["install"]
    if args.upgrade:
        pip_args.append("--upgrade")
    rc = _pip(pip_args + REQUIREMENTS)
    if rc != 0:
        print(f"ERROR: pip install failed (rc={rc})", file=sys.stderr)
        return rc

    try:
        version = _verify()
    except Exception as e:  # import/build/ABI mismatch surfaces here, not at first parse
        print(f"ERROR: tree-sitter verification failed after install: {e}", file=sys.stderr)
        return 1

    print(f"OK: tree-sitter {version} + C++ grammar installed; parser builds cleanly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
